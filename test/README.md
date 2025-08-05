# Smart Contract Testing Suite

This directory contains Solidity smart contracts and their corresponding test files for a blockchain-based supply chain management system.

## Structure

```
test/
├── contracts/
│   ├── BatchRegistry.sol      # Batch registration and status management
│   └── InspectionManager.sol  # Inspection result management
└── test/
    ├── BatchRegistry_test.sol      # Unit tests for BatchRegistry
    └── InspectionManager_test.sol  # Unit tests for InspectionManager
```

## Smart Contracts

### BatchRegistry.sol
- **Purpose**: Manages batch registration and status tracking
- **Features**: 
  - Batch creation and registration
  - Status management (PENDING, INSPECTED, APPROVED, REJECTED)
  - Batch information storage (product name, origin, quantity, dates)
  - Owner verification and access control

### InspectionManager.sol
- **Purpose**: Handles inspection processes and results
- **Features**:
  - Inspection record management
  - Result tracking (PENDING, PASSED, FAILED, NEEDS_RECHECK)
  - Inspector authorization
  - Integration with BatchRegistry

## Testing

The test files use Remix testing framework and provide comprehensive unit tests for:
- Contract deployment and initialization
- Function access controls
- State transitions
- Data integrity
- Event emissions

## Usage

These contracts are designed for testing and development purposes. They can be deployed and tested using:
- Remix IDE
- Truffle/Hardhat
- Local blockchain networks (Ganache, etc.)

## Requirements

- Solidity ^0.8.0
- Remix testing framework (for running tests)