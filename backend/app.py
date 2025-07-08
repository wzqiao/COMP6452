from flask import Flask, Blueprint
from config import Config
from extensions import db, jwt
from routes.auth import auth_bp
from routes.storage import upload_bp
# from routes.batch import batch_bp
# from routes.inspection import insp_bp

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    jwt.init_app(app)


    # 后端A：只启用了 auth_bp 与 upload_bp，其他功能待开发
    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(upload_bp)
    # app.register_blueprint(batch_bp, url_prefix="/batches")
    # app.register_blueprint(insp_bp,  url_prefix="/batches")

    return app

if __name__ == "__main__":
    app = create_app()
    app.run(debug=True, port=5000)
