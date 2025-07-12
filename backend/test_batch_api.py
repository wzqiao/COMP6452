#!/usr/bin/env python3
"""
批次API测试脚本
"""
import requests
import json
from datetime import datetime

BASE_URL = "http://127.0.0.1:5000"

def login_and_get_token():
    """登录并获取JWT token"""
    print("🔐 登录获取token...")
    login_data = {
        "email": "test@example.com",
        "password": "123456"
    }
    
    response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
    if response.status_code == 200:
        result = response.json()
        print(f"✅ 登录成功，角色: {result['role']}")
        return result['token']
    else:
        print(f"❌ 登录失败: {response.json()}")
        return None

def test_create_batch(token):
    """测试创建批次"""
    print("\n📦 测试创建批次...")
    
    # 准备批次数据
    batch_data = {
        "metadata": {
            "productName": "有机苹果",
            "origin": "山东烟台",
            "quantity": "100",
            "unit": "kg",
            "harvestDate": "2025-07-01",
            "expiryDate": "2025-08-15",
            "totalWeightKg": 100,
            "batchNumber": f"BATCH-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "organic": True,
            "import": False
        }
    }
    
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.post(f"{BASE_URL}/batches", json=batch_data, headers=headers)
    
    print(f"状态码: {response.status_code}")
    result = response.json()
    print(f"响应: {json.dumps(result, indent=2, ensure_ascii=False)}")
    
    if response.status_code == 201:
        print("✅ 批次创建成功")
        return result['batchId']
    else:
        print("❌ 批次创建失败")
        return None

def test_get_batch(batch_id):
    """测试查询批次详情"""
    print(f"\n🔍 测试查询批次详情 (ID: {batch_id})...")
    
    response = requests.get(f"{BASE_URL}/batches/{batch_id}")
    
    print(f"状态码: {response.status_code}")
    result = response.json()
    print(f"响应: {json.dumps(result, indent=2, ensure_ascii=False)}")
    
    if response.status_code == 200:
        print("✅ 批次查询成功")
        return True
    else:
        print("❌ 批次查询失败")
        return False

def test_list_batches():
    """测试批次列表查询"""
    print("\n📋 测试批次列表查询...")
    
    response = requests.get(f"{BASE_URL}/batches")
    
    print(f"状态码: {response.status_code}")
    result = response.json()
    print(f"响应: {json.dumps(result, indent=2, ensure_ascii=False)}")
    
    if response.status_code == 200:
        print(f"✅ 查询成功，共找到 {len(result['batches'])} 个批次")
        return True
    else:
        print("❌ 批次列表查询失败")
        return False

def test_update_batch_status(batch_id, token):
    """测试更新批次状态"""
    print(f"\n🔄 测试更新批次状态 (ID: {batch_id})...")
    
    status_data = {
        "status": "inspected"
    }
    
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.put(f"{BASE_URL}/batches/{batch_id}/status", json=status_data, headers=headers)
    
    print(f"状态码: {response.status_code}")
    result = response.json()
    print(f"响应: {json.dumps(result, indent=2, ensure_ascii=False)}")
    
    if response.status_code == 200:
        print("✅ 批次状态更新成功")
        return True
    else:
        print("❌ 批次状态更新失败")
        return False

def test_permission_errors():
    """测试权限验证"""
    print("\n🚫 测试权限验证...")
    
    # 测试不带token创建批次
    print("测试不带token创建批次:")
    batch_data = {"metadata": {"productName": "test"}}
    response = requests.post(f"{BASE_URL}/batches", json=batch_data)
    print(f"状态码: {response.status_code} - {response.json()}")
    
    # 测试缺少必填字段
    print("\n测试缺少必填字段:")
    token = login_and_get_token()
    if token:
        headers = {"Authorization": f"Bearer {token}"}
        invalid_data = {"metadata": {"productName": "test"}}  # 缺少其他必填字段
        response = requests.post(f"{BASE_URL}/batches", json=invalid_data, headers=headers)
        print(f"状态码: {response.status_code} - {response.json()}")

def main():
    print("🚀 开始批次API测试...")
    print("=" * 50)
    
    # 1. 登录获取token
    token = login_and_get_token()
    if not token:
        print("❌ 无法获取token，测试终止")
        return
    
    # 2. 创建批次
    batch_id = test_create_batch(token)
    if not batch_id:
        print("❌ 批次创建失败，后续测试可能受影响")
        return
    
    # 3. 查询批次详情
    test_get_batch(batch_id)
    
    # 4. 查询批次列表
    test_list_batches()
    
    # 5. 更新批次状态
    test_update_batch_status(batch_id, token)
    
    # 6. 再次查询确认状态更新
    test_get_batch(batch_id)
    
    # 7. 测试权限验证
    test_permission_errors()
    
    print("\n" + "=" * 50)
    print("🎉 批次API测试完成！")

if __name__ == "__main__":
    main() 