from extensions import db
from datetime import datetime


# User table ORM
class User(db.Model):
    __tablename__ = "users"

    id            = db.Column(db.Integer, primary_key=True)
    # User email, string up to 120 characters, required, cannot be repeated
    email         = db.Column(db.String(32), unique=True, nullable=False)
    # Password hash, string up to 128 characters, required
    password_hash = db.Column(db.String(32), nullable=False)
    # User role, string up to 10 characters, default value is producer
    role          = db.Column(db.String(10), default="producer")   # producer / inspector, cunsumer don't need to register
    # Wallet address, string up to 66 characters, can be empty
    wallet        = db.Column(db.String(66))                       # 0x…. wallet address

    def __repr__(self):
        return f"<User {self.email}>"
