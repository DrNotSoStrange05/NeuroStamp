#!/bin/bash
# 1. Login
curl -s -X POST -c cookies.txt -d "username=ren" -d "password=ren" http://127.0.0.1:8000/login
echo ""

# 2. Stamp
RES=$(curl -s -X POST -b cookies.txt -F "username=ren" -F "file=@assets/zenitsu.jpg" http://127.0.0.1:8000/stamp)
echo "Stamp res: $RES"
URL=$(echo $RES | grep -o '\"download_url\":[^,]*' | cut -d '"' -f 4)

sleep 1

# 3. Verify
curl -s -X POST -b cookies.txt -F "username=ren" -F "file=@.$URL" http://127.0.0.1:8000/verify
echo ""
