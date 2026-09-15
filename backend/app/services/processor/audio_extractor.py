import os
import subprocess
import threading
import imageio_ffmpeg

ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()

# Cache for UVR5 Separator
_separator_instance = None
_separator_lock = threading.Lock()

def extract_audio(video_path: str, output_audio_path: str):
    """
    Tách âm thanh từ video gốc thành file mp3 (nếu cần thiết cho các công cụ khác).
    """
    cmd = [
        ffmpeg_exe,
        "-y",
        "-i", video_path,
        "-q:a", "0",
        "-map", "a",
        output_audio_path
    ]
    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True, encoding='utf-8', errors='replace')
        return output_audio_path
    except subprocess.CalledProcessError as e:
        raise Exception(f"Lỗi FFmpeg khi trích xuất âm thanh: {e.stderr}")

def separate_audio_with_ai(audio_path: str, output_dir: str, log_callback=None):
    """
    Sử dụng AI (UVR5/Demucs) để bóc tách giọng nói/giọng hát ra khỏi nhạc nền.
    Trả về (vocal_file, instrumental_file). Nếu thất bại trả về (audio_path, None).
    """
    # 1. Ưu tiên kiểm tra xem Colab GPU có đang bật không
    try:
        from app.services.processor.colab_bridge import ColabBridge
        if ColabBridge.is_enabled():
            if log_callback:
                log_callback("[*] ☁️ [Colab T4] Đang gửi audio sang Google Colab để tách giọng nói & nhạc nền (UVR5 GPU)...\n")
            sep_res = ColabBridge.separate_audio(audio_path, output_dir)
            v_path = sep_res.get("vocal_path")
            i_path = sep_res.get("instrumental_path")
            if v_path and os.path.exists(v_path):
                if log_callback:
                    log_callback("[+] ☁️ [Colab T4] Đã tách giọng nói & nhạc nền thành công qua GPU T4!\n")
                return v_path, i_path
            else:
                if log_callback:
                    log_callback("[!] [Colab T4] Không nhận được file tách từ Colab. Chuyển sang xử lý local...\n")
    except Exception as colab_err:
        if log_callback:
            log_callback(f"[!] [Colab T4] Lỗi tách âm AI: {colab_err}. Tự động chuyển sang UVR5 Local...\n")

    # 2. Xử lý local bằng audio_separator (chạy trên máy cục bộ)
    try:
        from audio_separator.separator import Separator
    except ImportError:
        if log_callback:
            log_callback("[!] Chưa cài đặt audio-separator. Bỏ qua bước tách AI.\n")
        return audio_path, None

    if log_callback:
        log_callback(f"[*] Đang tách giọng nói bằng AI (UVR5), quá trình này mất khoảng 15-30s...\n")

    try:
        global _separator_instance
        
        with _separator_lock:
            if _separator_instance is None:
                if log_callback:
                    log_callback(f"[*] Đang nạp model AI (UVR5) vào bộ nhớ lần đầu tiên...\n")
                
                # Cấu hình Separator sử dụng CPU hoặc ONNX GPU
                _separator_instance = Separator(
                    output_dir=output_dir, 
                    output_format="wav"
                )
                
                # Tải mô hình Kim_Vocal_2 chuyên tách Giọng nói để giữ nguyên vẹn Hiệu ứng SFX cho Nhạc nền
                _separator_instance.load_model(model_filename="Kim_Vocal_2.onnx")
            else:
                # Đảm bảo output_dir được cập nhật theo thư mục mới
                _separator_instance.output_dir = output_dir
                
        # Chunking logic for long audio (VRAM optimization)
        import pydub
        from pydub import AudioSegment
        import tempfile
        import shutil
        
        # AudioSegment.converter was already set in tts_generator.py, but just in case:
        AudioSegment.converter = imageio_ffmpeg.get_ffmpeg_exe()
        
        audio = AudioSegment.from_file(audio_path)
        chunk_length_ms = 60 * 1000 # 60 seconds
        
        if len(audio) <= chunk_length_ms:
            # Process directly if short enough
            output_files = _separator_instance.separate(audio_path)
            
            vocal_file = None
            instrumental_file = None
            for f in output_files:
                if "Vocals" in f or "vocals" in f.lower():
                    vocal_file = os.path.join(output_dir, f)
                elif "Instrumental" in f or "instrumental" in f.lower() or "Other" in f:
                    instrumental_file = os.path.join(output_dir, f)
                    
            if not vocal_file and len(output_files) >= 2:
                vocal_file = os.path.join(output_dir, output_files[1])
            if not instrumental_file and len(output_files) >= 1:
                instrumental_file = os.path.join(output_dir, output_files[0])
                
            if vocal_file and os.path.exists(vocal_file):
                if log_callback:
                    log_callback(f"[*] Đã tách giọng nói bằng AI thành công.\n")
                return vocal_file, instrumental_file
                
            return audio_path, None
        else:
            if log_callback:
                log_callback(f"[*] File audio dài ({len(audio)/1000:.1f}s), đang chia nhỏ (chunking) để tránh tràn VRAM...\n")
                
            import math
            total_ms = len(audio)
            num_chunks = math.ceil(total_ms / chunk_length_ms)
            even_chunk_length = total_ms // num_chunks
            
            chunks = []
            for i in range(num_chunks):
                start = i * even_chunk_length
                end = (i + 1) * even_chunk_length if i < num_chunks - 1 else total_ms
                chunks.append(audio[start:end])
            
            tmp_dir = tempfile.mkdtemp(prefix="audio_chunks_")
            
            vocal_chunks = []
            inst_chunks = []
            
            import gc
            
            for idx, chunk in enumerate(chunks):
                if log_callback:
                    log_callback(f"[*] Tách âm AI: Đang xử lý phần {idx+1}/{len(chunks)}...\n")
                    
                chunk_path = os.path.join(tmp_dir, f"chunk_{idx}.wav")
                chunk.export(chunk_path, format="wav")
                
                # We do not change _separator_instance.output_dir dynamically,
                # because the library caches it or ignores changes.
                # Instead, we just let it output to its initial output_dir (which is output_dir).
                
                out_files = _separator_instance.separate(chunk_path)
                
                v_file = None
                i_file = None
                for f in out_files:
                    if "Vocals" in f or "vocals" in f.lower():
                        v_file = os.path.join(output_dir, f)
                    elif "Instrumental" in f or "instrumental" in f.lower() or "Other" in f:
                        i_file = os.path.join(output_dir, f)
                
                if not v_file and len(out_files) >= 2:
                    v_file = os.path.join(output_dir, out_files[1])
                if not i_file and len(out_files) >= 1:
                    i_file = os.path.join(output_dir, out_files[0])
                    
                if v_file and os.path.exists(v_file):
                    vocal_chunks.append(AudioSegment.from_file(v_file))
                    # Cleanup the separated chunk file to save disk space
                    try: os.remove(v_file)
                    except: pass
                if i_file and os.path.exists(i_file):
                    inst_chunks.append(AudioSegment.from_file(i_file))
                    # Cleanup the separated chunk file
                    try: os.remove(i_file)
                    except: pass
                    
                    
                # Free VRAM/RAM reference for garbage collector
                gc.collect()
            
            if log_callback:
                log_callback(f"[*] Đang ghép các phân đoạn âm thanh lại...\n")
                
            final_vocal = AudioSegment.empty()
            for vc in vocal_chunks: final_vocal += vc
            
            final_inst = AudioSegment.empty()
            for ic in inst_chunks: final_inst += ic
            
            import uuid
            base_name = os.path.basename(audio_path).split('_audio')[0]
            base_id = uuid.uuid4().hex[:4]
            final_v_path = os.path.join(output_dir, f"{base_name}_audio_Vocals_{base_id}.wav")
            final_i_path = os.path.join(output_dir, f"{base_name}_audio_Instrumental_{base_id}.wav")
            
            final_vocal.export(final_v_path, format="wav")
            final_inst.export(final_i_path, format="wav")
            
            try:
                shutil.rmtree(tmp_dir)
            except:
                pass
                
            if log_callback:
                log_callback(f"[*] Đã tách giọng nói bằng AI thành công (Chunking).\n")
                
            return final_v_path, final_i_path
        
    except Exception as e:
        if log_callback:
            log_callback(f"[!] Lỗi khi tách âm thanh AI: {e}. Sẽ sử dụng âm thanh gốc.\n")
        return audio_path, None

def release_audio_separator(log_callback=None):
    """
    Giải phóng toàn bộ mô hình UVR5 Separator (ONNX Runtime / CUDA context)
    và thu hồi bộ nhớ VRAM/RAM để chuẩn bị tài nguyên cho các tác vụ tiếp theo (như VieNeu-TTS).
    """
    global _separator_instance
    with _separator_lock:
        if _separator_instance is not None:
            try:
                del _separator_instance
            except Exception:
                pass
            _separator_instance = None
            
            import gc
            gc.collect()
            
            try:
                import torch
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
                    torch.cuda.ipc_collect()
            except Exception:
                pass
                
            if log_callback:
                log_callback("[*] [VRAM] Đã giải phóng hoàn toàn mô hình UVR5 và bộ nhớ VRAM.\n")
            return True
    return False
