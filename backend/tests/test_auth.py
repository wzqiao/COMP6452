# tests/test_auth.py
import pytest

class TestAuthAPI:
    """Test authentication related APIs"""
    
    def test_register_success(self, client):
        """Test successful user registration"""
        response = client.post('/auth/register', json={
            'email': 'newuser@test.com',
            'password': 'password123',
            'role': 'producer'
        })
        
        assert response.status_code == 201
        data = response.get_json()
        assert data['msg'] == 'User registered successfully'
    
    def test_register_default_role(self, client):
        """Test registration with default role (consumer)"""
        response = client.post('/auth/register', json={
            'email': 'defaultrole@test.com',
            'password': 'password123'
            # No role specified - should default to consumer
        })
        
        assert response.status_code == 201
        data = response.get_json()
        assert data['msg'] == 'User registered successfully'
    
    def test_register_duplicate_email(self, client, test_producer):
        """Test registration with existing email"""
        response = client.post('/auth/register', json={
            'email': 'producer@test.com',  # Already exists
            'password': 'password123',
            'role': 'producer'
        })
        
        assert response.status_code == 403
        data = response.get_json()
        assert data['message'] == 'Email already exists'
    
    def test_register_missing_email(self, client):
        """Test registration with missing email"""
        response = client.post('/auth/register', json={
            'password': 'password123',
            'role': 'producer'
        })
        
        assert response.status_code == 400
        data = response.get_json()
        assert data['message'] == 'invalid input'
    
    def test_register_missing_password(self, client):
        """Test registration with missing password"""
        response = client.post('/auth/register', json={
            'email': 'test@test.com',
            'role': 'producer'
        })
        
        assert response.status_code == 400
        data = response.get_json()
        assert data['message'] == 'invalid input'
    
    def test_register_empty_fields(self, client):
        """Test registration with empty email/password"""
        response = client.post('/auth/register', json={
            'email': '   ',  # Whitespace only
            'password': '',  # Empty
            'role': 'producer'
        })
        
        assert response.status_code == 400
        data = response.get_json()
        assert data['message'] == 'invalid input'
    
    def test_login_success_producer(self, client, test_producer):
        """Test successful login as producer"""
        response = client.post('/auth/login', json={
            'email': 'producer@test.com',
            'password': 'password123'
        })
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['message'] == 'login success'
        assert 'token' in data
        assert data['role'] == 'producer'
        assert 'walletAddress' in data
    
    def test_login_success_inspector(self, client, test_inspector):
        """Test successful login as inspector"""
        response = client.post('/auth/login', json={
            'email': 'inspector@test.com',
            'password': 'password123'
        })
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['message'] == 'login success'
        assert 'token' in data
        assert data['role'] == 'inspector'
    
    def test_login_invalid_email(self, client):
        """Test login with non-existent email"""
        response = client.post('/auth/login', json={
            'email': 'nonexistent@test.com',
            'password': 'password123'
        })
        
        assert response.status_code == 403
        data = response.get_json()
        assert data['message'] == 'invalid email'
    
    def test_login_wrong_password(self, client, test_producer):
        """Test login with wrong password"""
        response = client.post('/auth/login', json={
            'email': 'producer@test.com',
            'password': 'wrongpassword'
        })
        
        assert response.status_code == 401
        data = response.get_json()
        assert data['message'] == 'password error'
    
    def test_login_email_case_insensitive(self, client, test_producer):
        """Test login with different email case"""
        response = client.post('/auth/login', json={
            'email': 'PRODUCER@TEST.COM',  # Uppercase
            'password': 'password123'
        })
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['message'] == 'login success'
    
    def test_bind_wallet_success(self, client, test_producer):
        """Test successful wallet binding"""
        # Login to get token
        login_response = client.post('/auth/login', json={
            'email': 'producer@test.com',
            'password': 'password123'
        })
        token = login_response.get_json()['token']
        headers = {'Authorization': f'Bearer {token}'}
        
        # Bind wallet
        wallet_address = '0xC8FFDe08042cdBd4Ab7D2D033eB0e72121FdA32b'
        response = client.post('/auth/wallet', 
            headers=headers,
            json={'wallet': wallet_address}
        )
        
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['message'] == 'wallet bound'
        assert data['walletAddress'] == wallet_address
    
    def test_bind_wallet_invalid_address(self, client, test_producer):
        """Test wallet binding with invalid address"""
        # Login to get token
        login_response = client.post('/auth/login', json={
            'email': 'producer@test.com',
            'password': 'password123'
        })
        token = login_response.get_json()['token']
        headers = {'Authorization': f'Bearer {token}'}
        
        # Try invalid wallet address
        response = client.post('/auth/wallet', 
            headers=headers,
            json={'wallet': 'invalid_wallet_address'}
        )
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'bad address' in data['message']
    
    def test_bind_wallet_no_token(self, client):
        """Test wallet binding without authentication"""
        response = client.post('/auth/wallet', json={
            'wallet': '0x742d35Cc6634C0532925a3b8D49f6B63123456789'
        })
        
        assert response.status_code == 401  # JWT required
    
    def test_protected_route_with_valid_token(self, client, test_producer):
        """Test accessing protected route with valid token"""
        # Login to get token
        login_response = client.post('/auth/login', json={
            'email': 'producer@test.com',
            'password': 'password123'
        })
        token = login_response.get_json()['token']
        headers = {'Authorization': f'Bearer {token}'}
        
        # Access protected route (inspections requires auth)
        response = client.get('/inspections', headers=headers)
        
        # Should work (not unauthorized)
        assert response.status_code != 401
    
    def test_protected_route_with_invalid_token(self, client):
        """Test accessing protected route with invalid token"""
        headers = {'Authorization': 'Bearer invalid_token_here'}
        
        response = client.get('/inspections', headers=headers)
        
        assert response.status_code == 422  # JWT decode error