# Responsibility: Handle HTTP request/response, parameter validation, call business logic
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from models.batch import Batch
from models.user import User
from services.batch_service import BatchService
from extensions import db
from web3 import Web3
from deploy_config import get_network_config, get_contract_address, get_contract_abi
import time
from models.inspection import Inspection

batch_bp = Blueprint('batch', __name__)

@batch_bp.route('', methods=['POST'])
@jwt_required()
def create_batch():
    """
    Create batch
    POST /batches
    """
    try:
        # 1. Get current user information
        current_user_id = get_jwt_identity()
        jwt_claims = get_jwt()
        user_role = jwt_claims.get('role')
        
        # 2. Permission verification - only producer can create batches
        if user_role != 'producer':
            return jsonify({
                'error': 'Access denied',
                'message': 'Only producers can create batches'
            }), 403
        
        # 3. Get request data
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
        
        # 4. Use BatchService to validate metadata
        validation_result = BatchService.validate_metadata(metadata)
        
        if not validation_result['valid']:
            return jsonify({
                'error': 'Validation failed',
                'message': 'Invalid metadata',
                'details': validation_result['errors']
            }), 400
        
        # 5. If there are warnings, record the log (optional)
        if validation_result['warnings']:
            print(f"⚠️ Batch creation warnings: {validation_result['warnings']}")
        
        # 6. Automatically generate batch number (if not provided)
        if not metadata.get('batchNumber'):
            metadata['batchNumber'] = BatchService.get_next_batch_number()
        
        # 🔧 7. Blockchain integration - create batch to blockchain (must succeed)
        blockchain_tx = None
        blockchain_owner = None
        
        print(f"Creating batch on blockchain: {metadata['batchNumber']}")
        
        # Connect to blockchain
        network_config = get_network_config('testnet')
        w3 = Web3(Web3.HTTPProvider(network_config['rpc_url']))
        
        if not w3.is_connected():
            raise Exception("Failed to connect to blockchain network")
        
        # Get contract instance
        batch_address = get_contract_address('BatchRegistry', 'testnet')
        batch_abi = get_contract_abi('BatchRegistry')
        contract = w3.eth.contract(address=batch_address, abi=batch_abi)
        
        # Prepare contract parameters
        batch_number = metadata['batchNumber']
        product_name = metadata['productName']
        origin = metadata['origin']
        quantity = int(float(metadata['quantity']))
        unit = metadata['unit']
        
        # Process date - keep the original database format, but convert to timestamp for the contract
        harvest_date = convert_date_for_contract(metadata.get('harvestDate'))
        expiry_date = convert_date_for_contract(metadata.get('expiryDate'))
        
        # Get private key
        from deploy_config import DEVELOPMENT_PRIVATE_KEYS
        private_key = DEVELOPMENT_PRIVATE_KEYS.get('owner')
        
        if not private_key:
            raise Exception("No private key configured for blockchain transactions")
        
        # Create account
        account = w3.eth.account.from_key(private_key)
        blockchain_owner = account.address  # Save blockchain owner address
        
        # Build transaction
        transaction = contract.functions.createBatch(
            batch_number,
            product_name,
            origin,
            quantity,
            unit,
            harvest_date,
            expiry_date
        ).build_transaction({
            'from': account.address,
            'nonce': w3.eth.get_transaction_count(account.address),
            'gas': 500000,
            'gasPrice': w3.to_wei('20', 'gwei'),
        })
        
        # Sign and send transaction
        signed_txn = w3.eth.account.sign_transaction(transaction, private_key)
        tx_hash = w3.eth.send_raw_transaction(signed_txn.raw_transaction)
        
        print(f"Transaction sent: {tx_hash.hex()}")
        
        # Wait for transaction confirmation
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
        
        if receipt.status != 1:
            raise Exception("Blockchain transaction failed")
        
        blockchain_tx = tx_hash.hex()
        print(f"✅ Batch created on blockchain successfully: {blockchain_tx}")
        
        # 8. Only create batch to database after blockchain success
        batch = Batch.from_dict({'metadata': metadata}, owner_id=int(current_user_id))
        
        # Save blockchain transaction hash
        batch.blockchain_tx = blockchain_tx
        
        # 9. Save to database
        db.session.add(batch)
        db.session.commit()
        
        # 10. Build complete response data - include all necessary fields
        import time
        current_timestamp = int(time.time())
        
        # Ensure metadata contains timestamp
        if 'createdAt' not in metadata:
            metadata['createdAt'] = current_timestamp
        if 'timestamp' not in metadata:
            metadata['timestamp'] = current_timestamp
        
        response_data = {
            'batchId': batch.id,
            'message': 'Batch created successfully',
            'status': batch.status,
            'batchNumber': batch.batch_number,
            
            # Add complete batch information
            'exists': True,
            'fileUrl': getattr(batch, 'file_url', 'none'),
            'result': getattr(batch, 'result', 'none'),
            'inspections': getattr(batch, 'inspections', []),
            'timestamp': current_timestamp,
            
            # Complete metadata
            'metadata': metadata,
            
            # Status information
            'statusInfo': {
                'status': batch.status,
                'display': batch.status,
                'color': 'orange' if batch.status == 'pending' else 'green'
            },
            
            # Blockchain information
            'blockchainTx': blockchain_tx,
            'blockchain': {
                'success': True,
                'transactionHash': blockchain_tx,
                'message': 'Batch saved to blockchain and database'
            },
            
            # Blockchain owner address
            'owner': blockchain_owner
        }
        
        # Add warning information (if any)
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
        print(f"❌ Batch creation failed: {str(e)}")
        return jsonify({
            'error': 'Failed to create batch',
            'message': 'Blockchain or database operation failed',
            'details': str(e)
        }), 500
        
def convert_date_for_contract(date_str):
    """
    Convert date to timestamp format required by the contract
    Keep the original system compatible, just convert to timestamp for blockchain
    """
    try:
        if not date_str:
            return int(time.time())
        
        # If it is a string date format, convert to timestamp
        if isinstance(date_str, str):
            # Try to parse common date formats
            from datetime import datetime
            
            # Try different date formats
            date_formats = [
                '%Y-%m-%d',
                '%d/%m/%Y', 
                '%m/%d/%Y',
                '%Y-%m-%dT%H:%M:%S',
                '%Y-%m-%d %H:%M:%S'
            ]
            
            for fmt in date_formats:
                try:
                    dt = datetime.strptime(date_str, fmt)
                    return int(dt.timestamp())
                except ValueError:
                    continue
        
        # If it is already a timestamp, return directly
        if isinstance(date_str, (int, float)):
            return int(date_str)
        
        # If all fail, use current time
        return int(time.time())
        
    except Exception as e:
        print(f"Date conversion error: {e}, using current timestamp")
        return int(time.time())


@batch_bp.route('/<int:batch_id>', methods=['GET'])
def get_batch(batch_id):
    """
    Query batch details
    GET /batches/{id}
    """
    try:
        # 1. Query batch
        batch = Batch.query.get(batch_id)
        
        if not batch:
            return jsonify({
                'error': 'Batch not found',
                'message': f'No batch found with ID {batch_id}'
            }), 404
        
        # 2. Get batch data
        batch_data = batch.to_dict()
        
        # 3. Add status display information (using BatchService)
        status_info = BatchService.get_status_display_info(batch.status)
        batch_data['statusInfo'] = status_info
        
        # 4. Add batch summary information (using BatchService)
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
    Query batch list - Read from database (matching blockchain format)
    GET /batches
    """
    try:
        # Get query parameters
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        status = request.args.get('status')
        
        # 🔄 Query batch from database
        query = Batch.query
        
        # Filter by status if specified
        if status:
            query = query.filter(Batch.status == status)
        
        # 🎯 Sort by batch ID (ascending: 1, 2, 3...)
        query = query.order_by(Batch.id.asc())
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        batches_db = pagination.items
        
        # Get all batch data
        batch_list = []
        for batch in batches_db:
            try:
                # Convert date to timestamp (matching blockchain format)
                harvest_timestamp = 0
                expiry_timestamp = 0
                
                if batch.harvest_date:
                    from datetime import datetime, time
                    harvest_datetime = datetime.combine(batch.harvest_date, time())
                    harvest_timestamp = int(harvest_datetime.timestamp())
                
                if batch.expiry_date:
                    from datetime import datetime, time
                    expiry_datetime = datetime.combine(batch.expiry_date, time())
                    expiry_timestamp = int(expiry_datetime.timestamp())
                
                # Get inspection data for this batch
                result = 'none'
                file_url = 'none'
                inspections_list = []
                
                try:
                    # Get all inspection records for this batch
                    inspections = Inspection.query.filter_by(batch_id=batch.id)\
                                                .order_by(Inspection.created_at.desc())\
                                                .all()
                    
                    if inspections:
                        # Get latest inspection details
                        latest_inspection = inspections[0]
                        result = latest_inspection.result
                        file_url = latest_inspection.file_url if latest_inspection.file_url else 'none'
                        
                        # Build inspections list (matching blockchain format)
                        for inspection in inspections:
                            # Get inspector info
                            inspector = User.query.get(inspection.inspector_id)
                            inspector_id = inspector.email if inspector else str(inspection.inspector_id)
                            
                            inspections_list.append({
                                'batchId': batch.id,
                                'blockchainTx': inspection.blockchain_tx,
                                'fileUrl': inspection.file_url if inspection.file_url else 'none',
                                'inspDate': int(inspection.insp_date.timestamp()),
                                'inspId': inspection.id,
                                'inspectorId': inspector_id,
                                'notes': inspection.notes if inspection.notes else 'No notes',
                                'result': inspection.result
                            })
                
                except Exception as e:
                    # Keep default values if inspection fetch fails
                    pass
                
                # Convert database data to frontend format (matching blockchain format exactly)
                batch_dict = {
                    'batchId': batch.id,
                    'blockchainTx': batch.blockchain_tx,
                    'inspections': inspections_list,
                    'metadata': {
                        'batchNumber': batch.batch_number,
                        'productName': batch.product_name,
                        'origin': batch.origin,
                        'quantity': str(batch.quantity),
                        'unit': batch.unit,
                        'harvestDate': harvest_timestamp,  # 🎯 Timestamp format, matching blockchain
                        'expiryDate': expiry_timestamp,    # 🎯 Timestamp format, matching blockchain
                        'createdAt': int(batch.created_at.timestamp()),
                        'organic': batch.organic,
                        'import': batch.import_product,
                        'totalWeightKg': batch.total_weight_kg or 0,
                    },
                    'status': batch.status,  # 🎯 Read status from database
                    'owner': getattr(batch, 'owner_address', ''),
                    'timestamp': int(batch.created_at.timestamp()),
                    'exists': True,
                    'result': result,
                    'fileUrl': file_url
                }
                
                # Add status display info
                batch_dict['statusInfo'] = get_status_display_info(batch.status)
                
                batch_list.append(batch_dict)
                
            except Exception as e:
                continue
        
        # Filter by status if specified (after building the list)
        if status:
            batch_list = [b for b in batch_list if b['status'] == status]
        
        # Simple pagination
        start_index = (page - 1) * per_page
        end_index = start_index + per_page
        paginated_batches = batch_list[start_index:end_index]
        
        return jsonify({
            'batches': paginated_batches,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': len(batch_list),
                'pages': (len(batch_list) + per_page - 1) // per_page
            }
        }), 200
        
    except Exception as e:
        print(f"Error in list_batches: {e}")
        return jsonify({
            'error': 'Internal server error',
            'message': f'Failed to retrieve batches: {str(e)}'
        }), 500

def convert_date_for_display(date_value):
    try:
        if not date_value:
            return None  # Return None instead of current timestamp
        
        # If it is a string date format, convert to timestamp
        if isinstance(date_value, str):
            from datetime import datetime
            
            # Try different date formats
            date_formats = [
                '%Y-%m-%d',
                '%d/%m/%Y', 
                '%m/%d/%Y',
                '%Y-%m-%dT%H:%M:%S',
                '%Y-%m-%d %H:%M:%S'
            ]
            
            for fmt in date_formats:
                try:
                    dt = datetime.strptime(date_value, fmt)
                    return int(dt.timestamp())
                except ValueError:
                    continue
        
        # If it is already a timestamp, return directly
        if isinstance(date_value, (int, float)):
            return int(date_value)
        
        # If all fail, return None instead of current timestamp
        return None
        
    except Exception as e:
        print(f"Date conversion error: {e}")
        return None



@batch_bp.route('/<int:batch_id>/status', methods=['PUT'])
@jwt_required()
def update_batch_status(batch_id):
    """
    Update batch status
    PUT /batches/{id}/status
    """
    try:
        # 1. Get current user information
        current_user_id = get_jwt_identity()
        jwt_claims = get_jwt()
        user_role = jwt_claims.get('role')
        
        # 2. Query batch
        batch = Batch.query.get(batch_id)
        if not batch:
            return jsonify({
                'error': 'Batch not found',
                'message': f'No batch found with ID {batch_id}'
            }), 404
        
        # 3. Permission verification
        if user_role == 'producer' and batch.owner_id != int(current_user_id):
            return jsonify({
                'error': 'Access denied',
                'message': 'You can only update your own batches'
            }), 403
        
        # 4. Get new status
        data = request.get_json()
        if not data or 'status' not in data:
            return jsonify({
                'error': 'Invalid request',
                'message': 'status is required'
            }), 400
        
        new_status = data['status']
        
        # 5. Use BatchService to validate status transition
        transition_result = BatchService.validate_status_transition(batch.status, new_status)
        
        if not transition_result['valid']:
            return jsonify({
                'error': 'Invalid status transition',
                'message': transition_result['error']
            }), 400
        
        # 6. Update status
        old_status = batch.status
        batch.status = new_status
        db.session.commit()
        
        # 7. Get status display information
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
        

def convert_contract_status_to_string(status_code):
    """Convert contract status code to string"""
    status_mapping = {
        0: 'pending',     # PENDING
        1: 'inspected',   # INSPECTED  
        2: 'approved',    # APPROVED
        3: 'rejected'     # REJECTED
    }
    return status_mapping.get(status_code, 'pending')


def get_status_display_info(status):
    """Get status display information"""
    status_info = {
        'pending': {
            'color': 'orange',
            'display': 'pending',
            'status': 'pending'
        },
        'inspected': {
            'color': 'blue', 
            'display': 'inspected',
            'status': 'inspected'
        },
        'approved': {
            'color': 'green',
            'display': 'approved', 
            'status': 'approved'
        },
        'rejected': {
            'color': 'red',
            'display': 'rejected',
            'status': 'rejected'
        }
    }
    return status_info.get(status, status_info['pending'])
def convert_inspection_result_to_string(result_code):
    """Convert inspection result code to string"""
    result_mapping = {
        0: 'pending',
        1: 'passed', 
        2: 'failed',
        3: 'needs_recheck'
    }
    return result_mapping.get(result_code, 'none')


@batch_bp.route('/debug/compare/<int:batch_id>', methods=['GET'])
def compare_batch_status(batch_id):
    """Compare batch status between database and blockchain"""
    try:
        # Query database
        batch = Batch.query.get(batch_id)
        db_status = batch.status if batch else "Not found"
        
        # Query blockchain
        network_config = get_network_config('testnet')
        w3 = Web3(Web3.HTTPProvider(network_config['rpc_url']))
        batch_address = get_contract_address('BatchRegistry', 'testnet')
        batch_abi = get_contract_abi('BatchRegistry')
        contract = w3.eth.contract(address=batch_address, abi=batch_abi)
        
        batch_data = contract.functions.getBatch(batch_id).call()
        blockchain_status = convert_contract_status_to_string(batch_data[8])
        
        return jsonify({
            'batch_id': batch_id,
            'database_status': db_status,
            'blockchain_status': blockchain_status,
            'match': db_status == blockchain_status
        })
        
    except Exception as e:
        return jsonify({'error': str(e)})

@batch_bp.route('/debug/inspector-auth', methods=['GET'])
def check_inspector_auth():
    try:
        # Get current account address
        from deploy_config import DEVELOPMENT_PRIVATE_KEYS
        private_key = DEVELOPMENT_PRIVATE_KEYS.get('inspector1')
        if not private_key:
            private_key = DEVELOPMENT_PRIVATE_KEYS.get('owner')
        
        if not private_key:
            return jsonify({'error': 'No private key found'}), 400
        
        # Connect to blockchain
        network_config = get_network_config('testnet')
        w3 = Web3(Web3.HTTPProvider(network_config['rpc_url']))
        account = w3.eth.account.from_key(private_key)
        
        # Check InspectionManager permission
        inspection_address = get_contract_address('InspectionManager', 'testnet')
        inspection_abi = get_contract_abi('InspectionManager')
        inspection_contract = w3.eth.contract(address=inspection_address, abi=inspection_abi)
        
        # Check BatchRegistry permission
        batch_address = get_contract_address('BatchRegistry', 'testnet')
        batch_abi = get_contract_abi('BatchRegistry')
        batch_contract = w3.eth.contract(address=batch_address, abi=batch_abi)
        
        # Get permission status
        inspection_auth = inspection_contract.functions.isAuthorizedInspector(account.address).call()
        batch_auth = batch_contract.functions.isAuthorizedInspector(account.address).call()
        
        # Get balance
        balance = w3.eth.get_balance(account.address)
        balance_eth = w3.from_wei(balance, 'ether')
        
        return jsonify({
            'account_address': account.address,
            'inspection_manager_auth': inspection_auth,
            'batch_registry_auth': batch_auth,
            'balance_eth': float(balance_eth),
            'balance_wei': str(balance),
            'network': network_config['name'],
            'contracts': {
                'inspection_manager': inspection_address,
                'batch_registry': batch_address
            }
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500