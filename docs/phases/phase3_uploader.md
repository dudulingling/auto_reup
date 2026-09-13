# Tài Liệu Đặc Tả: Phase 3 - Logic Đăng Bài Tự Động (Uploader Engine)

Tài liệu này mô tả chi tiết quy trình (Phase 3) của hệ thống Auto Reup, chịu trách nhiệm tự động hóa việc phân phối và đăng tải video (đã qua xử lý ở Phase 2) lên các nền tảng mạng xã hội dựa trên cấu hình tài khoản.

## 1. Cấu Trúc Dữ Liệu Lịch Đăng (Upload Schedule)

Hệ thống quản lý hàng đợi đăng bài thông qua bảng `upload_schedules` trong Cơ sở dữ liệu.

### Các trường dữ liệu chính:
- `id`: Khóa chính.
- `video_id`: Khóa ngoại liên kết tới video đã được xử lý (Phase 2).
- `account_id`: Khóa ngoại liên kết tới tài khoản mạng xã hội mục tiêu (Phase 1).
- `scheduled_time`: Thời gian dự kiến đăng bài (Timestamp).
- `status`: Trạng thái lịch đăng (`pending`, `processing`, `completed`, `failed`).
- `post_url`: Đường dẫn bài viết sau khi đăng thành công (Nếu nền tảng hỗ trợ trả về).
- `error_message`: Lưu trữ log lỗi nếu tiến trình thất bại.
- `retry_count`: Số lần thử lại (Dùng cho cơ chế Retry tự động).

---

## 2. Quy Trình Kích Hoạt (Trigger Mechanism)

Quá trình đăng bài hoàn toàn tự động, được điều phối bởi hệ thống **Celery Beat** và **Celery Worker**.

1. **Quét lịch định kỳ (Cronjob/Beat)**:
   - Celery Beat chạy task `check_scheduled_uploads` mỗi phút một lần.
   - Truy vấn DB: Tìm tất cả các record có `status == 'pending'` VÀ `scheduled_time <= thời gian hiện tại`.
2. **Đẩy vào Hàng đợi (Queue)**:
   - Với mỗi lịch hợp lệ, chuyển `status = 'processing'`.
   - Bắn task `execute_upload(schedule_id)` vào hàng đợi của Celery Worker để xử lý bất đồng bộ.

---

## 3. Kiến Trúc Lõi Đăng Bài (Uploader Factory Pattern)

Tương tự như tính năng "Nuôi tài khoản", hệ thống đăng bài sử dụng Design Pattern `Factory` để linh hoạt chuyển đổi kịch bản (Engine) tùy thuộc vào `connection_type` của tài khoản mục tiêu.

### 3.1. Web Playwright Engine (`web_playwright`)
- **Nguyên lý**: Điều khiển trình duyệt ẩn danh (Chromium/Firefox) qua thư viện Playwright.
- **Quy trình**:
  1. Khởi tạo trình duyệt với Proxy (nếu có cấu hình).
  2. Bơm `auth_data` (chuỗi JSON Cookie) vào Context của trình duyệt để vượt qua khâu Login.
  3. Điều hướng tới trang Upload của nền tảng (VD: `tiktok.com/upload`).
  4. Bypass các rào cản chống Bot (nếu có).
  5. Upload file video, điền tiêu đề (Caption) + Hashtags.
  6. Bấm nút Đăng bài và trích xuất URL thành phẩm.

### 3.2. GPM Login Engine (`gpm_login`)
- **Nguyên lý**: Kế thừa sức mạnh của Playwright nhưng chạy trên môi trường chống phát hiện (Anti-detect browser) do GPM cung cấp.
- **Quy trình**:
  1. Gửi HTTP Request tới GPM API (Port `19995`) kèm theo `Profile ID` (lưu ở trường `device_id`).
  2. Lấy được WebSocket Debugger URL do GPM trả về.
  3. Dùng lệnh `playwright.chromium.connect_over_cdp()` để "nhập hồn" vào trình duyệt thật đang mở.
  4. Thực hiện các bước Upload tương tự như Web Playwright nhưng với độ an toàn cao hơn (Trust score cao).
  5. Đóng Profile qua GPM API khi hoàn tất.

### 3.3. App ADB Engine (`adb_device`)
- **Nguyên lý**: Giao tiếp trực tiếp với hệ điều hành Android thật hoặc máy ảo (LDPlayer/Nox) qua mạng LAN.
- **Quy trình**:
  1. Gọi `adb connect <IP:Port>` (lưu ở trường `device_id`) để nối sóng với thiết bị.
  2. Dùng lệnh `adb push` chuyển file video đã xử lý vào bộ nhớ trong của điện thoại (Thường là `/sdcard/Download/`).
  3. Gửi tín hiệu Broadcast (MEDIA_SCANNER) ép Android quét lại bộ nhớ để nhận diện video mới.
  4. Tự động nhận diện và gọi Package App (`com.ss.android.ugc.trill`, `com.zhiliaoapp.musically`, v.v.).
  5. Dùng lệnh `adb shell input` (tap, swipe, text) để giả lập thao tác tay: Bấm nút dấu cộng -> Chọn Album -> Chọn Video -> Điền chữ -> Bấm Đăng.
  6. Dọn dẹp video tạm trong `/sdcard/` để tránh đầy bộ nhớ.

---

## 4. Xử Lý Ngoại Lệ & Retry Cơ Bản

Do tính chất không ổn định của mạng lưới và các lớp chống Bot, tiến trình Upload được bọc trong vòng vây kiểm soát lỗi nghiêm ngặt:

1. **Bắt lỗi (Try/Catch)**: Mọi thao tác lỗi (Mất kết nối ADB, Đứt mạng, Sai Cookie, GPM treo) đều bị tóm gọn (Exception).
2. **Ghi log**: Lỗi được ghi thẳng vào trường `error_message` của `upload_schedules`.
3. **Thay đổi trạng thái**: 
   - Đánh dấu `status = 'failed'`.
   - Tăng `retry_count += 1`.
4. **Retry/Hồi sinh**: Người dùng có thể xem nguyên nhân lỗi trên Giao diện Lịch Đăng (Dashboard) và bấm nút **"Thử lại"** để đẩy task về lại trạng thái `pending`.

## 5. Định Hướng Tối Ưu (Future Roadmap)
- Cài đặt thêm ADBKeyboard cho ADB Engine để gõ Tiếng Việt / Unicode (Emoji) vào Caption dễ dàng hơn.
- Triển khai cơ chế xoay vòng (Round-robin) IP/Proxy linh hoạt hơn.
- Tự động hóa quá trình nhận diện OTP nếu Cookie hết hạn đối với Playwright Engine.
