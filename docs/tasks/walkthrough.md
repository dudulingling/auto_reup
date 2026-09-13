# Hướng dẫn Kiểm tra và Xác minh Tích hợp VieNeu-TTS (Docker Version)

Hệ thống đã được cập nhật thành công cả Backend và Frontend để hỗ trợ **VieNeu-TTS (Offline)**. Vì dự án của bạn đang chạy trong môi trường **Docker Container**, chúng ta không cần cài đặt phần mềm nào lên hệ thống Windows của bạn mà sẽ đóng gói và chạy trực tiếp mọi thứ bên trong Docker.

---

## 🛠️ Các Thay đổi Đã Thực hiện

1. **Docker & Cấu hình Hệ thống**:
   - Cập nhật [Dockerfile](file:///d:/Code/auto_reup/backend/Dockerfile) để cài đặt sẵn **eSpeak NG** (cần thiết cho phonemizer của VieNeu-TTS).
   - Tích hợp cài đặt **llama-cpp-python** có hỗ trợ GPU CUDA 12.4 trực tiếp từ các bản pre-built wheels chính thức. Điều này giúp container nhận diện và tăng tốc trực tiếp qua card rời NVIDIA GTX 1650 của bạn.
2. **Cấu hình Dependency**:
   - Cập nhật [requirements.txt](file:///d:/Code/auto_reup/backend/requirements.txt) để thêm thư viện `vieneu`.
3. **Backend**:
   - Sửa đổi [tts_generator.py](file:///d:/Code/auto_reup/backend/app/services/processor/tts_generator.py) để tích hợp VieNeu-TTS bằng cơ chế **Lazy Loading** (chỉ tải model khi sử dụng) và xuất trực tiếp âm thanh `.wav` chất lượng cao. Chừa sẵn chỗ cho tính năng **Clone giọng nói** trong tương lai.
   - Sửa đổi [settings.py](file:///d:/Code/auto_reup/backend/app/api/settings.py) để trả về danh sách giọng ảo VieNeu khi chọn Active TTS Provider là `vieneu`.
4. **Frontend**:
   - Sửa đổi [index.jsx](file:///d:/Code/auto_reup/frontend/src/pages/Settings/index.jsx) để thêm option lồng tiếng `VieNeu-TTS` và ẩn ô nhập API Key tương ứng.

---

## ⚡ Hướng dẫn Chạy thử & Xác minh trên Docker

Bạn chỉ cần thực hiện các lệnh sau trực tiếp từ thư mục dự án trên máy Windows của bạn (trong Terminal hoặc PowerShell):

### Bước 1: Build lại các container Backend và Celery Worker
Chạy lệnh sau để Docker build lại image mới có cài đặt `espeak-ng` và `vieneu`:
```powershell
docker-compose build backend celery_worker
```

### Bước 2: Khởi động lại hệ thống
```powershell
docker-compose down
docker-compose up -d
```

### Bước 3: Chạy script kiểm tra bên trong Container
Chạy script kiểm tra tự động mà tôi đã tạo sẵn tại [test_vieneu_setup.py](file:///d:/Code/auto_reup/scratch/test_vieneu_setup.py) trực tiếp bên trong container backend để xem nó đã nhận dạng GPU và sinh âm thanh thử nghiệm thành công chưa:
```powershell
docker-compose exec backend python scratch/test_vieneu_setup.py
```

*Lưu ý: Ở lần chạy thử đầu tiên, script sẽ tải mô hình v3 Turbo (~1.5GB) về thư mục cache bên trong container nên sẽ mất khoảng vài phút tùy thuộc vào tốc độ mạng.*

---

## 🔍 Xác minh trên Giao diện Web

1. Truy cập trang **Cấu hình (Settings)** -> Tab **Giọng nói (TTS)**:
   - Tại dropdown `Active TTS Provider`, chọn **VieNeu-TTS (Offline, Tăng tốc GPU/CPU)**.
   - Bấm **Lưu cài đặt**.
2. Vào trang xử lý video bất kỳ:
   - Khi chọn cấu hình lồng tiếng, bạn sẽ thấy xuất hiện các giọng đọc: **VieNeu Nữ**, **VieNeu Nam** hoặc **Tự động phân vai Nam/Nữ**.
   - Thử chạy lồng tiếng và kiểm tra chất lượng giọng đọc offline!
