import os
import sys

# Thêm đường dẫn project vào sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.services.crawler.douyin_api import DouyinAPIClient
import httpx
import re

client = DouyinAPIClient()
video_id = "7598158190605802602"
html_resp = httpx.get(
    f"https://www.douyin.com/video/{video_id}", 
    headers=client.headers, 
    cookies=client.cookies, 
    timeout=10, 
    follow_redirects=True
)
print("Status:", html_resp.status_code)
match = re.search(r'<script id="RENDER_DATA" type="application/json">(.*?)</script>', html_resp.text)
if match:
    print("RENDER_DATA found!")
else:
    print("RENDER_DATA not found. Dumping start of HTML:")
    print(html_resp.text[:500])
    
    with open("douyin_test.html", "w", encoding="utf-8") as f:
        f.write(html_resp.text)
