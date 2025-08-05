// SPDX-License-Identifier: MIT
pragma solidity >=0.8.0 <0.9.0;

import "remix_tests.sol";
import "remix_accounts.sol";
import "../contracts/BatchRegistry.sol";
import "../contracts/InspectionManager.sol";

contract InspectionManagerTest is InspectionManager {
    address acc0;
    address acc1;
    address acc2;
    
    BatchRegistry testBatchRegistry;
    uint256[] validInspectionIds;
    
    constructor() InspectionManager(address(0)) {}
    
    function beforeAll() public {
        acc0 = TestsAccounts.getAccount(0);
        acc1 = TestsAccounts.getAccount(1);
        acc2 = TestsAccounts.getAccount(2);
        
        testBatchRegistry = new BatchRegistry();
        updateBatchRegistry(address(testBatchRegistry));
        
        testBatchRegistry.authorizeInspector(acc1);
        testBatchRegistry.authorizeInspector(address(this));
        
        testBatchRegistry.createBatch(
            "BATCH-001",
            "Apple",
            "Farm",
            100,
            "kg",
            1704067200,
            1719676800
        );
        
        testBatchRegistry.createBatch(
            "BATCH-002",
            "Orange", 
            "Grove",
            200,
            "kg",
            1704153600,
            1719763200
        );
    }
    
    function testInitialization() public {
        Assert.equal(owner, acc0, "Owner should be acc0");
        Assert.equal(getTotalInspections(), 0, "Should start with 0 inspections");
    }
    
    function testInspectorAuth() public {
        Assert.equal(isAuthorizedInspector(acc1), true, "acc1 should be inspector");
        Assert.equal(isAuthorizedInspector(acc2), false, "acc2 should not be inspector");
    }
    
    /// #sender: account-1
    function testCreateInspection() public {
        uint256 inspectionId = createInspection(1, "test.pdf", "test notes");
        validInspectionIds.push(inspectionId);
        
        Assert.equal(inspectionId, 1, "Should return inspection ID 1");
        Assert.equal(getTotalInspections(), 1, "Should have 1 inspection");
    }
    
    /// #sender: account-1
    function testUpdateInspection() public {
        require(validInspectionIds.length > 0, "No valid inspections for update test");
        
        updateInspectionResult(validInspectionIds[0], InspectionResult.PASSED, "Completed");
        
        Inspection memory inspection = getInspection(validInspectionIds[0]);
        Assert.equal(uint8(inspection.result), 1, "Result should be PASSED");
    }
    
    function testPermissionSystem() public {
        Assert.equal(isAuthorizedInspector(acc1), true, "acc1 should be authorized inspector");
        Assert.equal(isAuthorizedInspector(acc2), false, "acc2 should not be authorized inspector");
        Assert.equal(isAuthorizedInspector(address(this)), true, "Test contract should be authorized inspector");
        
        Assert.equal(testBatchRegistry.isAuthorizedInspector(acc1), true, "acc1 should be authorized in BatchRegistry");
        Assert.equal(testBatchRegistry.isAuthorizedInspector(acc2), false, "acc2 should not be authorized in BatchRegistry");
        
        bool shouldPassForAcc1 = testBatchRegistry.isAuthorizedInspector(acc1);
        bool shouldFailForAcc2 = testBatchRegistry.isAuthorizedInspector(acc2);
        
        Assert.equal(shouldPassForAcc1, true, "Permission check should pass for acc1");
        Assert.equal(shouldFailForAcc2, false, "Permission check should fail for acc2");
    }
    
    function testUnauthorizedScenario() public {
        
        Assert.equal(isAuthorizedInspector(acc2), false, "acc2 should not have permission");
        Assert.equal(testBatchRegistry.isAuthorizedInspector(acc2), false, "BatchRegistry should not authorize acc2");
        
        bool inspectionManagerCheck = isAuthorizedInspector(acc2);
        bool batchRegistryCheck = testBatchRegistry.isAuthorizedInspector(acc2);
        Assert.equal(inspectionManagerCheck, batchRegistryCheck, "Permission checks should be consistent");
        
        Assert.equal(inspectionManagerCheck, false, "Unauthorized user should fail permission check");
    }
    
    /// #sender: account-1
    function testCompleteInspection() public {
        uint256 inspectionId = createInspection(2, "complete-test.pdf", "testing complete");
        validInspectionIds.push(inspectionId);
        
        completeInspection(inspectionId, InspectionResult.FAILED, "final-report.pdf", "Quality issues found");
        
        Inspection memory inspection = getInspection(inspectionId);
        Assert.equal(uint8(inspection.result), 2, "Result should be FAILED");
        Assert.equal(inspection.fileUrl, "final-report.pdf", "File URL should be updated");
    }
    
    function testBatchStatusSync() public {
        BatchRegistry.Batch memory batch1 = testBatchRegistry.getBatch(1);
        Assert.equal(uint8(batch1.status), 2, "Batch 1 should be APPROVED after PASSED inspection");
        
        BatchRegistry.Batch memory batch2 = testBatchRegistry.getBatch(2);
        Assert.equal(uint8(batch2.status), 3, "Batch 2 should be REJECTED after FAILED inspection");
    }
    
    function testQueryFunctions() public {
        uint256 actualCount = getTotalInspections();
        uint256[] memory inspectorInspections = getInspectorInspections(acc1);
        uint256[] memory batch1Inspections = getBatchInspections(1);
        uint256[] memory batch2Inspections = getBatchInspections(2);
        
        Assert.ok(actualCount >= 0, "Total inspections should not be negative");
        Assert.ok(inspectorInspections.length >= 0, "Inspector inspections should be valid");
        Assert.ok(batch1Inspections.length >= 0, "Batch 1 inspections should be valid");
        Assert.ok(batch2Inspections.length >= 0, "Batch 2 inspections should be valid");
        
        if (actualCount > 0) {
            Assert.equal(inspectorInspections.length, actualCount, "Inspector should have all inspections");
        }
        
        uint256 totalFromBatches = batch1Inspections.length + batch2Inspections.length;
        Assert.equal(totalFromBatches, actualCount, "Batch inspections sum should equal total");
        
        if (batch1Inspections.length > 0) {
            InspectionResult result1 = getLatestInspectionResult(1);
            Assert.ok(uint8(result1) >= 0 && uint8(result1) <= 3, "Batch 1 result should be valid enum value");
        }
        
        if (batch2Inspections.length > 0) {
            InspectionResult result2 = getLatestInspectionResult(2);
            Assert.ok(uint8(result2) >= 0 && uint8(result2) <= 3, "Batch 2 result should be valid enum value");
        }
        
        Assert.equal(validInspectionIds.length, actualCount, "Valid inspections should match total count");
        Assert.equal(inspectorInspections.length, validInspectionIds.length, "Inspector inspections should match valid inspections");
    }
    
    function testEdgeCases() public {
        uint256[] memory nonExistentBatchInspections = getBatchInspections(999);
        Assert.equal(nonExistentBatchInspections.length, 0, "Non-existent batch should have no inspections");
        
        uint256[] memory noInspections = getInspectorInspections(acc2);
        Assert.equal(noInspections.length, 0, "Non-inspector should have no inspections");
        
        InspectionResult resultForEmptyBatch = getLatestInspectionResult(999);
        Assert.equal(uint8(resultForEmptyBatch), 0, "Non-existent batch should return PENDING result");
    }
    
    function testContractConfiguration() public {
        Assert.equal(getBatchRegistryAddress(), address(testBatchRegistry), "BatchRegistry address should be set correctly");
        Assert.equal(owner, acc0, "Owner should be acc0");
        Assert.equal(nextInspectionId, validInspectionIds.length + 1, "Next inspection ID should be correct");
    }
}