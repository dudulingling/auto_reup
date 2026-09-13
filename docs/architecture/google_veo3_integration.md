# Kế hoạch Tích hợp Giải pháp Tạo Video AI bằng Google Veo (Vertex AI)

Tài liệu này mô tả chi tiết logic và các công cụ cần thiết để xây dựng Tab "Tạo Video AI" sử dụng mô hình Google Veo, tập trung vào khả năng mở rộng và trải nghiệm người dùng (UX) không gián đoạn.

---

## 1. Logic Luồng hoạt động (Workflow)

Quá trình tạo video bằng AI tạo sinh (Generative AI) đòi hỏi thời gian xử lý rất lâu. Do đó, logic hệ thống bắt buộc phải thiết kế theo hướng **Bất đồng bộ (Asynchronous)**.

1. **Giao diện (Frontend)**: 
   - Người dùng truy cập Tab "Tạo Video AI".
   - Nhập thông tin: `Prompt` (Nội dung cần tạo), `Aspect Ratio` (16:9 cho Youtube, 9:16 cho TikTok/Douyin), và tải lên `Image` (nếu dùng chế độ Image-to-Video).
   - Nhấn "Tạo Video".
   
2. **Tiếp nhận (FastAPI Backend)**: 
   - Backend nhận Request, lưu bản ghi vào Database (bảng `AIVideoHistory`) với trạng thái `pending`.
   - Backend đẩy một Task vào hàng đợi (Message Queue) thay vì đứng đợi API của Google phản hồi.
   - Trả về ngay lập tức cho Frontend một `task_id` để UI hiển thị thanh tiến trình.

3. **Xử lý ngầm (Celery Worker / Background Task)**:
   - Worker nhận Task, gọi đến API của **Google Cloud Vertex AI** (nơi host mô hình Veo).
   - Worker định kỳ (Polling) hỏi Google Cloud xem video đã render xong chưa.
   
4. **Hoàn thành & Lưu trữ**:
   - Khi Google báo hoàn thành, API sẽ trả về một link Cloud Storage.
   - Celery Worker sẽ tải file `.mp4` đó về máy tính, lưu vào thư mục `data/ai_videos/`.
   - Cập nhật trạng thái trong Database thành `completed`.

5. **Trải nghiệm tiếp nối**:
   - Sau khi tạo xong, video này có thể được click đẩy thẳng sang quy trình "Cấu hình & Xử lý" ở phần `video_editor` (để tự động thêm sub, đọc giọng AI, lách bản quyền, và đăng bài).

---

## 2. Các công cụ tối ưu cần sử dụng

Để triển khai được hệ thống này mượt mà, chúng ta cần phối hợp các công cụ sau:

### 2.1. Backend API & Quản lý Hàng đợi: Redis + Celery
*Đây là trái tim của hệ thống xử lý bất đồng bộ.*
- **Ưu điểm**:
  - Không làm treo (block) giao diện web hay backend khi phải đợi Google render video.
  - Cơ chế Retry tự động cực tốt (nếu Google API bị ngắt kết nối giữa chừng, Celery tự thử lại).
  - Có thể chạy nhiều worker để tạo nhiều video cùng lúc.
- **Nhược điểm**: Phải tốn tài nguyên chạy thêm 2 container (Redis làm Broker, Celery làm Worker). *Lưu ý: Hệ thống hiện tại có vẻ đã có cơ sở cho Celery ở Phase 1.*

### 2.2. SDK Tương tác AI: `google-cloud-aiplatform`
*Thư viện chính thức của Google để gọi mô hình Veo.*
- **Ưu điểm**: Bảo mật cao (dùng file json credentials), tài liệu rõ ràng, dễ dàng bắt các exception từ Google (ví dụ: lỗi vi phạm chính sách nội dung).
- **Nhược điểm**: Cần phải thiết lập dự án trên Google Cloud Platform (GCP), bật thanh toán (Billing) và cấu hình Service Account.

### 2.3. Cơ chế Cập nhật Real-time: WebSockets hoặc SSE (Server-Sent Events)
*Đẩy thông báo từ Backend lên Frontend khi video tạo xong.*
- **Ưu điểm**: Thay vì Frontend cứ 3 giây phải gọi `fetch()` để kiểm tra trạng thái, Backend sẽ chủ động "bắn" thông báo (Toast) khi video vừa tải xong. Trải nghiệm người dùng cực kỳ chuyên nghiệp (giống Midjourney hay ChatGPT).
- **Nhược điểm**: Setup phức tạp hơn REST API thông thường. Nếu muốn nhanh trong giai đoạn đầu, có thể tiếp tục dùng kỹ thuật Polling `setInterval`.

---

## 3. Kiến trúc Dữ liệu Dự kiến (Database Schema)

Tạo thêm một bảng `AIVideoHistory` trong SQLite:
- `id`: Khoá chính (Primary Key).
- `prompt`: Văn bản mô tả (Text).
- `ratio`: Tỷ lệ video (String - VD: "9:16").
- `status`: Enum (pending, generating, downloading, completed, failed).
- `video_path`: Đường dẫn file local sau khi lưu.
- `error_message`: Lưu lý do lỗi nếu Google từ chối prompt.
- `created_at` / `completed_at`: Đánh giá thời gian render.

---

## 4. Rủi ro & Lưu ý Tối ưu (Critical Notes)

1. **Chi phí (Cost Limit)**: Video AI tạo sinh tốn rất nhiều tiền (tính theo độ phân giải và số giây). Cần set Quota & Budget Alerts trên Google Cloud để tránh lủng ví nếu bị spam prompt.
2. **Bộ lọc an toàn (Safety Filters)**: Google kiểm duyệt cực kỳ gắt gao. Bất kỳ prompt nào dính bạo lực, người nổi tiếng, hoặc NSFW đều bị huỷ ngay lập tức. Backend **bắt buộc** phải parse lỗi này và hiển thị rõ ràng cho người dùng (ví dụ: *"Từ khóa vi phạm tiêu chuẩn cộng đồng"*).
3. **Timeout Handling**: Một task tạo video có thể kéo dài 15 phút. Worker timeout phải được cấu hình đủ dài (ví dụ: `time_limit=1800`), nếu không Worker sẽ tự giết tiến trình trước khi Google làm xong.
