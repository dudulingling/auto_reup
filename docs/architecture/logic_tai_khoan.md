# Tài Liệu Đặc Tả: Logic Lưu Trữ & Thêm Tài Khoản (Social Accounts)

Tài liệu này mô tả chi tiết cách hệ thống Auto Reup quản lý, lưu trữ và tương tác với các tài khoản mạng xã hội (TikTok, Douyin, YouTube Shorts, v.v.).

## 1. Cấu Trúc Cơ Sở Dữ Liệu (Database Schema)

Hệ thống sử dụng bảng `social_accounts` trong PostgreSQL để lưu trữ trạng thái và thông tin kết nối.

### Các trường dữ liệu (Fields) quan trọng:
- `id`: Khóa chính (UUID/Integer).
- `platform`: Nền tảng mạng xã hội (VD: `tiktok`, `douyin`).
- `username`: Tên hiển thị của tài khoản.
- `account_id`: ID định danh duy nhất của tài khoản trên nền tảng (VD: `@username`).
- `avatar_url`: Đường dẫn ảnh đại diện (Nếu trống, UI tự động tạo avatar chữ cái đầu).
- `connection_type`: Phương thức kết nối (Cốt lõi để điều phối logic hệ thống). Bao gồm:
  - `web_playwright`: Chạy tự động hóa bằng trình duyệt ẩn danh truyền thống.
  - `gpm_login`: Chạy qua profile của GPM (Anti-detect browser).
  - `adb_device`: Chạy tự động hóa bằng cách kết nối trực tiếp vào điện thoại thật hoặc máy ảo (Emulator) qua ADB.
- `auth_data`: Dữ liệu xác thực. Nội dung thay đổi tùy thuộc vào `connection_type`:
  - Đối với Web Playwright: Thường chứa chuỗi JSON Cookie.
- `device_id`: Thông tin định danh thiết bị. Nội dung thay đổi tùy thuộc vào `connection_type`:
  - Đối với GPM Login: Chứa **Profile ID** của GPM (VD: `b7f8c9...`).
  - Đối với ADB: Chứa **IP/Cổng** mạng hoặc serial thiết bị (VD: `192.168.43.1:5555`).
- `status`: Trạng thái hoạt động của tài khoản (`active`, `disconnected`, `failed`, `warming_up`).
- **Proxy fields** (`proxy_host`, `proxy_port`, `proxy_username`, `proxy_password`): Dùng để ẩn danh IP khi đăng bài qua Web.

---

## 2. Logic Thêm Mới Tài Khoản (Add Account Flow)

Khi người dùng thao tác trên giao diện Frontend (`SocialAccounts.jsx`):

### Bước 2.1: Nhập liệu trên UI
- Người dùng bấm **Thêm tài khoản**.
- Chọn **Phương thức kết nối (connection_type)**. Giao diện sẽ động cập nhật các ô nhập liệu:
  - Nếu chọn **GPM Login**: Ẩn ô nhập Cookie, hiện ô nhập **GPM Profile ID**.
  - Nếu chọn **App (ADB)**: Ẩn ô nhập Cookie, hiện ô nhập **Device ID / IP**.
  - Nếu chọn **Web Browser**: Hiện ô nhập **Cookie (JSON)** và cấu hình **Proxy**.

### Bước 2.2: Xử lý Backend API
- Giao diện gọi API: `POST /api/social-accounts/`.
- Backend tiếp nhận JSON Payload, chuẩn hóa dữ liệu.
- Lưu trữ vào DB với trạng thái mặc định là `active`.

---

## 3. Logic "Nuôi" Tài Khoản (Warm-up Engine)

Tính năng "Nuôi" giúp mô phỏng hành vi người dùng thật (xem video, thả tim) để tăng độ uy tín (Trust Score) cho tài khoản, tránh bị nền tảng quét bot.

### Cơ chế hoạt động:
1. **Khởi tạo**: Người dùng bấm nút **Nuôi (Warm-up)** trên UI (Chỉ hiện cho `gpm_login` và `adb_device`).
2. **Cập nhật DB & Giao diện**: 
   - Backend API cập nhật ngay `status = "warming_up"` vào Database.
   - Frontend lập tức đổi nút sang trạng thái **"Đang nuôi..."** (Màu xanh, hiệu ứng nhịp tim) để người dùng biết tiến trình đang chạy. Trạng thái này được lưu xuyên suốt các tab trình duyệt.
3. **Đẩy vào Hàng đợi (Celery Queue)**: 
   - Nhiệm vụ nuôi (`warmup_account_task`) được đẩy vào hệ thống chạy ngầm Celery.
4. **Phân luồng Logic (Factory Pattern)**:
   - `WarmupEngineFactory` sẽ dựa vào `connection_type` để gọi Engine tương ứng:
     - **ADB**: Gọi `adb shell monkey` để mở app (`com.zhiliaoapp.musically` hoặc `com.ss.android.ugc.trill`), giả lập vuốt và chạm màn hình.
     - **GPM**: Gọi API GPM để mở Profile, dùng Playwright để cuộn trang TikTok qua CDP WebSocket.
5. **Hoàn tất**: 
   - Sau khi hết thời gian nuôi (thường 10-15 phút), Celery tự đóng Profile/App.
   - Trả `status` trong Database về lại `"active"`. Giao diện Frontend tự động trở lại bình thường.

---

## 4. Logic Đăng Bài (Upload Engine)

Khi lịch đăng bài đến giờ (Celery Beat trigger):
- Hệ thống lấy thông tin `SocialAccount`.
- Dựa vào `connection_type`, nó sử dụng `UploaderFactory`:
  - **ADB Uploader**: Đẩy video qua cáp/WiFi vào `/sdcard/Download`, phát Broadcast cho Android nhận diện video, rồi mở TikTok, dùng giả lập click thao tác đăng.
  - **GPM Uploader**: Kết nối vào Profile GPM đã mở sẵn, dùng trình duyệt Chrome mượt mà upload lên Web.
  - **Web Playwright**: Mở trình duyệt ẩn danh mới, chèn Cookie vào và thực hiện quy trình đăng. 

## 5. Những Lưu ý Kỹ Thuật (Gotchas)
- **CORS & Mạng Docker**: Khi chạy ADB qua mạng, Docker cần phải dùng cú pháp `host.docker.internal` hoặc nối thẳng vào IP của thiết bị phát WiFi (`192.168.x.x`).
- **GPM Dependency**: Cần phải bật API Port của ứng dụng GPM Client trên Windows (`19995`) để Bot giao tiếp được.
- **Mã hóa Auth Data**: Trong các phiên bản sau, `auth_data` (chứa Cookie) nên được mã hóa AES (Symmetric Encryption) ở cấp độ DB để bảo vệ chống lộ lọt token của người dùng.
