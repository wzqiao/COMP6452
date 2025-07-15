from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_cors import CORS

# Initialize extensions
db = SQLAlchemy()
jwt = JWTManager()
cors = CORS()


# 简单初始化 SQLAlchemy、JWTManager 和 CORS。