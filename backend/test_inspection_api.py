# -*- coding: utf-8 -*-
"""
检验API测试文件
"""

import os
import sys
import json
import requests
from datetime import datetime, timedelta

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 配置
API_BASE_URL = "http://localhost:5000"
AUTH_URL = f"{API_BASE_URL}/auth"
BATCH_URL = f"{API_BASE_URL}/batches"
INSPECTION_URL = f"{API_BASE_URL}/api"

# 测试用户数据
TEST_USERS = {
    "producer": {
        "email": "producer_test@example.com",
        "password": "test123456",
        "role": "producer"
    },
    "inspector": {
        "email": "inspector_test@example.com",
        "password": "test123456",
        "role": "inspector"
    }
}

def print_separator(title):
    """打印分隔线"""
    print(f"\n{'='*50}")
    print(f"🧪 {title}")
    print('='*50)

def print_result(success, message, data=None):
    """打印测试结果"""
    status = "✅" if success else "❌"
    print(f"{status} {message}")
    if data:
        print(f"   数据: {json.dumps(data, indent=2, ensure_ascii=False)}")

def register_and_login(user_type):
    """注册并登录用户"""
    user_data = TEST_USERS[user_type]
    
    # 注册用户
    try:
        response = requests.post(f"{AUTH_URL}/register", json=user_data)
        if response.status_code in [201, 403]:  # 201创建成功，403用户已存在
            print(f"✅ {user_type} 注册/已存在")
        else:
            print(f"❌ {user_type} 注册失败: {response.json()}")
            return None
    except Exception as e:
        print(f"❌ {user_type} 注册异常: {str(e)}")
        return None
    
    # 登录用户
    try:
        response = requests.post(f"{AUTH_URL}/login", json={
            "email": user_data["email"],
            "password": user_data["password"]
        })
        if response.status_code == 200:
            token = response.json()["token"]
            print(f"✅ {user_type} 登录成功")
            return token
        else:
            print(f"❌ {user_type} 登录失败: {response.json()}")
            return None
    except Exception as e:
        print(f"❌ {user_type} 登录异常: {str(e)}")
        return None

def create_test_batch(token):
    """创建测试批次"""
    # 使用动态日期确保过期日期在未来
    harvest_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
    expiry_date = (datetime.now() + timedelta(days=90)).strftime('%Y-%m-%d')
    
    batch_data = {
        "metadata": {
            "productName": "测试苹果",
            "origin": "测试农场",
            "quantity": "100",
            "unit": "kg",
            "harvestDate": harvest_date,
            "expiryDate": expiry_date,
            "variety": "富士",
            "grade": "A级",
            "organic": True
        }
    }
    
    try:
        response = requests.post(
            f"{BATCH_URL}",
            json=batch_data,
            headers={"Authorization": f"Bearer {token}"}
        )
        if response.status_code == 201:
            batch_id = response.json()["batchId"]
            print(f"✅ 批次创建成功，ID: {batch_id}")
            return batch_id
        else:
            print(f"❌ 批次创建失败: {response.json()}")
            return None
    except Exception as e:
        print(f"❌ 批次创建异常: {str(e)}")
        return None

def test_submit_inspection():
    """测试提交检验结果"""
    print_separator("测试提交检验结果")
    
    # 1. 准备测试数据
    producer_token = register_and_login("producer")
    inspector_token = register_and_login("inspector")
    
    if not producer_token or not inspector_token:
        print("❌ 用户准备失败，跳过测试")
        return
    
    # 2. 创建测试批次
    batch_id = create_test_batch(producer_token)
    if not batch_id:
        print("❌ 批次创建失败，跳过测试")
        return
    
    # 3. 测试提交检验结果
    inspection_data = {
        "result": "passed",
        "file_url": "https://example.com/test-inspection-report.pdf",
        "notes": "检验通过，产品质量良好",
        "insp_date": datetime.now().isoformat()
    }
    
    try:
        response = requests.post(
            f"{INSPECTION_URL}/batches/{batch_id}/inspection",
            json=inspection_data,
            headers={"Authorization": f"Bearer {inspector_token}"}
        )
        
        if response.status_code == 201:
            result = response.json()
            print_result(True, "检验结果提交成功", result)
            return result["inspection"]["id"]
        else:
            print_result(False, f"检验结果提交失败，状态码: {response.status_code}", response.json())
            return None
            
    except Exception as e:
        print_result(False, f"检验结果提交异常: {str(e)}")
        return None

def test_submit_inspection_invalid_permission():
    """测试无效权限提交检验结果"""
    print_separator("测试权限验证")
    
    # 1. 准备测试数据
    producer_token = register_and_login("producer")
    
    if not producer_token:
        print("❌ 用户准备失败，跳过测试")
        return
    
    # 2. 创建测试批次
    batch_id = create_test_batch(producer_token)
    if not batch_id:
        print("❌ 批次创建失败，跳过测试")
        return
    
    # 3. 测试生产者提交检验结果（应该失败）
    inspection_data = {
        "result": "passed",
        "file_url": "https://example.com/test-report.pdf",
        "notes": "测试备注"
    }
    
    try:
        response = requests.post(
            f"{INSPECTION_URL}/batches/{batch_id}/inspection",
            json=inspection_data,
            headers={"Authorization": f"Bearer {producer_token}"}
        )
        
        if response.status_code == 403:
            print_result(True, "权限验证正确，生产者无法提交检验结果", response.json())
        else:
            print_result(False, f"权限验证失败，状态码: {response.status_code}", response.json())
            
    except Exception as e:
        print_result(False, f"权限验证测试异常: {str(e)}")

def test_submit_inspection_missing_fields():
    """测试缺少必填字段"""
    print_separator("测试数据验证")
    
    # 1. 准备测试数据
    producer_token = register_and_login("producer")
    inspector_token = register_and_login("inspector")
    
    if not producer_token or not inspector_token:
        print("❌ 用户准备失败，跳过测试")
        return
    
    # 2. 创建测试批次
    batch_id = create_test_batch(producer_token)
    if not batch_id:
        print("❌ 批次创建失败，跳过测试")
        return
    
    # 3. 测试缺少必填字段
    invalid_data = {
        "notes": "只有备注，缺少结果和文件URL"
    }
    
    try:
        response = requests.post(
            f"{INSPECTION_URL}/batches/{batch_id}/inspection",
            json=invalid_data,
            headers={"Authorization": f"Bearer {inspector_token}"}
        )
        
        if response.status_code == 400:
            print_result(True, "数据验证正确，缺少必填字段", response.json())
        else:
            print_result(False, f"数据验证失败，状态码: {response.status_code}", response.json())
            
    except Exception as e:
        print_result(False, f"数据验证测试异常: {str(e)}")

def test_get_batch_inspections():
    """测试获取批次检验记录"""
    print_separator("测试获取批次检验记录")
    
    # 1. 准备测试数据
    producer_token = register_and_login("producer")
    inspector_token = register_and_login("inspector")
    
    if not producer_token or not inspector_token:
        print("❌ 用户准备失败，跳过测试")
        return
    
    # 2. 创建测试批次
    batch_id = create_test_batch(producer_token)
    if not batch_id:
        print("❌ 批次创建失败，跳过测试")
        return
    
    # 3. 提交检验结果
    inspection_data = {
        "result": "failed",
        "file_url": "https://example.com/test-fail-report.pdf",
        "notes": "检验未通过，发现质量问题"
    }
    
    try:
        # 提交检验结果
        response = requests.post(
            f"{INSPECTION_URL}/batches/{batch_id}/inspection",
            json=inspection_data,
            headers={"Authorization": f"Bearer {inspector_token}"}
        )
        
        if response.status_code != 201:
            print("❌ 检验结果提交失败，跳过获取测试")
            return
        
        # 获取批次检验记录
        response = requests.get(
            f"{INSPECTION_URL}/batches/{batch_id}/inspections",
            headers={"Authorization": f"Bearer {producer_token}"}
        )
        
        if response.status_code == 200:
            result = response.json()
            print_result(True, f"获取检验记录成功，共 {result['total_count']} 条记录", result)
        else:
            print_result(False, f"获取检验记录失败，状态码: {response.status_code}", response.json())
            
    except Exception as e:
        print_result(False, f"获取检验记录测试异常: {str(e)}")

def test_get_inspection_detail():
    """测试获取检验记录详情"""
    print_separator("测试获取检验记录详情")
    
    # 1. 准备测试数据
    producer_token = register_and_login("producer")
    inspector_token = register_and_login("inspector")
    
    if not producer_token or not inspector_token:
        print("❌ 用户准备失败，跳过测试")
        return
    
    # 2. 创建测试批次
    batch_id = create_test_batch(producer_token)
    if not batch_id:
        print("❌ 批次创建失败，跳过测试")
        return
    
    # 3. 提交检验结果
    inspection_data = {
        "result": "needs_recheck",
        "file_url": "https://example.com/test-recheck-report.pdf",
        "notes": "需要复检，某些指标接近临界值"
    }
    
    try:
        # 提交检验结果
        response = requests.post(
            f"{INSPECTION_URL}/batches/{batch_id}/inspection",
            json=inspection_data,
            headers={"Authorization": f"Bearer {inspector_token}"}
        )
        
        if response.status_code != 201:
            print("❌ 检验结果提交失败，跳过详情测试")
            return
        
        inspection_id = response.json()["inspection"]["id"]
        
        # 获取检验记录详情
        response = requests.get(
            f"{INSPECTION_URL}/inspections/{inspection_id}",
            headers={"Authorization": f"Bearer {producer_token}"}
        )
        
        if response.status_code == 200:
            result = response.json()
            print_result(True, "获取检验记录详情成功", result)
        else:
            print_result(False, f"获取检验记录详情失败，状态码: {response.status_code}", response.json())
            
    except Exception as e:
        print_result(False, f"获取检验记录详情测试异常: {str(e)}")

def test_update_inspection():
    """测试更新检验记录"""
    print_separator("测试更新检验记录")
    
    # 1. 准备测试数据
    producer_token = register_and_login("producer")
    inspector_token = register_and_login("inspector")
    
    if not producer_token or not inspector_token:
        print("❌ 用户准备失败，跳过测试")
        return
    
    # 2. 创建测试批次
    batch_id = create_test_batch(producer_token)
    if not batch_id:
        print("❌ 批次创建失败，跳过测试")
        return
    
    # 3. 提交检验结果
    inspection_data = {
        "result": "needs_recheck",
        "file_url": "https://example.com/initial-report.pdf",
        "notes": "初步检验完成"
    }
    
    try:
        # 提交检验结果
        response = requests.post(
            f"{INSPECTION_URL}/batches/{batch_id}/inspection",
            json=inspection_data,
            headers={"Authorization": f"Bearer {inspector_token}"}
        )
        
        if response.status_code != 201:
            print("❌ 检验结果提交失败，跳过更新测试")
            return
        
        inspection_id = response.json()["inspection"]["id"]
        
        # 更新检验记录
        update_data = {
            "result": "passed",
            "file_url": "https://example.com/final-report.pdf",
            "notes": "复检完成，产品质量合格"
        }
        
        response = requests.put(
            f"{INSPECTION_URL}/inspections/{inspection_id}",
            json=update_data,
            headers={"Authorization": f"Bearer {inspector_token}"}
        )
        
        if response.status_code == 200:
            result = response.json()
            print_result(True, "更新检验记录成功", result)
        else:
            print_result(False, f"更新检验记录失败，状态码: {response.status_code}", response.json())
            
    except Exception as e:
        print_result(False, f"更新检验记录测试异常: {str(e)}")

def test_get_inspections_list():
    """测试获取检验记录列表"""
    print_separator("测试获取检验记录列表")
    
    # 1. 准备测试数据
    inspector_token = register_and_login("inspector")
    
    if not inspector_token:
        print("❌ 用户准备失败，跳过测试")
        return
    
    # 2. 获取检验记录列表
    try:
        response = requests.get(
            f"{INSPECTION_URL}/inspections?page=1&per_page=10",
            headers={"Authorization": f"Bearer {inspector_token}"}
        )
        
        if response.status_code == 200:
            result = response.json()
            print_result(True, f"获取检验记录列表成功，共 {len(result['inspections'])} 条记录", result)
        else:
            print_result(False, f"获取检验记录列表失败，状态码: {response.status_code}", response.json())
            
    except Exception as e:
        print_result(False, f"获取检验记录列表测试异常: {str(e)}")

def run_all_tests():
    """运行所有测试"""
    print("🧪 开始运行检验API测试...")
    print("=" * 60)
    
    # 基础功能测试
    test_submit_inspection()
    test_get_batch_inspections()
    test_get_inspection_detail()
    test_update_inspection()
    test_get_inspections_list()
    
    # 权限和验证测试
    test_submit_inspection_invalid_permission()
    test_submit_inspection_missing_fields()
    
    print_separator("测试完成")
    print("✅ 所有检验API测试已完成！")
    print("\n📝 注意事项：")
    print("1. 确保Flask应用正在运行 (python app.py)")
    print("2. 确保数据库已初始化 (python init_db.py)")
    print("3. 区块链功能需要配置相应的私钥和网络")
    print("4. 某些测试可能需要手动清理数据库")

if __name__ == "__main__":
    run_all_tests() 