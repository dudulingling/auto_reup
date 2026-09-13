import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from app.services.crawler.douyin_api import DouyinAPIClient

client = DouyinAPIClient()
params = client._default_query()
params.update({"sec_user_id": "MS4wLjABAAAAgbac9ihpTlet1afYz7ingYX92zHVMzSGZeHQtWVaLSE"})
if "a_bogus" in params:
    del params["a_bogus"]
resp_data = client.request_json("/aweme/v1/web/aweme/post/", params)
print("Response data:")
print(resp_data)
