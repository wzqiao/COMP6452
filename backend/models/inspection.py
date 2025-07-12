from extensions import db
from datetime import datetime


class Inspection(db.Model):
    __tablename__ = "inspections"

    # 主键
    id = db.Column(db.Integer, primary_key=True)
    
    # 关联关系
    batch_id = db.Column(db.Integer, db.ForeignKey('batches.id'), nullable=False)     # 关联的批次ID
    inspector_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)   # 检验员ID
    
    # 检验结果
    result = db.Column(db.String(20), nullable=False)                # 检验结果: pass/fail/pending
    file_url = db.Column(db.Text)                                    # PDF检验报告链接
    
    # 时间信息
    insp_date = db.Column(db.DateTime, default=datetime.utcnow)      # 检验日期
    created_at = db.Column(db.DateTime, default=datetime.utcnow)     # 创建时间
    
    # 区块链相关
    blockchain_tx = db.Column(db.String(66))                         # 区块链交易哈希
    
    # 备注信息
    notes = db.Column(db.Text)                                       # 检验备注
    
    def __repr__(self):
        return f"<Inspection {self.id}: {self.result} for Batch {self.batch_id}>"
    
    def to_dict(self):
        """转换为字典格式，用于API返回"""
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
        """从字典创建检验对象"""
        return cls(
            batch_id=batch_id,
            inspector_id=inspector_id,
            result=data.get('result', 'pending'),
            file_url=data.get('fileUrl'),
            notes=data.get('notes')
        )
