# Hướng Dẫn Cài Đặt & Sử Dụng Dự Án Auto Reup TikTok (Bản Nâng Cấp)

Tài liệu này hướng dẫn chi tiết cách cài đặt và sử dụng hệ thống Tự động hóa TikTok, bao gồm các tính năng mới nhất như Trình duyệt ẩn danh (GPM), Nuôi tài khoản giả lập (ADB) và Tăng tốc phần cứng (GPU).

---

## 📌 Phần 1: Yêu cầu hệ thống (System Requirements)

Để hệ thống hoạt động đầy đủ chức năng, máy tính của người dùng cần được cài đặt:

1. **[Git](https://git-scm.com/)**: Tải mã nguồn.
2. **[Docker Desktop](https://www.docker.com/products/docker-desktop/)**: Để chạy máy chủ (Backend/Frontend/Database) và Redis.
3. **[GPM Login](https://gpmlogin.com/)** *(Tùy chọn nhưng khuyến nghị)*: Phần mềm quản lý trình duyệt ẩn danh (Anti-detect browser) dùng để đăng nhập và tải video lách luật. Cần bật API trong phần cài đặt của GPM.
4. **Giả lập Android (LDPlayer / MEmu / Nox)** *(Tùy chọn nhưng khuyến nghị)*: Dùng cho tính năng "Nuôi Tài Khoản" (Warmup). Cần bật tính năng **ADB Debugging** (Gỡ lỗi USB) trong cài đặt của giả lập.
5. **VGA/GPU (Intel/Nvidia)** *(Tùy chọn)*: Hỗ trợ tăng tốc độ render video (FFMPEG Hardware Acceleration).

---

## ⚙️ Phần 2: Cài đặt và Khởi chạy

### Bước 1: Tải mã nguồn và Khởi động Hệ thống
1. Mở Terminal (Command Prompt hoặc PowerShell) tại nơi bạn muốn lưu dự án.
2. Tải code về:
   ```bash
   git clone <đường_link_repository_github>
   cd auto_reup_tiktok
   ```
3. Khởi động Docker Desktop (để phần mềm chạy ngầm).
4. *(Dành riêng cho máy có GPU hỗ trợ FFMPEG)*: Mở file `docker-compose.yml`, kiểm tra và thêm cấu hình GPU (ví dụ mapping `/dev/dri:/dev/dri` đối với chip Intel, hoặc cài Nvidia Container Toolkit đối với card Nvidia) nếu muốn dùng tăng tốc phần cứng. 
5. Chạy lệnh sau để tự động tải thư viện và chạy hệ thống:
   ```bash
   docker-compose up -d --build
   ```
   *(Quá trình này có thể mất 5-10 phút trong lần chạy đầu tiên).*

### Bước 2: Truy cập Web và Cấu hình Ban đầu
1. Mở trình duyệt web của bạn và truy cập: 👉 **http://localhost:5173**
2. Chuyển sang Tab **⚙️ Cài đặt (Settings)** trên giao diện web.
3. Điền các thông số bắt buộc:
   - **Gemini API Key:** (Bắt buộc) Dùng để dịch thuật và phân tích vai Nam/Nữ.
   - **Groq API Key:** (Tùy chọn) Dùng cho Whisper siêu tốc (Nhận diện giọng nói). Bật công tắc Groq nếu muốn dùng.
   - **GPM API URL:** Nếu bạn dùng GPM Login, điền đường dẫn API (Thường là `http://127.0.0.1:19995`).
   - **Tăng tốc phần cứng (GPU):** Bật công tắc này nếu máy bạn hỗ trợ Intel QSV hoặc Nvidia NVENC.
4. Nhấn **Lưu cấu hình**. (Hệ thống sẽ tự động lưu các thông số này vào file `.env` ở Backend).

---

## 🚀 Phần 3: Hướng dẫn sử dụng các chức năng chính

### 1. Quản lý & Thêm Tài Khoản (Account Management)
*Hệ thống cho phép bạn quản lý nhiều tài khoản mạng xã hội để phục vụ việc tự động đăng video.*
1. Chuyển sang Tab **👤 Quản Lý Tài Khoản** (Social Accounts).
2. Nhấn nút **Thêm Tài Khoản**.
3. Tại bảng thông tin, điền:
   - **Tên tài khoản**: Tên gợi nhớ.
   - **Nền tảng**: TikTok, Douyin, YouTube, v.v.
   - **Phương thức đăng**: Chọn GPM (trình duyệt ẩn danh) hoặc ADB (giả lập/điện thoại thật).
   - **GPM Profile ID / ADB Device ID**: Xem hướng dẫn lấy ID ở các mục bên dưới.
4. Lưu lại. Tài khoản sẽ hiển thị trong danh sách để bạn chọn khi Lên lịch đăng bài.

### 2. Kết Nối Điện Thoại / Giả Lập qua ADB (Dành cho Đăng & Nuôi Tài Khoản)
*Phương thức này sử dụng thiết bị Android thực tế hoặc giả lập (LDPlayer, Nox...) để thao tác bằng Auto-Click như người dùng thật.*
1. Bật **Gỡ lỗi USB (USB Debugging)** trên thiết bị Android:
   - Điện thoại thật: Cắm cáp vào máy tính, vào *Cài đặt Nhà phát triển* -> Bật *Gỡ lỗi USB*.
   - Giả lập: Vào Cài đặt phần mềm giả lập (VD: LDPlayer) -> Bật chế độ *ADB* hoặc *Gỡ lỗi cục bộ*.
2. Lấy **ADB Device ID**:
   - Mở Terminal/CMD, gõ lệnh `adb devices`.
   - Copy chuỗi ký tự hiển thị (VD: `emulator-5554` hoặc `127.0.0.1:5555`).
   - Điền ID này vào mục **ADB Device ID** khi Thêm tài khoản.

### 3. Kết Nối Trình Duyệt Ẩn Danh (GPM Login)
*Phương thức này sử dụng GPM Login để mở các Profile Chrome ẩn danh (Anti-Detect Browser), giúp lách luật chống bot, chống khóa tài khoản cực tốt.*
1. Mở phần mềm GPM Login trên máy tính.
2. Bật API của GPM: Vào *Settings* -> Bật *Enable API* (Ghi nhớ đường dẫn API, mặc định thường là `http://127.0.0.1:19995`). Điền đường dẫn này vào tab **⚙️ Cài đặt** của hệ thống Auto Reup.
3. Lấy **GPM Profile ID**:
   - Trong GPM Login, tạo một Profile mới và tự đăng nhập sẵn tài khoản TikTok/YouTube của bạn vào đó.
   - Copy mã ID (chuỗi ký tự dài bên cạnh tên Profile).
   - Điền mã này vào mục **GPM Profile ID** khi Thêm tài khoản.

### 4. Cào Video Douyin & Tự động Vượt rào (Anti-Bot)
1. Chuyển sang Tab **🕷️ Cào Video**.
2. Nhập Link Video Douyin/TikTok bạn muốn cào. Video sẽ tự động tải xuống không có logo.
3. **Cơ chế chống chặn:** Hệ thống đã tích hợp thuật toán sinh mã `a_bogus`. Nếu bị yêu cầu Captcha, hệ thống sẽ tự động kích hoạt trình duyệt tàng hình (Playwright) chạy ngầm để lấy Cookie mới và tải tiếp.

### 5. Xử lý, Edit Video & Tùy chỉnh Font chữ
1. Chuyển sang Tab **🎬 Lịch Sử** (nơi chứa các video vừa tải về).
2. Nhấn nút **Play (Cấu hình & Xử lý)** trên video.
3. Chọn **Giọng đọc AI (TTS)** và các tùy chọn lách bản quyền (Lật gương, Zoom, Chỉnh màu).
4. **Font Chữ Tùy Chỉnh:** Bạn có thể tự copy file `.ttf` hoặc `.otf` vào thư mục `data/fonts`. Sau đó F5 lại Web, hệ thống sẽ tự nhận diện để bạn tùy biến Font cho cả Phụ đề và Chữ ký (Watermark).
5. Nhấn **Xác nhận & Xử lý**. Hệ thống sẽ tự động tách lời, dịch AI và render.

### 6. Đăng Video Tự Động Đa Phương Thức (Auto Uploader)
1. Vào Tab **🚀 Tự Động Đăng (Upload Schedule)**.
2. Chọn **Tài Khoản** bạn muốn đăng lên (Đã thêm ở Bước 1).
3. Chọn Video thành phẩm, nhập Caption, #Hashtag và thiết lập **Ngày/Giờ đăng bài**.
4. Nhấn "Lên Lịch". Đến đúng giờ hệ thống sẽ tự động đăng bài:
   - **Nếu đăng qua GPM:** Tự mở Profile Chrome ảo, vào trang web TikTok giả lập thao tác chuột/phím đăng video cực kỳ chuẩn xác.
   - **Nếu đăng qua ADB:** Tự kết nối tới điện thoại/giả lập, mở App TikTok, bấm nút [+] và upload video.

### 7. Nuôi Tài Khoản Giả Lập (Warmup Engine)
*Giúp lướt TikTok tự động để tăng độ Trust.*
1. Đảm bảo giả lập/điện thoại ADB đã bật và mở sẵn TikTok.
2. Trên Web, vào Tab **📱 Nuôi Tài Khoản**. Quét thiết bị giả lập.
3. Thiết lập thời gian lướt. Hệ thống sẽ tự động tìm icon 🤍 (Tym) bằng AI Vision và tương tác tự nhiên.

---

## 🛠️ Phần 4: Xử Lý Sự Cố & Cập Nhật (Troubleshooting)

### 1. Cập nhật Code mới từ Git (Lỗi sập Backend)
Khi có bản cập nhật tính năng mới từ GitHub (Ví dụ: nâng cấp thư viện AI, thêm tính năng Playwright), nếu bạn chỉ chạy `docker-compose up -d`, hệ thống có thể bị sập (Crash) do Docker sử dụng lại môi trường cũ không có thư viện mới.

**Cách cập nhật đúng chuẩn:**
Mở Terminal tại thư mục dự án và chạy lần lượt các lệnh sau để ép Docker cài đặt lại thư viện:
```bash
git pull origin main
docker-compose down
docker-compose up -d --build
```
*(Cờ `--build` cực kỳ quan trọng để đảm bảo mọi thư viện mới trong `requirements.txt` đều được cài đặt lại).*

### 2. Khởi động lần đầu bị lỗi (Database Race Condition)
Nếu ở lần cài đặt đầu tiên mà hệ thống không chạy ngay, **đừng lo lắng!** Đây là do cơ sở dữ liệu PostgreSQL cần 5-10 giây để khởi tạo lần đầu, trong khi Backend khởi động quá nhanh. Hệ thống đã được lập trình cơ chế **Tự động thử lại (Auto Retry)**. Bạn chỉ cần đợi khoảng 10-15 giây là mọi thứ sẽ tự động kết nối và hoạt động bình thường.

### 3. Lỗi thiếu cột Database (Database Schema Mismatch / SQL Error)
Nếu sau khi cập nhật code mới, bạn chạy hệ thống và gặp lỗi SQL dài ngoằng dạng `column process_config does not exist`, thì nguyên nhân là do Docker vẫn đang dùng lại ổ đĩa cơ sở dữ liệu cũ (chưa có các cột mới).

**Cách khắc phục triệt để (Làm mới Database):**
Nếu dữ liệu cũ không quan trọng, hãy xóa ổ đĩa cũ và tạo lại bằng các lệnh sau:
```bash
docker-compose down -v
docker-compose up -d --build
```
*(Cờ `-v` rất quan trọng, nó sẽ xóa các ổ đĩa Volume bị lỗi thời để hệ thống tự động tạo lại cấu trúc Database mới nhất).*

*Lưu ý: Nếu bạn chạy trực tiếp bằng lệnh Python mà không qua Docker, hãy vào thư mục `data/` và xóa thủ công file `history.db` đi rồi chạy lại.*

---
*Hệ thống được phát triển chuyên biệt cho môi trường Windows kết hợp kiến trúc Microservices (Docker + Celery) và tự động hóa web (Playwright / ADB).*
