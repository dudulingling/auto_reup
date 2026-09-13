import httpx
import re

url = "https://www.douyin.com/video/7640334063244414217"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Referer": "https://www.douyin.com/"
}

try:
    resp = httpx.get(url, headers=headers, follow_redirects=True, timeout=10)
    print("Status code:", resp.status_code)
    print("URL after redirect:", resp.url)
    
    with open("douyin_test.html", "w", encoding="utf-8") as f:
        f.write(resp.text)
        
    match = re.search(r'<script id="RENDER_DATA" type="application/json">(.*?)</script>', resp.text)
    if match:
        print("FOUND RENDER_DATA len:", len(match.group(1)))
    else:
        print("RENDER_DATA NOT FOUND!")
        
    match2 = re.search(r'window\._ROUTER_DATA\s*=\s*(.*?);', resp.text)
    if match2:
        print("FOUND _ROUTER_DATA len:", len(match2.group(1)))
    else:
        print("_ROUTER_DATA NOT FOUND!")
        
except Exception as e:
    print("Error:", e)
