import asyncio
import os
import sys
import json
import time
import uuid
import shutil
from app.core.config import DATA_DIR
from fastapi import APIRouter, Request, UploadFile, File, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from app.tasks.processor_tasks import process_video_task
from app.core.logger import get_logger
from app.core.redis_pool import get_async_redis
from app.models.history import VideoHistory

logger = get_logger(__name__)
router = APIRouter()


class VideoMask(BaseModel):
    id: Optional[int] = None
    x: float
    y: float
    width: float
    height: float
    type: str
    color: str


class ProcessRequest(BaseModel):
    video_paths: list[str]
    voice_mode: str = "edge_auto"
    bg_volume: int = 10
    vocal_volume: int = 0
    flip_video: bool = False
    opt_zoom: bool = False
    opt_color: bool = False
    opt_noise: bool = False
    opt_pitch: bool = False
    opt_speed: bool = False
    opt_reverb: bool = False
    opt_vignette: bool = False
    opt_random_combo: bool = False
    force_render: bool = False
    use_bcut_asr: bool = False
    use_llm_segmentation: bool = False
    whisper_prompt: Optional[str] = None
    subtitle_style: str = "black_white"
    subtitle_font_family: str = "Liberation Sans"
    subtitle_text_color: str = "#000000"
    subtitle_bg_color: Optional[str] = "#FFFFFF"
    subtitle_font_size: Optional[int] = 8
    subtitle_margin_v: Optional[int] = 40
    subtitle_bg_padding: Optional[int] = 2
    subtitle_bg_opacity: Optional[int] = 100
    watermark_type: str = "none"
    watermark_text: Optional[str] = None
    watermark_image_path: Optional[str] = None
    watermark_x: float = 50.0
    watermark_y: float = 50.0
    watermark_size: float = 20.0
    watermark_color: str = "#FFFFFF"
    watermark_opacity: float = 50.0
    enable_subtitles: bool = True
    mask_enabled: bool = False
    mask_x: float = 10.0
    mask_y: float = 10.0
    mask_width: float = 20.0
    mask_height: float = 15.0
    mask_type: str = "color"
    mask_color: str = "#000000"
    masks: list[VideoMask] = []
    edited_subtitle: Optional[str] = None
    custom_srt: Optional[str] = None
    use_custom_srt: bool = False
    use_bcut_asr: bool = False
    use_llm_segmentation: bool = False


class PreviewRequest(ProcessRequest):
    preview_text: str = "Đây là phụ đề mẫu tự động sinh..."
    video_path: Optional[str] = None
    preview_time: float = 1.0


@router.post("/upload-logo")
async def upload_logo(file: UploadFile = File(...)):
    # Validate extension
    ext = file.filename.split(".")[-1].lower()
    if ext not in ["png", "jpg", "jpeg"]:
        raise HTTPException(status_code=400, detail="Chỉ hỗ trợ file PNG và JPG.")

    # 5MB limit
    content = await file.read()
    if len(content) > 5 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="Kích thước file không được vượt quá 5MB.")

    # Save file
    os.makedirs(os.path.join(DATA_DIR, "watermarks"), exist_ok=True)
    filename = f"logo_{uuid.uuid4().hex[:8]}.{ext}"
    filepath = os.path.join(DATA_DIR, "watermarks", filename)

    with open(filepath, "wb") as f:
        f.write(content)

    return {"status": "success", "path": filepath, "url": f"/api/files/watermarks/{filename}"}


@router.post("/upload-video")
async def upload_video(file: UploadFile = File(...)):
    # Validate extension
    ext = file.filename.split(".")[-1].lower()
    if ext not in ["mp4", "mkv", "webm", "avi", "mov", "flv"]:
        raise HTTPException(status_code=400, detail="Chỉ hỗ trợ file video (mp4, mkv, webm, avi, mov, flv).")

    # Save file
    os.makedirs(os.path.join(DATA_DIR, "raw_videos"), exist_ok=True)
    filename = f"upload_{uuid.uuid4().hex[:8]}_{file.filename}"
    filepath = os.path.join(DATA_DIR, "raw_videos", filename)

    try:
        with open(filepath, "wb") as f:
            shutil.copyfileobj(file.file, f)
    except Exception as e:
        logger.error(f"Lỗi lưu file video upload: {e}")
        raise HTTPException(status_code=500, detail=f"Không thể lưu file video: {str(e)}")

    relative_path = f"data/raw_videos/{filename}"
    return {"status": "success", "path": relative_path, "filename": file.filename}


@router.get("/test-bcut")
async def test_bcut():
    try:
        from app.services.processor.bcut_asr import test_bcut_api
        result = test_bcut_api()
        if result["status"] == "ok":
            return {"status": "success", "message": result["message"]}
        else:
            raise HTTPException(status_code=500, detail=result["message"])
    except Exception as e:
        logger.error(f"Lỗi kiểm tra Bcut API: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/preview-subtitle")
async def preview_subtitle(request: PreviewRequest):
    vp_clean = None
    if request.video_path:
        vp_clean = request.video_path.replace("\\", "/")
    elif request.video_paths and len(request.video_paths) > 0:
        vp_clean = request.video_paths[0].replace("\\", "/")
        
    if not vp_clean:
        raise HTTPException(status_code=400, detail="Thiếu đường dẫn video.")
        
    if "data/raw_videos/" in vp_clean:
        vp_clean = os.path.join(DATA_DIR, "raw_videos") + "/" + vp_clean.split("data/raw_videos/")[-1]
    
    if not os.path.exists(vp_clean):
        raise HTTPException(status_code=404, detail="Không tìm thấy video.")
        
    from app.services.processor.video_editor import VideoEditor
    editor = VideoEditor()
    
    try:
        from app.schemas.processor_config import VideoProcessingConfig
        config = VideoProcessingConfig(
            flip_video=request.flip_video,
            subtitle_style=request.subtitle_style,
            opt_zoom=request.opt_zoom,
            opt_color=request.opt_color,
            opt_noise=request.opt_noise,
            opt_pitch=request.opt_pitch,
            opt_speed=request.opt_speed,
            opt_reverb=request.opt_reverb,
            subtitle_text_color=request.subtitle_text_color,
            subtitle_bg_color=request.subtitle_bg_color,
            subtitle_font_size=request.subtitle_font_size,
            subtitle_margin_v=request.subtitle_margin_v,
            subtitle_bg_padding=request.subtitle_bg_padding,
            subtitle_bg_opacity=request.subtitle_bg_opacity,
            watermark_type=request.watermark_type,
            watermark_text=request.watermark_text,
            watermark_image_path=request.watermark_image_path,
            watermark_x=request.watermark_x,
            watermark_y=request.watermark_y,
            watermark_size=request.watermark_size,
            watermark_color=request.watermark_color,
            watermark_opacity=request.watermark_opacity,
            subtitle_font_family=request.subtitle_font_family,
            enable_subtitles=request.enable_subtitles,
            mask_enabled=request.mask_enabled,
            masks=[m.dict() for m in request.masks]
        )
        
        output_img = editor.generate_preview_frame(
            input_video=vp_clean,
            preview_text=request.preview_text,
            config=config,
            preview_time=request.preview_time
        )
        
        # Return image and delete temp file in background
        from fastapi.responses import FileResponse
        from starlette.background import BackgroundTask
        
        return FileResponse(
            output_img, 
            media_type="image/jpeg", 
            filename="preview.jpg",
            background=BackgroundTask(os.remove, output_img)
        )
    except Exception as e:
        logger.error(f"Lỗi generate preview frame: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/start")
async def start_processor(request: ProcessRequest):
    redis_client = get_async_redis()

    cleaned_paths = []
    for vp in request.video_paths:
        vp_clean = vp.replace("\\", "/")
        if "data/raw_videos/" in vp_clean:
            vp_clean = os.path.join(DATA_DIR, "raw_videos") + "/" + vp_clean.split("data/raw_videos/")[-1]
        cleaned_paths.append(vp_clean)

    logger.info(f"Nhận API request xử lý {len(cleaned_paths)} video qua Celery (Flip: {request.flip_video}, Force: {request.force_render})")

    # Clear pause flags and set PENDING status for immediate UI update
    try:
        from app.db.session import get_db_session
        from app.crud.crud_history import update_processing_config_and_status

        with get_db_session() as db:
            for vp_clean in cleaned_paths:
                base_name = os.path.basename(vp_clean).split('.')[0]
                await redis_client.delete(f"pause_video_{base_name}")

                new_config = {
                    "voice_mode": request.voice_mode,
                    "bg_volume": request.bg_volume,
                    "vocal_volume": request.vocal_volume,
                    "flip_video": request.flip_video,
                    "subtitle_style": request.subtitle_style,
                    "opt_zoom": request.opt_zoom,
                    "opt_color": request.opt_color,
                    "opt_noise": request.opt_noise,
                    "opt_pitch": request.opt_pitch,
                    "opt_speed": request.opt_speed,
                    "opt_reverb": request.opt_reverb,
                    "opt_vignette": request.opt_vignette,
                    "use_bcut_asr": request.use_bcut_asr,
                    "use_llm_segmentation": request.use_llm_segmentation,
                    "whisper_prompt": request.whisper_prompt,
                    "opt_random_combo": request.opt_random_combo,
                    "subtitle_font_family": request.subtitle_font_family,
                    "subtitle_text_color": request.subtitle_text_color,
                    "subtitle_bg_color": request.subtitle_bg_color,
                    "subtitle_font_size": request.subtitle_font_size,
                    "subtitle_margin_v": request.subtitle_margin_v,
                    "subtitle_bg_padding": request.subtitle_bg_padding,
                    "enable_subtitles": request.enable_subtitles,
                    "mask_enabled": request.mask_enabled,
                    "mask_x": request.mask_x,
                    "mask_y": request.mask_y,
                    "mask_width": request.mask_width,
                    "mask_height": request.mask_height,
                    "mask_type": request.mask_type,
                    "mask_color": request.mask_color,
                    "masks": [m.dict() for m in request.masks],
                    "watermark_type": request.watermark_type,
                    "watermark_text": request.watermark_text,
                    "watermark_image_path": request.watermark_image_path,
                    "watermark_x": request.watermark_x,
                    "watermark_y": request.watermark_y,
                    "watermark_size": request.watermark_size,
                    "watermark_color": request.watermark_color,
                    "watermark_opacity": request.watermark_opacity,
                    "custom_srt": request.custom_srt,
                    "use_custom_srt": request.use_custom_srt,
                }
                
                update_processing_config_and_status(
                    db=db, 
                    base_name=base_name, 
                    new_config=new_config, 
                    data_dir=DATA_DIR
                )
                
                # Nếu có sửa text subtitle từ UI
                if request.edited_subtitle is not None and len(cleaned_paths) == 1:
                    record = db.query(VideoHistory).filter(VideoHistory.raw_video_path.like(f"%{base_name}%")).first()
                    if record and record.srt_translated_path:
                        try:
                            new_sub = request.edited_subtitle.replace("\r\n", "\n").strip()
                            current_sub = ""
                            if os.path.exists(record.srt_translated_path):
                                with open(record.srt_translated_path, "r", encoding="utf-8") as f:
                                    current_sub = f.read().replace("\r\n", "\n").strip()
                            
                            # 1. Ghi đè file sub nếu có sự thay đổi thực sự
                            if current_sub != new_sub:
                                with open(record.srt_translated_path, "w", encoding="utf-8", newline="\n") as f:
                                    f.write(new_sub)
                                if record.srt_origin_path:
                                    with open(record.srt_origin_path, "w", encoding="utf-8", newline="\n") as f:
                                        f.write(new_sub)
                                    
                                # 2. Xoá file TTS cũ (nếu có) để ép hệ thống tạo lại audio cho sub mới
                                old_tts_path = record.audio_tts_path
                                if old_tts_path and os.path.exists(old_tts_path):
                                    try: 
                                        os.remove(old_tts_path)
                                        record.audio_tts_path = None
                                    except:
                                        import time
                                        # File bị lock bởi tiến trình khác (Windows), đổi tên path để tạo file mới
                                        dir_name = os.path.dirname(old_tts_path)
                                        base_name_rec = os.path.basename(record.raw_video_path).rsplit(".", 1)[0]
                                        record.audio_tts_path = os.path.join(dir_name, f"{base_name_rec}_tts_{int(time.time())}.mp3")
                                
                                # 3. Xoá file TTS meta (nếu có)
                                if old_tts_path:
                                    tts_meta_path = os.path.join(os.path.dirname(old_tts_path), f"{base_name}_tts_meta.json")
                                    if os.path.exists(tts_meta_path):
                                        try: os.remove(tts_meta_path)
                                        except: pass
                                
                                db.commit()
                        except Exception as file_e:
                            logger.error(f"Lỗi khi lưu edited_subtitle: {file_e}")
                            
    except Exception as e:
        logger.error(f"Lỗi update DB khi start: {e}")

    task = process_video_task.delay(
        cleaned_paths, request.voice_mode, request.bg_volume, request.vocal_volume, request.flip_video,
        request.force_render, request.subtitle_style, request.opt_zoom, request.opt_color,
        request.opt_noise, request.opt_pitch, request.opt_speed, request.opt_reverb, request.opt_vignette, request.opt_random_combo,
        request.subtitle_text_color, request.subtitle_bg_color,
        request.subtitle_font_size, request.subtitle_margin_v, request.subtitle_bg_padding,
        request.subtitle_bg_opacity, request.watermark_type, request.watermark_text,
        request.watermark_image_path, request.watermark_x, request.watermark_y,
        request.watermark_size, request.watermark_color, request.watermark_opacity,
        request.subtitle_font_family, request.enable_subtitles, request.mask_enabled,
        request.mask_x, request.mask_y, request.mask_width, request.mask_height,
        request.mask_type, request.mask_color,
        [m.dict() for m in request.masks],
        request.custom_srt, request.use_custom_srt,
        request.use_bcut_asr, request.use_llm_segmentation, request.whisper_prompt
    )
    
    # Map task ID to base names of raw videos to control cancellation for all videos in this task
    try:
        base_names = [os.path.basename(vp).split('.')[0] for vp in cleaned_paths]
        await redis_client.set(f"task_videos_{task.id}", json.dumps(base_names), ex=86400)
        for bn in base_names:
            await redis_client.set(f"video_task_{bn}", task.id, ex=86400)
    except Exception as e:
        logger.error(f"Lỗi khi lưu task videos mapping vào Redis: {e}")

    return {"status": "started", "task_id": task.id, "video_count": len(cleaned_paths)}


@router.get("/scan-folder")
async def scan_folder(folder_path: str):
    import glob
    base_raw_dir = os.path.join(DATA_DIR, "raw_videos")
    target_dir = os.path.join(base_raw_dir, folder_path).replace("\\", "/")

    if not os.path.exists(target_dir):
        return {"status": "error", "message": "Thư mục không tồn tại", "files": []}

    video_files = []
    for ext in ["*.mp4", "*.mkv", "*.webm", "*.flv"]:
        video_files.extend(glob.glob(os.path.join(target_dir, ext)))

    return {"status": "success", "files": [f.replace("\\", "/") for f in video_files]}


class PauseRequest(BaseModel):
    video_path: str


@router.post("/pause")
async def pause_processor(request: PauseRequest):
    redis_client = get_async_redis()

    vp_clean = request.video_path.replace("\\", "/")
    if "data/raw_videos/" in vp_clean:
        vp_clean = os.path.join(DATA_DIR, "raw_videos") + "/" + vp_clean.split("data/raw_videos/")[-1]

    base_name = os.path.basename(vp_clean).split('.')[0]
    await redis_client.set(f"pause_video_{base_name}", "1")
    logger.info(f"Đã đặt cờ Pause cho video: {base_name}")

    # Thu hồi Celery task nếu có
    try:
        task_id = await redis_client.get(f"video_task_{base_name}")
        if task_id:
            task_id_str = task_id.decode('utf-8') if isinstance(task_id, bytes) else str(task_id)
            from app.core.celery_app import celery_app
            celery_app.control.revoke(task_id_str, terminate=False)
            logger.info(f"Đã gửi lệnh revoke Celery task {task_id_str} cho video {base_name}")
    except Exception as rev_err:
        logger.warning(f"Không thể revoke Celery task cho {base_name}: {rev_err}")

    # Update DB to PAUSED for immediate UI feedback
    try:
        from app.db.session import get_db_session
        from app.models.history import ProcessStatus
        from app.crud.crud_history import update_status

        with get_db_session() as db:
            update_status(
                db=db, 
                base_name=base_name, 
                status=ProcessStatus.PAUSED, 
                exclude_statuses=[ProcessStatus.COMPLETED, ProcessStatus.FAILED]
            )
    except Exception as e:
        logger.error(f"Lỗi update DB khi pause: {e}")

    return {"status": "success", "message": f"Đã gửi lệnh dừng cho {base_name}"}


@router.get("/test-bcut")
async def test_bcut_api():
    """Test Bcut API Connectivity"""
    try:
        import os
        from app.services.processor.bcut_asr import BcutASR
        
        # Tạo file audio dummy (1 giây im lặng)
        dummy_audio = "dummy_test.mp3"
        import subprocess
        import imageio_ffmpeg
        ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
        
        # Tạo 1 file mp3 1 giây (im lặng)
        subprocess.run([
            ffmpeg_exe, "-y", "-f", "lavfi", "-i", "anullsrc=r=16000:cl=mono", 
            "-t", "1", "-q:a", "9", "-acodec", "libmp3lame", dummy_audio
        ], check=True, capture_output=True)
        
        try:
            bcut = BcutASR(dummy_audio)
            # Thử upload để kiểm tra token/signature
            file_url, upload_id, upload_sign = bcut._upload_file()
            if not file_url:
                raise Exception("Upload failed: No file URL returned")
        finally:
            if os.path.exists(dummy_audio):
                os.remove(dummy_audio)
                
        return {"status": "success", "message": "Bcut API connected and upload works."}
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stream/{task_id}")
async def stream_logs(task_id: str, request: Request):
    redis_client = get_async_redis()

    async def event_generator():
        channel = f"task_log_{task_id}"
        last_index = 0
        max_idle_seconds = 600  # Timeout after 10 minutes of no messages
        last_message_time = time.monotonic()

        while True:
            if await request.is_disconnected():
                logger.info("Client ngắt kết nối stream processor.")
                break

            messages = await redis_client.lrange(channel, last_index, -1)
            if messages:
                last_message_time = time.monotonic()
                for msg in messages:
                    data = str(msg)
                    for line in data.split('\n'):
                        if line.strip():
                            yield f"data: {line}\n\n"

                    if "[DONE]" in data:
                        await redis_client.expire(channel, 60)
                        return
                last_index += len(messages)
            elif time.monotonic() - last_message_time > max_idle_seconds:
                yield f'data: {{"log": "[System] Stream timeout sau {max_idle_seconds}s không hoạt động."}}\n\n'
                return

            await asyncio.sleep(0.5)

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.post("/stop/{task_id}")
async def stop_processor(task_id: str):
    logger.info(f"Yêu cầu dừng task xử lý video: {task_id}")
    from app.core.celery_app import celery_app
    import json
    try:
        celery_app.control.revoke(task_id, terminate=True)
        
        # Gửi thông điệp hủy tới kênh log stream Redis để đóng kết nối và cập nhật UI phía Client
        redis_client = get_async_redis()
        channel = f"task_log_{task_id}"
        await redis_client.rpush(channel, json.dumps({"log": "[System] Tiến trình xử lý video đã bị hủy bởi người dùng.\n[DONE]\n"}))
        
        # Đặt cờ pause cho toàn bộ video thuộc task_id để dừng nhanh
        task_videos_data = await redis_client.get(f"task_videos_{task_id}")
        if task_videos_data:
            base_names = json.loads(task_videos_data)
            for base_name in base_names:
                await redis_client.set(f"pause_video_{base_name}", "1")
                logger.info(f"Đã đặt cờ Pause cho video {base_name} qua dừng task {task_id}")
                
        return {"status": "stopped", "message": "Đã gửi lệnh hủy tiến trình xử lý."}
    except Exception as e:
        logger.error(f"Lỗi khi hủy tiến trình xử lý: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
