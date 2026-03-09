import subprocess
import time

# Let's write a simple python script to hit it with requests, now that we know we can install it
proc = subprocess.Popen(["uvicorn", "main:app", "--port", "8002"])
time.sleep(2)


import requests
base_url = "http://127.0.0.1:8002"
s = requests.Session()
r = s.post(f"{base_url}/register", data={"username": "testuser1", "password": "abc"})
if r.status_code != 200: print(r.text)
r = s.post(f"{base_url}/login", data={"username": "testuser1", "password": "abc"})
print("login", r.status_code)

with open("assets/zenitsu.jpg", "rb") as f:
    r = s.post(f"{base_url}/stamp", data={"username": "testuser1"}, files={"file": f})
    data = r.json()
    print("stamp", data)

stamped_url = data["download_url"]
with open("." + stamped_url, "rb") as f:
    r = s.post(f"{base_url}/verify", data={"username": "testuser1"}, files={"file": f})
    print("verify", r.json())

proc.terminate()
