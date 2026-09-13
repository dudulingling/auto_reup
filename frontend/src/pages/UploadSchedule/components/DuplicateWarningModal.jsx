import React from 'react';
import { AlertTriangle, X, ArrowRight } from 'lucide-react';

export function DuplicateWarningModal({ isOpen, onClose, onConfirm, duplicates = [] }) {
  if (!isOpen || duplicates.length === 0) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-fade-in">
      <div className="relative w-full max-w-lg overflow-hidden border rounded-2xl bg-bg-secondary border-border-primary shadow-2xl animate-scale-up">
        {/* Header */}
        <div className="flex items-center justify-between p-5 border-b border-border-primary/60 bg-amber-500/10">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-xl bg-amber-500/20 text-amber-400">
              <AlertTriangle className="w-6 h-6" />
            </div>
            <div>
              <h3 className="text-lg font-bold text-text-primary">
                Cảnh báo trùng lặp video
              </h3>
              <p className="text-xs text-text-secondary">
                Phát hiện {duplicates.length} lượt đăng đã từng thực hiện trước đó
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 text-text-tertiary transition-colors rounded-lg hover:text-text-primary hover:bg-bg-tertiary"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Body Content */}
        <div className="p-5 space-y-4">
          <p className="text-sm leading-relaxed text-text-secondary">
            Các video sau đây đã từng được lên lịch hoặc đăng thành công trên tài khoản tương ứng. Đăng lại video trùng lặp có thể giảm tương tác hoặc bị nền tảng đánh dấu spam:
          </p>

          {/* List of duplicates */}
          <div className="max-h-56 overflow-y-auto space-y-2 pr-1 custom-scrollbar">
            {duplicates.map((item, idx) => (
              <div
                key={idx}
                className="flex items-center justify-between p-3 text-xs border rounded-xl bg-bg-primary/60 border-border-primary/60"
              >
                <div className="flex-1 min-w-0 pr-2">
                  <span className="font-semibold text-text-primary block truncate">
                    🎬 {item.videoName}
                  </span>
                </div>
                <div className="flex items-center gap-1.5 flex-shrink-0 text-amber-400 bg-amber-500/10 px-2.5 py-1 rounded-lg">
                  <span className="font-medium truncate max-w-[120px]">
                    👤 {item.accountName}
                  </span>
                </div>
              </div>
            ))}
          </div>

          <div className="p-3 text-xs rounded-xl bg-bg-primary/40 border border-border-primary/40 text-text-secondary">
            💡 <strong className="text-text-primary">Gợi ý:</strong> Nếu bạn đã chỉnh sửa lại video hoặc muốn đăng lại có chủ đích, hãy bấm <span className="text-accent-primary font-semibold">"Tiếp tục đăng"</span> để bỏ qua cảnh báo này.
          </div>
        </div>

        {/* Footer Actions */}
        <div className="flex items-center justify-end gap-3 p-5 border-t border-border-primary/60 bg-bg-primary/40">
          <button
            type="button"
            onClick={onClose}
            className="px-4 py-2 text-sm font-medium transition-all rounded-xl text-text-secondary hover:text-text-primary hover:bg-bg-tertiary"
          >
            Hủy bỏ
          </button>
          <button
            type="button"
            onClick={onConfirm}
            className="flex items-center gap-2 px-5 py-2 text-sm font-semibold text-white transition-all shadow-lg rounded-xl bg-gradient-to-r from-amber-500 to-orange-500 hover:from-amber-600 hover:to-orange-600 shadow-amber-500/20 active:scale-95"
          >
            <span>Tiếp tục đăng</span>
            <ArrowRight className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
}
