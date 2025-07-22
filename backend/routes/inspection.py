# -*- coding: utf-8 -*-
"""
检验结果API路由
处理检验相关的HTTP请求
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime
import logging

from models.batch import Batch
from models.inspection import Inspection
from models.user import User
from extensions import db
from web3 import Web3
from deploy_config import (
    get_network_config, 
    get_contract_address, 
    get_contract_abi, 
    DEVELOPMENT_PRIVATE_KEYS 
)


# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 创建蓝图
inspection_bp = Blueprint('inspection', __name__)

@inspection_bp.route('/batches/<int:batch_id>/inspection', methods=['POST'])
@jwt_required()
def submit_inspection(batch_id):
    """
    Submit inspection result for a batch
    
    POST /batches/{id}/inspection
    """
    try:
        # 1. User validation
        current_user_id = get_jwt_identity()
        current_user = User.query.get(current_user_id)
        
        if not current_user:
            return jsonify({'error': 'User not found'}), 401
        
        if current_user.role != 'inspector':
            return jsonify({'error': 'Access denied. Only inspectors can submit inspection results'}), 403
        
        # 2. Batch validation
        batch = Batch.query.get(batch_id)
        if not batch:
            return jsonify({'error': 'Batch not found'}), 404
        
        # Allow both pending and inspected status batches to submit inspection results
        allowed_statuses = ['pending', 'inspected']
        if batch.status not in allowed_statuses:
            return jsonify({'error': f'Batch status is {batch.status}. Only pending or inspected batches can be inspected'}), 400
        
        # 3. Request data validation
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'Request data is empty'}), 400
        
        if 'result' not in data or not data['result']:
            return jsonify({'error': 'Missing required field: result'}), 400
        
        valid_results = ['passed', 'failed', 'needs_recheck']
        if data['result'] not in valid_results:
            return jsonify({'error': f'Invalid inspection result: {data["result"]}'}), 400
        
        # 4. Process data
        insp_date = data.get('insp_date')
        if insp_date:
            try:
                insp_date = datetime.fromisoformat(insp_date.replace('Z', '+00:00'))
                # Convert to local timezone (Sydney)
                import pytz
                utc = pytz.UTC
                sydney_tz = pytz.timezone('Australia/Sydney')
                if insp_date.tzinfo is None:
                    insp_date = utc.localize(insp_date)
                insp_date = insp_date.astimezone(sydney_tz)
            except ValueError:
                return jsonify({'error': 'Invalid inspection date format'}), 400
        else:
            # Use Sydney timezone for current time
            import pytz
            sydney_tz = pytz.timezone('Australia/Sydney')
            insp_date = datetime.now(sydney_tz)
        
        file_url = data.get('file_url', 'none')
        notes = data.get('notes', '')
        
        # 5. Blockchain operations - must succeed to continue
        blockchain_tx = None
        blockchain_inspection_id = None
        
        # Connect to blockchain
        network_config = get_network_config('testnet')
        w3 = Web3(Web3.HTTPProvider(network_config['rpc_url']))
        
        if not w3.is_connected():
            raise Exception("Failed to connect to blockchain network")
        
        # Get InspectionManager contract instance
        inspection_address = get_contract_address('InspectionManager', 'testnet')
        inspection_abi = get_contract_abi('InspectionManager')
        contract = w3.eth.contract(address=inspection_address, abi=inspection_abi)
        
        # Get private key and account
        private_key = DEVELOPMENT_PRIVATE_KEYS.get('inspector1')
        if not private_key:
            private_key = DEVELOPMENT_PRIVATE_KEYS.get('owner')
        
        if not private_key:
            raise Exception("No private key configured for inspection transactions")
        
        account = w3.eth.account.from_key(private_key)
        gas_price = w3.to_wei('20', 'gwei')
        
        # Step 1: Create inspection record
        create_transaction = contract.functions.createInspection(
            batch_id,
            file_url,
            notes
        ).build_transaction({
            'from': account.address,
            'nonce': w3.eth.get_transaction_count(account.address),
            'gas': 500000,
            'gasPrice': gas_price,
        })
        
        # Sign and send create inspection transaction
        signed_create_txn = w3.eth.account.sign_transaction(create_transaction, private_key)
        create_tx_hash = w3.eth.send_raw_transaction(signed_create_txn.raw_transaction)
        
        # Wait for create transaction confirmation
        create_receipt = w3.eth.wait_for_transaction_receipt(create_tx_hash, timeout=120)
        
        if create_receipt.status != 1:
            raise Exception("Create inspection transaction failed")
        
        # Try to parse event logs to get inspection ID, fallback to contract query if failed
        blockchain_inspection_id = None
        try:
            for log in create_receipt.logs:
                try:
                    decoded_log = contract.events.InspectionCreated().processLog(log)
                    blockchain_inspection_id = decoded_log['args']['inspectionId']
                    break
                except Exception:
                    continue
        except Exception:
            pass
        
        # If event parsing failed, use contract query method to get latest inspection ID
        if not blockchain_inspection_id:
            try:
                total_inspections = contract.functions.getTotalInspections().call()
                blockchain_inspection_id = total_inspections  # Latest created inspection ID
            except Exception:
                blockchain_inspection_id = 1  # Default fallback
        
        # Step 2: Complete inspection record
        result_mapping = {
            'passed': 1,         # InspectionResult.PASSED
            'failed': 2,         # InspectionResult.FAILED  
            'needs_recheck': 3   # InspectionResult.NEEDS_RECHECK
        }
        result_value = result_mapping.get(data['result'], 0)
        
        # Only passed and failed need to complete inspection (needs_recheck stays pending)
        if data['result'] in ['passed', 'failed']:
            # Build complete inspection transaction
            complete_transaction = contract.functions.completeInspection(
                blockchain_inspection_id,
                result_value,
                file_url,
                notes
            ).build_transaction({
                'from': account.address,
                'nonce': w3.eth.get_transaction_count(account.address),
                'gas': 500000,
                'gasPrice': gas_price,
            })
            
            # Sign and send complete inspection transaction
            signed_complete_txn = w3.eth.account.sign_transaction(complete_transaction, private_key)
            complete_tx_hash = w3.eth.send_raw_transaction(signed_complete_txn.raw_transaction)
            
            # Wait for complete transaction confirmation
            complete_receipt = w3.eth.wait_for_transaction_receipt(complete_tx_hash, timeout=120)
            
            if complete_receipt.status != 1:
                raise Exception("Complete inspection transaction failed")
            
            blockchain_tx = complete_tx_hash.hex()
        else:
            # needs_recheck - only create record, don't complete
            blockchain_tx = create_tx_hash.hex()
        
        # 6. Save to database only after blockchain success
        inspection = Inspection(
            batch_id=batch_id,
            inspector_id=current_user_id,
            result=data['result'],
            file_url=file_url,
            notes=notes,
            insp_date=insp_date
        )
        
        # Save blockchain transaction hash
        inspection.blockchain_tx = blockchain_tx
        db.session.add(inspection)
        
        # Update batch status
        old_status = batch.status
        if data['result'] == 'passed':
            batch.status = 'approved'
        elif data['result'] == 'failed':
            batch.status = 'rejected'
        else:  # needs_recheck
            batch.status = 'inspected'
        
        db.session.commit()
        
        # 7. Build response
        response_data = {
            'message': 'Inspection result submitted successfully',
            'inspection': {
                'id': inspection.id,
                'batch_id': inspection.batch_id,
                'inspector_id': inspection.inspector_id,
                'inspector_name': current_user.email,
                'result': inspection.result,
                'file_url': inspection.file_url,
                'notes': inspection.notes,
                'insp_date': inspection.insp_date.isoformat(),
                'blockchain_tx': inspection.blockchain_tx,
                'created_at': inspection.created_at.isoformat()
            },
            'batch': {
                'id': batch.id,
                'batch_number': batch.batch_number,
                'status': batch.status,
                'updated_at': getattr(batch, 'updated_at', batch.created_at).isoformat()
            },
            'blockchain': {
                'success': True,
                'tx_hash': blockchain_tx,
                'inspection_id': blockchain_inspection_id,
                'message': 'Inspection result synced to blockchain and database'
            }
        }
        
        return jsonify(response_data), 201
        
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({'error': 'Database operation failed', 'details': str(e)}), 500
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to submit inspection result', 'message': 'Blockchain or database operation failed', 'details': str(e)}), 500

@inspection_bp.route('/batches/<int:batch_id>/inspections', methods=['GET'])
@jwt_required()
def get_batch_inspections(batch_id):
    """
    获取批次的所有检验记录
    
    GET /batches/{id}/inspections
    """
    try:
        # 获取当前用户
        current_user_id = get_jwt_identity()
        current_user = User.query.get(current_user_id)
        
        if not current_user:
            return jsonify({'error': '用户不存在'}), 401
        
        # 验证批次存在
        batch = Batch.query.get(batch_id)
        if not batch:
            return jsonify({'error': '批次不存在'}), 404
        
        # 权限检查：生产者只能查看自己的批次，检验员可以查看所有批次
        if current_user.role == 'producer' and batch.owner_id != current_user_id:
            return jsonify({'error': '无权查看此批次的检验记录'}), 403
        
        # 获取检验记录
        inspections = Inspection.query.filter_by(batch_id=batch_id).order_by(Inspection.created_at.desc()).all()
        
        # 构建响应
        inspections_data = []
        for inspection in inspections:
            inspector = User.query.get(inspection.inspector_id)
            inspections_data.append({
                'id': inspection.id,
                'inspector_id': inspection.inspector_id,
                'inspector_name': inspector.email if inspector else '未知',
                'result': inspection.result,
                'file_url': inspection.file_url,
                'notes': inspection.notes,
                'insp_date': inspection.insp_date.isoformat(),
                'blockchain_tx': inspection.blockchain_tx,
                'created_at': inspection.created_at.isoformat(),
                'updated_at': getattr(inspection, 'updated_at', inspection.created_at)
            })
        
        return jsonify({
            'batch': {
                'id': batch.id,
                'batch_number': batch.batch_number,
                'product_name': batch.product_name,
                'status': batch.status
            },
            'inspections': inspections_data,
            'total_count': len(inspections_data)
        }), 200
        
    except Exception as e:
        logger.error(f"获取检验记录失败: {str(e)}")
        return jsonify({'error': '获取检验记录失败'}), 500

@inspection_bp.route('/inspections/<int:inspection_id>', methods=['GET'])
@jwt_required()
def get_inspection(inspection_id):
    """
    获取单个检验记录详情
    
    GET /inspections/{id}
    """
    try:
        # 获取当前用户
        current_user_id = get_jwt_identity()
        current_user = User.query.get(current_user_id)
        
        if not current_user:
            return jsonify({'error': '用户不存在'}), 401
        
        # 获取检验记录
        inspection = Inspection.query.get(inspection_id)
        if not inspection:
            return jsonify({'error': '检验记录不存在'}), 404
        
        # 获取关联批次
        batch = Batch.query.get(inspection.batch_id)
        if not batch:
            return jsonify({'error': '关联批次不存在'}), 404
        
        # 权限检查：生产者只能查看自己批次的检验记录，检验员可以查看所有记录
        if current_user.role == 'producer' and batch.owner_id != current_user_id:
            return jsonify({'error': '无权查看此检验记录'}), 403
        
        # 获取检验员信息
        inspector = User.query.get(inspection.inspector_id)
        
        # 构建响应
        response_data = {
            'inspection': {
                'id': inspection.id,
                'batch_id': inspection.batch_id,
                'inspector_id': inspection.inspector_id,
                'inspector_name': inspector.email if inspector else '未知',
                'result': inspection.result,
                'file_url': inspection.file_url,
                'notes': inspection.notes,
                'insp_date': inspection.insp_date.isoformat(),
                'blockchain_tx': inspection.blockchain_tx,
                'created_at': inspection.created_at.isoformat(),
                'updated_at': inspection.updated_at.isoformat()
            },
            'batch': {
                'id': batch.id,
                'batch_number': batch.batch_number,
                'product_name': batch.product_name,
                'origin': batch.origin,
                'status': batch.status
            }
        }
        
        # 如果有区块链记录，尝试获取链上数据
        if inspection.blockchain_tx:
            try:
                blockchain_service = get_blockchain_service()
                if blockchain_service.inspection_manager:
                    # 这里可以添加从区块链获取数据的逻辑
                    # chain_data = blockchain_service.get_inspection_from_chain(inspection_id)
                    response_data['blockchain'] = {
                        'tx_hash': inspection.blockchain_tx,
                        'message': '检验记录已上链'
                    }
            except Exception as e:
                logger.warning(f"获取区块链数据失败: {str(e)}")
        
        return jsonify(response_data), 200
        
    except Exception as e:
        logger.error(f"获取检验记录失败: {str(e)}")
        return jsonify({'error': '获取检验记录失败'}), 500

@inspection_bp.route('/inspections/<int:inspection_id>', methods=['PUT'])
@jwt_required()
def update_inspection(inspection_id):
    """
    更新检验记录
    
    PUT /inspections/{id}
    
    请求体：
    {
        "result": "passed|failed|needs_recheck",
        "file_url": "https://...",
        "notes": "更新的检验备注"
    }
    """
    try:
        # 获取当前用户
        current_user_id = get_jwt_identity()
        current_user = User.query.get(current_user_id)
        
        if not current_user:
            return jsonify({'error': '用户不存在'}), 401
        
        # 验证用户角色
        if current_user.role != 'inspector':
            return jsonify({'error': '只有检验员可以更新检验记录'}), 403
        
        # 获取检验记录
        inspection = Inspection.query.get(inspection_id)
        if not inspection:
            return jsonify({'error': '检验记录不存在'}), 404
        
        # 验证是否为记录创建者
        if inspection.inspector_id != current_user_id:
            return jsonify({'error': '只能更新自己创建的检验记录'}), 403
        
        # 获取请求数据
        data = request.get_json()
        if not data:
            return jsonify({'error': '请求数据为空'}), 400
        
        # 验证检验结果
        if 'result' in data:
            valid_results = ['passed', 'failed', 'needs_recheck']
            if data['result'] not in valid_results:
                return jsonify({'error': f'无效的检验结果: {data["result"]}'}), 400
        
        # 获取关联批次
        batch = Batch.query.get(inspection.batch_id)
        if not batch:
            return jsonify({'error': '关联批次不存在'}), 404
        
        # 更新检验记录
        old_result = inspection.result
        
        if 'result' in data:
            inspection.result = data['result']
        if 'file_url' in data:
            inspection.file_url = data['file_url']
        if 'notes' in data:
            inspection.notes = data['notes']
        
        inspection.updated_at = datetime.utcnow()
        
        # 如果检验结果发生变化，更新批次状态
        if 'result' in data and data['result'] != old_result:
            if data['result'] == 'passed':
                batch.status = 'approved'
            elif data['result'] == 'failed':
                batch.status = 'rejected'
            else:  # needs_recheck
                batch.status = 'inspected'
        
        # 区块链更新操作
        if inspection.blockchain_tx:
            try:
                blockchain_service = get_blockchain_service()
                if blockchain_service.inspection_manager and blockchain_service.account:
                    # 这里可以添加区块链更新逻辑
                    # blockchain_service.update_inspection_on_chain(...)
                    pass
            except Exception as e:
                logger.warning(f"区块链更新失败: {str(e)}")
        
        # 提交数据库事务
        db.session.commit()
        
        # 构建响应
        response_data = {
            'message': '检验记录更新成功',
            'inspection': {
                'id': inspection.id,
                'batch_id': inspection.batch_id,
                'inspector_id': inspection.inspector_id,
                'inspector_name': current_user.email,
                'result': inspection.result,
                'file_url': inspection.file_url,
                'notes': inspection.notes,
                'insp_date': inspection.insp_date.isoformat(),
                'blockchain_tx': inspection.blockchain_tx,
                'created_at': inspection.created_at.isoformat(),
                'updated_at': inspection.updated_at.isoformat()
            },
            'batch': {
                'id': batch.id,
                'batch_number': batch.batch_number,
                'status': batch.status,
                'updated_at': batch.updated_at.isoformat()
            }
        }
        
        return jsonify(response_data), 200
        
    except SQLAlchemyError as e:
        db.session.rollback()
        logger.error(f"数据库操作失败: {str(e)}")
        return jsonify({'error': '数据库操作失败'}), 500
    except Exception as e:
        db.session.rollback()
        logger.error(f"更新检验记录失败: {str(e)}")
        return jsonify({'error': '更新检验记录失败'}), 500

@inspection_bp.route('/inspections', methods=['GET'])
@jwt_required()
def get_inspections():
    """
    获取检验记录列表
    
    GET /inspections?page=1&per_page=10&result=passed&inspector_id=1
    """
    try:
        # 获取当前用户
        current_user_id = get_jwt_identity()
        current_user = User.query.get(current_user_id)
        
        if not current_user:
            return jsonify({'error': '用户不存在'}), 401
        
        # 获取查询参数
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 10, type=int), 100)
        result_filter = request.args.get('result')
        inspector_id = request.args.get('inspector_id', type=int)
        
        # 构建查询
        query = Inspection.query
        
        # 权限过滤：生产者只能查看自己批次的检验记录
        if current_user.role == 'producer':
            # 获取用户的批次ID列表
            user_batch_ids = [batch.id for batch in Batch.query.filter_by(owner_id=current_user_id).all()]
            query = query.filter(Inspection.batch_id.in_(user_batch_ids))
        
        # 结果过滤
        if result_filter:
            query = query.filter(Inspection.result == result_filter)
        
        # 检验员过滤
        if inspector_id:
            query = query.filter(Inspection.inspector_id == inspector_id)
        
        # 分页
        query = query.order_by(Inspection.created_at.desc())
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        inspections = pagination.items
        
        # 构建响应
        inspections_data = []
        for inspection in inspections:
            inspector = User.query.get(inspection.inspector_id)
            batch = Batch.query.get(inspection.batch_id)
            
            inspections_data.append({
                'id': inspection.id,
                'batch_id': inspection.batch_id,
                'batch_number': batch.batch_number if batch else '未知',
                'product_name': batch.product_name if batch else '未知',
                'inspector_id': inspection.inspector_id,
                'inspector_name': inspector.email if inspector else '未知',
                'result': inspection.result,
                'file_url': inspection.file_url,
                'notes': inspection.notes,
                'insp_date': inspection.insp_date.isoformat(),
                'blockchain_tx': inspection.blockchain_tx,
                'created_at': inspection.created_at.isoformat()
            })
        
        return jsonify({
            'inspections': inspections_data,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': pagination.total,
                'pages': pagination.pages,
                'has_prev': pagination.has_prev,
                'has_next': pagination.has_next
            }
        }), 200
        
    except Exception as e:
        logger.error(f"获取检验记录列表失败: {str(e)}")
        return jsonify({'error': '获取检验记录列表失败'}), 500