import urllib.request; import urllib.parse; import json; import io, mimetypes, uuid

boundary = uuid.uuid4().hex
body = b'--' + boundary.encode() + b'\r\n'
body += b'Content-Disposition: form-data; name="mode"\r\n\r\nproduct\r\n'
body += b'--' + boundary.encode() + b'\r\n'
body += b'Content-Disposition: form-data; name="prompt_text"\r\n\r\ntest\r\n'
body += b'--' + boundary.encode() + b'\r\n'
body += b'Content-Disposition: form-data; name="use_local_bg"\r\n\r\ntrue\r\n'
body += b'--' + boundary.encode() + b'\r\n'
body += b'Content-Disposition: form-data; name="image"; filename="test.jpg"\r\nContent-Type: image/jpeg\r\n\r\ndata\r\n'
body += b'--' + boundary.encode() + b'--\r\n'
req = urllib.request.Request('http://localhost:8000/api/ai-studio/generate', data=body)
req.add_header('Content-Type', 'multipart/form-data; boundary=' + boundary)
try:
    res = urllib.request.urlopen(req)
    print(res.read().decode('utf-8'))
except Exception as e:
    print(e.read().decode('utf-8'))
