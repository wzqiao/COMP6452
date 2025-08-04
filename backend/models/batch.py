from extensions import db
from datetime import datetime
import json


class Batch(db.Model):
    __tablename__ = "batches"

    # Primary key
    id = db.Column(db.Integer, primary_key=True)
    
    # Batch basic information
    batch_number = db.Column(db.String(50), unique=True, nullable=False)  # Batch number
    product_name = db.Column(db.String(100), nullable=False)              # Product name
    origin = db.Column(db.String(100), nullable=False)                   # Origin
    
    # Quantity information
    quantity = db.Column(db.String(20), nullable=False)                  # Quantity
    unit = db.Column(db.String(20), nullable=False)                      # Unit
    total_weight_kg = db.Column(db.Integer)                              # Total weight (kg)
    
    # Date information
    harvest_date = db.Column(db.Date)                                    # Harvest date
    expiry_date = db.Column(db.Date)                                     # Expiry date
    created_at = db.Column(db.DateTime, default=datetime.utcnow)         # Created time
    
    # Product characteristics
    organic = db.Column(db.Boolean, default=False)                       # Whether organic
    import_product = db.Column(db.Boolean, default=False)                # Whether imported
    
    # Status management
    status = db.Column(db.String(20), default="pending")                 # Status: pending/inspected/approved/rejected
    
    # Association relationship
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)  # Batch creator
    
    # Blockchain related
    blockchain_tx = db.Column(db.String(66))                             # Blockchain transaction hash
    
    # Reverse association: one batch can have multiple inspection records
    inspections = db.relationship('Inspection', backref='batch', lazy=True)
    
    def __repr__(self):
        return f"<Batch {self.batch_number}: {self.product_name}>"
    
    def to_dict(self):
        """Convert to dictionary format, for API return"""
        return {
            "batchId": self.id,
            "metadata": {
                "productName": self.product_name,
                "origin": self.origin,
                "quantity": self.quantity,
                "unit": self.unit,
                "createdAt": self.created_at.isoformat() if self.created_at else None,
                "totalWeightKg": self.total_weight_kg,
                "harvestDate": self.harvest_date.isoformat() if self.harvest_date else None,
                "expiryDate": self.expiry_date.isoformat() if self.expiry_date else None,
                "batchNumber": self.batch_number,
                "organic": self.organic,
                "import": self.import_product
            },
            "status": self.status,
            "blockchainTx": self.blockchain_tx,
            "inspections": [insp.to_dict() for insp in self.inspections]
        }
    
    @classmethod
    def from_dict(cls, data, owner_id):
        """Create batch object from dictionary"""
        metadata = data.get('metadata', {})
        
        # Parse date string
        harvest_date = None
        expiry_date = None
        
        if metadata.get('harvestDate'):
            harvest_date = datetime.strptime(metadata['harvestDate'], '%Y-%m-%d').date()
        
        if metadata.get('expiryDate'):
            expiry_date = datetime.strptime(metadata['expiryDate'], '%Y-%m-%d').date()
        
        return cls(
            batch_number=metadata.get('batchNumber', f"BATCH-{datetime.now().strftime('%Y%m%d%H%M%S')}"),
            product_name=metadata.get('productName'),
            origin=metadata.get('origin'),
            quantity=metadata.get('quantity'),
            unit=metadata.get('unit'),
            total_weight_kg=metadata.get('totalWeightKg'),
            harvest_date=harvest_date,
            expiry_date=expiry_date,
            organic=metadata.get('organic', False),
            import_product=metadata.get('import', False),
            owner_id=owner_id
        )
