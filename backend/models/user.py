from extensions import db
from datetime import datetime


# 用户表ORM
class User(db.Model):
    __tablename__ = "users"

    id            = db.Column(db.Integer, primary_key=True)
    # 用户邮箱，字符串最多 120 字符，必须填写，不能重复
    email         = db.Column(db.String(32), unique=True, nullable=False)
    # 密码哈希，字符串最多 128 字符，必须填写
    password_hash = db.Column(db.String(32), nullable=False)
    # 用户角色，字符串最多 10 字符，默认值为 producer
    role          = db.Column(db.String(10), default="producer")   # producer / inspector, cunsumer不用注册
    # 钱包地址，字符串最多 66 字符，可为空
    wallet        = db.Column(db.String(66))                       # 0x…. 钱包地址

    def __repr__(self):
        return f"<User {self.email}>"
