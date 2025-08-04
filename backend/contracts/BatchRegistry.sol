// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

/**
 * @title BatchRegistry
 * @dev Batch registration and status management contract
 */
contract BatchRegistry {
    // Batch status enumeration
    enum BatchStatus {
        PENDING,      // Pending inspection
        INSPECTED,    // Inspected
        APPROVED,     // Approved
        REJECTED      // Rejected
    }
    
    // Batch structure
    struct Batch {
        uint256 id;                    // Batch ID
        string batchNumber;            // Batch number
        string productName;            // Product name
        string origin;                 // Origin
        uint256 quantity;              // Quantity
        string unit;                   // Unit
        uint256 harvestDate;           // Harvest date (timestamp)
        uint256 expiryDate;            // Expiry date (timestamp)
        BatchStatus status;            // Batch status
        address owner;                 // Owner address
        uint256 createdAt;             // Created time
        uint256 updatedAt;             // Updated time
        bool exists;                   // Whether exists
    }
    
    // Status variables
    mapping(uint256 => Batch) public batches;           // Batch mapping
    mapping(address => uint256[]) public userBatches;   // User batch mapping
    uint256 public nextBatchId = 1;                     // Next batch ID
    uint256 public totalBatches = 0;                    // Total number of batches
    
    // Permission control
    mapping(address => bool) public authorizedInspectors;  // Authorized inspector
    address public owner;                                   // Contract owner
    
    // Event definition
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
    
    // Modifiers
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
    
    // Constructor
    constructor() {
        owner = msg.sender;
    }
    
    /**
     * @dev Create new batch
     * @param _batchNumber Batch number
     * @param _productName Product name
     * @param _origin Origin
     * @param _quantity Quantity
     * @param _unit Unit
     * @param _harvestDate Harvest date
     * @param _expiryDate Expiry date
     * @return batchId Created batch ID
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
            createdAt: block.timestamp,
            updatedAt: block.timestamp,
            exists: true
        });
        
        userBatches[msg.sender].push(batchId);
        totalBatches++;
        
        emit BatchCreated(batchId, _batchNumber, _productName, msg.sender, block.timestamp);
        
        return batchId;
    }
    
    /**
     * @dev Update batch status
     * @param batchId Batch ID
     * @param newStatus New status
     */
    function updateBatchStatus(uint256 batchId, BatchStatus newStatus) 
        public 
        batchExists(batchId) 
        onlyInspector 
    {
        Batch storage batch = batches[batchId];
        BatchStatus oldStatus = batch.status;
        
        // Status transition validation
        require(isValidStatusTransition(oldStatus, newStatus), "Invalid status transition");
        
        batch.status = newStatus;
        batch.updatedAt = block.timestamp;
        
        emit BatchStatusUpdated(batchId, oldStatus, newStatus, msg.sender, block.timestamp);
    }
    
    /**
     * @dev Validate status transition
     * @param current Current status
     * @param next Target status
     * @return Whether valid
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
     * @dev Get batch details
     * @param batchId Batch ID
     * @return batch Batch information
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
     * @dev Get all batches of a user
     * @param user User address
     * @return Batch ID array
     */
    function getUserBatches(address user) public view returns (uint256[] memory) {
        return userBatches[user];
    }
    
    /**
     * @dev Get total number of batches
     * @return Total number of batches
     */
    function getTotalBatches() public view returns (uint256) {
        return totalBatches;
    }
    
    /**
     * @dev Authorize inspector
     * @param inspector Inspector address
     */
    function authorizeInspector(address inspector) public onlyOwner {
        require(inspector != address(0), "Inspector address cannot be zero");
        require(!authorizedInspectors[inspector], "Inspector already authorized");
        
        authorizedInspectors[inspector] = true;
        emit InspectorAuthorized(inspector, msg.sender, block.timestamp);
    }
    
    /**
     * @dev Revoke inspector permission
     * @param inspector Inspector address
     */
    function revokeInspector(address inspector) public onlyOwner {
        require(authorizedInspectors[inspector], "Inspector not authorized");
        
        authorizedInspectors[inspector] = false;
        emit InspectorRevoked(inspector, msg.sender, block.timestamp);
    }
    
    /**
     * @dev Check if the inspector is authorized
     * @param inspector Inspector address
     * @return Whether the inspector is authorized
     */
    function isAuthorizedInspector(address inspector) public view returns (bool) {
        return authorizedInspectors[inspector];
    }
} 