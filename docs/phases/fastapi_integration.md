# Kế hoạch triển khai FastAPI (Kết nối Frontend - Backend)

Mục tiêu: Xây dựng máy chủ API bằng FastAPI để nhận lệnh cào dữ liệu từ giao diện React, thực thi lệnh thông qua `douyin_scraper`, và đẩy trực tiếp tiến trình cào (Live Logs) lên màn hình Frontend bằng SSE.

## Chi tiết triển khai

### 1. Backend Dependencies
- Thêm `fastapi`, `uvicorn`, `python-multipart`.

### 2. Khởi tạo FastAPI Server
- `backend/main.py`: App FastAPI, cấu hình CORS Middleware (cho phép port 5173).
- `backend/app/api/crawler.py`: API Endpoint điều phối.

### 3. Tái cấu trúc Crawler Logic
- Nâng cấp `backend/app/services/crawler/douyin_scraper.py` thành hàm Generator, dùng `yield` thay vì `print()` để bắn log.

### 4. Kết nối Frontend (API Call)
- Cập nhật `frontend/src/pages/Phase1Crawler.jsx` sử dụng `fetch()` và `EventSource` (SSE) để đọc log trực tiếp.
