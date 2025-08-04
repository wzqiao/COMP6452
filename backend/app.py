from flask import Flask, Blueprint
from config import Config
from extensions import db, jwt, cors
from routes.auth import auth_bp
from routes.batch import batch_bp
from routes.inspection import inspection_bp
from flask_cors import CORS

def create_app():
    app = Flask(__name__)
    CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)
    app.config.from_object(Config)

    db.init_app(app)
    jwt.init_app(app)
    cors.init_app(app)

    # Register routes
    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(batch_bp, url_prefix="/batches")
    app.register_blueprint(inspection_bp, url_prefix="")

    return app

if __name__ == "__main__":
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5000)
