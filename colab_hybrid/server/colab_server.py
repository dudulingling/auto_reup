import os
import shutil
import tempfile
import uuid
from typing import Optional
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from gpu_services import (
    get_gpu_info,
    WhisperGPUProcessor,
    VieneuTTSGPUProcessor,
    AudioSeparatorGPUProcessor,
    VideoEditorNVENC,
)

app = FastAPI(
    title="Auto Reup GPU Worker - Colab T4 Node",
    description="High-performance AI processing server running on Google Colab free Tesla T4 GPU",
    version="1.0.0",
)

# Enable CORS for external access from Local React UI or Local Python client
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Storage directories
STORAGE_DIR = os.getenv("STORAGE_DIR", "/content/auto_reup_storage" if os.path.exists("/content") else "./temp_storage")
OUTPUTS_DIR = os.path.join(STORAGE_DIR, "outputs")
UPLOADS_DIR = os.path.join(STORAGE_DIR, "uploads")
os.makedirs(OUTPUTS_DIR, exist_ok=True)
os.makedirs(UPLOADS_DIR, exist_ok=True)

# Mount static files to serve generated video/audio directly
app.mount("/files", StaticFiles(directory=STORAGE_DIR), name="storage_files")


class TTSRequest(BaseModel):
    text: str
    voice: str = "female"
    reference_audio_url: Optional[str] = None


@app.get("/")
@app.get("/api/gpu/health")
def health_check():
    """Returns GPU health status, VRAM usage, and capabilities."""
    gpu_info = get_gpu_info()
    return {
        "status": "online",
        "service": "Auto Reup Colab T4 GPU Worker",
        "gpu": gpu_info,
    }


@app.post("/api/gpu/transcribe")
async def transcribe_audio(
    file: UploadFile = File(...),
    model_size: str = Form("base"),
    language: Optional[str] = Form(None),
):
    """
    Transcribes uploaded audio/video using Faster-Whisper on T4 GPU (FP16).
    Returns transcript segments, full text, and SRT format string.
    """
    ext = os.path.splitext(file.filename)[1] or ".mp4"
    temp_input = os.path.join(UPLOADS_DIR, f"transcribe_{uuid.uuid4().hex}{ext}")

    try:
        with open(temp_input, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        processor = WhisperGPUProcessor(model_size=model_size)
        result = processor.transcribe(temp_input, language=language)

        # Save SRT file
        srt_filename = f"sub_{uuid.uuid4().hex[:8]}.srt"
        srt_path = os.path.join(OUTPUTS_DIR, srt_filename)
        with open(srt_path, "w", encoding="utf-8") as f:
            f.write(result["srt_content"])

        result["srt_file_url"] = f"/files/outputs/{srt_filename}"
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Whisper transcription failed: {str(e)}")
    finally:
        if os.path.exists(temp_input):
            try:
                os.remove(temp_input)
            except Exception:
                pass


@app.post("/api/gpu/tts")
async def generate_tts(
    text: str = Form(...),
    voice: str = Form("female"),
    reference_file: Optional[UploadFile] = File(None),
):
    """
    Generates Vietnamese speech using Vieneu neural TTS model on GPU.
    """
    out_filename = f"tts_{uuid.uuid4().hex[:8]}.wav"
    out_path = os.path.join(OUTPUTS_DIR, out_filename)
    ref_path = None

    try:
        if reference_file:
            ref_path = os.path.join(UPLOADS_DIR, f"ref_{uuid.uuid4().hex}.wav")
            with open(ref_path, "wb") as buffer:
                shutil.copyfileobj(reference_file.file, buffer)

        processor = VieneuTTSGPUProcessor()
        processor.synthesize(text=text, voice=voice, output_wav_path=out_path, reference_audio=ref_path)

        return FileResponse(
            out_path,
            media_type="audio/wav",
            filename=out_filename,
            headers={"X-File-Url": f"/files/outputs/{out_filename}"},
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"VieNeu TTS failed: {str(e)}")
    finally:
        if ref_path and os.path.exists(ref_path):
            try:
                os.remove(ref_path)
            except Exception:
                pass


@app.post("/api/gpu/separate-audio")
async def separate_audio(
    file: UploadFile = File(...),
):
    """
    Separates speech/vocal and background music using UVR5 AI on GPU.
    """
    ext = os.path.splitext(file.filename)[1] or ".wav"
    temp_audio = os.path.join(UPLOADS_DIR, f"sep_input_{uuid.uuid4().hex}{ext}")

    try:
        with open(temp_audio, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        sep_dir = os.path.join(OUTPUTS_DIR, f"sep_{uuid.uuid4().hex[:8]}")
        os.makedirs(sep_dir, exist_ok=True)

        processor = AudioSeparatorGPUProcessor(output_dir=sep_dir)
        res = processor.separate(temp_audio)

        vocal_rel = os.path.relpath(res["vocal_path"], STORAGE_DIR).replace("\\", "/") if res["vocal_path"] else None
        inst_rel = os.path.relpath(res["instrumental_path"], STORAGE_DIR).replace("\\", "/") if res["instrumental_path"] else None

        return {
            "status": "success",
            "vocal_url": f"/files/{vocal_rel}" if vocal_rel else None,
            "instrumental_url": f"/files/{inst_rel}" if inst_rel else None,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Audio separation failed: {str(e)}")
    finally:
        if os.path.exists(temp_audio):
            try:
                os.remove(temp_audio)
            except Exception:
                pass


@app.post("/api/gpu/render-video")
async def render_video(
    video_file: UploadFile = File(...),
    audio_file: Optional[UploadFile] = File(None),
    srt_file: Optional[UploadFile] = File(None),
    speed: float = Form(1.0),
    flip_horizontal: bool = Form(False),
    zoom_factor: float = Form(1.0),
    watermark_text: Optional[str] = Form(None),
):
    """
    Renders video using FFmpeg with NVENC hardware acceleration on T4 GPU.
    """
    vid_ext = os.path.splitext(video_file.filename)[1] or ".mp4"
    in_video_path = os.path.join(UPLOADS_DIR, f"in_vid_{uuid.uuid4().hex}{vid_ext}")
    in_audio_path = None
    in_srt_path = None

    out_vid_name = f"rendered_{uuid.uuid4().hex[:8]}.mp4"
    out_video_path = os.path.join(OUTPUTS_DIR, out_vid_name)

    try:
        with open(in_video_path, "wb") as buffer:
            shutil.copyfileobj(video_file.file, buffer)

        if audio_file:
            aud_ext = os.path.splitext(audio_file.filename)[1] or ".wav"
            in_audio_path = os.path.join(UPLOADS_DIR, f"in_aud_{uuid.uuid4().hex}{aud_ext}")
            with open(in_audio_path, "wb") as buffer:
                shutil.copyfileobj(audio_file.file, buffer)

        if srt_file:
            in_srt_path = os.path.join(UPLOADS_DIR, f"in_sub_{uuid.uuid4().hex}.srt")
            with open(in_srt_path, "wb") as buffer:
                shutil.copyfileobj(srt_file.file, buffer)

        VideoEditorNVENC.render(
            input_video=in_video_path,
            output_video=out_video_path,
            new_audio=in_audio_path,
            srt_subtitles=in_srt_path,
            speed=speed,
            flip_horizontal=flip_horizontal,
            zoom_factor=zoom_factor,
            watermark_text=watermark_text,
        )

        return FileResponse(
            out_video_path,
            media_type="video/mp4",
            filename=out_vid_name,
            headers={"X-File-Url": f"/files/outputs/{out_vid_name}"},
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"NVENC Video render failed: {str(e)}")
    finally:
        # Cleanup uploaded temp files
        for p in [in_video_path, in_audio_path, in_srt_path]:
            if p and os.path.exists(p):
                try:
                    os.remove(p)
                except Exception:
                    pass
