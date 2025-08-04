// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import "./BatchRegistry.sol";

/**
 * @title InspectionManager
 * @dev Inspection result management contract
 */
contract InspectionManager {
    // Inspection result enumeration
    enum InspectionResult {
        PENDING,        // Pending inspection
        PASSED,         // Passed
        FAILED,         // Failed
        NEEDS_RECHECK   // Needs recheck
    }
    
    // Inspection record structure
    struct Inspection {
        uint256 id;                    // Inspection ID
        uint256 batchId;               // Batch ID
        address inspector;             // Inspector address
        InspectionResult result;       // Inspection result
        string fileUrl;                // Inspection file URL
        string notes;                  // Inspection notes
        uint256 inspectionDate;        // Inspection date
        uint256 createdAt;             // Created time
        uint256 updatedAt;             // Updated time
        bool exists;                   // Whether exists
    }
    
    // Status variables
    mapping(uint256 => Inspection) public inspections;                    // Inspection record mapping
    mapping(uint256 => uint256[]) public batchInspections;               // Batch inspection record mapping
    mapping(address => uint256[]) public inspectorInspections;           // Inspector inspection record mapping
    uint256 public nextInspectionId = 1;                                 // Next inspection ID
    uint256 public totalInspections = 0;                                 // Total inspections
    
    // Associated BatchRegistry contract
    BatchRegistry public batchRegistry;
    
    // Permission control
    address public owner;
    mapping(address => bool) public authorizedInspectors;
    
    // Event definition
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
    
    // Modifiers
    modifier onlyOwner() {
        require(msg.sender == owner, "Only owner can call this function");
        _;
    }
    
    modifier onlyInspector() {
        require(authorizedInspectors[msg.sender], "Only authorized inspector can call this function");
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
    
    // Constructor
    constructor(address _batchRegistryAddress) {
        owner = msg.sender;
        batchRegistry = BatchRegistry(_batchRegistryAddress);
    }
    
    /**
     * @dev Create inspection record
     * @param batchId Batch ID
     * @param fileUrl Inspection file URL
     * @param notes Inspection notes
     * @return inspectionId Created inspection ID
     */
    function createInspection(
        uint256 batchId,
        string memory fileUrl,
        string memory notes
    ) public onlyInspector returns (uint256) {
        // Validate batch existence
        require(batchRegistry.batches(batchId).exists, "Batch does not exist");
        
        // Validate batch status
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
     * @dev Update inspection result
     * @param inspectionId Inspection ID
     * @param result Inspection result
     * @param notes Update notes
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
        
        // If inspection is completed, sync batch status
        if (result == InspectionResult.PASSED || result == InspectionResult.FAILED) {
            _syncBatchStatus(inspection.batchId, result);
            emit InspectionCompleted(inspectionId, inspection.batchId, result, msg.sender, block.timestamp);
        }
    }
    
    /**
     * @dev Complete inspection
     * @param inspectionId Inspection ID
     * @param result Inspection result
     * @param fileUrl Inspection file URL
     * @param notes Inspection notes
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
        
        // Sync batch status
        _syncBatchStatus(inspection.batchId, result);
        
        emit InspectionCompleted(inspectionId, inspection.batchId, result, msg.sender, block.timestamp);
    }
    
    /**
     * @dev Sync batch status
     * @param batchId Batch ID
     * @param inspectionResult Inspection result
     */
    function _syncBatchStatus(uint256 batchId, InspectionResult inspectionResult) internal {
        BatchRegistry.BatchStatus newStatus;
        
        if (inspectionResult == InspectionResult.PASSED) {
            newStatus = BatchRegistry.BatchStatus.APPROVED;
        } else if (inspectionResult == InspectionResult.FAILED) {
            newStatus = BatchRegistry.BatchStatus.REJECTED;
        } else {
            // For PENDING and NEEDS_RECHECK, first mark as INSPECTED
            newStatus = BatchRegistry.BatchStatus.INSPECTED;
        }
        
        // Update batch status to INSPECTED
        batchRegistry.updateBatchStatus(batchId, BatchRegistry.BatchStatus.INSPECTED);
        
        // If needed, update to final status
        if (newStatus != BatchRegistry.BatchStatus.INSPECTED) {
            batchRegistry.updateBatchStatus(batchId, newStatus);
        }
        
        emit BatchStatusSynced(batchId, newStatus, block.timestamp);
    }
    
    /**
     * @dev Get inspection record details
     * @param inspectionId Inspection ID
     * @return inspection Inspection record information
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
     * @dev Get all inspections of a batch
     * @param batchId Batch ID
     * @return Inspection ID array
     */
    function getBatchInspections(uint256 batchId) public view returns (uint256[] memory) {
        return batchInspections[batchId];
    }
    
    /**
     * @dev Get all inspections of an inspector
     * @param inspector Inspector address
     * @return Inspection ID array
     */
    function getInspectorInspections(address inspector) public view returns (uint256[] memory) {
        return inspectorInspections[inspector];
    }
    
    /**
     * @dev Get the latest inspection result of a batch
     * @param batchId Batch ID
     * @return Latest inspection result
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
     * @dev Get the total number of inspections
     * @return Total number of inspections
     */
    function getTotalInspections() public view returns (uint256) {
        return totalInspections;
    }
    
    /**
     * @dev Authorize inspector
     * @param inspector Inspector address
     */
    function authorizeInspector(address inspector) public onlyOwner {
        require(inspector != address(0), "Inspector address cannot be zero");
        require(!authorizedInspectors[inspector], "Inspector already authorized");
        
        authorizedInspectors[inspector] = true;
        
        // Authorize in BatchRegistry
        batchRegistry.authorizeInspector(inspector);
    }
    
    /**
     * @dev Revoke inspector permission
     * @param inspector Inspector address
     */
    function revokeInspector(address inspector) public onlyOwner {
        require(authorizedInspectors[inspector], "Inspector not authorized");
        
        authorizedInspectors[inspector] = false;
        
        // Revoke in BatchRegistry
        batchRegistry.revokeInspector(inspector);
    }
    
    /**
     * @dev Check if the inspector is authorized
     * @param inspector Inspector address
     * @return Whether the inspector is authorized
     */
    function isAuthorizedInspector(address inspector) public view returns (bool) {
        return authorizedInspectors[inspector];
    }
    
    /**
     * @dev Update BatchRegistry contract address
     * @param _batchRegistryAddress New BatchRegistry contract address
     */
    function updateBatchRegistry(address _batchRegistryAddress) public onlyOwner {
        require(_batchRegistryAddress != address(0), "Invalid address");
        batchRegistry = BatchRegistry(_batchRegistryAddress);
    }
} 