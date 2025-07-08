import os
from app import create_app
from extensions import db


from config import Config
uri = Config.SQLALCHEMY_DATABASE_URI


# 如果数据库文件存在，则删除
if uri.startswith("sqlite:///"):
    db_path = uri.replace("sqlite:///", "")
    
    if os.path.exists(db_path):
        print(f"🗑️  Old database file detected: {db_path}, deleting...")
        os.remove(db_path)
        print("  Old database deleted")

else:
    print("env not sqlite database")

# 创建新数据库
app = create_app()
with app.app_context():
    db.create_all()
    print("Sqlite database initialized")
