import os
import json
from app.db.session import SessionLocal
from app.models.history import VideoHistory, ProcessStatus
from app.core.redis_pool import get_sync_redis
from app.services.processor.transcriber import Transcriber
from app.services.processor.translator import Translator
from app.services.processor.video_editor import VideoEditor
from app.services.processor.tts_generator import TTSGenerator
from app.services.processor.steps.transcribe_step import TranscribeStep
from app.services.processor.steps.translate_tts_step import TranslateAndTTSStep
from app.services.processor.steps.render_step import RenderStep

sync_redis = get_sync_redis(decode_responses=True)

def clean_error_message(err_msg: str) -> str:
    if not err_msg:
        return "Lỗi không xác định"
    
    # Xử lý lỗi API Quota phổ biến
    if "RESOURCE_EXHAUSTED" in err_msg or "quota exceeded" in err_msg.lower() or "limit exceeded" in err_msg.lower():
        return "Lỗi API: Đã hết hạn mức sử dụng hoặc vượt quá giới hạn lượt gọi (Quota Exceeded / Rate Limit)."
        
    if "api key" in err_msg.lower() and ("invalid" in err_msg.lower() or "not found" in err_msg.lower() or "chưa cấu hình" in err_msg.lower()):
        return "Lỗi API Key: Khóa API không hợp lệ hoặc chưa được cấu hình đúng."
        
    if "connection" in err_msg.lower() or "timeout" in err_msg.lower() or "cannot connect" in err_msg.lower():
        return "Lỗi kết nối: Không thể kết nối tới dịch vụ AI (Mạng chập chờn hoặc Timeout)."

    # Giới hạn độ dài tối đa 250 ký tự
    if len(err_msg) > 250:
        return err_msg[:250] + "..."
    return err_msg

class ProcessorPipeline:
    def __init__(self):
        self.transcriber = Transcriber()
        self.translator = Translator()
        self.editor = VideoEditor()
        self.tts = TTSGenerator()

    def process_video(self, video_path: str, log_callback, config):
        if not os.path.exists(video_path):
            log_callback(f"[!] Lỗi: Không tìm thấy file {video_path}\n")
            return

        base_dir = os.path.dirname(video_path)
        base_name = os.path.basename(video_path).split('.')[0]
        
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../"))
        data_dir = os.path.join(project_root, "data")
        subtitles_dir = os.path.join(data_dir, "subtitles")
        audio_dir = os.path.join(data_dir, "audio")
        processed_dir = os.path.join(data_dir, "processed_videos")
        
        os.makedirs(subtitles_dir, exist_ok=True)
        os.makedirs(audio_dir, exist_ok=True)
        os.makedirs(processed_dir, exist_ok=True)
        
        orig_srt = os.path.join(subtitles_dir, f"{base_name}_orig.srt")
        vi_srt = os.path.join(subtitles_dir, f"{base_name}_vi.srt")
        output_video = os.path.join(processed_dir, f"{base_name}_processed.mp4")
        audio_tmp = os.path.join(audio_dir, f"{base_name}_audio.mp3")
        # Init DB record first so it can be used for TTS cache logic
        db = SessionLocal()
        try:
            record = db.query(VideoHistory).filter(VideoHistory.raw_video_path.like(f"%{base_name}%")).first()
            if not record:
                record = VideoHistory(
                    original_name=f"{base_name}.mp4",
                    source="Unknown",
                    raw_video_path=video_path,
                    status=ProcessStatus.PENDING
                )
                db.add(record)
                db.commit()
                db.refresh(record)

            audio_tts_path = record.audio_tts_path if record.audio_tts_path and not record.audio_tts_path.endswith("_tts.mp3") else os.path.join(audio_dir, f"{base_name}_tts.mp3")
            tts_meta_path = os.path.join(os.path.dirname(audio_tts_path), f"{base_name}_tts_meta.json")
            
            import json
            need_tts_regen = True
            if os.path.exists(tts_meta_path):
                try:
                    with open(tts_meta_path, 'r', encoding='utf-8') as f:
                        meta = json.load(f)
                        if meta.get("voice_mode") == config.voice_mode:
                            need_tts_regen = False
                except Exception:
                    pass
            
            # Cập nhật cache phụ đề và TTS nếu có thay đổi voice_mode
            if need_tts_regen:
                if os.path.exists(audio_tts_path):
                    try: os.remove(audio_tts_path)
                    except: 
                        import time
                        audio_tts_path = os.path.join(os.path.dirname(audio_tts_path), f"{base_name}_tts_{int(time.time())}.mp3")
                        record.audio_tts_path = audio_tts_path
                        db.commit()
            
            # Nếu cờ force_render bật, chỉ xóa file video output cũ để tiết kiệm thời gian dịch thuật cho các bước sau
            if config.force_render:
                if os.path.exists(output_video):
                    try:
                        os.remove(output_video)
                        log_callback(f"[*] Force Render: Đã xóa video cũ {os.path.basename(output_video)}.\n")
                    except Exception as e:
                        log_callback(f"[!] Force Render: Không thể xóa video cũ {os.path.basename(output_video)}: {e}\n")

            # Inject custom SRT if provided
            if getattr(config, 'use_custom_srt', False) and getattr(config, 'custom_srt', None):
                with open(vi_srt, 'w', encoding='utf-8') as f:
                    f.write(config.custom_srt)
                with open(orig_srt, 'w', encoding='utf-8') as f:
                    f.write(config.custom_srt)
                # Force TTS regeneration if custom SRT is used
                if os.path.exists(audio_tts_path):
                    try: os.remove(audio_tts_path)
                    except: 
                        import time
                        audio_tts_path = os.path.join(os.path.dirname(audio_tts_path), f"{base_name}_tts_{int(time.time())}.mp3")
                        record.audio_tts_path = audio_tts_path
                        db.commit()
                if os.path.exists(tts_meta_path):
                    try: os.remove(tts_meta_path)
                    except: pass
                log_callback(f"[*] Sử dụng Phụ đề Tùy chỉnh. Bỏ qua Dịch tự động.\n")

            if sync_redis.get(f"pause_video_{base_name}") == "1":
                log_callback(f"[*] Tiến trình đã được tạm dừng bởi người dùng.\n")
                record.status = ProcessStatus.PAUSED
                db.commit()
                return

            if os.path.exists(output_video) and os.path.getsize(output_video) > 0 and not config.force_render:
                log_callback(f"[*] Bỏ qua render do video đã tồn tại.\n", progress=100.0)
                record.final_video_path = output_video
                record.status = ProcessStatus.COMPLETED
                db.commit()
                log_callback(f"[*] Video đã hoàn tất từ trước!\n[*] File đầu ra: {output_video}\n")
                return

            context = {
                'db': db,
                'record': record,
                'config': config,
                'base_name': base_name,
                'video_path': video_path,
                'audio_tmp': audio_tmp,
                'audio_dir': audio_dir,
                'orig_srt': orig_srt,
                'vi_srt': vi_srt,
                'tts_audio': audio_tts_path,
                'out_video_path': output_video,
                'log_callback': log_callback,
                'sync_redis': sync_redis,
                'transcriber': self.transcriber,
                'translator': self.translator,
                'tts': self.tts,
                'video_editor': self.editor
            }

            steps = [
                TranscribeStep(),
                TranslateAndTTSStep(),
                RenderStep()
            ]

            for step in steps:
                if sync_redis.get(f"pause_video_{base_name}") in (b"1", "1", 1):
                    log_callback(f"[*] Tiến trình đã được tạm dừng bởi người dùng.\n")
                    record.status = ProcessStatus.PAUSED
                    db.commit()
                    return
                if not step.execute(context):
                    break
                    
        except Exception as e:
            import traceback
            traceback.print_exc()
            is_canceled = "bị hủy bởi người dùng" in str(e) or sync_redis.get(f"pause_video_{base_name}") in (b"1", "1", 1)
            record.status = ProcessStatus.PAUSED if is_canceled else ProcessStatus.FAILED
            record.error_message = clean_error_message(f"Pipeline Error: {str(e)}") if not is_canceled else None
            db.commit()
            if is_canceled:
                log_callback(f"[*] Tiến trình đã được tạm dừng bởi người dùng.\n")
            else:
                log_callback(f"[!] Lỗi Pipeline: {e}\n")
        finally:
            db.close()
