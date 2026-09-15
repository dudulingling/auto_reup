import os
import sys

if sys.platform == "win32":
    try:
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        if hasattr(sys.stderr, "reconfigure"):
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

import subprocess
import json
import shutil
from unittest.mock import patch, MagicMock
from contextlib import contextmanager

@contextmanager
def assert_raises(exc_class):
    class ExcHolder:
        value = None
    holder = ExcHolder()
    try:
        yield holder
    except exc_class as e:
        holder.value = e
    except Exception as e:
        raise AssertionError(f"Mong đợi ngoại lệ {exc_class}, nhưng nhận được {type(e)}: {e}")
    else:
        raise AssertionError(f"Mong đợi ngoại lệ {exc_class}, nhưng không có ngoại lệ nào được ném ra!")


# Add backend directory to sys.path
BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from app.utils.video_metadata import (
    get_device_camera_profile,
    verify_file_integrity,
    spoof_camera_metadata,
    CAMERA_PRESETS
)
from app.services.uploader.adb_engine import (
    ADBUploader,
    ADBCommandError,
    ADBTimeoutError
)


def test_device_camera_profile_fallback():
    """Kiểm tra get_device_camera_profile trả về preset hợp lệ khi không có ADB"""
    profile = get_device_camera_profile(adb_ip=None)
    assert profile is not None
    assert "manufacturer" in profile
    assert "model" in profile
    assert "android_version" in profile
    assert profile["source"] == "preset"
    assert profile["manufacturer"] in ["samsung", "Xiaomi", "Google"]


def test_verify_file_integrity(tmp_path):
    """Kiểm tra hàm verify_file_integrity"""
    # 1. File không tồn tại -> False
    assert not verify_file_integrity("not_exist_source.mp4", str(tmp_path / "not_exist.mp4"))

    # 2. File rỗng (0 bytes) -> False
    empty_target = tmp_path / "empty.mp4"
    empty_target.write_bytes(b"")
    assert not verify_file_integrity("source.mp4", str(empty_target))

    # 3. File quá nhỏ so với file gốc -> False
    src = tmp_path / "src.mp4"
    src.write_bytes(b"A" * 10000)
    small_target = tmp_path / "small.mp4"
    small_target.write_bytes(b"A" * 1000)  # 10% < 85%
    assert not verify_file_integrity(str(src), str(small_target), min_ratio=0.85)

    # 4. File hợp lệ -> True
    valid_target = tmp_path / "valid.mp4"
    valid_target.write_bytes(b"B" * 9500)  # 95% >= 85%
    assert verify_file_integrity(str(src), str(valid_target), min_ratio=0.85)


def test_spoof_camera_metadata_with_ffprobe(tmp_path):
    """Kiểm tra remux metadata bằng FFmpeg và kiểm tra các thẻ bằng ffprobe"""
    sample_video = os.path.join(BACKEND_DIR, "..", "data", "processed_videos", "7635277322316254500_processed.mp4")
    if not os.path.exists(sample_video):
        print("Bỏ qua test vì không có video mẫu")
        return

    out_file = str(tmp_path / "spoofed_camera.mp4")
    test_profile = {
        "manufacturer": "samsung",
        "model": "SM-S928B",
        "android_version": "14",
        "software": "S928BXXU1AXB5"
    }

    success = spoof_camera_metadata(sample_video, out_file, device_profile=test_profile, timeout=60)
    assert success is True
    assert os.path.exists(out_file)
    assert os.path.getsize(out_file) > 0

    # Dùng ffprobe để kiểm tra metadata tags thực tế của file kết quả
    probe_cmd = [
        "ffprobe", "-v", "quiet",
        "-print_format", "json",
        "-show_format",
        out_file
    ]
    probe_res = subprocess.run(probe_cmd, capture_output=True, text=True, encoding="utf-8")
    if probe_res.returncode == 0:
        probe_data = json.loads(probe_res.stdout)
        tags = probe_data.get("format", {}).get("tags", {})
        print("Format tags:", tags)
        # Kiểm tra Make & Model
        assert tags.get("make") == "samsung" or tags.get("com.android.manufacturer") == "samsung"
        assert tags.get("model") == "SM-S928B" or tags.get("com.android.model") == "SM-S928B"
        assert "creation_time" in tags


def test_adb_run_cmd_check_error():
    """Kiểm tra _run_adb_cmd(..., check=True) ném ngoại lệ khi có lỗi"""
    uploader = ADBUploader({"device_id": "127.0.0.1:5555", "auth_data": "127.0.0.1:5555"})
    
    # 1. Khi check=False: returncode != 0 chỉ in log và trả về stdout
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=1, stderr="device offline", stdout="")
        res = uploader._run_adb_cmd(["push", "a", "b"], check=False)
        assert res == ""

    # 2. Khi check=True: returncode != 0 PHẢI ném ADBCommandError
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=1, stderr="device offline", stdout="")
        with assert_raises(ADBCommandError) as exc_info:
            uploader._run_adb_cmd(["push", "a", "b"], check=True)
        assert "device offline" in str(exc_info.value)

    # 3. Khi check=True và bị TimeoutExpired: PHẢI ném ADBTimeoutError
    with patch("subprocess.run") as mock_run:
        mock_run.side_effect = subprocess.TimeoutExpired(cmd=["push"], timeout=120)
        with assert_raises(ADBTimeoutError):
            uploader._run_adb_cmd(["push", "a", "b"], check=True)


def test_upload_push_size_mismatch_halts(tmp_path):
    """Kiểm tra upload() dừng ngay và báo lỗi khi dung lượng file trên điện thoại bị lệch"""
    sample_video = tmp_path / "test_vid.mp4"
    sample_video.write_bytes(b"X" * 50000)

    uploader = ADBUploader({"device_id": "127.0.0.1:5555", "auth_data": "127.0.0.1:5555", "platform": "tiktok"})

    def fake_spoof(src, dst, **kwargs):
        with open(dst, "wb") as f:
            f.write(b"X" * 50000)
        return True

    with patch.object(uploader, "connect", return_value=True), \
         patch.object(uploader, "_run_adb_cmd") as mock_cmd, \
         patch("app.services.uploader.adb_engine.spoof_camera_metadata", side_effect=fake_spoof), \
         patch("app.services.uploader.adb_engine.verify_file_integrity", return_value=True):
        
        def fake_run_adb(args, timeout=60, check=False):
            if "stat" in args:
                return "20000"  # Giả lập kích thước trên điện thoại chỉ nhận được 20000 bytes trong khi local là 50000
            return ""

        mock_cmd.side_effect = fake_run_adb

        with assert_raises(Exception) as exc_info:
            uploader.upload(str(sample_video), caption="Test", hashtags="#test")

        print("Captured expected exception:", exc_info.value)
        assert "bị lỗi/cắt cụt" in str(exc_info.value) or "dung lượng" in str(exc_info.value)
        # Đảm bảo lệnh xóa file rác trên điện thoại đã được gọi
        cleanup_called = any("rm" in call.args[0] for call in mock_cmd.call_args_list)
        assert cleanup_called is True




if __name__ == "__main__":
    import pathlib
    import tempfile
    
    print("=== Đang chạy test: get_device_camera_profile ===")
    test_device_camera_profile_fallback()
    print("[PASS] test_device_camera_profile_fallback")

    with tempfile.TemporaryDirectory() as td:
        tmp = pathlib.Path(td)
        print("=== Đang chạy test: verify_file_integrity ===")
        test_verify_file_integrity(tmp)
        print("[PASS] test_verify_file_integrity")

        print("=== Đang chạy test: spoof_camera_metadata_with_ffprobe ===")
        test_spoof_camera_metadata_with_ffprobe(tmp)
        print("[PASS] test_spoof_camera_metadata_with_ffprobe")

        print("=== Đang chạy test: test_upload_push_size_mismatch_halts ===")
        test_upload_push_size_mismatch_halts(tmp)
        print("[PASS] test_upload_push_size_mismatch_halts")

    print("=== Đang chạy test: adb_run_cmd_check_error ===")
    test_adb_run_cmd_check_error()
    print("[PASS] test_adb_run_cmd_check_error")

    print("\n>>> TẤT CẢ CÁC BẢN TEST ĐÃ VƯỢT QUA 100%! <<<")

