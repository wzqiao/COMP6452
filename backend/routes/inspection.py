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
from services.blockchain import get_blockchain_service, BlockchainError, ContractNotFoundError
from extensions import db

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 创建蓝图
inspection_bp = Blueprint('inspection', __name__)

@inspection_bp.route('/batches/<int:batch_id>/inspection', methods=['POST'])
@jwt_required()
def submit_inspection(batch_id):
    """
    提交检验结果
    
    POST /batches/{id}/inspection
    
    请求体：
    {
        "result": "passed|failed|needs_recheck",
        "file_url": "https://...",
        "notes": "检验备注",
        "insp_date": "2024-01-01T10:00:00" (可选，默认当前时间)
    }
    """
    try:
        # 获取当前用户
        current_user_id = get_jwt_identity()
        current_user = User.query.get(current_user_id)
        
        if not current_user:
            return jsonify({'error': '用户不存在'}), 401
        
        # 验证用户角色（检验员）
        if current_user.role != 'inspector':
            return jsonify({'error': '只有检验员可以提交检验结果'}), 403
        
        # 验证批次存在
        batch = Batch.query.get(batch_id)
        if not batch:
            return jsonify({'error': '批次不存在'}), 404
        
        # 验证批次状态
        if batch.status != 'pending':
            return jsonify({'error': f'批次状态为 {batch.status}，无法提交检验结果'}), 400
        
        # 获取请求数据
        data = request.get_json()
        if not data:
            return jsonify({'error': '请求数据为空'}), 400
        
        # 验证必填字段
        required_fields = ['result', 'file_url']
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({'error': f'缺少必填字段: {field}'}), 400
        
        # 验证检验结果
        valid_results = ['passed', 'failed', 'needs_recheck']
        if data['result'] not in valid_results:
            return jsonify({'error': f'无效的检验结果: {data["result"]}'}), 400
        
        # 解析检验日期
        insp_date = data.get('insp_date')
        if insp_date:
            try:
                insp_date = datetime.fromisoformat(insp_date.replace('Z', '+00:00'))
            except ValueError:
                return jsonify({'error': '无效的检验日期格式'}), 400
        else:
            insp_date = datetime.utcnow()
        
        # 创建检验记录
        inspection = Inspection(
            batch_id=batch_id,
            inspector_id=current_user_id,
            result=data['result'],
            file_url=data['file_url'],
            notes=data.get('notes', ''),
            insp_date=insp_date
        )
        
        # 区块链上链操作
        blockchain_tx = None
        blockchain_inspection_id = None
        
        try:
            # 获取区块链服务
            blockchain_service = get_blockchain_service()
            
            # 检查是否有区块链账户
            if blockchain_service.account:
                # 检查检验员权限
                inspector_address = blockchain_service.get_account_address()
                if not blockchain_service.is_authorized_inspector(inspector_address):
                    logger.warning(f"检验员 {inspector_address} 未在区块链上授权")
                    return jsonify({'error': '检验员未在区块链上授权'}), 403
                
                # 如果批次有区块链记录，尝试上链
                if batch.blockchain_tx:
                    try:
                        # 创建检验记录上链
                        blockchain_tx, blockchain_inspection_id = blockchain_service.create_inspection_on_chain(
                            batch_id=batch_id,  # 使用数据库ID作为区块链批次ID
                            file_url=data['file_url'],
                            notes=data.get('notes', '')
                        )
                        
                        # 如果检验结果是通过或失败，立即完成检验
                        if data['result'] in ['passed', 'failed']:
                            blockchain_service.complete_inspection_on_chain(
                                inspection_id=blockchain_inspection_id,
                                result=data['result'],
                                file_url=data['file_url'],
                                notes=data.get('notes', '')
                            )
                        
                        inspection.blockchain_tx = blockchain_tx
                        logger.info(f"检验记录已上链: {blockchain_tx}")
                        
                    except (BlockchainError, ContractNotFoundError) as e:
                        logger.error(f"区块链操作失败: {str(e)}")
                        # 区块链操作失败不影响数据库操作，继续执行
                        inspection.blockchain_tx = None
                else:
                    logger.info("批次未上链，跳过区块链操作")
            else:
                logger.info("未配置区块链账户，跳过区块链操作")
                
        except Exception as e:
            logger.error(f"区块链操作异常: {str(e)}")
            # 区块链操作失败不影响数据库操作
            inspection.blockchain_tx = None
        
        # 保存检验记录到数据库
        db.session.add(inspection)
        
        # 更新批次状态
        if data['result'] == 'passed':
            batch.status = 'approved'
        elif data['result'] == 'failed':
            batch.status = 'rejected'
        else:  # needs_recheck
            batch.status = 'inspected'
        
        # 提交数据库事务
        db.session.commit()
        
        # 构建响应
        response_data = {
            'message': '检验结果提交成功',
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
                'updated_at': batch.updated_at.isoformat()
            }
        }
        
        if blockchain_tx:
            response_data['blockchain'] = {
                'tx_hash': blockchain_tx,
                'inspection_id': blockchain_inspection_id,
                'message': '检验结果已上链'
            }
        
        return jsonify(response_data), 201
        
    except SQLAlchemyError as e:
        db.session.rollback()
        logger.error(f"数据库操作失败: {str(e)}")
        return jsonify({'error': '数据库操作失败'}), 500
    except Exception as e:
        db.session.rollback()
        logger.error(f"提交检验结果失败: {str(e)}")
        return jsonify({'error': '提交检验结果失败'}), 500

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
                'updated_at': inspection.updated_at.isoformat()
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
