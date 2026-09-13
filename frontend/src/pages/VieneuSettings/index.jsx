import React, { useState, useEffect } from 'react';
import { Volume2, Play, Pause, Cpu, AlertTriangle, CheckCircle2, MessageSquare, Loader2, Upload, Trash2, Plus, FileAudio } from 'lucide-react';
import { toast } from 'react-hot-toast';

const VieneuSettings = () => {
  const [voices, setVoices] = useState([]);
  const [selectedVoice, setSelectedVoice] = useState('Trúc Ly');
  const [emotion, setEmotion] = useState('natural');
  const [text, setText] = useState('Xin chào, đây là âm thanh chạy thử nghiệm của hệ thống lồng tiếng tự động VieNeu. Hệ thống đang hoạt động ổn định trên phần cứng của bạn.');
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState({ loaded: false, error: null, message: 'Đang kết nối hệ thống...' });
  const [gpuStatus, setGpuStatus] = useState(null);
  const [audioUrl, setAudioUrl] = useState('');
  const [audioKey, setAudioKey] = useState(0); // for cache-busting
  const [clones, setClones] = useState([]);
  const [cloneName, setCloneName] = useState('');
  const [cloneFile, setCloneFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [playingCloneUrl, setPlayingCloneUrl] = useState(null);
  const [playingAudio, setPlayingAudio] = useState(null);

  // Fetch status and voices
  const fetchStatusAndVoices = async () => {
    try {
      const res = await fetch('http://localhost:8000/api/settings/vieneu/voices');
      const data = await res.json();
      if (data.status === 'success') {
        setVoices(data.voices || []);
        if (data.voices && data.voices.length > 0) {
          const defaultVoice = data.voices.find(v => v.id === 'Trúc Ly' || v.id === 'vieneu_Trúc Ly' || (v.name && v.name.includes('Trúc Ly')));
          setSelectedVoice(defaultVoice ? defaultVoice.id : data.voices[0].id);
        }
        setStatus({ loaded: true, error: null, message: 'Mô hình VieNeu-TTS đã tải và sẵn sàng hoạt động!' });
      } else {
        setStatus({ loaded: false, error: data.message, message: 'Không thể nạp mô hình VieNeu-TTS.' });
      }
    } catch (err) {
      console.error(err);
      setStatus({ 
        loaded: false, 
        error: 'Lỗi kết nối tới máy chủ backend. Vui lòng đảm bảo container backend đang chạy.', 
        message: 'Lỗi kết nối máy chủ.' 
      });
    }
  };

  // Fetch GPU Acceleration Status
  const fetchGpuStatus = async () => {
    try {
      const res = await fetch('http://localhost:8000/api/settings/gpu-status');
      const data = await res.json();
      setGpuStatus(data);
    } catch (err) {
      console.error("Lỗi fetch GPU:", err);
    }
  };

  const fetchClones = async () => {
    try {
      const res = await fetch('http://localhost:8000/api/settings/vieneu/clones');
      const data = await res.json();
      if (data.status === 'success') {
        setClones(data.clones || []);
      }
    } catch (err) {
      console.error("Lỗi fetch clones:", err);
    }
  };

  useEffect(() => {
    fetchStatusAndVoices();
    fetchGpuStatus();
    fetchClones();
  }, []);

  useEffect(() => {
    return () => {
      if (playingAudio) {
        playingAudio.pause();
      }
    };
  }, [playingAudio]);

  const handleUploadClone = async (e) => {
    e.preventDefault();
    if (!cloneFile) {
      toast.error('Vui lòng chọn file âm thanh mẫu');
      return;
    }
    if (!cloneName.trim()) {
      toast.error('Vui lòng nhập tên giọng đọc');
      return;
    }

    setUploading(true);
    const loadToast = toast.loading('Đang tải lên và cấu hình giọng clone...');
    
    const formData = new FormData();
    formData.append('file', cloneFile);
    formData.append('name', cloneName.trim());

    try {
      const res = await fetch('http://localhost:8000/api/settings/vieneu/clone', {
        method: 'POST',
        body: formData
      });
      const data = await res.json();
      toast.dismiss(loadToast);

      if (data.status === 'success') {
        toast.success(data.message);
        setCloneName('');
        setCloneFile(null);
        
        const fileInput = document.getElementById('clone-file-input');
        if (fileInput) fileInput.value = '';
        
        fetchClones();
        fetchStatusAndVoices();
      } else {
        toast.error(data.message || 'Lỗi khi tải lên giọng clone');
      }
    } catch (err) {
      toast.dismiss(loadToast);
      console.error(err);
      toast.error('Lỗi kết nối tới máy chủ');
    } finally {
      setUploading(false);
    }
  };

  const handleDeleteClone = async (filename) => {
    if (!window.confirm(`Bạn có chắc chắn muốn xóa giọng clone này không?`)) {
      return;
    }

    try {
      const res = await fetch(`http://localhost:8000/api/settings/vieneu/clones/${filename}`, {
        method: 'DELETE'
      });
      const data = await res.json();
      if (data.status === 'success') {
        toast.success(data.message);
        fetchClones();
        fetchStatusAndVoices();
      } else {
        toast.error(data.message || 'Lỗi khi xóa giọng clone');
      }
    } catch (err) {
      console.error(err);
      toast.error('Lỗi kết nối tới máy chủ');
    }
  };

  const togglePlayClone = (url) => {
    if (playingAudio && playingCloneUrl === url) {
      playingAudio.pause();
      setPlayingAudio(null);
      setPlayingCloneUrl(null);
    } else {
      if (playingAudio) {
        playingAudio.pause();
      }
      const fullUrl = `http://localhost:8000${url}`;
      const audio = new Audio(fullUrl);
      audio.play();
      audio.onended = () => {
        setPlayingAudio(null);
        setPlayingCloneUrl(null);
      };
      setPlayingAudio(audio);
      setPlayingCloneUrl(url);
    }
  };

  const handleGenerate = async (e) => {
    e.preventDefault();
    if (!text.trim()) {
      toast.error('Vui lòng nhập văn bản thử nghiệm');
      return;
    }

    setLoading(true);
    setAudioUrl('');
    const loadToast = toast.loading('Đang sinh giọng đọc (suy luận offline)...');

    try {
      const res = await fetch('http://localhost:8000/api/settings/vieneu/test', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          text: text.trim(),
          voice: selectedVoice,
          emotion: emotion
        })
      });

      const data = await res.json();
      toast.dismiss(loadToast);

      if (data.status === 'success') {
        const fullUrl = `http://localhost:8000${data.audio_url}`;
        setAudioUrl(fullUrl);
        setAudioKey(prev => prev + 1); // trigger audio reload
        toast.success('Sinh âm thanh thành công!');
      } else {
        toast.error(data.message || 'Có lỗi xảy ra khi sinh giọng nói');
      }
    } catch (err) {
      toast.dismiss(loadToast);
      console.error(err);
      toast.error('Lỗi kết nối tới máy chủ backend');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6 max-w-4xl">
      {/* Header Panel */}
      <div className="glass-panel p-6 rounded-2xl relative overflow-hidden">
        <div className="absolute top-0 right-0 w-32 h-32 bg-neon-purple/10 blur-3xl rounded-full pointer-events-none" />
        <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
          <div className="flex items-center gap-4">
            <div className="p-3 bg-neon-purple/10 border border-neon-purple/30 rounded-xl text-neon-purple shadow-[0_0_15px_rgba(168,85,247,0.2)]">
              <Volume2 size={32} />
            </div>
            <div>
              <h3 className="text-xl font-bold tracking-tight bg-gradient-to-r from-white to-text-secondary bg-clip-text text-transparent font-display">
                Cấu Hình & Thử Nghiệm VieNeu-TTS
              </h3>
              <p className="text-sm text-text-secondary mt-1">
                VieNeu-TTS là mô hình chuyển đổi văn bản thành giọng nói (TTS) tiếng Việt offline, chạy trực tiếp trên GPU/CPU của bạn.
              </p>
            </div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Status & Hardware Column */}
        <div className="space-y-6 md:col-span-1">
          {/* Active Model Status */}
          <div className="glass-panel p-5 rounded-2xl border border-border-subtle flex flex-col gap-4">
            <span className="text-xs font-bold text-text-secondary uppercase tracking-wider">Trạng thái mô hình</span>
            
            {status.error ? (
              <div className="flex items-start gap-3 p-3 bg-red-500/10 border border-red-500/20 rounded-xl">
                <AlertTriangle size={18} className="text-red-500 shrink-0 mt-0.5" />
                <div>
                  <p className="text-xs font-semibold text-red-500">Chưa sẵn sàng</p>
                  <p className="text-[10px] text-text-secondary mt-1 leading-normal">
                    {status.error}
                  </p>
                </div>
              </div>
            ) : status.loaded ? (
              <div className="flex items-start gap-3 p-3 bg-green-500/10 border border-green-500/20 rounded-xl">
                <CheckCircle2 size={18} className="text-green-500 shrink-0 mt-0.5" />
                <div>
                  <p className="text-xs font-semibold text-green-500">Đang hoạt động</p>
                  <p className="text-[10px] text-text-secondary mt-1 leading-normal">
                    Mô hình đã được nạp thành công trên container Backend. Bạn có thể sinh giọng nói ngay lập tức.
                  </p>
                </div>
              </div>
            ) : (
              <div className="flex items-center gap-3 p-3 bg-bg-tertiary/40 border border-border-subtle rounded-xl">
                <Loader2 size={18} className="text-neon-purple shrink-0 animate-spin" />
                <span className="text-xs text-text-secondary">{status.message}</span>
              </div>
            )}
            
            <button 
              onClick={fetchStatusAndVoices}
              disabled={loading}
              className="w-full bg-bg-secondary hover:bg-bg-tertiary border border-border-subtle text-text-primary px-3 py-2 rounded-xl text-xs font-bold transition-all duration-200 cursor-pointer disabled:opacity-50"
            >
              Kiểm tra lại kết nối
            </button>
          </div>

          {/* GPU Hardware Status */}
          <div className="glass-panel p-5 rounded-2xl border border-border-subtle flex flex-col gap-3">
            <span className="text-xs font-bold text-text-secondary uppercase tracking-wider">Tăng tốc phần cứng GPU</span>
            
            {gpuStatus ? (
              <div className="space-y-3">
                <div className="flex items-center gap-2">
                  <span className={`w-2 h-2 rounded-full ${gpuStatus.can_use_gpu_acceleration ? 'bg-green-500 animate-pulse' : 'bg-gray-500'}`} />
                  <span className="text-xs font-bold text-text-primary">{gpuStatus.gpu_name}</span>
                </div>
                {gpuStatus.gpu_available && (
                  <div className="p-2.5 bg-bg-secondary/50 rounded-lg border border-border-subtle/50 text-[10px] text-text-secondary leading-relaxed space-y-1">
                    <p>• Phiên bản CUDA: <span className="text-neon-purple font-mono font-bold">{gpuStatus.cuda_version}</span></p>
                    <p>• Tăng tốc qua CUDA: <span className="text-green-500 font-semibold">Khả dụng</span></p>
                    <p>• Trạng thái: <span className="text-text-primary font-medium">{gpuStatus.can_use_gpu_acceleration ? "Đang sử dụng GPU rời để xử lý" : "Đang chạy chế độ CPU"}</span></p>
                  </div>
                )}
              </div>
            ) : (
              <p className="text-xs text-text-secondary italic">Đang lấy thông tin phần cứng...</p>
            )}
          </div>
        </div>

        {/* Configuration & Inference Form */}
        <div className="md:col-span-2 space-y-6">
          <div className="glass-panel p-6 rounded-2xl border border-border-subtle">
            <h4 className="text-md font-bold mb-4 bg-gradient-to-r from-white to-text-secondary bg-clip-text text-transparent">
              Cấu hình suy luận (Inference Configuration)
            </h4>

            <form onSubmit={handleGenerate} className="space-y-4">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                {/* Voice Selection */}
                <div>
                  <label className="block text-xs font-semibold text-text-secondary mb-1.5 uppercase tracking-wide">Giọng đọc (Voice preset)</label>
                  <select
                    className="w-full bg-bg-secondary border border-border-subtle rounded-xl py-2.5 px-3 text-xs text-text-primary focus:outline-none focus:ring-2 focus:ring-neon-purple/50 transition-all duration-200 cursor-pointer"
                    value={selectedVoice}
                    onChange={(e) => setSelectedVoice(e.target.value)}
                    disabled={loading || voices.length === 0}
                  >
                    {voices.length === 0 ? (
                      <option value="Trúc Ly">VieNeu Giọng Nữ Trúc Ly (Mặc định)</option>
                    ) : (
                      voices.map(voice => (
                        <option key={voice.id} value={voice.id}>{voice.name}</option>
                      ))
                    )}
                  </select>
                </div>

                {/* Emotion Selection */}
                <div>
                  <label className="block text-xs font-semibold text-text-secondary mb-1.5 uppercase tracking-wide">Cảm xúc (Emotion)</label>
                  <select
                    className="w-full bg-bg-secondary border border-border-subtle rounded-xl py-2.5 px-3 text-xs text-text-primary focus:outline-none focus:ring-2 focus:ring-neon-purple/50 transition-all duration-200 cursor-pointer"
                    value={emotion}
                    onChange={(e) => setEmotion(e.target.value)}
                    disabled={loading}
                  >
                    <option value="natural">Tự nhiên (Natural)</option>
                    <option value="happy">Vui vẻ (Happy)</option>
                    <option value="sad">Buồn bã (Sad)</option>
                    <option value="angry">Tức giận (Angry)</option>
                  </select>
                </div>
              </div>

              {/* Text Input */}
              <div>
                <label className="block text-xs font-semibold text-text-secondary mb-1.5 uppercase tracking-wide">Văn bản cần đọc (TTS Text)</label>
                <textarea
                  rows="4"
                  className="w-full bg-bg-secondary border border-border-subtle rounded-xl p-3 text-xs text-text-primary focus:outline-none focus:ring-2 focus:ring-neon-purple/50 transition-all duration-200 resize-none leading-relaxed"
                  placeholder="Nhập nội dung văn bản tiếng Việt tại đây..."
                  value={text}
                  onChange={(e) => setText(e.target.value)}
                  disabled={loading}
                />
              </div>

              {/* Submit Button */}
              <button
                type="submit"
                disabled={loading || !status.loaded}
                className="w-full bg-gradient-to-r from-neon-purple to-neon-pink hover:opacity-90 border border-neon-purple/30 text-white py-3 rounded-xl text-xs font-bold transition-all duration-200 cursor-pointer shadow-[0_0_15px_rgba(168,85,247,0.2)] disabled:opacity-50 flex items-center justify-center gap-2"
              >
                {loading ? (
                  <>
                    <Loader2 size={16} className="animate-spin" />
                    Đang sinh giọng nói (suy luận offline)...
                  </>
                ) : (
                  <>
                    <MessageSquare size={16} />
                    Sinh giọng nói thử nghiệm
                  </>
                )}
              </button>
            </form>
          </div>

          {/* Audio Playback Card */}
          {audioUrl && (
            <div className="glass-panel p-5 rounded-2xl border border-neon-purple/20 bg-neon-purple/5 animate-fade-in flex flex-col gap-3">
              <div className="flex items-center gap-2 text-neon-purple">
                <Volume2 size={18} className="animate-bounce" />
                <span className="text-xs font-bold uppercase tracking-wider">Kết quả sinh âm thanh</span>
              </div>
              <p className="text-[10px] text-text-secondary leading-normal">
                Âm thanh được suy luận và biên dịch offline trực tiếp trên máy chủ cục bộ. Dưới đây là âm thanh chạy thử:
              </p>
              <div className="mt-1">
                <audio 
                  key={`${audioUrl}-${audioKey}`} 
                  controls 
                  autoPlay
                  className="w-full h-10 accent-neon-purple text-neon-purple rounded-lg filter drop-shadow-md"
                >
                  <source src={`${audioUrl}?t=${Date.now()}`} type="audio/wav" />
                  Trình duyệt của bạn không hỗ trợ thẻ phát âm thanh.
                </audio>
              </div>
            </div>
          )}

          {/* Clone Voice Panel */}
          <div className="glass-panel p-6 rounded-2xl border border-border-subtle flex flex-col gap-4">
            <div>
              <h4 className="text-md font-bold bg-gradient-to-r from-white to-text-secondary bg-clip-text text-transparent flex items-center gap-2">
                <Cpu size={18} className="text-neon-purple" />
                Quản lý Giọng đọc Clone (Voice Cloning)
              </h4>
              <p className="text-xs text-text-secondary mt-1 leading-relaxed">
                Tải lên file âm thanh mẫu ngắn (3-10 giây) để sao chép giọng nói. VieNeu-TTS sẽ phân tích và sinh giọng nói mới offline hoàn toàn.
              </p>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 pt-2 border-t border-border-subtle/30">
              {/* Upload Form */}
              <form onSubmit={handleUploadClone} className="space-y-4 lg:border-r lg:border-border-subtle/30 lg:pr-6">
                <div>
                  <label className="block text-xs font-semibold text-text-secondary mb-1.5 uppercase tracking-wide">
                    Tên giọng đọc clone
                  </label>
                  <input
                    type="text"
                    className="w-full bg-bg-secondary border border-border-subtle rounded-xl py-2.5 px-3 text-xs text-text-primary focus:outline-none focus:ring-2 focus:ring-neon-purple/50 transition-all duration-200"
                    placeholder="Ví dụ: Giọng cô Lan, Giọng anh Tuấn..."
                    value={cloneName}
                    onChange={(e) => setCloneName(e.target.value)}
                    disabled={uploading}
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold text-text-secondary mb-1.5 uppercase tracking-wide">
                    File âm thanh mẫu (.wav, .mp3, .m4a)
                  </label>
                  <div className="relative border border-dashed border-border-subtle/60 hover:border-neon-purple/50 rounded-xl p-4 flex flex-col items-center justify-center bg-bg-secondary/20 transition-all duration-200">
                    <input
                      id="clone-file-input"
                      type="file"
                      accept=".wav,.mp3,.m4a"
                      className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                      onChange={(e) => setCloneFile(e.target.files[0])}
                      disabled={uploading}
                    />
                    <Upload size={20} className="text-text-secondary mb-2" />
                    <span className="text-xs text-text-primary font-medium text-center truncate max-w-full">
                      {cloneFile ? cloneFile.name : 'Kéo thả hoặc nhấp để chọn file'}
                    </span>
                    <span className="text-[10px] text-text-secondary mt-1 text-center">
                      Khuyên dùng giọng đọc rõ ràng, ít tiếng ồn
                    </span>
                  </div>
                </div>

                <button
                  type="submit"
                  disabled={uploading || !cloneFile || !cloneName.trim()}
                  className="w-full bg-bg-secondary hover:bg-bg-tertiary border border-border-subtle text-text-primary py-2.5 rounded-xl text-xs font-bold transition-all duration-200 disabled:opacity-50 flex items-center justify-center gap-2 cursor-pointer"
                >
                  {uploading ? (
                    <>
                      <Loader2 size={14} className="animate-spin" />
                      Đang tải lên...
                    </>
                  ) : (
                    <>
                      <Plus size={14} />
                      Lưu mẫu clone giọng
                    </>
                  )}
                </button>
              </form>

              {/* Clones List */}
              <div className="space-y-3">
                <label className="block text-xs font-semibold text-text-secondary uppercase tracking-wide">
                  Mẫu giọng đã lưu ({clones.length})
                </label>
                
                {clones.length === 0 ? (
                  <div className="h-44 border border-border-subtle/30 border-dashed rounded-xl flex flex-col items-center justify-center text-xs text-text-secondary italic p-4 text-center">
                    <FileAudio size={24} className="text-text-secondary/50 mb-2" />
                    Chưa có giọng clone nào được tạo.
                  </div>
                ) : (
                  <div className="space-y-2 max-h-[196px] overflow-y-auto pr-1">
                    {clones.map((clone) => (
                      <div 
                        key={clone.id} 
                        className="flex items-center justify-between p-2.5 bg-bg-secondary/30 border border-border-subtle rounded-xl hover:border-neon-purple/20 transition-all duration-200"
                      >
                        <div className="flex items-center gap-2.5 min-w-0">
                          <div className="p-2 bg-neon-purple/10 border border-neon-purple/20 rounded-lg text-neon-purple shrink-0">
                            <FileAudio size={14} />
                          </div>
                          <div className="min-w-0">
                            <p className="text-xs font-bold text-text-primary truncate">{clone.name}</p>
                            <p className="text-[9px] text-text-secondary mt-0.5">
                              {(clone.size / 1024).toFixed(1)} KB • {clone.id.split('.').pop().toUpperCase()}
                            </p>
                          </div>
                        </div>

                        <div className="flex items-center gap-1 shrink-0">
                          <button
                            type="button"
                            onClick={() => togglePlayClone(clone.file_url)}
                            className="p-1.5 hover:bg-bg-secondary rounded-lg text-text-secondary hover:text-neon-purple transition-all duration-200 cursor-pointer"
                            title="Nghe thử file gốc"
                          >
                            {playingCloneUrl === clone.file_url ? <Pause size={12} /> : <Play size={12} />}
                          </button>
                          <button
                            type="button"
                            onClick={() => handleDeleteClone(clone.id)}
                            className="p-1.5 hover:bg-bg-secondary rounded-lg text-text-secondary hover:text-red-500 transition-all duration-200 cursor-pointer"
                            title="Xóa giọng clone"
                          >
                            <Trash2 size={12} />
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default VieneuSettings;
