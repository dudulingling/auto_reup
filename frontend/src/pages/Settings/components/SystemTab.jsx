import React from 'react';

const SystemTab = ({
  useGpuAcceleration, setUseGpuAcceleration,
  checkingGpu, fetchGpuStatus, gpuStatus,
  enableHealthCheck, setEnableHealthCheck,
  healthCheckInterval, setHealthCheckInterval,
  handleCheckNow,
  useColabGpu, setUseColabGpu,
  colabGpuUrl, setColabGpuUrl,
  colabStatus, checkingColab, handleCheckColab
}) => {
  return (
    <div className="space-y-6">
      <div className="bg-bg-tertiary/40 p-4 rounded-xl border border-border-subtle">
        <div className="flex items-center justify-between mb-2">
          <label className="block text-sm font-bold text-text-primary">🖥️ Tăng tốc phần cứng (GPU Acceleration)</label>
          <label className="relative inline-flex items-center cursor-pointer">
            <input
              type="checkbox"
              className="sr-only peer"
              checked={useGpuAcceleration}
              onChange={(e) => setUseGpuAcceleration(e.target.checked)}
            />
            <div className="w-11 h-6 bg-gray-600 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-green-500"></div>
          </label>
        </div>
        <p className="text-xs text-text-secondary mb-4">Sử dụng GPU (Intel QSV / Nvidia NVENC) để tăng tốc độ xử lý video bằng FFMPEG và giảm tải CPU. Hệ thống sẽ tự động quét và kiểm tra xem thiết bị của bạn có hỗ trợ GPU nào không.</p>
        
        {/* GPU Check Status Box */}
        <div className="mt-3 pt-3 border-t border-border-subtle/50">
          <div className="flex items-center justify-between mb-2">
            <span className="text-[10px] font-bold text-text-secondary uppercase tracking-wider">🔍 Trạng thái phần cứng GPU:</span>
            <button
              type="button"
              onClick={fetchGpuStatus}
              disabled={checkingGpu}
              className="text-[9px] bg-bg-secondary hover:bg-bg-tertiary text-text-primary border border-border-subtle px-2 py-0.5 rounded transition-colors disabled:opacity-50 font-bold uppercase tracking-wide cursor-pointer"
            >
              {checkingGpu ? "Đang quét..." : "🔄 Quét lại"}
            </button>
          </div>
          {checkingGpu ? (
            <p className="text-xs text-neon-purple animate-pulse">Đang kiểm tra khả năng tương thích của GPU...</p>
          ) : gpuStatus ? (
            <div className="space-y-2">
              <div className="flex items-center gap-2">
                <span className={`w-2.5 h-2.5 rounded-full ${gpuStatus.can_use_gpu_acceleration ? 'bg-green-500 animate-pulse' : gpuStatus.gpu_available ? 'bg-amber-500' : 'bg-gray-500'}`} />
                <span className="text-xs font-semibold text-text-primary">{gpuStatus.gpu_name}</span>
                {gpuStatus.gpu_available && (
                  <span className="text-[10px] bg-neon-purple/20 text-neon-purple px-1.5 py-0.5 rounded font-mono font-bold">CUDA {gpuStatus.cuda_version}</span>
                )}
              </div>
              <p className={`text-xs ${gpuStatus.can_use_gpu_acceleration ? 'text-green-500' : gpuStatus.gpu_available ? 'text-amber-500' : 'text-text-secondary'}`}>
                {gpuStatus.message}
              </p>
              {gpuStatus.gpu_available && (
                <div className="text-[10px] text-text-secondary/80 bg-bg-secondary/40 p-2 rounded border border-border-subtle/30 space-y-1">
                  <p>• GPU rời NVIDIA hỗ trợ: <span className="text-green-500 font-semibold">Có</span></p>
                  <p>• FFmpeg NVENC (Bộ giải mã card rời): <span className={gpuStatus.ffmpeg_nvenc_available ? 'text-green-500 font-semibold' : 'text-red-500 font-semibold'}>{gpuStatus.ffmpeg_nvenc_available ? 'Khả dụng (✓)' : 'Không tìm thấy (✕)'}</span></p>
                </div>
              )}
            </div>
          ) : (
            <p className="text-xs text-text-secondary italic">Chưa thực hiện quét phần cứng.</p>
          )}
        </div>
      </div>

      {/* Google Colab T4 GPU Worker Card */}
      <div className="bg-bg-tertiary/40 p-4 rounded-xl border border-border-subtle relative overflow-hidden">
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-2">
            <span className="text-base">☁️</span>
            <div>
              <label className="block text-sm font-bold text-text-primary">Google Colab GPU (Tesla T4 Miễn Phí)</label>
              <span className="text-[10px] text-neon-purple font-mono uppercase tracking-wider font-semibold">Mô hình Lai (Hybrid Worker)</span>
            </div>
          </div>
          <label className="relative inline-flex items-center cursor-pointer">
            <input
              type="checkbox"
              className="sr-only peer"
              checked={useColabGpu}
              onChange={(e) => setUseColabGpu(e.target.checked)}
            />
            <div className="w-11 h-6 bg-gray-600 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-neon-purple"></div>
          </label>
        </div>
        <p className="text-xs text-text-secondary mb-4">
          Tự động điều phối các tác vụ nặng (Bóc tách phụ đề Faster-Whisper, Lồng tiếng VieNeu-TTS, Tách giọng UVR5, Render NVENC 60fps+) sang máy ảo Google Colab T4 16GB VRAM để xử lý siêu tốc.
        </p>

        <div className="space-y-3">
          <div>
            <label className="block text-xs font-medium text-text-secondary mb-1.5">
              Đường dẫn Cloudflare Tunnel Colab (Public HTTPS URL)
            </label>
            <div className="flex gap-2">
              <input
                type="text"
                className="flex-1 bg-bg-secondary border border-border-subtle rounded-xl py-2 px-3 text-xs text-text-primary font-mono placeholder:text-text-muted focus:outline-none focus:ring-2 focus:ring-neon-purple/50 transition-all"
                placeholder="https://xyz-random-domain.trycloudflare.com"
                value={colabGpuUrl}
                onChange={(e) => setColabGpuUrl(e.target.value)}
                disabled={!useColabGpu}
              />
              <button
                type="button"
                onClick={handleCheckColab}
                disabled={!useColabGpu || checkingColab || !colabGpuUrl?.trim()}
                className="bg-neon-purple/20 hover:bg-neon-purple/30 text-neon-purple border border-neon-purple/40 px-3 py-2 rounded-xl text-xs font-bold transition-all disabled:opacity-40 disabled:cursor-not-allowed cursor-pointer flex items-center gap-1.5 whitespace-nowrap"
              >
                {checkingColab ? (
                  <>
                    <span className="w-3 h-3 border-2 border-neon-purple border-t-transparent rounded-full animate-spin"></span>
                    <span>Đang kiểm tra...</span>
                  </>
                ) : (
                  <>
                    <span>⚡</span>
                    <span>Kiểm tra kết nối</span>
                  </>
                )}
              </button>
            </div>
          </div>

          {/* Trạng thái kết nối Colab */}
          {colabStatus && (
            <div className={`text-xs p-3 rounded-xl border transition-all ${
              colabStatus.connected
                ? "bg-green-500/10 border-green-500/30 text-green-400"
                : "bg-red-500/10 border-red-500/30 text-red-400"
            }`}>
              <div className="flex items-center gap-2 font-semibold">
                <span className={`w-2.5 h-2.5 rounded-full ${colabStatus.connected ? "bg-green-500 animate-pulse" : "bg-red-500"}`} />
                <span>{colabStatus.message}</span>
              </div>
              {colabStatus.connected && (
                <div className="mt-2 text-[11px] grid grid-cols-2 sm:grid-cols-4 gap-2 pt-2 border-t border-green-500/20 text-text-secondary">
                  <div>GPU: <span className="text-white font-mono font-bold">{colabStatus.gpu_name}</span></div>
                  <div>VRAM: <span className="text-white font-mono font-bold">{Math.round((colabStatus.vram_free_mb || 0) / 1024)}GB trống</span></div>
                  <div>NVENC: <span className="text-green-400 font-bold">{colabStatus.nvenc_supported ? "Khả dụng (✓)" : "Không (✕)"}</span></div>
                  <div>Độ trễ: <span className="text-neon-cyan font-mono font-bold">{colabStatus.latency_ms}ms</span></div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      <div className="bg-bg-tertiary/40 p-4 rounded-xl border border-border-subtle">
        <div className="flex items-center justify-between mb-2">
          <label className="block text-sm font-bold text-text-primary">🏥 Giám sát Sức khỏe Tài khoản (Shadowban Check)</label>
          <label className="relative inline-flex items-center cursor-pointer">
            <input
              type="checkbox"
              className="sr-only peer"
              checked={enableHealthCheck}
              onChange={(e) => setEnableHealthCheck(e.target.checked)}
            />
            <div className="w-11 h-6 bg-gray-600 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-green-500"></div>
          </label>
        </div>
        <p className="text-xs text-text-secondary mb-4">Tự động dùng trình duyệt quét số lượt xem của các video mới đăng trong vòng 3 ngày. Nếu 0 view liên tục, hệ thống sẽ cảnh báo đỏ (Shadowbanned).</p>
        
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label className="block text-xs font-medium text-text-secondary mb-2">Chu kỳ kiểm tra</label>
            <select
              className="w-full bg-bg-secondary border border-border-subtle rounded-xl py-2.5 px-3 text-xs text-text-primary focus:outline-none focus:ring-2 focus:ring-brand-primary/50 transition-all duration-200 cursor-pointer"
              value={healthCheckInterval}
              onChange={(e) => setHealthCheckInterval(Number(e.target.value))}
              disabled={!enableHealthCheck}
            >
              <option value={4}>Mỗi 4 giờ (Khuyên dùng)</option>
              <option value={8}>Mỗi 8 giờ</option>
              <option value={12}>Mỗi 12 giờ</option>
              <option value={24}>Mỗi 24 giờ</option>
            </select>
          </div>
          <div className="flex items-end">
            <button
              type="button"
              onClick={handleCheckNow}
              className="w-full bg-bg-secondary hover:bg-bg-tertiary border border-border-subtle text-text-primary px-4 py-2.5 rounded-xl text-xs font-bold transition-all duration-200 cursor-pointer"
            >
              🔍 Kiểm tra ngay
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SystemTab;
