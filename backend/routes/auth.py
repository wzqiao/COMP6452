from flask import Blueprint, request, jsonify
from extensions import db
from flask_jwt_extended import (
    create_access_token, jwt_required, get_jwt_identity
)
from datetime import timedelta
from werkzeug.security import generate_password_hash, check_password_hash
from models.user import User

auth_bp = Blueprint("auth", __name__)

# ---------- Registration ----------
@auth_bp.post("/register")
def register():
    data = request.get_json() or {}
    email    = data.get("email", "").lower().strip()
    password = data.get("password", "")
    role     = data.get("role", "consumer")  # Default to consumer

    # Email or password is empty
    if not email or not password:
        return jsonify(message="invalid input"), 400

    # Email already exists
    if User.query.filter_by(email=email).first():
        return jsonify(message="Email already exists"), 403

    # Create user
    user = User(
        email=email,
        password_hash=generate_password_hash(password),
        role=role
    )

    # Add user to database
    db.session.add(user)
    db.session.commit()

    return jsonify(msg="User registered successfully"), 201


# ---------- Login ----------
@auth_bp.post("/login")
def login():
    data = request.get_json() or {}
    email    = data.get("email", "").lower().strip()
    password = data.get("password", "")

    # Skip validation - frontend requires both fields to be present before request

    # Query user
    user = User.query.filter_by(email=email).first()

    if not user:
        return jsonify(message="invalid email"), 403
   
    # Password doesn't match
    if not check_password_hash(user.password_hash, password):
        return jsonify(message="password error"), 401

    token = create_access_token(
        identity=str(user.id),
        additional_claims={"role": user.role},
        expires_delta=timedelta(minutes=30)
    )
    
    return jsonify(message="login success",
        token=token,
        role=user.role,
        walletAddress=user.wallet), 200


# ---------- Bind Wallet ----------
@auth_bp.post("/wallet")
@jwt_required()
def bind_wallet():
    current_id = get_jwt_identity()
    data       = request.get_json() or {}
    wallet     = data.get("wallet", "")

    if not wallet.startswith("0x") or len(wallet) != 42:
        return jsonify(message="bad address,length not = 42"), 400

    user = User.query.get(current_id)
    if not user:
        return jsonify(message="User not found"), 404
    
    user.wallet = wallet
    db.session.commit()
    return jsonify(message="wallet bound", walletAddress=wallet), 200
