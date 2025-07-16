// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

/**
 * @title BatchRegistry
 * @dev 批次注册和状态管理合约
 */
contract BatchRegistry {
    // 批次状态枚举
    enum BatchStatus {
        PENDING,      // 待检验
        INSPECTED,    // 已检验
        APPROVED,     // 已批准
        REJECTED      // 已拒绝
    }
    
    // 批次结构体
    struct Batch {
        uint256 id;                    // 批次ID
        string batchNumber;            // 批次编号
        string productName;            // 产品名称
        string origin;                 // 产地
        uint256 quantity;              // 数量
        string unit;                   // 单位
        uint256 harvestDate;           // 采收日期(时间戳)
        uint256 expiryDate;            // 过期日期(时间戳)
        BatchStatus status;            // 批次状态
        address owner;                 // 所有者地址
        uint256 timestamp;
        bool exists;                   // 是否存在
    }
    
    // 状态变量
    mapping(uint256 => Batch) public batches;           // 批次映射
    mapping(address => uint256[]) public userBatches;   // 用户批次映射
    uint256 public nextBatchId = 1;                     // 下一个批次ID
    uint256 public totalBatches = 0;                    // 总批次数
    
    // 权限控制
    mapping(address => bool) public authorizedInspectors;  // 授权检验员
    address public owner;                                   // 合约所有者
    
    // 事件定义
    event BatchCreated(
        uint256 indexed batchId,
        string batchNumber,
        string productName,
        address indexed owner,
        uint256 timestamp
    );
    
    event BatchStatusUpdated(
        uint256 indexed batchId,
        BatchStatus oldStatus,
        BatchStatus newStatus,
        address indexed updatedBy,
        uint256 timestamp
    );
    
    event InspectorAuthorized(
        address indexed inspector,
        address indexed authorizedBy,
        uint256 timestamp
    );
    
    event InspectorRevoked(
        address indexed inspector,
        address indexed revokedBy,
        uint256 timestamp
    );
    
    // 修饰符
    modifier onlyOwner() {
        require(msg.sender == owner, "Only owner can call this function");
        _;
    }
    
    modifier onlyInspector() {
        require(authorizedInspectors[msg.sender], "Only authorized inspector can call this function");
        _;
    }
    
    modifier batchExists(uint256 batchId) {
        require(batches[batchId].exists, "Batch does not exist");
        _;
    }
    
    modifier onlyBatchOwner(uint256 batchId) {
        require(batches[batchId].owner == msg.sender, "Only batch owner can call this function");
        _;
    }
    
    // 构造函数
    constructor() {
        owner = msg.sender;
    }
    
    /**
     * @dev 创建新批次
     * @param _batchNumber 批次编号
     * @param _productName 产品名称
     * @param _origin 产地
     * @param _quantity 数量
     * @param _unit 单位
     * @param _harvestDate 采收日期
     * @param _expiryDate 过期日期
     * @return batchId 创建的批次ID
     */
    function createBatch(
        string memory _batchNumber,
        string memory _productName,
        string memory _origin,
        uint256 _quantity,
        string memory _unit,
        uint256 _harvestDate,
        uint256 _expiryDate
    ) public returns (uint256) {
        require(bytes(_batchNumber).length > 0, "Batch number cannot be empty");
        require(bytes(_productName).length > 0, "Product name cannot be empty");
        require(bytes(_origin).length > 0, "Origin cannot be empty");
        require(_quantity > 0, "Quantity must be greater than 0");
        require(bytes(_unit).length > 0, "Unit cannot be empty");
        require(_harvestDate > 0, "Harvest date must be valid");
        require(_expiryDate > _harvestDate, "Expiry date must be after harvest date");
        
        uint256 batchId = nextBatchId;
        nextBatchId++;
        
        batches[batchId] = Batch({
            id: batchId,
            batchNumber: _batchNumber,
            productName: _productName,
            origin: _origin,
            quantity: _quantity,
            unit: _unit,
            harvestDate: _harvestDate,
            expiryDate: _expiryDate,
            status: BatchStatus.PENDING,
            owner: msg.sender,
            timestamp: block.timestamp,
            exists: true
        });
        
        userBatches[msg.sender].push(batchId);
        totalBatches++;
        
        emit BatchCreated(batchId, _batchNumber, _productName, msg.sender, block.timestamp);
        
        return batchId;
    }
    
    /**
     * @dev 更新批次状态
     * @param batchId 批次ID
     * @param newStatus 新状态
     */
    function updateBatchStatus(uint256 batchId, BatchStatus newStatus) 
        public 
        batchExists(batchId) 
        onlyInspector 
    {
        Batch storage batch = batches[batchId];
        BatchStatus oldStatus = batch.status;
        
        // 状态转换验证
        require(isValidStatusTransition(oldStatus, newStatus), "Invalid status transition");
        
        batch.status = newStatus;
        batch.timestamp = block.timestamp;
        
        emit BatchStatusUpdated(batchId, oldStatus, newStatus, msg.sender, block.timestamp);
    }
    
    /**
     * @dev 验证状态转换是否有效
     * @param current 当前状态
     * @param next 目标状态
     * @return 是否有效
     */
    function isValidStatusTransition(BatchStatus current, BatchStatus next) 
        public 
        pure 
        returns (bool) 
    {
        if (current == BatchStatus.PENDING) {
            return next == BatchStatus.INSPECTED;
        } else if (current == BatchStatus.INSPECTED) {
            return next == BatchStatus.APPROVED || next == BatchStatus.REJECTED;
        }
        return false;
    }
    
    /**
     * @dev 获取批次详情
     * @param batchId 批次ID
     * @return batch 批次信息
     */
    function getBatch(uint256 batchId) 
        public 
        view 
        batchExists(batchId) 
        returns (Batch memory) 
    {
        return batches[batchId];
    }
    
    /**
     * @dev 获取用户的所有批次
     * @param user 用户地址
     * @return 批次ID数组
     */
    function getUserBatches(address user) public view returns (uint256[] memory) {
        return userBatches[user];
    }
    
    /**
     * @dev 获取批次总数
     * @return 总批次数
     */
    function getTotalBatches() public view returns (uint256) {
        return totalBatches;
    }
    
    /**
     * @dev 授权检验员
     * @param inspector 检验员地址
     */
    function authorizeInspector(address inspector) public onlyOwner {
        require(inspector != address(0), "Inspector address cannot be zero");
        require(!authorizedInspectors[inspector], "Inspector already authorized");
        
        authorizedInspectors[inspector] = true;
        emit InspectorAuthorized(inspector, msg.sender, block.timestamp);
    }
    
    /**
     * @dev 撤销检验员权限
     * @param inspector 检验员地址
     */
    function revokeInspector(address inspector) public onlyOwner {
        require(authorizedInspectors[inspector], "Inspector not authorized");
        
        authorizedInspectors[inspector] = false;
        emit InspectorRevoked(inspector, msg.sender, block.timestamp);
    }
    
    /**
     * @dev 检查是否为授权检验员
     * @param inspector 检验员地址
     * @return 是否为授权检验员
     */
    function isAuthorizedInspector(address inspector) public view returns (bool) {
        return authorizedInspectors[inspector];
    }
} 