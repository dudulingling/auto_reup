# Kế hoạch triển khai Phase 1: Cào dữ liệu video Douyin

Mục tiêu: Xây dựng module cào dữ liệu video (không watermark) từ Douyin, đồng thời xây dựng cơ chế tải lũy tiến (chỉ tải video mới).

## Chi tiết triển khai

### 1. Nền tảng
- Tập trung cào **Douyin** trước, theo yêu cầu của user.
- Tạm thời hỗ trợ tải các video public (không cần cookie). File code sẽ được thiết kế mở để dễ dàng truyền cookie vào khi người dùng có sẵn.

### 2. Công cụ
- Sử dụng thư viện `yt-dlp` để tải video không logo (rất mạnh cho Douyin/TikTok).
- Sử dụng `httpx` (hoặc `requests`) nếu cần gọi API bổ sung từ bên ngoài.

### 3. Cơ chế đồng bộ (Incremental Sync)
- Sử dụng file JSON cục bộ (`data/db_data/download_history.json`) để lưu trữ danh sách ID các video đã tải. Tránh tải lại làm lãng phí băng thông ổ cứng.

## Cấu trúc các file mã nguồn sẽ tạo
1. `backend/requirements.txt`: Chứa dependencies.
2. `backend/app/services/crawler/douyin_scraper.py`: Logic tải video từ Douyin qua `yt-dlp`.
3. `backend/app/services/crawler/sync_manager.py`: Logic đọc/ghi file JSON lịch sử.
4. `backend/app/services/crawler/cli.py`: Giao diện dòng lệnh để test chức năng.
