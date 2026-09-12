import os
import requests
from typing import Optional, Dict, Any


class ColabGPUClient:
    """
    Python SDK Client để giao tiếp từ máy Local (Windows) tới
    GPU Worker chạy trên Google Colab qua Cloudflare Tunnel URL.
    """

    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")

    def check_health(self) -> Dict[str, Any]:
        """Kiểm tra tình trạng GPU, VRAM và kết nối tới Colab."""
        url = f"{self.base_url}/api/gpu/health"
        res = requests.get(url, timeout=10)
        res.raise_for_status()
        return res.json()

    def transcribe(
        self,
        media_path: str,
        model_size: str = "base",
        language: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Gửi file audio/video lên Colab để chạy Faster-Whisper bằng GPU T4.
        Trả về danh sách các câu phụ đề kèm mốc thời gian và nội dung SRT.
        """
        if not os.path.exists(media_path):
            raise FileNotFoundError(f"Không tìm thấy file: {media_path}")

        url = f"{self.base_url}/api/gpu/transcribe"
        data = {"model_size": model_size}
        if language:
            data["language"] = language

        with open(media_path, "rb") as f:
            files = {"file": (os.path.basename(media_path), f)}
            res = requests.post(url, data=data, files=files, timeout=300)

        res.raise_for_status()
        return res.json()

    def generate_tts(
        self,
        text: str,
        output_wav_path: str,
        voice: str = "female",
        reference_audio_path: Optional[str] = None,
    ) -> str:
        """
        Gửi văn bản lên Colab để tạo giọng nói tiếng Việt qua mô hình VieNeu-TTS.
        Lưu file audio kết quả về máy Local.
        """
        url = f"{self.base_url}/api/gpu/tts"
        data = {"text": text, "voice": voice}
        files = {}

        if reference_audio_path and os.path.exists(reference_audio_path):
            files["reference_file"] = open(reference_audio_path, "rb")

        try:
            res = requests.post(url, data=data, files=files if files else None, timeout=180, stream=True)
            res.raise_for_status()

            os.makedirs(os.path.dirname(os.path.abspath(output_wav_path)), exist_ok=True)
            with open(output_wav_path, "wb") as f:
                for chunk in res.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            return output_wav_path
        finally:
            for f in files.values():
                f.close()

    def separate_audio(self, audio_path: str, output_dir: str) -> Dict[str, str]:
        """
        Gửi audio lên Colab để tách Giọng nói (Vocal) và Nhạc nền (BGM) bằng UVR5 GPU.
        Tải 2 file kết quả về thư mục output_dir ở máy Local.
        """
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"Không tìm thấy file: {audio_path}")

        url = f"{self.base_url}/api/gpu/separate-audio"
        with open(audio_path, "rb") as f:
            files = {"file": (os.path.basename(audio_path), f)}
            res = requests.post(url, files=files, timeout=300)

        res.raise_for_status()
        data = res.json()

        os.makedirs(output_dir, exist_ok=True)
        vocal_local = os.path.join(output_dir, "vocal.wav")
        inst_local = os.path.join(output_dir, "instrumental.wav")

        # Tải file vocal
        if data.get("vocal_url"):
            v_res = requests.get(f"{self.base_url}{data['vocal_url']}", stream=True)
            with open(vocal_local, "wb") as f:
                for chunk in v_res.iter_content(8192):
                    f.write(chunk)

        # Tải file nhạc nền
        if data.get("instrumental_url"):
            i_res = requests.get(f"{self.base_url}{data['instrumental_url']}", stream=True)
            with open(inst_local, "wb") as f:
                for chunk in i_res.iter_content(8192):
                    f.write(chunk)

        return {
            "vocal_path": vocal_local if os.path.exists(vocal_local) else None,
            "instrumental_path": inst_local if os.path.exists(inst_local) else None,
        }

    def render_video_nvenc(
        self,
        video_path: str,
        output_video_path: str,
        audio_path: Optional[str] = None,
        srt_path: Optional[str] = None,
        speed: float = 1.0,
        flip_horizontal: bool = False,
        zoom_factor: float = 1.0,
        watermark_text: Optional[str] = None,
    ) -> str:
        """
        Gửi video và các cấu hình lên Colab để render bằng FFmpeg NVENC phần cứng T4.
        Tải video thành phẩm đã lách bản quyền về máy Local.
        """
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Không tìm thấy file video: {video_path}")

        url = f"{self.base_url}/api/gpu/render-video"
        data = {
            "speed": str(speed),
            "flip_horizontal": "true" if flip_horizontal else "false",
            "zoom_factor": str(zoom_factor),
        }
        if watermark_text:
            data["watermark_text"] = watermark_text

        files = {"video_file": (os.path.basename(video_path), open(video_path, "rb"))}

        if audio_path and os.path.exists(audio_path):
            files["audio_file"] = (os.path.basename(audio_path), open(audio_path, "rb"))

        if srt_path and os.path.exists(srt_path):
            files["srt_file"] = (os.path.basename(srt_path), open(srt_path, "rb"))

        try:
            res = requests.post(url, data=data, files=files, timeout=600, stream=True)
            res.raise_for_status()

            os.makedirs(os.path.dirname(os.path.abspath(output_video_path)), exist_ok=True)
            with open(output_video_path, "wb") as f:
                for chunk in res.iter_content(chunk_size=65536):
                    if chunk:
                        f.write(chunk)

            return output_video_path
        finally:
            for f in files.values():
                if hasattr(f[1], "close"):
                    f[1].close()
