import requests
import json

base_url = "http://127.0.0.1:8000"

# 1. Login
session = requests.Session()
res = session.post(f"{base_url}/login", data={"username": "ren", "password": "ren"})
print("Login:", res.status_code, res.json())

# 2. Stamp
with open("assets/zenitsu.jpg", "rb") as f:
    res = session.post(f"{base_url}/stamp", data={"username": "ren"}, files={"file": f})
    
print("Stamp res:", res.status_code, res.text)
if res.status_code == 200:
    data = res.json()
    stamped_url = data.get("download_url")
    print("Stamped URL:", stamped_url)
    
    # Wait a sec just in case the file hasn't flushed
    import time; time.sleep(1)
    
    # 3. Verify
    # The stamped image is in static/uploads
    # In the app, the frontend sends it back as a file. Let's do that.
    stamped_path = "." + stamped_url
    with open(stamped_path, "rb") as f:
        res = session.post(f"{base_url}/verify", data={"username": "ren"}, files={"file": f})
        print("Verify res:", res.status_code, res.text)
