import os
import glob
from app.services.processor.steps.base_step import ProcessorStep
from app.models.history import ProcessStatus
from app.services.processor.transcriber import GroqQuotaExceeded
from app.services.processor.audio_extractor import extract_audio, separate_audio_with_ai

class TranscribeStep(ProcessorStep):
    def execute(self, context: dict) -> bool:
        db = context['db']
        record = context['record']
        config = context['config']
        base_name = context['base_name']
        video_path = context['video_path']
        audio_tmp = context['audio_tmp']
        audio_dir = context['audio_dir']
        orig_srt = context['orig_srt']
        log_callback = context['log_callback']
        sync_redis = context['sync_redis']
        transcriber = context['transcriber']

        # Auto-detect existing extracted audio
        inst_files = glob.glob(os.path.join(audio_dir, f"{base_name}_audio*Instrumental*.wav"))
        context['instrumental_audio_path'] = inst_files[0] if inst_files else None
        
        voc_files = glob.glob(os.path.join(audio_dir, f"{base_name}_audio*Vocals*.wav"))
        context['vocal_ref_path'] = voc_files[0] if voc_files else None

        need_subtitles_data = config.enable_subtitles or (config.voice_mode != "none")

        if not need_subtitles_data:
            return True

        if os.path.exists(orig_srt) and os.path.getsize(orig_srt) > 0:
            log_callback(f"[*] Bước 1: Tìm thấy phụ đề gốc đã tạo, bỏ qua Whisper...\n", progress=15.0)
            record.srt_origin_path = orig_srt
            db.commit()
            return True
            
        log_callback(f"[*] Bước 1: Nhận diện giọng nói (Whisper) cho video...\n", progress=5.0)
        try:
            record.status = ProcessStatus.TRANSCRIBING
            db.commit()
            
            extract_audio(video_path, audio_tmp)
            if sync_redis.get(f"pause_video_{base_name}") in (b"1", "1", 1):
                raise Exception("Tiến trình bị hủy bởi người dùng.")

            use_demucs = os.getenv("ENABLE_DEMUCS", "False").lower() == "true"
            
            vocal_audio_path = audio_tmp
            if use_demucs:
                if sync_redis.get(f"pause_video_{base_name}") in (b"1", "1", 1):
                    raise Exception("Tiến trình bị hủy bởi người dùng.")
                v_path, i_path = separate_audio_with_ai(audio_tmp, audio_dir, log_callback)
                if v_path: vocal_audio_path = v_path
                if i_path: context['instrumental_audio_path'] = i_path
                
            if sync_redis.get(f"pause_video_{base_name}") in (b"1", "1", 1):
                raise Exception("Tiến trình bị hủy bởi người dùng.")

            from app.services.processor.colab_bridge import ColabBridge
            used_colab = False

            if ColabBridge.is_enabled():
                try:
                    log_callback("[*] ☁️ [Colab T4] Đang gửi audio sang Google Colab để bóc tách Faster-Whisper...\n", progress=8.0)
                    colab_res = ColabBridge.transcribe_whisper(vocal_audio_path)
                    with open(orig_srt, "w", encoding="utf-8") as f:
                        f.write(colab_res.get("srt_content", ""))
                    log_callback(f"[+] ☁️ [Colab T4] Đã bóc tách xong phụ đề ({colab_res.get('duration', 0)}s)!\n", progress=15.0)
                    used_colab = True
                except Exception as colab_err:
                    log_callback(f"[!] [Colab T4] Cảnh báo Whisper: {colab_err}. Tự động chuyển sang Whisper Local...\n")

            if not used_colab:
                if getattr(config, 'use_bcut_asr', False) or getattr(config, 'use_llm_segmentation', False):
                    use_bcut = getattr(config, 'use_bcut_asr', False)
                    use_llm = getattr(config, 'use_llm_segmentation', False)
                    whisper_prompt = getattr(config, 'whisper_prompt', None)
                    
                    log_callback(f"[*] Đang lấy word-level timestamps (Bcut={use_bcut})...\n")
                    words = transcriber.transcribe_to_words(vocal_audio_path, use_bcut=use_bcut, initial_prompt=whisper_prompt)
                    
                    from app.services.processor.subtitle_optimizer import SubtitleOptimizer
                    optimizer = SubtitleOptimizer()
                    optimizer.optimize_and_save_srt(words, orig_srt, use_llm=use_llm)
                else:
                    whisper_prompt = getattr(config, 'whisper_prompt', None)
                    transcriber.transcribe(vocal_audio_path, orig_srt, initial_prompt=whisper_prompt)

            record.srt_origin_path = orig_srt
            db.commit()
            log_callback(f"[*] Đã tạo phụ đề gốc thành công.\n", progress=15.0)
            
            auto_clone_enabled = os.getenv("ENABLE_AUTO_VOICE_CLONE", "False").lower() == "true"
            if not auto_clone_enabled:
                if vocal_audio_path != audio_tmp and os.path.exists(vocal_audio_path):
                    try: os.remove(vocal_audio_path)
                    except: pass
            else:
                context['vocal_ref_path'] = vocal_audio_path
                
        except GroqQuotaExceeded:
            log_callback(f"[!] Groq API đã hết hạn miễn phí. Tạm dừng tiến trình.\n")
            record.status = ProcessStatus.PAUSED
            record.error_message = "GROQ_LIMIT_EXCEEDED"
            db.commit()
            return False
        except Exception as e:
            log_callback(f"[!] Lỗi Whisper: {e}\n")
            raise e

        if sync_redis.get(f"pause_video_{base_name}") == "1":
            log_callback(f"[*] Tiến trình đã được tạm dừng bởi người dùng.\n")
            record.status = ProcessStatus.PAUSED
            db.commit()
            return False

        return True
