"""Diagnostic script: test generate_tts_track directly."""
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
BACKEND_DIR = os.path.join(ROOT_DIR, "backend")
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from app.services.processor.tts_generator import TTSGenerator

VIDEO = os.path.join(ROOT_DIR, "data", "raw_videos", "老六动画", "7642754049300811058.mp4")
SRT = os.path.join(ROOT_DIR, "data", "subtitles", "7642754049300811058_vi.srt")
OUTPUT_MP3 = os.path.join(ROOT_DIR, "data", "temp", "test_tts_output.mp3")

def dummy_log(msg, progress=None):
    print(f"LOG: {msg.strip()}")

tts = TTSGenerator()

try:
    print("Starting generate_tts_track...")
    res = tts.generate_tts_track(SRT, OUTPUT_MP3, "edge_auto", VIDEO, dummy_log)
    print(f"Success! Output: {res}")
    if os.path.exists(res):
        print(f"Output size: {os.path.getsize(res)} bytes")
except Exception as e:
    print(f"Exception: {e}")
