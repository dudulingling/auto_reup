import os
import sys
import time
import subprocess
import threading

# Thêm đường dẫn project vào sys.path để import module
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
BACKEND_DIR = os.path.join(ROOT_DIR, "backend")
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)
from app.services.processor.audio_extractor import separate_audio_with_ai

max_vram = 0
stop_monitoring = False

def monitor_gpu():
    global max_vram
    while not stop_monitoring:
        try:
            # Truy vấn VRAM hiện tại
            result = subprocess.run(
                ["nvidia-smi", "--query-gpu=memory.used", "--format=csv,nounits,noheader"],
                capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW
            )
            try:
                vram_used = int(result.stdout.strip())
                if vram_used > max_vram:
                    max_vram = vram_used
            except ValueError:
                pass
        except Exception:
            pass
        time.sleep(0.5)

if __name__ == "__main__":
    audio_file = os.path.join(ROOT_DIR, "data", "audio", "7641540695068584558_audio.mp3")
    output_dir = os.path.join(ROOT_DIR, "data", "temp")
    
    if not os.path.exists(audio_file):
        print(f"[!] Không tìm thấy file audio để test: {audio_file}")
        sys.exit(1)
        
    os.makedirs(output_dir, exist_ok=True)
    
    def log_cb(msg, **kwargs):
        print(msg.strip())
        
    print(f"[*] Bắt đầu test tách âm thanh AI (Demucs/UVR5) với file: {os.path.basename(audio_file)}")
    print(f"[*] Xin vui lòng chờ, quá trình này có thể mất một lúc...")
    
    # Khởi động thread giám sát GPU
    monitor_thread = threading.Thread(target=monitor_gpu)
    monitor_thread.start()
    
    start_time = time.time()
    try:
        vocal_file, inst_file = separate_audio_with_ai(audio_file, output_dir, log_callback=log_cb)
    except Exception as e:
        print(f"[!] Lỗi khi chạy Demucs: {e}")
        vocal_file, inst_file = None, None
        
    end_time = time.time()
    
    # Dừng giám sát GPU
    stop_monitoring = True
    monitor_thread.join()
    
    print("\n" + "=" * 50)
    print("📊 KẾT QUẢ ĐÁNH GIÁ HIỆU NĂNG DEMUCS")
    print("=" * 50)
    print(f"⏱️ Thời gian thực thi    : {end_time - start_time:.2f} giây")
    print(f"🎮 VRAM GPU tiêu thụ max : {max_vram} MB")
    
    if vocal_file and inst_file:
        print(f"✅ File Giọng nói (Vocal) : {os.path.basename(vocal_file)}")
        print(f"✅ File Nhạc nền (Inst)   : {os.path.basename(inst_file)}")
    else:
        print("❌ Quá trình tách âm thanh thất bại!")
    print("=" * 50)
