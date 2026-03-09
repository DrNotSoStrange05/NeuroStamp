import urllib.request
import urllib.parse
from urllib.error import URLError
import json

base_url = "http://127.0.0.1:8000"

print("1. Login")
data = urllib.parse.urlencode({'username': 'ren', 'password': 'ren'}).encode('utf-8')
req = urllib.request.Request(f"{base_url}/login", data=data)
try:
    with urllib.request.urlopen(req) as res:
        print(res.status, res.read().decode('utf-8'))
        cookie = res.info().get('Set-Cookie')
except URLError as e:
    print(e)
