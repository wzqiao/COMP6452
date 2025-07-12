# -*- coding: utf-8 -*-
"""
区块链服务层
实现Web3集成和智能合约调用逻辑
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

# 导入合约配置
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

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BlockchainError(Exception):
    """区块链操作异常"""
    pass

class ContractNotFoundError(BlockchainError):
    """合约未找到异常"""
    pass

class InsufficientFundsError(BlockchainError):
    """资金不足异常"""
    pass

class BlockchainService:
    """区块链服务类"""
    
    def __init__(self, network_name: str = None, private_key: str = None):
        """
        初始化区块链服务
        
        Args:
            network_name: 网络名称，默认为development
            private_key: 私钥，用于签名交易
        """
        self.network_name = network_name or DEFAULT_NETWORK
        self.network_config = get_network_config(self.network_name)
        
        # 初始化Web3连接
        self.w3 = self._init_web3()
        
        # 初始化账户
        self.account = self._init_account(private_key)
        
        # 初始化合约实例
        self.batch_registry = None
        self.inspection_manager = None
        self._init_contracts()
        
        logger.info(f"区块链服务已初始化，网络: {self.network_config['name']}")
    
    def _init_web3(self) -> Web3:
        """初始化Web3连接"""
        try:
            w3 = Web3(Web3.HTTPProvider(self.network_config['rpc_url']))
            if not w3.is_connected():
                raise BlockchainError(f"无法连接到网络: {self.network_config['rpc_url']}")
            
            logger.info(f"Web3连接成功，链ID: {w3.eth.chain_id}")
            return w3
        except Exception as e:
            raise BlockchainError(f"Web3初始化失败: {str(e)}")
    
    def _init_account(self, private_key: str = None) -> Optional[LocalAccount]:
        """初始化账户"""
        if not private_key:
            # 从环境变量获取私钥
            private_key = os.getenv('BLOCKCHAIN_PRIVATE_KEY')
        
        if not private_key:
            logger.warning("未提供私钥，某些功能可能无法使用")
            return None
        
        try:
            account = Account.from_key(private_key)
            balance = self.w3.eth.get_balance(account.address)
            logger.info(f"账户地址: {account.address}, 余额: {Web3.from_wei(balance, 'ether')} ETH")
            return account
        except Exception as e:
            logger.error(f"账户初始化失败: {str(e)}")
            return None
    
    def _init_contracts(self):
        """初始化合约实例"""
        try:
            # 初始化BatchRegistry合约
            batch_registry_address = get_contract_address('BatchRegistry', self.network_name)
            if batch_registry_address and batch_registry_address != '0x0000000000000000000000000000000000000000':
                batch_registry_abi = get_contract_abi('BatchRegistry')
                self.batch_registry = self.w3.eth.contract(
                    address=batch_registry_address,
                    abi=batch_registry_abi
                )
                logger.info(f"BatchRegistry合约已加载: {batch_registry_address}")
            
            # 初始化InspectionManager合约
            inspection_manager_address = get_contract_address('InspectionManager', self.network_name)
            if inspection_manager_address and inspection_manager_address != '0x0000000000000000000000000000000000000000':
                inspection_manager_abi = get_contract_abi('InspectionManager')
                self.inspection_manager = self.w3.eth.contract(
                    address=inspection_manager_address,
                    abi=inspection_manager_abi
                )
                logger.info(f"InspectionManager合约已加载: {inspection_manager_address}")
                
        except Exception as e:
            logger.error(f"合约初始化失败: {str(e)}")
    
    def _send_transaction(self, contract_function, *args, **kwargs) -> Tuple[str, Dict]:
        """
        发送交易
        
        Args:
            contract_function: 合约函数
            *args: 函数参数
            **kwargs: 额外参数
        
        Returns:
            tuple: (交易哈希, 交易收据)
        """
        if not self.account:
            raise BlockchainError("未配置账户，无法发送交易")
        
        try:
            # 构建交易
            transaction = contract_function(*args).build_transaction({
                'chainId': self.network_config['chain_id'],
                'gas': kwargs.get('gas', self.network_config['gas_limit']),
                'gasPrice': kwargs.get('gas_price', self.network_config['gas_price']),
                'nonce': self.w3.eth.get_transaction_count(self.account.address),
            })
            
            # 签名交易
            signed_txn = self.account.sign_transaction(transaction)
            
            # 发送交易
            tx_hash = self.w3.eth.send_raw_transaction(signed_txn.rawTransaction)
            
            # 等待交易确认
            tx_receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
            
            if tx_receipt.status == 1:
                logger.info(f"交易成功: {tx_hash.hex()}")
                return tx_hash.hex(), tx_receipt
            else:
                raise BlockchainError(f"交易失败: {tx_hash.hex()}")
                
        except ContractLogicError as e:
            raise BlockchainError(f"合约逻辑错误: {str(e)}")
        except ValueError as e:
            if "insufficient funds" in str(e).lower():
                raise InsufficientFundsError("账户余额不足")
            raise BlockchainError(f"交易错误: {str(e)}")
        except Exception as e:
            raise BlockchainError(f"发送交易失败: {str(e)}")
    
    def create_batch_on_chain(self, batch_data: Dict) -> Tuple[str, int]:
        """
        在区块链上创建批次
        
        Args:
            batch_data: 批次数据
            
        Returns:
            tuple: (交易哈希, 区块链批次ID)
        """
        if not self.batch_registry:
            raise ContractNotFoundError("BatchRegistry合约未找到")
        
        try:
            # 转换时间戳
            harvest_date = int(datetime.fromisoformat(batch_data['harvest_date']).timestamp())
            expiry_date = int(datetime.fromisoformat(batch_data['expiry_date']).timestamp())
            
            # 调用合约函数
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
            
            # 从交易收据中获取批次ID
            batch_id = self._get_batch_id_from_receipt(tx_receipt)
            
            logger.info(f"批次已上链: {batch_data['batch_number']}, 区块链ID: {batch_id}")
            return tx_hash, batch_id
            
        except Exception as e:
            logger.error(f"批次上链失败: {str(e)}")
            raise BlockchainError(f"批次上链失败: {str(e)}")
    
    def _get_batch_id_from_receipt(self, tx_receipt: Dict) -> int:
        """从交易收据中获取批次ID"""
        try:
            # 解析BatchCreated事件
            batch_created_event = self.batch_registry.events.BatchCreated().process_receipt(tx_receipt)
            if batch_created_event:
                return batch_created_event[0]['args']['batchId']
            else:
                raise BlockchainError("未找到BatchCreated事件")
        except Exception as e:
            raise BlockchainError(f"解析批次ID失败: {str(e)}")
    
    def get_batch_from_chain(self, batch_id: int) -> Dict:
        """
        从区块链获取批次信息
        
        Args:
            batch_id: 区块链批次ID
            
        Returns:
            dict: 批次信息
        """
        if not self.batch_registry:
            raise ContractNotFoundError("BatchRegistry合约未找到")
        
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
            logger.error(f"获取批次失败: {str(e)}")
            raise BlockchainError(f"获取批次失败: {str(e)}")
    
    def update_batch_status_on_chain(self, batch_id: int, new_status: str) -> str:
        """
        更新批次状态
        
        Args:
            batch_id: 区块链批次ID
            new_status: 新状态
            
        Returns:
            str: 交易哈希
        """
        if not self.batch_registry:
            raise ContractNotFoundError("BatchRegistry合约未找到")
        
        try:
            # 转换状态
            status_value = BATCH_STATUS.get(new_status.upper())
            if status_value is None:
                raise BlockchainError(f"无效的批次状态: {new_status}")
            
            tx_hash, _ = self._send_transaction(
                self.batch_registry.functions.updateBatchStatus,
                batch_id,
                status_value
            )
            
            logger.info(f"批次状态已更新: {batch_id} -> {new_status}")
            return tx_hash
            
        except Exception as e:
            logger.error(f"更新批次状态失败: {str(e)}")
            raise BlockchainError(f"更新批次状态失败: {str(e)}")
    
    def create_inspection_on_chain(self, batch_id: int, file_url: str, notes: str = "") -> Tuple[str, int]:
        """
        在区块链上创建检验记录
        
        Args:
            batch_id: 区块链批次ID
            file_url: 检验文件URL
            notes: 检验备注
            
        Returns:
            tuple: (交易哈希, 检验记录ID)
        """
        if not self.inspection_manager:
            raise ContractNotFoundError("InspectionManager合约未找到")
        
        try:
            tx_hash, tx_receipt = self._send_transaction(
                self.inspection_manager.functions.createInspection,
                batch_id,
                file_url,
                notes
            )
            
            # 从交易收据中获取检验ID
            inspection_id = self._get_inspection_id_from_receipt(tx_receipt)
            
            logger.info(f"检验记录已上链: 批次ID {batch_id}, 检验ID {inspection_id}")
            return tx_hash, inspection_id
            
        except Exception as e:
            logger.error(f"检验记录上链失败: {str(e)}")
            raise BlockchainError(f"检验记录上链失败: {str(e)}")
    
    def _get_inspection_id_from_receipt(self, tx_receipt: Dict) -> int:
        """从交易收据中获取检验ID"""
        try:
            # 解析InspectionCreated事件
            inspection_created_event = self.inspection_manager.events.InspectionCreated().process_receipt(tx_receipt)
            if inspection_created_event:
                return inspection_created_event[0]['args']['inspectionId']
            else:
                raise BlockchainError("未找到InspectionCreated事件")
        except Exception as e:
            raise BlockchainError(f"解析检验ID失败: {str(e)}")
    
    def complete_inspection_on_chain(self, inspection_id: int, result: str, file_url: str = "", notes: str = "") -> str:
        """
        完成检验记录
        
        Args:
            inspection_id: 检验记录ID
            result: 检验结果
            file_url: 检验文件URL
            notes: 检验备注
            
        Returns:
            str: 交易哈希
        """
        if not self.inspection_manager:
            raise ContractNotFoundError("InspectionManager合约未找到")
        
        try:
            # 转换检验结果
            result_value = INSPECTION_RESULT.get(result.upper())
            if result_value is None:
                raise BlockchainError(f"无效的检验结果: {result}")
            
            tx_hash, _ = self._send_transaction(
                self.inspection_manager.functions.completeInspection,
                inspection_id,
                result_value,
                file_url,
                notes
            )
            
            logger.info(f"检验记录已完成: {inspection_id} -> {result}")
            return tx_hash
            
        except Exception as e:
            logger.error(f"完成检验记录失败: {str(e)}")
            raise BlockchainError(f"完成检验记录失败: {str(e)}")
    
    def get_inspection_from_chain(self, inspection_id: int) -> Dict:
        """
        从区块链获取检验记录
        
        Args:
            inspection_id: 检验记录ID
            
        Returns:
            dict: 检验记录信息
        """
        if not self.inspection_manager:
            raise ContractNotFoundError("InspectionManager合约未找到")
        
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
            logger.error(f"获取检验记录失败: {str(e)}")
            raise BlockchainError(f"获取检验记录失败: {str(e)}")
    
    def get_batch_inspections_from_chain(self, batch_id: int) -> List[int]:
        """
        获取批次的所有检验记录ID
        
        Args:
            batch_id: 批次ID
            
        Returns:
            list: 检验记录ID列表
        """
        if not self.inspection_manager:
            raise ContractNotFoundError("InspectionManager合约未找到")
        
        try:
            inspection_ids = self.inspection_manager.functions.getBatchInspections(batch_id).call()
            return list(inspection_ids)
            
        except Exception as e:
            logger.error(f"获取批次检验记录失败: {str(e)}")
            raise BlockchainError(f"获取批次检验记录失败: {str(e)}")
    
    def authorize_inspector(self, inspector_address: str) -> str:
        """
        授权检验员
        
        Args:
            inspector_address: 检验员地址
            
        Returns:
            str: 交易哈希
        """
        if not self.inspection_manager:
            raise ContractNotFoundError("InspectionManager合约未找到")
        
        try:
            tx_hash, _ = self._send_transaction(
                self.inspection_manager.functions.authorizeInspector,
                inspector_address
            )
            
            logger.info(f"检验员已授权: {inspector_address}")
            return tx_hash
            
        except Exception as e:
            logger.error(f"授权检验员失败: {str(e)}")
            raise BlockchainError(f"授权检验员失败: {str(e)}")
    
    def is_authorized_inspector(self, inspector_address: str) -> bool:
        """
        检查是否为授权检验员
        
        Args:
            inspector_address: 检验员地址
            
        Returns:
            bool: 是否为授权检验员
        """
        if not self.inspection_manager:
            raise ContractNotFoundError("InspectionManager合约未找到")
        
        try:
            return self.inspection_manager.functions.isAuthorizedInspector(inspector_address).call()
            
        except Exception as e:
            logger.error(f"检查检验员权限失败: {str(e)}")
            return False
    
    def get_account_address(self) -> str:
        """获取当前账户地址"""
        if not self.account:
            raise BlockchainError("未配置账户")
        return self.account.address
    
    def get_account_balance(self) -> float:
        """获取账户余额（ETH）"""
        if not self.account:
            raise BlockchainError("未配置账户")
        balance = self.w3.eth.get_balance(self.account.address)
        return float(Web3.from_wei(balance, 'ether'))
    
    def get_network_info(self) -> Dict:
        """获取网络信息"""
        return {
            'network_name': self.network_name,
            'network_config': self.network_config,
            'chain_id': self.w3.eth.chain_id,
            'latest_block': self.w3.eth.block_number,
            'is_connected': self.w3.is_connected()
        }
    
    def get_contract_info(self) -> Dict:
        """获取合约信息"""
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

# 单例实例
_blockchain_service = None

def get_blockchain_service(network_name: str = None, private_key: str = None) -> BlockchainService:
    """获取区块链服务实例（单例模式）"""
    global _blockchain_service
    if _blockchain_service is None:
        _blockchain_service = BlockchainService(network_name, private_key)
    return _blockchain_service

def reset_blockchain_service():
    """重置区块链服务实例"""
    global _blockchain_service
    _blockchain_service = None
