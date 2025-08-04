# -*- coding: utf-8 -*-
"""
Contract deployment configuration file
Used to store contract addresses, ABIs, and network configurations
"""

# Network configuration
NETWORKS = {
    'development': {
        'name': 'Development Network',
        'rpc_url': 'http://127.0.0.1:8545',  # Ganache default address
        'chain_id': 1337,
        'gas_limit': 6721975,
        'gas_price': 20000000000,  # 20 Gwei
    },
    'testnet': {
        'name': 'Ethereum Testnet (Sepolia)',
        'rpc_url': 'https://sepolia.drpc.org',  # Sepolia testnet RPC address
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

# Contract address configuration (needs to be updated after deployment)
CONTRACT_ADDRESSES = {
    'development': {
        'BatchRegistry': '0x0d79A6bcEceC353339CC5a3E577B0B56a4AA973f',
        'InspectionManager': '0xD5D27407c79d39D1bb0a6154B3BAd147A6df7640',
    },
    'testnet': {
        'BatchRegistry': '0x0d79A6bcEceC353339CC5a3E577B0B56a4AA973f',
        'InspectionManager': '0xD5D27407c79d39D1bb0a6154B3BAd147A6df7640',
    },
    'mainnet': {
        'BatchRegistry': '0x0000000000000000000000000000000000000000',
        'InspectionManager': '0x0000000000000000000000000000000000000000',
    }
}

# BatchRegistry contract ABI (obtained from Remix)
BATCH_REGISTRY_ABI = [
    {
        "inputs": [
            {
                "internalType": "address",
                "name": "inspector",
                "type": "address"
            }
        ],
        "name": "authorizeInspector",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [],
        "stateMutability": "nonpayable",
        "type": "constructor"
    },
    {
        "anonymous": False,
        "inputs": [
            {
                "indexed": True,
                "internalType": "uint256",
                "name": "batchId",
                "type": "uint256"
            },
            {
                "indexed": False,
                "internalType": "string",
                "name": "batchNumber",
                "type": "string"
            },
            {
                "indexed": False,
                "internalType": "string",
                "name": "productName",
                "type": "string"
            },
            {
                "indexed": True,
                "internalType": "address",
                "name": "owner",
                "type": "address"
            },
            {
                "indexed": False,
                "internalType": "uint256",
                "name": "timestamp",
                "type": "uint256"
            }
        ],
        "name": "BatchCreated",
        "type": "event"
    },
    {
        "anonymous": False,
        "inputs": [
            {
                "indexed": True,
                "internalType": "uint256",
                "name": "batchId",
                "type": "uint256"
            },
            {
                "indexed": False,
                "internalType": "enum BatchRegistry.BatchStatus",
                "name": "oldStatus",
                "type": "uint8"
            },
            {
                "indexed": False,
                "internalType": "enum BatchRegistry.BatchStatus",
                "name": "newStatus",
                "type": "uint8"
            },
            {
                "indexed": True,
                "internalType": "address",
                "name": "updatedBy",
                "type": "address"
            },
            {
                "indexed": False,
                "internalType": "uint256",
                "name": "timestamp",
                "type": "uint256"
            }
        ],
        "name": "BatchStatusUpdated",
        "type": "event"
    },
    {
        "inputs": [
            {
                "internalType": "string",
                "name": "_batchNumber",
                "type": "string"
            },
            {
                "internalType": "string",
                "name": "_productName",
                "type": "string"
            },
            {
                "internalType": "string",
                "name": "_origin",
                "type": "string"
            },
            {
                "internalType": "uint256",
                "name": "_quantity",
                "type": "uint256"
            },
            {
                "internalType": "string",
                "name": "_unit",
                "type": "string"
            },
            {
                "internalType": "uint256",
                "name": "_harvestDate",
                "type": "uint256"
            },
            {
                "internalType": "uint256",
                "name": "_expiryDate",
                "type": "uint256"
            }
        ],
        "name": "createBatch",
        "outputs": [
            {
                "internalType": "uint256",
                "name": "",
                "type": "uint256"
            }
        ],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "anonymous": False,
        "inputs": [
            {
                "indexed": True,
                "internalType": "address",
                "name": "inspector",
                "type": "address"
            },
            {
                "indexed": True,
                "internalType": "address",
                "name": "authorizedBy",
                "type": "address"
            },
            {
                "indexed": False,
                "internalType": "uint256",
                "name": "timestamp",
                "type": "uint256"
            }
        ],
        "name": "InspectorAuthorized",
        "type": "event"
    },
    {
        "anonymous": False,
        "inputs": [
            {
                "indexed": True,
                "internalType": "address",
                "name": "inspector",
                "type": "address"
            },
            {
                "indexed": True,
                "internalType": "address",
                "name": "revokedBy",
                "type": "address"
            },
            {
                "indexed": False,
                "internalType": "uint256",
                "name": "timestamp",
                "type": "uint256"
            }
        ],
        "name": "InspectorRevoked",
        "type": "event"
    },
    {
        "inputs": [
            {
                "internalType": "address",
                "name": "inspector",
                "type": "address"
            }
        ],
        "name": "revokeInspector",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [
            {
                "internalType": "uint256",
                "name": "batchId",
                "type": "uint256"
            },
            {
                "internalType": "enum BatchRegistry.BatchStatus",
                "name": "newStatus",
                "type": "uint8"
            }
        ],
        "name": "updateBatchStatus",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [
            {
                "internalType": "address",
                "name": "",
                "type": "address"
            }
        ],
        "name": "authorizedInspectors",
        "outputs": [
            {
                "internalType": "bool",
                "name": "",
                "type": "bool"
            }
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [
            {
                "internalType": "uint256",
                "name": "",
                "type": "uint256"
            }
        ],
        "name": "batches",
        "outputs": [
            {
                "internalType": "uint256",
                "name": "id",
                "type": "uint256"
            },
            {
                "internalType": "string",
                "name": "batchNumber",
                "type": "string"
            },
            {
                "internalType": "string",
                "name": "productName",
                "type": "string"
            },
            {
                "internalType": "string",
                "name": "origin",
                "type": "string"
            },
            {
                "internalType": "uint256",
                "name": "quantity",
                "type": "uint256"
            },
            {
                "internalType": "string",
                "name": "unit",
                "type": "string"
            },
            {
                "internalType": "uint256",
                "name": "harvestDate",
                "type": "uint256"
            },
            {
                "internalType": "uint256",
                "name": "expiryDate",
                "type": "uint256"
            },
            {
                "internalType": "enum BatchRegistry.BatchStatus",
                "name": "status",
                "type": "uint8"
            },
            {
                "internalType": "address",
                "name": "owner",
                "type": "address"
            },
            {
                "internalType": "uint256",
                "name": "timestamp",
                "type": "uint256"
            },
            {
                "internalType": "bool",
                "name": "exists",
                "type": "bool"
            }
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [
            {
                "internalType": "uint256",
                "name": "batchId",
                "type": "uint256"
            }
        ],
        "name": "getBatch",
        "outputs": [
            {
                "components": [
                    {
                        "internalType": "uint256",
                        "name": "id",
                        "type": "uint256"
                    },
                    {
                        "internalType": "string",
                        "name": "batchNumber",
                        "type": "string"
                    },
                    {
                        "internalType": "string",
                        "name": "productName",
                        "type": "string"
                    },
                    {
                        "internalType": "string",
                        "name": "origin",
                        "type": "string"
                    },
                    {
                        "internalType": "uint256",
                        "name": "quantity",
                        "type": "uint256"
                    },
                    {
                        "internalType": "string",
                        "name": "unit",
                        "type": "string"
                    },
                    {
                        "internalType": "uint256",
                        "name": "harvestDate",
                        "type": "uint256"
                    },
                    {
                        "internalType": "uint256",
                        "name": "expiryDate",
                        "type": "uint256"
                    },
                    {
                        "internalType": "enum BatchRegistry.BatchStatus",
                        "name": "status",
                        "type": "uint8"
                    },
                    {
                        "internalType": "address",
                        "name": "owner",
                        "type": "address"
                    },
                    {
                        "internalType": "uint256",
                        "name": "timestamp",
                        "type": "uint256"
                    },
                    {
                        "internalType": "bool",
                        "name": "exists",
                        "type": "bool"
                    }
                ],
                "internalType": "struct BatchRegistry.Batch",
                "name": "",
                "type": "tuple"
            }
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "getTotalBatches",
        "outputs": [
            {
                "internalType": "uint256",
                "name": "",
                "type": "uint256"
            }
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [
            {
                "internalType": "address",
                "name": "user",
                "type": "address"
            }
        ],
        "name": "getUserBatches",
        "outputs": [
            {
                "internalType": "uint256[]",
                "name": "",
                "type": "uint256[]"
            }
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [
            {
                "internalType": "address",
                "name": "inspector",
                "type": "address"
            }
        ],
        "name": "isAuthorizedInspector",
        "outputs": [
            {
                "internalType": "bool",
                "name": "",
                "type": "bool"
            }
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [
            {
                "internalType": "enum BatchRegistry.BatchStatus",
                "name": "current",
                "type": "uint8"
            },
            {
                "internalType": "enum BatchRegistry.BatchStatus",
                "name": "next",
                "type": "uint8"
            }
        ],
        "name": "isValidStatusTransition",
        "outputs": [
            {
                "internalType": "bool",
                "name": "",
                "type": "bool"
            }
        ],
        "stateMutability": "pure",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "nextBatchId",
        "outputs": [
            {
                "internalType": "uint256",
                "name": "",
                "type": "uint256"
            }
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "owner",
        "outputs": [
            {
                "internalType": "address",
                "name": "",
                "type": "address"
            }
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "totalBatches",
        "outputs": [
            {
                "internalType": "uint256",
                "name": "",
                "type": "uint256"
            }
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [
            {
                "internalType": "address",
                "name": "",
                "type": "address"
            },
            {
                "internalType": "uint256",
                "name": "",
                "type": "uint256"
            }
        ],
        "name": "userBatches",
        "outputs": [
            {
                "internalType": "uint256",
                "name": "",
                "type": "uint256"
            }
        ],
        "stateMutability": "view",
        "type": "function"
    }
]

# InspectionManager contract ABI (obtained from Remix)
INSPECTION_MANAGER_ABI = [
    {
        "inputs": [
            {
                "internalType": "address",
                "name": "_batchRegistryAddress",
                "type": "address"
            }
        ],
        "stateMutability": "nonpayable",
        "type": "constructor"
    },
    {
        "anonymous": False,
        "inputs": [
            {
                "indexed": True,
                "internalType": "uint256",
                "name": "batchId",
                "type": "uint256"
            },
            {
                "indexed": False,
                "internalType": "enum BatchRegistry.BatchStatus",
                "name": "newStatus",
                "type": "uint8"
            },
            {
                "indexed": False,
                "internalType": "uint256",
                "name": "timestamp",
                "type": "uint256"
            }
        ],
        "name": "BatchStatusSynced",
        "type": "event"
    },
    {
        "inputs": [
            {
                "internalType": "uint256",
                "name": "inspectionId",
                "type": "uint256"
            },
            {
                "internalType": "enum InspectionManager.InspectionResult",
                "name": "result",
                "type": "uint8"
            },
            {
                "internalType": "string",
                "name": "fileUrl",
                "type": "string"
            },
            {
                "internalType": "string",
                "name": "notes",
                "type": "string"
            }
        ],
        "name": "completeInspection",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [
            {
                "internalType": "uint256",
                "name": "batchId",
                "type": "uint256"
            },
            {
                "internalType": "string",
                "name": "fileUrl",
                "type": "string"
            },
            {
                "internalType": "string",
                "name": "notes",
                "type": "string"
            }
        ],
        "name": "createInspection",
        "outputs": [
            {
                "internalType": "uint256",
                "name": "",
                "type": "uint256"
            }
        ],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "anonymous": False,
        "inputs": [
            {
                "indexed": True,
                "internalType": "uint256",
                "name": "inspectionId",
                "type": "uint256"
            },
            {
                "indexed": True,
                "internalType": "uint256",
                "name": "batchId",
                "type": "uint256"
            },
            {
                "indexed": False,
                "internalType": "enum InspectionManager.InspectionResult",
                "name": "result",
                "type": "uint8"
            },
            {
                "indexed": True,
                "internalType": "address",
                "name": "inspector",
                "type": "address"
            },
            {
                "indexed": False,
                "internalType": "uint256",
                "name": "timestamp",
                "type": "uint256"
            }
        ],
        "name": "InspectionCompleted",
        "type": "event"
    },
    {
        "anonymous": False,
        "inputs": [
            {
                "indexed": True,
                "internalType": "uint256",
                "name": "inspectionId",
                "type": "uint256"
            },
            {
                "indexed": True,
                "internalType": "uint256",
                "name": "batchId",
                "type": "uint256"
            },
            {
                "indexed": True,
                "internalType": "address",
                "name": "inspector",
                "type": "address"
            },
            {
                "indexed": False,
                "internalType": "uint256",
                "name": "timestamp",
                "type": "uint256"
            }
        ],
        "name": "InspectionCreated",
        "type": "event"
    },
    {
        "anonymous": False,
        "inputs": [
            {
                "indexed": True,
                "internalType": "uint256",
                "name": "inspectionId",
                "type": "uint256"
            },
            {
                "indexed": True,
                "internalType": "uint256",
                "name": "batchId",
                "type": "uint256"
            },
            {
                "indexed": False,
                "internalType": "enum InspectionManager.InspectionResult",
                "name": "oldResult",
                "type": "uint8"
            },
            {
                "indexed": False,
                "internalType": "enum InspectionManager.InspectionResult",
                "name": "newResult",
                "type": "uint8"
            },
            {
                "indexed": True,
                "internalType": "address",
                "name": "updatedBy",
                "type": "address"
            },
            {
                "indexed": False,
                "internalType": "uint256",
                "name": "timestamp",
                "type": "uint256"
            }
        ],
        "name": "InspectionUpdated",
        "type": "event"
    },
    {
        "inputs": [
            {
                "internalType": "address",
                "name": "_batchRegistryAddress",
                "type": "address"
            }
        ],
        "name": "updateBatchRegistry",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [
            {
                "internalType": "uint256",
                "name": "inspectionId",
                "type": "uint256"
            },
            {
                "internalType": "enum InspectionManager.InspectionResult",
                "name": "result",
                "type": "uint8"
            },
            {
                "internalType": "string",
                "name": "notes",
                "type": "string"
            }
        ],
        "name": "updateInspectionResult",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [
            {
                "internalType": "uint256",
                "name": "",
                "type": "uint256"
            },
            {
                "internalType": "uint256",
                "name": "",
                "type": "uint256"
            }
        ],
        "name": "batchInspections",
        "outputs": [
            {
                "internalType": "uint256",
                "name": "",
                "type": "uint256"
            }
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "batchRegistry",
        "outputs": [
            {
                "internalType": "contract BatchRegistry",
                "name": "",
                "type": "address"
            }
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [
            {
                "internalType": "uint256",
                "name": "batchId",
                "type": "uint256"
            }
        ],
        "name": "getBatchInspections",
        "outputs": [
            {
                "internalType": "uint256[]",
                "name": "",
                "type": "uint256[]"
            }
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "getBatchRegistryAddress",
        "outputs": [
            {
                "internalType": "address",
                "name": "",
                "type": "address"
            }
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [
            {
                "internalType": "uint256",
                "name": "inspectionId",
                "type": "uint256"
            }
        ],
        "name": "getInspection",
        "outputs": [
            {
                "components": [
                    {
                        "internalType": "uint256",
                        "name": "id",
                        "type": "uint256"
                    },
                    {
                        "internalType": "uint256",
                        "name": "batchId",
                        "type": "uint256"
                    },
                    {
                        "internalType": "address",
                        "name": "inspector",
                        "type": "address"
                    },
                    {
                        "internalType": "enum InspectionManager.InspectionResult",
                        "name": "result",
                        "type": "uint8"
                    },
                    {
                        "internalType": "string",
                        "name": "fileUrl",
                        "type": "string"
                    },
                    {
                        "internalType": "string",
                        "name": "notes",
                        "type": "string"
                    },
                    {
                        "internalType": "uint256",
                        "name": "inspectionDate",
                        "type": "uint256"
                    },
                    {
                        "internalType": "uint256",
                        "name": "createdAt",
                        "type": "uint256"
                    },
                    {
                        "internalType": "uint256",
                        "name": "updatedAt",
                        "type": "uint256"
                    },
                    {
                        "internalType": "bool",
                        "name": "exists",
                        "type": "bool"
                    }
                ],
                "internalType": "struct InspectionManager.Inspection",
                "name": "",
                "type": "tuple"
            }
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [
            {
                "internalType": "address",
                "name": "inspector",
                "type": "address"
            }
        ],
        "name": "getInspectorInspections",
        "outputs": [
            {
                "internalType": "uint256[]",
                "name": "",
                "type": "uint256[]"
            }
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [
            {
                "internalType": "uint256",
                "name": "batchId",
                "type": "uint256"
            }
        ],
        "name": "getLatestInspectionResult",
        "outputs": [
            {
                "internalType": "enum InspectionManager.InspectionResult",
                "name": "",
                "type": "uint8"
            }
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "getTotalInspections",
        "outputs": [
            {
                "internalType": "uint256",
                "name": "",
                "type": "uint256"
            }
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [
            {
                "internalType": "uint256",
                "name": "",
                "type": "uint256"
            }
        ],
        "name": "inspections",
        "outputs": [
            {
                "internalType": "uint256",
                "name": "id",
                "type": "uint256"
            },
            {
                "internalType": "uint256",
                "name": "batchId",
                "type": "uint256"
            },
            {
                "internalType": "address",
                "name": "inspector",
                "type": "address"
            },
            {
                "internalType": "enum InspectionManager.InspectionResult",
                "name": "result",
                "type": "uint8"
            },
            {
                "internalType": "string",
                "name": "fileUrl",
                "type": "string"
            },
            {
                "internalType": "string",
                "name": "notes",
                "type": "string"
            },
            {
                "internalType": "uint256",
                "name": "inspectionDate",
                "type": "uint256"
            },
            {
                "internalType": "uint256",
                "name": "createdAt",
                "type": "uint256"
            },
            {
                "internalType": "uint256",
                "name": "updatedAt",
                "type": "uint256"
            },
            {
                "internalType": "bool",
                "name": "exists",
                "type": "bool"
            }
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [
            {
                "internalType": "address",
                "name": "",
                "type": "address"
            },
            {
                "internalType": "uint256",
                "name": "",
                "type": "uint256"
            }
        ],
        "name": "inspectorInspections",
        "outputs": [
            {
                "internalType": "uint256",
                "name": "",
                "type": "uint256"
            }
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [
            {
                "internalType": "address",
                "name": "inspector",
                "type": "address"
            }
        ],
        "name": "isAuthorizedInspector",
        "outputs": [
            {
                "internalType": "bool",
                "name": "",
                "type": "bool"
            }
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "nextInspectionId",
        "outputs": [
            {
                "internalType": "uint256",
                "name": "",
                "type": "uint256"
            }
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "owner",
        "outputs": [
            {
                "internalType": "address",
                "name": "",
                "type": "address"
            }
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "totalInspections",
        "outputs": [
            {
                "internalType": "uint256",
                "name": "",
                "type": "uint256"
            }
        ],
        "stateMutability": "view",
        "type": "function"
    }
]

# Default network
DEFAULT_NETWORK = 'testnet'

# Private key configuration (only for development environment)
DEVELOPMENT_PRIVATE_KEYS = {
    'owner': '10c4bc8e616fba553e0cb005e66d1113a0d5d1ecfbed279deea60ea62425919c',  
    'inspector1': 'e211354e3b846f2def358c3936dccbc08faea2cf8e4e3ed0b813c59c4824e373',  
    'inspector2': '0xPrivate key from Remix or wallet',  
}

# Contract constants
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

# Event topic hash (used to filter events)
EVENT_SIGNATURES = {
    'BatchCreated': '0x...',      # Can be calculated using web3.keccak(text='BatchCreated(...)')
    'BatchStatusUpdated': '0x...',
    'InspectionCreated': '0x...',
    'InspectionCompleted': '0x...', 
}

def get_network_config(network_name=None):
    """Get network configuration"""
    if network_name is None:
        network_name = DEFAULT_NETWORK
    return NETWORKS.get(network_name, NETWORKS[DEFAULT_NETWORK])

def get_contract_address(contract_name, network_name=None):
    """Get contract address"""
    if network_name is None:
        network_name = DEFAULT_NETWORK
    return CONTRACT_ADDRESSES.get(network_name, {}).get(contract_name)

def get_contract_abi(contract_name):
    """Get contract ABI"""
    if contract_name == 'BatchRegistry':
        return BATCH_REGISTRY_ABI
    elif contract_name == 'InspectionManager':
        return INSPECTION_MANAGER_ABI
    else:
        raise ValueError(f"Unknown contract: {contract_name}")