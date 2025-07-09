import os
from dotenv import load_dotenv
from datetime import timedelta

class Config:
    # Flask
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key')
    
    # Database 先用sqlite测试，后续migration到别处
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///sqlite_test.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # JWT，.env 里没有后面再设
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', '6452-jwt-secret-key')
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=30)
    
    # 换lambda了，后端不生成预签名+处理，前端直接调用lambda
    # # AWS (placeholder values)
    # AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID', 'dummy-access-key')
    # AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY', 'dummy-secret-key')
    # AWS_REGION = os.getenv('AWS_REGION', 'ap-southeast-2')
    # AWS_BUCKET_NAME = os.getenv('AWS_BUCKET_NAME', 'dummy-bucket')


# 纯配置类 Config，字段都用 .env 环境变量兜底，默认值为占位（dev-secret-key、dummy-bucket 等）。
# 可正常工作，但生产环境需替换真实值。