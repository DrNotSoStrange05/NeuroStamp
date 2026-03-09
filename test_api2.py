import urllib.request
import urllib.parse
from urllib.error import URLError
import json
import time
import subprocess
import os

# Start the server in the background
proc = subprocess.Popen(["uvicorn", "main:app", "--port", "8001"])
time.sleep(2) # wait for startup

base_url = "http://127.0.0.1:8001"
print("1. Login")
data = urllib.parse.urlencode({'username': 'ren', 'password': 'ren'}).encode('utf-8')
req = urllib.request.Request(f"{base_url}/login", data=data)
cookie = ""
with urllib.request.urlopen(req) as res:
    print(res.status, res.read().decode('utf-8'))
    cookie = res.info().get('Set-Cookie')

print("\n2. Stamp")
import mimetypes
import uuid

def encode_multipart_formdata(fields, files):
    boundary = uuid.uuid4().hex
    body = bytearray()
    for key, value in fields.items():
        body.extend(f"--{boundary}\r\n".encode())
        body.extend(f"Content-Disposition: form-data; name=\"{key}\"\r\n\r\n".encode())
        body.extend(f"{value}\r\n".encode())
    for key, filename, value in files:
        mimetype = mimetypes.guess_type(filename)[0] or 'application/octet-stream'
        body.extend(f"--{boundary}\r\n".encode())
        body.extend(f"Content-Disposition: form-data; name=\"{key}\"; filename=\"{filename}\"\r\n".encode())
        body.extend(f"Content-Type: {mimetype}\r\n\r\n".encode())
        body.extend(value)
        body.extend(b"\r\n")
    body.extend(f"--{boundary}--\r\n".encode())
    return 'multipart/form-data; boundary=' + boundary, body

with open("assets/zenitsu.jpg", "rb") as f:
    content_type, body = encode_multipart_formdata({'username': 'ren'}, [('file', 'zenitsu.jpg', f.read())])

req = urllib.request.Request(f"{base_url}/stamp", data=body, headers={'Content-Type': content_type, 'Cookie': cookie})
with urllib.request.urlopen(req) as res:
    resp_data = json.loads(res.read().decode('utf-8'))
    print(resp_data)
    stamped_url = resp_data.get("download_url")

print("\n3. Verify")
stamped_path = "." + stamped_url
with open(stamped_path, "rb") as f:
    content_type, body = encode_multipart_formdata({'username': 'ren'}, [('file', 'stamped.jpg', f.read())])

req = urllib.request.Request(f"{base_url}/verify", data=body, headers={'Content-Type': content_type, 'Cookie': cookie})
with urllib.request.urlopen(req) as res:
    print(json.loads(res.read().decode('utf-8')))

proc.terminate()
