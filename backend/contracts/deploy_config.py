# -*- coding: utf-8 -*-
"""
合约部署配置文件
用于存储合约地址、ABI和网络配置
"""

# 网络配置
NETWORKS = {
    'development': {
        'name': 'Development Network',
        'rpc_url': 'http://127.0.0.1:8545',  # Ganache默认地址
        'chain_id': 1337,
        'gas_limit': 6721975,
        'gas_price': 20000000000,  # 20 Gwei
    },
    'testnet': {
        'name': 'Ethereum Testnet (Sepolia)',
        'rpc_url': 'https://sepolia.infura.io/v3/YOUR_PROJECT_ID',
        'chain_id': 11155111,
        'gas_limit': 3000000,
        'gas_price': 20000000000,
    },
    'mainnet': {
        'name': 'Ethereum Mainnet',
        'rpc_url': 'https://mainnet.infura.io/v3/YOUR_PROJECT_ID',
        'chain_id': 1,
        'gas_limit': 3000000,
        'gas_price': 20000000000,
    }
}

# 合约地址配置（部署后需要更新）
CONTRACT_ADDRESSES = {
    'development': {
        'BatchRegistry': '0x0000000000000000000000000000000000000000',  # 部署后更新
        'InspectionManager': '0x0000000000000000000000000000000000000000',  # 部署后更新
    },
    'testnet': {
        'BatchRegistry': '0x0000000000000000000000000000000000000000',
        'InspectionManager': '0x0000000000000000000000000000000000000000',
    },
    'mainnet': {
        'BatchRegistry': '0x0000000000000000000000000000000000000000',
        'InspectionManager': '0x0000000000000000000000000000000000000000',
    }
}

# BatchRegistry合约ABI（编译后需要更新）
BATCH_REGISTRY_ABI = [
    # 这里需要从编译后的合约中复制ABI
    # 示例结构：
    {
        "inputs": [],
        "name": "createBatch",
        "outputs": [{"name": "", "type": "uint256"}],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    # ... 其他函数定义
]

# InspectionManager合约ABI（编译后需要更新）
INSPECTION_MANAGER_ABI = [
    # 这里需要从编译后的合约中复制ABI
    # 示例结构：
    {
        "inputs": [],
        "name": "createInspection",
        "outputs": [{"name": "", "type": "uint256"}],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    # ... 其他函数定义
]

# 默认网络
DEFAULT_NETWORK = 'development'

# 私钥配置（仅用于开发环境）
DEVELOPMENT_PRIVATE_KEYS = {
    'owner': '0x0000000000000000000000000000000000000000000000000000000000000000',  # 合约所有者私钥
    'inspector1': '0x0000000000000000000000000000000000000000000000000000000000000000',  # 检验员1私钥
    'inspector2': '0x0000000000000000000000000000000000000000000000000000000000000000',  # 检验员2私钥
}

# 合约常量
BATCH_STATUS = {
    'PENDING': 0,
    'INSPECTED': 1,
    'APPROVED': 2,
    'REJECTED': 3
}

INSPECTION_RESULT = {
    'PENDING': 0,
    'PASSED': 1,
    'FAILED': 2,
    'NEEDS_RECHECK': 3
}

# 事件主题哈希（用于过滤事件）
EVENT_SIGNATURES = {
    'BatchCreated': '0x...',      # 计算后更新
    'BatchStatusUpdated': '0x...',
    'InspectionCreated': '0x...',
    'InspectionCompleted': '0x...',
}

def get_network_config(network_name=None):
    """获取网络配置"""
    if network_name is None:
        network_name = DEFAULT_NETWORK
    return NETWORKS.get(network_name, NETWORKS[DEFAULT_NETWORK])

def get_contract_address(contract_name, network_name=None):
    """获取合约地址"""
    if network_name is None:
        network_name = DEFAULT_NETWORK
    return CONTRACT_ADDRESSES.get(network_name, {}).get(contract_name)

def get_contract_abi(contract_name):
    """获取合约ABI"""
    if contract_name == 'BatchRegistry':
        return BATCH_REGISTRY_ABI
    elif contract_name == 'InspectionManager':
        return INSPECTION_MANAGER_ABI
    else:
        raise ValueError(f"Unknown contract: {contract_name}") 