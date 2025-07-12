# 职责：处理HTTP请求响应，参数验证，调用业务逻辑
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from models.batch import Batch
from models.user import User
from services.batch_service import BatchService
from extensions import db

batch_bp = Blueprint('batch', __name__)

@batch_bp.route('', methods=['POST'])
@jwt_required()
def create_batch():
    """
    创建批次
    POST /batches
    """
    try:
        # 1. 获取当前用户信息
        current_user_id = get_jwt_identity()
        jwt_claims = get_jwt()
        user_role = jwt_claims.get('role')
        
        # 2. 权限验证 - 只有producer能创建批次
        if user_role != 'producer':
            return jsonify({
                'error': 'Access denied',
                'message': 'Only producers can create batches'
            }), 403
        
        # 3. 获取请求数据
        data = request.get_json()
        if not data:
            return jsonify({
                'error': 'Invalid request',
                'message': 'Request body is required'
            }), 400
        
        if 'metadata' not in data:
            return jsonify({
                'error': 'Invalid request',
                'message': 'metadata is required'
            }), 400
        
        metadata = data['metadata']
        
        # 4. 使用BatchService进行元数据校验
        validation_result = BatchService.validate_metadata(metadata)
        
        if not validation_result['valid']:
            return jsonify({
                'error': 'Validation failed',
                'message': 'Invalid metadata',
                'details': validation_result['errors']
            }), 400
        
        # 5. 如果有警告，记录日志（可选）
        if validation_result['warnings']:
            print(f"⚠️ Batch creation warnings: {validation_result['warnings']}")
        
        # 6. 自动生成批次编号（如果没有提供）
        if not metadata.get('batchNumber'):
            metadata['batchNumber'] = BatchService.get_next_batch_number()
        
        # 7. 创建批次
        batch = Batch.from_dict({'metadata': metadata}, owner_id=int(current_user_id))
        
        # 8. 保存到数据库
        db.session.add(batch)
        db.session.commit()
        
        # 9. 返回成功响应（包含警告信息）
        response_data = {
            'batchId': batch.id,
            'message': 'Batch created successfully',
            'status': batch.status,
            'batchNumber': batch.batch_number
        }
        
        if validation_result['warnings']:
            response_data['warnings'] = validation_result['warnings']
        
        return jsonify(response_data), 201
        
    except ValueError as e:
        db.session.rollback()
        return jsonify({
            'error': 'Validation error',
            'message': str(e)
        }), 400
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'error': 'Internal server error',
            'message': 'Failed to create batch'
        }), 500


@batch_bp.route('/<int:batch_id>', methods=['GET'])
def get_batch(batch_id):
    """
    查询批次详情
    GET /batches/{id}
    """
    try:
        # 1. 查询批次
        batch = Batch.query.get(batch_id)
        
        if not batch:
            return jsonify({
                'error': 'Batch not found',
                'message': f'No batch found with ID {batch_id}'
            }), 404
        
        # 2. 获取批次数据
        batch_data = batch.to_dict()
        
        # 3. 添加状态显示信息（使用BatchService）
        status_info = BatchService.get_status_display_info(batch.status)
        batch_data['statusInfo'] = status_info
        
        # 4. 添加批次摘要信息（使用BatchService）
        summary = BatchService.calculate_batch_summary(batch_data['metadata'])
        batch_data['summary'] = summary
        
        return jsonify(batch_data), 200
        
    except Exception as e:
        return jsonify({
            'error': 'Internal server error',
            'message': 'Failed to retrieve batch'
        }), 500


@batch_bp.route('', methods=['GET'])
def list_batches():
    """
    查询批次列表
    GET /batches
    """
    try:
        # 获取查询参数
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        status = request.args.get('status')
        
        # 构建查询
        query = Batch.query
        
        # 状态过滤
        if status:
            # 使用BatchService验证状态有效性
            if status not in BatchService.VALID_STATUSES:
                return jsonify({
                    'error': 'Invalid status',
                    'message': f'Valid statuses: {", ".join(BatchService.VALID_STATUSES)}'
                }), 400
            query = query.filter_by(status=status)
        
        # 分页查询
        batches = query.paginate(
            page=page, 
            per_page=per_page, 
            error_out=False
        )
        
        # 为每个批次添加额外信息
        batch_list = []
        for batch in batches.items:
            batch_data = batch.to_dict()
            # 添加状态显示信息
            batch_data['statusInfo'] = BatchService.get_status_display_info(batch.status)
            batch_list.append(batch_data)
        
        return jsonify({
            'batches': batch_list,
            'pagination': {
                'page': batches.page,
                'per_page': batches.per_page,
                'total': batches.total,
                'pages': batches.pages
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            'error': 'Internal server error',
            'message': 'Failed to retrieve batches'
        }), 500


@batch_bp.route('/<int:batch_id>/status', methods=['PUT'])
@jwt_required()
def update_batch_status(batch_id):
    """
    更新批次状态
    PUT /batches/{id}/status
    """
    try:
        # 1. 获取当前用户信息
        current_user_id = get_jwt_identity()
        jwt_claims = get_jwt()
        user_role = jwt_claims.get('role')
        
        # 2. 查询批次
        batch = Batch.query.get(batch_id)
        if not batch:
            return jsonify({
                'error': 'Batch not found',
                'message': f'No batch found with ID {batch_id}'
            }), 404
        
        # 3. 权限验证
        if user_role == 'producer' and batch.owner_id != int(current_user_id):
            return jsonify({
                'error': 'Access denied',
                'message': 'You can only update your own batches'
            }), 403
        
        # 4. 获取新状态
        data = request.get_json()
        if not data or 'status' not in data:
            return jsonify({
                'error': 'Invalid request',
                'message': 'status is required'
            }), 400
        
        new_status = data['status']
        
        # 5. 使用BatchService验证状态转换
        transition_result = BatchService.validate_status_transition(batch.status, new_status)
        
        if not transition_result['valid']:
            return jsonify({
                'error': 'Invalid status transition',
                'message': transition_result['error']
            }), 400
        
        # 6. 更新状态
        old_status = batch.status
        batch.status = new_status
        db.session.commit()
        
        # 7. 获取状态显示信息
        status_info = BatchService.get_status_display_info(new_status)
        
        return jsonify({
            'message': 'Batch status updated successfully',
            'batchId': batch.id,
            'oldStatus': old_status,
            'newStatus': new_status,
            'statusInfo': status_info
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'error': 'Internal server error',
            'message': 'Failed to update batch status'
        }), 500