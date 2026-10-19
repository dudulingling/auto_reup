import sys
import os
import time
import threading
from typing import Dict, Any, List, Optional, Tuple
from playwright.sync_api import sync_playwright

from app.core.logger import get_logger

logger = get_logger(__name__)


class DouyinBrowserCrawler:
    """
    Trình bóc tách dữ liệu Douyin sử dụng Headless Chromium (Playwright).
    Vượt qua cơ chế kiểm tra bảo mật ArgusSecurityPlugin (Uifid & x-secsdk-web-signature) 
    và SSR React Server Components mới nhất của Douyin Web.
    """

    def __init__(self, cookies: dict = None, user_agent: str = None):
        self.cookies = cookies or {}
        self.user_agent = user_agent or "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"

    def _prepare_cookies(self) -> list:
        return [
            {"name": k, "value": v, "domain": ".douyin.com", "path": "/"}
            for k, v in self.cookies.items()
            if k and v
        ]

    def get_video_detail(self, video_id: str, timeout_sec: int = 20) -> dict:
        """
        Lấy chi tiết video đơn lẻ (bao gồm download URLs, tác giả, mô tả, hashtag).
        """
        video_url = f"https://www.douyin.com/video/{video_id}"
        result_holder = {}

        def _worker():
            try:
                with sync_playwright() as p:
                    browser = p.chromium.launch(
                        headless=True,
                        args=["--disable-blink-features=AutomationControlled"]
                    )
                    context = browser.new_context(
                        user_agent=self.user_agent,
                        viewport={"width": 1920, "height": 1080}
                    )
                    cookie_list = self._prepare_cookies()
                    if cookie_list:
                        context.add_cookies(cookie_list)
                    page = context.new_page()

                    def handle_response(response):
                        if "/aweme/v1/web/aweme/detail/" in response.url and response.status == 200:
                            try:
                                data = response.json()
                                if isinstance(data, dict) and "aweme_detail" in data:
                                    result_holder.update(data)
                            except Exception:
                                pass

                    page.on("response", handle_response)
                    try:
                        # Dùng commit để bắt đầu lắng nghe response sớm nhất có thể
                        page.goto(video_url, wait_until="commit", timeout=timeout_sec * 1000)
                    except Exception as e:
                        logger.warning(f"Browser goto video warning: {e}")

                    start = time.time()
                    while not result_holder and time.time() - start < timeout_sec:
                        page.wait_for_timeout(500)

                    browser.close()
            except Exception as e:
                logger.error(f"Error in browser get_video_detail: {e}", exc_info=True)

        t = threading.Thread(target=_worker)
        t.start()
        t.join(timeout=timeout_sec + 5)
        return result_holder

    def get_profile_and_posts(
        self, 
        sec_uid: str, 
        max_videos: int = 50, 
        check_cancel=None, 
        timeout_sec: int = 30
    ) -> Tuple[dict, list]:
        """
        Lấy thông tin tài khoản và danh sách video từ trang cá nhân (Profile).
        Tự động cuộn trang để lấy thêm video theo nhu cầu.
        """
        profile_url = f"https://www.douyin.com/user/{sec_uid}"
        profile_holder = {}
        videos_holder = []

        def _worker():
            try:
                with sync_playwright() as p:
                    browser = p.chromium.launch(
                        headless=True,
                        args=["--disable-blink-features=AutomationControlled"]
                    )
                    context = browser.new_context(
                        user_agent=self.user_agent,
                        viewport={"width": 1920, "height": 1080}
                    )
                    cookie_list = self._prepare_cookies()
                    if cookie_list:
                        context.add_cookies(cookie_list)
                    page = context.new_page()

                    has_more = [True]

                    def handle_response(response):
                        url = response.url
                        if "/aweme/v1/web/user/profile/other/" in url and response.status == 200:
                            try:
                                data = response.json()
                                user = data.get("user", {})
                                if user:
                                    profile_holder.update(user)
                            except Exception:
                                pass
                        elif "/aweme/v1/web/aweme/post/" in url and response.status == 200:
                            try:
                                data = response.json()
                                aweme_list = data.get("aweme_list", [])
                                has_more[0] = bool(data.get("has_more", 0))
                                existing_ids = {v.get("aweme_id") for v in videos_holder}
                                for aw in aweme_list:
                                    aw_id = aw.get("aweme_id")
                                    if aw_id and aw_id not in existing_ids:
                                        videos_holder.append(aw)
                                        existing_ids.add(aw_id)

                                if not profile_holder and aweme_list:
                                    author = aweme_list[0].get("author", {})
                                    if author:
                                        profile_holder.update(author)
                            except Exception:
                                pass

                    page.on("response", handle_response)
                    try:
                        page.goto(profile_url, wait_until="commit", timeout=timeout_sec * 1000)
                    except Exception as e:
                        logger.warning(f"Browser goto profile warning: {e}")

                    # Cuộn nhẹ để kích hoạt tải feed video
                    page.wait_for_timeout(2500)
                    page.evaluate("window.scrollTo(0, 500)")

                    start = time.time()
                    while not videos_holder and time.time() - start < 15:
                        if check_cancel and check_cancel():
                            break
                        page.wait_for_timeout(500)

                    # Cuộn tiếp nếu còn video và chưa đạt giới hạn max_videos
                    scroll_attempts = 0
                    last_count = len(videos_holder)
                    while has_more[0] and len(videos_holder) < max_videos and scroll_attempts < 6:
                        if check_cancel and check_cancel():
                            break
                        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                        page.wait_for_timeout(1500)
                        if len(videos_holder) == last_count:
                            scroll_attempts += 1
                        else:
                            scroll_attempts = 0
                            last_count = len(videos_holder)

                    browser.close()
            except Exception as e:
                logger.error(f"Error in browser get_profile_and_posts: {e}", exc_info=True)

        t = threading.Thread(target=_worker)
        t.start()
        t.join(timeout=timeout_sec + 15)
        return profile_holder, videos_holder
