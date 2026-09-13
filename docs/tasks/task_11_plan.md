# 📋 KẾ HOẠCH TRIỂN KHAI TASK 11: CỖ MÁY AUTO UPLOAD (PHASE 3)

## 🎯 Mục tiêu
Xây dựng một hệ thống hoàn toàn tự động, nhận các video đã qua chỉnh sửa (Phase 2) và tự động rải lên các tài khoản Mạng xã hội đã kết nối ở (Task 4) theo lịch trình đặt trước, kèm theo Caption & Hashtag do AI tự viết.

---

## 🛠️ CHI TIẾT CÁC GIAI ĐOẠN (PHASES)

### Giai đoạn 1: Xây dựng Cơ sở Dữ liệu & Hệ thống Lập lịch (Scheduler)
- **Model `UploadSchedule`**: Tạo bảng lưu trữ thông tin lịch đăng.
  - Các trường: `id`, `video_id` (khoá ngoại), `account_id` (khoá ngoại), `scheduled_time` (thời gian dự kiến đăng), `status` (pending, uploading, success, failed), `post_url` (link sau khi đăng), `error_message`, `retry_count`.
- **Chống trùng lặp**: Logic kiểm tra trước khi thêm lịch (1 Video không đăng lại trên cùng 1 Tài khoản).
- **Celery Beat**: Thiết lập bộ đếm thời gian (Cronjob) quét mỗi phút một lần. Nếu thấy có video đến giờ `scheduled_time` và `status=pending`, sẽ đẩy vào hàng đợi (Queue) để tiến hành Upload.

### Giai đoạn 2: Trí tuệ Nhân tạo (AI Content Generator)
- **Auto Caption**: Tích hợp Google Gemini (đã có sẵn `GEMINI_API_KEY`) để phân tích tên video hoặc file text/subtitles và sinh ra 1 đoạn Caption cực kỳ thu hút, giật tít ngắn gọn.
- **Auto Hashtag**: Dựa vào cơ sở dữ liệu Hot Trend (Task 9) để nhét thêm 3-5 hashtag đang viral vào cuối Caption.
- Cơ chế linh hoạt: Người dùng có thể để hệ thống tự viết, hoặc có thể vào xem lịch đăng và chỉnh sửa lại tay (Override) trước khi video được lên sóng.

### Giai đoạn 3: Động cơ Upload 1 - Môi trường Giả lập Trình duyệt (Playwright / Stealth)
> Đây là phương án chính và tối ưu nhất cho nền tảng web (TikTok Web, YouTube Studio, Instagram PC).
- **Cơ chế**: Dùng thư viện `playwright` kết hợp `playwright-stealth` để chống bị nền tảng phát hiện là Bot.
- **Gắn Proxy & Cookie**: Đọc IP/Port và Cookie từ bảng `social_accounts` (đã được giải mã) để nạp thẳng vào Trình duyệt ảo. Không cần đăng nhập bằng mật khẩu (vượt Captcha tự động nhờ Cookie sống).
- **Luồng thao tác (Flow)**:
  1. Mở trang chủ nền tảng (VD: tiktok.com/upload).
  2. Dùng CSS Selector tải file video `mp4` lên.
  3. Dùng lệnh `type` để nhập Caption + Hashtag đã sinh ra ở GĐ 2.
  4. Chờ thanh Upload video chạy xong 100% -> Bấm nút "Đăng" (Post).
  5. Bắt lấy link video vừa đăng và lưu vào DB, chuyển trạng thái `success`.
- **Xử lý sự cố**: Nếu fail, chụp lại ảnh màn hình (Screenshot), lưu log lỗi, tăng `retry_count` và thử lại vào 10 phút sau (Up nối tiếp khi bị gián đoạn).

### Giai đoạn 4: Động cơ Upload 2 - Môi trường Thiết bị thật / Máy ảo Android (ADB)
> Đây là phương án dành cho ứng dụng Douyin/TikTok nội địa hoặc các nền tảng quét giả lập gắt gao.
- **Cơ chế**: Sử dụng giao thức `ADB` (Android Debug Bridge) kết nối qua IP:Port đến điện thoại cắm cáp hoặc máy ảo LDPlayer/Nox.
- **Luồng thao tác (Flow)**:
  1. Đẩy file Video từ Server vào bộ nhớ điện thoại qua lệnh `adb push`.
  2. Bật ứng dụng (VD: Douyin) bằng lệnh `adb shell monkey`.
  3. Mô phỏng tọa độ thao tác (Tap/Swipe) để nhấn vào nút dấu `+`.
  4. Chọn video vừa push vào.
  5. Cài đặt thêm bàn phím `ADBKeyboard` để gõ Caption tiếng Việt không bị lỗi font.
  6. Mô phỏng bấm nút Đăng bài.
- **Hạn chế**: Cần cấu hình phần cứng vật lý khá phức tạp. Hệ thống sẽ có một "Trạm kiểm tra kết nối" (ADB Ping) trước khi đẩy lệnh để tránh treo máy.

### Giai đoạn 5: Giao diện Quản lý (Frontend)
- Tạo một trang **"Lịch Đăng Bài" (Upload Scheduler)** dạng bảng điều khiển.
- **Chức năng**:
  - Chọn 1 hoặc nhiều Video đã Render xong.
  - Tick chọn 1 hoặc nhiều Tài khoản MXH cần rải video lên.
  - Lựa chọn: "Đăng ngay" hoặc "Hẹn giờ" (ví dụ rải 30 phút đăng 1 video).
- **Theo dõi tiến độ**: Giao diện hiển thị trực quan Video nào đang ở trạng thái nào (⏳ Đang đợi, 🚀 Đang up, ✅ Thành công, ❌ Thất bại). Có nút bấm vào để xem lại ảnh màn hình lỗi.

---

## 🚦 THỨ TỰ THỰC THI (ROADMAP)

1. **Step 1:** Khởi tạo cấu trúc DB (`UploadSchedule`) và thiết lập **Celery Beat**. Cập nhật Frontend để có giao diện chọn video lên lịch.
2. **Step 2:** Tích hợp AI sinh Caption & Hashtag.
3. **Step 3:** Xây dựng Động cơ Playwright (Test với YouTube hoặc TikTok trước vì tính ổn định cao).
4. **Step 4:** Xây dựng Động cơ ADB (Test với thiết bị ảo/vật lý).
5. **Step 5:** Ráp nối toàn bộ luồng xử lý lỗi, retry, và báo cáo kết quả lên Frontend.
