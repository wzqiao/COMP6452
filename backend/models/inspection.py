from extensions import db
from datetime import datetime


class Inspection(db.Model):
    __tablename__ = "inspections"

    # Primary key
    id = db.Column(db.Integer, primary_key=True)
    
    # Association relationship
    batch_id = db.Column(db.Integer, db.ForeignKey('batches.id'), nullable=False)     # Associated batch ID
    inspector_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)   # Inspector ID
    
    # Inspection result
    result = db.Column(db.String(20), nullable=False)                # Inspection result: pass/fail/pending
    file_url = db.Column(db.Text)                                    # PDF inspection report link
    
    # Time information
    insp_date = db.Column(db.DateTime, default=datetime.utcnow)      # Inspection date
    created_at = db.Column(db.DateTime, default=datetime.utcnow)     # Created time
    
    # Blockchain related
    blockchain_tx = db.Column(db.String(66))                         # Blockchain transaction hash
    
    # Notes
    notes = db.Column(db.Text)                                       # Inspection notes
    
    def __repr__(self):
        return f"<Inspection {self.id}: {self.result} for Batch {self.batch_id}>"
    
    def to_dict(self):
        """Convert to dictionary format, for API return"""
        return {
            "inspId": self.id,
            "batchId": self.batch_id,
            "result": self.result,
            "fileUrl": self.file_url,
            "inspDate": self.insp_date.isoformat() if self.insp_date else None,
            "inspectorId": self.inspector_id,
            "blockchainTx": self.blockchain_tx,
            "notes": self.notes
        }
    
    @classmethod
    def from_dict(cls, data, batch_id, inspector_id):
        """Create inspection object from dictionary"""
        return cls(
            batch_id=batch_id,
            inspector_id=inspector_id,
            result=data.get('result', 'pending'),
            file_url=data.get('fileUrl'),
            notes=data.get('notes')
        )
