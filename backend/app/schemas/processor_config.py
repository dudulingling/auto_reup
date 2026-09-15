from pydantic import BaseModel
from typing import List, Optional

class VideoMask(BaseModel):
    id: Optional[int] = None
    x: float = 10.0
    y: float = 10.0
    width: float = 20.0
    height: float = 15.0
    type: str = "color"
    color: str = "#000000"

class VideoProcessingConfig(BaseModel):
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
    custom_srt: Optional[str] = None
    use_custom_srt: bool = False
    use_bcut_asr: bool = False
    use_llm_segmentation: bool = False
    whisper_prompt: Optional[str] = None
    
    subtitle_style: str = "black_white"
    subtitle_font_family: str = "Liberation Sans"
    subtitle_text_color: str = "#000000"
    subtitle_bg_color: Optional[str] = "#FFFFFF"
    subtitle_font_size: int = 8
    subtitle_margin_v: int = 40
    subtitle_bg_padding: int = 2
    subtitle_bg_opacity: Optional[int] = 100
    enable_subtitles: bool = True
    enable_ai_subtitle_polish: bool = True
    subtitle_polish_style: str = "tiktok_viral"
    watermark_type: str = "none"
    watermark_text: Optional[str] = None
    watermark_image_path: Optional[str] = None
    watermark_x: float = 50.0
    watermark_y: float = 50.0
    watermark_size: float = 20.0
    watermark_color: str = "#FFFFFF"
    watermark_opacity: float = 50.0
    
    mask_enabled: bool = False
    mask_x: float = 10.0
    mask_y: float = 10.0
    mask_width: float = 20.0
    mask_height: float = 15.0
    mask_type: str = "color"
    mask_color: str = "#000000"
    masks: List[VideoMask] = []
