from flask import Blueprint, request, jsonify
from extensions import db
from flask_jwt_extended import (
    create_access_token, jwt_required, get_jwt_identity
)
from werkzeug.security import generate_password_hash, check_password_hash
from models.user import User

auth_bp = Blueprint("auth", __name__)

# ---------- 注册 ----------
@auth_bp.post("/register")
def register():
    data = request.get_json() or {}
    email    = data.get("email", "").lower().strip()
    password = data.get("password", "")
    role     = data.get("role", "consumer")  # 默认消费者

    # 邮箱或密码为空
    if not email or not password:
        return jsonify(message="invalid input"), 400

    # 邮箱已存在
    if User.query.filter_by(email=email).first():
        return jsonify(message="Email already exists"), 403

    # 创建用户
    user = User(
        email=email,
        password_hash=generate_password_hash(password),
        role=role
    )

    # 添加用户到数据库
    db.session.add(user)
    db.session.commit()

    return jsonify(msg="User registered successfully"), 201


# ---------- 登录 ----------
@auth_bp.post("/login")
def login():
    data = request.get_json() or {}
    email    = data.get("email", "").lower().strip()
    password = data.get("password", "")

    # 省一个报错，前端要求必须两个字段都有才能请求，不验证字段是否填入了

    # 查询用户
    user = User.query.filter_by(email=email).first()

    if not user:
        return jsonify(message="invalid email"), 403
   
    # 密码不匹配
    if not check_password_hash(user.password_hash, password):
        return jsonify(message="password error"), 401

    token = create_access_token(
        identity=str(user.id),
        additional_claims={"role": user.role}
    )
    return jsonify(message="login success",
        token=token,
        role=user.role,
        walletAddress=user.wallet), 200


# ---------- 绑定钱包 ----------
@auth_bp.post("/wallet")
@jwt_required()
def bind_wallet():
    current_id = get_jwt_identity()
    data       = request.get_json() or {}
    wallet     = data.get("wallet", "")

    if not wallet.startswith("0x") or len(wallet) != 42:
        return jsonify(message="bad address,length not = 42"), 400

    user = User.query.get(current_id)
    user.wallet = wallet
    db.session.commit()
    return jsonify(message="wallet bound", walletAddress=wallet), 200
