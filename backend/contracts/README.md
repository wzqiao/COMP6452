# 智能合约说明

## 合约概述

本项目包含两个主要的智能合约，用于食品供应链管理系统：

### 1. BatchRegistry.sol
**批次注册和状态管理合约**

**功能：**
- 批次创建和注册
- 批次状态管理（PENDING → INSPECTED → APPROVED/REJECTED）
- 权限控制（合约所有者、检验员授权）
- 批次查询和统计

**主要方法：**
- `createBatch()` - 创建新批次
- `updateBatchStatus()` - 更新批次状态
- `getBatch()` - 获取批次详情
- `authorizeInspector()` - 授权检验员
- `getUserBatches()` - 获取用户的所有批次

### 2. InspectionManager.sol
**检验结果管理合约**

**功能：**
- 检验记录创建
- 检验结果提交和更新
- 与BatchRegistry自动同步状态
- 检验文件URL存储

**主要方法：**
- `createInspection()` - 创建检验记录
- `updateInspectionResult()` - 更新检验结果
- `completeInspection()` - 完成检验
- `getBatchInspections()` - 获取批次的检验记录
- `getLatestInspectionResult()` - 获取最新检验结果

## 状态流转

### 批次状态流转
```
PENDING → INSPECTED → APPROVED/REJECTED
```

### 检验结果流转
```
PENDING → PASSED/FAILED/NEEDS_RECHECK
```

### 状态同步机制
- 当检验结果为PASSED时，批次状态更新为APPROVED
- 当检验结果为FAILED时，批次状态更新为REJECTED
- 当检验结果为NEEDS_RECHECK时，批次状态保持INSPECTED

## 权限控制

### 合约所有者权限
- 授权/撤销检验员
- 更新合约配置

### 检验员权限
- 创建检验记录
- 更新检验结果
- 更新批次状态

### 生产者权限
- 创建批次
- 查看自己的批次

## 部署说明

### 1. 环境准备
```bash
# 安装Solidity编译器
npm install -g solc

# 或使用在线编译器 Remix
```

### 2. 合约编译
```bash
# 编译BatchRegistry合约
solc --abi --bin BatchRegistry.sol

# 编译InspectionManager合约
solc --abi --bin InspectionManager.sol
```

### 3. 部署步骤
1. 首先部署BatchRegistry合约
2. 使用BatchRegistry地址部署InspectionManager合约
3. 更新`deploy_config.py`中的合约地址和ABI

### 4. 初始化设置
```solidity
// 授权检验员
batchRegistry.authorizeInspector(inspectorAddress);

// 或通过InspectionManager授权（会同步到BatchRegistry）
inspectionManager.authorizeInspector(inspectorAddress);
```

## 事件日志

### BatchRegistry事件
- `BatchCreated` - 批次创建
- `BatchStatusUpdated` - 批次状态更新
- `InspectorAuthorized` - 检验员授权
- `InspectorRevoked` - 检验员撤销

### InspectionManager事件
- `InspectionCreated` - 检验记录创建
- `InspectionUpdated` - 检验结果更新
- `InspectionCompleted` - 检验完成
- `BatchStatusSynced` - 批次状态同步

## 使用示例

### 创建批次
```solidity
uint256 batchId = batchRegistry.createBatch(
    "BATCH-2024-001",      // 批次编号
    "有机苹果",            // 产品名称
    "新疆阿克苏",          // 产地
    1000,                  // 数量
    "kg",                  // 单位
    1704067200,            // 采收日期
    1706745600             // 过期日期
);
```

### 创建检验记录
```solidity
uint256 inspectionId = inspectionManager.createInspection(
    batchId,                           // 批次ID
    "https://s3.amazonaws.com/...",    // 检验文件URL
    "质量检验报告"                     // 检验备注
);
```

### 完成检验
```solidity
inspectionManager.completeInspection(
    inspectionId,                      // 检验ID
    InspectionResult.PASSED,           // 检验结果
    "https://s3.amazonaws.com/...",    // 最终检验文件URL
    "检验通过，产品质量符合标准"       // 检验备注
);
```

## 安全考虑

1. **权限控制**：严格的修饰符确保只有授权用户可以执行相应操作
2. **状态验证**：合约验证状态转换的有效性
3. **输入验证**：对所有输入参数进行验证
4. **事件记录**：所有重要操作都记录事件日志
5. **防重入攻击**：使用适当的修饰符和状态管理

## 注意事项

1. 合约部署后，需要更新`deploy_config.py`中的地址和ABI
2. 检验员权限需要由合约所有者授权
3. 批次状态转换是单向的，不可逆转
4. 检验记录一旦创建，只能由创建者更新 