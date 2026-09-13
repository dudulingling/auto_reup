"""Test with REAL subtitle renderer output (not empty PNGs)."""
import os, sys, tempfile, subprocess, shutil
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
BACKEND_DIR = os.path.join(ROOT_DIR, "backend")
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from app.services.processor.subtitle_renderer import SubtitleRenderer

VIDEO = os.path.join(ROOT_DIR, "data", "raw_videos", "老六动画", "7642754049300811058.mp4")
ffmpeg_exe = shutil.which("ffmpeg")

# Find the actual SRT file
srt_path = os.path.join(ROOT_DIR, "data", "subtitles", "7642754049300811058_vi.srt")
if not os.path.exists(srt_path):
    print(f"SRT not found: {srt_path}")
    # List available SRTs
    srt_dir = os.path.join(ROOT_DIR, "data", "subtitles")
    if os.path.exists(srt_dir):
        for f in os.listdir(srt_dir):
            if "7642754049300811058" in f:
                print(f"  Found: {f}")
    sys.exit(1)

# Generate real subtitle PNGs
d = tempfile.mkdtemp(prefix="test_real_subs_")
renderer = SubtitleRenderer(
    video_width=1024, video_height=576,
    font_family="Liberation Sans", font_size=8,
    text_color="#000000", bg_color="#FFFFFF",
    bg_opacity=100, margin_v=40, bg_padding=2, style="classic"
)
concat_file = renderer.generate_subtitle_sequence(srt_path, d)
concat_esc = concat_file.replace("\\", "/")

# Count files
png_count = len([f for f in os.listdir(d) if f.endswith(".png")])
print(f"Generated {png_count} PNG files in {d}")
print(f"Concat file: {concat_file}")

# Print first 10 lines of concat
with open(concat_file, "r") as f:
    lines = f.readlines()
    print(f"\nConcat file has {len(lines)} lines. First 10:")
    for line in lines[:10]:
        print(f"  {line.rstrip()}")
    print(f"  ... last 4:")
    for line in lines[-4:]:
        print(f"  {line.rstrip()}")

# Test: run FFmpeg with real subtitles
print("\n=== TEST: Real subtitle overlay ===")
tts = os.path.join(ROOT_DIR, "data", "audio", "7642754049300811058_tts.mp3")
tts_exists = os.path.exists(tts)
print(f"TTS exists: {tts_exists}")

if tts_exists:
    cmd = [
        ffmpeg_exe, "-y", "-threads", "0",
        "-i", VIDEO,
        "-f", "concat", "-safe", "0", "-i", concat_esc,
        "-i", tts,
        "-t", "10",
        "-filter_complex",
        "[0:v]crop=iw/1.02:ih/1.02,scale=iw:ih,noise=alls=1:allf=t+u[vbase];"
        "[vbase][1:v]overlay=x=0:y=0[vsub_out];"
        "[vsub_out]copy[vout];"
        "[0:a]volume=0.1,asetrate=44100*1.02,atempo=1/1.02[bg];"
        "[2:a]volume=1.0[tts];"
        "[bg][tts]amix=inputs=2:duration=first:dropout_transition=2:normalize=0[aout]",
        "-map", "[vout]", "-map", "[aout]",
        "-c:v", "libx264", "-preset", "ultrafast", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "128k",
        "-shortest",
        "-f", "null", "NUL"
    ]
else:
    cmd = [
        ffmpeg_exe, "-y", "-threads", "0",
        "-i", VIDEO,
        "-f", "concat", "-safe", "0", "-i", concat_esc,
        "-t", "10",
        "-filter_complex",
        "[0:v]crop=iw/1.02:ih/1.02,scale=iw:ih,noise=alls=1:allf=t+u[vbase];"
        "[vbase][1:v]overlay=x=0:y=0[vsub_out];"
        "[vsub_out]copy[vout]",
        "-map", "[vout]", "-map", "0:a",
        "-c:v", "libx264", "-preset", "ultrafast", "-c:a", "copy",
        "-shortest",
        "-f", "null", "NUL"
    ]

r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
print(f"Exit code: {r.returncode}")
if r.returncode != 0:
    print(f"STDERR (last 800 chars):\n{r.stderr[-800:]}")
else:
    print("OK!")

shutil.rmtree(d, ignore_errors=True)
