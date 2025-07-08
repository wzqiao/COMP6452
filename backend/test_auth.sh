#!/bin/bash

# 注册账号
echo "测试注册用户"
curl -s -X POST http://127.0.0.1:5000/auth/register \
     -H "Content-Type: application/json" \
     -d '{"email":"a@b.com","password":"123456"}'
echo -e "\n"

# 登录获取 token
echo "测试登录获取 access_token"
RESPONSE=$(curl -s -X POST http://127.0.0.1:5000/auth/login \
     -H "Content-Type: application/json" \
     -d '{"email":"a@b.com","password":"123456"}')

echo "$RESPONSE"
TOKEN=$(echo $RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])")

# 绑定钱包
echo "测试钱包绑定"
curl -s -X POST http://127.0.0.1:5000/auth/wallet \
     -H "Authorization: Bearer $TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"wallet":"0x1234567890abcdef1234567890abcdef12345678"}'
echo -e "\n"

echo "测试结束"
