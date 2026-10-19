import os
import random
import httpx
import string
from typing import Dict, Any, Optional, Tuple
from urllib.parse import urlencode, urlparse, parse_qs
from dotenv import load_dotenv
from app.core.security import decrypt_data
from .abogus import ABogus
from .cookie_fetcher import fetch_fresh_cookies

_USER_AGENT_POOL = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
]

class DouyinAPIClient:
    BASE_URL = "https://www.douyin.com"

    def __init__(self):
        self.user_agent = random.choice(_USER_AGENT_POOL)
        self.headers = {
            "User-Agent": self.user_agent,
            "Referer": "https://www.douyin.com/",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "vi-VN,vi;q=0.9,fr-FR;q=0.8,fr;q=0.7,en-US;q=0.6,en;q=0.5",
        }
        self.abogus_generator = ABogus(user_agent=self.user_agent)
        
        self._load_cookies_from_env()

    def _load_cookies_from_env(self):
        # Parse cookie from env (always load latest)
        env_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../data/.env"))
        load_dotenv(env_path, override=True)
        self.raw_cookie = decrypt_data(os.getenv("DOUYIN_COOKIE", "")).strip()
        self.cookies = {}
        for part in self.raw_cookie.split(";"):
            part = part.strip()
            if "=" in part:
                k, v = part.split("=", 1)
                self.cookies[k] = v
                
        # Load User-Agent from .env first
        env_ua = os.getenv("DOUYIN_USER_AGENT", "").strip()
        if env_ua:
            self.user_agent = env_ua
            self.headers["User-Agent"] = self.user_agent
            self.abogus_generator = ABogus(user_agent=self.user_agent)
        else:
            # Attempt to extract User-Agent from cookie to match browser exactly (Fallback)
            if "__druidClientInfo=" in self.raw_cookie:
                import base64
                import json
                import urllib.parse
                try:
                    for part in self.raw_cookie.split(";"):
                        part = part.strip()
                        if part.startswith("__druidClientInfo="):
                            val = urllib.parse.unquote(part.split("=", 1)[1])
                            decoded = base64.b64decode(val).decode('utf-8')
                            info = json.loads(decoded)
                            if "userAgent" in info:
                                self.user_agent = info["userAgent"]
                                self.headers["User-Agent"] = self.user_agent
                                self.abogus_generator = ABogus(user_agent=self.user_agent)
                            break
                except Exception:
                    pass

        # Generate random msToken if not exist
        if "msToken" not in self.cookies:
            random_token = ''.join(random.choices(string.ascii_letters + string.digits + "=_", k=107))
            self.cookies["msToken"] = random_token

    def refresh_cookies(self):
        """Khởi chạy Playwright để lấy cookie mới và load lại vào instance này"""
        try:
            fetch_fresh_cookies()
            self._load_cookies_from_env()
            return True
        except Exception:
            return False

    def _default_query(self) -> dict:
        return {
            "device_platform": "webapp",
            "aid": "6383",
            "channel": "channel_pc_web",
            "pc_client_type": "1",
            "version_code": "190500",
            "version_name": "19.5.0",
            "cookie_enabled": "true",
            "screen_width": "1920",
            "screen_height": "1080",
            "browser_language": "vi-VN",
            "browser_platform": "Win32",
            "browser_name": "Chrome",
            "browser_version": "124.0.0.0",
            "browser_online": "true",
            "engine_name": "Blink",
            "engine_version": "124.0.0.0",
            "os_name": "Windows",
            "os_version": "10",
            "cpu_core_num": "8",
            "device_memory": "8",
            "platform": "PC",
            "downlink": "10",
            "effective_type": "4g",
            "round_trip_time": "50",
            "msToken": self.cookies.get("msToken", ""),
        }

    def build_signed_url(self, path: str, params: dict) -> str:
        query = urlencode(params)
        _, abogus_param, ua_val, _ = self.abogus_generator.generate_abogus(query)
        base_url = f"{self.BASE_URL}{path}?{query}&a_bogus={abogus_param}"
        return base_url

    def request_json(self, path: str, params: dict, auto_retry: bool = True) -> dict:
        signed_url = self.build_signed_url(path, params)
        try:
            response = httpx.get(
                signed_url,
                headers=self.headers,
                cookies=self.cookies,
                timeout=15,
                follow_redirects=True
            )
            if response.status_code == 200:
                try:
                    data = response.json()
                    # Kiểm tra xem có bị lỗi Captcha/Anti-spam hay không (mặc dù HTTP 200)
                    if isinstance(data, dict):
                        nil_type = None
                        if "search_nil_info" in data:
                            nil_type = data["search_nil_info"].get("search_nil_type")
                        elif "search_nil_type" in data:
                            nil_type = data.get("search_nil_type")
                            
                        # Douyin đôi khi trả về mảng rỗng nếu thiếu __ac_signature
                        aweme_list = data.get("aweme_list", [])
                        
                        if nil_type in ["antispam_check", "verify_check"] or (path.endswith("/post/") and not aweme_list):
                            if auto_retry:
                                # Kích hoạt giải cứu bằng Playwright
                                if self.refresh_cookies():
                                    params["msToken"] = self.cookies.get("msToken", "")
                                    return self.request_json(path, params, auto_retry=False)
                    return data
                except Exception:
                    pass
            elif response.status_code == 403: # Bị chặn
                if auto_retry:
                    if self.refresh_cookies():
                        params["msToken"] = self.cookies.get("msToken", "")
                        return self.request_json(path, params, auto_retry=False)
        except Exception as e:
            pass
        return {}

    def resolve_short_url(self, short_url: str) -> Optional[str]:
        try:
            response = httpx.get(
                short_url,
                headers={"User-Agent": self.user_agent},
                follow_redirects=True,
                timeout=10
            )
            return str(response.url)
        except Exception:
            return None

    def extract_sec_uid(self, url: str) -> Optional[str]:
        import re
        match = re.search(r"/user/([A-Za-z0-9_-]+)", url)
        if match:
            return match.group(1)
        return None

    def extract_video_id(self, url: str) -> Optional[str]:
        import re
        match = re.search(r"/video/(\d+)", url)
        if match:
            return match.group(1)
        match = re.search(r"modal_id=(\d+)", url)
        if match:
            return match.group(1)
        return None

    def get_video_detail(self, aweme_id: str) -> dict:
        params = self._default_query()
        params.update({
            "aweme_id": aweme_id,
            "aid": "6383",
        })
        if "a_bogus" in params:
            del params["a_bogus"]
        # Thử HTTP API trước (không auto_retry vì Argus sẽ chặn trên raw HTTP)
        data = self.request_json("/aweme/v1/web/aweme/detail/", params, auto_retry=False)
        if data and data.get("aweme_detail"):
            return data

        # Fallback qua Playwright để giải mã ArgusSecurityPlugin
        try:
            from .douyin_browser_crawler import DouyinBrowserCrawler
            browser_crawler = DouyinBrowserCrawler(cookies=self.cookies, user_agent=self.user_agent)
            browser_data = browser_crawler.get_video_detail(aweme_id)
            if browser_data and browser_data.get("aweme_detail"):
                return browser_data
        except Exception:
            pass
        return {}

    def get_user_post(self, sec_uid: str, max_cursor: int = 0, count: int = 35) -> dict:
        params = self._default_query()
        params.update({
            "sec_user_id": sec_uid,
            "max_cursor": max_cursor,
            "count": count,
            "locate_query": "false",
            "show_live_replay_strategy": "1",
            "need_time_list": "1",
            "time_list_query": "0",
        })
        data = self.request_json("/aweme/v1/web/aweme/post/", params, auto_retry=False)
        if data and data.get("aweme_list"):
            return data

        # Fallback qua Playwright nếu HTTP API bị chặn
        try:
            from .douyin_browser_crawler import DouyinBrowserCrawler
            browser_crawler = DouyinBrowserCrawler(cookies=self.cookies, user_agent=self.user_agent)
            _, videos = browser_crawler.get_profile_and_posts(sec_uid, max_videos=count)
            if videos:
                return {
                    "aweme_list": videos,
                    "has_more": False,
                    "max_cursor": 0
                }
        except Exception:
            pass
        return {}

    def get_user_profile(self, sec_uid: str) -> dict:
        """Fetch detailed Douyin user profile using sec_uid."""
        params = self._default_query()
        params.update({
            "sec_user_id": sec_uid,
            "publish_video_strategy_type": "2",
            "personal_center_strategy": "1",
        })
        data = self.request_json("/aweme/v1/web/user/profile/other/", params, auto_retry=False)
        if data and data.get("user"):
            return data

        # Fallback qua Playwright nếu HTTP API bị chặn
        try:
            from .douyin_browser_crawler import DouyinBrowserCrawler
            browser_crawler = DouyinBrowserCrawler(cookies=self.cookies, user_agent=self.user_agent)
            profile_data, _ = browser_crawler.get_profile_and_posts(sec_uid, max_videos=1)
            if profile_data:
                return {"user": profile_data}
        except Exception:
            pass
        return {}

    def get_hot_search_board(self) -> dict:
        """Lấy danh sách bảng xếp hạng từ khóa hot trend của Douyin"""
        params = self._default_query()
        params.update({"detail_list": "1", "source": "6"})
        
        raw = self.request_json("/aweme/v1/web/hot/search/list/", params)
        if not raw:
            return {"items": []}
            
        data_root = raw.get("data", {}) if isinstance(raw.get("data"), dict) else raw
        word_list = data_root.get("word_list", [])
        return {
            "items": word_list if isinstance(word_list, list) else [],
            "raw": raw
        }

    def search_aweme(self, keyword: str, offset: int = 0, count: int = 10, auto_retry: bool = True) -> dict:
        """Tìm kiếm video theo từ khóa"""
        old_referer = self.headers.get("Referer", "https://www.douyin.com/")
        import urllib.parse
        encoded_kw = urllib.parse.quote(keyword)
        self.headers["Referer"] = f"https://www.douyin.com/search/{encoded_kw}"
        
        try:
            params = self._default_query()
            params.update({
                "keyword": keyword,
                "search_channel": "aweme_video_web",
                "sort_type": 0,
                "publish_time": 0,
                "search_source": "normal_search",
                "query_correct_type": "1",
                "is_filter_search": 0,
                "offset": offset,
                "count": count,
            })
            
            raw = self.request_json("/aweme/v1/web/general/search/single/", params)
            if not raw:
                if auto_retry:
                    from app.core.logger import get_logger
                    logger = get_logger(__name__)
                    logger.info("Không có phản hồi từ API tìm kiếm Douyin, tiến hành refresh cookie...")
                    if self.refresh_cookies():
                        params["msToken"] = self.cookies.get("msToken", "")
                        self.headers["Referer"] = old_referer
                        return self.search_aweme(keyword, offset, count, auto_retry=False)
                self.headers["Referer"] = old_referer
                return {"items": [], "has_more": False, "max_cursor": 0}
                
            data_list = raw.get("data", []) if isinstance(raw.get("data"), list) else []
            items = []
            for entry in data_list:
                if isinstance(entry, dict) and "aweme_info" in entry:
                    items.append(entry["aweme_info"])
                    
            has_more = bool(raw.get("has_more", 0))
            next_offset = int(raw.get("cursor") or raw.get("offset") or 0)
            status_code = int(raw.get("status_code") or 0)
            
            # Kiểm tra nếu bị chặn do thiếu cookie signature hoặc chưa đăng nhập
            if status_code != 0 or not items:
                status_msg = raw.get("status_msg", "")
                if status_code == 2483 or "登录" in status_msg:
                    error_msg = "Tìm kiếm Hot Trend yêu cầu tài khoản Douyin đã đăng nhập. Vui lòng vào trang Cấu hình để cập nhật Cookie chứa 'sessionid' thủ công!"
                    raise Exception(error_msg)

                if auto_retry:
                    from app.core.logger import get_logger
                    logger = get_logger(__name__)
                    logger.info("Tìm kiếm Douyin bị chặn hoặc không có kết quả, tiến hành lấy cookie mới...")
                    if self.refresh_cookies():
                        params["msToken"] = self.cookies.get("msToken", "")
                        self.headers["Referer"] = old_referer
                        return self.search_aweme(keyword, offset, count, auto_retry=False)
                
                error_msg = "Không tìm thấy kết quả hoặc API bị chặn."
                if "search_nil_info" in raw:
                    nil_type = raw["search_nil_info"].get("search_nil_type")
                    if nil_type == "antispam_check":
                        error_msg = "Tìm kiếm bị Douyin chặn (Anti-Spam). Yêu cầu cập nhật Cookie chứa '__ac_signature' từ trình duyệt!"
                    elif nil_type == "verify_check":
                        error_msg = "Tài khoản/IP yêu cầu xác minh Captcha. Vui lòng mở lại trình duyệt Douyin, tìm kiếm và giải Captcha rồi copy lại Cookie mới."
                elif "search_nil_type" in raw:
                    nil_type = raw.get("search_nil_type")
                    if nil_type == "antispam_check":
                        error_msg = "Tìm kiếm bị Douyin chặn (Anti-Spam). Yêu cầu cập nhật Cookie chứa '__ac_signature' từ trình duyệt!"
                    elif nil_type == "verify_check":
                        error_msg = "Tài khoản/IP yêu cầu xác minh Captcha. Vui lòng mở lại trình duyệt Douyin, tìm kiếm và giải Captcha rồi copy lại Cookie mới."
                raise Exception(error_msg)

            self.headers["Referer"] = old_referer
            return {
                "items": items,
                "has_more": has_more,
                "max_cursor": next_offset,
                "status_code": status_code,
                "raw": raw,
            }
        except Exception as e:
            self.headers["Referer"] = old_referer
            raise e
