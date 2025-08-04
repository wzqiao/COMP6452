import os
from app import create_app
from extensions import db


from config import Config
uri = Config.SQLALCHEMY_DATABASE_URI


# Delete the database file if it exists
if uri.startswith("sqlite:///"):
    # Handle both relative and absolute paths
    if uri.startswith("sqlite:////"):
        db_path = uri.replace("sqlite:////", "/")
    else:
        db_path = uri.replace("sqlite:///", "")
    
    # Ensure directory exists
    db_dir = os.path.dirname(db_path)
    if db_dir and not os.path.exists(db_dir):
        os.makedirs(db_dir, exist_ok=True)
        print(f"Created directory: {db_dir}")
    
    if os.path.exists(db_path):
        print(f"🗑️  Old database file detected: {db_path}, deleting...")
        os.remove(db_path)
        print("  Old database deleted")

else:
    print("env not sqlite database")

# Create new database
app = create_app()
with app.app_context():
    db.create_all()
    print("Sqlite database initialized")
