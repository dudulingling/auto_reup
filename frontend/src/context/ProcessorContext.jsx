import React, { createContext, useState, useContext, useRef } from 'react';

const ProcessorContext = createContext();

export const ProcessorProvider = ({ children }) => {
  const [videoPath, setVideoPath] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);
  const [activeTaskId, setActiveTaskId] = useState(null);
  const [logs, setLogs] = useState(["[System] Đang chờ lệnh xử lý..."]);
  const [progress, setProgress] = useState(0);
  const eventSourceRef = useRef(null);

  const startProcessing = async (submitPath, options = {}) => {
    if (!submitPath) return;
    setIsProcessing(true);
    setProgress(0);
    setLogs(["[System] Đang khởi tạo luồng xử lý..."]);

    try {
      const pathsArray = Array.isArray(submitPath) ? submitPath : submitPath.split('\n').map(p => p.trim()).filter(p => p);
      if (pathsArray.length === 0) return;

      let finalWatermarkImagePath = options.subConfig?.watermarkImagePreview || '';
      
      if (options.subConfig?.watermarkType === 'image' && options.subConfig?.watermarkImageFile) {
        const formData = new FormData();
        formData.append('file', options.subConfig.watermarkImageFile);
        
        try {
          const uploadRes = await fetch('http://localhost:8000/api/processor/upload-logo', {
            method: 'POST',
            body: formData
          });
          if (uploadRes.ok) {
            const uploadData = await uploadRes.json();
            finalWatermarkImagePath = uploadData.path;
          } else {
            setLogs(prev => [...prev, "[!] Lỗi khi tải lên ảnh Logo!"]);
            setIsProcessing(false);
            return;
          }
        } catch (error) {
          setLogs(prev => [...prev, `[!] Lỗi upload ảnh: ${error.message}`]);
          setIsProcessing(false);
          return;
        }
      }

      const res = await fetch('http://localhost:8000/api/processor/start', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          video_paths: pathsArray,
          voice_mode: options.voiceMode || 'edge_auto',
          bg_volume: options.bgVolume !== undefined ? options.bgVolume : 10,
          vocal_volume: options.vocalVolume !== undefined ? options.vocalVolume : 0,
          flip_video: options.flipVideo || false,
          opt_zoom: options.optZoom || false,
          opt_color: options.optColor || false,
          opt_noise: options.optNoise || false,
          opt_pitch: options.optPitch || false,
          opt_speed: options.optSpeed || false,
          opt_reverb: options.optReverb || false,
          opt_vignette: options.optVignette || false,
          opt_random_combo: options.optRandomCombo || false,
          subtitle_style: options.subConfig?.style || 'black_white',
          subtitle_text_color: options.subConfig?.textColor || '#000000',
          subtitle_bg_color: options.subConfig?.bgColor || '#ffffff',
          subtitle_font_size: options.subConfig?.fontSize || 20,
          subtitle_margin_v: options.subConfig?.marginV || 40,
          subtitle_bg_padding: options.subConfig?.bgPadding || 2,
          subtitle_bg_opacity: options.subConfig?.bgOpacity || 100,
          watermark_type: options.subConfig?.watermarkType || 'none',
          watermark_text: options.subConfig?.watermarkText || '',
          watermark_image_path: finalWatermarkImagePath,
          watermark_x: options.subConfig?.watermarkX ?? 50.0,
          watermark_y: options.subConfig?.watermarkY ?? 50.0,
          watermark_size: options.subConfig?.watermarkSize ?? 20.0,
          watermark_color: options.subConfig?.watermarkColor || '#FFFFFF',
          watermark_opacity: options.subConfig?.watermarkOpacity ?? 50.0,
          enable_subtitles: options.subConfig?.enableSubtitles ?? true,
          enable_ai_subtitle_polish: options.subConfig?.enableAiSubtitlePolish ?? true,
          subtitle_polish_style: options.subConfig?.subtitlePolishStyle || 'tiktok_viral',
          mask_enabled: options.subConfig?.maskEnabled ?? false,
          mask_x: options.subConfig?.maskX ?? 10.0,
          mask_y: options.subConfig?.maskY ?? 10.0,
          mask_width: options.subConfig?.maskWidth ?? 20.0,
          mask_height: options.subConfig?.maskHeight ?? 15.0,
          mask_type: options.subConfig?.maskType || 'color',
          mask_color: options.subConfig?.maskColor || '#000000',
          masks: options.subConfig?.masks || [],
          use_custom_srt: options.subConfig?.useCustomSrt ?? false,
          custom_srt: options.subConfig?.customSrt || '',
          use_bcut_asr: options.subConfig?.useBcutAsr ?? false,
          use_llm_segmentation: options.subConfig?.useLlmSegmentation ?? false,
          whisper_prompt: options.subConfig?.whisperPrompt || null
        })
      });
      
      if (!res.ok) {
        throw new Error("Lỗi kết nối Backend API Processor");
      }

      const data = await res.json();
      const taskId = data.task_id;
      setActiveTaskId(taskId);

      if (eventSourceRef.current) {
        eventSourceRef.current.close();
      }

      const eventSource = new EventSource(`http://localhost:8000/api/processor/stream/${taskId}`);
      eventSourceRef.current = eventSource;
      
      eventSource.onmessage = (event) => {
        const newLog = event.data;
        if (newLog.includes("[DONE]")) {
          setIsProcessing(false);
          setProgress(100);
          setActiveTaskId(null);
          eventSource.close();
        } else {
          try {
            const parsed = JSON.parse(newLog);
            if (parsed.progress !== undefined) {
              setProgress(parsed.progress);
            }
            if (parsed.log) {
              setLogs(prev => [...prev, parsed.log]);
            }
          } catch (e) {
            setLogs(prev => [...prev, newLog]);
          }
        }
      };

      eventSource.onerror = (error) => {
        console.error("SSE Error:", error);
        setLogs(prev => [...prev, "[System] Mất kết nối Stream API."]);
        eventSource.close();
        setIsProcessing(false);
        setActiveTaskId(null);
      };

    } catch (error) {
      setLogs(prev => [...prev, `[System Error] ${error.message}`]);
      setIsProcessing(false);
      setActiveTaskId(null);
    }
  };

  const stopProcessing = async () => {
    if (!activeTaskId) return;
    try {
      const res = await fetch(`http://localhost:8000/api/processor/stop/${activeTaskId}`, {
        method: 'POST'
      });
      const data = await res.json();
      if (res.ok) {
        setLogs(prev => [...prev, "[System] Đang gửi yêu cầu hủy tiến trình xử lý..."]);
      } else {
        setLogs(prev => [...prev, `[System Error] Không thể hủy: ${data.detail || "Lỗi hệ thống"}`]);
      }
    } catch (error) {
      setLogs(prev => [...prev, `[System Error] Lỗi kết nối: ${error.message}`]);
    }
  };

  return (
    <ProcessorContext.Provider value={{ videoPath, setVideoPath, isProcessing, logs, progress, startProcessing, stopProcessing }}>
      {children}
    </ProcessorContext.Provider>
  );
};

export const useProcessor = () => useContext(ProcessorContext);
