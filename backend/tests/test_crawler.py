import os
import sys

# Thêm đường dẫn project vào sys.path
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
BACKEND_DIR = os.path.join(ROOT_DIR, "backend")
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from app.services.crawler.douyin_scraper import DouyinScraper
from dotenv import load_dotenv

load_dotenv(os.path.join(ROOT_DIR, "data", ".env"))
scraper = DouyinScraper(output_dir=os.path.join(ROOT_DIR, "data", "raw_videos"))
url = "https://www.douyin.com/video/7598158190605802602"

print(f"Testing URL: {url}")
for log_line in scraper.scrape_profile_generator(url):
    print(log_line, end="")
