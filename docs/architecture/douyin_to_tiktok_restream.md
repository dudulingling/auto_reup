# Kế hoạch & Giải pháp Restream Từ Douyin sang TikTok Live

Tài liệu này trình bày tư duy kiến trúc và quy trình logic để thực hiện việc lấy luồng phát trực tiếp (livestream) từ Douyin và phát lại (restream) lên nền tảng TikTok một cách tự động, kèm theo cơ chế lách bản quyền luồng trực tiếp.

---

## 1. Nguyên lý Hoạt động (Luồng Dữ liệu)

Quá trình Restream diễn ra theo luồng Real-time (Thời gian thực) và chia làm 3 giai đoạn chính:

### Giai đoạn 1: Bắt luồng (Stream Capture)
- Nhập **Room ID** (hoặc URL phòng live) của Douyin vào hệ thống.
- Hệ thống gửi request mô phỏng Web/App Client để trích xuất được đường dẫn luồng video trực tiếp (thường có định dạng `.flv` hoặc `.m3u8`).
- Đường dẫn này sẽ là nguồn đầu vào (Input) liên tục cho máy chủ của chúng ta.

### Giai đoạn 2: Trộn và Lách bản quyền theo Thời gian thực (Real-time Processing)
- Đưa đường dẫn luồng (Input) vào **FFmpeg**.
- Áp dụng các bộ lọc (Filters) trực tiếp trên luồng đang chạy để lách AI nhận diện luồng lậu của TikTok:
  - Lật ngang video (Horizontal Flip).
  - Phóng to nhẹ (Zoom 102%).
  - Đổi màu sắc, chỉnh lại độ sáng/tương phản.
  - Phủ thêm 1 lớp nhiễu mờ (Noise overlay) cực mỏng.
  - Biến đổi cao độ âm thanh gốc (Pitch Shift) hoặc trộn thêm nhạc nền không bản quyền.
  - (Nâng cao) Phủ thêm một khung viền (Frame) mang thương hiệu riêng.

### Giai đoạn 2.5: Dịch thuật và lồng tiếng Real-time (Voice AI)
- Đây là giải pháp nâng cao lấy cảm hứng từ các công cụ như `Douyin & Bilibili Subtitle Translator`.
- **Speech-to-Text (Nhận diện giọng nói):** Luồng âm thanh gốc (Tiếng Trung) sẽ được trích xuất song song và gửi qua các API nhận diện siêu tốc như **Soniox API** hoặc **Whisper Streaming** để lấy text với độ trễ chỉ 1-2 giây.
- **Translation (Dịch thuật):** Gọi Google Cloud Translation hoặc OpenAI GPT-4o-mini API để dịch văn bản sang tiếng Việt.
- **Text-to-Speech (Tùy chọn):** Nếu muốn lồng tiếng, gửi text đã dịch qua API TTS (ElevenLabs, Edge-TTS) để tạo luồng âm thanh mới.
- **Overlay:** Dùng FFmpeg filter `drawtext` (đọc text từ file text được cập nhật liên tục) để hiển thị phụ đề dịch đuổi ngay trên màn hình Live, hoặc trộn luồng âm thanh tiếng Việt đè lên luồng gốc.

### Giai đoạn 3: Phát luồng (Stream Push)
- Hệ thống cần có **RTMP Server URL** và **Stream Key** của phiên Live trên tài khoản TikTok của bạn.
- FFmpeg sẽ mã hóa lại luồng đã xử lý và đẩy (Push) liên tục qua giao thức `rtmp://...` lên máy chủ của TikTok.

---

## 2. Các Công cụ Tối ưu Cần sử dụng

### 2.1. FFmpeg (Công cụ Cốt lõi)
- **Công dụng**: Vừa làm nhiệm vụ Pull luồng (từ Douyin), vừa Filter (lách bản quyền), vừa Push (lên TikTok). Tất cả chỉ bằng 1 dòng lệnh siêu dài.
- **Ưu điểm**: Nhẹ, cực kỳ mạnh mẽ, chạy ngầm ổn định 24/7 trên Server (VPS Linux/Windows) mà không cần bật màn hình giao diện.
- **Nhược điểm**: Phải cấu hình phần cứng tốt (Có GPU xử lý video stream như NVENC) để giảm độ trễ, nếu dùng CPU để transcode luồng trực tiếp sẽ gây giật lag.

### 2.2. Trình Trích xuất Douyin (Custom Python Script)
- **Công dụng**: Các API công khai thường xuyên bị Douyin khóa chặn. Cần một module Python chuyên biệt chuyên tạo signature, giải mã JSON trả về từ API Douyin để móc ra cái link luồng `.flv` ẩn bên dưới.

### 2.3. Lấy Stream Key TikTok (Third-party Tool / Kịch bản tự động)
- **Công dụng**: TikTok thường giấu Stream Key và yêu cầu dùng TikTok Live Studio. Cần có công cụ (hoặc bot tự động) để lấy chuỗi Stream Key này thì FFmpeg mới có đích đến để đẩy video lên.

---

## 3. Thách thức lớn & Cảnh báo Rủi ro (Critical Risks)

1. **Thuật toán quét Restream của TikTok**: 
   TikTok quét rất gắt. Dù bạn có lách hình ảnh, AI của họ có thể nhận diện qua "Môi trường tĩnh" (Ví dụ màn hình Douyin có cái khung chat, icon quà tặng... mang đặc trưng của Douyin). 
   👉 **Giải pháp**: Cần dùng crop video để cắt bỏ các rìa ngoài chứa logo/UI của Douyin, chỉ lấy nhân vật chính.

2. **Chính sách cấp Stream Key của TikTok**:
   Bạn phải đạt được điều kiện cho phép Live qua ứng dụng bên thứ 3 (PC/Console) mới có thể lấy được Stream Key. Thường tài khoản phải có độ trust (uy tín) và lượng Follower nhất định (1k - 10k tuỳ khu vực).

3. **Độ trễ (Latency) & Chênh lệch Băng thông**:
   Khi Restream, Server trung gian (VPS của Sếp) phải chịu tải mạng gấp đôi: Vừa TẢI XUỐNG luồng từ TQ, vừa TẢI LÊN luồng cho TikTok quốc tế. Cần Server có băng thông quốc tế mạnh để không bị hiện tượng "Buffering" trên luồng Live.

4. **Biên dịch Real-time & Băng thông (Khó khăn lớn nhất)**:
   Để xử lý luồng Voice AI Real-time (như Giai đoạn 2.5), Server phải liên tục xử lý đa luồng (Video encode + Audio extract + API Call + Overlay). Điều này đòi hỏi CPU/GPU cực mạnh và băng thông quốc tế ổn định. Độ trễ của Live có thể bị cộng dồn lên 10-15 giây so với nguồn gốc.
   👉 **Giải pháp**: Tối ưu FFmpeg buffer và chấp nhận độ trễ (Delay) 15 giây để Subtitle kịp render.

---

## 4. Tóm tắt Kiến trúc (Architecture Concept)

```text
[ Douyin Live Room ] 
        |
    (Trích xuất .flv qua Python)
        |
        V
[ FFmpeg Server (Có GPU) ] 
  --> Chạy Filter (Crop, Hflip, Màu, Noise)
  --> Encode H264/AAC
        |
    (Đẩy giao thức RTMP)
        |
        V
[ Máy chủ TikTok Live ] --> Người xem
```
