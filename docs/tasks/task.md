# DANH SÁCH CÔNG VIỆC (TODO LIST)

## 1. Lưu trữ dữ liệu (Backend)
- [x] Lưu lại các bản `.srt` tách phụ đề từ video gốc.
- [x] Lưu lại các bản dịch thuật tiếng Trung sang tiếng Việt từ file `.srt`.
- [x] Lưu lại các bản audio tiếng Việt (TTS) từ file `.srt`.
- [x] Tất cả lưu vào folder `data/`, phân loại tách riêng biệt thành từng folder nhỏ (`subtitles/`, `audio/`, `processed_videos/`).
- [x] (Yêu cầu 2.a) Lưu lại quá trình của video đang diễn ra để khi lỗi được khắc phục hoặc người dùng muốn dừng tiến trình thì hôm sau có thể tiếp tục xử lý (Auto Resume).
- [x] (Yêu cầu 4) Chạy đa luồng (Multi-threading/Multi-processing với Celery), xử lý nhiều video cùng lúc.

## 2. Nâng cấp chất lượng Video
- [x] (Yêu cầu 3) Phần lồng tiếng điều chỉnh được tốc độ duy trì, tạo điểm nhấn: chỗ nào cần nhấn mạnh thì đọc chậm lại, cần giải thích nhanh thì tăng tốc độ lên dựa trên mật độ chữ (CPS - Characters Per Second).
- [x] Tối ưu hóa việc sử dụng GPU (Phân bổ Whisper / FFmpeg chạy trên CUDA nếu có GPU).


## 3. Giao diện người dùng (Frontend - Dashboard)
- [x] Trong Dashboard, thêm đường dẫn điều hướng đến trang "Lịch sử".
- [x] **Lưu lại lịch sử theo dạng danh sách (List / Table) gồm các cột:**
  - [x] Tên video gốc.
  - [x] Nguồn tải (Douyin, Xiaohongshu, ....). hiện thị tên người dùng hoặc id người dùng
  - [x] Ngày tải.
  - [x] Trạng thái: Tiến độ đang nằm ở bước nào (Sử dụng biểu tượng: chấm xanh = hoàn thành, chấm vàng = đang xử lý/chưa xong).
  - [x] Trạng thái Upload: Đã up lên nền tảng nào theo ngày giờ nào (Nếu chưa up, ghi rõ là "Chưa up lên nền tảng nào").
- [x] **Tính năng Tương tác trên Danh sách Lịch sử:**
  - [x] Ở phần danh sách, khi hiển thị tên file, bản dịch, hoặc file lồng tiếng -> Có nút để xem video, nghe audio, đọc phụ đề trực tiếp (Preview).
  - [x] Chức năng "Chọn hàng loạt" (Checkboxes) để Xóa nhiều video hoặc Chỉnh sửa hàng loạt.
- [x] **Tính năng Tìm kiếm & Lọc:**
  - [x] Tìm kiếm theo ngày tải.
  - [x] Lọc theo nguồn tải (Douyin, Xiaohongshu...).
  - [x] Lọc theo tiến trình video (đã dịch thuật, đã sinh audio...).
- [x] **Giao diện Trực quan (Workflow UI):**
  - [x] Cấu trúc UI theo thứ tự dạng Workflow rẽ nhánh (Ví dụ: Từ việc này sang việc khác).
  - [x] Thêm các Animation (Hiệu ứng chuyển động) đẹp mắt giữa các bước xử lý (Đã tải về -> Đã dịch -> Đã sinh audio -> Đã render -> Đã up).
  - [x] Chỉ để 2 tiến trình đang xảy ra và tiếp theo, ví dụ quá trình đang ở nhận diện thì chỉ hiện nhận diện -> dịch
  - [x] Phía trên cùng thêm ghi chú workfow để người dùng hiểu các bước
  - [x] Nếu tiến trình của video đó chưa hoàn thành đến bước cuối cùng là render video, thì hãy thêm nút play bên cạnh workflow để người dùng bấm vào thì tiến trình video tiếp tục chạy luôn không cần chuyển qua trang edit
- [x] **Tính năng Chỉnh sửa (Edit Video):**
  - [x] Thêm mục "Edit": Bấm vào sẽ chuyển sang một trang chuyên dụng để Edit Video.
  - [x] Chức năng Edit: Cho phép thay đổi giọng nói (Voice AI khác), lấy lại và chỉnh sửa phụ đề, và tái sử dụng lại âm thanh đã lồng tiếng trước đó để render lại video mới.
## 4. Tab quản lý tài khoản mạng xã hội như tiktok, youtube, instagram... 
- [x] Thêm tab "Quản lý tài khoản mạng xã hội" vào Dashboard.
- [x] Trong tab "Quản lý tài khoản mạng xã hội", hiển thị danh sách các tài khoản mạng xã hội đã được thêm vào hệ thống.
- [x] Thêm chức năng "Thêm tài khoản mạng xã hội" vào tab "Quản lý tài khoản mạng xã hội".
- [x] Thêm chức năng "Xóa tài khoản mạng xã hội" vào tab "Quản lý tài khoản mạng xã hội".
- [x] Thêm chức năng "Chỉnh sửa tài khoản mạng xã hội" vào tab "Quản lý tài khoản mạng xã hội".
- [x] Thêm chức năng "Kiểm tra trạng thái tài khoản mạng xã hội" vào tab "Quản lý tài khoản mạng xã hội"
- [x] Thêm chức năng gắn proxy vào tài khoản mạng xã hội (tài khoản mạng xã hội nào cũng có 1 proxy riêng để tránh trùng IP)
## 5. Tối ưu nén bộ nhớ, Ram (backend)
- [x] Tối ưu nén video sau khi render để giảm dung lượng file.
- [x] Giữ lại data dưới dạng gói (archive) để đẩy lên Cloud, giải pháp an toàn nhất để đảm bảo có thể "Rollback" hoặc tận dụng lại file gốc bất kỳ lúc nào. (Đã có /api/history/backup)
## 6. Thêm tab chức năng sao chép (backend + frontend)
- [ ]. Người dùng nhập đường dẫn đến user của nền tảng, hệ thống sẽ lưu lại id, tên user đó, sau đó quét video mới nhất của user đó và tải về.
- [x] Integrate Demucs via `audio-separator` for BGM extraction.
- [x] Integrate Pyannote for speaker diarization to support multiple AI voices.
- [x] Expose configuration flags via API (HF Token, Enable Demucs, Enable Diarization, BGM Volume).
- [x] Update Settings Frontend UI to control these features.
- [ ]. Hệ thống sẽ so sánh video đã tải về với video đã có trong database để tránh tải lại video đã tải.
- [ ]. Không cập nhật liên tục, thêm nút "Kiểm tra data", để phát hiện user đó có đăng tải video nào mới không, sau đó mới chạy tiến trình
- [ ]. Tự động up video sau khi chỉnh sửa của user đó lên các nền tảng đến 1 tài khoản mạng xã hội khác được gắn vào
## 7. Nâng cấp chạy nhiều video cùng lúc từ nhiều user khác nhau
 - [x]. Đầu tiên nâng cấp hệ thống có thể xử lý được nhiều video cùng lúc (tải và edit) cùng lúc, số luồng 1 thời điểm tùy thuộc vào lựa chọn người dùng
 - [x]. Phần cào dữ liệu có thể cào 1 video từ url hoặc nhiều video từ nhiều url khác nhau hoặc cào toàn bộ video của một user nào đó sau đó tạo thành 1 folder lưu trong /raw_data (đặt tên folder theo id và tên user + tên nền tảng)
 - [x]. Tương tự phần edit người dùng nhập đường dẫn của 1 hoặc nhiều video đã lưu trong máy (thường là ở /raw_videos) hoặc nhập đường dẫn đến folder video thì hệ thống sẽ edit toàn bộ video trong folder đó
## 8. Quản lý trùng lặp data
 - [x]. Kiểm tra video bị trùng lặp dựa vào url hoặc id của video, trong tab upload đã có mục kiểm tra video trùng lặp rồi, nhưng cần tối ưu thuật toán để khi tải về cần kiểm tra lại video có bị trùng lặp không (so sánh với file video trong thư mục raw_videos)
 - [x]. Đảm bảo nếu chạy đi chạy lại sẽ không bao giờ tải trùng video đã tải trước đó
 - [x]. Tải tăng dần (Incremental Download): Chỉ tải những video "mới xuất hiện" kể từ lần tải cuối cùng. Khi kiểm tra đường dẫn user
 ## 9. Thêm tính năng tìm kiếm hot trend của douyin, gợi ý những tài khoản viral 
  - [x].  Thiết kế bảng xếp hạng tìm kiếm, hashtag từ khóa hottrend.
  - [x].  Thiết kế bảng gợi ý những tài khoản viral
  - [x]. Thêm trường tìm kiếm để người dùng nhập từ khóa, hastags, sau đó tạo danh sách những video hot theo từ khóa, có thống kê lượt view, tym.
  - [x]. Mỗi bảng xếp hạng gợi ý tối đa 10 video hoặc 10 user 
## 10. Tab lịch sử
 - [x] thêm cột STT ở đầu, 
 - [x] Kiểm tra lại xem khi người dùng chọn edit video hàng loạt, thì khi hệ thống đang xử lý video nào thì có chuyển nút pause đã chuyển sang play như click play từng video chưa.
 - [x] Thu nhỏ trường tiến trình, thêm cột "ghi chú" ở sau "Trạng thái", log lại lỗi nếu quá trình edit gặp sự cố, còn cột tiến trình gặp lỗi ở quá trình nào thì vẫn hiện ở quá trình đó.
 - [x] Nếu tiến trình edit video bị lỗi, thì tô đỏ nhạt cho cả hàng video bị lỗi,
## 11. Phase 3, upload video tự động lên các nền tảng có sẵn
  Xây dựng 2 hệ thống up video tự động 
  + Hệ thống đầu tiên : up qua adb điện thoại Android (Up lên Douyin, Youtube )
  + Hệ thống thứ 2:  up qua máy ảo (người dùng cấp quyền tài khoản và mật khẩu + proxy)
 Yêu cầu: 
 - Tự động đăng bài, thêm hastag hot, chỉnh sửa description, viết cap ngắn gọn.
 - Đặt lịch, thời gian đăng bài, up nối tiếp khi bị gián đoạn, xử lý lỗi video up thất bại , tránh đăng trùng lặp video.
## 12. Một số lỗi 
Khi kích hoạt vào lịch bài đăng hiện toast báo lỗi" Lỗi khi tải dữ liệu bài đăng"
- Kiểm tra lại hệ thống, khi tôi tải video thành công từ phần " Cào video", nhưng lịch sử không hiện video đó.
- Phần thêm tài khoản mạng xã hội, khi chạy local tôi chỉ cần thêm token hoặc cookie là được, không phải thêm proxy đúng không?
## 13. Tính năng mở rộng cho tương lai (Future Tracking)
 - [ ] Chuyển đổi phương thức đăng nhập tài khoản sang dạng **Nhúng Trình duyệt Ảo (NoVNC)** vào giữa trang Web. Triển khai Docker container `kasmweb/chrome` hoặc `selenium/standalone-chrome-debug` để người dùng thao tác trực tiếp trên giao diện web mà không cần Local Agent.
 - [x] Tự động lấy tên người tài khoản, id tài khoản và avatar đăng nhập (Hoàn thành qua tính năng của Local Agent).
  - [x] Kiểm tra video đã render khi đã up lên nền tảng, id , tên  và avatar người dùng nào trong tài khoản mxh thì phần lịch sử, video đó cũng cập nhật luôn ở trường trạng thái upload.
  - [x] hiện log đã up thành công, hiện link post nhưng bấm vào link thì không thấy video đâu? (Đã thay mã Mock bằng Bot Automation thực tế Playwright)
## 14. Cập nhật lại dữ liệu khi đồng bộ dữ liệu
 - [x] Tải lại toàn bộ dữ liệu lịch sử video trong phần data, hiện thị đúng theo thư mục (nguồn tải, ngày tải, đã render ...) (Đã có API Sync Database)
 - [x] Có cách nào lưu những video đã up lên tài khoản nào không, khi máy bị reset dữ liệu hoặc đồng bộ dữ liệu giữa các máy không, đặc biệt là phương thức sử dụng ADB để kết nối
 - [x] Có cách nào đồng bộ tài khoản mạng xã hội đang sử dụng không?

## 15. Sửa lại edit video
- [x] Phụ đề sau khi dịch sang tiếng việt nên được căn chỉnh đè lên phụ đề gốc của video (Sử dụng kỹ thuật Bounding Box)
- [x] Phụ đề gốc video nên được làm mờ hoặc ẩn đi (Tự động che bởi Bounding Box).
- [x] Thêm tùy chỉnh lật video nếu muốn (Thêm Checkbox ở frontend và API hỗ trợ hflip).

## 16. Lộ trình Nâng cấp Hệ thống Reup Công nghiệp (Phase 2)
- [x] **1. Cơ chế Lách Bản Quyền Cấp Độ Cao (Unique-ification):** Tự động lật viền, Zoom (101%-105%), chỉnh Brightness/Contrast, và chèn Noise overlay (nhiễu 1%). Bóp méo cao độ (Pitch shift) của âm thanh để lách bản quyền.
- [x] **2. Nâng cấp Trình duyệt Chống phát hiện (Anti-Detect Browser):** Tích hợp `playwright-stealth` hoặc liên kết API với AdsPower / GoLogin để xóa dấu vết Webdriver, mỗi tài khoản một Profile sạch.
- [x] **3. Tự động "Nuôi" Tài khoản (Account Warm-up):** Kịch bản Playwright tự động lướt For You, xem video, thả tim, comment dạo như người thật trước khi up để tránh Shadowban.
- [ ] **4. Quản lý Tài nguyên Dữ liệu (Auto Cleanup):** Celery Cronjob tự động xóa các file video/audio rác đã up quá 7 ngày, hoặc đẩy lên Cloud để dọn dẹp dung lượng Ổ cứng Server.
- [ ] **5. Cào Dữ liệu Tương tác (Analytics Dashboard):** Celery Task tự động lấy chỉ số Lượt xem, Tim, Comment của các video đã up và đổ ra Dashboard Báo cáo hiệu suất từng tài khoản.
17. Hoàn thiện kịch bản Auto-Click ADB (Tọa độ, UI Element) cho TikTok/Douyin (Warmup Engine).**t

## 19. Lộ trình Nâng cấp lên Nền tảng Công nghiệp (Enterprise Platform)
### 🛡️ Máy chủ & Logic (Backend)
- [ ] **Hệ thống "Dọn rác" tự động (Garbage Collection):** Tạo Cronjob (Celery Beat) chạy lúc 2h sáng rà quét và tự động xóa các file rác (mp4, mp3, srt) của các video đã đăng thành công quá 3 ngày để giải phóng ổ cứng.
- [x] **Quản lý Proxy / IP Xoay (Proxy Rotation):** Tạo Database quản lý HTTP Proxy. Gắn cố định mỗi "Tài khoản GPM/ADB" với 1 IP Proxy để tạo độ trust và chống ban IP khi tải video.
- [x] **Hệ thống cảnh báo Account Health:** Bot tuần tra kiểm tra view sau 24h. Đánh dấu đỏ cảnh báo "Shadowban" nếu video 0 view để người dùng chuyển sang chế độ Warmup.
- [x] **Error Handling & Retry Queues:** Tự động thử lại (Retry) các Task Celery khi mạng lỗi, proxy chết.

### 20. 🖥️ Trải nghiệm & Giao diện (Frontend)
- [x] **Bảng điều khiển (Analytics Dashboard):** Tạo trang tổng quan sử dụng React Recharts biểu đồ hóa hiệu suất: Video đã cào, Số lượng Up thành công/Thất bại, Tăng trưởng View/Follower.
- [ ] **Tab Sáng tạo AI Faceless:** Nhập Prompt -> AI viết kịch bản -> AI sinh ảnh/video stock -> Đọc TTS -> Ráp video hoàn chỉnh và Auto-Upload.
- [x] **Lưu Cấu hình Edit mẫu (Edit Profiles):** Cho phép người dùng lưu các Preset (VD: "Mẫu Kinh dị: Lật gương + Zoom 105% + Font A"). Bấm 1 nút áp dụng cho 50 video cùng lúc.
- [x] **Tiến độ Thời gian thực (Real-time Progress Bar):** Tích hợp WebSockets/SSE để thanh tiến độ Render và Tải video chạy mượt mà theo % thực tế thay vì F5 thủ công.

## 21. Các Tính năng Nâng cấp Mở rộng (Đề xuất mới)
- [ ] **Smart Crop (Auto Re-frame 16:9 -> 9:16):** Tích hợp AI (OpenCV) nhận diện khuôn mặt người nói để tự động crop khung hình dọc bám theo chuyển động (chống reup hiệu quả cho video YouTube/Ngang).
- [ ] **Chèn Logo/Watermark Động:** Tùy chọn cho phép Logo di chuyển ngẫu nhiên hoặc trôi nổi khắp màn hình để tránh bị AI của nền tảng quét mã băm (hash) tĩnh.
- [ ] **Voice Cloning (Lồng tiếng AI Độc quyền):** Tích hợp API của ElevenLabs hoặc VITS cho phép nhân bản giọng nói thật của bạn, tự động lồng tiếng cho mọi video reup thay vì dùng giọng Google nhàm chán.
- [ ] **Phân tách Người nói (Pyannote Diarization):** Tự động nhận diện nhiều người nói trong video để gán các giọng lồng tiếng khác nhau (Nam/Nữ) thay vì phải gán thủ công [M]/[F].
- [ ] **Tách Âm thanh Nền (Demucs Audio Separation):** Xóa sạch giọng gốc của video nhưng giữ nguyên 100% tiếng nhạc nền (BGM) và tiếng động môi trường (SFX) để trộn với giọng TTS mới, tạo ra bản lồng tiếng chuyên nghiệp.
- [ ] **Chuyển đổi Giọng nói Cảm xúc (RVC - Retrieval-based Voice Conversion):** Nhái lại giọng nói gốc của video (giữ nguyên tiếng khóc, cười, ho, la hét) nhưng được phát âm bằng ngôn ngữ dịch.

## 22. Lộ trình Nâng cấp "Live Restream" (Giữ chân & Tăng chuyển đổi)
- [ ] **1. Auto Audio Mixer (Nhạc Nền Chill):** FFmpeg tự động giảm âm lượng gốc xuống 20%, mix thêm nhạc Lofi/Trending không bản quyền để lách âm thanh và tăng độ giữ chân.
- [ ] **2. AI Voice Cloning (Lồng tiếng Real-time):** Dùng AI dịch giọng nói idol Trung Quốc thành âm thanh Tiếng Việt siêu thực phát đè lên luồng Live.
- [ ] **3. Khung Viền & Đếm Ngược (Dynamic Overlay):** Chèn các thông báo kích Sale (vd: "Flash Sale 1K giỏ hàng") và đồng hồ đếm ngược kích thích hiệu ứng tâm lý FOMO.
- [ ] **4. Bot Chim Mồi (Auto Chatbot):** Bot tự động thả comment dạo theo kịch bản để tạo luồng tranh luận giả, làm nhộn nhịp không khí phòng Live.
- [ ] **5. Minigame Tương Tác (Vinh danh Real-time):** Quét API comment TikTok, khi có người thả từ khóa, FFmpeg sẽ lập tức đóng mác (drawtext) tên họ lên video để tri ân ngay trên Live reup.
## 23. Fix lỗi đăng bài qua ADB
- [ ]. Với 1 số dòng máy có kích thước khác nhau như snap 88, thì với logic bấm dấu "+"ở trang chủ tiktok 
        dòng 313 và 314 trong file @adb_engine.py:
            logger.info("[ADB] Bấm nút + (Tạo mới) ở giữa cạnh dưới màn hình...")
            automator.click_percentage(0.5, 0.92)
  thì lại bị bấm trượt ra ngoài. cần có cách bấm dựa vào tọa độ UI thực tế. 
  + Đề xuất hướng giải quyết  sau khi bấm lướt 1-2 video để tăng độ trust thì có thể bấm dừng tài khoản để quét XML tìm phần tử đó.
- [ ]. Về tìm thư viện ảnh - video, đa số sẽ không tìm được bằng cơ chế 1 là dùng XML, thay vào đó dùng cơ chế 2 luôn bằng cách
    + Tìm nút bên trái trước (vì đa số máy đều hiện bên trái). tìm nút "Đăng", có thể sử dụng screenshort tìm  vị trí nút đăng, nút đăng thường ở giữa màn hình giống nút chụp (quay, to trắng nhất), 
    + sau đó dịch hết cỡ sang trái, cách trái khoảng 5% màn hình. thử lại bằng cách đối chiếu với  ảnh @tiktok snap 88.jpg
- []. Sau khi đăng video, quay về trang chủ để lướt 1-2 video tăng độ trust,chưa hoạt động vì không  thể tìm được nút" Dành cho bạn" hoặc "Đề xuất"
    + Hướng giải quyết, tìm nút "Đã follow" trước, sau đó tìm nút" Đề xuất"hoặc "Dành cho bạn", các mục đề xuất này nằm trên cùng màn hình và bị ẩn hoặc mờ thiếu chữ vì nó quá dài.
    docker-compose up -d

## 24. Một số lỗi nhỏ cần sửa 
- [ ].  Sau khi chỉnh sửa những video đã edit,hệ thống data vẫn lưu lại video đã edit cũ trước đó
- [ ]. Kiểm tra lại logic tách gốc voice ra khỏi video, vì có thể đó là lý do phần sub dịch bị thiếu, voice gốc tách bị thiếu -> srt gốc bị thiếu  -> sub dịch thiếu -> voice tts bị thiếu.
