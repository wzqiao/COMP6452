import os
from dotenv import load_dotenv
from datetime import timedelta

class Config:
    # Flask
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key')
    
    # Database - Use sqlite for testing, migrate to other DB later
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///sqlite_test.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # JWT - Set in .env file if not provided
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', '6452-jwt-secret-key')
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=30)
    
    # CORS configuration - Allow frontend cross-origin access
    CORS_ORIGINS = ['http://localhost:5173', 'http://127.0.0.1:5173']
    CORS_ALLOW_HEADERS = ['Content-Type', 'Authorization']
    CORS_METHODS = ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS']
    
    # Using lambda now, backend doesn't generate presigned URLs, frontend calls lambda directly
    # # AWS (placeholder values)
    # AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID', 'dummy-access-key')
    # AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY', 'dummy-secret-key')
    # AWS_REGION = os.getenv('AWS_REGION', 'ap-southeast-2')
    # AWS_BUCKET_NAME = os.getenv('AWS_BUCKET_NAME', 'dummy-bucket')


# Pure configuration class Config, all fields use .env environment variables as fallback, 
# default values are placeholders (dev-secret-key, dummy-bucket, etc.).
# Works normally, but production environment needs real values.