#!/usr/bin/env python3
import requests
import json

BASE_URL = "http://127.0.0.1:5000"

def test_register():
    """测试用户注册"""
    print("🔧 测试用户注册...")
    url = f"{BASE_URL}/auth/register"
    data = {
        "email": "test@example.com",
        "password": "123456",
        "role": "producer"
    }
    
    try:
        response = requests.post(url, json=data)
        print(f"状态码: {response.status_code}")
        print(f"响应: {response.json()}")
        return response.status_code == 201
    except Exception as e:
        print(f"❌ 注册失败: {e}")
        return False

def test_login():
    """测试用户登录"""
    print("\n🔐 测试用户登录...")
    url = f"{BASE_URL}/auth/login"
    data = {
        "email": "test@example.com",
        "password": "123456"
    }
    
    try:
        response = requests.post(url, json=data)
        print(f"状态码: {response.status_code}")
        result = response.json()
        print(f"响应: {result}")
        
        if response.status_code == 200 and 'token' in result:
            return result['token']
        return None
    except Exception as e:
        print(f"❌ 登录失败: {e}")
        return None

def test_wallet_bind(token):
    """测试钱包绑定"""
    print("\n💰 测试钱包绑定...")
    url = f"{BASE_URL}/auth/wallet"
    data = {
        "wallet": "0x1234567890abcdef1234567890abcdef12345678"
    }
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    try:
        response = requests.post(url, json=data, headers=headers)
        print(f"状态码: {response.status_code}")
        print(f"响应: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ 钱包绑定失败: {e}")
        return False

def main():
    print("🚀 开始API测试...")
    
    # 测试注册
    if test_register():
        print("✅ 注册成功")
    else:
        print("❌ 注册失败")
        return
    
    # 测试登录
    token = test_login()
    if token:
        print("✅ 登录成功")
        
        # 测试钱包绑定
        if test_wallet_bind(token):
            print("✅ 钱包绑定成功")
        else:
            print("❌ 钱包绑定失败")
    else:
        print("❌ 登录失败")
    
    print("\n🎉 测试完成!")

if __name__ == "__main__":
    main() 