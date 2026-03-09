import requests
import time
import os
from PIL import Image

# 1. Login to get session
session = requests.Session()
login_res = session.post("http://127.0.0.1:8000/login", data={"username": "testuser", "password": "password123"})
print(f"Login: {login_res.status_code}")

# 2. Stamp image
with open("assets/zenitsu.jpg", "rb") as f:
    stamp_res = session.post("http://127.0.0.1:8000/stamp", data={"username": "testuser"}, files={"file": f})
    
download_url = stamp_res.json()["download_url"]
print(f"Stamper: {download_url}")

# 3. Download the stamped image
stamped_path = f".{download_url}"

# 4. Simulate Instagram (Crush to 300x300, losing aspect ratio and 80% of data)
print("Simulating Social Media Upload (300x300 deform) ...")
img = Image.open(stamped_path)
img = img.resize((300, 300), Image.Resampling.LANCZOS)
img.save("static/uploads/instagram_theft.jpg", "JPEG", quality=60)

# 5. Verify the deformed image anonymously! (No username provided)
print("Verifying Anonymous Suspect File...")
with open("static/uploads/instagram_theft.jpg", "rb") as f:
    verify_res = session.post("http://127.0.0.1:8000/verify", files={"file": f})
    
print("Verify Result:")
print(verify_res.json())

