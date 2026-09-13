import os
import requests
from dotenv import load_dotenv
from typing import Optional, Dict, Any

ENV_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../data/.env"))


class ColabBridge:
    """
    Cầu nối giao tiếp giữa Backend Local và Google Colab T4 GPU Worker.
    Tự động kiểm tra trạng thái và cung cấp các phương thức gọi AI/NVENC từ xa.
    """

    @classmethod
    def get_config(cls) -> tuple[bool, str]:
        load_dotenv(ENV_PATH, override=True)
        use_colab = os.getenv("USE_COLAB_GPU", "False").lower() == "true"
        url = os.getenv("COLAB_GPU_URL", "").strip().rstrip("/")
        if url and not url.startswith("http"):
            url = f"https://{url}"
        return use_colab, url

    @classmethod
    def is_enabled(cls) -> bool:
        use_colab, url = cls.get_config()
        return bool(use_colab and url)

    @classmethod
    def check_health(cls) -> Dict[str, Any]:
        use_colab, url = cls.get_config()
        if not url:
            return {"connected": False, "message": "Chưa cấu hình Colab GPU URL."}

        try:
            res = requests.get(f"{url}/api/gpu/health", timeout=5)
            if res.status_code == 200:
                return {"connected": True, "data": res.json()}
            return {"connected": False, "message": f"HTTP {res.status_code}"}
        except Exception as e:
            return {"connected": False, "message": str(e)}

    @classmethod
    def transcribe_whisper(
        cls,
        audio_path: str,
        model_size: str = "base",
        language: Optional[str] = None,
        timeout: int = 300,
    ) -> Dict[str, Any]:
        """Gửi file audio sang Colab để bóc tách phụ đề bằng Faster-Whisper trên GPU T4."""
        _, base_url = cls.get_config()
        if not base_url:
            raise ValueError("Colab URL chưa được cấu hình.")

        url = f"{base_url}/api/gpu/transcribe"
        data = {"model_size": model_size}
        if language:
            data["language"] = language

        with open(audio_path, "rb") as f:
            files = {"file": (os.path.basename(audio_path), f)}
            res = requests.post(url, data=data, files=files, timeout=timeout)

        res.raise_for_status()
        return res.json()

    @classmethod
    def generate_tts(
        cls,
        text: str,
        voice: str,
        output_wav_path: str,
        reference_audio_path: Optional[str] = None,
        timeout: int = 180,
    ) -> str:
        """Gửi văn bản sang Colab để lồng tiếng bằng mô hình VieNeu-TTS trên GPU T4."""
        _, base_url = cls.get_config()
        if not base_url:
            raise ValueError("Colab URL chưa được cấu hình.")

        url = f"{base_url}/api/gpu/tts"
        voice_to_send = voice if voice and voice not in ["default", "female", "vieneu_female", "vieneu_default"] else "Trúc Ly"
        data = {"text": text, "voice": voice_to_send}
        files = {}

        if reference_audio_path and os.path.exists(reference_audio_path):
            files["reference_file"] = open(reference_audio_path, "rb")

        try:
            res = requests.post(url, data=data, files=files if files else None, timeout=timeout, stream=True)
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

    @classmethod
    def separate_audio(
        cls,
        audio_path: str,
        output_dir: str,
        timeout: int = 300,
    ) -> Dict[str, str]:
        """Gửi audio sang Colab để tách Vocal và Nhạc nền (BGM) bằng UVR5 GPU."""
        _, base_url = cls.get_config()
        if not base_url:
            raise ValueError("Colab URL chưa được cấu hình.")

        url = f"{base_url}/api/gpu/separate-audio"
        with open(audio_path, "rb") as f:
            files = {"file": (os.path.basename(audio_path), f)}
            res = requests.post(url, files=files, timeout=timeout)

        res.raise_for_status()
        data = res.json()

        os.makedirs(output_dir, exist_ok=True)
        base = os.path.splitext(os.path.basename(audio_path))[0]
        # Clean temporary suffixes to produce standard filenames matching glob patterns
        base_clean = base.replace("_audio", "")
        vocal_local = os.path.join(output_dir, f"{base_clean}_audio_(Vocals)_Kim_Vocal_2.wav")
        inst_local = os.path.join(output_dir, f"{base_clean}_audio_(Instrumental)_Kim_Vocal_2.wav")

        if data.get("vocal_url"):
            v_res = requests.get(f"{base_url}{data['vocal_url']}", stream=True, timeout=120)
            with open(vocal_local, "wb") as f:
                for chunk in v_res.iter_content(8192):
                    f.write(chunk)

        if data.get("instrumental_url"):
            i_res = requests.get(f"{base_url}{data['instrumental_url']}", stream=True, timeout=120)
            with open(inst_local, "wb") as f:
                for chunk in i_res.iter_content(8192):
                    f.write(chunk)

        return {
            "vocal_path": vocal_local if os.path.exists(vocal_local) and os.path.getsize(vocal_local) > 0 else None,
            "instrumental_path": inst_local if os.path.exists(inst_local) and os.path.getsize(inst_local) > 0 else None,
        }

    @classmethod
    def render_video_nvenc(
        cls,
        video_path: str,
        output_video_path: str,
        audio_path: Optional[str] = None,
        srt_path: Optional[str] = None,
        speed: float = 1.0,
        flip_horizontal: bool = False,
        zoom_factor: float = 1.0,
        watermark_text: Optional[str] = None,
        timeout: int = 600,
        log_callback=None,
    ) -> str:
        """Gửi video, audio và phụ đề sang Colab để render phần cứng NVENC."""
        _, base_url = cls.get_config()
        if not base_url:
            raise ValueError("Colab URL chưa được cấu hình.")

        url = f"{base_url}/api/gpu/render-video"
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
            if log_callback:
                log_callback("[*] ☁️ [Colab T4] Đang gửi dữ liệu video sang Google Colab để render NVENC...\n", progress=52.0)

            res = requests.post(url, data=data, files=files, timeout=timeout)
            res.raise_for_status()

            content_type = res.headers.get("content-type", "")

            # Pha 1: Nếu Colab trả về JSON (hệ thống URL tĩnh)
            if "application/json" in content_type:
                resp_data = res.json()
                video_url = resp_data.get("video_url")
                total_bytes = resp_data.get("size_bytes", 0)
                total_mb = total_bytes / (1024 * 1024) if total_bytes > 0 else 0

                if not video_url:
                    raise ValueError(f"Colab không trả về đường dẫn video: {resp_data}")

                download_url = f"{base_url}{video_url}"
                if log_callback:
                    if total_mb > 0:
                        log_callback(f"[+] ☁️ [Colab T4] GPU đã render xong ({total_mb:.1f} MB)! Bắt đầu tải video về máy...\n", progress=70.0)
                    else:
                        log_callback("[+] ☁️ [Colab T4] GPU đã render xong! Bắt đầu tải video về máy...\n", progress=70.0)

                down_res = requests.get(download_url, stream=True, timeout=300)
                down_res.raise_for_status()

                if not total_bytes:
                    total_bytes = int(down_res.headers.get("content-length", 0))
                    total_mb = total_bytes / (1024 * 1024) if total_bytes > 0 else 0

                os.makedirs(os.path.dirname(os.path.abspath(output_video_path)), exist_ok=True)
                downloaded = 0
                last_reported_pct = 0

                with open(output_video_path, "wb") as f:
                    for chunk in down_res.iter_content(chunk_size=131072):
                        if chunk:
                            f.write(chunk)
                            downloaded += len(chunk)
                            if total_bytes > 0 and log_callback:
                                pct = int((downloaded / total_bytes) * 100)
                                if pct - last_reported_pct >= 10:
                                    last_reported_pct = pct
                                    curr_prog = 70.0 + (pct / 100.0) * 25.0
                                    log_callback(f"[*] ☁️ [Colab T4] Đang nhận video: {downloaded/(1024*1024):.1f} MB / {total_mb:.1f} MB ({pct}%)...\n", progress=curr_prog)

            # Pha 2: Fallback nếu Colab đang chạy phiên bản cũ trả về FileResponse
            else:
                total_bytes = int(res.headers.get("content-length", 0))
                total_mb = total_bytes / (1024 * 1024) if total_bytes > 0 else 0

                if log_callback:
                    log_callback("[+] ☁️ [Colab T4] GPU đã render xong! Đang lưu video thành phẩm...\n", progress=75.0)

                os.makedirs(os.path.dirname(os.path.abspath(output_video_path)), exist_ok=True)
                with open(output_video_path, "wb") as f:
                    for chunk in res.iter_content(chunk_size=65536):
                        if chunk:
                            f.write(chunk)

            if not os.path.exists(output_video_path) or os.path.getsize(output_video_path) == 0:
                raise ValueError("File video nhận được từ Colab bị rỗng (0 bytes).")

            final_mb = os.path.getsize(output_video_path) / (1024 * 1024)
            if log_callback:
                log_callback(f"[+] ☁️ [Colab T4] Đã nhận và lưu video thành phẩm an toàn: {os.path.basename(output_video_path)} ({final_mb:.1f} MB)!\n", progress=95.0)

            return output_video_path
        finally:
            for f in files.values():
                if hasattr(f[1], "close"):
                    f[1].close()
