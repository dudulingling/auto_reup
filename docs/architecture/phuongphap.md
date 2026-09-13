# HỆ THỐNG AUTO RE-UP VIDEO ĐA NỀN TẢNG

## I. MỤC TIÊU CỐT LÕI
Tự động hóa toàn bộ quy trình: Thu thập (Crawl) -> Xử lý/Chế bản (Edit/Translate) -> Phân phối (Upload) video từ các nguồn (Douyin, Xiaohongshu...) sang các nền tảng đích (TikTok, YouTube Shorts, Facebook Reels...).

## II. QUY TRÌNH HOẠT ĐỘNG (WORKFLOW)

### Phase 1: Thu thập dữ liệu (Data Ingestion)
- **Đầu vào:** URL profile kênh nguồn (hoặc danh sách URL video).
- **Thực thi:**
  - Cào dữ liệu (Scrape) metadata và tải video (không logo/watermark) về Local hoặc Cloud Storage.
  - Cơ chế đồng bộ: Lưu trữ lịch sử các kênh đã quét. Khi quét lại, chỉ tải các video mới (Incremental Sync).
  - Quản lý anti-bot: Tích hợp Proxy và delay ngẫu nhiên để tránh bị block IP.

### Phase 2: Xử lý & Chế bản (Processing & Editing)
- **Nhận diện giọng nói/văn bản:** Chuyển đổi âm thanh (Whisper) hoặc hình ảnh (OCR) thành văn bản gốc.
- **Dịch thuật:** Gọi LLM (OpenAI API, Claude, hoặc Local LLM) để dịch văn bản sang ngôn ngữ đích, tối ưu ngữ cảnh.
- **Render Video:**
  - (Tùy chọn) Chuyển đổi văn bản dịch thành giọng nói mới (Text-To-Speech).
  - Ghép phụ đề (Burn subtitles) và ghép audio mới vào video gốc.
  - Thêm hiệu ứng, chỉnh sửa khung hình, lật video, đổi MD5 (chống đánh bản quyền).

### Phase 3: Phân phối & Đăng tải (Distribution)
- **Lên lịch đăng:** Phân bổ thời gian đăng video theo cấu hình từng kênh để tránh bị nền tảng đánh dấu spam.
- **Đăng tải tự động:** Upload video lên các kênh đích (TikTok, YouTube, Facebook) kèm Tiêu đề, Mô tả và Hashtag đã được LLM tạo sẵn.

## III. QUẢN TRỊ HỆ THỐNG (DASHBOARD & DATABASE)

### 1. Quản lý Dữ liệu (Database)
- Lưu trữ thông tin Kênh Nguồn, Kênh Đích.
- Theo dõi vòng đời Video: Đã tải -> Đang xử lý -> Đã render -> Đã đăng tải -> Lỗi.
- Lưu trữ cấu hình hệ thống, lịch sử hoạt động, log lỗi.

### 2. Quản lý Tài khoản (Account Management)
- Thêm/Xóa/Sửa tài khoản mạng xã hội (Target Accounts) và Cookie/Token.
- Quản lý trạng thái sống/chết của tài khoản.
- Quản lý Proxy gán cho từng tài khoản để tránh liên đới.

### 3. Giao diện (Dashboard)
- Hiển thị trực quan tiến trình (Pipeline) của từng video (Phase 1 -> Phase 2 -> Phase 3).
- Xem thống kê, lịch sử, log lỗi chi tiết để dễ dàng khắc phục (Troubleshooting).
- Điều khiển Play/Pause/Stop các chiến dịch.

## IV. CẤU TRÚC KỸ THUẬT ĐỀ XUẤT
- **Backend:** Python (FastAPI/Django) kết hợp Celery + Redis để xử lý hàng đợi (Task Queue) chạy ngầm (cực kỳ quan trọng cho các phase tốn thời gian như tải và render video).
- **Database:** PostgreSQL (dữ liệu chính) + Redis (Cache/Queue).
- **Frontend:** React/VueJS để làm Dashboard trực quan.
- **Môi trường:** Docker hóa để quản lý môi trường ảo độc lập.

## V. CẤU TRÚC THƯ MỤC DỰ ÁN (DIRECTORY STRUCTURE)
Dựa trên kiến trúc Micro-services / Modular Monolith, dự án được chia thành các phân hệ độc lập:

```text
auto_reup_tiktok/
├── backend/                 # Mã nguồn Backend (Python/FastAPI)
│   ├── app/
│   │   ├── api/             # API Endpoints (Giao tiếp với Frontend)
│   │   ├── core/            # Config, Security, DB connection
│   │   ├── models/          # Database Models (SQLAlchemy)
│   │   ├── schemas/         # Data Validation (Pydantic)
│   │   ├── services/        # Chứa Logic nghiệp vụ (Business Logic)
│   │   │   ├── crawler/     # Phase 1: Cào dữ liệu (Douyin, Xiaohongshu...)
│   │   │   ├── processor/   # Phase 2: Whisper, LLM Dịch thuật, FFmpeg Edit
│   │   │   └── uploader/    # Phase 3: Logic Auto Upload (TikTok, FB, YT...)
│   │   └── worker/          # Định nghĩa các Task chạy ngầm (Celery)
│   ├── requirements.txt
│   └── main.py
├── frontend/                # Mã nguồn Giao diện Quản trị (React/Vue)
│   ├── src/
│   │   ├── components/      # UI Components dùng chung
│   │   ├── pages/           # Các trang (Dashboard, Account, Logs)
│   │   ├── services/        # Call API Backend
│   │   └── utils/
│   └── package.json
├── docker/                  # Cấu hình Docker (Dockerfile, docker-compose.yml)
├── data/                    # Thư mục chứa dữ liệu cục bộ (cần ignore khỏi git)
│   ├── raw_videos/          # Video gốc vừa tải về
│   ├── processed_videos/    # Video đã qua xử lý (thêm sub, lật, đổi MD5)
│   └── db_data/             # Dữ liệu volume của database
├── .env                     # Biến môi trường (DB_URL, API_KEYS)
├── .gitignore
└── phuongphap.txt           # Tài liệu thiết kế hệ thống
```
