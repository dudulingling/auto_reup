import os
import sys
import time

def test_vieneu_clone():
    print("[*] Bắt đầu kiểm tra tính năng Clone giọng nói của VieNeu-TTS...")
    
    # 1. Thử import vieneu
    try:
        from vieneu import Vieneu
        print("  - Import 'vieneu' thành công! ✓")
    except ImportError as e:
        print(f"  - Lỗi: Không thể import 'vieneu'. Chi tiết: {e} ✕")
        return
        
    # 2. Khởi tạo mô hình
    try:
        tts = Vieneu(emotion="natural")
        print("  - Khởi tạo VieNeu-TTS thành công! ✓")
    except Exception as e:
        print(f"  - Lỗi khi khởi tạo mô hình: {e} ✕")
        return

    # 3. Kiểm tra xem class Vieneu có hỗ trợ clone (encode_reference) không
    if not hasattr(tts, 'encode_reference'):
        print("  - Lỗi: Thư viện 'vieneu' cài đặt không hỗ trợ method 'encode_reference'! ✕")
        return
    else:
        print("  - Thư viện 'vieneu' hỗ trợ phương thức 'encode_reference'! ✓")

    # 4. Kiểm tra giả lập sinh giọng với một file wav mẫu (nếu tồn tại)
    output_dir = "/data/temp"
    os.makedirs(output_dir, exist_ok=True)
    ref_audio_path = os.path.join(output_dir, "temp_ref.wav")
    
    print("\n[*] Sinh âm thanh mặc định để làm file mẫu clone...")
    try:
        audio = tts.infer(text="Đây là âm thanh mẫu được sinh ra để kiểm tra tính năng sao chép giọng nói.")
        tts.save(audio, ref_audio_path)
        print(f"  - Đã lưu file mẫu tại: {ref_audio_path} ✓")
    except Exception as e:
        print(f"  - Lỗi khi sinh âm thanh mặc định: {e} ✕")
        return
        
    print("\n[*] Thử nghiệm clone giọng nói bằng file mẫu vừa tạo...")
    try:
        start_time = time.time()
        # Encode giọng mẫu
        voice_data = tts.encode_reference(ref_audio_path)
        print("  - Encode file âm thanh mẫu thành công! ✓")
        
        # Sinh giọng mới sử dụng giọng clone
        cloned_audio = tts.infer(text="Xin chào, đây là giọng đọc đã được sao chép thành công.", voice=voice_data)
        
        output_file = os.path.join(output_dir, "test_cloned_output.wav")
        tts.save(cloned_audio, output_file)
        
        print(f"  - Sinh giọng clone thành công! ✓ (Thời gian: {time.time() - start_time:.2f} giây)")
        print(f"  - Kết quả lưu tại: {output_file}")
    except Exception as e:
        print(f"  - Lỗi trong quá trình clone giọng nói: {e} ✕")
    finally:
        # Dọn dẹp file temp ref
        if os.path.exists(ref_audio_path):
            os.remove(ref_audio_path)

if __name__ == "__main__":
    test_vieneu_clone()
