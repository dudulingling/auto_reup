# 📖 HƯỚNG DẪN TRIỂN KHAI HỆ THỐNG TRÊN GOOGLE COLAB (GPU T4 MIỄN PHÍ)
*(Mô Hình Lai - Hybrid Architecture — Độc Lập, Không Đụng Chạm Code Gốc)*

---

## 🌟 1. VÌ SAO CHỌN MÔ HÌNH LAI (HYBRID ARCHITECTURE)?

Hệ thống **Auto Re-up TikTok / Douyin** có những tác vụ cực kỳ ngốn tài nguyên đồ họa (AI) và những tác vụ yêu cầu môi trường nội bộ ổn định:

| Tác Vụ | Chạy Ở Đâu Tốt Nhất? | Lý Do |
| :--- | :--- | :--- |
| **Bóc tách phụ đề AI (`faster-whisper`)** | ☁️ **Google Colab T4** | T4 16GB VRAM chạy FP16 chỉ mất 5–10 giây cho một video. |
| **Lồng tiếng AI tiếng Việt (`vieneu`)** | ☁️ **Google Colab T4** | Mô hình neural cần GPU mạnh để tổng hợp giọng nói tự nhiên, không bị giật lag. |
| **Tách giọng nói & BGM (`audio-separator`)** | ☁️ **Google Colab T4** | Mô hình UVR5 / Demucs ngốn GPU, chạy trên Colab cực mượt. |
| **Render video lách bản quyền (`NVENC`)** | ☁️ **Google Colab T4** | Tốc độ render phần cứng 60fps+, giảm 90% tải cho CPU máy tính cá nhân. |
| **Giao diện quản trị Web (React/Vite)** | 💻 **Máy Local (Cá nhân)** | Xem preview tức thì, phản hồi nhanh, không phụ thuộc đường truyền mạng. |
| **Lưu Database (`history.db`) & Cấu hình** | 💻 **Máy Local (Cá nhân)** | An toàn 100%, không sợ bị mất lịch sử khi Colab tắt phiên. |
| **Đăng bài & Nuôi nick (ADB / Giả lập / GPM)** | 💻 **Máy Local (Cá nhân)** | Colab không chạy được giả lập Android. Đăng bằng IP mạng nhà tránh checkpoint TikTok. |

---

## 📁 2. CẤU TRÚC THƯ MỤC `colab_hybrid/`

Thư mục này hoạt động hoàn toàn độc lập, tách biệt với mã nguồn chính:

```text
colab_hybrid/
├── auto_reup_colab.ipynb       # File Notebook tải lên Google Colab để chạy 1-Click
├── server/
│   ├── colab_server.py         # FastAPI GPU Server độc lập trên Colab T4
│   ├── gpu_services.py         # Bộ tích hợp GPU: Faster-Whisper, Vieneu, Audio-Separator, NVENC
│   ├── requirements_colab.txt  # Thư viện tối ưu cho Colab Linux + CUDA 12.x
│   └── start_colab.sh          # Script khởi động tự động + Cloudflare Tunnel
├── client/
│   ├── colab_client.py         # Python SDK để máy tính Local gọi sang Colab GPU Server
│   └── test_connection.py      # Script kiểm tra kết nối & benchmark thông số GPU T4
├── config/
│   └── colab_env.example       # Mẫu file cấu hình môi trường
└── README.md                   # Tài liệu hướng dẫn này
```

---

## 🚀 3. HƯỚNG DẪN BẮT ĐẦU NHANH (STEP-BY-STEP)

### BƯỚC 1: Mở Notebook Trên Google Colab
1. Truy cập [Google Colab](https://colab.research.google.com/).
2. Chọn tab **Upload (Tải lên)** và chọn file `colab_hybrid/auto_reup_colab.ipynb` từ máy tính của bạn.
3. Trên thanh menu của Colab, vào:
   👉 **Runtime** -> **Change runtime type** -> Chọn **T4 GPU** -> Bấm **Save**.

### BƯỚC 2: Tải Bộ Code Server Lên Colab
Có 2 cách đơn giản:
- **Cách 1 (Nhanh nhất):** Copy toàn bộ thư mục `colab_hybrid/server/` vào thư mục `auto_reup_storage` trên Google Drive của bạn.
- **Cách 2:** Kéo thả trực tiếp 2 file `colab_server.py` và `gpu_services.py` vào tab **Files (Thư mục)** ở cột trái của giao diện Colab.

### BƯỚC 3: Chạy Lần Lượt Các Cell Trong Notebook
- **Cell 1:** Xác nhận GPU NVIDIA Tesla T4 đã kích hoạt.
- **Cell 2:** Mount Google Drive để lưu trữ dữ liệu vĩnh viễn (video, weights).
- **Cell 3:** Cài đặt các gói hệ thống và thư viện AI (khoảng 1–2 phút).
- **Cell 4:** Khởi chạy GPU Server và đường hầm **Cloudflare Tunnel**.

Khi Cell 4 chạy xong, một đường dẫn HTTPS công khai sẽ xuất hiện trên màn hình, ví dụ:
```text
============================================================
🎉 CHÚC MỪNG! GPU WORKER CỦA BẠN ĐÃ ONLINE!

👉 ĐỊA CHỈ GPU CLOUD CỦA BẠN:
   https://xyz-random-domain.trycloudflare.com

👉 KIỂM TRA TRẠNG THÁI (Swagger API Docs):
   https://xyz-random-domain.trycloudflare.com/docs
============================================================
```

---

## 💻 4. KẾT NỐI & KIỂM TRA TỪ MÁY LOCAL (WINDOWS)

Mở terminal (CMD / PowerShell) trên máy tính cá nhân và chạy lệnh:

```bash
python colab_hybrid/client/test_connection.py https://xyz-random-domain.trycloudflare.com
```

Kết quả sẽ trả về tức thì:
```text
============================================================
🎉 KẾT NỐI THÀNH CÔNG!
============================================================
⏱️ Độ trễ mạng (Ping):      150 ms
🖥️ Tên Card Đồ Họa:         Tesla T4
🚀 CUDA Available:          True
📦 Tổng VRAM GPU:           15109 MB (~16 GB)
📊 VRAM Trống:              14850 MB
🎬 Hỗ trợ Render NVENC:     CÓ (Siêu Tốc)
============================================================
```

---

## 🛠️ 5. SỬ DỤNG PYTHON CLIENT ĐỂ XỬ LÝ VIDEO NẶNG

Bạn có thể viết script hoặc gọi trực tiếp từ code Python ở máy Local:

```python
from colab_hybrid.client.colab_client import ColabGPUClient

# 1. Khởi tạo kết nối với Colab
client = ColabGPUClient(base_url="https://xyz-random-domain.trycloudflare.com")

# 2. Bóc tách phụ đề video bằng Faster-Whisper trên T4 GPU (Chỉ mất vài giây!)
result = client.transcribe(media_path="video_goc.mp4", model_size="base")
print("Phụ đề nhận diện được:", result["full_text"])

# 3. Lồng tiếng thuyết minh AI bằng Vieneu
client.generate_tts(
    text="Chào mừng bạn đến với kênh của tôi!",
    output_wav_path="./tts_output.wav",
    voice="female"
)

# 4. Tách nhạc nền và giọng nói
tracks = client.separate_audio(audio_path="./tts_output.wav", output_dir="./separated")
print("File Vocal:", tracks["vocal_path"])
print("File BGM:", tracks["instrumental_path"])

# 5. Render video lách bản quyền bằng NVENC phần cứng
client.render_video_nvenc(
    video_path="video_goc.mp4",
    output_video_path="video_thanh_pham.mp4",
    audio_path="./tts_output.wav",
    speed=1.05,
    flip_horizontal=True,
    zoom_factor=1.03,
    watermark_text="@KenhCuaToi"
)
print("✅ Video đã render xong và tải về máy tính!")
```

---

## 💡 6. MẸO SỬ DỤNG & KHẮC PHỤC SỰ CỐ (TIPS & FAQ)

1. **Làm sao để Colab không tự tắt khi rảnh rỗi?**
   - Mở giao diện Colab trên Chrome, bấm phím **F12** để mở Developer Console.
   - Dán đoạn mã sau vào và nhấn Enter:
     ```javascript
     function ClickConnect(){
         console.log("Giữ kết nối: " + new Date().toLocaleTimeString());
         document.querySelector("colab-connect-button")?.shadowRoot?.querySelector("#connect")?.click();
     }
     setInterval(ClickConnect, 60000);
     ```
2. **Quota GPU miễn phí của Google Colab là bao nhiêu?**
   - Google cấp khoảng 12 giờ sử dụng GPU T4 liên tục mỗi ngày cho tài khoản miễn phí.
   - Khi không xử lý video, bạn có thể bấm **Runtime -> Disconnect and delete runtime** để tiết kiệm hạn ngạch GPU cho lần sau.
3. **Dữ liệu có bị mất khi tắt Colab không?**
   - Không! Toàn bộ file xuất ra (`outputs/`) được lưu vĩnh viễn trên **Google Drive** tại thư mục `/MyDrive/auto_reup_storage/`.
