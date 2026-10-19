import os
import subprocess
import json
import sys
from .sync_manager import SyncManager
from app.core.logger import get_logger
from app.db.session import SessionLocal
from app.models.history import VideoHistory, ProcessStatus
from app.models.followed_account import FollowedAccount

logger = get_logger(__name__)

def save_or_update_followed_account(db, sec_uid: str, nickname: str, avatar: str = "", follower_count: int = 0, total_favorited: int = 0, video_count: int = 0):
    try:
        acc = db.query(FollowedAccount).filter(FollowedAccount.sec_uid == sec_uid).first()
        if not acc:
            acc = FollowedAccount(
                sec_uid=sec_uid,
                nickname=nickname,
                avatar=avatar,
                follower_count=follower_count,
                total_favorited=total_favorited,
                video_count=video_count
            )
            db.add(acc)
        else:
            acc.nickname = nickname
            if avatar:
                acc.avatar = avatar
            if follower_count > 0:
                acc.follower_count = follower_count
            if total_favorited > 0:
                acc.total_favorited = total_favorited
            if video_count > 0:
                acc.video_count = video_count
        db.commit()
    except Exception as e:
        logger.error(f"Error saving followed account: {e}")
        db.rollback()

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../"))
DEFAULT_OUTPUT_DIR = os.path.join(PROJECT_ROOT, "data", "raw_videos")

class DouyinScraper:
    def __init__(self, output_dir: str = DEFAULT_OUTPUT_DIR):
        self.output_dir = output_dir
        self.sync_manager = SyncManager()
        self.cookie_path = os.path.join(PROJECT_ROOT, "data", "douyin_cookie.txt")
        os.makedirs(self.output_dir, exist_ok=True)
        logger.info("Khởi tạo DouyinScraper thành công.")

    def split_caption_and_hashtags(self, desc: str) -> tuple:
        """
        Split original video description into clean caption and hashtags.
        """
        if not desc:
            return "", ""
        import re
        tags = re.findall(r'#[^\s#]+', desc)
        hashtags = " ".join(tags)
        
        clean_caption = re.sub(r'#[^\s#]+', '', desc)
        clean_caption = re.sub(r'\s+', ' ', clean_caption).strip()
        
        return clean_caption, hashtags

    def scrape_profile_generator(self, profile_url: str, check_cancel=None):
        logger.info(f"Bắt đầu quét profile: {profile_url}")
        yield f"[*] Bắt đầu quét profile: {profile_url}\n"
        
        from .douyin_api import DouyinAPIClient
        client = DouyinAPIClient()
        
        # Xử lý URL (nếu là link ngắn v.douyin thì giải mã)
        long_url = client.resolve_short_url(profile_url) or profile_url
        
        # 1. Kiểm tra xem đây có phải là link 1 video cụ thể không
        video_id_match = client.extract_video_id(long_url)
        if video_id_match:
            yield f"[*] Phát hiện link video đơn lẻ: {video_id_match}\n"
            data = client.get_video_detail(video_id_match)
            aweme = data.get("aweme_detail")
            
            if not aweme:
                yield "[*] API bị chặn, đang kích hoạt giải mã Playwright ngầm...\n"
                try:
                    from .douyin_browser_crawler import DouyinBrowserCrawler
                    browser_crawler = DouyinBrowserCrawler(cookies=client.cookies, user_agent=client.user_agent)
                    b_data = browser_crawler.get_video_detail(video_id_match)
                    if b_data and b_data.get("aweme_detail"):
                        aweme = b_data["aweme_detail"]
                except Exception as b_err:
                    logger.error(f"Browser Scrape Error: {b_err}")
            
            if not aweme:
                yield "[!] Không tìm thấy chi tiết video. Link lỗi, video bị xóa hoặc bị chặn.\n"
                return
                
            video_urls = []
            for br in aweme.get("video", {}).get("bit_rate", []):
                for u in br.get("play_addr", {}).get("url_list", []):
                    if u and u not in video_urls:
                        video_urls.append(u)
            for u in aweme.get("video", {}).get("play_addr", {}).get("url_list", []):
                if u and u not in video_urls:
                    video_urls.append(u)

            if not video_urls:
                yield "[!] Không thể lấy link tải trực tiếp của video này (có thể là dạng hình ảnh/slideshow).\n"
                return

            video_urls.sort(key=lambda x: 0 if "aweme/v1/play" in x else 1)
                
            uploader = aweme.get("author", {}).get("nickname", "Unknown User")
            
            author = aweme.get("author", {})
            author_sec_uid = author.get("sec_uid")
            if author_sec_uid:
                db = SessionLocal()
                try:
                    save_or_update_followed_account(
                        db,
                        sec_uid=author_sec_uid,
                        nickname=author.get("nickname"),
                        avatar=author.get("avatar_thumb", {}).get("url_list", [""])[0] if author.get("avatar_thumb") else "",
                        follower_count=author.get("follower_count", 0),
                        total_favorited=author.get("total_favorited", 0),
                        video_count=author.get("aweme_count", 0)
                    )
                finally:
                    db.close()
            
            if self.sync_manager.is_downloaded(video_id_match):
                yield f"[-] Bỏ qua video {video_id_match} - Đã tải trước đó.\n"
                return
                
            desc = aweme.get("desc", "")
            clean_caption, tags = self.split_caption_and_hashtags(desc)
            yield f"[+] Đang tải video: {video_id_match} từ {uploader}\n"
            for dl_log in self._download_video_generator(client, video_urls, video_id_match, uploader, clean_caption, tags, author_sec_uid, check_cancel):
                yield dl_log
                
            return

        # 2. Xử lý link Profile
        sec_uid = client.extract_sec_uid(long_url)
        
        if not sec_uid:
            yield "[!] Không thể bóc tách mã người dùng (sec_uid) từ URL. Vui lòng kiểm tra lại link.\n"
            return
            
        profile_data = {}
        try:
            profile_info = client.get_user_profile(sec_uid)
            user_obj = profile_info.get("user", {}) if isinstance(profile_info, dict) else {}
            if user_obj:
                profile_data = {
                    "nickname": user_obj.get("nickname"),
                    "avatar": user_obj.get("avatar_thumb", {}).get("url_list", [""])[0] if user_obj.get("avatar_thumb") else "",
                    "follower_count": user_obj.get("follower_count", 0),
                    "total_favorited": user_obj.get("total_favorited", 0),
                    "video_count": user_obj.get("aweme_count", 0)
                }
                db = SessionLocal()
                try:
                    save_or_update_followed_account(
                        db,
                        sec_uid=sec_uid,
                        nickname=profile_data["nickname"],
                        avatar=profile_data["avatar"],
                        follower_count=profile_data["follower_count"],
                        total_favorited=profile_data["total_favorited"],
                        video_count=profile_data["video_count"]
                    )
                finally:
                    db.close()
        except Exception as e:
            logger.error(f"Error fetching/saving followed account profile: {e}")
            
        # Fetch number of crawled videos from DB and total videos from latest profile data
        db = SessionLocal()
        crawled_count = 0
        total_videos = 0
        try:
            crawled_count = db.query(VideoHistory).filter(VideoHistory.author_sec_uid == sec_uid).count()
        except Exception as e:
            logger.error(f"Error querying crawled video counts: {e}")
        finally:
            db.close()

        if profile_data and "video_count" in profile_data:
            total_videos = profile_data["video_count"]
        else:
            db = SessionLocal()
            try:
                acc = db.query(FollowedAccount).filter(FollowedAccount.sec_uid == sec_uid).first()
                if acc:
                    total_videos = acc.video_count or 0
            except Exception as e:
                logger.error(f"Error querying FollowedAccount: {e}")
            finally:
                db.close()

        logger.info(f"Kênh {sec_uid} có tổng số video: {total_videos}, đã cào: {crawled_count}")
        yield f"[*] Thông tin kênh - Tổng số video: {total_videos}, Đã cào: {crawled_count}\n"

        cursor = 0
        has_more = True
        total_fetched = 0
        consecutive_duplicates = 0
        force_stop = False
        
        while has_more and not force_stop:
            if check_cancel and check_cancel():
                yield "[!] Tiến trình cào đã bị hủy bởi người dùng.\n"
                break
                
            data = client.get_user_post(sec_uid, max_cursor=cursor, count=18)
            aweme_list = data.get("aweme_list", [])
            if not aweme_list:
                if total_fetched == 0:
                    yield "[*] Đang thử bóc tách danh sách video kênh qua Playwright ngầm...\n"
                    try:
                        from .douyin_browser_crawler import DouyinBrowserCrawler
                        browser_crawler = DouyinBrowserCrawler(cookies=client.cookies, user_agent=client.user_agent)
                        b_prof, b_vids = browser_crawler.get_profile_and_posts(sec_uid, max_videos=50, check_cancel=check_cancel)
                        if b_vids:
                            aweme_list = b_vids
                            if b_prof and not profile_data:
                                profile_data = b_prof
                    except Exception as b_err:
                        logger.error(f"Browser profile scrape error: {b_err}")

            if not aweme_list:
                if total_fetched == 0:
                    yield "[!] Không tìm thấy video nào. Có thể do tài khoản bị khóa riêng tư, hoặc thuật toán chống bot quá mạnh. Vui lòng cập nhật Cookie thủ công!\n"
                break
                
            if aweme_list and not profile_data:
                first_aweme = aweme_list[0]
                author = first_aweme.get("author", {})
                if author:
                    db = SessionLocal()
                    try:
                        save_or_update_followed_account(
                            db,
                            sec_uid=sec_uid,
                            nickname=author.get("nickname"),
                            avatar=author.get("avatar_thumb", {}).get("url_list", [""])[0] if author.get("avatar_thumb") else "",
                            follower_count=author.get("follower_count", 0),
                            total_favorited=author.get("total_favorited", 0),
                            video_count=author.get("aweme_count", 0)
                        )
                        profile_data = {"nickname": author.get("nickname")}
                        total_videos = author.get("aweme_count", 0)
                    finally:
                        db.close()
                
            for aweme in aweme_list:
                video_id = aweme.get("aweme_id")
                if not video_id: 
                    continue
                
                try:
                    video_urls = []
                    for br in aweme.get("video", {}).get("bit_rate", []):
                        for u in br.get("play_addr", {}).get("url_list", []):
                            if u and u not in video_urls:
                                video_urls.append(u)
                    for u in aweme.get("video", {}).get("play_addr", {}).get("url_list", []):
                        if u and u not in video_urls:
                            video_urls.append(u)
                    if not video_urls:
                        continue
                    video_urls.sort(key=lambda x: 0 if "aweme/v1/play" in x else 1)
                except (KeyError, IndexError, TypeError):
                    # Skip image-based videos / corrupted metadata
                    continue
                    
                uploader = aweme.get("author", {}).get("nickname", "Unknown User")
                total_fetched += 1
                
                if self.sync_manager.is_downloaded(video_id):
                    consecutive_duplicates += 1
                    logger.info(f"Bỏ qua video {video_id} - Đã tải trước đó.")
                    yield f"[-] Bỏ qua video {video_id} - Đã tải trước đó.\n"
                    
                    if consecutive_duplicates >= 5:
                        if total_videos > 0 and crawled_count < total_videos:
                            # There are still uncrawled videos further down, so do not stop crawling
                            logger.info(f"Gặp 5 video cũ liên tiếp nhưng còn video chưa cào ({crawled_count}/{total_videos}). Tiếp tục quét...")
                        else:
                            yield f"[!] Đã gặp 5 video cũ liên tiếp và đã cào hết video mới. Kích hoạt 'Tải Tăng Dần', dừng quét profile này để tối ưu.\n"
                            force_stop = True
                            break
                    continue
                    
                # Reset counter when we encounter a new video
                consecutive_duplicates = 0
                
                desc = aweme.get("desc", "")
                clean_caption, tags = self.split_caption_and_hashtags(desc)
                logger.info(f"Đang tải video mới: {video_id} từ {uploader}")
                yield f"[+] Đang tải video mới: {video_id}\n"
                
                download_success = False
                for dl_log in self._download_video_generator(client, video_urls, video_id, uploader, clean_caption, tags, sec_uid, check_cancel):
                    yield dl_log
                    if isinstance(dl_log, dict) and dl_log.get("progress") == 100:
                        download_success = True

                if download_success:
                    crawled_count += 1
                    
            cursor = data.get("max_cursor", 0)
            has_more = data.get("has_more", False)

    def _download_video_generator(self, client, video_urls: list, video_id: str, uploader: str, original_caption: str = "", original_hashtags: str = "", author_sec_uid: str = None, check_cancel=None):
        import httpx
        user_folder = "".join(c for c in uploader if c.isalnum() or c in (' ', '_', '-')).strip()
        if not user_folder:
            user_folder = "Unknown_User"
            
        target_dir = os.path.join(self.output_dir, user_folder)
        os.makedirs(target_dir, exist_ok=True)
        
        output_file = os.path.join(target_dir, f"{video_id}.mp4")
        temp_file = output_file + ".part"
        
        success = False
        last_error = ""
        max_retries_per_url = 2
        
        for url_idx, video_url in enumerate(video_urls):
            if success: break
            
            for attempt in range(max_retries_per_url):
                try:
                    dl_headers = dict(client.headers)
                    if "douyinvod.com" in video_url:
                        dl_headers["Referer"] = ""
                    with httpx.Client() as hx_client:
                        with hx_client.stream("GET", video_url, headers=dl_headers, cookies=client.cookies, timeout=30, follow_redirects=True) as response:
                            response.raise_for_status()
                            
                            total_size = int(response.headers.get('content-length', 0))
                            downloaded = 0
                            
                            if total_size > 0:
                                mb_size = round(total_size / (1024 * 1024), 2)
                                yield f"[*] Bắt đầu tải file (CDN {url_idx + 1}), kích thước: {mb_size} MB\n"
                            else:
                                yield f"[*] Bắt đầu tải file (CDN {url_idx + 1})...\n"
                                
                            last_percent = 0
                            with open(temp_file, 'wb') as f:
                                for chunk in response.iter_bytes(chunk_size=8192*8):
                                    if chunk:
                                        if check_cancel and check_cancel():
                                            raise InterruptedError("Download cancelled by user")
                                        f.write(chunk)
                                        downloaded += len(chunk)
                                        if total_size > 0:
                                            percent = int((downloaded / total_size) * 100)
                                            if percent >= last_percent + 10:
                                                yield {"log": f"[download] {percent}% of {mb_size}MB\n", "progress": percent}
                                                last_percent = percent
                    
                    # Đổi tên file part thành mp4 sau khi tải xong 100%
                    if os.path.exists(temp_file):
                        os.rename(temp_file, output_file)
                        
                    logger.info(f"Tải thành công video: {video_id} từ CDN {url_idx + 1}")
                    yield {"log": f"[*] Tải thành công video: {video_id}\n", "progress": 100}
                    self.sync_manager.mark_as_downloaded(video_id)
                    
                    db = SessionLocal()
                    try:
                        record = db.query(VideoHistory).filter(VideoHistory.raw_video_path == output_file).first()
                        if not record:
                            record = VideoHistory(
                                original_name=f"{video_id}.mp4",
                                source=f"Douyin - {uploader}",
                                raw_video_path=output_file,
                                status=ProcessStatus.PENDING,
                                original_caption=original_caption,
                                original_hashtags=original_hashtags,
                                author_sec_uid=author_sec_uid
                            )
                            db.add(record)
                            db.commit()
                        else:
                            if not record.author_sec_uid and author_sec_uid:
                                record.author_sec_uid = author_sec_uid
                                db.commit()
                    except Exception as e:
                        logger.error(f"Lỗi khi lưu DB VideoHistory: {e}")
                    finally:
                        db.close()
                        
                    success = True
                    break # Thành công, thoát vòng lặp retry
                    
                except Exception as e:
                    last_error = str(e)
                    if os.path.exists(temp_file):
                        try:
                            os.remove(temp_file)
                        except:
                            pass
                            
                    if attempt < max_retries_per_url - 1:
                        yield f"[*] Mất kết nối khi tải, đang thử lại lần {attempt + 2}...\n"
                        
            if not success and url_idx < len(video_urls) - 1:
                yield f"[*] CDN {url_idx + 1} không phản hồi, đang chuyển sang server dự phòng...\n"
                
        if not success:
            logger.error(f"Lỗi hệ thống khi tải video {video_id}: {last_error}", exc_info=True)
            yield f"[!] Lỗi khi tải video {video_id}: {last_error}. Bỏ qua video này.\n"

