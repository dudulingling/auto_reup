import os
import subprocess
import shutil
import random
import time
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional
from app.core.logger import get_logger

logger = get_logger(__name__)

# Danh sách Preset phần cứng điện thoại phổ biến và uy tín cao để chống quét reup
CAMERA_PRESETS = [
    {
        "manufacturer": "samsung",
        "model": "SM-S928B",  # Samsung Galaxy S24 Ultra
        "android_version": "14",
        "software": "S928BXXU1AXB5"
    },
    {
        "manufacturer": "samsung",
        "model": "SM-S918B",  # Samsung Galaxy S23 Ultra
        "android_version": "14",
        "software": "S918BXXU3BWJM"
    },
    {
        "manufacturer": "Xiaomi",
        "model": "2210132G",  # Xiaomi 13 Pro
        "android_version": "13",
        "software": "MIUI-V14.0.9.0.UMBMIXM"
    },
    {
        "manufacturer": "Xiaomi",
        "model": "23049PCD8G",  # POCO F5 Pro / Redmi K60
        "android_version": "14",
        "software": "HyperOS-1.0.2.0.UMNEUXM"
    },
    {
        "manufacturer": "Google",
        "model": "Pixel 8 Pro",
        "android_version": "14",
        "software": "UQ1A.240205.004"
    }
]


def get_device_camera_profile(adb_ip: Optional[str] = None) -> Dict[str, str]:
    """
    Lấy thông tin thiết bị để giả lập Camera.
    Ưu tiên 1: Đọc trực tiếp từ phần cứng điện thoại đang cắm ADB (getprop).
    Ưu tiên 2: Fallback sang Preset thiết bị cao cấp ngẫu nhiên.
    """
    if adb_ip:
        try:
            def _get_prop(prop_name: str) -> str:
                cmd = ["adb", "-s", adb_ip, "shell", "getprop", prop_name]
                res = subprocess.run(cmd, capture_output=True, text=True, timeout=10, encoding="utf-8", errors="replace")
                if res.returncode == 0:
                    return res.stdout.strip()
                return ""

            manufacturer = _get_prop("ro.product.manufacturer")
            model = _get_prop("ro.product.model")
            android_version = _get_prop("ro.build.version.release")
            software = _get_prop("ro.build.display.id")

            if manufacturer and model:
                logger.info(f"[Metadata] Đã tự động nhận diện thiết bị ADB thật: {manufacturer} {model} (Android {android_version or '13'})")
                return {
                    "manufacturer": manufacturer,
                    "model": model,
                    "android_version": android_version or "13",
                    "software": software or f"{model}_build",
                    "source": "adb_hardware"
                }
        except Exception as e:
            logger.warning(f"[Metadata] Không thể đọc thông số phần cứng từ ADB ({adb_ip}): {e}. Sẽ dùng Preset.")

    # Fallback Preset ngẫu nhiên
    chosen = random.choice(CAMERA_PRESETS).copy()
    chosen["source"] = "preset"
    logger.info(f"[Metadata] Sử dụng Preset Camera: {chosen['manufacturer']} {chosen['model']} (Android {chosen['android_version']})")
    return chosen


def verify_file_integrity(source_path: str, target_path: str, min_ratio: float = 0.85) -> bool:
    """
    Kiểm tra tính toàn vẹn của file tạm sau khi tạo/remux trên ổ cứng HDD:
    1. File đích phải tồn tại trên đĩa.
    2. Kích thước file đích phải > 0 bytes.
    3. Tỷ lệ kích thước so với file nguồn phải >= min_ratio (mặc định 85% vì là -c copy không re-encode).
    4. File handle có thể đọc được (đảm bảo buffer OS đã flush xong).
    """
    if not os.path.exists(target_path):
        logger.error(f"[Integrity] File đích không tồn tại: {target_path}")
        return False

    target_size = os.path.getsize(target_path)
    if target_size <= 0:
        logger.error(f"[Integrity] File đích rỗng (0 bytes): {target_path}")
        return False

    if os.path.exists(source_path):
        source_size = os.path.getsize(source_path)
        if source_size > 0:
            ratio = target_size / source_size
            if ratio < min_ratio:
                logger.error(f"[Integrity] Dung lượng file đích quá nhỏ so với file gốc ({target_size} vs {source_size} bytes, ratio={ratio:.2f})")
                return False

    # Thử đọc header để xác nhận OS đã đóng file và hoàn tất flush buffer trên HDD
    try:
        with open(target_path, "rb") as f:
            header = f.read(1024)
            if len(header) < 16:
                logger.error(f"[Integrity] Header file quá ngắn: {len(header)} bytes")
                return False
    except Exception as e:
        logger.error(f"[Integrity] Không thể đọc file đích {target_path}: {e}")
        return False

    return True


def generate_camera_filename(dt: Optional[datetime] = None) -> str:
    """
    Tạo tên file theo đúng chuẩn Camera điện thoại Android (LG, Samsung, Xiaomi, Pixel):
    Ví dụ: VID_20260915_150823.mp4
    """
    if not dt:
        dt = datetime.now()
    return dt.strftime("VID_%Y%m%d_%H%M%S.mp4")


def spoof_camera_metadata(
    input_path: str,
    output_path: str,
    device_profile: Optional[Dict[str, str]] = None,
    creation_time: Optional[datetime] = None,
    timeout: int = 300
) -> bool:
    """
    Xóa sạch metadata cũ (dấu vết CapCut, Lavf, tool cào) và gắn Metadata chuẩn Camera điện thoại:
    - Sử dụng FFmpeg `-c copy` (Stream copy siêu tốc 1-3s, 0% giảm chất lượng).
    - `-map_metadata -1`: Xóa toàn bộ tags cũ.
    - `-fflags +bitexact`: Loại bỏ chuỗi Lavf encoder mặc định của FFmpeg.
    - Gắn Make, Model, creation_time giả lập giờ quay bằng điện thoại trước đó 5-15 phút.
    - Gắn Android QuickTime atoms: com.android.manufacturer, com.android.model, com.android.version.
    - Gắn Handler names: VideoHandle, SoundHandle.
    """
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"File video nguồn không tồn tại: {input_path}")

    if not device_profile:
        device_profile = get_device_camera_profile()

    # Tính toán creation_time giả lập thời điểm quay video
    if not creation_time:
        minutes_offset = random.randint(5, 15)
        simulated_shoot_time = datetime.now(timezone.utc) - timedelta(minutes=minutes_offset)
    else:
        if creation_time.tzinfo is None:
            simulated_shoot_time = creation_time.replace(tzinfo=timezone.utc)
        else:
            simulated_shoot_time = creation_time.astimezone(timezone.utc)
        minutes_offset = max(0, int((datetime.now(timezone.utc) - simulated_shoot_time).total_seconds() / 60))

    creation_iso = simulated_shoot_time.strftime("%Y-%m-%dT%H:%M:%SZ")

    logger.info(f"[Metadata] Giả lập Camera: {device_profile['manufacturer']} {device_profile['model']} | Giờ quay: {creation_iso} (trước {minutes_offset} phút)")


    cmd = [
        "ffmpeg", "-y",
        "-i", input_path,
        "-c", "copy",
        "-map_metadata", "-1",                     # Xóa sạch toàn bộ metadata cũ
        "-movflags", "+faststart+use_metadata_tags", # Đưa moov atom lên đầu và cho phép ghi custom metadata tags vào MP4
        "-fflags", "+bitexact",                    # Xóa encoder signature Lavf
        "-flags:v", "+bitexact",
        "-flags:a", "+bitexact",
        "-metadata", "encoder=",                   # Xóa sạch tên encoder
        "-metadata:g", f"creation_time={creation_iso}",
        "-metadata:g", f"make={device_profile['manufacturer']}",
        "-metadata:g", f"model={device_profile['model']}",
        "-metadata:g", f"com.android.manufacturer={device_profile['manufacturer']}",
        "-metadata:g", f"com.android.model={device_profile['model']}",
        "-metadata:g", f"com.android.version={device_profile.get('android_version', '13')}",
        "-metadata:s:v:0", "handler_name=VideoHandle",
        "-metadata:s:a:0", "handler_name=SoundHandle",
        "-metadata:s:v:0", "rotate=0",
        output_path
    ]


    try:
        res = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            encoding="utf-8",
            errors="replace"
        )
        if res.returncode == 0 and verify_file_integrity(input_path, output_path):
            logger.info(f"[Metadata] Đã tạo file video giả lập Camera thành công ({os.path.getsize(output_path)} bytes): {output_path}")
            return True
        else:
            logger.warning(f"[Metadata] FFmpeg remux thất bại (code {res.returncode}): {res.stderr[:300]}. Fallback sang copy an toàn.")
    except subprocess.TimeoutExpired:
        logger.warning(f"[Metadata] FFmpeg remux bị timeout sau {timeout}s trên ổ HDD. Fallback sang copy an toàn.")
    except Exception as e:
        logger.warning(f"[Metadata] Lỗi khi remux metadata bằng FFmpeg: {e}. Fallback sang copy an toàn.")

    # Fallback: Copy trực tiếp nếu FFmpeg gặp trục trặc
    try:
        shutil.copy2(input_path, output_path)
        if verify_file_integrity(input_path, output_path):
            logger.info(f"[Metadata] Copy trực tiếp thành công: {output_path}")
            return True
        else:
            raise Exception("File copy không đạt tiêu chuẩn toàn vẹn (integrity check failed).")
    except Exception as err:
        logger.error(f"[Metadata] Thất bại hoàn toàn khi tạo file tạm: {err}")
        if os.path.exists(output_path):
            try:
                os.remove(output_path)
            except Exception:
                pass
        raise Exception(f"Không thể chuẩn bị file an toàn từ {input_path}: {err}")
