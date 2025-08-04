# -*- coding: utf-8 -*-
"""
Updated contract data synchronization script
Adapted to actual contract data format
"""

import json
from datetime import datetime
from app import create_app
from extensions import db
from services.blockchain import get_blockchain_service, BlockchainError

# Assume you have these models, if not, please check models.py first
try:
    from models import Batch, User, Inspection
except ImportError:
    print("❌ Model file not found, please check if models.py exists")
    exit(1)

def convert_timestamp_to_datetime(timestamp):
    """Convert timestamp to datetime object"""
    if timestamp and timestamp > 0:
        return datetime.fromtimestamp(timestamp)
    return None

def find_or_create_user(wallet_address, email_prefix, role):
    """Find or create user"""
    if wallet_address:
        user = User.query.filter_by(wallet=wallet_address).first()
        if user:
            return user
    
    # Create new user
    user = User(
        email=f"{email_prefix}_{wallet_address[:8] if wallet_address else 'unknown'}@blockchain.local",
        password_hash="contract_generated",
        role=role,
        wallet=wallet_address or ""
    )
    db.session.add(user)
    db.session.flush()
    return user

# Removed complex status synchronization logic for performance
# Now directly using batch status from the contract

def sync_batches_from_contract():
    """Sync batch data from contract"""
    print("🔄 Start syncing batch data...")
    
    try:
        print("🔗 Getting blockchain service...")
        blockchain_service = get_blockchain_service()
        print("✅ Blockchain service obtained")
        
        # Get total number of batches from contract
        if not blockchain_service.batch_registry:
            print("❌ BatchRegistry contract not found")
            return False
        
        print("📋 Calling getTotalBatches() on contract...")
        total_batches = blockchain_service.batch_registry.functions.getTotalBatches().call()
        print(f"📦 Contract found {total_batches} batches")
        
        synced_count = 0
        updated_count = 0
        
        for batch_id in range(1, total_batches + 1):
            try:
                # Get batch data from contract
                batch_raw = blockchain_service.batch_registry.functions.getBatch(batch_id).call()
                
                # Status mapping
                status_map = {0: 'pending', 1: 'inspected', 2: 'approved', 3: 'rejected'}
                
                # Parse batch data (according to your contract structure)
                batch_data = {
                    'id': batch_raw[0],
                    'batch_number': batch_raw[1],
                    'product_name': batch_raw[2],
                    'origin': batch_raw[3],
                    'quantity': str(batch_raw[4]),
                    'unit': batch_raw[5],
                    'harvest_date': convert_timestamp_to_datetime(batch_raw[6]),
                    'expiry_date': convert_timestamp_to_datetime(batch_raw[7]),
                    'status': status_map.get(batch_raw[8], 'pending'),  # Convert to string status
                    'owner': batch_raw[9],
                    'timestamp': convert_timestamp_to_datetime(batch_raw[10]),
                    'exists': batch_raw[11] if len(batch_raw) > 11 else True
                }
                
                if not batch_data['exists']:
                    continue
                
                print(f"📋 Processing batch: {batch_data['batch_number']} - {batch_data['product_name']}")
                
                # Check if batch already exists
                existing_batch = Batch.query.filter_by(
                    batch_number=batch_data['batch_number']
                ).first()
                
                # Find or create owner
                owner_user = find_or_create_user(
                    batch_data['owner'], 
                    "producer", 
                    "producer"
                )
                
                if existing_batch:
                    # Update existing batch
                    existing_batch.product_name = batch_data['product_name']
                    existing_batch.origin = batch_data['origin']
                    existing_batch.quantity = batch_data['quantity']
                    existing_batch.unit = batch_data['unit']
                    existing_batch.harvest_date = batch_data['harvest_date'].date() if batch_data['harvest_date'] else None
                    existing_batch.expiry_date = batch_data['expiry_date'].date() if batch_data['expiry_date'] else None
                    existing_batch.status = batch_data['status']
                    existing_batch.owner_id = owner_user.id
                    existing_batch.blockchain_tx = None  # Set to None, display "none"
                    
                    updated_count += 1
                    print(f"   ✏️  Update existing batch")
                else:
                    # Create new batch
                    new_batch = Batch(
                        batch_number=batch_data['batch_number'],
                        product_name=batch_data['product_name'],
                        origin=batch_data['origin'],
                        quantity=batch_data['quantity'],
                        unit=batch_data['unit'],
                        harvest_date=batch_data['harvest_date'].date() if batch_data['harvest_date'] else None,
                        expiry_date=batch_data['expiry_date'].date() if batch_data['expiry_date'] else None,
                        status=batch_data['status'],
                        owner_id=owner_user.id,
                        created_at=batch_data['timestamp'] or datetime.now(),
                        blockchain_tx=None,  # Set to None, display "none"
                        # Set some default values
                        organic=True,
                        import_product=False,
                        total_weight_kg=100
                    )
                    
                    db.session.add(new_batch)
                    synced_count += 1
                    print(f"   ✅ Create new batch")
                
            except Exception as e:
                print(f"   ❌ Process batch {batch_id} failed: {str(e)}")
                continue
        
        # Submit all changes
        db.session.commit()
        print(f"🎉 Batch synchronization completed!")
        print(f"   📦 New: {synced_count} batches")
        print(f"   ✏️  Updated: {updated_count} batches")
        
        return True
        
    except Exception as e:
        print(f"❌ Batch synchronization failed: {str(e)}")
        db.session.rollback()
        return False

def sync_inspections_from_contract():
    """Sync inspection data from contract"""
    print("🔄 Start syncing inspection data...")
    
    try:
        blockchain_service = get_blockchain_service()
        
        if not blockchain_service.inspection_manager:
            print("❌ InspectionManager contract not found")
            return False
        
        total_inspections = blockchain_service.inspection_manager.functions.getTotalInspections().call()
        print(f"🔍 Contract found {total_inspections} inspections")
        
        synced_count = 0
        updated_count = 0
        
        for inspection_id in range(1, total_inspections + 1):
            try:
                # Get inspection data from contract
                inspection_raw = blockchain_service.inspection_manager.functions.getInspection(inspection_id).call()
                
                # Result mapping
                result_map = {0: 'pending', 1: 'passed', 2: 'failed', 3: 'needs_recheck'}
                
                inspection_data = {
                    'id': inspection_raw[0],
                    'batch_id': inspection_raw[1],
                    'inspector': inspection_raw[2],
                    'result': result_map.get(inspection_raw[3], 'pending'),  # Convert to string result
                    'file_url': inspection_raw[4],
                    'notes': inspection_raw[5],
                    'inspection_date': convert_timestamp_to_datetime(inspection_raw[6]),
                    'created_at': convert_timestamp_to_datetime(inspection_raw[7]),
                    'updated_at': convert_timestamp_to_datetime(inspection_raw[8]),
                    'exists': inspection_raw[9] if len(inspection_raw) > 9 else True
                }
                
                if not inspection_data['exists']:
                    continue
                
                print(f"🔍 Processing inspection: batch ID {inspection_data['batch_id']}")
                
                # Find corresponding database batch (find by blockchain batch ID)
                # First try to find by batch number (because now blockchain_tx is None)
                batch = None
                
                # Method 1: Find corresponding batch by contract data
                batch_raw_for_inspection = blockchain_service.batch_registry.functions.getBatch(inspection_data['batch_id']).call()
                batch_number = batch_raw_for_inspection[1]  # Get batch number
                batch = Batch.query.filter_by(batch_number=batch_number).first()
                
                if not batch:
                    print(f"   ❌ No corresponding batch found (blockchain ID: {inspection_data['batch_id']}, batch number: {batch_number})")
                    continue
                
                # Find or create inspector
                inspector_user = find_or_create_user(
                    inspection_data['inspector'],
                    "inspector",
                    "inspector"
                )
                
                # Check if inspection already exists
                existing_inspection = Inspection.query.filter_by(
                    batch_id=batch.id,
                    inspector_id=inspector_user.id
                ).first()
                
                if existing_inspection:
                    # Update existing inspection
                    existing_inspection.result = inspection_data['result']
                    existing_inspection.file_url = inspection_data['file_url']
                    existing_inspection.notes = inspection_data['notes']
                    existing_inspection.insp_date = inspection_data['inspection_date']
                    existing_inspection.blockchain_tx = None  # Set to None
                    
                    updated_count += 1
                    print(f"   ✏️  Update existing inspection")
                else:
                    # Create new inspection
                    new_inspection = Inspection(
                        batch_id=batch.id,
                        inspector_id=inspector_user.id,
                        result=inspection_data['result'],
                        file_url=inspection_data['file_url'],
                        notes=inspection_data['notes'],
                        insp_date=inspection_data['inspection_date'],
                        created_at=inspection_data['created_at'] or datetime.now(),
                        blockchain_tx=None  # Set to None
                    )
                    
                    db.session.add(new_inspection)
                    synced_count += 1
                    print(f"   ✅ Create new inspection")
                
            except Exception as e:
                print(f"   ❌ Process inspection {inspection_id} failed: {str(e)}")
                continue
        
        # Submit all changes
        db.session.commit()
        print(f"🎉 Inspection synchronization completed!")
        print(f"   🔍 New: {synced_count} inspections")
        print(f"   ✏️  Updated: {updated_count} inspections")
        
        return True
        
    except Exception as e:
        print(f"❌ Inspection synchronization failed: {str(e)}")
        db.session.rollback()
        return False

def clear_database():
    """Clear database (optional)"""
    print("⚠️  Clear database...")
    try:
        # Delete inspection records
        Inspection.query.delete()
        # Delete batch records
        Batch.query.delete()
        # Delete automatically generated users (keep manually created ones)
        User.query.filter(User.email.like('%@blockchain.local')).delete()
        
        db.session.commit()
        print("✅ Database cleared")
        return True
    except Exception as e:
        print(f"❌ Clear database failed: {str(e)}")
        db.session.rollback()
        return False

def main():
    """Main function"""
    print("🚀 Smart contract data synchronization tool")
    print("=" * 50)
    
    app = create_app()
    with app.app_context():
        
        # Ask if database should be cleared
        choice = input("Clear existing database? (y/N): ").lower().strip()
        if choice == 'y':
            if not clear_database():
                return
        
        print("\nStart syncing...")
        
        # Sync batch data
        batch_success = sync_batches_from_contract()
        
        # Sync inspection data
        inspection_success = sync_inspections_from_contract()
        
        if batch_success and inspection_success:
            print("\n✅ All data synchronized!")
        else:
            print("\n⚠️  Some data synchronization failed, please check error information")

if __name__ == "__main__":
    main()