import os
import json
import threading
import concurrent.futures

# --- FIX CUDNN DLL CONFLICT ---
# Import torch BEFORE faster_whisper/ctranslate2 (imported via pipeline)
# so PyTorch loads its own full cudnn64_9.dll instead of ctranslate2's stripped version.
import torch
import torch.nn as nn
torch.backends.cuda.enable_cudnn_sdp(False)
torch.backends.cuda.enable_flash_sdp(False)
torch.backends.cuda.enable_mem_efficient_sdp(False)

from app.core.celery_app import celery_app
from app.services.processor.pipeline import ProcessorPipeline
from app.core.logger import get_logger
from app.core.redis_pool import get_sync_redis
from celery.exceptions import MaxRetriesExceededError

logger = get_logger(__name__)

# Thread-safe singleton for ProcessorPipeline (heavy AI model loading)
_pipeline_lock = threading.Lock()
_pipeline_instance = None


def _get_pipeline(log_callback=None):
    """Get or create the ProcessorPipeline singleton in a thread-safe manner."""
    global _pipeline_instance
    if _pipeline_instance is None:
        with _pipeline_lock:
            # Double-checked locking
            if _pipeline_instance is None:
                # --- PYTORCH 2.3.1 POLYFILL: nn.RMSNorm (added in PyTorch 2.4) ---
                # Required by VieNeu TTS model on legacy GPU (GTX 1050 / sm_61)
                if not hasattr(nn, 'RMSNorm'):
                    class _RMSNorm(nn.Module):
                        def __init__(self, normalized_shape, eps=1e-6):
                            super().__init__()
                            if isinstance(normalized_shape, int):
                                normalized_shape = (normalized_shape,)
                            self.weight = nn.Parameter(torch.ones(normalized_shape))
                            self.eps = eps

                        def forward(self, x):
                            variance = x.float().pow(2).mean(-1, keepdim=True)
                            return (self.weight * x * torch.rsqrt(variance + self.eps)).to(x.dtype)

                    nn.RMSNorm = _RMSNorm
                # -----------------------------------------------------------------
                
                if log_callback:
                    log_callback("[System] Đang nạp AI Models vào bộ nhớ tiến trình (chỉ chạy 1 lần)...\n")
                _pipeline_instance = ProcessorPipeline()
    return _pipeline_instance


@celery_app.task(bind=True, name="processor_tasks.process_video", max_retries=3)
def process_video_task(
    self,
    video_paths: list,
    voice_mode: str,
    bg_volume: int,
    vocal_volume: int,
    flip_video: bool = False,
    force_render: bool = False,
    subtitle_style: str = "black_white",
    opt_zoom: bool = False,
    opt_color: bool = False,
    opt_noise: bool = False,
    opt_pitch: bool = False,
    opt_speed: bool = False,
    opt_reverb: bool = False,
    opt_vignette: bool = False,
    opt_random_combo: bool = False,
    subtitle_text_color: str = "#000000",
    subtitle_bg_color: str = "#FFFFFF",
    subtitle_font_size: int = 8,
    subtitle_margin_v: int = 40,
    subtitle_bg_padding: int = 2,
    subtitle_bg_opacity: int = 100,
    watermark_type: str = "none",
    watermark_text: str = None,
    watermark_image_path: str = None,
    watermark_x: float = 50.0,
    watermark_y: float = 50.0,
    watermark_size: float = 20.0,
    watermark_color: str = "#FFFFFF",
    watermark_opacity: float = 50.0,
    subtitle_font_family: str = "Liberation Sans",
    enable_subtitles: bool = True,
    mask_enabled: bool = False,
    mask_x: float = 10.0,
    mask_y: float = 10.0,
    mask_width: float = 20.0,
    mask_height: float = 15.0,
    mask_type: str = "color",
    mask_color: str = "#000000",
    masks: list = None,
    custom_srt: str = None,
    use_custom_srt: bool = False,
    use_bcut_asr: bool = False,
    use_llm_segmentation: bool = False,
    whisper_prompt: str = None,
):
    task_id = self.request.id
    channel = f"task_log_{task_id}"

    redis_client = get_sync_redis()

    # Clean up old log list
    redis_client.delete(channel)

    def log_callback(msg: str, progress: float = None):
        payload = {"log": msg.strip()}
        if progress is not None:
            payload["progress"] = progress

        redis_client.rpush(channel, json.dumps(payload))
        if progress is not None:
            logger.info(f"[{task_id}] {msg.strip()} (Progress: {progress}%)")
        else:
            logger.info(f"[{task_id}] {msg.strip()}")

    try:
        pipeline = _get_pipeline(log_callback)

        from dotenv import load_dotenv
        load_dotenv(override=True)
        concurrency = int(os.getenv("AI_CONCURRENCY_LIMIT", 1))

        log_callback(f"[System] Chế độ đa luồng đang bật: {concurrency} luồng song song\n")

        from app.schemas.processor_config import VideoProcessingConfig
        
        # Collect all process kwargs once to construct the config object
        config = VideoProcessingConfig(
            voice_mode=voice_mode,
            bg_volume=bg_volume,
            vocal_volume=vocal_volume,
            flip_video=flip_video,
            force_render=force_render,
            subtitle_style=subtitle_style,
            opt_zoom=opt_zoom,
            opt_color=opt_color,
            opt_noise=opt_noise,
            opt_pitch=opt_pitch,
            opt_speed=opt_speed,
            opt_reverb=opt_reverb,
            opt_vignette=opt_vignette,
            opt_random_combo=opt_random_combo,
            subtitle_text_color=subtitle_text_color,
            subtitle_bg_color=subtitle_bg_color,
            subtitle_font_size=subtitle_font_size,
            subtitle_margin_v=subtitle_margin_v,
            subtitle_bg_padding=subtitle_bg_padding,
            subtitle_bg_opacity=subtitle_bg_opacity,
            watermark_type=watermark_type,
            watermark_text=watermark_text,
            watermark_image_path=watermark_image_path,
            watermark_x=watermark_x,
            watermark_y=watermark_y,
            watermark_size=watermark_size,
            watermark_color=watermark_color,
            watermark_opacity=watermark_opacity,
            subtitle_font_family=subtitle_font_family,
            enable_subtitles=enable_subtitles,
            mask_enabled=mask_enabled,
            mask_x=mask_x,
            mask_y=mask_y,
            mask_width=mask_width,
            mask_height=mask_height,
            mask_type=mask_type,
            mask_color=mask_color,
            masks=masks if masks else [],
            custom_srt=custom_srt,
            use_custom_srt=use_custom_srt,
            use_bcut_asr=use_bcut_asr,
            use_llm_segmentation=use_llm_segmentation,
            whisper_prompt=whisper_prompt
        )

        def process_single(vp):
            base_name = os.path.basename(vp).split('.')[0]
            try:
                # 1. Kiểm tra nhanh cờ dừng từ Redis
                pause_flag = redis_client.get(f"pause_video_{base_name}")
                if pause_flag in (b"1", "1"):
                    log_callback(f"[System] Video {base_name} đã nhận cờ Dừng trước đó. Bỏ qua.\n")
                    logger.info(f"Video {base_name} có cờ pause_video=1, bỏ qua.")
                    return

                # 2. Kiểm tra trạng thái DB để chặn triệt để task tồn dư khi restart server
                from app.db.session import get_db_session
                from app.models.history import VideoHistory, ProcessStatus
                with get_db_session() as db:
                    record = db.query(VideoHistory).filter(VideoHistory.raw_video_path.like(f"%{base_name}%")).first()
                    if record and record.status in [ProcessStatus.PAUSED, ProcessStatus.FAILED, ProcessStatus.COMPLETED]:
                        log_callback(f"[System] Video {base_name} đang ở trạng thái '{record.status}'. Hủy xử lý task tồn dư.\n")
                        logger.info(f"Video {base_name} đang có status '{record.status}' trong DB, bỏ qua task Celery.")
                        return

                # If random combo is enabled, create a unique config per video
                video_config = config
                if opt_random_combo:
                    import random
                    random_overrides = {
                        'flip_video': random.random() < 0.5,
                        'opt_zoom': random.random() < 0.6,
                        'opt_color': random.random() < 0.6,
                        'opt_noise': random.random() < 0.4,
                        'opt_pitch': random.random() < 0.5,
                        'opt_speed': random.random() < 0.5,
                        'opt_reverb': random.random() < 0.4,
                        'opt_vignette': random.random() < 0.5,
                    }
                    video_config = config.model_copy(update=random_overrides)
                    enabled = [k for k, v in random_overrides.items() if v]
                    log_callback(f"[Random] {os.path.basename(vp)}: {', '.join(enabled) if enabled else 'none'}\n")
                pipeline.process_video(vp, log_callback, video_config)
            except Exception as e:
                error_msg = str(e)
                if "bị hủy bởi người dùng" in error_msg:
                    log_callback(f"[*] Tiến trình xử lý cho {base_name} đã dừng theo yêu cầu của người dùng.\n")
                    logger.info(f"Tiến trình xử lý {base_name} đã dừng do người dùng hủy.")
                    return

                logger.error(f"Lỗi khi xử lý {vp}: {e}")

                # Classify OOM / Resource errors for retry
                err_lower = error_msg.lower()
                if any(kw in err_lower for kw in ("memory", "resource", "os error", "killed")):
                    log_callback(f"[!] Lỗi tài nguyên hệ thống khi xử lý {vp}: {e}. Retry...\n")
                    raise  # Re-raise for outer retry
                else:
                    log_callback(f"[!] Lỗi logic/FFmpeg khi xử lý {vp}: {e}. Bỏ qua video này.\n")

        with concurrent.futures.ThreadPoolExecutor(max_workers=concurrency) as executor:
            futures = []
            for video_path in video_paths:
                log_callback(f"\n[System] Đưa vào hàng đợi: {video_path}\n")
                futures.append(executor.submit(process_single, video_path))

            for future in concurrent.futures.as_completed(futures):
                try:
                    future.result()
                except Exception as exc:
                    raise exc  # Re-raise to trigger outer retry

        log_callback("\n[System] Hoàn thành toàn bộ luồng xử lý video.\n[DONE]\n")
        return {"status": "success", "processed_count": len(video_paths)}

    except MaxRetriesExceededError:
        log_callback("[System] Hết số lần thử lại cho render video.\n[DONE]\n")
        raise
    except Exception as e:
        logger.error(f"Lỗi nghiêm trọng trong Celery Task: {str(e)}", exc_info=True)
        try:
            backoff_delays = [60, 120, 300]
            retries = self.request.retries
            delay = backoff_delays[retries] if retries < len(backoff_delays) else 300
            log_callback(f"[System] Lỗi tài nguyên: {e}. Đang thử lại lần {retries + 1} sau {delay}s...\n")
            raise self.retry(exc=e, countdown=delay)
        except MaxRetriesExceededError:
            log_callback(f"[System] Hết số lần thử lại (3 lần). Bỏ qua.\n[DONE]\n")
            return {"status": "error", "error": str(e)}
