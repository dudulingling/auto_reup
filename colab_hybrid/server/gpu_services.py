import os
import shutil
import subprocess
import threading
import torch
from typing import Dict, Any, List, Optional

# Global cache for heavy AI models
_whisper_instance = None
_whisper_lock = threading.Lock()

_vieneu_instance = None
_vieneu_lock = threading.Lock()

_separator_instance = None
_separator_lock = threading.Lock()


def get_gpu_info() -> Dict[str, Any]:
    """Inspect NVIDIA GPU availability, VRAM, and driver details."""
    cuda_available = torch.cuda.is_available()
    info = {
        "cuda_available": cuda_available,
        "device_count": torch.cuda.device_count() if cuda_available else 0,
        "device_name": torch.cuda.get_device_name(0) if cuda_available else "CPU Only",
        "pytorch_version": torch.__version__,
        "cuda_version": torch.version.cuda if cuda_available else None,
        "vram_total_mb": 0,
        "vram_free_mb": 0,
        "vram_used_mb": 0,
        "nvenc_supported": False,
    }

    if cuda_available:
        try:
            total_bytes = torch.cuda.get_device_properties(0).total_memory
            reserved_bytes = torch.cuda.memory_reserved(0)
            allocated_bytes = torch.cuda.memory_allocated(0)
            free_bytes = total_bytes - reserved_bytes

            info["vram_total_mb"] = round(total_bytes / (1024 * 1024), 2)
            info["vram_used_mb"] = round((reserved_bytes) / (1024 * 1024), 2)
            info["vram_free_mb"] = round(free_bytes / (1024 * 1024), 2)
        except Exception as e:
            info["vram_error"] = str(e)

    # Check FFmpeg NVENC encoder
    try:
        ffmpeg_bin = shutil.which("ffmpeg") or "ffmpeg"
        res = subprocess.run([ffmpeg_bin, "-encoders"], capture_output=True, text=True, errors="replace")
        if "h264_nvenc" in res.stdout.lower():
            info["nvenc_supported"] = True
    except Exception:
        pass

    return info


class WhisperGPUProcessor:
    """High-speed audio transcription using faster-whisper on T4 GPU (FP16)."""

    def __init__(self, model_size: str = "large-v3"):
        self.model_size = model_size

    def get_model(self):
        global _whisper_instance
        with _whisper_lock:
            if _whisper_instance is None:
                from faster_whisper import WhisperModel
                device = "cuda" if torch.cuda.is_available() else "cpu"
                compute_type = "float16" if device == "cuda" else "int8"
                print(f"[*] Loading WhisperModel '{self.model_size}' on '{device}' ({compute_type})...")
                _whisper_instance = WhisperModel(self.model_size, device=device, compute_type=compute_type)
                print(f"[+] WhisperModel '{self.model_size}' loaded successfully!")
        return _whisper_instance

    def transcribe(self, audio_path: str, language: Optional[str] = None) -> Dict[str, Any]:
        model = self.get_model()
        segments, info = model.transcribe(
            audio_path,
            language=language,
            beam_size=5,
            vad_filter=True,
            vad_parameters=dict(min_silence_duration_ms=500),
        )

        segment_list = []
        srt_lines = []
        full_text = []

        for idx, seg in enumerate(segments, 1):
            segment_list.append({
                "id": idx,
                "start": round(seg.start, 2),
                "end": round(seg.end, 2),
                "text": seg.text.strip(),
            })
            full_text.append(seg.text.strip())

            # Convert to standard SRT format
            start_srt = self._format_srt_time(seg.start)
            end_srt = self._format_srt_time(seg.end)
            srt_lines.append(f"{idx}\n{start_srt} --> {end_srt}\n{seg.text.strip()}\n")

        return {
            "language": info.language,
            "language_probability": round(info.language_probability, 4),
            "duration": round(info.duration, 2),
            "full_text": " ".join(full_text),
            "segments": segment_list,
            "srt_content": "\n".join(srt_lines),
        }

    @staticmethod
    def _format_srt_time(seconds: float) -> str:
        hrs = int(seconds // 3600)
        mins = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds - int(seconds)) * 1000)
        return f"{hrs:02d}:{mins:02d}:{secs:02d},{millis:03d}"


class VieneuTTSGPUProcessor:
    """Vietnamese neural Text-to-Speech using Vieneu model on T4 GPU."""

    def __init__(self):
        pass

    def get_client(self):
        global _vieneu_instance
        with _vieneu_lock:
            if _vieneu_instance is None:
                from vieneu import Vieneu
                print("[*] Initializing Vieneu-TTS model on GPU...")
                _vieneu_instance = Vieneu(emotion="natural")
                if hasattr(_vieneu_instance, "_default_voice"):
                    _vieneu_instance._default_voice = "Trúc Ly"
                print("[+] Vieneu-TTS model loaded successfully!")
        return _vieneu_instance

    def synthesize(self, text: str, voice: str, output_wav_path: str, reference_audio: Optional[str] = None) -> str:
        client = self.get_client()
        os.makedirs(os.path.dirname(os.path.abspath(output_wav_path)), exist_ok=True)

        if not voice or voice in ["default", "female"]:
            voice = "Trúc Ly"

        if hasattr(client, "_default_voice"):
            client._default_voice = "Trúc Ly"

        # Generate audio using Vieneu
        if reference_audio and os.path.exists(reference_audio) and os.path.getsize(reference_audio) > 500:
            try:
                if hasattr(client, "clone_voice"):
                    client.clone_voice(text=text, reference_audio=reference_audio, output_path=output_wav_path)
                elif hasattr(client, "infer"):
                    ref_codes = client.encode_reference(reference_audio) if hasattr(client, "encode_reference") else None
                    audio = client.infer(text=text, ref_codes=ref_codes, voice=voice)
                    client.save(audio, output_wav_path)
                else:
                    client.tts(text=text, voice=voice, output_path=output_wav_path)
            except Exception as e:
                print(f"[!] Lỗi khi clone giọng: {e}. Fallback trực tiếp về giọng {voice}...")
                if hasattr(client, "infer"):
                    audio = client.infer(text=text, voice=voice)
                    client.save(audio, output_wav_path)
                else:
                    client.tts(text=text, voice=voice, output_path=output_wav_path)
        else:
            if hasattr(client, "infer"):
                audio = client.infer(text=text, voice=voice)
                client.save(audio, output_wav_path)
            elif hasattr(client, "tts"):
                client.tts(text=text, voice=voice, output_path=output_wav_path)

        return output_wav_path


class AudioSeparatorGPUProcessor:
    """Vocal and Background Music Separation using AI UVR5 on ONNX GPU."""

    def __init__(self, output_dir: str):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def separate(self, audio_path: str, model_filename: str = "Kim_Vocal_2.onnx") -> Dict[str, str]:
        from audio_separator.separator import Separator

        sep = Separator(
            output_dir=self.output_dir,
            output_format="wav",
        )
        print(f"[*] Loading UVR5 model '{model_filename}' on GPU...")
        sep.load_model(model_filename=model_filename)
        print(f"[*] Separating audio tracks: {audio_path}...")
        output_files = sep.separate(audio_path)

        # Usually returns [vocal_file, instrumental_file]
        vocal_path = None
        instrumental_path = None

        for filename in output_files:
            abs_p = os.path.join(self.output_dir, filename) if not os.path.isabs(filename) else filename
            if "(Vocals)" in filename or "Vocals" in filename:
                vocal_path = abs_p
            elif "(Instrumental)" in filename or "Instrumental" in filename:
                instrumental_path = abs_p

        return {
            "vocal_path": vocal_path or (os.path.join(self.output_dir, output_files[0]) if len(output_files) > 0 else None),
            "instrumental_path": instrumental_path or (os.path.join(self.output_dir, output_files[1]) if len(output_files) > 1 else None),
        }


class VideoEditorNVENC:
    """Fast video rendering utilizing FFmpeg with NVIDIA NVENC hardware encoder."""

    @staticmethod
    def get_encoder() -> str:
        try:
            res = subprocess.run(["ffmpeg", "-encoders"], capture_output=True, text=True, errors="replace")
            if "h264_nvenc" in res.stdout.lower() and torch.cuda.is_available():
                return "h264_nvenc"
        except Exception:
            pass
        return "libx264"

    @classmethod
    def render(
        cls,
        input_video: str,
        output_video: str,
        new_audio: Optional[str] = None,
        srt_subtitles: Optional[str] = None,
        speed: float = 1.0,
        flip_horizontal: bool = False,
        zoom_factor: float = 1.0,
        watermark_text: Optional[str] = None,
    ) -> str:
        encoder = cls.get_encoder()
        print(f"[*] Video rendering with encoder: {encoder} (GPU accelerated)")

        os.makedirs(os.path.dirname(os.path.abspath(output_video)), exist_ok=True)

        filter_chain = []

        # Video filters
        if flip_horizontal:
            filter_chain.append("hflip")

        if zoom_factor > 1.0:
            # Crop center to zoom
            filter_chain.append(f"scale=iw*{zoom_factor}:ih*{zoom_factor},crop=iw/{zoom_factor}:ih/{zoom_factor}")

        if speed != 1.0:
            pts_factor = 1.0 / speed
            filter_chain.append(f"setpts={pts_factor}*PTS")

        if srt_subtitles and os.path.exists(srt_subtitles):
            # Escape path for ffmpeg filter
            sub_path_escaped = srt_subtitles.replace("\\", "/").replace(":", "\\:")
            filter_chain.append(f"subtitles='{sub_path_escaped}':force_style='FontSize=20,PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,BorderStyle=3'")

        if watermark_text:
            filter_chain.append(f"drawtext=text='{watermark_text}':fontcolor=white@0.8:fontsize=24:x=(w-text_w)/2:y=h-50:box=1:boxcolor=black@0.5")

        vf_str = ",".join(filter_chain) if filter_chain else "null"

        cmd = ["ffmpeg", "-y", "-i", input_video]

        if new_audio and os.path.exists(new_audio):
            cmd.extend(["-i", new_audio, "-map", "0:v:0", "-map", "1:a:0"])
        else:
            cmd.extend(["-map", "0:v:0", "-map", "0:a:0?"])

        cmd.extend(["-vf", vf_str, "-c:v", encoder])

        if encoder == "h264_nvenc":
            cmd.extend(["-preset", "p4", "-rc:v", "vbr", "-cq:v", "26", "-b:v", "2M", "-maxrate", "3M", "-bufsize", "4M"])
        else:
            cmd.extend(["-preset", "fast", "-crf", "23"])

        cmd.extend(["-c:a", "aac", "-b:a", "192k", output_video])

        print(f"[*] Running FFmpeg: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True, errors="replace")

        if result.returncode != 0:
            raise RuntimeError(f"FFmpeg render failed:\n{result.stderr}")

        print(f"[+] Video rendered successfully: {output_video}")
        return output_video
