# Kế hoạch triển khai Phase 2: Xử lý & Chế bản Video

Mục tiêu: Tự động hóa quy trình: Trích xuất âm thanh -> Nhận diện giọng nói (Speech-to-Text) -> Dịch thuật phụ đề (LLM Gemini) -> Lồng tiếng (TTS) -> Render ra video hoàn chỉnh cuối cùng.

## Quyết định kỹ thuật
1. **Công cụ Render:** Dùng FFmpeg (đòi hỏi cài đặt system-wide).
2. **LLM Dịch thuật:** Dùng Google Gemini API (`google-generativeai`).
3. **Lồng tiếng (TTS):** Dùng `edge-tts` (miễn phí, chất lượng cao).
4. **Mô hình STT:** Dùng `faster-whisper` chạy nội bộ.

## Proposed Changes

### 1. Cập nhật Backend Dependencies
- Cài đặt thêm: `faster-whisper`, `edge-tts`, `google-generativeai`, `ffmpeg-python`, `python-dotenv`.

### 2. Thiết kế Module `processor/`
- `audio_extractor.py`: Tách file `.mp3` từ video gốc.
- `transcriber.py`: Dùng Whisper tạo Phụ đề gốc (`.srt`).
- `translator.py`: Gọi Gemini API dịch `.srt` sang tiếng Việt.
- `tts_generator.py`: Lồng tiếng tiếng Việt khớp với thời gian.
- `video_editor.py`: Ghép Audio mới + Burn phụ đề + Đổi mã MD5 bằng FFmpeg.
- `pipeline.py`: Quản lý toàn bộ tiến trình trên tuần tự.

### 3. Tích hợp Backend API và Frontend
- **Backend API**: 
  - `POST /api/processor/start`
  - `GET /api/processor/stream` (SSE Log)
- **Frontend**: `Phase2Processor.jsx` hiển thị tiến trình và danh sách video.
