import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from app.services.crawler.douyin_api import DouyinAPIClient
import httpx

client = DouyinAPIClient()
print("Using cookie:", {k: v[:5] + "..." if v else "" for k, v in client.cookies.items()})

video_id = "7598158190605802602"
params = client._default_query()
params.update({
    "aweme_id": video_id,
    "aid": "6383",
})
signed_url = client.build_signed_url("/aweme/v1/web/aweme/detail/", params)
print("\nURL:", signed_url)
resp = httpx.get(
    signed_url,
    headers=client.headers,
    cookies=client.cookies,
    timeout=15,
    follow_redirects=True
)
print("Status:", resp.status_code)
print("Headers:", resp.headers)
print("Response length:", len(resp.text))
print("Response text:", resp.text[:200])

# Let's also check if the post API works to confirm the cookie is truly valid
params_post = client._default_query()
params_post.update({"sec_user_id": "MS4wLjABAAAAgbac9ihpTlet1afYz7ingYX92zHVMzSGZeHQtWVaLSE"})
signed_url_post = client.build_signed_url("/aweme/v1/web/aweme/post/", params_post)
resp_post = httpx.get(
    signed_url_post,
    headers=client.headers,
    cookies=client.cookies,
    timeout=15,
    follow_redirects=True
)
print("\nPost Status:", resp_post.status_code)
print("Post Response len:", len(resp_post.text))
try:
    print("Post status_code in JSON:", resp_post.json().get("status_code"))
except Exception:
    print("Post not JSON")
