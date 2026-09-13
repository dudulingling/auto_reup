import os
import sys
import subprocess
import imageio_ffmpeg

if sys.platform == "win32":
    try:
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        if hasattr(sys.stderr, "reconfigure"):
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from dotenv import load_dotenv

import shutil
system_ffmpeg = shutil.which("ffmpeg")
ffmpeg_exe = system_ffmpeg if system_ffmpeg else imageio_ffmpeg.get_ffmpeg_exe()

def hex_to_ass_color(hex_color: str, alpha: str = "00") -> str:
    hex_color = hex_color.lstrip('#')
    if len(hex_color) != 6:
        hex_color = "FFFFFF"
    r, g, b = hex_color[0:2], hex_color[2:4], hex_color[4:6]
    return f"&H{alpha}{b}{g}{r}"

def get_video_duration(video_path: str) -> float:
    try:
        import re
        cmd = [ffmpeg_exe, "-i", video_path]
        result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='replace')
        match = re.search(r"Duration: (\d{2}):(\d{2}):(\d{2}\.\d{2})", result.stderr)
        if match:
            h, m, s = match.groups()
            return int(h) * 3600 + int(m) * 60 + float(s)
    except Exception:
        pass
    return 0.0
def get_video_resolution(video_path: str) -> tuple[int, int]:
    try:
        import json
        cmd = [
            "ffprobe", "-v", "error", 
            "-select_streams", "v:0", 
            "-show_entries", "stream=width,height:stream_tags=rotate", 
            "-of", "json", 
            video_path
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='replace')
        data = json.loads(result.stdout)
        
        if "streams" in data and len(data["streams"]) > 0:
            stream = data["streams"][0]
            w = int(stream.get("width", 1920))
            h = int(stream.get("height", 1080))
            
            # Check rotation metadata
            tags = stream.get("tags", {})
            rotate = tags.get("rotate")
            if rotate is not None:
                rotate_val = abs(int(rotate))
                if rotate_val == 90 or rotate_val == 270:
                    # Swap width and height for vertical video
                    return h, w
                    
            return w, h
    except Exception as e:
        print(f"Error reading video resolution via ffprobe: {e}")
        
    return 1920, 1080

def get_safe_boxblur_params(crop_w: float, crop_h: float, target_radius: int) -> str:
    # yuv420p chroma dimensions are half of luma
    chroma_w = crop_w / 2.0
    chroma_h = crop_h / 2.0
    
    # FFmpeg boxblur radius constraint for luma: must be >= 0 and <= (luma_dim + 1)/2
    # To be safe: luma_radius <= (luma_dim - 1)/2
    max_luma_r = int((min(crop_w, crop_h) - 1) / 2)
    luma_r = min(target_radius, max_luma_r)
    if luma_r < 1:
        luma_r = 1
        
    # boxblur radius constraint for chroma: must be >= 0 and <= (chroma_dim + 1)/2
    # To be safe: chroma_radius <= (chroma_dim - 1)/2
    max_chroma_r = int((min(chroma_w, chroma_h) - 1) / 2)
    chroma_r = min(luma_r, max_chroma_r)
    if chroma_r < 1:
        chroma_r = 1
        
    return f"{luma_r}:5:{chroma_r}:5"

class VideoEditor:
    def _get_gpu_vram_mb(self) -> int:
        """Query NVIDIA GPU VRAM in MB. Returns 0 if no GPU or query fails."""
        try:
            result = subprocess.run(
                ["nvidia-smi", "--query-gpu=memory.total", "--format=csv,noheader,nounits"],
                capture_output=True, text=True, timeout=5, encoding='utf-8', errors='replace'
            )
            if result.returncode == 0:
                vram_mb = int(result.stdout.strip().split('\n')[0])
                return vram_mb
        except Exception:
            pass
        return 0

    def get_optimal_video_encoder(self, use_gpu: bool = False) -> str:
        if not use_gpu:
            return "libx264"
        
        try:
            result = subprocess.run([ffmpeg_exe, "-encoders"], capture_output=True, text=True, check=True, encoding='utf-8', errors='replace')
            output = result.stdout.lower()
            
            # Kiểm tra NVENC (NVIDIA)
            if "h264_nvenc" in output and shutil.which("nvidia-smi"):
                print("[*] Phát hiện GPU NVIDIA. Sử dụng NVENC encoder.")
                return "h264_nvenc"
            
            # Kiểm tra QSV (Intel)
            if "h264_qsv" in output and os.path.exists("/dev/dri"):
                return "h264_qsv"
                
        except Exception as e:
            print(f"Lỗi khi kiểm tra encoder, tự động fallback về CPU: {e}")
            
        return "libx264"

    def burn_subtitles(self, input_video: str, srt_file: str, output_video: str, tts_audio: str = None, bgm_audio: str = None, vocal_audio: str = None, config=None, log_callback=None, force_cpu: bool = False):
        if config is None:
            from app.schemas.processor_config import VideoProcessingConfig
            config = VideoProcessingConfig()
            
        bg_volume = config.bg_volume
        flip_video = config.flip_video
        subtitle_style = config.subtitle_style
        opt_zoom = config.opt_zoom
        opt_color = config.opt_color
        opt_noise = config.opt_noise
        opt_pitch = config.opt_pitch
        subtitle_text_color = config.subtitle_text_color
        subtitle_bg_color = config.subtitle_bg_color
        subtitle_font_size = config.subtitle_font_size
        subtitle_margin_v = config.subtitle_margin_v
        subtitle_bg_padding = config.subtitle_bg_padding
        subtitle_bg_opacity = config.subtitle_bg_opacity
        watermark_type = config.watermark_type
        watermark_text = config.watermark_text
        watermark_image_path = config.watermark_image_path
        watermark_x = config.watermark_x
        watermark_y = config.watermark_y
        watermark_size = config.watermark_size
        watermark_color = config.watermark_color
        watermark_opacity = config.watermark_opacity
        subtitle_font_family = config.subtitle_font_family
        enable_subtitles = config.enable_subtitles
        mask_enabled = config.mask_enabled
        mask_x = config.mask_x
        mask_y = config.mask_y
        mask_width = config.mask_width
        mask_height = config.mask_height
        mask_type = config.mask_type
        mask_color = config.mask_color
        masks = config.masks

        load_dotenv(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../data/.env")), override=True)
        use_gpu = os.getenv("USE_GPU_ACCELERATION", "False").lower() == "true" and not force_cpu
        vcodec = self.get_optimal_video_encoder(use_gpu)
        print(f"[*] Sử dụng Video Encoder: {vcodec} (GPU={use_gpu})")

        cmd = [ffmpeg_exe, "-y", "-threads", "0"]
        
        # KHÔNG SỬ DỤNG -hwaccel cuda ở đây vì các filter (overlay, drawtext, blur) là CPU filters.
        # Sử dụng decode bằng GPU rồi ném vào CPU filter mà không qua hwdownload sẽ gây lỗi STATUS_HEAP_CORRUPTION (Crash).
            
        cmd.extend(["-i", input_video])
        input_count = 1
        video_w, video_h = get_video_resolution(input_video)
        
        from app.services.processor.ffmpeg_builder import FFmpegFilterBuilder
        builder = FFmpegFilterBuilder(config, video_w, video_h)
        
        builder.build_basic_filters()
        builder.build_text_watermark()
        builder.apply_vf_filters()
        
        if config.mask_enabled and not config.masks:
            config.masks = [{
                "x": config.mask_x,
                "y": config.mask_y,
                "width": config.mask_width,
                "height": config.mask_height,
                "type": config.mask_type,
                "color": config.mask_color
            }]
            
        builder.build_masks()
        builder.finalize_vbase()
        
        subs_dir = None
        if config.enable_subtitles and srt_file:
            from app.services.processor.subtitle_renderer import SubtitleRenderer
            import tempfile
            subs_dir = tempfile.mkdtemp(prefix="subs_")
            
            renderer = SubtitleRenderer(
                video_width=video_w,
                video_height=video_h,
                font_family=config.subtitle_font_family,
                font_size=config.subtitle_font_size,
                text_color=config.subtitle_text_color,
                bg_color=config.subtitle_bg_color,
                bg_opacity=config.subtitle_bg_opacity,
                margin_v=config.subtitle_margin_v,
                bg_padding=config.subtitle_bg_padding,
                style=config.subtitle_style
            )
            
            subtitle_output = renderer.generate_subtitle_sequence(srt_file, subs_dir)
            if subtitle_output.endswith('.ass'):
                builder.ass_file = subtitle_output
            else:
                concat_escaped = subtitle_output.replace('\\', '/')
                cmd.extend(["-f", "concat", "-safe", "0", "-i", concat_escaped])
                builder.subs_input_idx = input_count
                input_count += 1
                
        builder.build_subtitle_overlay()
        
        if config.watermark_type == "image" and config.watermark_image_path and os.path.exists(config.watermark_image_path):
            cmd.extend(["-i", config.watermark_image_path])
            builder.wm_image_idx = input_count
            input_count += 1
            
        builder.build_image_watermark()
        
        if tts_audio and os.path.exists(tts_audio):
            cmd.extend(["-i", tts_audio])
            builder.tts_idx = input_count
            input_count += 1
            
        if bgm_audio and os.path.exists(bgm_audio):
            cmd.extend(["-i", bgm_audio])
            builder.bgm_idx = input_count
            input_count += 1
            
        if vocal_audio and os.path.exists(vocal_audio):
            cmd.extend(["-i", vocal_audio])
            builder.vocal_idx = input_count
            input_count += 1
            
        a_map = builder.build_audio_filters()
        filter_complex_str = builder.get_filter_complex_string()
        
        print(f"DEBUG V_FILTER_COMPLEX: {filter_complex_str}")

        cmd.extend([
            "-filter_complex", filter_complex_str,
            "-map", "[vout]",
            "-map", a_map,
            "-c:v", vcodec,
        ])

        if vcodec == "h264_nvenc":
            # NVENC GPU: Bitrate mục tiêu 5 Mbps, tối đa 8 Mbps, cq 23 giúp giữ nguyên độ sắc nét Full HD cho TikTok
            cmd.extend([
                "-preset", "medium",
                "-rc:v", "vbr",
                "-cq:v", "23",
                "-b:v", "5M",
                "-maxrate", "8M",
                "-bufsize", "10M",
                "-pix_fmt", "yuv420p"
            ])
        else:
            # CPU Fallback: CRF 22 với veryfast preset để tối ưu cân bằng giữa tốc độ và độ sắc nét
            cmd.extend([
                "-crf", "22",
                "-preset", "veryfast",
                "-pix_fmt", "yuv420p"
            ])
        
        if builder.tts_idx != -1 or config.opt_pitch or getattr(config, 'opt_speed', False) or getattr(config, 'opt_reverb', False):
            cmd.extend([
                "-c:a", "aac",
                "-b:a", "128k"
            ])
        else:
            cmd.extend(["-c:a", "copy"])
        
        # Removed -shortest to allow video to freeze on last frame if TTS voice is longer than original video
        cmd.append(output_video)
        
        total_duration = get_video_duration(input_video)
        
        try:
            import re
            from app.core.redis_pool import get_sync_redis
            sync_redis = get_sync_redis(decode_responses=True)
            base_name = os.path.basename(input_video).split('.')[0]
 
            stderr_lines = []
            import time
            last_redis_check = 0
            
            process = subprocess.Popen(cmd, stderr=subprocess.PIPE, universal_newlines=True, encoding='utf-8', errors='replace')
            for line in process.stderr:
                stderr_lines.append(line)
                
                # Periodically check pause/cancellation flag (throttle to every 2 seconds)
                current_time = time.time()
                if current_time - last_redis_check > 2.0:
                    last_redis_check = current_time
                    if sync_redis.get(f"pause_video_{base_name}") == "1":
                        log_callback(f"[System] Phát hiện lệnh dừng từ người dùng. Đang hủy tiến trình FFmpeg cho {base_name}...\n")
                        process.kill()
                        raise Exception("Tiến trình bị hủy bởi người dùng.")
 
                if log_callback and total_duration > 0:
                    match = re.search(r"time=(\d{2}):(\d{2}):(\d{2}\.\d{2})", line)
                    if match:
                        h, m, s = match.groups()
                        current_sec = int(h) * 3600 + int(m) * 60 + float(s)
                        percent = 40.0 + (current_sec / total_duration) * 50.0
                        percent = min(90.0, max(40.0, percent))
                        log_callback(f"[*] Đang Render... {current_sec:.1f}s / {total_duration:.1f}s\n", progress=round(percent, 1))
            
            process.wait()
            if process.returncode != 0:
                if sync_redis.get(f"pause_video_{base_name}") == "1":
                    raise Exception("Tiến trình bị hủy bởi người dùng.")
                ffmpeg_err = "".join(stderr_lines[-15:])
                cmd_str = " ".join(cmd)
                print(f"FFmpeg Error Output:\n{ffmpeg_err}")
                raise Exception(f"FFmpeg exited with code {process.returncode}.\nCommand: {cmd_str}\nLog: {ffmpeg_err.strip()}")
            return output_video
        except Exception as e:
            # Tự động fallback về CPU nếu gặp lỗi do GPU encoder hoặc crash phần cứng
            err_str = str(e).lower()
            is_gpu_err = any(x in err_str for x in ["nvenc", "libnvidia", "driver", "encoder", "cuda", "3199971767", "3221225477", "0xc0000005"])
            if use_gpu and is_gpu_err:
                print(f"[!] Lỗi GPU Encoder: {e}. Tự động fallback về CPU (libx264)...")
                if log_callback:
                    log_callback(f"[!] Phát hiện lỗi bộ mã hóa GPU (NVENC): {e}.\nTự động chuyển hướng render bằng CPU (libx264)...\n")
                return self.burn_subtitles(
                    input_video=input_video, 
                    srt_file=srt_file, 
                    output_video=output_video, 
                    tts_audio=tts_audio, 
                    bgm_audio=bgm_audio, 
                    vocal_audio=vocal_audio,
                    config=config, 
                    log_callback=log_callback, 
                    force_cpu=True
                )
            else:
                raise Exception(f"Lỗi FFmpeg khi burn sub: {e}")
        finally:
            if builder:
                builder.cleanup()
            
            # Cleanup: dọn dẹp thư mục subtitle PNGs tạm
            if subs_dir and os.path.exists(subs_dir):
                try:
                    import shutil as _shutil
                    _shutil.rmtree(subs_dir, ignore_errors=True)
                except Exception:
                    pass

    def generate_preview_frame(self, input_video: str, preview_text: str, config=None, preview_time: float = 1.0) -> str:
        """
        Extracts a single frame from the input_video at a specific timestamp (preview_time seconds in),
        applies the EXACT same video filters, subtitles, and watermarks as `burn_subtitles`,
        and returns the absolute path to a generated JPG image file.
        """
        if config is None:
            from app.schemas.processor_config import VideoProcessingConfig
            config = VideoProcessingConfig()
            
        flip_video = config.flip_video
        subtitle_style = config.subtitle_style
        opt_zoom = config.opt_zoom
        opt_color = config.opt_color
        opt_noise = config.opt_noise
        subtitle_text_color = config.subtitle_text_color
        subtitle_bg_color = config.subtitle_bg_color
        subtitle_font_size = config.subtitle_font_size
        subtitle_margin_v = config.subtitle_margin_v
        subtitle_bg_padding = config.subtitle_bg_padding
        subtitle_bg_opacity = config.subtitle_bg_opacity
        watermark_type = config.watermark_type
        watermark_text = config.watermark_text
        watermark_image_path = config.watermark_image_path
        watermark_x = config.watermark_x
        watermark_y = config.watermark_y
        watermark_size = config.watermark_size
        watermark_color = config.watermark_color
        watermark_opacity = config.watermark_opacity
        subtitle_font_family = config.subtitle_font_family
        enable_subtitles = config.enable_subtitles
        mask_enabled = config.mask_enabled
        masks = config.masks

        import tempfile
        import uuid
        
        output_image = os.path.join(tempfile.gettempdir(), f"preview_{uuid.uuid4().hex}.jpg")
        video_w, video_h = get_video_resolution(input_video)
        
        # Chụp tại đúng thời điểm preview_time (giây)
        ss_time = max(0.0, float(preview_time))
        cmd = [ffmpeg_exe, "-y", "-ss", f"{ss_time:.2f}"]
        cmd.extend(["-i", input_video])
        input_count = 1
        
        from app.services.processor.ffmpeg_builder import FFmpegFilterBuilder
        builder = FFmpegFilterBuilder(config, video_w, video_h)
        
        builder.build_basic_filters()
        
        subs_dir = None
        srt_file = None
        
        try:
            if config.enable_subtitles and preview_text:
                from app.services.processor.subtitle_renderer import SubtitleRenderer
                import pysrt
                import tempfile
                
                subs_dir = tempfile.mkdtemp(prefix="preview_subs_")
                
                srt_file = os.path.join(subs_dir, "preview.srt")
                dummy_sub = pysrt.SubRipFile()
                dummy_sub.append(pysrt.SubRipItem(
                    1, start=pysrt.SubRipTime(0,0,0,0), end=pysrt.SubRipTime(0,0,10,0), text=preview_text
                ))
                dummy_sub.save(srt_file, encoding='utf-8')
                
                renderer = SubtitleRenderer(
                    video_width=video_w,
                    video_height=video_h,
                    font_family=config.subtitle_font_family,
                    font_size=config.subtitle_font_size,
                    text_color=config.subtitle_text_color,
                    bg_color=config.subtitle_bg_color,
                    bg_opacity=config.subtitle_bg_opacity,
                    margin_v=config.subtitle_margin_v,
                    bg_padding=config.subtitle_bg_padding,
                    style=config.subtitle_style
                )
                
                subtitle_output = renderer.generate_subtitle_sequence(srt_file, subs_dir)
                
                if subtitle_output.endswith('.ass'):
                    builder.ass_file = subtitle_output
                else:
                    concat_escaped = subtitle_output.replace('\\', '/')
                    cmd.extend(["-f", "concat", "-safe", "0", "-i", concat_escaped])
                    builder.subs_input_idx = input_count
                    input_count += 1
            
            builder.build_text_watermark()
            builder.apply_vf_filters()
            
            if config.mask_enabled and not config.masks:
                config.masks = [{
                    "x": config.mask_x,
                    "y": config.mask_y,
                    "width": config.mask_width,
                    "height": config.mask_height,
                    "type": config.mask_type,
                    "color": config.mask_color
                }]
                
            builder.build_masks()
            builder.finalize_vbase()
            builder.build_subtitle_overlay()
            
            if config.watermark_type == "image" and config.watermark_image_path and os.path.exists(config.watermark_image_path):
                cmd.extend(["-i", config.watermark_image_path])
                builder.wm_image_idx = input_count
                input_count += 1
                
            builder.build_image_watermark()
            v_filter_complex = builder.get_filter_complex_string()
            
            cmd.extend([
                "-filter_complex", v_filter_complex,
                "-map", "[vout]",
                "-frames:v", "1",
                "-q:v", "2",
                output_image
            ])
            
            print(f"DEBUG PREVIEW CMD: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='replace')
            if result.returncode != 0:
                print(f"FFmpeg Preview Error:\n{result.stderr}")
                raise Exception(f"FFmpeg exited with code {result.returncode} during preview generation.")
                
            return output_image
            
        finally:
            if builder:
                builder.cleanup()
            if subs_dir and os.path.exists(subs_dir):
                import shutil as _shutil
                _shutil.rmtree(subs_dir, ignore_errors=True)
