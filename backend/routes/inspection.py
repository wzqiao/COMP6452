# -*- coding: utf-8 -*-
"""
Inspection Results API Routes
Handles inspection-related HTTP requests
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


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create blueprint
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
        logger.info(f"🌐 Starting blockchain operations...")
        network_config = get_network_config('testnet')
        logger.info(f"   Network configuration: {network_config['name']}")
        logger.info(f"   RPC URL: {network_config['rpc_url']}")
        logger.info(f"   Chain ID: {network_config['chain_id']}")
        
        try:
            w3 = Web3(Web3.HTTPProvider(network_config['rpc_url']))
            logger.info(f"   Web3 instance created successfully")
        except Exception as web3_error:
            logger.error(f"❌ Web3 instance creation failed: {str(web3_error)}")
            raise Exception(f"Failed to create Web3 instance: {str(web3_error)}")
        
        if not w3.is_connected():
            logger.error(f"❌ Unable to connect to blockchain network!")
            logger.error(f"   RPC URL: {network_config['rpc_url']}")
            logger.error(f"   Please check network connection or try other RPC providers")
            raise Exception(f"Failed to connect to blockchain network: {network_config['rpc_url']}")
        
        # Get network information
        try:
            chain_id = w3.eth.chain_id
            block_number = w3.eth.block_number
            gas_price_current = w3.eth.gas_price
            logger.info(f"✅ Blockchain connection successful!")
            logger.info(f"   Current Chain ID: {chain_id}")
            logger.info(f"   Latest block: {block_number}")
            logger.info(f"   Current Gas price: {w3.from_wei(gas_price_current, 'gwei'):.2f} Gwei")
        except Exception as network_info_error:
            logger.warning(f"⚠️  Failed to get network information: {str(network_info_error)}")
            logger.info(f"✅ Blockchain connection successful (basic connection)")
        
        # Get InspectionManager contract instance
        logger.info(f"📋 Initializing smart contract...")
        inspection_address = get_contract_address('InspectionManager', 'testnet')
        logger.info(f"   InspectionManager address: {inspection_address}")
        
        try:
            # Check if contract address has code
            contract_code = w3.eth.get_code(inspection_address)
            if contract_code == b'':
                logger.error(f"❌ Contract address has no code! Address may be wrong or contract not deployed")
                raise Exception(f"No contract code at address: {inspection_address}")
            
            logger.info(f"   Contract code length: {len(contract_code)} bytes")
            
            inspection_abi = get_contract_abi('InspectionManager')
            contract = w3.eth.contract(address=inspection_address, abi=inspection_abi)
            logger.info(f"✅ Contract instance created successfully")
            
            # Test contract read functionality
            try:
                total_inspections = contract.functions.getTotalInspections().call()
                logger.info(f"   Current total inspections: {total_inspections}")
            except Exception as read_error:
                logger.warning(f"⚠️  Contract read test failed: {str(read_error)}")
                
        except Exception as contract_error:
            logger.error(f"❌ Contract initialization failed: {str(contract_error)}")
            raise Exception(f"Failed to initialize contract: {str(contract_error)}")
        
        # Get private key and account
        logger.info(f"🔑 Configuring account...")
        private_key = DEVELOPMENT_PRIVATE_KEYS.get('inspector1')
        if not private_key:
            logger.info(f"   inspector1 private key not found, trying owner private key")
            private_key = DEVELOPMENT_PRIVATE_KEYS.get('owner')
        
        if not private_key:
            logger.error(f"❌ No available private key configuration found")
            logger.error(f"   Please check DEVELOPMENT_PRIVATE_KEYS configuration")
            raise Exception("No private key configured for inspection transactions")
        
        logger.info(f"✅ Private key configured successfully")
        
        account = w3.eth.account.from_key(private_key)
        gas_price = w3.to_wei('20', 'gwei')
        
        # Step 1: Find the blockchain batch ID for this database batch
        logger.info(f"🔍 Finding blockchain batch ID for database batch ID {batch_id}...")
        
        blockchain_batch_id = None
        try:
            # Get BatchRegistry contract to find matching batch
            batch_registry_address = get_contract_address('BatchRegistry', 'testnet')
            batch_registry_abi = get_contract_abi('BatchRegistry')
            batch_registry_contract = w3.eth.contract(address=batch_registry_address, abi=batch_registry_abi)
            
            # Get total number of batches on blockchain
            total_batches = batch_registry_contract.functions.getTotalBatches().call()
            logger.info(f"   Total batches on blockchain: {total_batches}")
            
            # Iterate through all blockchain batches to find matching batch number
            for blockchain_id in range(1, total_batches + 1):
                try:
                    blockchain_batch = batch_registry_contract.functions.getBatch(blockchain_id).call()
                    blockchain_batch_number = blockchain_batch[1]  # batchNumber field
                    
                    logger.info(f"   Checking blockchain batch ID {blockchain_id}: {blockchain_batch_number}")
                    
                    if blockchain_batch_number == batch.batch_number:
                        blockchain_batch_id = blockchain_id
                        logger.info(f"✅ Found matching blockchain batch ID: {blockchain_batch_id}")
                        break
                        
                except Exception as e:
                    logger.warning(f"   Skipping blockchain batch ID {blockchain_id}: {str(e)}")
                    continue
            
            if not blockchain_batch_id:
                logger.error(f"❌ Database batch {batch_id} ({batch.batch_number}) not found on blockchain")
                raise Exception(f"Database batch {batch_id} ({batch.batch_number}) not found on blockchain")
            
        except Exception as e:
            logger.error(f"❌ Failed to find blockchain batch ID: {str(e)}")
            raise Exception(f"Failed to find blockchain batch ID: {str(e)}")
        
        # Step 2: Create inspection record using blockchain batch ID
        logger.info(f"🔗 Creating inspection record - using blockchain batch ID: {blockchain_batch_id}")
        create_transaction = contract.functions.createInspection(
            blockchain_batch_id,  # Use blockchain batch ID instead of database ID
            file_url,
            notes
        ).build_transaction({
            'from': account.address,
            'nonce': w3.eth.get_transaction_count(account.address),
            'gas': 500000,
            'gasPrice': gas_price,
        })
        
        # Sign and send create inspection transaction
        logger.info(f"🔗 Preparing to send create inspection transaction...")
        logger.info(f"   Batch ID: {batch_id}")
        logger.info(f"   Account address: {account.address}")
        logger.info(f"   Gas limit: {create_transaction['gas']}")
        logger.info(f"   Gas price: {create_transaction['gasPrice']} wei ({w3.from_wei(create_transaction['gasPrice'], 'gwei')} Gwei)")
        
        # Check account balance
        account_balance = w3.eth.get_balance(account.address)
        account_balance_eth = w3.from_wei(account_balance, 'ether')
        estimated_cost = create_transaction['gas'] * create_transaction['gasPrice']
        estimated_cost_eth = w3.from_wei(estimated_cost, 'ether')
        
        logger.info(f"   Account balance: {account_balance_eth:.6f} ETH")
        logger.info(f"   Estimated transaction cost: {estimated_cost_eth:.6f} ETH")
        
        if account_balance < estimated_cost:
            logger.error(f"❌ Insufficient account balance! Need {estimated_cost_eth:.6f} ETH, currently have {account_balance_eth:.6f} ETH")
            raise Exception(f"Insufficient balance: need {estimated_cost_eth:.6f} ETH, have {account_balance_eth:.6f} ETH")
        
        try:
            signed_create_txn = w3.eth.account.sign_transaction(create_transaction, private_key)
            logger.info(f"✅ Transaction signed successfully")
            
            create_tx_hash = w3.eth.send_raw_transaction(signed_create_txn.raw_transaction)
            logger.info(f"✅ Transaction sent, hash: {create_tx_hash.hex()}")
            
            # Wait for create transaction confirmation
            logger.info(f"⏳ Waiting for transaction confirmation (max 120 seconds)...")
            create_receipt = w3.eth.wait_for_transaction_receipt(create_tx_hash, timeout=120)
            
            # Detailed transaction receipt information
            logger.info(f"📄 Transaction receipt details:")
            logger.info(f"   Transaction hash: {create_receipt.transactionHash.hex()}")
            logger.info(f"   Block number: {create_receipt.blockNumber}")
            logger.info(f"   Block hash: {create_receipt.blockHash.hex()}")
            logger.info(f"   Gas used: {create_receipt.gasUsed}/{create_transaction['gas']} ({(create_receipt.gasUsed/create_transaction['gas']*100):.1f}%)")
            logger.info(f"   Actual cost: {w3.from_wei(create_receipt.gasUsed * create_transaction['gasPrice'], 'ether'):.6f} ETH")
            logger.info(f"   Transaction status: {create_receipt.status}")
            logger.info(f"   Number of logs: {len(create_receipt.logs)}")
            
        except Exception as send_error:
            logger.error(f"❌ Failed to send transaction: {str(send_error)}")
            logger.error(f"   Error type: {type(send_error).__name__}")
            raise Exception(f"Failed to send create inspection transaction: {str(send_error)}")
        
        if create_receipt.status != 1:
            logger.error(f"❌ Create inspection transaction failed!")
            logger.error(f"   Transaction status: {create_receipt.status} (expected: 1)")
            logger.error(f"   Transaction hash: {create_receipt.transactionHash.hex()}")
            logger.error(f"   Block number: {create_receipt.blockNumber}")
            logger.error(f"   Gas used: {create_receipt.gasUsed}/{create_transaction['gas']}")
            
            # Try to get revert reason
            try:
                if hasattr(create_receipt, 'logs') and create_receipt.logs:
                    logger.error(f"   Event logs: {len(create_receipt.logs)} logs")
                    for i, log in enumerate(create_receipt.logs):
                        logger.error(f"     Log{i}: {log}")
                else:
                    logger.error(f"   No event logs")
                    
                # Try to replay transaction to get error info
                try:
                    w3.eth.call(create_transaction, create_receipt.BlockNumber)
                except Exception as call_error:
                    logger.error(f"   Contract call error: {str(call_error)}")
                    
            except Exception as debug_error:
                logger.error(f"   Failed to get debug info: {str(debug_error)}")
            
            raise Exception(f"Create inspection transaction failed - Status: {create_receipt.status}, TxHash: {create_receipt.transactionHash.hex()}, Block: {create_receipt.blockNumber}")
        
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
            logger.info(f"✅ Preparing to send complete inspection transaction...")
            logger.info(f"   Inspection ID: {blockchain_inspection_id}")
            logger.info(f"   Result value: {result_value} ({data['result']})")
            logger.info(f"   Gas limit: {complete_transaction['gas']}")
            logger.info(f"   Gas price: {complete_transaction['gasPrice']} wei ({w3.from_wei(complete_transaction['gasPrice'], 'gwei')} Gwei)")
            
            # Check account balance (for complete transaction)
            account_balance_current = w3.eth.get_balance(account.address)
            account_balance_eth_current = w3.from_wei(account_balance_current, 'ether')
            estimated_cost_complete = complete_transaction['gas'] * complete_transaction['gasPrice']
            estimated_cost_complete_eth = w3.from_wei(estimated_cost_complete, 'ether')
            
            logger.info(f"   Current account balance: {account_balance_eth_current:.6f} ETH")
            logger.info(f"   Complete transaction estimated cost: {estimated_cost_complete_eth:.6f} ETH")
            
            if account_balance_current < estimated_cost_complete:
                logger.error(f"❌ Insufficient account balance for complete transaction! Need {estimated_cost_complete_eth:.6f} ETH, currently have {account_balance_eth_current:.6f} ETH")
                raise Exception(f"Insufficient balance for complete transaction: need {estimated_cost_complete_eth:.6f} ETH, have {account_balance_eth_current:.6f} ETH")
            
            try:
                signed_complete_txn = w3.eth.account.sign_transaction(complete_transaction, private_key)
                logger.info(f"✅ Complete transaction signed successfully")
                
                complete_tx_hash = w3.eth.send_raw_transaction(signed_complete_txn.raw_transaction)
                logger.info(f"✅ Complete transaction sent, hash: {complete_tx_hash.hex()}")
                
                # Wait for complete transaction confirmation
                logger.info(f"⏳ Waiting for complete transaction confirmation (max 120 seconds)...")
                complete_receipt = w3.eth.wait_for_transaction_receipt(complete_tx_hash, timeout=120)
                
                # Detailed complete transaction receipt information
                logger.info(f"📄 Complete transaction receipt details:")
                logger.info(f"   Transaction hash: {complete_receipt.transactionHash.hex()}")
                logger.info(f"   Block number: {complete_receipt.blockNumber}")
                logger.info(f"   Block hash: {complete_receipt.blockHash.hex()}")
                logger.info(f"   Gas used: {complete_receipt.gasUsed}/{complete_transaction['gas']} ({(complete_receipt.gasUsed/complete_transaction['gas']*100):.1f}%)")
                logger.info(f"   Actual cost: {w3.from_wei(complete_receipt.gasUsed * complete_transaction['gasPrice'], 'ether'):.6f} ETH")
                logger.info(f"   Transaction status: {complete_receipt.status}")
                logger.info(f"   Number of logs: {len(complete_receipt.logs)}")
                
            except Exception as complete_send_error:
                logger.error(f"❌ Failed to send complete transaction: {str(complete_send_error)}")
                logger.error(f"   Error type: {type(complete_send_error).__name__}")
                raise Exception(f"Failed to send complete inspection transaction: {str(complete_send_error)}")
            
            if complete_receipt.status != 1:
                logger.error(f"❌ Complete inspection transaction failed!")
                logger.error(f"   Transaction status: {complete_receipt.status} (expected: 1)")
                logger.error(f"   Transaction hash: {complete_receipt.transactionHash.hex()}")
                logger.error(f"   Block number: {complete_receipt.blockNumber}")
                logger.error(f"   Gas used: {complete_receipt.gasUsed}/{complete_transaction['gas']}")
                logger.error(f"   Inspection ID: {blockchain_inspection_id}")
                logger.error(f"   Result value: {result_value}")
                
                # Try to get revert reason for complete transaction
                try:
                    if hasattr(complete_receipt, 'logs') and complete_receipt.logs:
                        logger.error(f"   Event logs: {len(complete_receipt.logs)} logs")
                        for i, log in enumerate(complete_receipt.logs):
                            logger.error(f"     Log{i}: {log}")
                    else:
                        logger.error(f"   No event logs")
                        
                    # Try to replay transaction to get error info
                    try:
                        w3.eth.call(complete_transaction, complete_receipt.blockNumber)
                    except Exception as complete_call_error:
                        logger.error(f"   Contract call error: {str(complete_call_error)}")
                        
                except Exception as complete_debug_error:
                    logger.error(f"   Failed to get debug info: {str(complete_debug_error)}")
                
                raise Exception(f"Complete inspection transaction failed - Status: {complete_receipt.status}, TxHash: {complete_receipt.transactionHash.hex()}, Block: {complete_receipt.blockNumber}, InspectionID: {blockchain_inspection_id}")
            
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
        
        logger.info(f"🎉 Inspection result submission completely successful!")
        logger.info(f"   Batch ID: {batch_id}")
        logger.info(f"   Inspection result: {data['result']}")
        logger.info(f"   Blockchain transaction: {blockchain_tx}")
        logger.info(f"   Database record ID: {inspection.id}")
        logger.info(f"   Batch new status: {batch.status}")
        
        return jsonify(response_data), 201
        
    except SQLAlchemyError as e:
        db.session.rollback()
        logger.error(f"❌ Database operation failed: {str(e)}")
        logger.error(f"   Exception type: {type(e).__name__}")
        logger.error(f"   Batch ID: {batch_id if 'batch_id' in locals() else 'Unknown'}")
        return jsonify({'error': 'Database operation failed', 'details': str(e)}), 500
    except Exception as e:
        db.session.rollback()
        error_msg = str(e)
        error_type = type(e).__name__
        
        logger.error(f"❌ Inspection result submission failed: {error_msg}")
        logger.error(f"   Exception type: {error_type}")
        logger.error(f"   Batch ID: {batch_id if 'batch_id' in locals() else 'Unknown'}")
        logger.error(f"   User ID: {current_user_id if 'current_user_id' in locals() else 'Unknown'}")
        logger.error(f"   Inspection result: {data.get('result') if 'data' in locals() and data else 'Unknown'}")
        
        # Provide specific resolution suggestions based on error type
        if "connect" in error_msg.lower():
            logger.error(f"💡 Suggestion: Check blockchain network connection or RPC endpoint")
        elif "insufficient" in error_msg.lower() and "balance" in error_msg.lower():
            logger.error(f"💡 Suggestion: Insufficient account balance, please go to https://sepoliafaucet.com/ to get test ETH")
        elif "contract" in error_msg.lower():
            logger.error(f"💡 Suggestion: Check smart contract address and ABI configuration")
        elif "private key" in error_msg.lower():
            logger.error(f"💡 Suggestion: Check DEVELOPMENT_PRIVATE_KEYS configuration")
        elif "transaction failed" in error_msg.lower():
            logger.error(f"💡 Suggestion: Check detailed transaction logs above to analyze failure cause")
        return jsonify({'error': 'Failed to submit inspection result', 'message': 'Blockchain or database operation failed', 'details': str(e)}), 500

@inspection_bp.route('/batches/<int:batch_id>/inspections', methods=['GET'])
@jwt_required()
def get_batch_inspections(batch_id):
    """
    Get all inspection records for a batch
    
    GET /batches/{id}/inspections
    """
    try:
        # Get current user
        current_user_id = get_jwt_identity()
        current_user = User.query.get(current_user_id)
        
        if not current_user:
            return jsonify({'error': 'User not found'}), 401
        
        # Verify batch exists
        batch = Batch.query.get(batch_id)
        if not batch:
            return jsonify({'error': 'Batch not found'}), 404
        
        # Permission check: producers can only view their own batches, inspectors can view all batches
        if current_user.role == 'producer' and batch.owner_id != current_user_id:
            return jsonify({'error': 'No permission to view inspection records for this batch'}), 403
        
        # Get inspection records
        inspections = Inspection.query.filter_by(batch_id=batch_id).order_by(Inspection.created_at.desc()).all()
        
        # Build response
        inspections_data = []
        for inspection in inspections:
            inspector = User.query.get(inspection.inspector_id)
            inspections_data.append({
                'id': inspection.id,
                'inspector_id': inspection.inspector_id,
                'inspector_name': inspector.email if inspector else 'Unknown',
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
        logger.error(f"Failed to get inspection record: {str(e)}")
        return jsonify({'error': 'Failed to get inspection record'}), 500

@inspection_bp.route('/inspections/<int:inspection_id>', methods=['GET'])
@jwt_required()
def get_inspection(inspection_id):
    """
    Get single inspection record details
    
    GET /inspections/{id}
    """
    try:
        # Get current user
        current_user_id = get_jwt_identity()
        current_user = User.query.get(current_user_id)
        
        if not current_user:
            return jsonify({'error': 'User not found'}), 401
        
        # Get inspection records
        inspection = Inspection.query.get(inspection_id)
        if not inspection:
            return jsonify({'error': 'Inspection record not found'}), 404
        
        # Get associated batch
        batch = Batch.query.get(inspection.batch_id)
        if not batch:
            return jsonify({'error': 'Associated batch not found'}), 404
        
        # Permission check: producers can only view inspection records of their own batches, inspectors can view all records
        if current_user.role == 'producer' and batch.owner_id != current_user_id:
            return jsonify({'error': 'No permission to view this inspection record'}), 403
        
        # Get inspector information
        inspector = User.query.get(inspection.inspector_id)
        
        # Build response
        response_data = {
            'inspection': {
                'id': inspection.id,
                'batch_id': inspection.batch_id,
                'inspector_id': inspection.inspector_id,
                'inspector_name': inspector.email if inspector else 'Unknown',
                'result': inspection.result,
                'file_url': inspection.file_url,
                'notes': inspection.notes,
                'insp_date': inspection.insp_date.isoformat(),
                'blockchain_tx': inspection.blockchain_tx,
                'created_at': inspection.created_at.isoformat(),
            },
            'batch': {
                'id': batch.id,
                'batch_number': batch.batch_number,
                'product_name': batch.product_name,
                'origin': batch.origin,
                'status': batch.status
            }
        }
        
        # If there's a blockchain record, try to get on-chain data
        if inspection.blockchain_tx:
            try:
                blockchain_service = get_blockchain_service()
                if blockchain_service.inspection_manager:
                    # Here we can add logic to get data from blockchain
                    # chain_data = blockchain_service.get_inspection_from_chain(inspection_id)
                    response_data['blockchain'] = {
                        'tx_hash': inspection.blockchain_tx,
                        'message': 'Inspection record is on blockchain'
                    }
            except Exception as e:
                logger.warning(f"Failed to get blockchain data: {str(e)}")
        
        return jsonify(response_data), 200
        
    except Exception as e:
        logger.error(f"Failed to get inspection record: {str(e)}")
        return jsonify({'error': 'Failed to get inspection record'}), 500

@inspection_bp.route('/inspections/<int:inspection_id>', methods=['PUT'])
@jwt_required()
def update_inspection(inspection_id):
    """
    Update inspection record
    
    PUT /inspections/{id}
    
    Request body:
    {
        "result": "passed|failed|needs_recheck",
        "file_url": "https://...",
        "notes": "Updated inspection notes"
    }
    """
    try:
        # Get current user
        current_user_id = get_jwt_identity()
        current_user = User.query.get(current_user_id)
        
        if not current_user:
            return jsonify({'error': 'User not found'}), 401
        
        # Verify user role
        if current_user.role != 'inspector':
            return jsonify({'error': 'Only inspectors can update inspection records'}), 403
        
        # Get inspection records
        inspection = Inspection.query.get(inspection_id)
        if not inspection:
            return jsonify({'error': 'Inspection record not found'}), 404
        
        # Verify if the record is created by the user
        if inspection.inspector_id != current_user_id:
            return jsonify({'error': 'Only the creator can update the inspection record'}), 403
        
        # Get request data
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Request data is empty'}), 400
        
        # Verify inspection result
        if 'result' in data:
            valid_results = ['passed', 'failed', 'needs_recheck']
            if data['result'] not in valid_results:
                return jsonify({'error': f'Invalid inspection result: {data["result"]}'}), 400
        
        # Get associated batch
        batch = Batch.query.get(inspection.batch_id)
        if not batch:
            return jsonify({'error': 'Associated batch not found'}), 404
        
        # Update inspection record
        old_result = inspection.result
        
        if 'result' in data:
            inspection.result = data['result']
        if 'file_url' in data:
            inspection.file_url = data['file_url']
        if 'notes' in data:
            inspection.notes = data['notes']
        
        inspection.updated_at = datetime.utcnow()
        
        # If the inspection result changes, update the batch status
        if 'result' in data and data['result'] != old_result:
            if data['result'] == 'passed':
                batch.status = 'approved'
            elif data['result'] == 'failed':
                batch.status = 'rejected'
            else:  # needs_recheck
                batch.status = 'inspected'
        
        # Blockchain update operation
        if inspection.blockchain_tx:
            try:
                blockchain_service = get_blockchain_service()
                if blockchain_service.inspection_manager and blockchain_service.account:
                    # Blockchain update logic can be added here
                    # blockchain_service.update_inspection_on_chain(...)
                    pass
            except Exception as e:
                logger.warning(f"Blockchain update failed: {str(e)}")
        
        # Submit database transaction
        db.session.commit()
        
        # Build response
        response_data = {
            'message': 'Inspection record updated successfully',
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
        logger.error(f"Database operation failed: {str(e)}")
        return jsonify({'error': 'Database operation failed'}), 500
    except Exception as e:
        db.session.rollback()
        logger.error(f"Update inspection record failed: {str(e)}")
        return jsonify({'error': 'Update inspection record failed'}), 500

@inspection_bp.route('/inspections', methods=['GET'])
@jwt_required()
def get_inspections():
    """
        Get inspection record list
    
    GET /inspections?page=1&per_page=10&result=passed&inspector_id=1
    """
    try:
        # Get current user
        current_user_id = get_jwt_identity()
        current_user = User.query.get(current_user_id)
        
        if not current_user:
            return jsonify({'error': 'User not found'}), 401
        
        # Get query parameters
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 10, type=int), 100)
        result_filter = request.args.get('result')
        inspector_id = request.args.get('inspector_id', type=int)
        
        # Build query
        query = Inspection.query
        
        # Permission filter: producers can only view inspection records of their own batches
        if current_user.role == 'producer':
            # Get user's batch ID list
            user_batch_ids = [batch.id for batch in Batch.query.filter_by(owner_id=current_user_id).all()]
            query = query.filter(Inspection.batch_id.in_(user_batch_ids))
        
        # Result filter
        if result_filter:
            query = query.filter(Inspection.result == result_filter)
        
        # Inspector filter
        if inspector_id:
            query = query.filter(Inspection.inspector_id == inspector_id)
        
        # Pagination
        query = query.order_by(Inspection.created_at.desc())
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        inspections = pagination.items
        
        # Build response
        inspections_data = []
        for inspection in inspections:
            inspector = User.query.get(inspection.inspector_id)
            batch = Batch.query.get(inspection.batch_id)
            
            inspections_data.append({
                'id': inspection.id,
                'batch_id': inspection.batch_id,
                'batch_number': batch.batch_number if batch else 'Unknown',
                'product_name': batch.product_name if batch else 'Unknown',
                'inspector_id': inspection.inspector_id,
                'inspector_name': inspector.email if inspector else 'Unknown',
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
        logger.error(f"Failed to get inspection record list: {str(e)}")
        return jsonify({'error': 'Failed to get inspection record list'}), 500