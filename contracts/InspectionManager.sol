// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import "./BatchRegistry.sol";

/**
 * @title InspectionManager
 * @dev 检验结果管理合约 
 */
contract InspectionManager {
    // 检验结果枚举
    enum InspectionResult {
        PENDING,        // 待检验
        PASSED,         // 通过
        FAILED,         // 未通过
        NEEDS_RECHECK   // 需要复检
    }
    
    // 检验记录结构体
    struct Inspection {
        uint256 id;                    // 检验ID
        uint256 batchId;               // 批次ID
        address inspector;             // 检验员地址
        InspectionResult result;       // 检验结果
        string fileUrl;                // 检验文件URL
        string notes;                  // 检验备注
        uint256 inspectionDate;        // 检验日期
        uint256 createdAt;             // 创建时间
        uint256 updatedAt;             // 更新时间
        bool exists;                   // 是否存在
    }
    
    // 状态变量
    mapping(uint256 => Inspection) public inspections;                    // 检验记录映射
    mapping(uint256 => uint256[]) public batchInspections;               // 批次检验记录映射
    mapping(address => uint256[]) public inspectorInspections;           // 检验员检验记录映射
    uint256 public nextInspectionId = 1;                                 // 下一个检验ID
    uint256 public totalInspections = 0;                                 // 总检验数
    
    // 关联的BatchRegistry合约
    BatchRegistry public batchRegistry;
    
    // 权限控制 - 使用 BatchRegistry 的检验员权限
    address public owner;
    
    // 事件定义
    event InspectionCreated(
        uint256 indexed inspectionId,
        uint256 indexed batchId,
        address indexed inspector,
        uint256 timestamp
    );
    
    event InspectionUpdated(
        uint256 indexed inspectionId,
        uint256 indexed batchId,
        InspectionResult oldResult,
        InspectionResult newResult,
        address indexed updatedBy,
        uint256 timestamp
    );
    
    event InspectionCompleted(
        uint256 indexed inspectionId,
        uint256 indexed batchId,
        InspectionResult result,
        address indexed inspector,
        uint256 timestamp
    );
    
    event BatchStatusSynced(
        uint256 indexed batchId,
        BatchRegistry.BatchStatus newStatus,
        uint256 timestamp
    );
    
    // 修饰符
    modifier onlyOwner() {
        require(msg.sender == owner, "Only owner can call this function");
        _;
    }
    
    // 🔥 使用 BatchRegistry 的检验员权限系统
    modifier onlyInspector() {
        require(batchRegistry.isAuthorizedInspector(msg.sender), "Only authorized inspector can call this function");
        _;
    }
    
    modifier inspectionExists(uint256 inspectionId) {
        require(inspections[inspectionId].exists, "Inspection does not exist");
        _;
    }
    
    modifier onlyInspectionOwner(uint256 inspectionId) {
        require(inspections[inspectionId].inspector == msg.sender, "Only inspection owner can call this function");
        _;
    }
    
    // 构造函数
    constructor(address _batchRegistryAddress) {
        owner = msg.sender;
        batchRegistry = BatchRegistry(_batchRegistryAddress);
    }
    
    /**
     * @dev 创建检验记录
     * @param batchId 批次ID
     * @param fileUrl 检验文件URL
     * @param notes 检验备注
     * @return inspectionId 创建的检验ID
     */
    function createInspection(
        uint256 batchId,
        string memory fileUrl,
        string memory notes
    ) public onlyInspector returns (uint256) {
        // 验证批次是否存在
        BatchRegistry.Batch memory batch = batchRegistry.getBatch(batchId);
        require(batch.status == BatchRegistry.BatchStatus.PENDING, "Batch is not in pending status");
        
        uint256 inspectionId = nextInspectionId;
        nextInspectionId++;
        
        inspections[inspectionId] = Inspection({
            id: inspectionId,
            batchId: batchId,
            inspector: msg.sender,
            result: InspectionResult.PENDING,
            fileUrl: fileUrl,
            notes: notes,
            inspectionDate: block.timestamp,
            createdAt: block.timestamp,
            updatedAt: block.timestamp,
            exists: true
        });
        
        batchInspections[batchId].push(inspectionId);
        inspectorInspections[msg.sender].push(inspectionId);
        totalInspections++;
        
        emit InspectionCreated(inspectionId, batchId, msg.sender, block.timestamp);
        
        return inspectionId;
    }
    
    /**
     * @dev 更新检验结果
     * @param inspectionId 检验ID
     * @param result 检验结果
     * @param notes 更新备注
     */
    function updateInspectionResult(
        uint256 inspectionId,
        InspectionResult result,
        string memory notes
    ) public inspectionExists(inspectionId) onlyInspectionOwner(inspectionId) {
        Inspection storage inspection = inspections[inspectionId];
        InspectionResult oldResult = inspection.result;
        
        inspection.result = result;
        if (bytes(notes).length > 0) {
            inspection.notes = notes;
        }
        inspection.updatedAt = block.timestamp;
        
        emit InspectionUpdated(inspectionId, inspection.batchId, oldResult, result, msg.sender, block.timestamp);
        
        // 如果检验完成，同步批次状态
        if (result == InspectionResult.PASSED || result == InspectionResult.FAILED) {
            _syncBatchStatus(inspection.batchId, result);
            emit InspectionCompleted(inspectionId, inspection.batchId, result, msg.sender, block.timestamp);
        }
    }
    
    /**
     * @dev 完成检验
     * @param inspectionId 检验ID
     * @param result 检验结果
     * @param fileUrl 检验文件URL
     * @param notes 检验备注
     */
    function completeInspection(
        uint256 inspectionId,
        InspectionResult result,
        string memory fileUrl,
        string memory notes
    ) public inspectionExists(inspectionId) onlyInspectionOwner(inspectionId) {
        require(result == InspectionResult.PASSED || result == InspectionResult.FAILED, "Invalid completion result");
        
        Inspection storage inspection = inspections[inspectionId];
        require(inspection.result == InspectionResult.PENDING, "Inspection already completed");
        
        inspection.result = result;
        if (bytes(fileUrl).length > 0) {
            inspection.fileUrl = fileUrl;
        }
        if (bytes(notes).length > 0) {
            inspection.notes = notes;
        }
        inspection.updatedAt = block.timestamp;
        
        // 🔥 自动同步批次状态
        _syncBatchStatus(inspection.batchId, result);
        
        emit InspectionCompleted(inspectionId, inspection.batchId, result, msg.sender, block.timestamp);
    }
    
    /**
     * @dev 同步批次状态
     * @param batchId 批次ID
     * @param inspectionResult 检验结果
     */
    function _syncBatchStatus(uint256 batchId, InspectionResult inspectionResult) internal {
        BatchRegistry.BatchStatus newStatus;
        
        if (inspectionResult == InspectionResult.PASSED) {
            newStatus = BatchRegistry.BatchStatus.APPROVED;
        } else if (inspectionResult == InspectionResult.FAILED) {
            newStatus = BatchRegistry.BatchStatus.REJECTED;
        } else {
            newStatus = BatchRegistry.BatchStatus.INSPECTED;
        }
        
        // 🔥 关键：这里需要 InspectionManager 合约本身有检验员权限
        // 先更新为 INSPECTED
        batchRegistry.updateBatchStatus(batchId, BatchRegistry.BatchStatus.INSPECTED);
        
        // 如果需要，再更新为最终状态
        if (newStatus != BatchRegistry.BatchStatus.INSPECTED) {
            batchRegistry.updateBatchStatus(batchId, newStatus);
        }
        
        emit BatchStatusSynced(batchId, newStatus, block.timestamp);
    }
    
    /**
     * @dev 获取检验记录详情
     * @param inspectionId 检验ID
     * @return inspection 检验记录信息
     */
    function getInspection(uint256 inspectionId) 
        public 
        view 
        inspectionExists(inspectionId) 
        returns (Inspection memory) 
    {
        return inspections[inspectionId];
    }
    
    /**
     * @dev 获取批次的所有检验记录
     * @param batchId 批次ID
     * @return 检验ID数组
     */
    function getBatchInspections(uint256 batchId) public view returns (uint256[] memory) {
        return batchInspections[batchId];
    }
    
    /**
     * @dev 获取检验员的所有检验记录
     * @param inspector 检验员地址
     * @return 检验ID数组
     */
    function getInspectorInspections(address inspector) public view returns (uint256[] memory) {
        return inspectorInspections[inspector];
    }
    
    /**
     * @dev 获取批次的最新检验结果
     * @param batchId 批次ID
     * @return 最新检验结果
     */
    function getLatestInspectionResult(uint256 batchId) public view returns (InspectionResult) {
        uint256[] memory inspectionIds = batchInspections[batchId];
        if (inspectionIds.length == 0) {
            return InspectionResult.PENDING;
        }
        
        uint256 latestId = inspectionIds[inspectionIds.length - 1];
        return inspections[latestId].result;
    }
    
    /**
     * @dev 获取检验总数
     * @return 总检验数
     */
    function getTotalInspections() public view returns (uint256) {
        return totalInspections;
    }
    
    /**
     * @dev 检查是否为授权检验员（使用 BatchRegistry 的权限）
     * @param inspector 检验员地址
     * @return 是否为授权检验员
     */
    function isAuthorizedInspector(address inspector) public view returns (bool) {
        return batchRegistry.isAuthorizedInspector(inspector);
    }
    
    /**
     * @dev 更新BatchRegistry合约地址
     * @param _batchRegistryAddress 新的BatchRegistry合约地址
     */
    function updateBatchRegistry(address _batchRegistryAddress) public onlyOwner {
        require(_batchRegistryAddress != address(0), "Invalid address");
        batchRegistry = BatchRegistry(_batchRegistryAddress);
    }
    
    /**
     * @dev 获取关联的 BatchRegistry 地址
     * @return BatchRegistry 合约地址
     */
    function getBatchRegistryAddress() public view returns (address) {
        return address(batchRegistry);
    }
}