import logging
import os
import json
import time
import random
from typing import Dict, Any
from .base_engine import BaseUploaderEngine
from playwright.sync_api import sync_playwright
from app.core.config import DATA_DIR
from app.core.logger import get_logger

logger = get_logger(__name__)


class PlaywrightUploader(BaseUploaderEngine):
    """
    Engine upload sử dụng Playwright (Stealth mode) thông qua Trình duyệt ảo.
    Chuyên trị các nền tảng: YouTube, TikTok Web, Instagram PC...
    """
    
    def __init__(self, account_data: Dict[str, Any], schedule_id: int = None):
        super().__init__(account_data, schedule_id=schedule_id)
        
        proxy_host = self.account_data.get("proxy_host")
        proxy_port = self.account_data.get("proxy_port")
        proxy_username = self.account_data.get("proxy_username")
        proxy_password = self.account_data.get("proxy_password")
        
        self.proxy_server = None
        self.proxy_auth = None
        if proxy_host and proxy_port:
            self.proxy_server = f"http://{proxy_host}:{proxy_port}"
            if proxy_username and proxy_password:
                self.proxy_auth = {
                    "username": proxy_username,
                    "password": proxy_password
                }
        
        # Parse cookie từ auth_data (đã được giải mã json)
        try:
            self.cookies = json.loads(self.account_data.get("auth_data", "[]"))
        except Exception:
            self.cookies = []

    def _smart_sleep(self, page, timeout_ms: int):
        """
        Poll Redis for cancellation signal while sleeping.
        Uses page.wait_for_timeout to keep the Playwright event loop pumping.
        """
        if not self.schedule_id:
            page.wait_for_timeout(timeout_ms)
            return
            
        elapsed = 0
        interval = 500
        while elapsed < timeout_ms:
            self.check_control()
            page.wait_for_timeout(interval)
            elapsed += interval

    def _apply_stealth(self, page):
        """Inject tệp javascript để ẩn danh bot (Bypass Cloudflare/Tiktok Captcha)"""
        try:
            from playwright_stealth import stealth_sync
            stealth_sync(page)
        except Exception as e:
            logger.warning(f"[Playwright] Không thể áp dụng stealth mode: {e}")

    def upload(self, video_path: str, caption: str, hashtags: str) -> str:
        logger.info(f"[Playwright] Bắt đầu upload video: {video_path}")
        
        if not os.path.exists(video_path):
            raise Exception(f"File video không tồn tại: {video_path}")

        post_url = ""
        full_caption = f"{caption}\n\n{hashtags}"

        # Load environment variables from .env to ensure we get the latest GPM_API_URL
        from dotenv import load_dotenv
        ENV_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../data/.env"))
        load_dotenv(ENV_PATH, override=True)

        with sync_playwright() as p:
            is_gpm = self.account_data.get("connection_type") == "gpm_login"
            gpm_api_url = os.getenv("GPM_API_URL", "").rstrip('/')
            gpm_profile_id = self.account_data.get("device_id")
            
            if is_gpm:
                if not gpm_api_url or not gpm_profile_id:
                    raise Exception("Thiếu GPM API URL hoặc Profile ID để khởi chạy GPM Login.")
                import requests
                logger.info(f"[Playwright] Khởi động GPM Profile {gpm_profile_id}")
                
                ws_endpoint = None
                # Try GPM API v1 first (newer GPMLogin Global versions)
                try:
                    url_v1 = f"{gpm_api_url}/api/v1/profiles/start/{gpm_profile_id}"
                    start_res = requests.get(url_v1, timeout=15)
                    start_data = start_res.json()
                    if isinstance(start_data, dict):
                        if start_data.get("success") and start_data.get("data"):
                            ws_endpoint = start_data["data"].get("websocket_debugging_url") or start_data["data"].get("ws_endpoint")
                    else:
                        logger.warning(f"[Playwright] API v1 trả về dữ liệu không đúng định dạng (có thể là lỗi): {start_data}")
                except Exception as e:
                    logger.warning(f"[Playwright] Thử GPM API v1 thất bại: {e}")
                
                # Fallback to GPM API v2 (older GPM versions)
                if not ws_endpoint:
                    try:
                        url_v2 = f"{gpm_api_url}/api/v2/profile/start?profileId={gpm_profile_id}"
                        start_res = requests.get(url_v2, timeout=15)
                        start_data = start_res.json()
                        if isinstance(start_data, dict):
                            if start_data.get("success") and start_data.get("data"):
                                ws_endpoint = start_data["data"].get("ws_endpoint") or start_data["data"].get("websocket_debugging_url")
                        else:
                            logger.warning(f"[Playwright] API v2 trả về dữ liệu không đúng định dạng (có thể là lỗi): {start_data}")
                    except Exception as e:
                        logger.warning(f"[Playwright] Thử GPM API v2 thất bại: {e}")
                
                if not ws_endpoint:
                    raise Exception(f"Không thể mở GPM Profile qua cả API v1 và v2 cho Profile ID: {gpm_profile_id}")
                
                from urllib.parse import urlparse
                parsed_api = urlparse(gpm_api_url)
                api_host = parsed_api.hostname
                if api_host:
                    ws_endpoint = ws_endpoint.replace("127.0.0.1", api_host).replace("localhost", api_host)
                
                browser = p.chromium.connect_over_cdp(ws_endpoint)
                if browser.contexts and browser.contexts[0].pages:
                    page = browser.contexts[0].pages[0]
                else:
                    context = browser.contexts[0] if browser.contexts else browser.new_context()
                    page = context.new_page()
            else:
                # Cấu hình Proxy nếu có cho Chromium thường
                launch_args = {
                    "headless": True,
                    "args": ["--disable-blink-features=AutomationControlled"]
                }
                if self.proxy_server:
                    launch_args["proxy"] = {"server": self.proxy_server}
                    if self.proxy_auth:
                        launch_args["proxy"]["username"] = self.proxy_auth["username"]
                        launch_args["proxy"]["password"] = self.proxy_auth["password"]

                browser = p.chromium.launch(**launch_args)
                
                ua = self.account_data.get("user_agent")
                if not ua:
                    ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
                
                context = browser.new_context(
                    user_agent=ua
                )
                
                # Add cookies
                if self.cookies and isinstance(self.cookies, list):
                    context.add_cookies(self.cookies)
                    
                page = context.new_page()
                self._apply_stealth(page)
            
            
            try:
                # Phân loại nền tảng dựa trên tên tài khoản hoặc biến platform
                platform = self.account_data.get("platform", "tiktok").lower()
                
                if platform == "tiktok":
                    post_url = self._upload_tiktok(page, video_path, full_caption)
                elif platform == "youtube":
                    post_url = self._upload_youtube(page, video_path, full_caption)
                elif platform == "twitter":
                    post_url = self._upload_twitter(page, video_path, full_caption)
                else:
                    raise Exception(f"Nền tảng {platform} chưa được hỗ trợ.")
                    
            except Exception as e:
                # Capture screenshot khi lỗi để debug
                page.screenshot(path=os.path.join(DATA_DIR, f"error_{int(time.time())}.png"))
                raise e
            finally:
                if is_gpm:
                    browser.close()
                    import requests
                    logger.info(f"[Playwright] Đóng GPM Profile {gpm_profile_id}")
                    
                    # Try closing with API v1 first
                    closed = False
                    try:
                        url_v1 = f"{gpm_api_url}/api/v1/profiles/close/{gpm_profile_id}"
                        res = requests.get(url_v1, timeout=10)
                        if res.json().get("success"):
                            closed = True
                    except Exception:
                        pass
                        
                    # Fallback to API v2 stop
                    if not closed:
                        try:
                            url_v2 = f"{gpm_api_url}/api/v2/profile/stop?profileId={gpm_profile_id}"
                            requests.get(url_v2, timeout=10)
                        except Exception:
                            pass
                else:
                    browser.close()
                
        return post_url

    def _upload_tiktok(self, page, video_path: str, text: str) -> str:
        logger.info("[Playwright] Mở trang Tiktok Upload...")
        page.goto("https://www.tiktok.com/creator-center/upload", timeout=60000, wait_until="domcontentloaded")
        self._smart_sleep(page, 5000)
        
        # Check login
        if "login" in page.url:
            raise Exception("Tiktok báo chưa đăng nhập (Cookie hết hạn hoặc không hợp lệ).")
            
        # TIKTOK UPLOAD LOGIC 2024
        logger.info("[Playwright] Đang tìm trường Upload File Tiktok...")
        try:
            # Hỗ trợ cả trường hợp trang upload bọc trong Iframe hoặc nằm ngay ngoài
            frame = page.frame_locator('iframe[data-tt="Upload_index_iframe"]')
            file_input = frame.locator('input[type="file"][accept*="video"]')
            
            if file_input.count() == 0:
                file_input = page.locator('input[type="file"][accept*="video"]')
                
            try:
                # BYPASS 50MB LIMIT OVER CDP
                # Gán ID tạm cho element để tìm qua CDP (kể cả trong iframe)
                file_input.first.evaluate("el => el.id = 'gpm-upload-bypass'")
                client = page.context.new_cdp_session(page)
                client.send("DOM.enable")
                client.send("DOM.getDocument")
                
                # Sử dụng DOM.performSearch để tìm xuyên qua các iframe
                search_res = client.send("DOM.performSearch", {"query": "#gpm-upload-bypass"})
                results = client.send("DOM.getSearchResults", {
                    "searchId": search_res["searchId"], 
                    "fromIndex": 0, 
                    "toIndex": 1
                })
                
                if not results.get("nodeIds"):
                    raise Exception("Không tìm thấy node qua performSearch")
                    
                node_id = results["nodeIds"][0]
                
                # Truyền trực tiếp đường dẫn file nội bộ qua CDP thay vì để Playwright gửi buffer qua websocket
                client.send("DOM.setFileInputFiles", {
                    "nodeId": node_id,
                    "files": [os.path.abspath(video_path)]
                })
                logger.info(f"[Playwright] Đã upload qua CDP Bypass (không giới hạn 50MB).")
            except Exception as cdp_err:
                logger.warning(f"[Playwright] CDP bypass thất bại, fallback cách cũ: {cdp_err}")
                file_input.set_input_files(video_path)
                
        except Exception as e:
            # Fallback
            try:
                page.locator('input[type="file"]').first.evaluate("el => el.id = 'gpm-upload-bypass-fallback'")
                client = page.context.new_cdp_session(page)
                client.send("DOM.enable")
                client.send("DOM.getDocument")
                search_res = client.send("DOM.performSearch", {"query": "#gpm-upload-bypass-fallback"})
                results = client.send("DOM.getSearchResults", {
                    "searchId": search_res["searchId"], 
                    "fromIndex": 0, 
                    "toIndex": 1
                })
                client.send("DOM.setFileInputFiles", {
                    "nodeId": results["nodeIds"][0],
                    "files": [os.path.abspath(video_path)]
                })
            except Exception as fallback_err:
                logger.warning(f"[Playwright] Fallback CDP cũng thất bại, dùng API mặc định: {fallback_err}")
                page.locator('input[type="file"]').first.set_input_files(video_path)
            
        logger.info("[Playwright] Đã tải video lên, chờ hệ thống xử lý nội bộ...")
        self._smart_sleep(page, 10000)
        
        # Tiêu diệt toàn bộ popup / overlay cản đường bằng Javascript
        try:
            page.evaluate("""
                document.querySelectorAll('.TUXModal-overlay, [data-floating-ui-portal], .react-joyride__overlay, #react-joyride-portal').forEach(el => el.style.display = 'none');
            """)
        except:
            pass
        page.keyboard.press("Escape")
        
        logger.info("[Playwright] Đang nhập Caption...")
        try:
            # Tìm ô nhập caption
            caption_editor = page.locator('.public-DraftEditor-content')
            if caption_editor.count() == 0:
                frame = page.frame_locator('iframe[data-tt="Upload_index_iframe"]')
                caption_editor = frame.locator('.public-DraftEditor-content')
                
            caption_editor.click(timeout=10000)
            
            # Xóa tên file mặc định do Tiktok tự động điền vào ô caption
            page.keyboard.press("Control+A")
            self._smart_sleep(page, 200)
            page.keyboard.press("Backspace")
            self._smart_sleep(page, 500)
            
            page.keyboard.type(text, delay=30)
        except Exception as e:
            logger.warning(f"[Playwright] Bỏ qua nhập caption do không tìm thấy ô nhập: {e}")
            
        logger.info("[Playwright] Đang bấm nút Đăng (Post)...")
        try:
            # Tiêu diệt popup lần nữa trước khi bấm
            try:
                page.evaluate("""
                    document.querySelectorAll('.TUXModal-overlay, [data-floating-ui-portal], .react-joyride__overlay, #react-joyride-portal').forEach(el => el.style.display = 'none');
                """)
            except:
                pass
            
            # Chờ thêm 5 giây để nút đăng sáng lên (hết disable)
            self._smart_sleep(page, 5000)
            
            post_selector = 'button:has-text("Post"), button:has-text("Đăng"), [data-e2e="post_video_button"]'
            post_btn = page.locator(post_selector).last
            
            try:
                # Bỏ force=True để nó tự check nút có bị mờ không, nếu mờ thì đợi. Tăng timeout lên 90s cho mạng chậm.
                post_btn.click(timeout=90000)
            except Exception as e:
                logger.warning(f"[Playwright] Không click được nút Đăng ở trang chính, thử tìm trong Iframe: {e}")
                frame = page.frame_locator('iframe[data-tt="Upload_index_iframe"]')
                post_btn = frame.locator(post_selector).last
                post_btn.click(timeout=60000)
        except Exception as e:
            logger.error(f"[Playwright] Không bấm được nút Đăng: {e}")
            raise Exception(f"Không bấm được nút Đăng, có thể do mạng chậm hoặc giao diện thay đổi: {str(e)}")
            
        logger.info("[Playwright] Hoàn tất lệnh Upload Tiktok. Đợi URL trả về...")
        self._smart_sleep(page, 8000)
        
        # Thử lấy link post nếu Tiktok trả về thông báo "Video upload saved/posted"
        try:
            # Ưu tiên lấy link từ các toast hoặc modal thông báo thành công
            success_toast = page.locator('div[class*="toast"] a[href*="/video/"], div[class*="modal"] a[href*="/video/"], .tiktok-toast a[href*="/video/"]').last
            if success_toast.is_visible(timeout=5000):
                href = success_toast.get_attribute("href")
                if href and href.startswith("/"):
                    href = f"https://www.tiktok.com{href}"
                return href
            
            # Nếu không tìm thấy toast rõ ràng, đừng lấy bừa thẻ a href video trên trang (vì có thể là video cũ)
            # Trả về URL mặc định của trang Profile hoặc Upload
            final_url = "https://www.tiktok.com/profile"
        except:
            final_url = "https://www.tiktok.com/profile"
            
        # --- Lướt feed sau khi đăng để tăng độ trust ---
        try:
            num_scrolls = random.randint(2, 5)
            num_likes = random.randint(0, min(2, num_scrolls))
            num_favorites = random.randint(0, min(2, num_scrolls))
            like_indices = random.sample(range(num_scrolls), num_likes)
            fav_indices = random.sample(range(num_scrolls), num_favorites)
            
            logger.info(f"[Playwright] Chuyển về trang chủ Tiktok để lướt dạo {num_scrolls} video (thả tim {num_likes}, lưu yêu thích {num_favorites})...")
            page.goto("https://www.tiktok.com/foryou", timeout=40000, wait_until="domcontentloaded")
            self._smart_sleep(page, 5000)
            
            # Đóng popups trước khi lướt
            try:
                page.evaluate("""() => {
                    const selectors = ['[data-e2e="modal-close-inner-button"]', '[class*="DivCloseIcon"]', 'div[role="dialog"] button[aria-label="Close"]', 'button[class*="close"]', '[class*="BottomBannerClose"]'];
                    for (const sel of selectors) {
                        document.querySelectorAll(sel).forEach(btn => { try { btn.click(); } catch(e) {} });
                    }
                }""")
            except:
                pass
            
            for i in range(num_scrolls):
                logger.info(f"[Playwright] Xem video Tiktok thứ {i+1}...")
                self._smart_sleep(page, random.randint(6000, 12000))
                
                if i in like_indices:
                    logger.info(f"[Playwright] Thả tim video Tiktok thứ {i+1}...")
                    try:
                        viewport = page.viewport_size
                        if viewport:
                            center_x = viewport['width'] / 2
                            center_y = viewport['height'] / 2
                            page.mouse.dblclick(center_x, center_y)
                            self._smart_sleep(page, 1000)
                    except Exception as e:
                        logger.error(f"Lỗi khi thả tim: {str(e)}")
                        
                if i in fav_indices:
                    logger.info(f"[Playwright] Thêm yêu thích video Tiktok thứ {i+1}...")
                    try:
                        js_fav = """
                        () => {
                            const selectors = ['span[data-e2e="collect-icon"]', 'span[data-e2e="undefined-icon"]', 'span[data-e2e="favorite-icon"]', 'span[data-e2e="save-icon"]', 'span[data-e2e="bookmark-icon"]'];
                            for (let sel of selectors) {
                                const elements = document.querySelectorAll(sel);
                                for (let el of elements) {
                                    const rect = el.getBoundingClientRect();
                                    if (rect.top > 0 && rect.bottom < window.innerHeight && rect.height > 0) {
                                        el.click();
                                        return true;
                                    }
                                }
                            }
                            return false;
                        }
                        """
                        page.evaluate(js_fav)
                        self._smart_sleep(page, 1000)
                    except Exception as e:
                        logger.error(f"Lỗi khi thêm yêu thích: {str(e)}")
                        
                # Scroll to next video
                try:
                    page.evaluate("""() => {
                        const nextBtn = document.querySelector('button[data-e2e="arrow-right"], button[class*="ButtonArrowRight"], button[class*="BottomVideoNext"]');
                        if (nextBtn) { nextBtn.click(); return; }
                        
                        const containers = document.querySelectorAll('[data-e2e="recommend-list-item-container"], [class*="DivItemContainer"]');
                        if (containers && containers.length > 0) {
                            for (let i = 0; i < containers.length; i++) {
                                const rect = containers[i].getBoundingClientRect();
                                if (rect.top > (window.innerHeight * 0.4)) {
                                    containers[i].scrollIntoView({behavior: 'smooth', block: 'start'});
                                    return;
                                }
                            }
                        }
                        window.scrollBy({ top: window.innerHeight, behavior: 'smooth' });
                    }""")
                    self._smart_sleep(page, 1500)
                except Exception as e:
                    logger.error(f"Lỗi cuộn JS (dùng fallback): {e}")
                    page.keyboard.press("ArrowDown")
                    
        except Exception as surf_err:
            logger.warning(f"[Playwright] Lỗi khi lướt dạo Tiktok (bỏ qua): {surf_err}")

        return final_url
        
    def _upload_youtube(self, page, video_path: str, text: str) -> str:
        logger.info("[Playwright] Mở trang Youtube Studio...")
        page.goto("https://studio.youtube.com/", timeout=60000, wait_until="domcontentloaded")
        self._smart_sleep(page, 5000)
        
        # Check login
        if "accounts.google.com" in page.url or "v=SIGNIN" in page.url:
            raise Exception("Youtube báo chưa đăng nhập (Cookie hết hạn).")
            
        # YOUTUBE UPLOAD LOGIC
        logger.info("[Playwright] Bắt đầu luồng Upload Youtube...")
        try:
            # 1. Bấm nút Create / Tạo
            create_btn = page.locator('ytcp-icon-button[aria-label*="Create"], ytcp-icon-button[aria-label*="Tạo"]').first
            create_btn.click()
            page.locator('tp-yt-paper-item:has-text("Upload videos"), tp-yt-paper-item:has-text("Tải video lên")').click()
            
            # 2. Upload file
            self._smart_sleep(page, 2000)
            
            try:
                # BYPASS 50MB LIMIT OVER CDP
                page.locator('input[type="file"]').first.evaluate("el => el.id = 'gpm-yt-upload-bypass'")
                client = page.context.new_cdp_session(page)
                client.send("DOM.enable")
                client.send("DOM.getDocument")
                search_res = client.send("DOM.performSearch", {"query": "#gpm-yt-upload-bypass"})
                results = client.send("DOM.getSearchResults", {
                    "searchId": search_res["searchId"], 
                    "fromIndex": 0, 
                    "toIndex": 1
                })
                
                if not results.get("nodeIds"):
                    raise Exception("Không tìm thấy node qua performSearch")
                    
                client.send("DOM.setFileInputFiles", {
                    "nodeId": results["nodeIds"][0],
                    "files": [os.path.abspath(video_path)]
                })
                logger.info(f"[Playwright] Đã upload Youtube qua CDP Bypass.")
            except Exception as cdp_err:
                logger.warning(f"[Playwright] Youtube CDP bypass thất bại: {cdp_err}")
                page.locator('input[type="file"]').first.set_input_files(video_path)
            
            # 3. Nhập chi tiết (Đợi dialog hiện lên)
            self._smart_sleep(page, 8000)
            logger.info("[Playwright] Đang nhập mô tả (Description)...")
            
            desc_box = page.locator('#textbox').nth(1)
            desc_box.click()
            page.keyboard.type(text, delay=20)
            
            # 4. Chọn "No, it's not made for kids" (Bắt buộc)
            not_for_kids = page.locator('[name="VIDEO_MADE_FOR_KIDS_NOT_MFK"]')
            if not_for_kids.is_visible():
                not_for_kids.click()
            
            # 5. Next qua các bước
            for _ in range(3):
                next_btn = page.locator('#next-button')
                if next_btn.is_visible():
                    next_btn.click()
                self._smart_sleep(page, 1000)
                
            # 6. Chọn Public
            public_radio = page.locator('[name="PUBLIC"]')
            if public_radio.is_visible():
                public_radio.click()
            
            # 7. Publish
            done_btn = page.locator('#done-button')
            done_btn.click()
            
            logger.info("[Playwright] Đã gửi video Youtube, đợi link Public...")
            self._smart_sleep(page, 10000)
            
            # 8. Lấy URL (Trong hộp thoại Video Published)
            final_url = "https://studio.youtube.com/"
            video_link = page.locator('a.ytcp-video-info').first
            if video_link.is_visible():
                final_url = video_link.get_attribute("href")
                
        except Exception as e:
            logger.error(f"[Playwright] Lỗi thao tác Youtube: {e}")
            raise e
            
        # --- Lướt feed sau khi đăng để tăng độ trust ---
        try:
            num_scrolls = random.randint(2, 5)
            num_likes = random.randint(0, min(2, num_scrolls))
            like_indices = random.sample(range(num_scrolls), num_likes)
            
            logger.info(f"[Playwright] Chuyển về Youtube Shorts để lướt dạo {num_scrolls} video (thả tim {num_likes} video)...")
            page.goto("https://www.youtube.com/shorts", timeout=40000, wait_until="domcontentloaded")
            self._smart_sleep(page, 5000)
            for i in range(num_scrolls):
                logger.info(f"[Playwright] Xem video Shorts thứ {i+1}...")
                page.keyboard.press("ArrowDown")
                self._smart_sleep(page, random.randint(6000, 12000))
                
                if i in like_indices:
                    logger.info(f"[Playwright] Thả tim video Youtube thứ {i+1}...")
                    try:
                        like_btn = page.locator('#like-button button, ytd-toggle-button-renderer button').first
                        if like_btn.is_visible(timeout=2000):
                            like_btn.click(timeout=2000)
                    except:
                        pass
        except Exception as surf_err:
            logger.warning(f"[Playwright] Lỗi khi lướt dạo Youtube (bỏ qua): {surf_err}")

        return final_url

    def _upload_twitter(self, page, video_path: str, text: str) -> str:
        logger.info("[Playwright] Mở trang soạn thảo Twitter/X...")
        page.goto("https://x.com/compose/tweet", timeout=60000, wait_until="domcontentloaded")
        self._smart_sleep(page, 5000)
        
        # Check login
        if "login" in page.url or "i/flow/login" in page.url:
            raise Exception("Twitter/X báo chưa đăng nhập (Cookie hết hạn hoặc không hợp lệ).")
            
        logger.info("[Playwright] Đang tải video lên Twitter...")
        try:
            # Tìm input file (ẩn)
            file_input = page.locator('input[type="file"][accept*="video"]')
            file_input.set_input_files(video_path)
            logger.info("[Playwright] Đã đính kèm video, chờ render thanh timeline...")
            
            # Twitter cần thời gian để xử lý media. Chờ đến khi xuất hiện nút "Edit" trên video hoặc progress bar mất
            page.wait_for_selector('[aria-label="Edit video"]', timeout=90000)
            self._smart_sleep(page, 2000)
        except Exception as e:
            logger.error(f"[Playwright] Lỗi đính kèm video lên Twitter: {e}")
            raise Exception(f"Không thể tải video lên Twitter: {str(e)}")

        logger.info("[Playwright] Đang nhập nội dung Tweet...")
        try:
            # Tìm thẻ soạn thảo (contenteditable)
            tweet_editor = page.locator('[data-testid="tweetTextarea_0"]')
            tweet_editor.click()
            page.keyboard.type(text, delay=20)
        except Exception as e:
            logger.warning(f"[Playwright] Lỗi nhập nội dung: {e}")
            
        logger.info("[Playwright] Đang bấm nút Post...")
        try:
            post_btn = page.locator('[data-testid="tweetButton"]')
            post_btn.click()
            
            # Đợi toast thông báo thành công
            logger.info("[Playwright] Đợi xác nhận đăng thành công từ Twitter...")
            toast = page.locator('[data-testid="toast"]')
            toast.wait_for(state="visible", timeout=60000)
            
            # Tìm link view (Your Tweet was sent. View)
            # href thường có định dạng /username/status/123456789
            view_link = toast.locator('a[href*="/status/"]')
            final_url = "https://x.com/home"
            if view_link.is_visible(timeout=5000):
                href = view_link.get_attribute("href")
                if href:
                    final_url = f"https://x.com{href}" if href.startswith("/") else href
                    
        except Exception as e:
            logger.error(f"[Playwright] Lỗi khi bấm Đăng hoặc không bắt được Toast: {e}")
            final_url = "https://x.com/home" # Fallback

        # Lướt feed sau khi đăng
        try:
            num_scrolls = random.randint(2, 5)
            num_likes = random.randint(0, min(2, num_scrolls))
            like_indices = random.sample(range(num_scrolls), num_likes)
            
            logger.info(f"[Playwright] Lướt feed X dạo {num_scrolls} lần (thả tim {num_likes} bài)...")
            page.goto("https://x.com/home", timeout=40000, wait_until="domcontentloaded")
            self._smart_sleep(page, 3000)
            for i in range(num_scrolls):
                page.keyboard.press("PageDown")
                self._smart_sleep(page, random.randint(4000, 8000))
                
                if i in like_indices:
                    logger.info(f"[Playwright] Thả tim bài viết X lần lướt thứ {i+1}...")
                    try:
                        like_btn = page.locator('[data-testid="like"]').first
                        if like_btn.is_visible(timeout=2000):
                            like_btn.click(timeout=2000)
                    except:
                        pass
        except Exception as surf_err:
            logger.warning(f"[Playwright] Lỗi khi lướt dạo X (bỏ qua): {surf_err}")

        return final_url

    def check_status(self) -> dict:
        """Kiểm tra trạng thái (Mở Tiktok -> Lướt dạo 3-5 video -> Cập nhật thông tin kênh)."""
        logger.info(f"[Playwright] Bắt đầu quá trình Nuôi kênh & Kiểm tra trạng thái...")
        try:
            account_id = self.account_data.get('id')
            username = self.account_data.get('username')
            
            # Khởi tạo Playwright
            from playwright.sync_api import sync_playwright
            playwright = sync_playwright().start()
            
            if self.account_data.get('connection_type') == 'gpm_login':
                port = self._open_gpm_profile()
                browser = playwright.chromium.connect_over_cdp(f"http://127.0.0.1:{port}")
                context = browser.contexts[0]
                page = context.pages[0] if context.pages else context.new_page()
            else:
                browser = playwright.chromium.launch(headless=True)
                context = browser.new_context()
                if self.cookies and isinstance(self.cookies, list):
                    context.add_cookies(self.cookies)
                page = context.new_page()

            # 1. Truy cập Tiktok & Lướt dạo 3-5 video (Farming)
            page.goto("https://www.tiktok.com/foryou", timeout=40000, wait_until="domcontentloaded")
            self._smart_sleep(page, 5000)
            
            # Tắt popup nếu có
            try:
                page.evaluate("""() => {
                    const selectors = ['[data-e2e="modal-close-inner-button"]', 'div[role="dialog"] button[aria-label="Close"]', 'button[class*="close"]'];
                    selectors.forEach(sel => document.querySelectorAll(sel).forEach(btn => { try { btn.click(); } catch(e) {} }));
                }""")
            except:
                pass
                
            num_scrolls = random.randint(3, 6)
            logger.info(f"[Playwright] Lướt dạo {num_scrolls} video (Farming)...")
            for i in range(num_scrolls):
                try:
                    page.keyboard.press("ArrowDown")
                    self._smart_sleep(page, random.randint(3000, 7000))
                    # Xác suất thả tim 20%
                    if random.random() < 0.2:
                        like_btn = page.locator('[data-e2e="like-icon"]').first
                        if like_btn.is_visible(timeout=1000):
                            like_btn.click()
                except:
                    pass

            # 2. Lấy số liệu thông qua Stealth Fetch (Cào JSON ngầm)
            logger.info(f"[Playwright] Bắt đầu Stealth Fetch lấy dữ liệu cho @{username}...")
            js_fetch = f"""
            async () => {{
                try {{
                    const response = await fetch('/@{username}');
                    const html = await response.text();
                    
                    let dataStr = html.split('id="__UNIVERSAL_DATA_FOR_REHYDRATION__"')[1];
                    if (dataStr) {{
                        dataStr = dataStr.split('>')[1].split('</script>')[0];
                        const data = JSON.parse(dataStr);
                        const userModule = data.__DEFAULT_SCOPE__['webapp.user-detail'].userInfo;
                        return {{
                            followers: userModule.stats.followerCount || 0,
                            likes: userModule.stats.heartCount || 0,
                            videos: userModule.stats.videoCount || 0,
                            actual_username: userModule.user.uniqueId || null,
                            avatar: userModule.user.avatarLarger || userModule.user.avatarMedium || null
                        }};
                    }}
                    return null;
                }} catch (e) {{
                    return null;
                }}
            }}
            """
            stats = page.evaluate(js_fetch)
            
            browser.close()
            playwright.stop()
            
            # Cập nhật DB
            if account_id and stats:
                logger.info(f"[Playwright] Dữ liệu cào được: {stats}")
                from app.db.session import get_db_session
                from app.models.social_account import SocialAccount
                with get_db_session() as db:
                    acc = db.query(SocialAccount).filter(SocialAccount.id == account_id).first()
                    if acc:
                        if stats.get('actual_username') and stats.get('actual_username') != acc.username:
                            acc.username = stats.get('actual_username')
                        if stats.get('followers') is not None:
                            acc.followers_count = stats.get('followers')
                        if stats.get('likes') is not None:
                            acc.total_likes = stats.get('likes')
                        if stats.get('videos') is not None:
                            acc.videos_count = stats.get('videos')
                        if stats.get('avatar') is not None:
                            acc.avatar_url = stats.get('avatar')
                        
                        from sqlalchemy.sql import func
                        acc.last_checked_at = func.now()
                        acc.health_checked_at = func.now()
                        acc.status = 'active'
                        db.commit()
                        return {"status": "success", "message": "Nuôi kênh và kiểm tra dữ liệu thành công!"}
                        
            return {"status": "success", "message": "Nuôi kênh xong nhưng không lấy được số liệu mới."}
            
        except Exception as e:
            logger.error(f"[Playwright] Lỗi Check Status & Farming: {e}")
            return {"status": "error", "message": str(e)}
