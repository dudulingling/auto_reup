# Nghiên cứu & Đánh giá Tích hợp VieNeu-TTS vào Hệ thống Auto_Reup

Tài liệu này trình bày kết quả nghiên cứu mô hình **VieNeu-TTS** (Vietnamese Text-to-Speech) và đánh giá khả năng tích hợp nó vào hệ thống `auto_reup` hiện tại của bạn, được cập nhật dựa trên dữ liệu sử dụng phần cứng thực tế của bạn.

---

## 1. Tổng quan về VieNeu-TTS

**VieNeu-TTS** là một mô hình chuyển đổi văn bản thành giọng nói (TTS) tiếng Việt tiên tiến được phát triển bởi tác giả `pnnbao97` (Phạm Nguyễn Ngọc Bảo) với các đặc điểm nổi bật:
*   **Instant Voice Cloning (Zero-shot):** Cho phép sao chép (clone) giọng nói bất kỳ chỉ từ một file âm thanh mẫu ngắn khoảng 3–5 giây.
*   **Chất lượng âm thanh cao:** Hỗ trợ tần số lấy mẫu lên đến 24kHz hoặc 48kHz (tùy phiên bản model), cho giọng đọc tự nhiên, truyền cảm và ít bị "robot" hơn các giải pháp cloud truyền thống.
*   **Hỗ trợ song ngữ Anh-Việt:** Xử lý tốt các trường hợp trộn lẫn từ tiếng Anh trong văn bản tiếng Việt (code-switching).
*   **Chạy Offline / On-Device:** Không phụ thuộc vào kết nối Internet hay API Key bên thứ ba (như FPT, ElevenLabs, OpenAI).
*   **Biểu cảm phong phú:** Hỗ trợ chèn các biểu cảm phi ngôn ngữ trực tiếp vào văn bản như `[cười]`, `[thở dài]`,... (đối với model v3 Turbo).

---

## 2. Phân tích & Đánh giá lại Cấu hình Phần cứng Thực tế

Qua kết quả kiểm tra hệ thống và chạy `nvidia-smi` thực tế:
*   **CPU (i5-9300H):** Sử dụng 50-100%, duy trì **100%** khi chạy render video.
*   **RAM:** Chiếm dụng **14/16 GB** (gần chạm ngưỡng tối đa 16GB, chỉ còn trống ~2GB).
*   **GPU tích hợp (Intel HD 630):** Hoạt động khoảng **80%** (chủ yếu gánh hiển thị và giải mã UI/Video nhẹ).
*   **GPU rời (NVIDIA GeForce GTX 1650):** 
    *   **Driver Version:** 595.97
    *   **CUDA Version hỗ trợ tối đa:** 13.2
    *   **VRAM:** Đang sử dụng **0 / 4096 MiB (trống 100%)**.
    *   **Hoạt động:** 0% (Không có tiến trình nào đang sử dụng card đồ họa rời).

### 🔍 Nhận xét:
Card đồ họa rời NVIDIA GTX 1650 đang hoàn toàn rảnh rỗi. Đây là tài nguyên lý tưởng để gánh vác các tác vụ nặng như **VieNeu-TTS (sử dụng CUDA)** và **Render video (sử dụng NVENC)** nhằm giải cứu CPU (đang quá tải 100%) và RAM (đang quá tải 14/16GB).

---

## 3. Xác định Phiên bản CUDA Toolkit Phù hợp

Dựa trên thông số driver của bạn:
*   Driver `595.97` hỗ trợ tối đa **CUDA 13.2**.
*   **Khuyến nghị phiên bản CUDA Toolkit cần cài đặt:** 
    *   **CUDA Toolkit 12.4 (Khuyên dùng - Ổn định nhất):** Đây là phiên bản CUDA phổ biến nhất hiện nay cho các thư viện AI Python (như PyTorch, llama-cpp-python prebuilt wheels). Việc cài đặt sẽ cực kỳ thuận tiện và ít gặp lỗi tương thích.
    *   **CUDA Toolkit 12.8 (Mới nhất theo khuyến nghị của tác giả VieNeu-TTS):** Phù hợp nếu bạn muốn chạy các phiên bản tối ưu mới nhất, driver của bạn hoàn toàn đáp ứng được.

---

## 4. Hướng dẫn Cấu hình để Kích hoạt GPU rời NVIDIA trên Windows

Để đánh thức GPU NVIDIA rời trên máy tính của bạn gánh vác hệ thống, bạn cần làm các bước sau:

### Bước 1: Ép Windows chạy Python trên GPU rời
1. Mở **Start Menu** trên Windows, gõ và chọn **Graphics Settings** (Cài đặt đồ họa).
2. Ở mục *Choose an app to set preference*, chọn **Desktop app** và bấm **Browse**.
3. Tìm đến file `python.exe` của môi trường ảo (venv) đang chạy backend của bạn (ví dụ: `d:\Code\auto_reup\backend\venv\Scripts\python.exe`).
4. Sau khi thêm vào danh sách, bấm vào nó -> Chọn **Options** -> Chọn **High Performance** (NVIDIA GeForce GTX 1650) -> Bấm **Save**.

### Bước 2: Cài đặt CUDA Toolkit 12.4
1. Tải và cài đặt **CUDA Toolkit 12.4** từ trang web chính thức của NVIDIA.
2. Đảm bảo cài đặt thành công bằng cách mở terminal mới và chạy lệnh `nvcc --version`.

### Bước 3: Cài đặt thư viện Python hỗ trợ GPU
Để cài đặt VieNeu-TTS chạy trên GPU CUDA:
```powershell
# Thiết lập biến môi trường CUDA trước khi cài đặt llama-cpp-python để nó compile hỗ trợ GPU rời
$env:CMAKE_ARGS="-DGGML_CUDA=on"
pip install llama-cpp-python --force-reinstall --upgrade --no-cache-dir
pip install vieneu
```

### Bước 4: Kích hoạt trong cài đặt ứng dụng
1. Vào trang cài đặt (Settings) của ứng dụng hoặc sửa trực tiếp file `data/.env`.
2. Bật tùy chọn **Tăng tốc phần cứng GPU** (`USE_GPU_ACCELERATION=True`).
3. Khởi động lại backend để áp dụng các thay đổi.
