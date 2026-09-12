import React, { useState, useEffect } from 'react';
import AiKeysTab from './components/AiKeysTab';
import TtsTab from './components/TtsTab';
import BrowserTab from './components/BrowserTab';
import SystemTab from './components/SystemTab';
import ThemeTab from './components/ThemeTab';const Settings = () => {
  const [fptKey, setFptKey] = useState("");
  const [elevenlabsKey, setElevenlabsKey] = useState("");
  const [geminiKey, setGeminiKey] = useState("");
  const [geminiModel, setGeminiModel] = useState("gemini-3.5-flash");
  const [openaiKey, setOpenaiKey] = useState("");
  const [anthropicKey, setAnthropicKey] = useState("");
  const [xaiKey, setXaiKey] = useState("");
  const [customAiEndpoint, setCustomAiEndpoint] = useState("http://localhost:20128/v1");
  const [customAiKey, setCustomAiKey] = useState("");
  const [customAiModel, setCustomAiModel] = useState("kr/claude-sonnet-4.5");
  const [groqKey, setGroqKey] = useState("");
  const [pexelsKey, setPexelsKey] = useState("");
  const [useGroq, setUseGroq] = useState(false);
  const [useGpuAcceleration, setUseGpuAcceleration] = useState(false);
  const [enableHealthCheck, setEnableHealthCheck] = useState(false);
  const [healthCheckInterval, setHealthCheckInterval] = useState(4);
  const [activeAIProvider, setActiveAIProvider] = useState("gemini");
  const [activeTTSProvider, setActiveTTSProvider] = useState("edge");
  const [concurrency, setConcurrency] = useState(1);
  const [douyinCookie, setDouyinCookie] = useState("");
  const [antiDetectProvider, setAntiDetectProvider] = useState("none");
  const [gpmApiUrl, setGpmApiUrl] = useState("");
  const [themeBgType, setThemeBgType] = useState("default");
  const [themeBgCustomPath, setThemeBgCustomPath] = useState("");
  const [hfToken, setHfToken] = useState("");
  const [enableDemucs, setEnableDemucs] = useState(false);
  const [enableAutoVoiceClone, setEnableAutoVoiceClone] = useState(false);
  const [enableDiarization, setEnableDiarization] = useState(false);
  const [bgmVolume, setBgmVolume] = useState(50);
  const [defaultVocalVolume, setDefaultVocalVolume] = useState(0);
  const [uploadBgStatus, setUploadBgStatus] = useState("");
  const [saveStatus, setSaveStatus] = useState("");
  const [validateStatus, setValidateStatus] = useState({ fpt: "", elevenlabs: "", gemini: "", openai: "", anthropic: "", xai: "", groq: "", pexels: "", douyin: "", gpm: "", custom: "" });
  const [activeTab, setActiveTab] = useState("ai");
  const [gpuStatus, setGpuStatus] = useState(null);
  const [checkingGpu, setCheckingGpu] = useState(false);
  const [useColabGpu, setUseColabGpu] = useState(false);
  const [colabGpuUrl, setColabGpuUrl] = useState("");
  const [colabStatus, setColabStatus] = useState(null);
  const [checkingColab, setCheckingColab] = useState(false);

  const settingsTabs = [
    { id: "ai", label: "API & AI Keys" },
    { id: "tts", label: "🎙️ Âm thanh & Lồng tiếng (Audio/TTS)" },
    { id: "browser", label: "Trình duyệt & Proxy" },
    { id: "system", label: "Hệ thống & Giám sát" },
    { id: "theme", label: "Giao diện" }
  ];

  const fetchGpuStatus = () => {
    setCheckingGpu(true);
    fetch('http://localhost:8000/api/settings/gpu-status')
      .then(res => res.json())
      .then(data => {
        setGpuStatus(data);
        setCheckingGpu(false);
      })
      .catch(err => {
        console.error("Lỗi fetch GPU:", err);
        setCheckingGpu(false);
      });
  };

  useEffect(() => {
    if (activeTab === "system") {
      fetchGpuStatus();
    }
  }, [activeTab]);

  useEffect(() => {
    fetch('http://localhost:8000/api/settings/keys')
      .then(res => res.json())
      .then(data => {
        if (data.fpt_ai_api_key) setFptKey(data.fpt_ai_api_key);
        if (data.elevenlabs_api_key) setElevenlabsKey(data.elevenlabs_api_key);
        if (data.gemini_api_key) setGeminiKey(data.gemini_api_key);
        if (data.gemini_model) setGeminiModel(data.gemini_model);
        if (data.openai_api_key) setOpenaiKey(data.openai_api_key);
        if (data.anthropic_api_key) setAnthropicKey(data.anthropic_api_key);
        if (data.xai_api_key) setXaiKey(data.xai_api_key);
        if (data.groq_api_key) setGroqKey(data.groq_api_key);
        if (data.pexels_api_key) setPexelsKey(data.pexels_api_key);
        if (data.use_groq !== undefined) setUseGroq(data.use_groq);
        if (data.use_gpu_acceleration !== undefined) setUseGpuAcceleration(data.use_gpu_acceleration);
        if (data.enable_health_check !== undefined) setEnableHealthCheck(data.enable_health_check);
        if (data.health_check_interval_hours) setHealthCheckInterval(data.health_check_interval_hours);
        if (data.active_ai_provider) setActiveAIProvider(data.active_ai_provider);
        if (data.active_tts_provider) setActiveTTSProvider(data.active_tts_provider);
        if (data.ai_concurrency_limit) setConcurrency(data.ai_concurrency_limit);
        if (data.douyin_cookie) setDouyinCookie(data.douyin_cookie);
        if (data.anti_detect_provider) setAntiDetectProvider(data.anti_detect_provider);
        if (data.gpm_api_url) setGpmApiUrl(data.gpm_api_url);
        if (data.theme_bg_type) setThemeBgType(data.theme_bg_type);
        if (data.theme_bg_custom_path) setThemeBgCustomPath(data.theme_bg_custom_path);
        if (data.hf_token) setHfToken(data.hf_token);
        if (data.custom_ai_endpoint) setCustomAiEndpoint(data.custom_ai_endpoint);
        if (data.custom_ai_key) setCustomAiKey(data.custom_ai_key);
        if (data.custom_ai_model) setCustomAiModel(data.custom_ai_model);
        if (data.enable_demucs !== undefined) setEnableDemucs(data.enable_demucs);
        if (data.enable_auto_voice_clone !== undefined) setEnableAutoVoiceClone(data.enable_auto_voice_clone);
        if (data.enable_diarization !== undefined) setEnableDiarization(data.enable_diarization);
        if (data.bgmVolume !== undefined) setBgmVolume(data.bgmVolume);
        if (data.default_vocal_volume !== undefined) setDefaultVocalVolume(data.default_vocal_volume);
        if (data.use_colab_gpu !== undefined) setUseColabGpu(data.use_colab_gpu);
        if (data.colab_gpu_url !== undefined) setColabGpuUrl(data.colab_gpu_url);

        // Tự động kiểm tra trạng thái ngay khi load trang nếu có dữ liệu
        if (data.fpt_ai_api_key || data.gemini_api_key || data.douyin_cookie || data.pexels_api_key) {
          fetch('http://localhost:8000/api/settings/validate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              fpt_ai_api_key: data.fpt_ai_api_key || "",
              elevenlabs_api_key: data.elevenlabs_api_key || "",
              gemini_api_key: data.gemini_api_key || "",
              gemini_model: data.gemini_model || "gemini-3.5-flash",
              openai_api_key: data.openai_api_key || "",
              anthropic_api_key: data.anthropic_api_key || "",
              xai_api_key: data.xai_api_key || "",
              groq_api_key: data.groq_api_key || "",
              pexels_api_key: data.pexels_api_key || "",
              active_ai_provider: data.active_ai_provider || "gemini",
              active_tts_provider: data.active_tts_provider || "edge",
              ai_concurrency_limit: data.ai_concurrency_limit || 1,
              douyin_cookie: data.douyin_cookie || "",
              anti_detect_provider: data.anti_detect_provider || "none",
              gpm_api_url: data.gpm_api_url || "",
              custom_ai_endpoint: data.custom_ai_endpoint || "http://localhost:20128/v1",
              custom_ai_key: data.custom_ai_key || "",
              custom_ai_model: data.custom_ai_model || "kr/claude-sonnet-4.5"
            })
          })
            .then(vRes => vRes.json())
            .then(vData => {
              setValidateStatus({
                fpt: vData.fpt_ai_api_key,
                elevenlabs: vData.elevenlabs_api_key,
                gemini: vData.gemini_api_key,
                openai: vData.openai_api_key,
                anthropic: vData.anthropic_api_key,
                xai: vData.xai_api_key,
                groq: vData.groq_api_key,
                pexels: vData.pexels_api_key,
                douyin: vData.douyin_cookie,
                gpm: vData.gpm_api_url,
                custom: vData.custom_ai_key,
                douyin_details: vData.douyin_details || null
              });
            })
            .catch(err => console.error("Lỗi validate:", err));
        }
      })
      .catch(err => console.error(err));
  }, []);

  const handleSave = async () => {
    setSaveStatus("Đang lưu...");
    try {
      const res = await fetch('http://localhost:8000/api/settings/keys', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          fpt_ai_api_key: fptKey,
          elevenlabs_api_key: elevenlabsKey,
          gemini_api_key: geminiKey,
          gemini_model: geminiModel,
          openai_api_key: openaiKey,
          anthropic_api_key: anthropicKey,
          xai_api_key: xaiKey,
          pexels_api_key: pexelsKey,
          active_ai_provider: activeAIProvider,
          active_tts_provider: activeTTSProvider,
          ai_concurrency_limit: Number(concurrency),
          douyin_cookie: douyinCookie,
          anti_detect_provider: antiDetectProvider,
          gpm_api_url: gpmApiUrl,
          groq_api_key: groqKey,
          use_groq: useGroq,
          use_gpu_acceleration: useGpuAcceleration,
          enable_health_check: enableHealthCheck,
          health_check_interval_hours: Number(healthCheckInterval),
          theme_bg_type: themeBgType,
          theme_bg_custom_path: themeBgCustomPath,
          hf_token: hfToken,
          enable_demucs: enableDemucs,
          enable_auto_voice_clone: enableAutoVoiceClone,
          enable_diarization: enableDiarization,
          bgm_volume: Number(bgmVolume),
          default_vocal_volume: Number(defaultVocalVolume),
          custom_ai_endpoint: customAiEndpoint,
          custom_ai_key: customAiKey,
          custom_ai_model: customAiModel,
          use_colab_gpu: useColabGpu,
          colab_gpu_url: colabGpuUrl.trim()
        })
      });
      if (res.ok) {
        setSaveStatus("Đã lưu thành công! Đang kiểm tra kết nối...");
        localStorage.setItem('theme_bg_type', themeBgType);
        localStorage.setItem('theme_bg_custom_path', themeBgCustomPath);
        
        // Áp dụng trực tiếp giao diện
        if (themeBgType === 'dark') {
          document.documentElement.style.setProperty('--bg-image', 'none');
          document.documentElement.style.setProperty('--bg-opacity', '0');
        } else if (themeBgType === 'custom' && themeBgCustomPath) {
          const fullUrl = themeBgCustomPath.startsWith('http') ? themeBgCustomPath : `http://localhost:8000${themeBgCustomPath}`;
          document.documentElement.style.setProperty('--bg-image', `url('${fullUrl}')`);
          document.documentElement.style.setProperty('--bg-opacity', '0.8');
        } else {
          document.documentElement.style.setProperty('--bg-image', "url('/src/assets/bg.jpg')");
          document.documentElement.style.setProperty('--bg-opacity', '0.8');
        }

        // Gọi API kiểm tra validate
        const valRes = await fetch('http://localhost:8000/api/settings/validate', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            fpt_ai_api_key: fptKey,
            elevenlabs_api_key: elevenlabsKey,
            gemini_api_key: geminiKey,
            gemini_model: geminiModel,
            openai_api_key: openaiKey,
            anthropic_api_key: anthropicKey,
            xai_api_key: xaiKey,
            groq_api_key: groqKey,
            pexels_api_key: pexelsKey,
            active_ai_provider: activeAIProvider,
            active_tts_provider: activeTTSProvider,
            ai_concurrency_limit: Number(concurrency),
            douyin_cookie: douyinCookie,
            anti_detect_provider: antiDetectProvider,
            gpm_api_url: gpmApiUrl,
            use_groq: useGroq,
            use_gpu_acceleration: useGpuAcceleration,
            enable_health_check: enableHealthCheck,
            health_check_interval_hours: Number(healthCheckInterval),
            theme_bg_type: themeBgType,
            theme_bg_custom_path: themeBgCustomPath,
            custom_ai_endpoint: customAiEndpoint,
            custom_ai_key: customAiKey,
            custom_ai_model: customAiModel
          })
        });

        if (valRes.ok) {
          const valData = await valRes.json();
          setValidateStatus({
            fpt: valData.fpt_ai_api_key,
            elevenlabs: valData.elevenlabs_api_key,
            gemini: valData.gemini_api_key,
            openai: valData.openai_api_key,
            anthropic: valData.anthropic_api_key,
            xai: valData.xai_api_key,
            groq: valData.groq_api_key,
            pexels: valData.pexels_api_key,
            douyin: valData.douyin_cookie,
            gpm: valData.gpm_api_url,
            custom: valData.custom_ai_key,
            douyin_details: valData.douyin_details || null
          });
        }

        setTimeout(() => setSaveStatus(""), 4000);
      } else {
        setSaveStatus("Lỗi khi lưu!");
      }
    } catch (e) {
      setSaveStatus("Lỗi kết nối server!");
    }
  };

  const handleCheckNow = async () => {
    try {
      setSaveStatus("Đang gửi lệnh kiểm tra...");
      const res = await fetch('http://localhost:8000/api/settings/health/check_now', { method: 'POST' });
      if (res.ok) {
        setSaveStatus("Đã gửi lệnh kiểm tra vào hàng đợi (Xem console backend)!");
        setTimeout(() => setSaveStatus(""), 4000);
      } else {
        setSaveStatus("Lỗi khi gửi lệnh!");
      }
    } catch (e) {
      setSaveStatus("Lỗi kết nối server!");
    }
  };

  const handleCheckColab = async () => {
    if (!colabGpuUrl?.trim()) return;
    setCheckingColab(true);
    setColabStatus(null);
    try {
      const res = await fetch('http://localhost:8000/api/settings/colab-status', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url: colabGpuUrl.trim() })
      });
      const data = await res.json();
      setColabStatus(data);
    } catch (err) {
      setColabStatus({ connected: false, message: `Lỗi kết nối: ${err.message}` });
    } finally {
      setCheckingColab(false);
    }
  };

  const handleUploadBg = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    
    setUploadBgStatus("Đang tải lên...");
    const formData = new FormData();
    formData.append("file", file);
    
    try {
      const res = await fetch("http://localhost:8000/api/settings/upload-background", {
        method: "POST",
        body: formData
      });
      const data = await res.json();
      if (data.status === "success") {
        setUploadBgStatus("Tải lên thành công!");
        setThemeBgCustomPath(data.url);
        // Áp dụng lập tức
        document.documentElement.style.setProperty('--bg-image', `url('http://localhost:8000${data.url}')`);
        document.documentElement.style.setProperty('--bg-opacity', '0.8');
      } else {
        setUploadBgStatus("Lỗi: " + data.message);
      }
    } catch (err) {
      setUploadBgStatus("Lỗi kết nối máy chủ");
    }
  };

  return (
    <div className="space-y-6">
      <div className="glass-panel p-6 rounded-2xl max-w-6xl w-full relative overflow-hidden">
        <div className="absolute top-0 right-0 w-32 h-32 bg-neon-purple/5 blur-3xl rounded-full pointer-events-none" />
        
        <h3 className="text-xl font-bold mb-6 tracking-tight font-display bg-gradient-to-r from-white to-text-secondary bg-clip-text text-transparent">
          Cấu Hình Hệ Thống
        </h3>

        {/* Tabs Bar */}
        <div className="flex border-b border-border-subtle overflow-x-auto pb-px gap-2 scrollbar-none mb-6">
          {settingsTabs.map((tab) => (
            <button
              key={tab.id}
              type="button"
              onClick={() => setActiveTab(tab.id)}
              className={`py-2 px-3 text-xs font-bold uppercase tracking-wider border-b-2 transition-all duration-300 cursor-pointer whitespace-nowrap pb-3 ${
                activeTab === tab.id
                  ? "border-neon-purple text-neon-purple"
                  : "border-transparent text-text-secondary hover:text-text-primary"
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>

        <form className="space-y-6">
          <div className="min-h-[350px]">
            {activeTab === "ai" && (
              <AiKeysTab
                activeAIProvider={activeAIProvider} setActiveAIProvider={setActiveAIProvider}
                geminiKey={geminiKey} setGeminiKey={setGeminiKey}
                openaiKey={openaiKey} setOpenaiKey={setOpenaiKey}
                anthropicKey={anthropicKey} setAnthropicKey={setAnthropicKey}
                xaiKey={xaiKey} setXaiKey={setXaiKey}
                geminiModel={geminiModel} setGeminiModel={setGeminiModel}
                validateStatus={validateStatus}
                useGroq={useGroq} setUseGroq={setUseGroq}
                groqKey={groqKey} setGroqKey={setGroqKey}
                pexelsKey={pexelsKey} setPexelsKey={setPexelsKey}
                customAiEndpoint={customAiEndpoint} setCustomAiEndpoint={setCustomAiEndpoint}
                customAiKey={customAiKey} setCustomAiKey={setCustomAiKey}
                customAiModel={customAiModel} setCustomAiModel={setCustomAiModel}
              />
            )}

            {activeTab === "tts" && (
              <TtsTab
                concurrency={concurrency} setConcurrency={setConcurrency}
                enableDiarization={enableDiarization} setEnableDiarization={setEnableDiarization}
                hfToken={hfToken} setHfToken={setHfToken}
                enableDemucs={enableDemucs} setEnableDemucs={setEnableDemucs}
                bgmVolume={bgmVolume} setBgmVolume={setBgmVolume}
                defaultVocalVolume={defaultVocalVolume} setDefaultVocalVolume={setDefaultVocalVolume}
                activeTTSProvider={activeTTSProvider} setActiveTTSProvider={setActiveTTSProvider}
                enableAutoVoiceClone={enableAutoVoiceClone} setEnableAutoVoiceClone={setEnableAutoVoiceClone}
                fptKey={fptKey} setFptKey={setFptKey}
                openaiKey={openaiKey} setOpenaiKey={setOpenaiKey}
                elevenlabsKey={elevenlabsKey} setElevenlabsKey={setElevenlabsKey}
                validateStatus={validateStatus}
              />
            )}

            {activeTab === "browser" && (
              <BrowserTab
                douyinCookie={douyinCookie} setDouyinCookie={setDouyinCookie}
                antiDetectProvider={antiDetectProvider} setAntiDetectProvider={setAntiDetectProvider}
                gpmApiUrl={gpmApiUrl} setGpmApiUrl={setGpmApiUrl}
                validateStatus={validateStatus}
              />
            )}

            {activeTab === "system" && (
              <SystemTab
                useGpuAcceleration={useGpuAcceleration} setUseGpuAcceleration={setUseGpuAcceleration}
                checkingGpu={checkingGpu} fetchGpuStatus={fetchGpuStatus} gpuStatus={gpuStatus}
                enableHealthCheck={enableHealthCheck} setEnableHealthCheck={setEnableHealthCheck}
                healthCheckInterval={healthCheckInterval} setHealthCheckInterval={setHealthCheckInterval}
                handleCheckNow={handleCheckNow}
                useColabGpu={useColabGpu} setUseColabGpu={setUseColabGpu}
                colabGpuUrl={colabGpuUrl} setColabGpuUrl={setColabGpuUrl}
                colabStatus={colabStatus} checkingColab={checkingColab}
                handleCheckColab={handleCheckColab}
              />
            )}

            {activeTab === "theme" && (
              <ThemeTab
                themeBgType={themeBgType} setThemeBgType={setThemeBgType}
                themeBgCustomPath={themeBgCustomPath} handleUploadBg={handleUploadBg}
                uploadBgStatus={uploadBgStatus}
              />
            )}
          </div>

          <div className="flex items-center gap-4 pt-6 border-t border-border-subtle mt-6">
            <button
              type="button"
              className="bg-brand-primary hover:bg-brand-hover text-white px-6 py-3 rounded-xl font-medium transition-all duration-200 active:scale-95 cursor-pointer text-sm"
              onClick={handleSave}
            >
              Lưu cấu hình
            </button>
            {saveStatus && (
              <span className={`text-sm font-medium ${saveStatus.includes('thành công') ? 'text-green-500' : 'text-brand-primary animate-pulse'}`}>
                {saveStatus}
              </span>
            )}
          </div>
        </form>
      </div>
    </div>
  );
};

export default Settings;
