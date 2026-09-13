import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from app.services.crawler.douyin_api import DouyinAPIClient
import httpx

client = DouyinAPIClient()
aweme_id = "7598158190605802602"

for aid in ["6383", "1128"]:
    params = client._default_query()
    params.update({
        "aweme_id": aweme_id,
        "aid": aid,
    })
    signed_url = client.build_signed_url("/aweme/v1/web/aweme/detail/", params)
    print(f"Testing aid {aid}")
    print(signed_url)
    resp = httpx.get(
        signed_url,
        headers=client.headers,
        cookies=client.cookies,
        timeout=15,
        follow_redirects=True
    )
    print("Status:", resp.status_code)
    print("Response text length:", len(resp.text))
    print(resp.text[:500])
