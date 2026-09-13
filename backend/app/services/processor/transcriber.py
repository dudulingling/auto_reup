from faster_whisper import WhisperModel
import os
import subprocess
from dotenv import load_dotenv
from app.core.security import decrypt_data

ENV_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../data/.env"))

# Global Cache for Whisper and Pyannote
_whisper_instance = None
_whisper_lock = __import__('threading').Lock()
_pyannote_instance = None
_pyannote_lock = __import__('threading').Lock()

class GroqQuotaExceeded(Exception):
    pass

class Transcriber:
    def __init__(self, model_size="base"):
        load_dotenv(ENV_PATH, override=True)
        self.use_groq = os.getenv("USE_GROQ", "False").lower() == "true"
        self.groq_api_key = decrypt_data(os.getenv("GROQ_API_KEY", ""))
        use_gpu_env = os.getenv("USE_GPU_ACCELERATION")
        if use_gpu_env is not None:
            self.use_gpu = use_gpu_env.lower() == "true"
        else:
            try:
                import torch
                self.use_gpu = torch.cuda.is_available()
            except Exception:
                self.use_gpu = False
        self.model_size = model_size
        
        if self.use_groq and not self.groq_api_key:
            # Fallback nếu bật Groq nhưng quên nhập Key
            self.use_groq = False

    def _get_whisper_model(self):
        global _whisper_instance
        with _whisper_lock:
            if _whisper_instance is None:
                device = "cuda" if self.use_gpu else "cpu"
                compute_type = "float16" if device == "cuda" else "int8"
                try:
                    print(f"Initializing WhisperModel '{self.model_size}' on '{device}' (compute_type={compute_type})...")
                    _whisper_instance = WhisperModel(self.model_size, device=device, compute_type=compute_type)
                    print(f"WhisperModel '{self.model_size}' successfully initialized on '{device}'.")
                except Exception as e:
                    if device == "cuda":
                        print(f"Warning: Failed to load WhisperModel on GPU/CUDA: {e}. Falling back to CPU...")
                        try:
                            _whisper_instance = WhisperModel(self.model_size, device="cpu", compute_type="int8")
                            print("WhisperModel successfully initialized on CPU fallback.")
                        except Exception as fallback_err:
                            print(f"Critical Error: Failed to initialize WhisperModel on CPU fallback: {fallback_err}")
                            raise fallback_err
                    else:
                        raise e
        return _whisper_instance
            
    def _extract_audio_for_api(self, source_audio_path: str) -> str:
        audio_path = source_audio_path + ".temp.wav"
        import imageio_ffmpeg
        ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
        cmd = [
            ffmpeg_exe, "-y", "-i", source_audio_path, 
            "-vn", "-acodec", "pcm_s16le", "-ar", "16000", "-ac", "1",
            audio_path
        ]
        
        try:
            subprocess.run(cmd, check=True, capture_output=True, text=True, encoding='utf-8', errors='replace')
        except subprocess.CalledProcessError as e:
            raise Exception(f"Lỗi khi trích xuất âm thanh từ video cho Groq API: {e.stderr}")
            
        if not os.path.exists(audio_path):
            raise Exception(f"Lỗi: File audio trích xuất không tồn tại ({audio_path})")
            
        file_size = os.path.getsize(audio_path)
        if file_size < 1000:
            raise Exception(f"Lỗi: File audio trích xuất quá nhỏ ({file_size} bytes). FFmpeg không trích xuất được âm thanh từ video này.")
            
        print(f"[*] Trích xuất âm thanh thành công, kích thước: {file_size / 1024:.2f} KB")
        return audio_path

    def _extract_audio_mp3(self, source_audio_path: str) -> str:
        audio_path = source_audio_path + ".temp.mp3"
        import imageio_ffmpeg
        ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
        cmd = [
            ffmpeg_exe, "-y", "-i", source_audio_path, 
            "-vn", "-acodec", "libmp3lame", "-ar", "16000", "-ac", "1", "-q:a", "5",
            audio_path
        ]
        
        try:
            subprocess.run(cmd, check=True, capture_output=True, text=True, encoding='utf-8', errors='replace')
        except subprocess.CalledProcessError as e:
            raise Exception(f"Lỗi khi trích xuất mp3 từ video: {e.stderr}")
            
        if not os.path.exists(audio_path):
            raise Exception(f"Lỗi: File mp3 trích xuất không tồn tại ({audio_path})")
            
        return audio_path

    def transcribe_to_words(self, media_path: str, use_bcut: bool = False, initial_prompt: str = None) -> list:
        """Transcribe and return a list of word-level dictionaries: [{'word': '...', 'start': 0.0, 'end': 0.5}]"""
        if use_bcut:
            try:
                print("[Transcriber] Attempting to transcribe using Bcut ASR...")
                mp3_path = self._extract_audio_mp3(media_path)
                from app.services.processor.bcut_asr import BcutASR
                bcut = BcutASR(mp3_path)
                words = bcut.run()
                if os.path.exists(mp3_path):
                    os.remove(mp3_path)
                return words
            except Exception as e:
                print(f"[!] Bcut ASR failed: {e}. Falling back to Whisper...")
                
        # Fallback to local faster-whisper which supports word_timestamps
        print(f"[Transcriber] Transcribing with local Whisper (word-level). Prompt: {initial_prompt}")
        model = self._get_whisper_model()
        
        transcribe_kwargs = {
            "beam_size": 5,
            "vad_filter": True,
            "vad_parameters": dict(min_silence_duration_ms=500),
            "word_timestamps": True,
            "condition_on_previous_text": False
        }
        if initial_prompt:
            transcribe_kwargs["initial_prompt"] = initial_prompt
            
        segments, info = model.transcribe(
            media_path, 
            **transcribe_kwargs
        )
        
        words = []
        for segment in segments:
            if segment.words:
                for w in segment.words:
                    word_text = w.word.strip()
                    if word_text:
                        words.append({
                            "word": word_text,
                            "start": w.start,
                            "end": w.end
                        })
            else:
                # Fallback if words are missing (shouldn't happen with word_timestamps=True)
                words.append({
                    "word": segment.text.strip(),
                    "start": segment.start,
                    "end": segment.end
                })
        return words

    def transcribe(self, media_path: str, output_srt_path: str, initial_prompt: str = None):
        if self.use_groq:
            try:
                print("Attempting to transcribe using Groq API...")
                srt_path = self._transcribe_groq(media_path, output_srt_path, initial_prompt)
            except Exception as e:
                print(f"[!] Lỗi khi dùng Groq API: {e}. Đang tự động chuyển sang dùng Offline Whisper (Local)...")
                # Xóa file audio tạm nếu còn sót lại
                temp_audio = media_path + ".temp.wav"
                if os.path.exists(temp_audio):
                    try:
                        os.remove(temp_audio)
                    except:
                        pass
                srt_path = self._transcribe_offline(media_path, output_srt_path, initial_prompt)
        else:
            srt_path = self._transcribe_offline(media_path, output_srt_path, initial_prompt)
            
        # Tự động Diarization nếu được bật
        if os.getenv("ENABLE_DIARIZATION", "False").lower() == "true":
            self._apply_diarization(media_path, srt_path)
            
        return srt_path
        
    def _apply_diarization(self, media_path: str, srt_path: str):
        try:
            hf_token = decrypt_data(os.getenv("HF_TOKEN", ""))
            if not hf_token:
                print("Skipping Diarization: HF_TOKEN is not configured.")
                return
                
            from pyannote.audio import Pipeline
            import torch
            import pysrt
            
            global _pyannote_instance
            with _pyannote_lock:
                if _pyannote_instance is None:
                    print("Loading Pyannote Diarization Pipeline into memory...")
                    device = torch.device("cuda" if self.use_gpu else "cpu")
                    pipeline = Pipeline.from_pretrained("pyannote/speaker-diarization-3.1", use_auth_token=hf_token)
                    pipeline.to(device)
                    _pyannote_instance = pipeline
                else:
                    print("Using cached Pyannote Diarization Pipeline...")
            
            print("Running Pyannote Diarization...")
            diarization = _pyannote_instance(media_path)
            
            # Đọc file srt vừa tạo
            subs = pysrt.open(srt_path, encoding="utf-8")
            
            # Ánh xạ Speaker -> M hoặc F. SPEAKER_00 -> M, SPEAKER_01 -> F, v.v.
            speaker_map = {}
            gender_cycle = ["M", "F"]
            
            for sub in subs:
                start_sec = sub.start.ordinal / 1000.0
                end_sec = sub.end.ordinal / 1000.0
                mid_sec = (start_sec + end_sec) / 2.0
                
                # Tìm speaker có mặt tại mid_sec
                assigned_speaker = None
                for turn, _, speaker in diarization.itertracks(yield_label=True):
                    if turn.start <= mid_sec <= turn.end:
                        assigned_speaker = speaker
                        break
                        
                if assigned_speaker:
                    if assigned_speaker not in speaker_map:
                        speaker_map[assigned_speaker] = gender_cycle[len(speaker_map) % 2]
                    
                    gender_tag = speaker_map[assigned_speaker]
                    # Chèn tag [M] hoặc [F] vào đầu câu nếu chưa có
                    if not sub.text.startswith("[M]") and not sub.text.startswith("[F]"):
                        sub.text = f"[{gender_tag}] {sub.text}"
                        
            subs.save(srt_path, encoding="utf-8")
            print("Diarization completed. Tags injected into SRT.")
            
        except Exception as e:
            print(f"Diarization failed: {e}")

    def _transcribe_groq(self, media_path: str, output_srt_path: str, initial_prompt: str = None):
        try:
            from groq import Groq
            client = Groq(api_key=self.groq_api_key)
            audio_path = self._extract_audio_for_api(media_path)
            
            groq_kwargs = {
                "model": "whisper-large-v3",
                "temperature": 0.0,
                "response_format": "verbose_json",
                "timeout": 300
            }
            if initial_prompt:
                groq_kwargs["prompt"] = initial_prompt
                
            with open(audio_path, "rb") as file:
                transcription = client.audio.transcriptions.create(
                    file=("audio.wav", file, "audio/wav"),
                    **groq_kwargs
                )
            
            # Xóa file audio tạm
            if os.path.exists(audio_path):
                os.remove(audio_path)
                
            # Tạo SRT
            with open(output_srt_path, "w", encoding="utf-8") as f:
                idx = 1
                for segment in transcription.segments:
                    sub_segments = self._split_long_segment(segment["start"], segment["end"], segment["text"])
                    for (s_start, s_end, s_text) in sub_segments:
                        start_str = self._format_timestamp(s_start)
                        end_str = self._format_timestamp(s_end)
                        f.write(f"{idx}\n")
                        f.write(f"{start_str} --> {end_str}\n")
                        f.write(f"{s_text}\n\n")
                        idx += 1
                    
            return output_srt_path
            
        except Exception as e:
            error_str = str(e).lower()
            if "rate limit" in error_str or "quota" in error_str or "429" in error_str or "402" in error_str:
                raise GroqQuotaExceeded("GROQ_LIMIT_EXCEEDED")
            raise e

    def _transcribe_offline(self, media_path: str, output_srt_path: str, initial_prompt: str = None):
        model = self._get_whisper_model()
        
        transcribe_kwargs = {
            "beam_size": 5,
            "vad_filter": True,
            "vad_parameters": dict(min_silence_duration_ms=500),
            "word_timestamps": True,
            "condition_on_previous_text": False
        }
        if initial_prompt:
            transcribe_kwargs["initial_prompt"] = initial_prompt
            
        segments, info = model.transcribe(
            media_path, 
            **transcribe_kwargs
        )
        
        with open(output_srt_path, "w", encoding="utf-8") as f:
            idx = 1
            for segment in segments:
                sub_segments = self._split_long_segment(segment.start, segment.end, segment.text)
                for (s_start, s_end, s_text) in sub_segments:
                    start_str = self._format_timestamp(s_start)
                    end_str = self._format_timestamp(s_end)
                    f.write(f"{idx}\n")
                    f.write(f"{start_str} --> {end_str}\n")
                    f.write(f"{s_text}\n\n")
                    idx += 1
                
        return output_srt_path

    def _format_timestamp(self, seconds: float) -> str:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds - int(seconds)) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"

    def _split_long_segment(self, start: float, end: float, text: str):
        import re
        text = text.strip()
        # Tách theo dấu gạch ngang (đại diện cho hội thoại người khác nhau)
        text = re.sub(r'(^|\s+)-\s+', r'\n- ', text).strip()
        
        # Tách theo dấu kết thúc câu nếu đoạn quá dài (> 3 giây)
        if (end - start) > 3.0:
            text = re.sub(r'([。！？\!\?])\s*', r'\1\n', text).strip()
            
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        
        if len(lines) <= 1:
            return [(start, end, lines[0] if lines else text)]
            
        total_len = sum(len(line) for line in lines)
        total_duration = end - start
        
        result = []
        current_time = start
        for line in lines:
            duration = (len(line) / total_len) * total_duration if total_len > 0 else 0
            line_end = current_time + duration
            result.append((current_time, line_end, line))
            current_time = line_end
            
        return result
