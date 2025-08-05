// SPDX-License-Identifier: GPL-3.0
pragma solidity >=0.8.00 <0.9.0;

import "remix_tests.sol"; 
import "remix_accounts.sol";
import "../contracts/BatchRegistry.sol";

contract BatchRegistryTest is BatchRegistry {
    
    address acc0;
    address acc1;
    address acc2;

    function beforeAll() public {
        acc0 = TestsAccounts.getAccount(0);
        acc1 = TestsAccounts.getAccount(1);
        acc2 = TestsAccounts.getAccount(2);
    }

    function ownerTest() public {
        Assert.equal(owner, acc0, 'Owner should be acc0');
    }
    
    function setInspector() public {
        authorizeInspector(acc1);
        Assert.equal(isAuthorizedInspector(acc1), true, 'acc1 should be authorized inspector');
    }
    
    /// #sender: account-2
    function setInspectorFailure() public {
        try this.authorizeInspector(acc2) {
            Assert.ok(false, 'Method execution did not fail');
        } catch Error(string memory reason) {
            Assert.equal(reason, 'Only owner can call this function', 'Failed with unexpected reason');
        } catch Panic(uint /* errorCode */) {
            Assert.ok(false, 'Failed unexpected with error code');
        } catch (bytes memory /*lowLevelData*/) {
            Assert.ok(false, 'Failed unexpected');
        }
    }
    
    function setBatches() public {
        Assert.equal(createBatch("APPLE001", "Red Apple", "Shandong", 1000, "kg", 1704067200, 1719619200), 1, 'Should be equal to 1');
        Assert.equal(createBatch("JUICE001", "Apple Juice", "Jinan", 500, "boxes", 1704153600, 1735689600), 2, 'Should be equal to 2');
        Assert.equal(getTotalBatches(), 2, 'Total batches should be 2');
    }
    
    function setBatchFailure() public {
        try this.createBatch("", "Test Product", "Test Origin", 100, "kg", 1704067200, 1719619200) returns (uint b) {
            Assert.notEqual(b, 3, 'Method execution did not fail');
        } catch Error(string memory reason) {
            Assert.equal(reason, 'Batch number cannot be empty', 'Failed with unexpected reason');
        } catch Panic(uint /* errorCode */) {
            Assert.ok(false, 'Failed unexpected with error code');
        } catch (bytes memory /*lowLevelData*/) {
            Assert.ok(false, 'Failed unexpected');
        }
    }
    
    /// #sender: account-1
    function inspectBatch() public {
        updateBatchStatus(1, BatchStatus.INSPECTED);
        BatchRegistry.Batch memory batch = getBatch(1);
        Assert.equal(uint(batch.status), uint(BatchStatus.INSPECTED), "Status should be INSPECTED");
    }

    /// #sender: account-1
    function approveBatch() public {
        updateBatchStatus(1, BatchStatus.APPROVED);
        BatchRegistry.Batch memory batch = getBatch(1);
        Assert.equal(uint(batch.status), uint(BatchStatus.APPROVED), "Status should be APPROVED");
    }
    
    /// #sender: account-2
    function updateStatusFailure() public {
        try this.updateBatchStatus(2, BatchStatus.INSPECTED) {
            Assert.ok(false, 'Method execution did not fail');
        } catch Error(string memory reason) {
            Assert.equal(reason, 'Only authorized inspector can call this function', 'Failed with unexpected reason');
        } catch Panic(uint /* errorCode */) {
            Assert.ok(false, 'Failed unexpected with error code');        
        } catch (bytes memory /*lowLevelData*/) {
            Assert.ok(false, 'Failed unexpected');
        }
    }

    /// #sender: account-1
    function rejectBatch() public {
        updateBatchStatus(2, BatchStatus.INSPECTED);
        updateBatchStatus(2, BatchStatus.REJECTED);
        BatchRegistry.Batch memory batch = getBatch(2);
        Assert.equal(uint(batch.status), uint(BatchStatus.REJECTED), "Status should be REJECTED");
    }

    function batchStatusTest() public {
        BatchRegistry.Batch memory batch1 = getBatch(1);
        Assert.equal(uint(batch1.status), uint(BatchStatus.APPROVED), 'Batch 1 should be APPROVED');
        
        BatchRegistry.Batch memory batch2 = getBatch(2);
        Assert.equal(uint(batch2.status), uint(BatchStatus.REJECTED), 'Batch 2 should be REJECTED');
    }
    
    function batchDetailsTest() public {
        BatchRegistry.Batch memory batch = getBatch(1);
        Assert.equal(batch.batchNumber, 'APPLE001', 'Batch number should match');
        Assert.equal(batch.productName, 'Red Apple', 'Product name should match');
        Assert.equal(batch.origin, 'Shandong', 'Origin should match');
        Assert.equal(batch.quantity, 1000, 'Quantity should match');
        Assert.equal(batch.unit, 'kg', 'Unit should match');
    }
    
    function statusTransitionTest() public {
        Assert.equal(isValidStatusTransition(BatchStatus.PENDING, BatchStatus.INSPECTED), true, 'PENDING to INSPECTED should be valid');
        Assert.equal(isValidStatusTransition(BatchStatus.INSPECTED, BatchStatus.APPROVED), true, 'INSPECTED to APPROVED should be valid');
        Assert.equal(isValidStatusTransition(BatchStatus.PENDING, BatchStatus.APPROVED), false, 'PENDING to APPROVED should be invalid');
    }

    function revokeInspectorTest() public {
        revokeInspector(acc1);
        Assert.equal(isAuthorizedInspector(acc1), false, 'acc1 should not be authorized after revoke');
    }
    
    /// #sender: account-1
    function updateStatusAfterRevokeFailure() public {
        try this.updateBatchStatus(2, BatchStatus.INSPECTED) {
            Assert.ok(false, 'Method execution did not fail');
        } catch Error(string memory reason) {
            Assert.equal(reason, 'Only authorized inspector can call this function', 'Failed with unexpected reason');
        } catch Panic(uint /* errorCode */) {
            Assert.ok(false, 'Failed unexpected with error code');        
        } catch (bytes memory /*lowLevelData*/) {
            Assert.ok(false, 'Failed unexpected');
        }
    }
    
    /// #sender: account-2
    function revokeInspectorFailure() public {
        try this.revokeInspector(acc1) {
            Assert.ok(false, 'Method execution did not fail');
        } catch Error(string memory reason) {
            Assert.equal(reason, 'Only owner can call this function', 'Failed with unexpected reason');
        } catch Panic(uint /* errorCode */) {
            Assert.ok(false, 'Failed unexpected with error code');        
        } catch (bytes memory /*lowLevelData*/) {
            Assert.ok(false, 'Failed unexpected');
        }
    }

    
}