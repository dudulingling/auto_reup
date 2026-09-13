# TÀI LIỆU CÁC MÔ HÌNH AI TIỀM NĂNG (TƯƠNG LAI)

> **Mục tiêu**: Lưu trữ thông tin về các mô hình AI tiên tiến có thể tích hợp vào hệ thống Auto Reup TikTok trong tương lai (để nâng cấp thành bản PRO/VIP). Hiện tại hệ thống chưa tích hợp các mô hình này để đảm bảo hiệu suất nhẹ nhàng cho Laptop phổ thông.

---

## 1. MÔ HÌNH XỬ LÝ HÌNH ẢNH (Video OCR & Inpainting)

### PaddleOCR (Baidu) & Inpainting (Lama / OpenCV)
- **Mục đích**: Tìm và xóa sạch chữ cứng (hardcoded sub) tiếng Trung/Anh dính trên video gốc, sau đó lấp đầy background (Inpainting) để video trông như mới.
- **Ưu điểm**:
  - Chống gậy bản quyền quét OCR (chữ) của TikTok/Douyin cực kỳ hiệu quả.
  - Video xuất ra siêu sạch, sub Tiếng Việt chèn vào không bị đè nham nhở lên sub cũ.
- **Nhược điểm & Yêu cầu phần cứng**:
  - **Tốc độ**: Cực kỳ chậm. Phải xử lý từng khung hình (frame by frame). Video 1 phút (30fps) = 1800 khung hình.
  - **Phần cứng**: Ngốn CPU và GPU dữ dội. Bắt buộc cần có Card rời (Nvidia RTX) tối thiểu 6GB VRAM để chạy mượt. Nếu chạy trên CPU Laptop thường có thể mất 20-30 phút cho 1 video ngắn.
  - **Lưu trữ**: Dung lượng tool sẽ phình to thêm 2-3GB cho các models và thư viện xử lý ảnh.

---

## 2. MÔ HÌNH XỬ LÝ GIỌNG NÓI (Speech-to-Text)

### SenseVoice (Alibaba)
- **Mục đích**: Thay thế mô hình Whisper hiện tại để bóc băng (STT) siêu tốc độ, đặc biệt mạnh về Tiếng Trung.
- **Ưu điểm**:
  - Tốc độ bóc băng có thể nhanh gấp 5-10 lần so với Whisper (tùy cấu hình).
  - Độ chính xác với Tiếng Trung (kể cả giọng địa phương, tiếng lóng) cực tốt.
  - Có thể nhận diện được cả cảm xúc (khóc, cười, ho) và âm thanh môi trường.
- **Nhược điểm & Yêu cầu phần cứng**:
  - Cần cài đặt hệ sinh thái `FunASR` của Alibaba, yêu cầu setup môi trường (C++ Build Tools) phức tạp hơn trên Windows so với `faster_whisper`.
  - Khả năng đa ngôn ngữ (Tiếng Anh, v.v.) hiện tại chưa được chứng minh vượt trội bằng Whisper.

---

## 3. MÔ HÌNH TÁCH ÂM THANH (Vocal Remover)

### UVR5 (Ultimate Vocal Remover) - BS RoFormer / MDX-Net
- **Mục đích**: Thay thế mô hình Demucs v4 hiện tại để tách giọng nói (Voice) ra khỏi nhạc nền (BGM).
- **Ưu điểm**:
  - Chất lượng bóc tách ở đẳng cấp Studio. Xóa sạch mọi tiếng bass, EDM ồn ào của TikTok mà vẫn giữ được chất giọng gốc trong vắt. Giúp tăng tỷ lệ nhận diện chữ lên 99%.
- **Nhược điểm & Yêu cầu phần cứng**:
  - **VRAM Killer**: Mô hình BS RoFormer (Transformer) cực kỳ nặng. Đòi hỏi ít nhất 8GB VRAM (như RTX 3060/4060).
  - **Rủi ro OOM (Out of Memory)**: Nếu chạy trên Laptop 8GB-16GB RAM không có card rời, hệ thống sẽ rất dễ bị văng (Crash) do tràn bộ nhớ, hoặc chạy rất chậm.

---

## 4. MÔ HÌNH NHÁI GIỌNG (Voice Cloning / AI Dubbing)

### OpenVoice (MyShell) / XTTS v2 (Coqui) / ElevenLabs
- **Mục đích**: Không dùng giọng TTS máy móc (Google/Edge), mà dùng trực tiếp giọng nói thật của nhân vật trong video để đọc phụ đề Tiếng Việt.
- **Ưu điểm**:
  - Cực kỳ chân thực. Chỉ cần sample 3-5 giây âm thanh gốc là AI có thể "nhái" lại toàn bộ tone giọng, cảm xúc, nhịp thở để đọc Tiếng Việt.
- **Nhược điểm & Yêu cầu phần cứng**:
  - OpenVoice / XTTS v2 yêu cầu phần cứng cực mạnh để render nhanh (Card Nvidia 8GB+).
  - Nếu dùng API thương mại (như ElevenLabs) thì rất đắt đỏ.

## 5. MÔ HÌNH TẠO VIDEO 3D SIMULATION (Sora / Luma / Kling AI)

### Gen-AI 3D Video (Luma Dream Machine, Kling AI, Runway Gen-3) & Workflow 3DREAL
- **Mục đích**: Tự động hóa việc tạo ra các video 3D Simulation (vật lý, motion graphics, hạt, mìn, bóng lăn...) đang rất thịnh hành trên Reels/TikTok (như ví dụ link Instagram).
- **Ưu điểm**:
  - Biến các prompt văn bản hoặc hình ảnh tham chiếu đơn giản thành video 3D có tính chất vật lý (mềm, dẻo, va đập) siêu thực tế.
  - Áp dụng Workflow "Render-to-Real": Dựng một cảnh 3D nháp cực thô (Blockout) bằng Blender, sau đó cho AI (như LTX-2.3 hoặc ComfyUI AnimateDiff) render đè lên để thành video 3D mãn nhãn. Rút ngắn 90% thời gian render 3D truyền thống.
- **Nhược điểm & Yêu cầu phần cứng**:
  - Các mô hình tạo Video AI (Sora, Luma, Kling) chủ yếu chạy qua API Cloud thương mại (rất tốn kém, tính phí theo giây) do mô hình quá khổng lồ để chạy Local.
  - Nếu muốn tự chạy Local (như ComfyUI + AnimateDiff + ControlNet), cần máy trạm cực mạnh (VRAM tối thiểu 16GB-24GB như RTX 4090) và cấu hình Workflow phức tạp.
  - Khó kiểm soát tính đồng nhất (Consistency) 100% về vật lý so với phần mềm 3D gốc như Houdini hay Blender.

---

**Định hướng tích hợp**: 
Chỉ nên tích hợp các module này vào nhánh phát triển riêng (bản **PRO/Studio**) dành cho những khách hàng sở hữu cấu hình PC Render Farm (RTX 3060, 32GB RAM trở lên). Không nên nhúng vào bản tiêu chuẩn (chạy trên Laptop phổ thông) để tránh tình trạng treo máy. Mảng 3D Video Generation có thể tích hợp dưới dạng gọi API của Luma/Kling để tiết kiệm phần cứng.
