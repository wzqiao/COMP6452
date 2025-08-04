#!/bin/bash

# Register account
echo "Test register user"
curl -s -X POST http://127.0.0.1:5000/auth/register \
     -H "Content-Type: application/json" \
     -d '{"email":"aa@b.com","password":"123456"}'
echo -e "\n"

# Login to get token
echo "Test login to get access_token"
RESPONSE=$(curl -s -X POST http://127.0.0.1:5000/auth/login \
     -H "Content-Type: application/json" \
     -d '{"email":"aa@b.com","password":"123456"}')

echo "$RESPONSE"
TOKEN=$(echo $RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])")

# Bind wallet
echo "Test wallet bind"
curl -s -X POST http://127.0.0.1:5000/auth/wallet \
     -H "Authorization: Bearer $TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"wallet":"0x1234567890abcdef1234567890abcdef12345678"}'
echo -e "\n"

echo "Test end"
