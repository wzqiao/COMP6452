from extensions import db
from datetime import datetime
import json


class Batch(db.Model):
    __tablename__ = "batches"

    # 主键
    id = db.Column(db.Integer, primary_key=True)
    
    # 批次基本信息
    batch_number = db.Column(db.String(50), unique=True, nullable=False)  # 批次编号
    product_name = db.Column(db.String(100), nullable=False)              # 产品名称
    origin = db.Column(db.String(100), nullable=False)                   # 产地
    
    # 数量信息
    quantity = db.Column(db.String(20), nullable=False)                  # 数量
    unit = db.Column(db.String(20), nullable=False)                      # 单位
    total_weight_kg = db.Column(db.Integer)                              # 总重量(kg)
    
    # 日期信息
    harvest_date = db.Column(db.Date)                                    # 收获日期
    expiry_date = db.Column(db.Date)                                     # 过期日期
    created_at = db.Column(db.DateTime, default=datetime.utcnow)         # 创建时间
    
    # 产品特性
    organic = db.Column(db.Boolean, default=False)                       # 是否有机
    import_product = db.Column(db.Boolean, default=False)                # 是否进口
    
    # 状态管理
    status = db.Column(db.String(20), default="pending")                 # 状态: pending/inspected/approved/rejected
    
    # 关联关系
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)  # 批次创建者
    
    # 区块链相关
    blockchain_tx = db.Column(db.String(66))                             # 区块链交易哈希
    
    # 反向关联：一个批次可以有多个检验记录
    inspections = db.relationship('Inspection', backref='batch', lazy=True)
    
    def __repr__(self):
        return f"<Batch {self.batch_number}: {self.product_name}>"
    
    def to_dict(self):
        """转换为字典格式，用于API返回"""
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
        """从字典创建批次对象"""
        metadata = data.get('metadata', {})
        
        # 解析日期字符串
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
