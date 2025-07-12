# -*- coding: utf-8 -*-
"""
区块链服务测试文件
"""

import os
import sys
import unittest
from unittest.mock import Mock, patch, MagicMock

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.blockchain import (
    BlockchainService,
    BlockchainError,
    ContractNotFoundError,
    InsufficientFundsError,
    get_blockchain_service,
    reset_blockchain_service
)

class TestBlockchainService(unittest.TestCase):
    """区块链服务测试类"""
    
    def setUp(self):
        """设置测试环境"""
        self.test_private_key = "0x" + "0" * 64  # 测试私钥
        self.test_batch_data = {
            'batch_number': 'TEST-001',
            'product_name': '测试产品',
            'origin': '测试产地',
            'quantity': 100,
            'unit': 'kg',
            'harvest_date': '2024-01-01T00:00:00',
            'expiry_date': '2024-12-31T23:59:59'
        }
        
    def tearDown(self):
        """清理测试环境"""
        reset_blockchain_service()
    
    @patch('services.blockchain.Web3')
    def test_init_web3_success(self, mock_web3):
        """测试Web3初始化成功"""
        # 模拟Web3连接成功
        mock_w3_instance = Mock()
        mock_w3_instance.is_connected.return_value = True
        mock_w3_instance.eth.chain_id = 1337
        mock_web3.return_value = mock_w3_instance
        
        service = BlockchainService()
        self.assertIsNotNone(service.w3)
        self.assertEqual(service.network_name, 'development')
    
    @patch('services.blockchain.Web3')
    def test_init_web3_connection_failed(self, mock_web3):
        """测试Web3连接失败"""
        # 模拟Web3连接失败
        mock_w3_instance = Mock()
        mock_w3_instance.is_connected.return_value = False
        mock_web3.return_value = mock_w3_instance
        
        with self.assertRaises(BlockchainError):
            BlockchainService()
    
    @patch('services.blockchain.Web3')
    @patch('services.blockchain.Account')
    def test_init_account_success(self, mock_account, mock_web3):
        """测试账户初始化成功"""
        # 模拟Web3连接
        mock_w3_instance = Mock()
        mock_w3_instance.is_connected.return_value = True
        mock_w3_instance.eth.chain_id = 1337
        mock_w3_instance.eth.get_balance.return_value = 1000000000000000000  # 1 ETH
        mock_web3.return_value = mock_w3_instance
        
        # 模拟账户创建
        mock_account_instance = Mock()
        mock_account_instance.address = '0x1234567890abcdef'
        mock_account.from_key.return_value = mock_account_instance
        
        service = BlockchainService(private_key=self.test_private_key)
        self.assertIsNotNone(service.account)
        self.assertEqual(service.account.address, '0x1234567890abcdef')
    
    @patch('services.blockchain.Web3')
    def test_init_account_no_private_key(self, mock_web3):
        """测试没有私钥的账户初始化"""
        # 模拟Web3连接
        mock_w3_instance = Mock()
        mock_w3_instance.is_connected.return_value = True
        mock_w3_instance.eth.chain_id = 1337
        mock_web3.return_value = mock_w3_instance
        
        service = BlockchainService()
        self.assertIsNone(service.account)
    
    @patch('services.blockchain.Web3')
    @patch('services.blockchain.get_contract_address')
    @patch('services.blockchain.get_contract_abi')
    def test_init_contracts_success(self, mock_get_abi, mock_get_address, mock_web3):
        """测试合约初始化成功"""
        # 模拟Web3连接
        mock_w3_instance = Mock()
        mock_w3_instance.is_connected.return_value = True
        mock_w3_instance.eth.chain_id = 1337
        mock_w3_instance.eth.contract.return_value = Mock()
        mock_web3.return_value = mock_w3_instance
        
        # 模拟合约地址和ABI
        mock_get_address.return_value = '0x1234567890abcdef1234567890abcdef12345678'
        mock_get_abi.return_value = [{'name': 'test'}]
        
        service = BlockchainService()
        self.assertIsNotNone(service.batch_registry)
        self.assertIsNotNone(service.inspection_manager)
    
    @patch('services.blockchain.Web3')
    @patch('services.blockchain.get_contract_address')
    def test_init_contracts_no_address(self, mock_get_address, mock_web3):
        """测试合约地址未配置"""
        # 模拟Web3连接
        mock_w3_instance = Mock()
        mock_w3_instance.is_connected.return_value = True
        mock_w3_instance.eth.chain_id = 1337
        mock_web3.return_value = mock_w3_instance
        
        # 模拟合约地址为空
        mock_get_address.return_value = '0x0000000000000000000000000000000000000000'
        
        service = BlockchainService()
        self.assertIsNone(service.batch_registry)
        self.assertIsNone(service.inspection_manager)
    
    @patch('services.blockchain.Web3')
    def test_send_transaction_no_account(self, mock_web3):
        """测试没有账户时发送交易"""
        # 模拟Web3连接
        mock_w3_instance = Mock()
        mock_w3_instance.is_connected.return_value = True
        mock_w3_instance.eth.chain_id = 1337
        mock_web3.return_value = mock_w3_instance
        
        service = BlockchainService()
        
        # 模拟合约函数
        mock_contract_function = Mock()
        
        with self.assertRaises(BlockchainError):
            service._send_transaction(mock_contract_function)
    
    @patch('services.blockchain.Web3')
    def test_create_batch_no_contract(self, mock_web3):
        """测试没有合约时创建批次"""
        # 模拟Web3连接
        mock_w3_instance = Mock()
        mock_w3_instance.is_connected.return_value = True
        mock_w3_instance.eth.chain_id = 1337
        mock_web3.return_value = mock_w3_instance
        
        service = BlockchainService()
        service.batch_registry = None
        
        with self.assertRaises(ContractNotFoundError):
            service.create_batch_on_chain(self.test_batch_data)
    
    @patch('services.blockchain.Web3')
    def test_create_inspection_no_contract(self, mock_web3):
        """测试没有合约时创建检验记录"""
        # 模拟Web3连接
        mock_w3_instance = Mock()
        mock_w3_instance.is_connected.return_value = True
        mock_w3_instance.eth.chain_id = 1337
        mock_web3.return_value = mock_w3_instance
        
        service = BlockchainService()
        service.inspection_manager = None
        
        with self.assertRaises(ContractNotFoundError):
            service.create_inspection_on_chain(1, 'http://test.com', 'test notes')
    
    @patch('services.blockchain.Web3')
    @patch('services.blockchain.get_contract_address')
    @patch('services.blockchain.get_contract_abi')
    def test_get_network_info(self, mock_get_abi, mock_get_address, mock_web3):
        """测试获取网络信息"""
        # 模拟Web3连接
        mock_w3_instance = Mock()
        mock_w3_instance.is_connected.return_value = True
        mock_w3_instance.eth.chain_id = 1337
        mock_w3_instance.eth.block_number = 12345
        mock_web3.return_value = mock_w3_instance
        
        service = BlockchainService()
        network_info = service.get_network_info()
        
        self.assertEqual(network_info['network_name'], 'development')
        self.assertEqual(network_info['chain_id'], 1337)
        self.assertEqual(network_info['latest_block'], 12345)
        self.assertTrue(network_info['is_connected'])
    
    @patch('services.blockchain.Web3')
    @patch('services.blockchain.get_contract_address')
    @patch('services.blockchain.get_contract_abi')
    def test_get_contract_info(self, mock_get_abi, mock_get_address, mock_web3):
        """测试获取合约信息"""
        # 模拟Web3连接
        mock_w3_instance = Mock()
        mock_w3_instance.is_connected.return_value = True
        mock_w3_instance.eth.chain_id = 1337
        
        # 模拟合约实例
        mock_contract = Mock()
        mock_contract.address = '0x1234567890abcdef1234567890abcdef12345678'
        mock_w3_instance.eth.contract.return_value = mock_contract
        mock_web3.return_value = mock_w3_instance
        
        # 模拟合约地址和ABI
        mock_get_address.return_value = '0x1234567890abcdef1234567890abcdef12345678'
        mock_get_abi.return_value = [{'name': 'test'}]
        
        service = BlockchainService()
        contract_info = service.get_contract_info()
        
        self.assertEqual(contract_info['batch_registry']['address'], '0x1234567890abcdef1234567890abcdef12345678')
        self.assertTrue(contract_info['batch_registry']['is_loaded'])
        self.assertEqual(contract_info['inspection_manager']['address'], '0x1234567890abcdef1234567890abcdef12345678')
        self.assertTrue(contract_info['inspection_manager']['is_loaded'])
    
    @patch('services.blockchain.Web3')
    @patch('services.blockchain.Account')
    def test_get_account_info(self, mock_account, mock_web3):
        """测试获取账户信息"""
        # 模拟Web3连接
        mock_w3_instance = Mock()
        mock_w3_instance.is_connected.return_value = True
        mock_w3_instance.eth.chain_id = 1337
        mock_w3_instance.eth.get_balance.return_value = 1000000000000000000  # 1 ETH
        mock_web3.return_value = mock_w3_instance
        
        # 模拟账户
        mock_account_instance = Mock()
        mock_account_instance.address = '0x1234567890abcdef'
        mock_account.from_key.return_value = mock_account_instance
        
        service = BlockchainService(private_key=self.test_private_key)
        
        self.assertEqual(service.get_account_address(), '0x1234567890abcdef')
        self.assertEqual(service.get_account_balance(), 1.0)
    
    @patch('services.blockchain.Web3')
    def test_get_account_info_no_account(self, mock_web3):
        """测试没有账户时获取账户信息"""
        # 模拟Web3连接
        mock_w3_instance = Mock()
        mock_w3_instance.is_connected.return_value = True
        mock_w3_instance.eth.chain_id = 1337
        mock_web3.return_value = mock_w3_instance
        
        service = BlockchainService()
        
        with self.assertRaises(BlockchainError):
            service.get_account_address()
        
        with self.assertRaises(BlockchainError):
            service.get_account_balance()
    
    def test_get_blockchain_service_singleton(self):
        """测试单例模式"""
        with patch('services.blockchain.Web3') as mock_web3:
            # 模拟Web3连接
            mock_w3_instance = Mock()
            mock_w3_instance.is_connected.return_value = True
            mock_w3_instance.eth.chain_id = 1337
            mock_web3.return_value = mock_w3_instance
            
            service1 = get_blockchain_service()
            service2 = get_blockchain_service()
            
            self.assertIs(service1, service2)
    
    def test_reset_blockchain_service(self):
        """测试重置区块链服务"""
        with patch('services.blockchain.Web3') as mock_web3:
            # 模拟Web3连接
            mock_w3_instance = Mock()
            mock_w3_instance.is_connected.return_value = True
            mock_w3_instance.eth.chain_id = 1337
            mock_web3.return_value = mock_w3_instance
            
            service1 = get_blockchain_service()
            reset_blockchain_service()
            service2 = get_blockchain_service()
            
            self.assertIsNot(service1, service2)

class TestBlockchainIntegration(unittest.TestCase):
    """区块链集成测试类（需要真实的区块链网络）"""
    
    def setUp(self):
        """设置测试环境"""
        self.test_private_key = os.getenv('TEST_PRIVATE_KEY')
        self.test_network = os.getenv('TEST_NETWORK', 'development')
    
    def test_network_connection(self):
        """测试网络连接（需要真实网络）"""
        if not self.test_private_key:
            self.skipTest("未设置测试私钥，跳过集成测试")
        
        try:
            service = BlockchainService(
                network_name=self.test_network,
                private_key=self.test_private_key
            )
            
            # 检查网络连接
            network_info = service.get_network_info()
            self.assertTrue(network_info['is_connected'])
            
            # 检查账户余额
            balance = service.get_account_balance()
            self.assertIsInstance(balance, float)
            
        except Exception as e:
            self.skipTest(f"集成测试失败: {str(e)}")

if __name__ == '__main__':
    print("🧪 运行区块链服务测试...")
    print("=" * 50)
    
    # 运行单元测试
    unittest.main(verbosity=2, exit=False)
    
    print("\n" + "=" * 50)
    print("✅ 区块链服务测试完成！")
    print("\n📝 注意事项：")
    print("1. 集成测试需要设置环境变量 TEST_PRIVATE_KEY")
    print("2. 需要运行本地区块链网络（如 Ganache）")
    print("3. 需要部署智能合约并更新 deploy_config.py")
    print("4. 生产环境请使用真实的私钥和网络配置") 