# 📚 TÀI LIỆU KỸ THUẬT & HỆ THỐNG (PROJECT DOCUMENTATION)

Chào mừng bạn đến với kho tài liệu kỹ thuật của dự án **Auto Reup TikTok / Douyin**.
Toàn bộ tài liệu được phân loại theo từng nhóm chức năng cụ thể dưới đây:

---

## 🏛️ 1. Kiến Trúc Hệ Thống (`docs/architecture/`)
Các tài liệu phân tích mô hình, luồng dữ liệu và thiết kế kiến trúc toàn diện:
- [douyin_to_tiktok_restream.md](file:///docs/architecture/douyin_to_tiktok_restream.md): Quy trình luồng Restream & Re-up từ Douyin sang TikTok.
- [logic_tai_khoan.md](file:///docs/architecture/logic_tai_khoan.md): Cơ chế quản lý tài khoản mạng xã hội, phân quyền và liên kết phiên.
- [mohinhtuonglai.md](file:///docs/architecture/mohinhtuonglai.md): Tầm nhìn kiến trúc mở rộng và tương lai của hệ thống.
- [phuongphap.md](file:///docs/architecture/phuongphap.md): Phương pháp luận xử lý video, lách bản quyền và an toàn tài khoản.
- [google_veo3_integration.md](file:///docs/architecture/google_veo3_integration.md): Thiết kế tích hợp Google Veo3 & AI sinh video.
- [LAYOUT_REDESIGN.md](file:///docs/architecture/LAYOUT_REDESIGN.md): Thiết kế tái cấu trúc giao diện người dùng.
- [NEW_FRONTEND.MD](file:///docs/architecture/NEW_FRONTEND.MD): Đặc tả công nghệ và UI/UX Cyberpunk Glassmorphism.

---

## 🚀 2. Các Giai Đoạn Phát Triển (`docs/phases/`)
Đặc tả chi tiết từng Phase nghiệp vụ của hệ thống:
- [phase1_douyin_crawler.md](file:///docs/phases/phase1_douyin_crawler.md): **Giai đoạn 1** - Trình cào video Douyin / TikTok không logo.
- [phase2_processor.md](file:///docs/phases/phase2_processor.md): **Giai đoạn 2** - Bộ máy xử lý video, tách nhạc, Whisper AI, dịch thuật và render phụ đề.
- [phase3_uploader.md](file:///docs/phases/phase3_uploader.md): **Giai đoạn 3** - Động cơ đăng bài tự động (GPM Anti-detect Browser & ADB Engine) và Warmup nuôi nick.
- [fastapi_integration.md](file:///docs/phases/fastapi_integration.md): Tài liệu tích hợp Backend FastAPI & Celery background tasks.
- [frontend_dashboard.md](file:///docs/phases/frontend_dashboard.md): Đặc tả bảng điều khiển Dashboard và luồng người dùng.

---

## 📖 3. Cẩm Nang & Hướng Dẫn (`docs/guides/`)
- [Huong_dan_cai_dat.md](file:///docs/guides/Huong_dan_cai_dat.md): Hướng dẫn cài đặt chi tiết cho người phát triển.
- Xem thêm hướng dẫn A-Z tại [SETUP_GUIDE.md](file:///SETUP_GUIDE.md) ở thư mục gốc.

---

## 📝 4. Ghi Chú Nghiên Cứu & Nhiệm Vụ (`docs/tasks/`)
- [task.md](file:///docs/tasks/task.md): Danh mục nhiệm vụ và checklist triển khai tổng thể.
- [task_11_plan.md](file:///docs/tasks/task_11_plan.md): Kế hoạch chi tiết Task 11 (Tối ưu hóa pipeline).
- [tts_research_notes.md](file:///docs/tasks/tts_research_notes.md): Ghi chép nghiên cứu công nghệ Text-to-Speech (VieNeu, Edge-TTS, FPT.AI).
- [promt_ai.md](file:///docs/tasks/promt_ai.md): Mẫu prompts AI dùng trong xử lý nội dung và tạo kịch bản.
- [walkthrough.md](file:///docs/tasks/walkthrough.md): Nhật ký nghiệm thu và tổng hợp thay đổi của các lần bàn giao.
