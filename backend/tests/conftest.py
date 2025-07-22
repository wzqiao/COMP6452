# tests/conftest.py
import pytest
import tempfile
import os
import sys


project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from app import create_app
from extensions import db
from models import User, Batch

@pytest.fixture
def app():
    """创建测试应用"""

    db_fd, db_path = tempfile.mkstemp()
    

    app = create_app()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
    app.config['WTF_CSRF_ENABLED'] = False
    app.config['JWT_SECRET_KEY'] = 'test-secret-key'
    
    with app.app_context():

        db.create_all()
        yield app

        db.drop_all()
    

    os.close(db_fd)
    os.unlink(db_path)

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def test_batch(app, test_producer):
    with app.app_context():
        batch = Batch(
            batch_number='TEST001',
            product_name='Test Apple',
            origin='Test Farm',
            quantity=100,
            unit='kg',
            status='pending',
            owner_id=test_producer['id'],
            organic=False,
            import_product=False
        )
        db.session.add(batch)
        db.session.commit()
        
        batch_dict = {
            'id': batch.id,
            'batch_number': batch.batch_number,
            'product_name': batch.product_name,
            'origin': batch.origin,
            'quantity': batch.quantity,
            'unit': batch.unit,
            'status': batch.status,
            'owner_id': batch.owner_id,
            'organic': batch.organic,
            'import_product': batch.import_product,
            'created_at': batch.created_at.isoformat() if batch.created_at else None,
            'harvest_date': batch.harvest_date.isoformat() if batch.harvest_date else None,
            'expiry_date': batch.expiry_date.isoformat() if batch.expiry_date else None
        }
        
        return batch_dict

@pytest.fixture
def test_producer(app):
    with app.app_context():
        from werkzeug.security import generate_password_hash
        
        user = User(
            email='producer@test.com',
            password_hash=generate_password_hash('password123'),
            role='producer'
        )
        db.session.add(user)
        db.session.commit()
        
        db.session.refresh(user)
        
        return {
            'id': user.id,
            'email': user.email,
            'role': user.role
        }

@pytest.fixture
def test_inspector(app):
    with app.app_context():
        from werkzeug.security import generate_password_hash
        
        user = User(
            email='inspector@test.com',
            password_hash=generate_password_hash('password123'),
            role='inspector'
        )
        db.session.add(user)
        db.session.commit()
        
        db.session.refresh(user)
        
        return {
            'id': user.id,
            'email': user.email,
            'role': user.role
        }

@pytest.fixture
def inspector_token(client, test_inspector):
    response = client.post('/auth/login', json={
        'email': 'inspector@test.com',
        'password': 'password123'
    })
    
    if response.status_code == 200:
        return response.json['access_token']
    else:
        return None

@pytest.fixture
def producer_token(client, test_producer):
    response = client.post('/auth/login', json={
        'email': 'producer@test.com',
        'password': 'password123'
    })
    
    if response.status_code == 200:
        return response.json['access_token']
    else:
        return None

@pytest.fixture
def auth_headers_inspector(inspector_token):
    if inspector_token:
        return {'Authorization': f'Bearer {inspector_token}'}
    else:
        return {}

@pytest.fixture
def auth_headers_producer(producer_token):
    if producer_token:
        return {'Authorization': f'Bearer {producer_token}'}
    else:
        return {}