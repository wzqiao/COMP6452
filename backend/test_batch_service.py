#!/usr/bin/env python3
"""
BatchService 测试脚本
测试元数据校验和状态更新功能
"""

from services.batch_service import BatchService
import json

def test_metadata_validation():
    """测试元数据校验功能"""
    print("📋 测试元数据校验功能")
    print("=" * 50)
    
    # 1. 测试正常数据
    print("\n✅ 测试正常数据:")
    valid_metadata = {
        "productName": "有机苹果",
        "origin": "山东烟台",
        "quantity": "100",
        "unit": "kg",
        "harvestDate": "2025-01-10",
        "expiryDate": "2025-01-25",
        "totalWeightKg": 100,
        "organic": True,
        "import": False
    }
    
    result = BatchService.validate_metadata(valid_metadata)
    print(f"校验结果: {json.dumps(result, indent=2, ensure_ascii=False)}")
    
    # 2. 测试缺少必填字段
    print("\n❌ 测试缺少必填字段:")
    invalid_metadata = {
        "productName": "苹果",
        "quantity": "100"
        # 缺少 origin 和 unit
    }
    
    result = BatchService.validate_metadata(invalid_metadata)
    print(f"校验结果: {json.dumps(result, indent=2, ensure_ascii=False)}")
    
    # 3. 测试格式错误
    print("\n❌ 测试格式错误:")
    format_error_metadata = {
        "productName": "苹果",
        "origin": "产地",
        "quantity": 100,  # 应该是字符串
        "unit": "kg",
        "harvestDate": "2025/01/10",  # 错误格式
        "expiryDate": "2024-01-25",   # 过期日期在过去
        "totalWeightKg": -10,         # 负数
        "organic": "yes"              # 应该是布尔值
    }
    
    result = BatchService.validate_metadata(format_error_metadata)
    print(f"校验结果: {json.dumps(result, indent=2, ensure_ascii=False)}")
    
    # 4. 测试业务规则警告
    print("\n⚠️ 测试业务规则警告:")
    warning_metadata = {
        "productName": "长期保存产品",
        "origin": "某地",
        "quantity": "50",
        "unit": "kg",
        "harvestDate": "2025-01-01",
        "expiryDate": "2026-01-01",  # 保质期1年，会产生警告
        "totalWeightKg": 100,        # 与数量不一致，会产生警告
        "organic": True,
        "import": False
    }
    
    result = BatchService.validate_metadata(warning_metadata)
    print(f"校验结果: {json.dumps(result, indent=2, ensure_ascii=False)}")

def test_status_transitions():
    """测试状态转换功能"""
    print("\n\n🔄 测试状态转换功能")
    print("=" * 50)
    
    # 测试合法转换
    print("\n✅ 测试合法转换:")
    transitions = [
        ("pending", "inspected"),
        ("inspected", "approved"),
        ("inspected", "rejected")
    ]
    
    for current, new in transitions:
        result = BatchService.validate_status_transition(current, new)
        print(f"{current} -> {new}: {result}")
    
    # 测试非法转换
    print("\n❌ 测试非法转换:")
    invalid_transitions = [
        ("pending", "approved"),    # 跳过检验
        ("approved", "rejected"),   # 最终状态不能更改
        ("rejected", "approved"),   # 最终状态不能更改
        ("pending", "invalid")      # 无效状态
    ]
    
    for current, new in invalid_transitions:
        result = BatchService.validate_status_transition(current, new)
        print(f"{current} -> {new}: {result}")

def test_utility_functions():
    """测试工具函数"""
    print("\n\n🛠️ 测试工具函数")
    print("=" * 50)
    
    # 测试批次编号生成
    print("\n📝 测试批次编号生成:")
    batch_number = BatchService.get_next_batch_number()
    print(f"生成的批次编号: {batch_number}")
    
    # 测试批次摘要计算
    print("\n📊 测试批次摘要计算:")
    metadata = {
        "productName": "有机苹果",
        "origin": "山东烟台",
        "quantity": "100",
        "unit": "kg",
        "harvestDate": "2025-01-10",
        "expiryDate": "2025-01-25",
        "organic": True,
        "import": False
    }
    
    summary = BatchService.calculate_batch_summary(metadata)
    print(f"批次摘要: {json.dumps(summary, indent=2, ensure_ascii=False)}")
    
    # 测试状态显示信息
    print("\n🎨 测试状态显示信息:")
    statuses = ["pending", "inspected", "approved", "rejected"]
    for status in statuses:
        info = BatchService.get_status_display_info(status)
        print(f"{status}: {info}")

def main():
    print("🚀 BatchService 功能测试")
    print("按照队友设计：辅助元数据校验、状态更新")
    
    try:
        test_metadata_validation()
        test_status_transitions()
        test_utility_functions()
        
        print("\n" + "=" * 50)
        print("🎉 所有测试完成！BatchService 功能正常")
        
    except Exception as e:
        print(f"\n❌ 测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 