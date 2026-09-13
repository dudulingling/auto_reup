import subprocess
import time
import re
import argparse
import os

def run_adb(cmd, device_id=None):
    base_cmd = ["adb"]
    if device_id:
        base_cmd.extend(["-s", device_id])
    base_cmd.extend(cmd.split())
    print(f"Executing: {' '.join(base_cmd)}")
    result = subprocess.run(base_cmd, capture_output=True, text=True)
    return result.stdout.strip()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--device", help="Device ID (IP or serial)")
    parser.add_argument("--video", help="Path to local video file", default="test_video.mp4")
    parser.add_argument("--pkg", help="Tiktok Package Name", default="com.zhiliaoapp.musically")
    args = parser.parse_args()
    
    device_id = args.device
    if device_id and ":" in device_id:
        print(f"Đang kết nối tới thiết bị {device_id}...")
        run_adb(f"connect {device_id}")
        
    if not device_id:
        print("Lấy danh sách thiết bị ADB...")
        devices_out = run_adb("devices")
        lines = devices_out.split('\n')[1:]
        devices = [line.split('\t')[0] for line in lines if '\t' in line]
        if not devices:
            print("Không tìm thấy thiết bị ADB nào đang kết nối!")
            return
        device_id = devices[0]
        print(f"Tự động chọn thiết bị: {device_id}")

    # Cố gắng tìm một file MP4 thực tế từ dự án để Share không bị lỗi
    local_vid = args.video
    if not os.path.exists(local_vid):
        # Tạo file nháp 1KB (Có thể bị Tiktok báo lỗi định dạng nhưng vẫn vào được màn hình Edit)
        print(f"Không có file {local_vid}, tạo file video giả 1KB...")
        with open(local_vid, "wb") as f:
            f.write(b"\x00" * 1024)

    remote_path = f"/sdcard/DCIM/Camera/reup_share_{int(time.time())}.mp4"
    
    # 1. Chép file vào điện thoại
    print(f"\n1. Chép video vào điện thoại ({remote_path})...")
    run_adb(f"push {local_vid} {remote_path}", device_id)
    
    # 2. Quét Media Store
    print("\n2. Gọi hệ điều hành quét file vừa chép vào Thư viện...")
    run_adb(f"shell am broadcast -a android.intent.action.MEDIA_SCANNER_SCAN_FILE -d file://{remote_path}", device_id)
    time.sleep(3)
    
    # 3. Truy vấn Content URI từ MediaStore
    print("\n3. Lấy Content URI (bắt buộc trên Android 7+)...")
    query_cmd = f"shell content query --uri content://media/external/video/media --projection _id,_data"
    query_out = run_adb(query_cmd, device_id)
    
    content_uri = None
    for line in query_out.split('\n'):
        if remote_path in line:
            match = re.search(r'_id=(\d+)', line)
            if match:
                video_id = match.group(1)
                content_uri = f"content://media/external/video/media/{video_id}"
                break
                
    if not content_uri:
        print("Không tìm được Content URI, fallback sang file://...")
        content_uri = f"file://{remote_path}"
    else:
        print(f"Thành công! URI: {content_uri}")
        
    print(f"\n4. Tắt TikTok ({args.pkg}) để đảm bảo không bị kẹt cache...")
    run_adb(f"shell am force-stop {args.pkg}", device_id)
    time.sleep(2)
    
    # 5. Bắn Share Intent
    print(f"\n5. KÍCH HOẠT SHARE INTENT sang TikTok...")
    share_cmd = f"shell am start -a android.intent.action.SEND -t video/mp4 --eu android.intent.extra.STREAM {content_uri} -f 1 -p {args.pkg}"
    out = run_adb(share_cmd, device_id)
    print("\nKết quả:")
    print(out)
    print("\n>>> HÃY KIỂM TRA ĐIỆN THOẠI XEM TIKTOK ĐÃ NHẢY VÀO BƯỚC ĐIỀN CAPTIONS CHƯA! <<<")

if __name__ == "__main__":
    main()
