import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Type, ShieldAlert, Sliders, Plus, Trash2, Mic, Wand2, RefreshCw, Sparkles } from 'lucide-react';
import { toast } from 'react-hot-toast';

export const SubtitleConfigPanel = ({ config }) => {
  const [availableFonts, setAvailableFonts] = useState([]);

  useEffect(() => {
    fetch('http://localhost:8000/api/settings/fonts')
      .then(res => res.json())
      .then(data => {
        if (data.fonts) {
          setAvailableFonts(data.fonts);
        }
      })
      .catch(err => console.error("Error fetching fonts:", err));
  }, []);

  return (
    <div className="space-y-6">
      {/* Transcription & Optimization Panel */}
      <div className="bg-bg-secondary/40 rounded-2xl border border-white/5 p-5 w-full relative overflow-hidden">
        <div className="flex items-center justify-between mb-4 border-b border-white/5 pb-3">
          <label className="text-sm font-bold text-text-primary flex items-center gap-2 font-display">
            <Mic size={18} className="text-neon-cyan" />
            Nhận diện giọng nói (ASR) & Ngắt câu AI
          </label>
        </div>
        
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <motion.div 
            whileHover={{ scale: 1.01 }}
            className={`flex items-center gap-3 p-3 rounded-xl border transition-colors ${
              config.useBcutAsr 
                ? 'bg-neon-cyan/10 border-neon-cyan text-neon-cyan' 
                : 'bg-bg-primary/20 border-white/5 hover:border-white/10'
            }`}
          >
            <input 
              type="checkbox" 
              id="useBcutAsrToggle" 
              checked={config.useBcutAsr} 
              onChange={(e) => config.setUseBcutAsr(e.target.checked)} 
              className="w-4 h-4 accent-neon-cyan border-border-subtle rounded cursor-pointer" 
            />
            <div className="flex flex-col flex-1">
              <label htmlFor="useBcutAsrToggle" className="text-xs font-bold cursor-pointer select-none">
                Sử dụng Bcut ASR (Miễn phí)
              </label>
              <span className="text-[10px] text-text-secondary mt-0.5">Tiết kiệm chi phí Whisper. Nhận diện cực nhanh bởi Bilibili.</span>
            </div>
            
            <button
              onClick={async () => {
                const btn = document.getElementById('testBcutBtn');
                if (btn) btn.innerHTML = '<span class="animate-spin inline-block">↻</span> Đang thử...';
                try {
                  const res = await fetch('http://localhost:8000/api/processor/test-bcut');
                  const data = await res.json();
                  if (data.status === 'success') {
                    toast.success('Kết nối Bcut API thành công! API đang hoạt động tốt.');
                  } else {
                    toast.error('Lỗi kết nối Bcut API: ' + (data.detail || data.message || 'Unknown error'));
                  }
                } catch (e) {
                  toast.error('Không thể kết nối đến server: ' + e.message);
                } finally {
                  if (btn) btn.innerHTML = 'Test API';
                }
              }}
              id="testBcutBtn"
              className="text-[10px] bg-bg-primary border border-white/10 hover:border-neon-cyan hover:text-neon-cyan px-2 py-1 rounded transition-colors"
            >
              Test API
            </button>
          </motion.div>

          <motion.div 
            whileHover={{ scale: 1.01 }}
            className={`flex items-center gap-3 p-3 rounded-xl border transition-colors ${
              config.useLlmSegmentation 
                ? 'bg-neon-purple/10 border-neon-purple text-neon-purple' 
                : 'bg-bg-primary/20 border-white/5 hover:border-white/10'
            }`}
          >
            <input 
              type="checkbox" 
              id="useLlmSegmentationToggle" 
              checked={config.useLlmSegmentation} 
              onChange={(e) => config.setUseLlmSegmentation(e.target.checked)} 
              className="w-4 h-4 accent-neon-purple border-border-subtle rounded cursor-pointer" 
            />
            <div className="flex flex-col">
              <label htmlFor="useLlmSegmentationToggle" className="text-xs font-bold cursor-pointer select-none">
                Sử dụng LLM Ngắt câu phụ đề
              </label>
              <span className="text-[10px] text-text-secondary mt-0.5">Dùng Claude để chia lại câu sao cho tự nhiên nhất thay vì bị cắt vụn.</span>
            </div>
          </motion.div>
        </div>

        {/* Cấu hình Prompt Whisper */}
        <div className="mt-4 pt-4 border-t border-white/5">
          <label className="text-xs font-bold text-text-primary flex items-center gap-2 mb-2">
            Mồi ngôn ngữ Whisper (Fallback)
          </label>
          <select 
            value={config.whisperPrompt || ''} 
            onChange={(e) => config.setWhisperPrompt(e.target.value)} 
            className="w-full bg-bg-primary/50 border border-white/10 rounded-xl p-2 text-xs text-text-primary focus:border-neon-cyan focus:outline-none transition-colors"
          >
            <option value="">Tự động (Khuyên dùng - Whisper tự nhận diện)</option>
            <option value="Bóc băng nguyên văn, đầy đủ, chính xác từng từ một, không tóm tắt, không bỏ sót chữ.">Tiếng Việt</option>
            <option value="请准确逐字转写，不要省略，不要总结。">Tiếng Trung</option>
            <option value="Transcribe accurately word by word without omitting or summarizing.">Tiếng Anh</option>
          </select>
          <p className="text-[10px] text-text-secondary mt-1">
            Chỉ áp dụng khi Bcut bị lỗi và hệ thống lùi về dùng Whisper. "Tự động" giúp chống lỗi ảo giác lệch thời gian.
          </p>
        </div>
      </div>

      {/* AI Subtitle Polish & Script Doctor Panel */}
      <div className="bg-bg-secondary/40 rounded-2xl border border-white/5 p-5 w-full relative overflow-hidden">
        <div className="flex items-center justify-between mb-4 border-b border-white/5 pb-3">
          <div className="flex items-center gap-2">
            <Wand2 size={18} className="text-neon-cyan" />
            <label className="text-sm font-bold text-text-primary font-display flex items-center gap-2">
              Hiệu chỉnh & Làm đẹp Phụ đề AI
              <span className="px-2 py-0.5 text-[10px] font-semibold bg-neon-cyan/15 text-neon-cyan border border-neon-cyan/25 rounded-full">
                AI Script Doctor
              </span>
            </label>
          </div>

          <label className="relative inline-flex items-center cursor-pointer">
            <input 
              type="checkbox" 
              checked={config.enableAiSubtitlePolish ?? true} 
              onChange={(e) => config.setEnableAiSubtitlePolish(e.target.checked)} 
              className="sr-only peer"
            />
            <div className="w-9 h-5 bg-bg-primary peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-border-subtle after:border after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-neon-cyan"></div>
          </label>
        </div>

        <p className="text-xs text-text-secondary mb-4 leading-relaxed">
          Tự động hàn gắn câu cụt lủn do Whisper cắt vụn, chèn dấu ngắt nghỉ chuẩn xác cho giọng đọc TTS truyền cảm, và cân đối độ dài thị giác (5–8 từ/dòng).
        </p>

        {config.enableAiSubtitlePolish && (
          <motion.div 
            initial={{ opacity: 0, y: -8 }}
            animate={{ opacity: 1, y: 0 }}
            className="space-y-3"
          >
            <label className="text-xs font-bold text-text-primary flex items-center gap-1.5">
              <Sparkles size={14} className="text-amber-400" />
              Phong cách Kịch bản & Ngôn từ
            </label>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              {[
                {
                  id: "tiktok_viral",
                  icon: "⚡",
                  title: "TikTok Viral",
                  desc: "Ngắn gọn, giật tít nhẹ, bắt trend, cuốn hút ngay 3s đầu",
                  color: "border-neon-cyan bg-neon-cyan/10 text-neon-cyan"
                },
                {
                  id: "reviewer",
                  icon: "🍜",
                  title: "Reviewer / Đời sống",
                  desc: "Trực diện, chân thực, hào hứng, cảm nhận sắc sảo",
                  color: "border-neon-pink bg-neon-pink/10 text-neon-pink"
                },
                {
                  id: "storytelling",
                  icon: "📖",
                  title: "Kể chuyện / Tâm sự",
                  desc: "Mượt mà, sâu lắng, trau chuốt, giàu cảm xúc",
                  color: "border-neon-purple bg-neon-purple/10 text-neon-purple"
                },
                {
                  id: "formal",
                  icon: "📰",
                  title: "Tin tức / Kiến thức",
                  desc: "Gãy gọn, chuẩn xác, trung tính, cấu trúc chuẩn",
                  color: "border-emerald-400 bg-emerald-400/10 text-emerald-400"
                }
              ].map((style) => {
                const isSelected = (config.subtitlePolishStyle || 'tiktok_viral') === style.id;
                return (
                  <div
                    key={style.id}
                    onClick={() => config.setSubtitlePolishStyle(style.id)}
                    className={`p-3 rounded-xl border cursor-pointer transition-all duration-200 ${
                      isSelected 
                        ? `${style.color} shadow-sm ring-1 ring-white/10` 
                        : 'bg-bg-primary/20 border-white/5 hover:border-white/10 text-text-secondary hover:text-text-primary'
                    }`}
                  >
                    <div className="flex items-center gap-2 font-bold text-xs mb-1">
                      <span>{style.icon}</span>
                      <span>{style.title}</span>
                      {isSelected && <span className="ml-auto text-[10px] font-mono font-bold">✓ Đang chọn</span>}
                    </div>
                    <div className="text-[11px] opacity-80 leading-snug">
                      {style.desc}
                    </div>
                  </div>
                );
              })}
            </div>
          </motion.div>
        )}
      </div>

      {/* Micro-alterations Panel */}
      <div className="bg-bg-secondary/40 rounded-2xl border border-white/5 p-5 w-full relative overflow-hidden">
        <div className="flex items-center justify-between mb-4 border-b border-white/5 pb-3">
          <label className="text-sm font-bold text-text-primary flex items-center gap-2 font-display">
            <ShieldAlert size={18} className="text-neon-pink" />
            Tính năng Siêu lách bản quyền (Micro-alterations)
          </label>
          <motion.button 
            whileHover={!config.optRandomCombo ? { scale: 1.05 } : {}}
            whileTap={!config.optRandomCombo ? { scale: 0.95 } : {}}
            type="button" 
            onClick={config.toggleAllMicroAlterations}
            disabled={config.optRandomCombo}
            className={`text-xs px-3 py-1.5 rounded-lg font-bold transition-all duration-300 shadow-sm ${
              config.optRandomCombo 
                ? 'bg-white/5 text-white/30 border border-white/5 cursor-not-allowed' 
                : 'bg-neon-pink/15 text-neon-pink border border-neon-pink/20 hover:bg-neon-pink hover:text-white cursor-pointer'
            }`}
          >
            Chọn tất cả
          </motion.button>
        </div>
        
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          {[
            { id: "flipVideoEdit", label: "Lật gương (Mirror)", checked: config.flipVideo, onChange: (e) => config.setFlipVideo(e.target.checked) },
            { id: "optZoomEdit", label: "Zoom 2%", checked: config.optZoom, onChange: (e) => config.setOptZoom(e.target.checked) },
            { id: "optColorEdit", label: "Tăng màu (EQ)", checked: config.optColor, onChange: (e) => config.setOptColor(e.target.checked) },
            { id: "optNoiseEdit", label: "Nhiễu hạt (Noise)", checked: config.optNoise, onChange: (e) => config.setOptNoise(e.target.checked) },
          ].map((item) => (
            <motion.div 
              whileHover={!config.optRandomCombo ? { x: 2 } : {}}
              key={item.id} 
              className={`flex items-center gap-3 p-2.5 rounded-xl border transition-colors ${
                config.optRandomCombo 
                  ? 'bg-bg-primary/10 border-transparent opacity-40 grayscale pointer-events-none' 
                  : 'bg-bg-primary/20 border-white/5 hover:border-white/10'
              }`}
            >
              <input 
                type="checkbox" 
                id={item.id} 
                checked={item.checked} 
                onChange={item.onChange} 
                disabled={config.optRandomCombo}
                className="w-4 h-4 accent-neon-pink border-border-subtle rounded cursor-pointer disabled:cursor-not-allowed" 
              />
              <label htmlFor={item.id} className="text-xs font-semibold text-text-secondary cursor-pointer select-none hover:text-text-primary transition-colors">
                {item.label}
              </label>
            </motion.div>
          ))}
          <motion.div 
            whileHover={!config.optRandomCombo ? { x: 2 } : {}}
            className={`flex items-center gap-3 p-2.5 rounded-xl border transition-colors sm:col-span-2 ${
              config.optRandomCombo 
                ? 'bg-bg-primary/10 border-transparent opacity-40 grayscale pointer-events-none' 
                : 'bg-bg-primary/20 border-white/5 hover:border-white/10'
            }`}
          >
            <input 
              type="checkbox" 
              id="optPitchEdit" 
              checked={config.optPitch} 
              onChange={(e) => config.setOptPitch(e.target.checked)} 
              disabled={config.optRandomCombo}
              className="w-4 h-4 accent-neon-pink border-border-subtle rounded cursor-pointer disabled:cursor-not-allowed" 
            />
            <label htmlFor="optPitchEdit" className="text-xs font-semibold text-text-secondary cursor-pointer select-none hover:text-text-primary transition-colors">
              Đổi tần số âm thanh (Pitch 2%)
            </label>
          </motion.div>
          <motion.div 
            whileHover={!config.optRandomCombo ? { x: 2 } : {}}
            className={`flex items-center gap-3 p-2.5 rounded-xl border transition-colors sm:col-span-2 ${
              config.optRandomCombo 
                ? 'bg-bg-primary/10 border-transparent opacity-40 grayscale pointer-events-none' 
                : 'bg-bg-primary/20 border-white/5 hover:border-white/10'
            }`}
          >
            <input 
              type="checkbox" 
              id="optSpeedEdit" 
              checked={config.optSpeed} 
              onChange={(e) => config.setOptSpeed(e.target.checked)} 
              disabled={config.optRandomCombo}
              className="w-4 h-4 accent-neon-pink border-border-subtle rounded cursor-pointer disabled:cursor-not-allowed" 
            />
            <label htmlFor="optSpeedEdit" className="text-xs font-semibold text-text-secondary cursor-pointer select-none hover:text-text-primary transition-colors">
              Đổi tốc độ video & âm thanh (Tăng 3%)
            </label>
          </motion.div>
          <motion.div 
            whileHover={!config.optRandomCombo ? { x: 2 } : {}}
            className={`flex items-center gap-3 p-2.5 rounded-xl border transition-colors sm:col-span-2 ${
              config.optRandomCombo 
                ? 'bg-bg-primary/10 border-transparent opacity-40 grayscale pointer-events-none' 
                : 'bg-bg-primary/20 border-white/5 hover:border-white/10'
            }`}
          >
            <input 
              type="checkbox" 
              id="optReverbEdit" 
              checked={config.optReverb} 
              onChange={(e) => config.setOptReverb(e.target.checked)} 
              disabled={config.optRandomCombo}
              className="w-4 h-4 accent-neon-pink border-border-subtle rounded cursor-pointer disabled:cursor-not-allowed" 
            />
            <label htmlFor="optReverbEdit" className="text-xs font-semibold text-text-secondary cursor-pointer select-none hover:text-text-primary transition-colors">
              Thêm hiệu ứng vang (Reverb âm thanh)
            </label>
          </motion.div>
          <motion.div 
            whileHover={!config.optRandomCombo ? { x: 2 } : {}}
            className={`flex items-center gap-3 p-2.5 rounded-xl border transition-colors sm:col-span-2 ${
              config.optRandomCombo 
                ? 'bg-bg-primary/10 border-transparent opacity-40 grayscale pointer-events-none' 
                : 'bg-bg-primary/20 border-white/5 hover:border-white/10'
            }`}
          >
            <input 
              type="checkbox" 
              id="optVignetteEdit" 
              checked={config.optVignette} 
              onChange={(e) => config.setOptVignette(e.target.checked)} 
              disabled={config.optRandomCombo}
              className="w-4 h-4 accent-neon-pink border-border-subtle rounded cursor-pointer disabled:cursor-not-allowed" 
            />
            <label htmlFor="optVignetteEdit" className="text-xs font-semibold text-text-secondary cursor-pointer select-none hover:text-text-primary transition-colors">
              Thêm hiệu ứng tối 4 góc (Vignette)
            </label>
          </motion.div>
        </div>
        
        {/* Random Combo Toggle */}
        <motion.div 
          whileHover={{ scale: 1.01 }}
          className={`flex items-center gap-3 p-3 rounded-xl border transition-all duration-300 mt-3 ${
            config.optRandomCombo 
              ? 'bg-gradient-to-r from-purple-500/20 to-neon-pink/20 border-purple-400/40 shadow-lg shadow-purple-500/10' 
              : 'bg-bg-primary/20 border-white/5 hover:border-white/10'
          }`}
        >
          <input 
            type="checkbox" 
            id="optRandomComboEdit" 
            checked={config.optRandomCombo} 
            onChange={(e) => config.setOptRandomCombo(e.target.checked)} 
            className="w-4 h-4 accent-purple-500 border-border-subtle rounded cursor-pointer" 
          />
          <label htmlFor="optRandomComboEdit" className="text-xs font-bold cursor-pointer select-none transition-colors flex items-center gap-2" style={{ color: config.optRandomCombo ? '#c084fc' : 'var(--text-secondary)' }}>
            🎲 Combo Ngẫu Nhiên (Mỗi video khác nhau)
          </label>
        </motion.div>

        {/* Anti-Copyright Score Bar */}
        <div className="mt-4 px-1">
          <div className="flex items-center justify-between mb-1.5">
            <span className="text-xs font-bold text-text-secondary">🛡️ Anti-Copyright Score</span>
            <span className={`text-xs font-extrabold ${
              config.antiCopyrightScore >= 60 ? 'text-green-400' : config.antiCopyrightScore >= 30 ? 'text-yellow-400' : 'text-red-400'
            }`}>
              {config.antiCopyrightScore}%
            </span>
          </div>
          <div className="w-full h-2.5 bg-bg-primary/40 rounded-full overflow-hidden border border-white/5">
            <motion.div 
              className="h-full rounded-full"
              initial={{ width: 0 }}
              animate={{ width: `${config.antiCopyrightScore}%` }}
              transition={{ duration: 0.5, ease: "easeOut" }}
              style={{
                background: config.antiCopyrightScore >= 60 
                  ? 'linear-gradient(90deg, #22c55e, #4ade80)' 
                  : config.antiCopyrightScore >= 30 
                    ? 'linear-gradient(90deg, #eab308, #facc15)' 
                    : 'linear-gradient(90deg, #ef4444, #f87171)'
              }}
            />
          </div>
          <div className="flex justify-between mt-1">
            <span className="text-[10px] text-red-400/60">Nguy hiểm</span>
            <span className="text-[10px] text-yellow-400/60">Trung bình</span>
            <span className="text-[10px] text-green-400/60">An toàn</span>
          </div>
        </div>
      </div>

      {/* Logo Masking Panel */}
      <div className="bg-bg-secondary/40 rounded-2xl border border-white/5 p-5 w-full relative overflow-hidden">
        <div className="flex items-center justify-between mb-4 border-b border-white/5 pb-3">
          <label className="text-sm font-bold text-text-primary flex items-center gap-2 font-display">
            <Sliders size={18} className="text-neon-pink" />
            Che Logo Video Gốc
          </label>
          <div className="flex items-center gap-3">
            <label className="flex items-center gap-2 cursor-pointer bg-bg-primary/40 px-3 py-1.5 rounded-xl border border-white/5 hover:border-white/10 transition-colors">
              <input
                type="checkbox"
                checked={config.maskEnabled}
                onChange={(e) => config.setMaskEnabled(e.target.checked)}
                className="w-4 h-4 accent-neon-pink cursor-pointer rounded"
              />
              <span className="text-xs font-bold text-text-secondary select-none">Bật Che Logo</span>
            </label>
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              type="button"
              onClick={config.addMask}
              className="flex items-center gap-1 text-xs bg-neon-pink/15 text-neon-pink border border-neon-pink/20 px-3 py-1.5 rounded-lg hover:bg-neon-pink hover:text-white font-bold transition-all duration-300 cursor-pointer shadow-sm"
            >
              <Plus size={14} />
              Thêm Ô Che
            </motion.button>
          </div>
        </div>

        <div className={`transition-opacity duration-300 ${config.maskEnabled ? 'opacity-100' : 'opacity-40 pointer-events-none'}`}>
          {/* List of current masks */}
          <div className="flex flex-wrap gap-2 mb-4">
            {(config.masks || []).length === 0 ? (
              <span className="text-xs text-text-secondary italic">Chưa có ô che nào. Nhấp "Thêm Ô Che" để bắt đầu.</span>
            ) : (
              (config.masks || []).map((mask, idx) => {
                const isActive = mask.id === config.activeMaskId;
                return (
                  <div
                    key={mask.id}
                    className={`flex items-center gap-2 px-3 py-1.5 rounded-xl border text-xs font-semibold transition-all cursor-pointer ${
                      isActive
                        ? 'bg-neon-pink/10 border-neon-pink text-neon-pink shadow-sm'
                        : 'bg-bg-primary/40 border-white/5 text-text-secondary hover:border-white/10'
                    }`}
                    onClick={() => config.setActiveMaskId(mask.id)}
                  >
                    <span>Ô #{idx + 1} ({mask.type === 'color' ? 'Màu' : mask.type === 'blur' ? 'Mờ' : 'Nhiễu'})</span>
                    <button
                      type="button"
                      onClick={(e) => {
                        e.stopPropagation();
                        config.removeMask(mask.id);
                      }}
                      className="text-text-secondary hover:text-neon-pink p-0.5 rounded transition-colors"
                      title="Xóa ô này"
                    >
                      <Trash2 size={12} />
                    </button>
                  </div>
                );
              })
            )}
          </div>

          {/* Configuration form for the active mask */}
          {config.masks && config.masks.length > 0 && (() => {
            const activeMask = config.masks.find(m => m.id === config.activeMaskId) || config.masks[0];
            if (!activeMask) return null;
            return (
              <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4 items-end bg-bg-primary/20 border border-white/5 rounded-xl p-4">
                <div className="flex flex-col gap-1.5 sm:col-span-1">
                  <label className="text-xs font-bold text-text-secondary uppercase tracking-wider">
                    Cấu hình Ô Che #{config.masks.findIndex(m => m.id === activeMask.id) + 1}
                  </label>
                  <select
                    value={activeMask.type}
                    onChange={(e) => config.updateMask(activeMask.id, { type: e.target.value })}
                    className="w-full bg-bg-primary border border-border-subtle text-text-primary text-xs rounded-xl px-3 py-2.5 focus:outline-none focus:border-neon-purple cursor-pointer"
                  >
                    <option value="color">Che màu (Solid Box)</option>
                    <option value="blur">Làm mờ (Blur)</option>
                    <option value="noise">Làm nhiễu (Noise)</option>
                  </select>
                </div>

                {activeMask.type === 'color' && (
                  <div className="flex items-center justify-between bg-bg-primary/60 border border-border-subtle rounded-xl p-2 h-[38px]">
                    <label className="text-xs font-bold text-text-secondary uppercase tracking-wider pl-1">Màu Sắc Ô Che</label>
                    <input 
                      type="color" 
                      value={activeMask.color || '#000000'} 
                      onChange={(e) => config.updateMask(activeMask.id, { color: e.target.value })} 
                      className="w-7 h-7 p-0 border-0 rounded-lg cursor-pointer bg-transparent"
                    />
                  </div>
                )}
                
                <div className="flex flex-col gap-1.5 bg-bg-primary/30 border border-border-subtle rounded-xl p-2.5 h-[38px] justify-center sm:col-span-1">
                  <span className="text-[10px] font-bold text-text-secondary uppercase tracking-wider">
                    Kéo thả & co giãn ô trên Preview
                  </span>
                </div>
              </div>
            );
          })()}
        </div>
      </div>

      {/* Subtitle Customization Panel */}
      <div className="bg-bg-secondary/40 rounded-2xl border border-white/5 p-5 w-full relative overflow-hidden">
        <div className="flex items-center justify-between mb-4 flex-wrap gap-2">
          <h3 className="text-sm font-bold text-text-primary flex items-center gap-2 font-display">
            <Type size={18} className="text-neon-purple" />
            Tùy chỉnh Phụ Đề
          </h3>
          <label className="flex items-center gap-2 cursor-pointer bg-bg-primary/40 px-3 py-1.5 rounded-xl border border-white/5 hover:border-white/10 transition-colors">
            <input
              type="checkbox"
              checked={config.enableSubtitles}
              onChange={(e) => config.setEnableSubtitles(e.target.checked)}
              className="w-4 h-4 accent-neon-pink cursor-pointer rounded"
            />
            <span className="text-xs font-bold text-text-secondary select-none">Bật Phụ Đề / Dịch Thuật</span>
          </label>
        </div>
        
        <div className={`flex flex-col gap-5 transition-opacity duration-300 ${config.enableSubtitles ? 'opacity-100' : 'opacity-40 pointer-events-none'}`}>
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-4 items-end">
            <div className="flex flex-col gap-1.5">
              <label className="text-xs font-bold text-text-secondary uppercase tracking-wider">Font chữ</label>
              <select
                value={config.subtitleFont}
                onChange={e => config.setSubtitleFont(e.target.value)}
                className="w-full bg-bg-primary border border-border-subtle text-text-primary text-xs rounded-xl px-3 py-2.5 focus:outline-none focus:border-neon-purple cursor-pointer"
              >
                {availableFonts.map(f => (
                  <option key={f.id} value={f.id}>{f.name}</option>
                ))}
              </select>
            </div>
            
            <div className="flex flex-col gap-1.5">
              <label className="text-xs font-bold text-text-secondary uppercase tracking-wider">Kiểu Nền (Style)</label>
              <select
                value={config.subtitleStyle}
                onChange={e => config.setSubtitleStyle(e.target.value)}
                className="w-full bg-bg-primary border border-border-subtle text-text-primary text-xs rounded-xl px-3 py-2.5 focus:outline-none focus:border-neon-purple cursor-pointer"
              >
                <option value="classic">Cổ điển (Vuông)</option>
                <option value="rounded">Bo Góc (Sang trọng)</option>
                <option value="cloud">Đám mây (Lượn sóng)</option>
                <option value="neon">Neon Glow (Phát sáng)</option>
              </select>
            </div>
            
            <div className="flex items-center justify-between bg-bg-primary/60 border border-border-subtle rounded-xl p-2 h-[38px]">
              <label className="text-xs font-bold text-text-secondary uppercase tracking-wider pl-1">Màu Chữ</label>
              <input 
                type="color" 
                value={config.subtitleTextColor} 
                onChange={e => config.setSubtitleTextColor(e.target.value)} 
                className="w-7 h-7 p-0 border-0 rounded-lg cursor-pointer bg-transparent"
              />
            </div>
            
            <div className="flex items-center justify-between bg-bg-primary/60 border border-border-subtle rounded-xl p-2 h-[38px]">
              <label className="text-xs font-bold text-text-secondary uppercase tracking-wider pl-1">Màu Nền</label>
              <input 
                type="color" 
                value={config.subtitleBgColor} 
                onChange={e => config.setSubtitleBgColor(e.target.value)} 
                className="w-7 h-7 p-0 border-0 rounded-lg cursor-pointer bg-transparent"
              />
            </div>
            
            <div className="flex flex-col gap-1.5 bg-bg-primary/30 border border-border-subtle rounded-xl p-2.5 h-[38px] justify-center">
              <label className="text-[10px] font-bold text-text-secondary uppercase tracking-wider flex justify-between">
                <span>Opacity Nền</span>
                <span className="text-neon-purple font-mono font-bold">{config.subtitleBgOpacity}%</span>
              </label>
              <input 
                type="range" 
                min="0" max="100" 
                value={config.subtitleBgOpacity} 
                onChange={e => config.setSubtitleBgOpacity(Number(e.target.value))} 
                className="w-full h-1 bg-border-subtle rounded-lg appearance-none cursor-pointer accent-neon-purple"
              />
            </div>
          </div>
          
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div className="flex flex-col gap-2 bg-bg-primary/30 border border-border-subtle rounded-xl p-3 sm:col-span-2">
              <label className="text-xs font-bold text-text-secondary uppercase tracking-wider flex justify-between">
                <span>Nội Dung Phụ Đề Mẫu</span>
              </label>
              <input 
                type="text" 
                value={config.previewSubtitleText || ''} 
                onChange={e => config.setPreviewSubtitleText(e.target.value)} 
                placeholder="Nhập nội dung mẫu..."
                className="w-full bg-bg-primary border border-white/5 text-text-primary text-sm rounded-lg px-3 py-2 focus:outline-none focus:border-neon-purple"
              />
            </div>
            
            <div className="flex flex-col gap-2 bg-bg-primary/30 border border-border-subtle rounded-xl p-3">
              <label className="text-xs font-bold text-text-secondary uppercase tracking-wider flex justify-between">
                <span>Kích Thước Chữ</span>
                <span className="text-neon-pink font-mono font-bold">{config.subtitleFontSize}px</span>
              </label>
              <input 
                type="range" 
                min="2" max="20" 
                value={config.subtitleFontSize} 
                onChange={e => config.setSubtitleFontSize(Number(e.target.value))} 
                className="w-full h-1 bg-border-subtle rounded-lg appearance-none cursor-pointer accent-neon-pink"
              />
            </div>
            
            <div className="flex flex-col gap-2 bg-bg-primary/30 border border-border-subtle rounded-xl p-3">
              <label className="text-xs font-bold text-text-secondary uppercase tracking-wider flex justify-between">
                <span>Độ Dày Nền</span>
                <span className="text-neon-purple font-mono font-bold">{config.subtitleBgPadding}</span>
              </label>
              <input 
                type="range" 
                min="0" max="15" 
                value={config.subtitleBgPadding} 
                onChange={e => config.setSubtitleBgPadding(Number(e.target.value))} 
                className="w-full h-1 bg-border-subtle rounded-lg appearance-none cursor-pointer accent-neon-purple"
              />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
