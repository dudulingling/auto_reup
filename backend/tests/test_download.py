import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.config import DATA_DIR
from app.services.crawler.douyin_scraper import DouyinScraper
from app.services.crawler.douyin_api import DouyinAPIClient

client = DouyinAPIClient()
print("Cookies extracted from /.env:", {k: v[:10] + "..." if v else "" for k, v in client.cookies.items()})

scraper = DouyinScraper(output_dir=os.path.join(DATA_DIR, "raw_videos"))
url = "https://www.douyin.com/video/7598158190605802602"

print(f"Testing URL: {url}")
for log_line in scraper.scrape_profile_generator(url):
    print(log_line, end="")
