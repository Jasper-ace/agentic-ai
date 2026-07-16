import os
import logging
from flask import Flask, jsonify
from flask_cors import CORS
from app.config import Config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_app() -> Flask:
    app = Flask(__name__)
    
    # Enable Cross-Origin Resource Sharing (CORS)
    CORS(app, resources={r"/*": {"origins": "*"}})
    
    # Import Blueprints
    from app.routes.health import health_bp
    from app.routes.upload import upload_bp
    from app.routes.chat import chat_bp
    from app.routes.documents import documents_bp
    
    # Register Blueprints
    app.register_blueprint(health_bp)
    app.register_blueprint(upload_bp)
    app.register_blueprint(chat_bp)
    app.register_blueprint(documents_bp)
    
    # Ensure upload directory exists
    os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
    
    # Global Error Handlers
    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({"error": "Bad request", "details": str(error)}), 400

    @app.errorhandler(404)
    def not_found(error):
        return jsonify({"error": "Resource not found"}), 404

    @app.errorhandler(500)
    def internal_server_error(error):
        return jsonify({"error": "Internal server error", "details": str(error)}), 500
        
    logger.info("Flask application initialized successfully.")
    return app

app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
