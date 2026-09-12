import os
from app.services.processor.steps.base_step import ProcessorStep
from app.models.history import ProcessStatus

class RenderStep(ProcessorStep):
    def execute(self, context: dict) -> bool:
        db = context['db']
        record = context['record']
        config = context['config']
        video_path = context['video_path']
        vi_srt = context['vi_srt']
        out_video_path = context['out_video_path']
        log_callback = context['log_callback']
        sync_redis = context['sync_redis']
        video_editor = context['video_editor']
        instrumental_audio_path = context.get('instrumental_audio_path')
        vocal_audio_path = context.get('vocal_ref_path')
        tts_audio_path = context.get('tts_audio_path')

        log_callback(f"[*] Bước 4: Đang render video kết quả...\n", progress=40.0)
        
        try:
            record.status = ProcessStatus.RENDERING
            db.commit()
            
            # Xử lý TTS file nếu bị rỗng hoặc không chọn voice
            final_tts_audio = tts_audio_path
            if final_tts_audio and (not os.path.exists(final_tts_audio) or os.path.getsize(final_tts_audio) == 0):
                final_tts_audio = None
            if config.voice_mode == "none":
                final_tts_audio = None
                
            srt_to_use = vi_srt if config.enable_subtitles else None

            from app.services.processor.colab_bridge import ColabBridge
            rendered_by_colab = False

            if ColabBridge.is_enabled():
                try:
                    log_callback("[*] ☁️ [Colab T4] Đang gửi dữ liệu sang Google Colab để render NVENC...\n", progress=50.0)
                    speed_val = 1.05 if getattr(config, 'opt_speed', False) else 1.0
                    zoom_val = 1.03 if getattr(config, 'opt_zoom', False) else 1.0
                    audio_for_render = final_tts_audio or instrumental_audio_path
                    ColabBridge.render_video_nvenc(
                        video_path=video_path,
                        output_video_path=out_video_path,
                        audio_path=audio_for_render,
                        srt_path=srt_to_use,
                        speed=speed_val,
                        flip_horizontal=getattr(config, 'flip_video', False),
                        zoom_factor=zoom_val,
                        watermark_text=config.watermark_text if getattr(config, 'watermark_type', '') == 'text' else None
                    )
                    log_callback("[+] ☁️ [Colab T4] Đã render NVENC hoàn tất!\n", progress=95.0)
                    rendered_by_colab = True
                except Exception as colab_err:
                    log_callback(f"[!] [Colab T4] Cảnh báo NVENC: {colab_err}. Tự động chuyển sang render FFMPEG Local...\n")

            if not rendered_by_colab:
                video_editor.burn_subtitles(
                    input_video=video_path,
                    srt_file=srt_to_use,
                    output_video=out_video_path,
                    tts_audio=final_tts_audio,
                    bgm_audio=instrumental_audio_path,
                    vocal_audio=vocal_audio_path,
                    config=config,
                    log_callback=log_callback
                )
            
            record.final_video_path = out_video_path
            record.status = ProcessStatus.COMPLETED
            record.error_message = None
            db.commit()
            log_callback(f"[*] Đã render xong video: {out_video_path}\n", progress=100.0)
            
        except Exception as e:
            if "bị hủy" in str(e):
                log_callback(f"[*] Tiến trình render đã bị hủy bởi người dùng.\n")
                record.status = ProcessStatus.PAUSED
                db.commit()
                return False
            else:
                log_callback(f"[!] Lỗi Render: {e}\n")
                raise e

        return True
