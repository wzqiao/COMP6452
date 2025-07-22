# -*- coding: utf-8 -*-
"""
更新的合约数据同步脚本
适配实际的合约数据格式
"""

import json
from datetime import datetime
from app import create_app
from extensions import db
from blockchain import get_blockchain_service, BlockchainError

# 假设你有这些模型，如果没有需要先检查
try:
    from models import Batch, User, Inspection
except ImportError:
    print("❌ 找不到模型文件，请检查 models.py 是否存在")
    exit(1)

def convert_timestamp_to_datetime(timestamp):
    """转换时间戳为datetime对象"""
    if timestamp and timestamp > 0:
        return datetime.fromtimestamp(timestamp)
    return None

def find_or_create_user(wallet_address, email_prefix, role):
    """查找或创建用户"""
    if wallet_address:
        user = User.query.filter_by(wallet=wallet_address).first()
        if user:
            return user
    
    # 创建新用户
    user = User(
        email=f"{email_prefix}_{wallet_address[:8] if wallet_address else 'unknown'}@blockchain.local",
        password_hash="contract_generated",
        role=role,
        wallet=wallet_address or ""
    )
    db.session.add(user)
    db.session.flush()
    return user

def sync_batches_from_contract():
    """从合约同步批次数据"""
    print("🔄 开始同步批次数据...")
    
    try:
        blockchain_service = get_blockchain_service()
        
        # 获取合约中的总批次数
        if not blockchain_service.batch_registry:
            print("❌ BatchRegistry合约未找到")
            return False
        
        total_batches = blockchain_service.batch_registry.functions.getTotalBatches().call()
        print(f"📦 合约中发现 {total_batches} 个批次")
        
        synced_count = 0
        updated_count = 0
        
        for batch_id in range(1, total_batches + 1):
            try:
                # 从合约获取批次数据
                batch_raw = blockchain_service.batch_registry.functions.getBatch(batch_id).call()
                
                # 状态映射
                status_map = {0: 'pending', 1: 'inspected', 2: 'approved', 3: 'rejected'}
                
                # 解析批次数据（根据你的合约结构）
                batch_data = {
                    'id': batch_raw[0],
                    'batch_number': batch_raw[1],
                    'product_name': batch_raw[2],
                    'origin': batch_raw[3],
                    'quantity': str(batch_raw[4]),
                    'unit': batch_raw[5],
                    'harvest_date': convert_timestamp_to_datetime(batch_raw[6]),
                    'expiry_date': convert_timestamp_to_datetime(batch_raw[7]),
                    'status': status_map.get(batch_raw[8], 'pending'),  # 转换为字符串状态
                    'owner': batch_raw[9],
                    'timestamp': convert_timestamp_to_datetime(batch_raw[10]),
                    'exists': batch_raw[11] if len(batch_raw) > 11 else True
                }
                
                if not batch_data['exists']:
                    continue
                
                print(f"📋 处理批次: {batch_data['batch_number']} - {batch_data['product_name']}")
                
                # 检查批次是否已存在
                existing_batch = Batch.query.filter_by(
                    batch_number=batch_data['batch_number']
                ).first()
                
                # 查找或创建拥有者
                owner_user = find_or_create_user(
                    batch_data['owner'], 
                    "producer", 
                    "producer"
                )
                
                if existing_batch:
                    # 更新现有批次
                    existing_batch.product_name = batch_data['product_name']
                    existing_batch.origin = batch_data['origin']
                    existing_batch.quantity = batch_data['quantity']
                    existing_batch.unit = batch_data['unit']
                    existing_batch.harvest_date = batch_data['harvest_date'].date() if batch_data['harvest_date'] else None
                    existing_batch.expiry_date = batch_data['expiry_date'].date() if batch_data['expiry_date'] else None
                    existing_batch.status = batch_data['status']
                    existing_batch.owner_id = owner_user.id
                    existing_batch.blockchain_tx = None  # 设置为空，显示"none"
                    
                    updated_count += 1
                    print(f"   ✏️  更新现有批次")
                else:
                    # 创建新批次
                    new_batch = Batch(
                        batch_number=batch_data['batch_number'],
                        product_name=batch_data['product_name'],
                        origin=batch_data['origin'],
                        quantity=batch_data['quantity'],
                        unit=batch_data['unit'],
                        harvest_date=batch_data['harvest_date'].date() if batch_data['harvest_date'] else None,
                        expiry_date=batch_data['expiry_date'].date() if batch_data['expiry_date'] else None,
                        status=batch_data['status'],
                        owner_id=owner_user.id,
                        created_at=batch_data['timestamp'] or datetime.now(),
                        blockchain_tx=None,  # 设置为空，显示"none"
                        # 设置一些默认值
                        organic=True,
                        import_product=False,
                        total_weight_kg=100
                    )
                    
                    db.session.add(new_batch)
                    synced_count += 1
                    print(f"   ✅ 创建新批次")
                
            except Exception as e:
                print(f"   ❌ 处理批次 {batch_id} 失败: {str(e)}")
                continue
        
        # 提交所有更改
        db.session.commit()
        print(f"🎉 批次同步完成！")
        print(f"   📦 新增: {synced_count} 个批次")
        print(f"   ✏️  更新: {updated_count} 个批次")
        
        return True
        
    except Exception as e:
        print(f"❌ 同步批次失败: {str(e)}")
        db.session.rollback()
        return False

def sync_inspections_from_contract():
    """从合约同步检验数据"""
    print("🔄 开始同步检验数据...")
    
    try:
        blockchain_service = get_blockchain_service()
        
        if not blockchain_service.inspection_manager:
            print("❌ InspectionManager合约未找到")
            return False
        
        total_inspections = blockchain_service.inspection_manager.functions.getTotalInspections().call()
        print(f"🔍 合约中发现 {total_inspections} 个检验记录")
        
        synced_count = 0
        updated_count = 0
        
        for inspection_id in range(1, total_inspections + 1):
            try:
                # 从合约获取检验数据
                inspection_raw = blockchain_service.inspection_manager.functions.getInspection(inspection_id).call()
                
                # 结果映射
                result_map = {0: 'pending', 1: 'passed', 2: 'failed', 3: 'needs_recheck'}
                
                inspection_data = {
                    'id': inspection_raw[0],
                    'batch_id': inspection_raw[1],
                    'inspector': inspection_raw[2],
                    'result': result_map.get(inspection_raw[3], 'pending'),  # 转换为字符串结果
                    'file_url': inspection_raw[4],
                    'notes': inspection_raw[5],
                    'inspection_date': convert_timestamp_to_datetime(inspection_raw[6]),
                    'created_at': convert_timestamp_to_datetime(inspection_raw[7]),
                    'updated_at': convert_timestamp_to_datetime(inspection_raw[8]),
                    'exists': inspection_raw[9] if len(inspection_raw) > 9 else True
                }
                
                if not inspection_data['exists']:
                    continue
                
                print(f"🔍 处理检验: 批次ID {inspection_data['batch_id']}")
                
                # 查找对应的数据库批次（通过区块链批次ID查找）
                # 先尝试通过批次号查找（因为现在blockchain_tx为None）
                batch = None
                
                # 方法1: 通过合约数据查找对应的批次
                batch_raw_for_inspection = blockchain_service.batch_registry.functions.getBatch(inspection_data['batch_id']).call()
                batch_number = batch_raw_for_inspection[1]  # 获取批次号
                batch = Batch.query.filter_by(batch_number=batch_number).first()
                
                if not batch:
                    print(f"   ❌ 找不到对应的批次 (区块链ID: {inspection_data['batch_id']}, 批次号: {batch_number})")
                    continue
                
                # 查找或创建检验员
                inspector_user = find_or_create_user(
                    inspection_data['inspector'],
                    "inspector",
                    "inspector"
                )
                
                # 检查检验是否已存在
                existing_inspection = Inspection.query.filter_by(
                    batch_id=batch.id,
                    inspector_id=inspector_user.id
                ).first()
                
                if existing_inspection:
                    # 更新现有检验
                    existing_inspection.result = inspection_data['result']
                    existing_inspection.file_url = inspection_data['file_url']
                    existing_inspection.notes = inspection_data['notes']
                    existing_inspection.insp_date = inspection_data['inspection_date']
                    existing_inspection.blockchain_tx = None  # 设置为空
                    
                    updated_count += 1
                    print(f"   ✏️  更新现有检验")
                else:
                    # 创建新检验
                    new_inspection = Inspection(
                        batch_id=batch.id,
                        inspector_id=inspector_user.id,
                        result=inspection_data['result'],
                        file_url=inspection_data['file_url'],
                        notes=inspection_data['notes'],
                        insp_date=inspection_data['inspection_date'],
                        created_at=inspection_data['created_at'] or datetime.now(),
                        blockchain_tx=None  # 设置为空
                    )
                    
                    db.session.add(new_inspection)
                    synced_count += 1
                    print(f"   ✅ 创建新检验")
                
            except Exception as e:
                print(f"   ❌ 处理检验 {inspection_id} 失败: {str(e)}")
                continue
        
        # 提交所有更改
        db.session.commit()
        print(f"🎉 检验同步完成！")
        print(f"   🔍 新增: {synced_count} 个检验")
        print(f"   ✏️  更新: {updated_count} 个检验")
        
        return True
        
    except Exception as e:
        print(f"❌ 同步检验失败: {str(e)}")
        db.session.rollback()
        return False

def clear_database():
    """清空数据库（可选）"""
    print("⚠️  清空数据库...")
    try:
        # 删除检验记录
        Inspection.query.delete()
        # 删除批次记录
        Batch.query.delete()
        # 删除自动生成的用户（保留手动创建的）
        User.query.filter(User.email.like('%@blockchain.local')).delete()
        
        db.session.commit()
        print("✅ 数据库已清空")
        return True
    except Exception as e:
        print(f"❌ 清空数据库失败: {str(e)}")
        db.session.rollback()
        return False

def main():
    """主函数"""
    print("🚀 智能合约数据同步工具")
    print("=" * 50)
    
    app = create_app()
    with app.app_context():
        
        # 询问是否清空数据库
        choice = input("是否清空现有数据库? (y/N): ").lower().strip()
        if choice == 'y':
            if not clear_database():
                return
        
        print("\n开始同步...")
        
        # 同步批次数据
        batch_success = sync_batches_from_contract()
        
        # 同步检验数据
        inspection_success = sync_inspections_from_contract()
        
        if batch_success and inspection_success:
            print("\n✅ 所有数据同步完成!")
        else:
            print("\n⚠️  部分数据同步失败，请检查错误信息")

if __name__ == "__main__":
    main()