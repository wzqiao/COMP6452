# -*- coding: utf-8 -*-
"""
Blockchain service layer
Implement Web3 integration and smart contract call logic
"""

import os
import json
import logging
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
from web3 import Web3
from web3.contract import Contract
from web3.exceptions import Web3Exception, ContractLogicError
from eth_account import Account
from eth_account.signers.local import LocalAccount

# Import contract configuration
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'contracts'))
from deploy_config import (
    get_network_config, 
    get_contract_address, 
    get_contract_abi,
    BATCH_STATUS, 
    INSPECTION_RESULT,
    DEFAULT_NETWORK
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BlockchainError(Exception):
    """Blockchain operation exception"""
    pass

class ContractNotFoundError(BlockchainError):
    """Contract not found exception"""
    pass

class InsufficientFundsError(BlockchainError):
    """Insufficient funds exception"""
    pass

class BlockchainService:
    """Blockchain service class"""
    
    def __init__(self, network_name: str = None, private_key: str = None):
        """
        Initialize blockchain service
        
        Args:
            network_name: Network name, default is development
            private_key: Private key, used to sign transactions
        """
        self.network_name = network_name or DEFAULT_NETWORK
        self.network_config = get_network_config(self.network_name)
        
        # Initialize Web3 connection
        self.w3 = self._init_web3()
        
        # Initialize account
        self.account = self._init_account(private_key)
        
        # Initialize contract instance
        self.batch_registry = None
        self.inspection_manager = None
        self._init_contracts()
        
        logger.info(f"Blockchain service initialized, network: {self.network_config['name']}")
    
    def _init_web3(self) -> Web3:
        """Initialize Web3 connection"""
        try:
            w3 = Web3(Web3.HTTPProvider(self.network_config['rpc_url']))
            if not w3.is_connected():
                raise BlockchainError(f"Cannot connect to network: {self.network_config['rpc_url']}")
            
            logger.info(f"Web3 connection successful, chain ID: {w3.eth.chain_id}")
            return w3
        except Exception as e:
            raise BlockchainError(f"Web3 initialization failed: {str(e)}")
    
    def _init_account(self, private_key: str = None) -> Optional[LocalAccount]:
        """Initialize account"""
        if not private_key:
            # Get private key from environment variable
            private_key = os.getenv('BLOCKCHAIN_PRIVATE_KEY')
        
        if not private_key:
            logger.warning("No private key provided, some features may not work")
            return None
        
        try:
            account = Account.from_key(private_key)
            balance = self.w3.eth.get_balance(account.address)
            logger.info(f"Account address: {account.address}, balance: {Web3.from_wei(balance, 'ether')} ETH")
            return account
        except Exception as e:
            logger.error(f"Account initialization failed: {str(e)}")
            return None
    
    def _init_contracts(self):
        """Initialize contract instance"""
        try:
            # Initialize BatchRegistry contract
            batch_registry_address = get_contract_address('BatchRegistry', self.network_name)
            if batch_registry_address and batch_registry_address != '0x0000000000000000000000000000000000000000':
                batch_registry_abi = get_contract_abi('BatchRegistry')
                self.batch_registry = self.w3.eth.contract(
                    address=batch_registry_address,
                    abi=batch_registry_abi
                )
                logger.info(f"BatchRegistry contract loaded: {batch_registry_address}")
            
            # Initialize InspectionManager contract
            inspection_manager_address = get_contract_address('InspectionManager', self.network_name)
            if inspection_manager_address and inspection_manager_address != '0x0000000000000000000000000000000000000000':
                inspection_manager_abi = get_contract_abi('InspectionManager')
                self.inspection_manager = self.w3.eth.contract(
                    address=inspection_manager_address,
                    abi=inspection_manager_abi
                )
                logger.info(f"InspectionManager contract loaded: {inspection_manager_address}")
                
        except Exception as e:
            logger.error(f"Contract initialization failed: {str(e)}")
    
    def _send_transaction(self, contract_function, *args, **kwargs) -> Tuple[str, Dict]:
        """
        Send transaction
        
        Args:
            contract_function: Contract function
            *args: Function arguments
            **kwargs: Additional parameters
        
        Returns:
            tuple: (transaction hash, transaction receipt)
        """
        if not self.account:
            raise BlockchainError("No account configured, cannot send transaction")
        
        try:
            # Build transaction
            transaction = contract_function(*args).build_transaction({
                'chainId': self.network_config['chain_id'],
                'gas': kwargs.get('gas', self.network_config['gas_limit']),
                'gasPrice': kwargs.get('gas_price', self.network_config['gas_price']),
                'nonce': self.w3.eth.get_transaction_count(self.account.address),
            })
            
            # Sign transaction
            signed_txn = self.account.sign_transaction(transaction)
            
            # Send transaction
            tx_hash = self.w3.eth.send_raw_transaction(signed_txn.rawTransaction)
            
            # Wait for transaction confirmation
            tx_receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
            
            if tx_receipt.status == 1:
                logger.info(f"Transaction successful: {tx_hash.hex()}")
                return tx_hash.hex(), tx_receipt
            else:
                raise BlockchainError(f"Transaction failed: {tx_hash.hex()}")
                
        except ContractLogicError as e:
            raise BlockchainError(f"Contract logic error: {str(e)}")
        except ValueError as e:
            if "insufficient funds" in str(e).lower():
                raise InsufficientFundsError("Account balance insufficient")
            raise BlockchainError(f"Transaction error: {str(e)}")
        except Exception as e:
            raise BlockchainError(f"Send transaction failed: {str(e)}")
    
    def create_batch_on_chain(self, batch_data: Dict) -> Tuple[str, int]:
        """
        Create batch on blockchain
        
        Args:
            batch_data: Batch data
            
        Returns:
            tuple: (transaction hash, blockchain batch ID)
        """
        if not self.batch_registry:
            raise ContractNotFoundError("BatchRegistry contract not found")
        
        try:
            # Convert timestamp
            harvest_date = int(datetime.fromisoformat(batch_data['harvest_date']).timestamp())
            expiry_date = int(datetime.fromisoformat(batch_data['expiry_date']).timestamp())
            
            # Call contract function
            tx_hash, tx_receipt = self._send_transaction(
                self.batch_registry.functions.createBatch,
                batch_data['batch_number'],
                batch_data['product_name'],
                batch_data['origin'],
                int(batch_data['quantity']),
                batch_data['unit'],
                harvest_date,
                expiry_date
            )
            
            # Get batch ID from transaction receipt
            batch_id = self._get_batch_id_from_receipt(tx_receipt)
            
            logger.info(f"Batch created on blockchain: {batch_data['batch_number']}, blockchain ID: {batch_id}")
            return tx_hash, batch_id
            
        except Exception as e:
            logger.error(f"Batch creation failed: {str(e)}")
            raise BlockchainError(f"Batch creation failed: {str(e)}")
    
    def _get_batch_id_from_receipt(self, tx_receipt: Dict) -> int:
        """Get batch ID from transaction receipt"""
        try:
            # Parse BatchCreated event
            batch_created_event = self.batch_registry.events.BatchCreated().process_receipt(tx_receipt)
            if batch_created_event:
                return batch_created_event[0]['args']['batchId']
            else:
                raise BlockchainError("BatchCreated event not found")
        except Exception as e:
            raise BlockchainError(f"Failed to get batch ID: {str(e)}")
    
    def get_batch_from_chain(self, batch_id: int) -> Dict:
        """
        Get batch information from blockchain
        
        Args:
            batch_id: Blockchain batch ID
            
        Returns:
            dict: Batch information
        """
        if not self.batch_registry:
            raise ContractNotFoundError("BatchRegistry contract not found")
        
        try:
            batch_data = self.batch_registry.functions.getBatch(batch_id).call()
            
            return {
                'id': batch_data[0],
                'batch_number': batch_data[1],
                'product_name': batch_data[2],
                'origin': batch_data[3],
                'quantity': batch_data[4],
                'unit': batch_data[5],
                'harvest_date': datetime.fromtimestamp(batch_data[6]).isoformat(),
                'expiry_date': datetime.fromtimestamp(batch_data[7]).isoformat(),
                'status': batch_data[8],
                'owner': batch_data[9],
                'created_at': datetime.fromtimestamp(batch_data[10]).isoformat(),
                'updated_at': datetime.fromtimestamp(batch_data[11]).isoformat(),
                'exists': batch_data[12]
            }
            
        except Exception as e:
            logger.error(f"Failed to get batch: {str(e)}")
            raise BlockchainError(f"Failed to get batch: {str(e)}")
    
    def update_batch_status_on_chain(self, batch_id: int, new_status: str) -> str:
        """
        Update batch status
        
        Args:
            batch_id: Blockchain batch ID
            new_status: New status
            
        Returns:
            str: Transaction hash
        """
        if not self.batch_registry:
            raise ContractNotFoundError("BatchRegistry contract not found")
        
        try:
            # Convert status
            status_value = BATCH_STATUS.get(new_status.upper())
            if status_value is None:
                raise BlockchainError(f"Invalid batch status: {new_status}")
            
            tx_hash, _ = self._send_transaction(
                self.batch_registry.functions.updateBatchStatus,
                batch_id,
                status_value
            )
            
            logger.info(f"Batch status updated: {batch_id} -> {new_status}")
            return tx_hash
            
        except Exception as e:
            logger.error(f"Failed to update batch status: {str(e)}")
            raise BlockchainError(f"Failed to update batch status: {str(e)}")
    
    def create_inspection_on_chain(self, batch_id: int, file_url: str, notes: str = "") -> Tuple[str, int]:
        """
        Create inspection record on blockchain
        
        Args:
            batch_id: Blockchain batch ID
            file_url: Inspection file URL
            notes: Inspection notes
            
        Returns:
            tuple: (transaction hash, inspection record ID)
        """
        if not self.inspection_manager:
            raise ContractNotFoundError("InspectionManager contract not found")
        
        try:
            tx_hash, tx_receipt = self._send_transaction(
                self.inspection_manager.functions.createInspection,
                batch_id,
                file_url,
                notes
            )
            
            # Get inspection ID from transaction receipt
            inspection_id = self._get_inspection_id_from_receipt(tx_receipt)
            
            logger.info(f"Inspection record created on blockchain: batch ID {batch_id}, inspection ID {inspection_id}")
            return tx_hash, inspection_id
            
        except Exception as e:
            logger.error(f"Failed to create inspection record: {str(e)}")
            raise BlockchainError(f"Failed to create inspection record: {str(e)}")
    
    def _get_inspection_id_from_receipt(self, tx_receipt: Dict) -> int:
        """Get inspection ID from transaction receipt"""
        try:
            # Parse InspectionCreated event
            inspection_created_event = self.inspection_manager.events.InspectionCreated().process_receipt(tx_receipt)
            if inspection_created_event:
                return inspection_created_event[0]['args']['inspectionId']
            else:
                raise BlockchainError("InspectionCreated event not found")
        except Exception as e:
            raise BlockchainError(f"Failed to get inspection ID: {str(e)}")
    
    def complete_inspection_on_chain(self, inspection_id: int, result: str, file_url: str = "", notes: str = "") -> str:
        """
        Complete inspection record
        
        Args:
            inspection_id: Inspection record ID
            result: Inspection result
            file_url: Inspection file URL
            notes: Inspection notes
            
        Returns:
            str: Transaction hash
        """
        if not self.inspection_manager:
            raise ContractNotFoundError("InspectionManager contract not found")
        
        try:
            # Convert inspection result
            result_value = INSPECTION_RESULT.get(result.upper())
            if result_value is None:
                raise BlockchainError(f"Invalid inspection result: {result}")
            
            tx_hash, _ = self._send_transaction(
                self.inspection_manager.functions.completeInspection,
                inspection_id,
                result_value,
                file_url,
                notes
            )
            
            logger.info(f"Inspection record completed: {inspection_id} -> {result}")
            return tx_hash
            
        except Exception as e:
            logger.error(f"Failed to complete inspection record: {str(e)}")
            raise BlockchainError(f"Failed to complete inspection record: {str(e)}")
    
    def get_inspection_from_chain(self, inspection_id: int) -> Dict:
        """
        Get inspection record from blockchain
        
        Args:
            inspection_id: Inspection record ID
            
        Returns:
            dict: Inspection record information
        """
        if not self.inspection_manager:
            raise ContractNotFoundError("InspectionManager contract not found")
        
        try:
            inspection_data = self.inspection_manager.functions.getInspection(inspection_id).call()
            
            return {
                'id': inspection_data[0],
                'batch_id': inspection_data[1],
                'inspector': inspection_data[2],
                'result': inspection_data[3],
                'file_url': inspection_data[4],
                'notes': inspection_data[5],
                'inspection_date': datetime.fromtimestamp(inspection_data[6]).isoformat(),
                'created_at': datetime.fromtimestamp(inspection_data[7]).isoformat(),
                'updated_at': datetime.fromtimestamp(inspection_data[8]).isoformat(),
                'exists': inspection_data[9]
            }
            
        except Exception as e:
            logger.error(f"Failed to get inspection record: {str(e)}")
            raise BlockchainError(f"Failed to get inspection record: {str(e)}")
    
    def get_batch_inspections_from_chain(self, batch_id: int) -> List[int]:
        """
        Get all inspection record IDs for a batch
        
        Args:
            batch_id: Batch ID
            
        Returns:
            list: Inspection record ID list
        """
        if not self.inspection_manager:
            raise ContractNotFoundError("InspectionManager contract not found")
        
        try:
            inspection_ids = self.inspection_manager.functions.getBatchInspections(batch_id).call()
            return list(inspection_ids)
            
        except Exception as e:
            logger.error(f"Failed to get batch inspections: {str(e)}")
            raise BlockchainError(f"Failed to get batch inspections: {str(e)}")
    
    def authorize_inspector(self, inspector_address: str) -> str:
        """
        Authorize inspector
        
        Args:
            inspector_address: Inspector address
            
        Returns:
            str: Transaction hash
        """
        if not self.inspection_manager:
            raise ContractNotFoundError("InspectionManager contract not found")
        
        try:
            tx_hash, _ = self._send_transaction(
                self.inspection_manager.functions.authorizeInspector,
                inspector_address
            )
            
            logger.info(f"Inspector authorized: {inspector_address}")
            return tx_hash
            
        except Exception as e:
            logger.error(f"Failed to authorize inspector: {str(e)}")
            raise BlockchainError(f"Failed to authorize inspector: {str(e)}")
    
    def is_authorized_inspector(self, inspector_address: str) -> bool:
        """
        Check if the inspector is authorized
        
        Args:
            inspector_address: Inspector address
            
        Returns:
            bool: Whether the inspector is authorized
        """
        if not self.inspection_manager:
            raise ContractNotFoundError("InspectionManager contract not found")
        
        try:
            return self.inspection_manager.functions.isAuthorizedInspector(inspector_address).call()
            
        except Exception as e:
            logger.error(f"Failed to check inspector permission: {str(e)}")
            return False
    
    def get_account_address(self) -> str:
        """Get current account address"""
        if not self.account:
            raise BlockchainError("No account configured")
        return self.account.address
    
    def get_account_balance(self) -> float:
        """Get account balance (ETH)"""
        if not self.account:
            raise BlockchainError("No account configured")
        balance = self.w3.eth.get_balance(self.account.address)
        return float(Web3.from_wei(balance, 'ether'))
    
    def get_network_info(self) -> Dict:
        """Get network information"""
        return {
            'network_name': self.network_name,
            'network_config': self.network_config,
            'chain_id': self.w3.eth.chain_id,
            'latest_block': self.w3.eth.block_number,
            'is_connected': self.w3.is_connected()
        }
    
    def get_contract_info(self) -> Dict:
        """Get contract information"""
        return {
            'batch_registry': {
                'address': self.batch_registry.address if self.batch_registry else None,
                'is_loaded': self.batch_registry is not None
            },
            'inspection_manager': {
                'address': self.inspection_manager.address if self.inspection_manager else None,
                'is_loaded': self.inspection_manager is not None
            }
        }

# Singleton instance
_blockchain_service = None

def get_blockchain_service(network_name: str = None, private_key: str = None) -> BlockchainService:
    """Get blockchain service instance (singleton mode)"""
    global _blockchain_service
    if _blockchain_service is None:
        _blockchain_service = BlockchainService(network_name, private_key)
    return _blockchain_service

def reset_blockchain_service():
    """Reset blockchain service instance"""
    global _blockchain_service
    _blockchain_service = None
