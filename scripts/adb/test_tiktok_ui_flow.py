import sys
import os
import time
import argparse
import subprocess
import xml.etree.ElementTree as ET
import re

class ADBAutomator:
    def __init__(self, adb_ip: str):
        self.adb_ip = adb_ip
        self.local_xml_path = f"window_dump_{self.adb_ip.replace(':', '_')}.xml"

    def _run_adb(self, args: list, timeout: int = 60) -> str:
        cmd = ["adb", "-s", self.adb_ip] + args
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
            return result.stdout
        except Exception as e:
            print(f"[ADBAutomator] Lỗi chạy lệnh {cmd}: {e}")
            return ""

    def dump_ui(self) -> ET.Element:
        remote_xml = "/sdcard/window_dump.xml"
        self._run_adb(["shell", "uiautomator", "dump", remote_xml])
        self._run_adb(["pull", remote_xml, self.local_xml_path])
        if not os.path.exists(self.local_xml_path):
            return None
        try:
            return ET.parse(self.local_xml_path).getroot()
        except:
            return None

    def _get_center_from_bounds(self, bounds_str: str):
        match = re.match(r'\[(\d+),(\d+)\]\[(\d+),(\d+)\]', bounds_str)
        if match:
            x1, y1, x2, y2 = map(int, match.groups())
            return (x1 + x2) // 2, (y1 + y2) // 2
        return None

    def find_element(self, texts=None, texts_contains=None, content_descs=None, resource_ids=None, classes=None):
        root = self.dump_ui()
        if root is None: return None
        for node in root.iter('node'):
            text = node.attrib.get('text', '')
            desc = node.attrib.get('content-desc', '')
            res_id = node.attrib.get('resource-id', '')
            cls = node.attrib.get('class', '')
            bounds = node.attrib.get('bounds', '')
            match = False
            if texts and text in texts: match = True
            elif texts_contains and any(t in text for t in texts_contains): match = True
            elif content_descs and desc in content_descs: match = True
            elif resource_ids and res_id in resource_ids: match = True
            elif classes and cls in classes: match = True
            if match and bounds:
                return self._get_center_from_bounds(bounds)
        return None

    def click_element(self, texts=None, texts_contains=None, content_descs=None, resource_ids=None, classes=None, wait=1, retries=2) -> bool:
        for _ in range(retries):
            coords = self.find_element(texts, texts_contains, content_descs, resource_ids, classes)
            if coords:
                x, y = coords
                print(f"[ADB] Bấm vào tọa độ {x},{y} (Tìm thấy element)")
                self._run_adb(["shell", "input", "tap", str(x), str(y)])
                time.sleep(wait)
                return True
            time.sleep(1)
        return False

    def click_percentage(self, pct_x: float, pct_y: float):
        w, h = 1080, 2400
        output = self._run_adb(["shell", "wm", "size"])
        match = re.search(r'Physical size: (\d+)x(\d+)', output)
        if match:
            w, h = int(match.group(1)), int(match.group(2))
        x = int(w * pct_x)
        y = int(h * pct_y)
        print(f"[ADB] Click tọa độ tương đối ({pct_x}, {pct_y}) -> ({x}, {y})")
        self._run_adb(["shell", "input", "tap", str(x), str(y)])
        time.sleep(1)

    def handle_permission_popups(self):
        self.click_element(texts=["Cho phép", "Allow", "Đồng ý", "Agree", "Got it", "While using the app", "Trong khi dùng ứng dụng"], wait=1, retries=1)

    def click_dynamic_bottom_right(self):
        self.click_percentage(0.8, 0.88)

    def click_dynamic_bottom_left(self):
        self.click_percentage(0.2, 0.88)


def run_adb(cmd, device_id=None):
    import subprocess
    base_cmd = ["adb"]
    if device_id:
        base_cmd.extend(["-s", device_id])
    base_cmd.extend(cmd.split())
    print(f"Executing: {' '.join(base_cmd)}")
    result = subprocess.run(base_cmd, capture_output=True, text=True)
    return result.stdout.strip()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--device", required=True, help="Device ID")
    parser.add_argument("--pkg", default="com.zhiliaoapp.musically")
    args = parser.parse_args()

    automator = ADBAutomator(args.device)
    
    # Do chạy trên Windows, thư mục /tmp có thể không tồn tại, đổi sang thư mục hiện tại
    automator.local_xml_path = f"window_dump_{args.device.replace(':', '_')}.xml"
    
    print(f"1. Tắt hoàn toàn TikTok ({args.pkg})...")
    run_adb(f"shell am force-stop {args.pkg}", args.device)
    time.sleep(2)
    
    print(f"\n2. Khởi chạy TikTok...")
    run_adb(f"shell monkey -p {args.pkg} -c android.intent.category.LAUNCHER 1", args.device)
    
    print("\n3. Chờ trang chủ tải (Tối đa 60 giây)...")
    app_opened = False
    for i in range(12):
        time.sleep(5)
        print(f"   Đang kiểm tra giao diện lần {i+1}...")
        if automator.find_element(texts=["Trang chủ", "Home", "Hồ sơ", "Profile", "Tạo", "Create", "Hộp thư", "Inbox"]):
            app_opened = True
            break
            
    if not app_opened:
        print("LỖI: Không thể mở vào trang chủ! (Có thể do mạng chậm hoặc vướng quảng cáo)")
        return
        
    print("\n4. NHÌN THẤY TRANG CHỦ! Chuẩn bị bấm Nút + (tọa độ 50% x 92%)...")
    time.sleep(2)
    automator.click_percentage(0.5, 0.92)
    time.sleep(3)
    
    print("\n5. Đóng popup quyền (nếu có)...")
    automator.handle_permission_popups()
    
    print("\n6. Bấm nút Tải lên (Upload)...")
    if not automator.click_element(texts=["Tải lên", "Upload", "Uploads"], content_descs=["Tải lên", "Upload", "Album", "Gallery", "Thư viện"], wait=3):
        print("   Không tìm thấy nút Tải lên bằng chữ hoặc mô tả ẩn, dùng thuật toán click mù...")
        automator.click_dynamic_bottom_left()
        
    automator.handle_permission_popups()
    
    print("\n7. Chuyển sang tab Video...")
    automator.click_element(texts_contains=["Video", "Videos"], content_descs=["Video", "Videos"], wait=2)
    
    print("\n8. Chọn video đầu tiên...")
    automator.click_percentage(0.25, 0.3)
    time.sleep(2)
    
    print("\n9. Bấm Tiếp / Next...")
    automator.click_element(texts=["Tiếp", "Next"], wait=4)
    
    print("\n10. Bấm Tiếp / Next (Màn hình edit)...")
    automator.click_element(texts=["Tiếp", "Next"], wait=3)
    
    print("\n>>> HOÀN TẤT LUỒNG TEST UI! KIỂM TRA ĐIỆN THOẠI XEM ĐÃ ĐẾN BƯỚC CAPTION CHƯA! <<<")

if __name__ == "__main__":
    main()
