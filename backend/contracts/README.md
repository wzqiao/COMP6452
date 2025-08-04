# Smart Contract Documentation

## Contract Overview

This project contains two main smart contracts for the food supply chain management system:

### 1. BatchRegistry.sol
**Batch Registration and Status Management Contract**

**Features:**
- Batch creation and registration
- Batch status management (PENDING → INSPECTED → APPROVED/REJECTED)
- Access control (contract owner, inspector authorization)
- Batch querying and statistics

**Main Methods:**
- `createBatch()` - Create a new batch
- `updateBatchStatus()` - Update batch status
- `getBatch()` - Get batch details
- `authorizeInspector()` - Authorize inspector
- `getUserBatches()` - Get all batches for a user

### 2. InspectionManager.sol
**Inspection Result Management Contract**

**Features:**
- Inspection record creation
- Inspection result submission and updates
- Automatic status synchronization with BatchRegistry
- Inspection file URL storage

**Main Methods:**
- `createInspection()` - Create inspection record
- `updateInspectionResult()` - Update inspection result
- `completeInspection()` - Complete inspection
- `getBatchInspections()` - Get inspection records for a batch
- `getLatestInspectionResult()` - Get latest inspection result

## Status Flow

### Batch Status Flow
```
PENDING → INSPECTED → APPROVED/REJECTED
```

### Inspection Result Flow
```
PENDING → PASSED/FAILED/NEEDS_RECHECK
```

### Status Synchronization Mechanism
- When inspection result is PASSED, batch status updates to APPROVED
- When inspection result is FAILED, batch status updates to REJECTED
- When inspection result is NEEDS_RECHECK, batch status remains INSPECTED

## Access Control

### Contract Owner Permissions
- Authorize/revoke inspectors
- Update contract configuration

### Inspector Permissions
- Create inspection records
- Update inspection results
- Update batch status

### Producer Permissions
- Create batches
- View their own batches

## Deployment Instructions

### 1. Environment Setup
```bash
# Install Solidity compiler
npm install -g solc

# Or use online compiler Remix
```

### 2. Contract Compilation
```bash
# Compile BatchRegistry contract
solc --abi --bin BatchRegistry.sol

# Compile InspectionManager contract
solc --abi --bin InspectionManager.sol
```

### 3. Deployment Steps
1. First deploy BatchRegistry contract
2. Deploy InspectionManager contract using BatchRegistry address
3. Update contract addresses and ABI in `deploy_config.py`

### 4. Initialization Setup
```solidity
// Authorize inspector
batchRegistry.authorizeInspector(inspectorAddress);

// Or authorize through InspectionManager (will sync to BatchRegistry)
inspectionManager.authorizeInspector(inspectorAddress);
```

## Event Logs

### BatchRegistry Events
- `BatchCreated` - Batch creation
- `BatchStatusUpdated` - Batch status update
- `InspectorAuthorized` - Inspector authorization
- `InspectorRevoked` - Inspector revocation

### InspectionManager Events
- `InspectionCreated` - Inspection record creation
- `InspectionUpdated` - Inspection result update
- `InspectionCompleted` - Inspection completion
- `BatchStatusSynced` - Batch status synchronization

## Usage Examples

### Create Batch
```solidity
uint256 batchId = batchRegistry.createBatch(
    "BATCH-2024-001",      // Batch number
    "Organic Apples",      // Product name
    "Xinjiang Aksu",       // Origin
    1000,                  // Quantity
    "kg",                  // Unit
    1704067200,            // Harvest date
    1706745600             // Expiry date
);
```

### Create Inspection Record
```solidity
uint256 inspectionId = inspectionManager.createInspection(
    batchId,                           // Batch ID
    "https://s3.amazonaws.com/...",    // Inspection file URL
    "Quality inspection report"        // Inspection notes
);
```

### Complete Inspection
```solidity
inspectionManager.completeInspection(
    inspectionId,                      // Inspection ID
    InspectionResult.PASSED,           // Inspection result
    "https://s3.amazonaws.com/...",    // Final inspection file URL
    "Inspection passed, product quality meets standards"  // Inspection notes
);
```

## Security Considerations

1. **Access Control**: Strict modifiers ensure only authorized users can perform corresponding operations
2. **State Validation**: Contract validates the validity of state transitions
3. **Input Validation**: All input parameters are validated
4. **Event Logging**: All important operations are logged as events
5. **Reentrancy Protection**: Use appropriate modifiers and state management

## Important Notes

1. After contract deployment, update addresses and ABI in `deploy_config.py`
2. Inspector permissions must be authorized by the contract owner
3. Batch status transitions are unidirectional and irreversible
4. Inspection records can only be updated by their creator once created 