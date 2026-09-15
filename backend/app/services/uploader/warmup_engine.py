import logging
import time
import random
import os
import requests
from typing import Dict, Any
from app.core.logger import get_logger

logger = get_logger(__name__)


class BaseWarmupEngine:
    def __init__(self, account_data: Dict[str, Any]):
        self.account_data = account_data
        
    def warmup(self):
        raise NotImplementedError

class GpmWarmupEngine(BaseWarmupEngine):
    def warmup(self):
        from playwright.sync_api import sync_playwright
        
        # Load environment variables from .env to ensure we get the latest GPM_API_URL
        from dotenv import load_dotenv
        ENV_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../data/.env"))
        load_dotenv(ENV_PATH, override=True)

        # 1. Start GPM Profile
        gpm_api_url = os.getenv("GPM_API_URL", "").rstrip('/')
        profile_id = self.account_data.get("device_id")
        
        if not gpm_api_url or not profile_id:
            raise Exception("GPM API URL hoặc Profile ID không hợp lệ.")
            
        logger.info(f"[Warmup-GPM] Đang khởi động GPM Profile: {profile_id}")
        
        ws_endpoint = None
        # Try GPM API v1 first (newer GPMLogin Global versions)
        try:
            url_v1 = f"{gpm_api_url}/api/v1/profiles/start/{profile_id}"
            start_res = requests.get(url_v1, timeout=15)
            start_data = start_res.json()
            if isinstance(start_data, dict):
                if start_data.get("success") and start_data.get("data"):
                    ws_endpoint = start_data["data"].get("websocket_debugging_url") or start_data["data"].get("ws_endpoint")
            else:
                logger.warning(f"[Warmup-GPM] API v1 trả về dữ liệu không đúng định dạng (có thể là lỗi): {start_data}")
        except Exception as e:
            logger.warning(f"[Warmup-GPM] Thử GPM API v1 thất bại: {e}")
            
        # Fallback to GPM API v2 (older GPM versions)
        if not ws_endpoint:
            try:
                url_v2 = f"{gpm_api_url}/api/v2/profile/start?profileId={profile_id}"
                start_res = requests.get(url_v2, timeout=15)
                start_data = start_res.json()
                if isinstance(start_data, dict):
                    if start_data.get("success") and start_data.get("data"):
                        ws_endpoint = start_data["data"].get("ws_endpoint") or start_data["data"].get("websocket_debugging_url")
                else:
                    logger.warning(f"[Warmup-GPM] API v2 trả về dữ liệu không đúng định dạng (có thể là lỗi): {start_data}")
            except Exception as e:
                logger.warning(f"[Warmup-GPM] Thử GPM API v2 thất bại: {e}")
                
        if not ws_endpoint:
            raise Exception(f"Không thể mở GPM Profile qua cả API v1 và v2 cho Profile ID: {profile_id}")
            
        from urllib.parse import urlparse
        parsed_api = urlparse(gpm_api_url)
        api_host = parsed_api.hostname
        if api_host:
            ws_endpoint = ws_endpoint.replace("127.0.0.1", api_host).replace("localhost", api_host)
            
        logger.info(f"[Warmup-GPM] Kết nối qua CDP: {ws_endpoint}")
        
        with sync_playwright() as p:
            browser = p.chromium.connect_over_cdp(ws_endpoint)
            # Find an existing page or create a new one
            if browser.contexts and browser.contexts[0].pages:
                page = browser.contexts[0].pages[0]
            else:
                context = browser.contexts[0] if browser.contexts else browser.new_context()
                page = context.new_page()
                
            try:
                platform = self.account_data.get("platform", "tiktok").lower()
                if platform == "tiktok":
                    self._warmup_tiktok(page)
                else:
                    logger.warning(f"Chưa hỗ trợ nuôi nền tảng {platform}")
            finally:
                # QUAN TRỌNG: Dùng disconnect() thay vì close() để không đóng trình duyệt GPM
                try:
                    browser.close()
                except Exception:
                    pass
                
                # Stop profile after warmup
                logger.info(f"[Warmup-GPM] Đóng GPM Profile: {profile_id}")
                
                # Try closing with API v1 first
                closed = False
                try:
                    url_v1 = f"{gpm_api_url}/api/v1/profiles/close/{profile_id}"
                    res = requests.get(url_v1, timeout=10)
                    if res.json().get("success"):
                        closed = True
                except Exception:
                    pass
                    
                # Fallback to API v2 stop
                if not closed:
                    try:
                        url_v2 = f"{gpm_api_url}/api/v2/profile/stop?profileId={profile_id}"
                        requests.get(url_v2, timeout=10)
                    except Exception:
                        pass

    def _warmup_tiktok(self, page):
        logger.info("[Warmup-GPM] Mở tiktok.com/foryou")
        
        # Dùng wait_until='domcontentloaded' để tránh bị treo chờ TikTok load hết tài nguyên
        try:
            page.goto("https://www.tiktok.com/foryou", timeout=60000, wait_until="domcontentloaded")
        except Exception as e:
            logger.warning(f"[Warmup-GPM] page.goto gặp lỗi (vẫn tiếp tục): {e}")
        
        # Đợi trang ổn định
        time.sleep(8)
        
        # Log URL hiện tại để debug
        try:
            current_url = page.url
            logger.info(f"[Warmup-GPM] URL hiện tại: {current_url}")
        except Exception:
            pass
        
        # Đóng tất cả các popup phổ biến trên TikTok
        self._dismiss_popups(page)
        time.sleep(2)
        
        # Xác nhận trang đã thực sự sẵn sàng (có video element)
        try:
            page.wait_for_selector("video", timeout=15000)
            logger.info("[Warmup-GPM] Đã phát hiện video element, trang sẵn sàng lướt!")
        except Exception:
            logger.warning("[Warmup-GPM] Không tìm thấy video element nhưng vẫn tiếp tục lướt...")
        
        # Lấy thời lượng nuôi từ account_data hoặc mặc định 10-15 phút
        warmup_duration = self.account_data.get("warmup_duration", random.randint(600, 900))
        end_time = time.time() + warmup_duration
        
        videos_watched = 0
        likes_given = 0
        favorites_given = 0
        
        # Khởi tạo Redis để kiểm tra cờ dừng
        try:
            from app.core.redis_pool import get_sync_redis
            r = get_sync_redis()
            account_id = self.account_data.get("id")
        except Exception:
            r = None
            account_id = None
        
        logger.info(f"[Warmup-GPM] Bắt đầu lướt dạo (Kéo dài {warmup_duration}s)...")
        while time.time() < end_time:
            # Kiểm tra xem có lệnh dừng không
            if r and account_id:
                try:
                    if r.get(f"warmup_stop:{account_id}"):
                        logger.info("[Warmup-GPM] Nhận được tín hiệu dừng nuôi từ hệ thống.")
                        r.delete(f"warmup_stop:{account_id}")
                        break
                except Exception:
                    pass

            # Ngẫu nhiên dừng lại xem video từ 10s đến 45s (kiểm tra ngắt nhịp mỗi 0.5s)
            watch_time = random.randint(10, 45)
            logger.info(f"[Warmup-GPM] Đang xem video {videos_watched + 1} trong {watch_time}s...")
            stopped_early = False
            elapsed_w = 0.0
            while elapsed_w < watch_time:
                if r and account_id and r.get(f"warmup_stop:{account_id}"):
                    logger.info("[Warmup-GPM] Nhận được tín hiệu dừng nuôi từ hệ thống.")
                    r.delete(f"warmup_stop:{account_id}")
                    stopped_early = True
                    break
                time.sleep(0.5)
                elapsed_w += 0.5

            if stopped_early:
                break
            
            # Ngẫu nhiên thả tim (Tỷ lệ 15%) bằng double-click
            if random.random() < 0.15:
                try:
                    viewport = page.viewport_size
                    if viewport:
                        center_x = viewport['width'] / 2
                        center_y = viewport['height'] / 2
                        page.mouse.dblclick(center_x, center_y)
                        likes_given += 1
                        logger.info(f"[Warmup-GPM] Đã thả tim video! (Tổng: {likes_given})")
                        time.sleep(1)
                except Exception as e:
                    logger.warning(f"[Warmup-GPM] Lỗi khi thả tim: {e}")
                    
            # Ngẫu nhiên yêu thích (Lưu video) (Tỷ lệ 10%)
            if random.random() < 0.10:
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
                    success = page.evaluate(js_fav)
                    if success:
                        favorites_given += 1
                        logger.info(f"[Warmup-GPM] Đã thêm video vào Yêu thích! (Tổng: {favorites_given})")
                        time.sleep(1)
                except Exception as e:
                    logger.warning(f"[Warmup-GPM] Lỗi khi yêu thích video: {e}")
            
            # ============ CUỘN XUỐNG VIDEO TIẾP THEO ============
            scrolled = self._scroll_to_next_video(page)
            if scrolled:
                logger.info(f"[Warmup-GPM] Đã cuộn sang video tiếp theo thành công!")
            else:
                logger.warning(f"[Warmup-GPM] Cuộn video có thể không thành công, thử lại...")
                # Thử lại 1 lần nữa sau khi đóng popup
                self._dismiss_popups(page)
                time.sleep(1)
                self._scroll_to_next_video(page)
                
            videos_watched += 1
            
        logger.info(f"[Warmup-GPM] Hoàn tất phiên nuôi! Đã lướt {videos_watched} video, thả {likes_given} tim, yêu thích {favorites_given} video.")
    
    def _dismiss_popups(self, page):
        """Đóng tất cả popup/modal trên TikTok Web"""
        try:
            page.evaluate("""() => {
                try {
                    // Đóng popup đăng nhập, banner, modal
                    const selectors = [
                        '[data-e2e="modal-close-inner-button"]',
                        '[class*="DivCloseIcon"]',
                        'div[role="dialog"] button[aria-label="Close"]',
                        'button[class*="close"]',
                        '[class*="BottomBannerClose"]',
                        '[class*="ModalClose"]',
                        'div[id*="loginContainer"] [class*="close"]'
                    ];
                    for (const sel of selectors) {
                        document.querySelectorAll(sel).forEach(btn => {
                            try { btn.click(); } catch(e) {}
                        });
                    }
                    // Chấp nhận cookies nếu có
                    const acceptBtn = document.querySelector('button[class*="cookie" i], button[class*="accept" i]');
                    if (acceptBtn) acceptBtn.click();
                } catch(e) {}
            }""")
        except Exception:
            pass
    
    def _scroll_to_next_video(self, page):
        """Cuộn sang video tiếp theo bằng nhiều chiến lược JavaScript trực tiếp trên DOM"""
        try:
            result = page.evaluate("""() => {
                // Chiến lược 1: Tìm nút 'Tiếp theo' của giao diện xem (thường dùng khi bấm vào chi tiết video)
                const nextBtn = document.querySelector('button[data-e2e="arrow-right"], button[class*="ButtonArrowRight"], button[class*="BottomVideoNext"]');
                if (nextBtn) {
                    nextBtn.click();
                    return 'button_click';
                }
                
                // Chiến lược 2: Tìm video container tiếp theo và dùng scrollIntoView() - Chiến lược đáng tin cậy nhất
                const containers = document.querySelectorAll('[data-e2e="recommend-list-item-container"], [class*="DivItemContainer"]');
                if (containers && containers.length > 0) {
                    for (let i = 0; i < containers.length; i++) {
                        const rect = containers[i].getBoundingClientRect();
                        // Video đang xem sẽ có rect.top gần 0. Video tiếp theo sẽ nằm phía dưới màn hình
                        if (rect.top > (window.innerHeight * 0.4)) {
                            containers[i].scrollIntoView({behavior: 'smooth', block: 'start'});
                            return 'scroll_into_view';
                        }
                    }
                }
                
                // Chiến lược 3: Tìm scroll container của TikTok và cuộn nó
                const scrollContainers = [
                    document.querySelector('[class*="DivVideoFeedV2"]'),
                    document.querySelector('#app > div > div:nth-child(2)'),
                    document.querySelector('main'),
                    document.querySelector('[class*="VideoFeed"]'),
                    document.querySelector('[class*="DivContentContainer"]')
                ];
                
                for (const container of scrollContainers) {
                    if (container && container.scrollHeight > container.clientHeight) {
                        container.scrollBy({ top: container.clientHeight, behavior: 'smooth' });
                        return 'container_scroll';
                    }
                }
                
                // Chiến lược 4: Scroll toàn bộ trang (window) bằng chiều cao viewport
                window.scrollBy({ top: window.innerHeight, behavior: 'smooth' });
                return 'window_scroll';
            }""")
            
            time.sleep(1.5)  # Chờ animation scroll-snap hoàn tất
            
            logger.info(f"[Warmup-GPM] Phương pháp cuộn: {result}")
            return True
            
        except Exception as e:
            logger.warning(f"[Warmup-GPM] Lỗi khi cuộn video bằng JS: {e}")
            
            # Fallback cuối cùng: dùng Playwright keyboard
            try:
                page.keyboard.press("ArrowDown")
                time.sleep(1)
                return True
            except Exception:
                return False

class AdbWarmupEngine(BaseWarmupEngine):
    def warmup(self):
        import subprocess
        device_id = self.account_data.get("device_id")
        if not device_id:
            raise Exception("Thiếu Device ID cho ADB.")
            
        if ":" in device_id:
            logger.info(f"[Warmup-ADB] Đang connect tới {device_id}...")
            subprocess.run(f"adb connect {device_id}", shell=True, capture_output=True)
            
        # Kiểm tra thiết bị có thực sự online không
        devices = subprocess.run(["adb", "devices"], capture_output=True, text=True, encoding='utf-8', errors='replace').stdout
        is_online = False
        for line in devices.splitlines():
            if device_id in line and "device" in line and "offline" not in line and "unauthorized" not in line:
                is_online = True
                break
        
        if not is_online:
            raise Exception(f"Thiết bị {device_id} đang offline hoặc chưa kết nối ADB. Không thể nuôi tài khoản.")
            
        account_id = self.account_data.get("id")
        try:
            from app.core.redis_pool import get_sync_redis
            r = get_sync_redis(decode_responses=True)
        except Exception:
            r = None

        def _check_adb_stop() -> bool:
            if r and account_id:
                try:
                    if r.get(f"warmup_stop:{account_id}") in ("1", b"1", 1):
                        logger.info(f"[Warmup-ADB] Nhận được tín hiệu dừng nuôi từ hệ thống cho account #{account_id}.")
                        r.delete(f"warmup_stop:{account_id}")
                        subprocess.run(f"adb -s {device_id} shell input keyevent 3", shell=True)
                        return True
                except Exception:
                    pass
            return False

        if _check_adb_stop():
            logger.info("[Warmup-ADB] Đã có cờ dừng nuôi từ trước. Hủy tác vụ ngay lập tức.")
            return

        adb_cmd = ["adb", "-s", device_id]
        
        logger.info(f"[Warmup-ADB] Khởi động Tiktok trên thiết bị {device_id}")
        # Mở app Tiktok (Thử lần lượt các phiên bản Quốc tế, Châu Á, Douyin)
        packages = ["com.zhiliaoapp.musically", "com.ss.android.ugc.trill", "com.ss.android.ugc.aweme"]
        app_launched = False
        
        launched_pkg = None
        for pkg in packages:
            if _check_adb_stop():
                return
            res = subprocess.run(adb_cmd + ["shell", "monkey", "-p", pkg, "-c", "android.intent.category.LAUNCHER", "1"], capture_output=True, text=True, encoding='utf-8', errors='replace')
            output = res.stdout + res.stderr
            if "No activities found to run" not in output and "error:" not in output and "device offline" not in output and "not found" not in output:
                logger.info(f"[Warmup-ADB] Đã gửi lệnh khởi chạy package {pkg}")
                app_launched = True
                launched_pkg = pkg
                break
                
        if not app_launched:
            raise Exception("Lỗi: Không thể khởi chạy Tiktok (Chưa cài đặt app, sai IP hoặc bị HĐH chặn lệnh monkey).")
            
        # Đợi app load với khả năng ngắt quãng
        for _ in range(20):
            if _check_adb_stop():
                return
            time.sleep(0.5)
        
        # Xác minh app có thực sự đang mở trên màn hình hay không
        try:
            if _check_adb_stop():
                return
            from app.services.uploader.adb_automator import ADBAutomator
            automator = ADBAutomator(device_id)
            target_pkgs = [launched_pkg] if launched_pkg else packages
            if not automator.wait_for_app_foreground(target_pkgs, timeout=60):
                raise Exception("Lỗi: Tiktok tải quá chậm, bị treo, hoặc lệnh monkey bị HĐH chặn (Cần bật Gỡ lỗi USB bảo mật).")
            time.sleep(5) # Chờ 5s cho UI ổn định và tải xong video đầu tiên
        except Exception as e:
            if "Tiktok tải quá chậm" in str(e) or "bị HĐH chặn" in str(e):
                raise e
            logger.warning(f"[Warmup-ADB] Không thể xác minh giao diện Tiktok nhưng vẫn tiếp tục: {e}")
        
        
        warmup_duration = self.account_data.get("warmup_duration", random.randint(600, 900))
        end_time = time.time() + warmup_duration
        
        videos_watched = 0
        likes_given = 0
        
        adb_cmd_str = f"adb -s {device_id}"
        
        # Tính toán kích thước màn hình động để vuốt cho chuẩn xác
        res_wm = subprocess.run(f"{adb_cmd_str} shell wm size", shell=True, capture_output=True, text=True, encoding='utf-8', errors='replace')
        width, height = 720, 1280
        if "Physical size:" in res_wm.stdout:
            size_str = res_wm.stdout.split("Physical size:")[1].strip()
            try:
                w, h = size_str.split("x")
                width = int(w)
                height = int(h)
            except:
                pass
        
        logger.info(f"[Warmup-ADB] Kích thước màn hình: {width}x{height}")

        while time.time() < end_time:
            if _check_adb_stop():
                logger.info("[Warmup-ADB] Dừng tiến trình nuôi tài khoản theo lệnh của người dùng.")
                break

            watch_time = random.randint(10, 20)
            logger.info(f"[Warmup-ADB] Đang xem video {videos_watched + 1} trong {watch_time}s...")
            
            # Kiểm tra cờ dừng ngắt nhịp mỗi 0.5s thay vì ngủ liền 20s
            stopped_early = False
            elapsed_w = 0.0
            while elapsed_w < watch_time:
                if _check_adb_stop():
                    logger.info("[Warmup-ADB] Dừng tiến trình nuôi tài khoản theo lệnh của người dùng.")
                    stopped_early = True
                    break
                time.sleep(0.5)
                elapsed_w += 0.5

            if stopped_early:
                break
            
            if _check_adb_stop():
                break

            # Tỷ lệ thả tim 15%
            if random.random() < 0.15:
                logger.info(f"[Warmup-ADB] Tìm và bấm thả tim video...")
                # Tìm nút thả tim bằng chữ 'Thích' hoặc 'Like' (content-desc)
                try:
                    from app.services.uploader.adb_automator import ADBAutomator
                    automator = ADBAutomator(device_id)
                    if automator.click_element(content_descs=['Thích', 'Like']):
                        logger.info("[Warmup-ADB] ĐÃ TÌM THẤY VÀ BẤM NÚT TIM THÀNH CÔNG!")
                        likes_given += 1
                        time.sleep(1)
                    else:
                        logger.info("[Warmup-ADB] KHÔNG TÌM THẤY NÚT TIM! (Livestream/Ad). BỎ QUA.")
                except Exception as e:
                    logger.error(f"[Warmup-ADB] Lỗi khi cố gắng thả tim: {e}")
                    
            if _check_adb_stop():
                break

            # Tỷ lệ yêu thích 15%
            if random.random() < 0.15:
                logger.info(f"[Warmup-ADB] Tìm và bấm yêu thích video...")
                try:
                    from app.services.uploader.adb_automator import ADBAutomator
                    automator = ADBAutomator(device_id)
                    if automator.click_element(content_descs=['Thêm vào mục Yêu thích', 'Add to Favorites', 'Lưu', 'Save']):
                        logger.info("[Warmup-ADB] ĐÃ THÊM YÊU THÍCH THÀNH CÔNG!")
                        time.sleep(1)
                    else:
                        logger.info("[Warmup-ADB] KHÔNG TÌM THẤY NÚT YÊU THÍCH! BỎ QUA.")
                except Exception as e:
                    logger.error(f"[Warmup-ADB] Lỗi khi cố gắng thêm yêu thích: {e}")
                
            # Lấy lại kích thước màn hình cho swipe nếu chưa lấy
            if 'width' not in locals():
                width, height = 720, 1280
            
            # Swipe lên video tiếp (Vuốt từ y=80% lên y=20%)
            start_x = int(width * 0.5)
            start_y = int(height * 0.8)
            end_x = int(width * 0.5)
            end_y = int(height * 0.2)
            swipe_res = subprocess.run(f"{adb_cmd_str} shell input swipe {start_x} {start_y} {end_x} {end_y} 300", shell=True, capture_output=True, text=True, encoding='utf-8', errors='replace')
            
            # Nếu thiết bị đột ngột bị ngắt kết nối giữa chừng
            if "device offline" in swipe_res.stdout or "not found" in swipe_res.stdout or "device offline" in swipe_res.stderr or "not found" in swipe_res.stderr:
                raise Exception(f"Thiết bị {device_id} đã bị ngắt kết nối giữa quá trình nuôi tài khoản.")
                
            videos_watched += 1
            
        logger.info(f"[Warmup-ADB] Hoàn tất phiên nuôi! Đã lướt {videos_watched} video, thả {likes_given} tim.")
        # Về màn hình chính hoặc tắt màn
        subprocess.run(f"{adb_cmd_str} shell input keyevent 3", shell=True)

class WarmupEngineFactory:
    @staticmethod
    def get_engine(account_data: Dict[str, Any]) -> BaseWarmupEngine:
        connection_type = account_data.get("connection_type")
        if connection_type == "gpm_login":
            return GpmWarmupEngine(account_data)
        elif connection_type == "adb_device":
            return AdbWarmupEngine(account_data)
        else:
            raise ValueError(f"Không hỗ trợ nuôi tài khoản cho loại kết nối: {connection_type}")
