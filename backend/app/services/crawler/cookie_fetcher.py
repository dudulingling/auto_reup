import os
import time
import json
import urllib.parse
import base64
import threading
from playwright.sync_api import sync_playwright
from app.core.logger import get_logger
from app.core.security import encrypt_data

logger = get_logger(__name__)

_env_file_lock = threading.Lock()
_playwright_lock = threading.Lock()

def update_env_file(cookie_str: str, user_agent: str = None):
    """Cập nhật hoặc thêm biến DOUYIN_COOKIE và DOUYIN_USER_AGENT vào file .env"""
    env_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../data/.env"))
    
    with _env_file_lock:
        # Đọc file hiện tại
        env_lines = []
        old_cookie_encrypted = ""
        if os.path.exists(env_path):
            with open(env_path, 'r', encoding='utf-8') as f:
                env_lines = f.readlines()
                
        # Tìm cookie cũ để gộp
        for line in env_lines:
            if line.startswith("DOUYIN_COOKIE="):
                old_cookie_encrypted = line.split("=", 1)[1].strip()
                break
                
        cookie_dict = {}
        old_login_cookies = {}
        if old_cookie_encrypted:
            try:
                # Giải mã cookie cũ
                from app.core.security import decrypt_data
                old_cookie_str = decrypt_data(old_cookie_encrypted).strip()
                login_keys = {"sessionid", "sessionid_ss", "sid_guard", "uid_tt", "uid_tt_ss", "sid_tt", "passport_csrf_token", "passport_csrf_token_default"}
                for part in old_cookie_str.split(";"):
                    part = part.strip()
                    if "=" in part:
                        k, v = part.split("=", 1)
                        cookie_dict[k] = v
                        if k in login_keys and v:
                            old_login_cookies[k] = v
            except Exception as decrypt_err:
                logger.error(f"Lỗi giải mã cookie cũ khi gộp: {decrypt_err}")

        # Parse cookie mới lấy từ Playwright và ghi đè/bổ sung vào dict
        for part in cookie_str.split(";"):
            part = part.strip()
            if "=" in part:
                k, v = part.split("=", 1)
                cookie_dict[k] = v

        # Bảo vệ và khôi phục cookie đăng nhập nếu cookie mới từ Playwright là phiên khách (chưa đăng nhập)
        for k, v in old_login_cookies.items():
            if not cookie_dict.get(k):
                cookie_dict[k] = v

        # Dựng lại cookie string đã gộp
        merged_cookie_str = "; ".join([f"{k}={v}" for k, v in cookie_dict.items()])
        
        # Xử lý cập nhật
        encrypted_cookie = encrypt_data(merged_cookie_str)
        new_env_lines = []
        updated_cookie = False
        updated_ua = False
        
        for line in env_lines:
            if line.startswith("DOUYIN_COOKIE="):
                new_env_lines.append(f"DOUYIN_COOKIE={encrypted_cookie}\n")
                updated_cookie = True
            elif user_agent and line.startswith("DOUYIN_USER_AGENT="):
                new_env_lines.append(f"DOUYIN_USER_AGENT={user_agent}\n")
                updated_ua = True
            else:
                new_env_lines.append(line)
                
        if not updated_cookie:
            if new_env_lines and not new_env_lines[-1].endswith('\n'):
                new_env_lines.append('\n')
            new_env_lines.append(f"DOUYIN_COOKIE={encrypted_cookie}\n")
            
        if user_agent and not updated_ua:
            new_env_lines.append(f"DOUYIN_USER_AGENT={user_agent}\n")
            
        with open(env_path, 'w', encoding='utf-8') as f:
            f.writelines(new_env_lines)
        
        logger.info("Đã gộp và lưu cookie mới cùng User-Agent vào file data/.env")

def fetch_fresh_cookies() -> str:
    """Mở trình duyệt ngầm để lấy Cookie mới từ Douyin"""
    # Tránh việc mở nhiều trình duyệt Chromium cùng lúc nếu bị lỗi hàng loạt
    if not _playwright_lock.acquire(blocking=False):
        logger.info("Một luồng khác đang lấy Cookie, đợi luồng đó hoàn thành...")
        _playwright_lock.acquire(blocking=True) # Đợi luồng kia xong
        _playwright_lock.release()
        logger.info("Luồng khác đã lấy Cookie xong, tái sử dụng.")
        return "" # Trả về rỗng để báo hiệu đã được cập nhật bởi luồng khác
        
    try:
        logger.info("Bắt đầu tiến trình Playwright lấy Cookie Douyin mới...")
        
        selected_ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        
        cookie_str_container = [""]
        
        def worker():
            try:
                with sync_playwright() as p:
                    # Khởi chạy trình duyệt chromium
                    browser = p.chromium.launch(headless=True, args=["--disable-blink-features=AutomationControlled"])
                    context = browser.new_context(
                        user_agent=selected_ua,
                        viewport={"width": 1920, "height": 1080}
                    )
                    
                    # Thêm script chống phát hiện
                    context.add_init_script("""
                        Object.defineProperty(navigator, 'webdriver', {
                          get: () => undefined
                        })
                    """)
                    
                    page = context.new_page()
                    
                    # Điều hướng tới trang chủ douyin
                    logger.info("Đang truy cập https://www.douyin.com ...")
                    try:
                        page.goto("https://www.douyin.com", wait_until="domcontentloaded", timeout=25000)
                        # Giả lập tương tác cuộn trang nhẹ để sinh ra các cookie chống bot
                        page.evaluate("window.scrollTo(0, 300)")
                        time.sleep(2)
                        page.evaluate("window.scrollTo(0, 600)")
                    except Exception as goto_err:
                        logger.warning(f"Cảnh báo khi goto Douyin (bỏ qua để cố lấy cookie): {goto_err}")
                    
                    # Đợi thêm một chút để các API ngầm chạy xong và sinh ra các cookie signature
                    time.sleep(6)
                    
                    # Cố gắng lấy danh sách cookies
                    cookies = context.cookies()
                    cookie_dict = {}
                    for c in cookies:
                        cookie_dict[c["name"]] = c["value"]
                    
                    logger.info(f"Danh sách Key Cookie thu thập được: {list(cookie_dict.keys())}")
                        
                    # Đảm bảo có một số cookie thiết yếu
                    if "ttwid" not in cookie_dict:
                        logger.warning("Không tìm thấy ttwid trong lần thử đầu tiên, đợi thêm 5s...")
                        try:
                            page.reload(wait_until="domcontentloaded", timeout=20000)
                        except Exception as reload_err:
                            logger.warning(f"Cảnh báo khi reload Douyin: {reload_err}")
                        time.sleep(3)
                        cookies = context.cookies()
                        for c in cookies:
                            cookie_dict[c["name"]] = c["value"]
                            
                    # Dựng lại cookie string
                    cookie_str = "; ".join([f"{k}={v}" for k, v in cookie_dict.items()])
                    
                    browser.close()
                    
                    if cookie_str:
                        logger.info("Lấy cookie qua Playwright thành công.")
                        update_env_file(cookie_str, selected_ua)
                        cookie_str_container[0] = cookie_str
                    else:
                        logger.error("Không thể lấy cookie nào từ trình duyệt.")
                        
            except Exception as e:
                logger.error(f"Lỗi khi chạy Playwright trong thread: {str(e)}", exc_info=True)
    
        # Chạy playwright trong một thread riêng biệt để tránh lỗi asyncio loop của FastAPI
        thread = threading.Thread(target=worker)
        thread.start()
        thread.join()
        
        return cookie_str_container[0]
    finally:
        _playwright_lock.release()
