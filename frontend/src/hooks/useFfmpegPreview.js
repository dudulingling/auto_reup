import { useState, useEffect } from 'react';

export const useFfmpegPreview = (subtitleConfig, videoPath, previewTime = 1) => {
  const [ffmpegPreviewUrl, setFfmpegPreviewUrl] = useState(null);
  const [isGeneratingPreview, setIsGeneratingPreview] = useState(false);

  useEffect(() => {
    if (!videoPath) return;
    
    // Don't generate preview while actively dragging
    if (subtitleConfig.isDragging || subtitleConfig.isDraggingWatermark) return;

    const timer = setTimeout(async () => {
      setIsGeneratingPreview(true);
      try {
        const configObj = subtitleConfig.getCurrentConfigObj();
        
        const payload = {
          video_paths: [videoPath],
          video_path: videoPath,
          preview_time: Number(previewTime) || 1,
          preview_text: configObj.previewSubtitleText,
          voice_mode: configObj.voice,
          bg_volume: configObj.volume,
          flip_video: configObj.flipVideo,
          opt_zoom: configObj.optZoom,
          opt_color: configObj.optColor,
          opt_noise: configObj.optNoise,
          opt_pitch: configObj.optPitch,
          opt_speed: configObj.optSpeed,
          opt_reverb: configObj.optReverb,
          opt_vignette: configObj.optVignette,
          opt_random_combo: configObj.optRandomCombo,
          subtitle_style: configObj.subtitleStyle,
          subtitle_text_color: configObj.subtitleTextColor,
          subtitle_bg_color: configObj.subtitleBgColor,
          subtitle_font_size: configObj.subtitleFontSize,
          subtitle_margin_v: configObj.subtitleMarginV,
          subtitle_bg_padding: configObj.subtitleBgPadding,
          subtitle_bg_opacity: configObj.subtitleBgOpacity,
          subtitle_font_family: configObj.subtitleFont,
          watermark_type: configObj.watermarkType,
          watermark_text: configObj.watermarkText,
          watermark_image_path: configObj.watermarkImagePreview || '',
          watermark_x: configObj.watermarkX,
          watermark_y: configObj.watermarkY,
          watermark_size: configObj.watermarkSize,
          watermark_color: configObj.watermarkColor,
          watermark_opacity: configObj.watermarkOpacity,
          enable_subtitles: configObj.enableSubtitles,
          mask_enabled: configObj.maskEnabled,
          masks: configObj.masks
        };
        
        const response = await fetch('http://localhost:8000/api/processor/preview-subtitle', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        });
        
        if (response.ok) {
          const blob = await response.blob();
          const objectUrl = URL.createObjectURL(blob);
          setFfmpegPreviewUrl(prev => {
            if (prev) URL.revokeObjectURL(prev);
            return objectUrl;
          });
        }
      } catch (err) {
        console.error('Failed to fetch FFmpeg preview:', err);
      } finally {
        setIsGeneratingPreview(false);
      }
    }, 600); // 600ms debounce
    
    return () => clearTimeout(timer);
  }, [
    subtitleConfig.voice, subtitleConfig.volume, subtitleConfig.flipVideo, 
    subtitleConfig.optZoom, subtitleConfig.optColor, subtitleConfig.optNoise, 
    subtitleConfig.optPitch, subtitleConfig.optSpeed, subtitleConfig.optReverb, subtitleConfig.optVignette,
    subtitleConfig.subtitleFont, subtitleConfig.subtitleStyle, 
    subtitleConfig.subtitleTextColor, subtitleConfig.subtitleBgColor, subtitleConfig.subtitleFontSize, 
    subtitleConfig.subtitleMarginV, subtitleConfig.subtitleBgPadding, subtitleConfig.subtitleBgOpacity, 
    subtitleConfig.previewSubtitleText, subtitleConfig.watermarkType, subtitleConfig.watermarkText, 
    subtitleConfig.watermarkImagePreview, subtitleConfig.watermarkX, subtitleConfig.watermarkY, 
    subtitleConfig.watermarkSize, subtitleConfig.watermarkColor, subtitleConfig.watermarkOpacity, 
    subtitleConfig.enableSubtitles, subtitleConfig.maskEnabled, subtitleConfig.masks,
    subtitleConfig.isDragging, subtitleConfig.isDraggingWatermark,
    videoPath, previewTime
  ]);

  return { ffmpegPreviewUrl, isGeneratingPreview };
};
