import os
import requests
from fastapi import APIRouter, Request, UploadFile, File, Form, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from pydantic import BaseModel
from dotenv import load_dotenv, set_key
from app.core.config import DATA_DIR
from app.core.security import encrypt_data, decrypt_data

router = APIRouter()

ENV_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../data/.env"))

class KeysUpdate(BaseModel):
    fpt_ai_api_key: str = ""
    elevenlabs_api_key: str = ""
    gemini_api_key: str = ""
    gemini_model: str = "gemini-3.5-flash"
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    xai_api_key: str = ""
    pexels_api_key: str = ""
    active_ai_provider: str = "gemini"
    active_tts_provider: str = "edge"
    ai_concurrency_limit: int = 1
    douyin_cookie: str = ""
    anti_detect_provider: str = "none"
    gpm_api_url: str = ""
    groq_api_key: str = ""
    use_groq: bool = False
    use_gpu_acceleration: bool = False
    enable_health_check: bool = False
    health_check_interval_hours: int = 4
    theme_bg_type: str = "default"
    theme_bg_custom_path: str = ""
    hf_token: str = ""
    enable_demucs: bool = False
    enable_auto_voice_clone: bool = False
    enable_diarization: bool = False
    bgm_volume: int = 50
    default_vocal_volume: int = 0
    custom_ai_endpoint: str = "http://localhost:20128/v1"
    custom_ai_key: str = ""
    custom_ai_model: str = "kr/claude-sonnet-4.5"
    use_colab_gpu: bool = False
    colab_gpu_url: str = ""

@router.get("/fonts")
async def get_available_fonts():
    fonts_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../data/fonts"))
    fonts = []
    
    # Mặc định luôn có font Liberation Sans của hệ thống Linux/FFmpeg
    default_font = {"id": "Liberation Sans", "name": "Liberation Sans (Mặc định)", "file": ""}
    
    try:
        if os.path.exists(fonts_dir):
            for file in os.listdir(fonts_dir):
                if file.lower().endswith(('.ttf', '.otf')):
                    # Lấy tên file bỏ đuôi làm tên Font
                    font_name = os.path.splitext(file)[0]
                    fonts.append({
                        "id": font_name,
                        "name": font_name,
                        "file": file
                    })
    except Exception as e:
        print(f"Error reading fonts dir: {e}")
        
    if not fonts:
        return {"fonts": [default_font]}
        
    # Thêm font mặc định vào đầu danh sách
    return {"fonts": [default_font] + sorted(fonts, key=lambda x: x["name"])}

@router.get("/edit_profile/{video_id}")
async def get_edit_profile(video_id: str, db: Session = Depends(get_db)):
    profile_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../data/edit_profiles"))
    os.makedirs(profile_dir, exist_ok=True)
    
    # Check specific video profile first
    profile_path = os.path.join(profile_dir, f"{video_id}.json")
    
    try:
        import json
        # If specific config exists, return it
        if os.path.exists(profile_path):
            with open(profile_path, "r", encoding="utf-8") as f:
                return json.load(f)
                
        # FALLBACK: Lấy process_config từ DB của video đã render
        try:
            from app.models.history import VideoHistory
            if video_id.isdigit():
                vid_id_int = int(video_id)
                record = db.query(VideoHistory).filter(VideoHistory.id == vid_id_int).first()
                if record and record.process_config:
                    db_config = json.loads(record.process_config)
                    if db_config:
                        # Map backend snake_case to frontend camelCase
                        return {
                            "voice": db_config.get("voice_mode", "edge_auto"),
                            "volume": db_config.get("bg_volume", 10),
                            "vocalVolume": db_config.get("vocal_volume", 0),
                            "useBcutAsr": db_config.get("use_bcut_asr", False),
                            "useLlmSegmentation": db_config.get("use_llm_segmentation", False),
                            "whisperPrompt": db_config.get("whisper_prompt", ""),
                            "flipVideo": db_config.get("flip_video", False),
                            "optZoom": db_config.get("opt_zoom", False),
                            "optColor": db_config.get("opt_color", False),
                            "optNoise": db_config.get("opt_noise", False),
                            "optPitch": db_config.get("opt_pitch", False),
                            "optSpeed": db_config.get("opt_speed", False),
                            "optReverb": db_config.get("opt_reverb", False),
                            "optVignette": db_config.get("opt_vignette", False),
                            "optRandomCombo": db_config.get("opt_random_combo", False),
                            "subtitleFont": db_config.get("subtitle_font_family", "Liberation Sans"),
                            "subtitleStyle": db_config.get("subtitle_style", "black_white"),
                            "subtitleTextColor": db_config.get("subtitle_text_color", "#000000"),
                            "subtitleBgColor": db_config.get("subtitle_bg_color", "#FFFFFF"),
                            "subtitleFontSize": db_config.get("subtitle_font_size", 8),
                            "subtitleMarginV": db_config.get("subtitle_margin_v", 40),
                            "subtitleBgPadding": db_config.get("subtitle_bg_padding", 2),
                            "subtitleBgOpacity": db_config.get("subtitle_bg_opacity", 100),
                            "enableSubtitles": db_config.get("enable_subtitles", True),
                            "maskEnabled": db_config.get("mask_enabled", False),
                            "masks": db_config.get("masks", []),
                            "watermarkType": db_config.get("watermark_type", "none"),
                            "watermarkText": db_config.get("watermark_text", ""),
                            "watermarkImagePreview": db_config.get("watermark_image_path", ""),
                            "watermarkX": db_config.get("watermark_x", 50.0),
                            "watermarkY": db_config.get("watermark_y", 50.0),
                            "watermarkSize": db_config.get("watermark_size", 20.0),
                            "watermarkColor": db_config.get("watermark_color", "#FFFFFF"),
                            "watermarkOpacity": db_config.get("watermark_opacity", 50.0),
                        }
        except Exception as e:
            print(f"Error reading process_config fallback: {e}")
            
        # Return empty dictionary if no specific profile exists, forcing frontend to use default clean state
        return {}
        
    except Exception as e:
        print(f"Error reading edit profile: {e}")
        
    return {}

@router.post("/edit_profile/{video_id}")
async def save_edit_profile(video_id: str, request: Request):
    profile_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../data/edit_profiles"))
    os.makedirs(profile_dir, exist_ok=True)
    profile_path = os.path.join(profile_dir, f"{video_id}.json")
    
    try:
        import json
        data = await request.json()
        with open(profile_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return {"status": "success"}
    except Exception as e:
        print(f"Error saving edit profile: {e}")
        return {"status": "error", "message": str(e)}

# In-memory cache for voices list (avoids re-initializing VieNeu engine on every request)
_voices_cache = {"provider": None, "voices": None}

@router.get("/voices")
async def get_available_voices():
    global _voices_cache
    load_dotenv(ENV_PATH, override=True)
    active_tts = os.getenv("ACTIVE_TTS_PROVIDER", "edge")
    
    # Return cached result if provider hasn't changed
    if _voices_cache["provider"] == active_tts and _voices_cache["voices"] is not None:
        return {"voices": _voices_cache["voices"]}
    
    voices = []
    
    # Auto Voice option that delegates to active provider
    voices.append({"id": "auto", "name": "Tự động phân vai Nam/Nữ", "provider": "Auto"})
    
    if active_tts == "fpt":
        voices.extend([
            {"id": "fpt_banmai", "name": "FPT Nữ (Ban Mai - Miền Bắc)", "provider": "FPT.AI"},
            {"id": "fpt_minhquang", "name": "FPT Nam (Minh Quang - Miền Nam)", "provider": "FPT.AI"},
            {"id": "fpt_thuminh", "name": "FPT Nữ (Thu Minh - Miền Bắc)", "provider": "FPT.AI"}
        ])
    elif active_tts == "openai":
        voices.extend([
            {"id": "openai_alloy", "name": "OpenAI (Alloy - Nam tính)", "provider": "OpenAI"},
            {"id": "openai_echo", "name": "OpenAI (Echo - Trầm ấm)", "provider": "OpenAI"},
            {"id": "openai_fable", "name": "OpenAI (Fable - Kể chuyện)", "provider": "OpenAI"},
            {"id": "openai_onyx", "name": "OpenAI (Onyx - Trầm)", "provider": "OpenAI"},
            {"id": "openai_nova", "name": "OpenAI (Nova - Nữ tính)", "provider": "OpenAI"},
            {"id": "openai_shimmer", "name": "OpenAI (Shimmer - Nữ trong trẻo)", "provider": "OpenAI"}
        ])
    elif active_tts == "elevenlabs":
        voices.extend([
            {"id": "elevenlabs_rachel", "name": "ElevenLabs (Rachel - Nữ)", "provider": "ElevenLabs"},
            {"id": "elevenlabs_drew", "name": "ElevenLabs (Drew - Nam)", "provider": "ElevenLabs"},
            {"id": "elevenlabs_clyde", "name": "ElevenLabs (Clyde - Nam)", "provider": "ElevenLabs"},
            {"id": "elevenlabs_mimi", "name": "ElevenLabs (Mimi - Nữ em bé)", "provider": "ElevenLabs"}
        ])
    elif active_tts == "vieneu":
        try:
            import json
            import importlib.util
            from pathlib import Path
            
            # Find vieneu package path without importing its heavy modules
            spec = importlib.util.find_spec("vieneu")
            if spec and spec.origin:
                assets_path = Path(spec.origin).parent / "assets" / "voices_v3_turbo.json"
                if assets_path.exists():
                    data = json.loads(assets_path.read_text(encoding="utf-8"))
                    presets_items = list(data.get("presets", {}).items())
                    # Sort so Trúc Ly comes first as default
                    presets_items.sort(key=lambda item: 0 if item[0] == "Trúc Ly" else 1)
                    for name, v in presets_items:
                        desc = v.get("description", "")
                        is_default = (name == "Trúc Ly")
                        label = f"{name} — {desc}" if desc else name
                        if is_default:
                            label += " (Mặc định)"
                        voices.append({
                            "id": f"vieneu_{name}",
                            "name": f"VieNeu: {label}",
                            "provider": "VieNeu-TTS"
                        })
                else:
                    raise FileNotFoundError("assets/voices_v3_turbo.json not found")
            else:
                raise ImportError("vieneu module not found")
        except Exception as e:
            print(f"Error loading Vieneu presets JSON: {e}")
            # Fallback if library or file not found
            voices.extend([
                {"id": "vieneu_female", "name": "VieNeu Nữ (Trúc Ly - Mặc định)", "provider": "VieNeu-TTS"},
                {"id": "vieneu_male", "name": "VieNeu Nam (Miền Nam/Bắc)", "provider": "VieNeu-TTS"},
                {"id": "vieneu_default", "name": "VieNeu Giọng Mặc Định (Trúc Ly)", "provider": "VieNeu-TTS"}
            ])
        
        # Add cloned voices
        clone_dir = os.path.join(DATA_DIR, "vieneu_clones")
        if os.path.exists(clone_dir):
            try:
                for filename in sorted(os.listdir(clone_dir)):
                    if filename.lower().endswith(('.wav', '.mp3', '.m4a')):
                        voice_name, _ = os.path.splitext(filename)
                        voices.append({
                            "id": f"vieneu_clone_{filename}",
                            "name": f"VieNeu Clone: {voice_name}",
                            "provider": "VieNeu-TTS (Clone)"
                        })
            except Exception as e:
                print(f"Error scanning cloned voices: {e}")
    else:
        # Default edge
        voices.extend([
            {"id": "edge_hoaimy", "name": "Chỉ Nữ (Hoài My)", "provider": "Edge-TTS"},
            {"id": "edge_namminh", "name": "Chỉ Nam (Nam Minh)", "provider": "Edge-TTS"}
        ])
        
    voices.append({"id": "none", "name": "Không lồng tiếng (Chỉ ghép phụ đề)", "provider": "None"})
    
    # Cache the result
    _voices_cache = {"provider": active_tts, "voices": voices}
        
    return {"voices": voices}

@router.get("/keys")
async def get_keys():
    load_dotenv(ENV_PATH, override=True)
    return {
        "fpt_ai_api_key": decrypt_data(os.getenv("FPT_AI_API_KEY", "")),
        "elevenlabs_api_key": decrypt_data(os.getenv("ELEVENLABS_API_KEY", "")),
        "gemini_api_key": decrypt_data(os.getenv("GEMINI_API_KEY", "")),
        "gemini_model": os.getenv("GEMINI_MODEL", "gemini-3.5-flash"),
        "openai_api_key": decrypt_data(os.getenv("OPENAI_API_KEY", "")),
        "anthropic_api_key": decrypt_data(os.getenv("ANTHROPIC_API_KEY", "")),
        "xai_api_key": decrypt_data(os.getenv("XAI_API_KEY", "")),
        "pexels_api_key": decrypt_data(os.getenv("PEXELS_API_KEY", "")),
        "active_ai_provider": os.getenv("ACTIVE_AI_PROVIDER", "gemini"),
        "active_tts_provider": os.getenv("ACTIVE_TTS_PROVIDER", "edge"),
        "ai_concurrency_limit": int(os.getenv("AI_CONCURRENCY_LIMIT", 1)),
        "douyin_cookie": decrypt_data(os.getenv("DOUYIN_COOKIE", "")),
        "anti_detect_provider": os.getenv("ANTI_DETECT_PROVIDER", "none"),
        "gpm_api_url": os.getenv("GPM_API_URL", ""),
        "groq_api_key": decrypt_data(os.getenv("GROQ_API_KEY", "")),
        "use_groq": os.getenv("USE_GROQ", "False").lower() == "true",
        "use_gpu_acceleration": os.getenv("USE_GPU_ACCELERATION", "False").lower() == "true",
        "enable_health_check": os.getenv("ENABLE_HEALTH_CHECK", "False").lower() == "true",
        "health_check_interval_hours": int(os.getenv("HEALTH_CHECK_INTERVAL_HOURS", 4)),
        "theme_bg_type": os.getenv("THEME_BG_TYPE", "default"),
        "theme_bg_custom_path": os.getenv("THEME_BG_CUSTOM_PATH", ""),
        "hf_token": decrypt_data(os.getenv("HF_TOKEN", "")),
        "enable_demucs": os.getenv("ENABLE_DEMUCS", "False").lower() == "true",
        "enable_auto_voice_clone": os.getenv("ENABLE_AUTO_VOICE_CLONE", "False").lower() == "true",
        "enable_diarization": os.getenv("ENABLE_DIARIZATION", "False").lower() == "true",
        "bgm_volume": int(os.getenv("BGM_VOLUME", 50)),
        "default_vocal_volume": int(os.getenv("DEFAULT_VOCAL_VOLUME", 0)),
        "custom_ai_endpoint": os.getenv("CUSTOM_AI_ENDPOINT", "http://localhost:20128/v1"),
        "custom_ai_key": decrypt_data(os.getenv("CUSTOM_AI_KEY", "")),
        "custom_ai_model": os.getenv("CUSTOM_AI_MODEL", "kr/claude-sonnet-4.5"),
        "use_colab_gpu": os.getenv("USE_COLAB_GPU", "False").lower() == "true",
        "colab_gpu_url": os.getenv("COLAB_GPU_URL", "")
    }

@router.post("/keys")
async def update_keys(data: KeysUpdate):
    # Đảm bảo file .env tồn tại
    if not os.path.exists(ENV_PATH):
        with open(ENV_PATH, "w") as f:
            f.write("")
            
    set_key(ENV_PATH, "FPT_AI_API_KEY", encrypt_data(data.fpt_ai_api_key))
    set_key(ENV_PATH, "ELEVENLABS_API_KEY", encrypt_data(data.elevenlabs_api_key))
    set_key(ENV_PATH, "GEMINI_API_KEY", encrypt_data(data.gemini_api_key))
    set_key(ENV_PATH, "GEMINI_MODEL", data.gemini_model)
    set_key(ENV_PATH, "OPENAI_API_KEY", encrypt_data(data.openai_api_key))
    set_key(ENV_PATH, "ANTHROPIC_API_KEY", encrypt_data(data.anthropic_api_key))
    set_key(ENV_PATH, "XAI_API_KEY", encrypt_data(data.xai_api_key))
    set_key(ENV_PATH, "PEXELS_API_KEY", encrypt_data(data.pexels_api_key))
    set_key(ENV_PATH, "ACTIVE_AI_PROVIDER", data.active_ai_provider)
    set_key(ENV_PATH, "ACTIVE_TTS_PROVIDER", data.active_tts_provider)
    set_key(ENV_PATH, "AI_CONCURRENCY_LIMIT", str(data.ai_concurrency_limit))
    set_key(ENV_PATH, "DOUYIN_COOKIE", encrypt_data(data.douyin_cookie))
    set_key(ENV_PATH, "ANTI_DETECT_PROVIDER", data.anti_detect_provider)
    set_key(ENV_PATH, "GPM_API_URL", data.gpm_api_url)
    set_key(ENV_PATH, "GROQ_API_KEY", encrypt_data(data.groq_api_key))
    set_key(ENV_PATH, "USE_GROQ", str(data.use_groq))
    set_key(ENV_PATH, "USE_GPU_ACCELERATION", str(data.use_gpu_acceleration))
    set_key(ENV_PATH, "ENABLE_HEALTH_CHECK", str(data.enable_health_check))
    set_key(ENV_PATH, "HEALTH_CHECK_INTERVAL_HOURS", str(data.health_check_interval_hours))
    set_key(ENV_PATH, "THEME_BG_TYPE", data.theme_bg_type)
    set_key(ENV_PATH, "THEME_BG_CUSTOM_PATH", data.theme_bg_custom_path)
    set_key(ENV_PATH, "HF_TOKEN", encrypt_data(data.hf_token))
    set_key(ENV_PATH, "ENABLE_DEMUCS", str(data.enable_demucs))
    set_key(ENV_PATH, "ENABLE_AUTO_VOICE_CLONE", str(data.enable_auto_voice_clone))
    set_key(ENV_PATH, "ENABLE_DIARIZATION", str(data.enable_diarization))
    set_key(ENV_PATH, "BGM_VOLUME", str(data.bgm_volume))
    set_key(ENV_PATH, "DEFAULT_VOCAL_VOLUME", str(data.default_vocal_volume))
    set_key(ENV_PATH, "CUSTOM_AI_ENDPOINT", data.custom_ai_endpoint)
    set_key(ENV_PATH, "CUSTOM_AI_KEY", encrypt_data(data.custom_ai_key))
    set_key(ENV_PATH, "CUSTOM_AI_MODEL", data.custom_ai_model)
    set_key(ENV_PATH, "USE_COLAB_GPU", str(data.use_colab_gpu))
    set_key(ENV_PATH, "COLAB_GPU_URL", data.colab_gpu_url.strip().rstrip("/"))
    
    # Invalidate voices cache when TTS provider might have changed
    global _voices_cache
    _voices_cache = {"provider": None, "voices": None}
    
    # Save cookie to file in Netscape format for yt-dlp (Lưu ý: yt-dlp cần file raw text)
    cookie_path = os.path.join(os.path.dirname(ENV_PATH), "douyin_cookie.txt")
    if os.path.exists(os.path.dirname(cookie_path)):
        lines = ["# Netscape HTTP Cookie File", ""]
        for domain in [".douyin.com", ".iesdouyin.com"]:
            for part in data.douyin_cookie.strip().split(";"):
                part = part.strip()
                if not part or "=" not in part: continue
                k, v = part.split("=", 1)
                lines.append(f"{domain}\tTRUE\t/\tFALSE\t2147483647\t{k}\t{v}")
            
        with open(cookie_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
    
    return {"status": "success", "message": "Cập nhật cấu hình thành công"}
 
@router.post("/validate")
def validate_keys(data: KeysUpdate):
    results = {
        "fpt_ai_api_key": "unknown",
        "elevenlabs_api_key": "unknown",
        "gemini_api_key": "unknown",
        "openai_api_key": "unknown",
        "anthropic_api_key": "unknown",
        "xai_api_key": "unknown",
        "groq_api_key": "unknown",
        "pexels_api_key": "unknown",
        "douyin_cookie": "unknown",
        "gpm_api_url": "unknown",
        "custom_ai_key": "unknown"
    }
    
    # 1. Test FPT API Key
    if data.fpt_ai_api_key and data.fpt_ai_api_key.strip():
        headers = {"api-key": data.fpt_ai_api_key}
        payload = {"text": "test", "voice": "banmai"}
        try:
            resp = requests.post("https://api.fpt.ai/hmi/tts/v5", headers=headers, data=payload, timeout=5)
            if resp.status_code in [200, 201]:
                results["fpt_ai_api_key"] = "valid"
            else:
                results["fpt_ai_api_key"] = "invalid"
        except Exception:
            results["fpt_ai_api_key"] = "error"
            
    # Test ElevenLabs API Key
    if data.elevenlabs_api_key and data.elevenlabs_api_key.strip():
        try:
            headers = {"xi-api-key": data.elevenlabs_api_key}
            resp = requests.get("https://api.elevenlabs.io/v1/user", headers=headers, timeout=5)
            if resp.status_code == 200:
                results["elevenlabs_api_key"] = "valid"
            else:
                results["elevenlabs_api_key"] = "invalid"
        except Exception:
            results["elevenlabs_api_key"] = "error"
            
    # 2. Test Gemini API Key
    if data.gemini_api_key and data.gemini_api_key.strip():
        try:
            from google import genai
            client = genai.Client(api_key=data.gemini_api_key)
            # Test simple completion
            client.models.generate_content(
                model=data.gemini_model,
                contents='hello'
            )
            results["gemini_api_key"] = "valid"
        except Exception as e:
            error_str = str(e).lower()
            print("Gemini Test Error:", e)
            if "429" in error_str or "resource_exhausted" in error_str or "503" in error_str or "unavailable" in error_str:
                # Authenticaton succeeded, just quota/server issues
                results["gemini_api_key"] = "valid"
            else:
                results["gemini_api_key"] = "invalid"

    # 3. Test OpenAI API Key
    if data.openai_api_key and data.openai_api_key.strip():
        try:
            from openai import OpenAI
            client = OpenAI(api_key=data.openai_api_key)
            client.models.list()
            results["openai_api_key"] = "valid"
        except Exception as e:
            print("OpenAI Test Error:", e)
            results["openai_api_key"] = "invalid"

    # 4. Test Anthropic API Key
    if data.anthropic_api_key and data.anthropic_api_key.strip():
        try:
            from anthropic import Anthropic
            client = Anthropic(api_key=data.anthropic_api_key)
            # Make a cheap call
            client.messages.create(model="claude-3-haiku-20240307", max_tokens=10, messages=[{"role": "user", "content": "hi"}])
            results["anthropic_api_key"] = "valid"
        except Exception as e:
            print("Anthropic Test Error:", e)
            results["anthropic_api_key"] = "invalid"

    # 5. Test xAI API Key
    if data.xai_api_key and data.xai_api_key.strip():
        try:
            from openai import OpenAI
            client = OpenAI(api_key=data.xai_api_key, base_url="https://api.x.ai/v1")
            client.models.list()
            results["xai_api_key"] = "valid"
        except Exception as e:
            print("xAI Test Error:", e)
            results["xai_api_key"] = "invalid"

    # Test Groq API Key
    if data.groq_api_key and data.groq_api_key.strip():
        try:
            from groq import Groq
            client = Groq(api_key=data.groq_api_key)
            client.models.list()
            results["groq_api_key"] = "valid"
        except Exception as e:
            print("Groq Test Error:", e)
            results["groq_api_key"] = "invalid"

    # Test Pexels API Key
    if data.pexels_api_key and data.pexels_api_key.strip():
        try:
            headers = {"Authorization": data.pexels_api_key}
            resp = requests.get("https://api.pexels.com/v1/collections", headers=headers, timeout=5)
            if resp.status_code == 200:
                results["pexels_api_key"] = "valid"
            else:
                results["pexels_api_key"] = "invalid"
        except Exception as e:
            print("Pexels Test Error:", e)
            results["pexels_api_key"] = "error"
            
    # 6. Test Douyin Cookie
    if data.douyin_cookie and data.douyin_cookie.strip():
        import urllib.parse
        from datetime import datetime, timezone
        
        missing = []
        if "sessionid=" not in data.douyin_cookie:
            missing.append("sessionid")
        if "__ac_signature=" not in data.douyin_cookie:
            missing.append("__ac_signature")
            
        expires = None
        is_expired = False
        for item in data.douyin_cookie.split(";"):
            item = item.strip()
            if item.startswith("sid_guard="):
                parts = item.split("=", 1)
                if len(parts) > 1:
                    val_parts = urllib.parse.unquote(parts[1]).split("|")
                    if len(val_parts) >= 4:
                        expires = val_parts[3].replace("+", " ")
                        try:
                            # Định dạng thường thấy: Sat, 25-Jul-2026 08:37:35 GMT
                            exp_dt = datetime.strptime(expires, "%a, %d-%b-%Y %H:%M:%S GMT")
                            exp_dt = exp_dt.replace(tzinfo=timezone.utc)
                            if datetime.now(timezone.utc) > exp_dt:
                                is_expired = True
                        except Exception as e:
                            print("Lỗi parse ngày hết hạn cookie:", e)
                break

        results["douyin_details"] = {
            "missing": missing,
            "expires": expires
        }

        try:
            from ..services.crawler.douyin_api import DouyinAPIClient
            client = DouyinAPIClient()
            client.raw_cookie = data.douyin_cookie
            client.cookies = {}
            for part in data.douyin_cookie.split(";"):
                part = part.strip()
                if "=" in part:
                    k, v = part.split("=", 1)
                    client.cookies[k] = v
                    
            if "__druidClientInfo=" in data.douyin_cookie:
                import base64
                import json
                import urllib.parse
                try:
                    for part in data.douyin_cookie.split(";"):
                        part = part.strip()
                        if part.startswith("__druidClientInfo="):
                            val = urllib.parse.unquote(part.split("=", 1)[1])
                            decoded = base64.b64decode(val).decode('utf-8')
                            info = json.loads(decoded)
                            if "userAgent" in info:
                                client.user_agent = info["userAgent"]
                                client.headers["User-Agent"] = client.user_agent
                                client.abogus_generator.user_agent = client.user_agent
                            break
                except Exception:
                    pass

            # Thử lấy bảng xếp hạng hoặc profile để kiểm tra chính xác
            params = client._default_query()
            params.update({"sec_user_id": "MS4wLjABAAAAgbac9ihpTlet1afYz7ingYX92zHVMzSGZeHQtWVaLSE"})
            resp_data = client.request_json("/aweme/v1/web/aweme/post/", params)
            
            if is_expired:
                results["douyin_cookie"] = "invalid"
            elif resp_data and isinstance(resp_data, dict):
                if resp_data.get("status_code") == 0:
                    results["douyin_cookie"] = "valid"
                else:
                    results["douyin_cookie"] = "invalid"
            else:
                results["douyin_cookie"] = "invalid"
                
        except Exception as e:
            results["douyin_cookie"] = "error"
    else:
        results["douyin_cookie"] = "missing"
        
    # Test GPM API URL
    if data.anti_detect_provider == "gpm" and data.gpm_api_url and data.gpm_api_url.strip():
        try:
            resp = requests.get(data.gpm_api_url.strip().rstrip('/'), timeout=3)
            # As long as it responds, consider it valid
            results["gpm_api_url"] = "valid"
        except requests.exceptions.RequestException:
            results["gpm_api_url"] = "invalid"
            
    # Test Custom AI API Key
    if data.custom_ai_endpoint and data.custom_ai_key and data.custom_ai_key.strip():
        try:
            from openai import OpenAI
            client = OpenAI(api_key=data.custom_ai_key, base_url=data.custom_ai_endpoint)
            client.models.list()
            results["custom_ai_key"] = "valid"
        except Exception as e:
            print("Custom AI Test Error:", e)
            results["custom_ai_key"] = "invalid"
            
    return results

@router.post("/health/check_now")
async def trigger_health_check_now():
    try:
        from app.tasks.health_tasks import check_all_accounts_health_task
        check_all_accounts_health_task.delay()
        return {"status": "success", "message": "Đã đưa lệnh kiểm tra sức khỏe tài khoản vào hàng đợi (Celery Queue)."}
    except Exception as e:
        return {"status": "error", "message": f"Lỗi kích hoạt task: {str(e)}"}

@router.post("/upload-background")
async def upload_background(file: UploadFile = File(...)):
    import shutil
    try:
        bg_path = os.path.join(DATA_DIR, "custom_bg.jpg")
        os.makedirs(os.path.dirname(bg_path), exist_ok=True)
        with open(bg_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        return {"status": "success", "url": "/api/files/custom_bg.jpg"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def check_gpu_status():
    status = {
        "gpu_available": False,
        "gpu_name": "Không phát hiện GPU rời NVIDIA",
        "cuda_version": "N/A",
        "ffmpeg_nvenc_available": False,
        "can_use_gpu_acceleration": False,
        "message": ""
    }
    
    import shutil
    import subprocess
    import re
    import imageio_ffmpeg
    
    # 1. Kiểm tra GPU NVIDIA qua nvidia-smi
    try:
        if shutil.which("nvidia-smi"):
            # Lấy tên GPU
            result = subprocess.run(["nvidia-smi", "--query-gpu=name", "--format=csv,noheader"], 
                                    capture_output=True, text=True, check=True, encoding='utf-8', errors='replace')
            gpu_name = result.stdout.strip()
            if gpu_name:
                status["gpu_available"] = True
                status["gpu_name"] = gpu_name
                
            # Lấy phiên bản CUDA được driver hỗ trợ
            cuda_res = subprocess.run(["nvidia-smi"], capture_output=True, text=True, encoding='utf-8', errors='replace')
            match = re.search(r"CUDA Version:\s*([\d\.]+)", cuda_res.stdout)
            if match:
                status["cuda_version"] = match.group(1)
    except Exception as e:
        print(f"[GPU Check] Lỗi khi chạy nvidia-smi: {e}")
        
    # 2. Kiểm tra FFmpeg hỗ trợ NVENC
    try:
        system_ffmpeg = shutil.which("ffmpeg")
        ffmpeg_exe_path = system_ffmpeg if system_ffmpeg else imageio_ffmpeg.get_ffmpeg_exe()
        
        encoder_res = subprocess.run([ffmpeg_exe_path, "-encoders"], capture_output=True, text=True, encoding='utf-8', errors='replace')
        if "h264_nvenc" in encoder_res.stdout.lower():
            status["ffmpeg_nvenc_available"] = True
    except Exception as e:
        print(f"[GPU Check] Lỗi khi kiểm tra FFmpeg: {e}")
        
    # 3. Kết luận khả năng sử dụng GPU acceleration
    if status["gpu_available"] and status["ffmpeg_nvenc_available"]:
        status["can_use_gpu_acceleration"] = True
        status["message"] = f"Phát hiện GPU {status['gpu_name']} (CUDA {status['cuda_version']}). Tăng tốc phần cứng hoạt động tốt."
    elif status["gpu_available"] and not status["ffmpeg_nvenc_available"]:
        status["message"] = f"Phát hiện GPU {status['gpu_name']} nhưng FFmpeg hiện tại không hỗ trợ bộ mã hóa h264_nvenc (cần cài bản FFmpeg đầy đủ)."
    else:
        status["message"] = "Không phát hiện thấy GPU rời NVIDIA tương thích hoặc driver NVIDIA chưa được cài đặt."
        
    return status

@router.get("/gpu-status")
async def get_gpu_status():
    return check_gpu_status()

class ColabStatusCheckRequest(BaseModel):
    url: str

@router.post("/colab-status")
async def check_colab_status(data: ColabStatusCheckRequest):
    target_url = data.url.strip().rstrip("/")
    if not target_url:
        return {"connected": False, "message": "Chưa nhập Colab GPU URL."}
    if not target_url.startswith("http"):
        target_url = f"https://{target_url}"

    import time
    start = time.time()
    try:
        res = requests.get(f"{target_url}/api/gpu/health", timeout=8)
        latency_ms = round((time.time() - start) * 1000, 1)
        if res.status_code == 200:
            resp_data = res.json()
            gpu_info = resp_data.get("gpu", {})
            return {
                "connected": True,
                "latency_ms": latency_ms,
                "gpu_name": gpu_info.get("device_name", "Tesla T4"),
                "vram_total_mb": gpu_info.get("vram_total_mb", 0),
                "vram_free_mb": gpu_info.get("vram_free_mb", 0),
                "nvenc_supported": gpu_info.get("nvenc_supported", True),
                "cuda_version": gpu_info.get("cuda_version", "N/A"),
                "message": f"Kết nối máy ảo Colab GPU thành công ({latency_ms}ms)!"
            }
        else:
            return {
                "connected": False,
                "message": f"Máy chủ Colab trả về mã phản hồi HTTP {res.status_code}."
            }
    except requests.exceptions.Timeout:
        return {"connected": False, "message": "Quá thời gian kết nối (Timeout 8s). Vui lòng kiểm tra lại notebook Colab."}
    except Exception as e:
        return {"connected": False, "message": f"Không thể kết nối tới Colab: {str(e)}"}



_vieneu_instance = None

def get_vieneu_client(emotion="natural"):
    global _vieneu_instance
    if _vieneu_instance is None:
        from vieneu import Vieneu
        _vieneu_instance = Vieneu(emotion=emotion)
        if hasattr(_vieneu_instance, "_default_voice"):
            _vieneu_instance._default_voice = "Trúc Ly"
    return _vieneu_instance

class VieneuTestRequest(BaseModel):
    text: str
    voice: str
    emotion: str = "natural"

@router.get("/vieneu/voices")
def get_vieneu_voices():
    try:
        tts = get_vieneu_client()
        presets = tts.list_preset_voices()
        voices = []
        for desc, v_id in presets:
            is_default = (v_id == "Trúc Ly" or "Trúc Ly" in desc)
            name_label = f"{desc} (Mặc định)" if is_default and "(Mặc định)" not in desc else desc
            voices.append({"id": v_id, "name": name_label})

        # Sort so Trúc Ly is listed first
        voices.sort(key=lambda x: 0 if (x["id"] == "Trúc Ly" or "Trúc Ly" in x["name"]) else 1)
        
        # Add cloned voices
        clone_dir = os.path.join(DATA_DIR, "vieneu_clones")
        if os.path.exists(clone_dir):
            try:
                for filename in sorted(os.listdir(clone_dir)):
                    if filename.lower().endswith(('.wav', '.mp3', '.m4a')):
                        voice_name, _ = os.path.splitext(filename)
                        voices.append({
                            "id": f"clone_{filename}",
                            "name": f"VieNeu Clone: {voice_name}"
                        })
            except Exception as e:
                print(f"Error scanning cloned voices in /vieneu/voices: {e}")
        return {"status": "success", "voices": voices}
    except Exception as e:
        return {"status": "error", "message": f"Không thể lấy danh sách giọng VieNeu: {str(e)}"}

@router.post("/vieneu/test")
def test_vieneu_tts(data: VieneuTestRequest):
    try:
        tts = get_vieneu_client(emotion=data.emotion)
        
        voice_data = None
        # Check if voice is a cloned voice
        if data.voice and data.voice.startswith("clone_"):
            filename = data.voice.replace("clone_", "")
            clone_path = os.path.join(DATA_DIR, "vieneu_clones", filename)
            if os.path.exists(clone_path):
                try:
                    voice_data = tts.encode_reference(clone_path)
                except Exception as e:
                    print(f"Error encoding cloned voice: {e}")
                    raise Exception(f"Không thể giải mã file âm thanh mẫu: {str(e)}")
        elif data.voice and data.voice not in ["default", "vieneu_default"]:
            try:
                voice_data = tts.get_preset_voice(data.voice)
            except Exception:
                pass
        else:
            # Default voice is Trúc Ly
            try:
                voice_data = tts.get_preset_voice("Trúc Ly")
            except Exception:
                pass
                
        audio = tts.infer(text=data.text, voice=voice_data)
        
        temp_dir = os.path.join(DATA_DIR, "temp")
        os.makedirs(temp_dir, exist_ok=True)
        output_file = os.path.join(temp_dir, "test_vieneu_web.wav")
        
        tts.save(audio, output_file)
        
        return {
            "status": "success",
            "audio_url": "/api/files/temp/test_vieneu_web.wav"
        }
    except Exception as e:
        return {"status": "error", "message": f"Lỗi sinh âm thanh VieNeu: {str(e)}"}

# API quản lý Clone giọng nói (Voice Cloning)
@router.get("/vieneu/clones")
def get_vieneu_clones():
    clone_dir = os.path.join(DATA_DIR, "vieneu_clones")
    os.makedirs(clone_dir, exist_ok=True)
    clones = []
    try:
        for filename in sorted(os.listdir(clone_dir)):
            if filename.lower().endswith(('.wav', '.mp3', '.m4a')):
                file_path = os.path.join(clone_dir, filename)
                voice_name, _ = os.path.splitext(filename)
                clones.append({
                    "id": filename,
                    "name": voice_name,
                    "file_url": f"/api/files/vieneu_clones/{filename}",
                    "size": os.path.getsize(file_path)
                })
        return {"status": "success", "clones": clones}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@router.post("/vieneu/clone")
async def create_vieneu_clone(
    file: UploadFile = File(...),
    name: str = Form(...)
):
    import shutil
    # Clean and validate name
    clean_name = "".join([c for c in name if c.isalpha() or c.isdigit() or c in ' -_']).strip()
    if not clean_name:
        return {"status": "error", "message": "Tên giọng đọc không hợp lệ."}
        
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ['.wav', '.mp3', '.m4a']:
        return {"status": "error", "message": "Định dạng file không hỗ trợ. Vui lòng tải lên file .wav, .mp3 hoặc .m4a"}
        
    clone_dir = os.path.join(DATA_DIR, "vieneu_clones")
    os.makedirs(clone_dir, exist_ok=True)
    
    dest_filename = f"{clean_name}{ext}"
    dest_path = os.path.join(clone_dir, dest_filename)
    
    try:
        with open(dest_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        return {
            "status": "success",
            "message": f"Đã lưu giọng clone '{clean_name}' thành công.",
            "voice": {
                "id": dest_filename,
                "name": clean_name,
                "file_url": f"/api/files/vieneu_clones/{dest_filename}"
            }
        }
    except Exception as e:
        return {"status": "error", "message": f"Không thể lưu file: {str(e)}"}

@router.delete("/vieneu/clones/{voice_filename}")
def delete_vieneu_clone(voice_filename: str):
    safe_filename = os.path.basename(voice_filename)
    clone_path = os.path.join(DATA_DIR, "vieneu_clones", safe_filename)
    
    if os.path.exists(clone_path):
        try:
            os.remove(clone_path)
            return {"status": "success", "message": "Đã xóa giọng clone thành công"}
        except Exception as e:
            return {"status": "error", "message": f"Không thể xóa file: {str(e)}"}
    else:
        return {"status": "error", "message": "Không tìm thấy giọng clone cần xóa"}


