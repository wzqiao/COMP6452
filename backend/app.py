from flask import Flask, Blueprint
from config import Config
from extensions import db, jwt, cors
from routes.auth import auth_bp
from routes.batch import batch_bp
from routes.inspection import inspection_bp

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    jwt.init_app(app)
    cors.init_app(app)

    # 注册路由
    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(batch_bp, url_prefix="/batches")
    app.register_blueprint(inspection_bp, url_prefix="/api")

    return app

if __name__ == "__main__":
    app = create_app()
    app.run(debug=True, port=5000)
