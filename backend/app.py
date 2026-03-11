import os
import logging
import time
from datetime import datetime
from flask import Flask, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
from dotenv import load_dotenv
from config import config

# Load environment variables
load_dotenv()

# Initialize extensions
db = SQLAlchemy()

def create_app(config_name=None):
    """Application factory"""
    if config_name is None:
        config_name = os.getenv('FLASK_ENV', 'development')

    app = Flask(__name__)

    # Load configuration
    app.config.from_object(config[config_name])

    # Session configuration
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    app.config['SESSION_TYPE'] = 'filesystem'
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
    app.config['PERMANENT_SESSION_LIFETIME'] = 86400  # 24 hours
    
    # Initialize extensions
    db.init_app(app)
    CORS(app, resources={
        r"/api/*": {
            "origins": ["http://localhost:8080", "http://localhost:5173"],
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"],
            "supports_credentials": True
        }
    })
    
    # Setup logging
    setup_logging(app)
    
    # Register error handlers
    register_error_handlers(app)
    
    # Register health check endpoint
    register_health_check(app)
    
    # Register blueprints
    register_blueprints(app)
    
    # Create database tables with retry logic
    with app.app_context():
        max_retries = 5
        retry_delay = 2

        for attempt in range(max_retries):
            try:
                db.create_all()
                app.logger.info('Database tables created successfully')
                break
            except Exception as e:
                if attempt < max_retries - 1:
                    app.logger.warning(f'Failed to create database tables (attempt {attempt + 1}/{max_retries}): {str(e)}')
                    app.logger.info(f'Retrying in {retry_delay} seconds...')
                    time.sleep(retry_delay)
                else:
                    app.logger.error(f'Failed to create database tables after {max_retries} attempts: {str(e)}')
    
    return app

def setup_logging(app):
    """Configure logging"""
    log_level = logging.DEBUG if app.config['DEBUG'] else logging.INFO
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    
    # Formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_handler.setFormatter(formatter)
    
    # Add handler to app logger
    app.logger.addHandler(console_handler)
    app.logger.setLevel(log_level)
    
    app.logger.info('Shogi App started')
    app.logger.info(f'Environment: {os.getenv("FLASK_ENV", "development")}')

def register_error_handlers(app):
    """Register error handlers"""
    
    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({
            'error': 'Bad Request',
            'message': str(error.description) if hasattr(error, 'description') else str(error),
            'timestamp': datetime.utcnow().isoformat()
        }), 400
    
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            'error': 'Not Found',
            'message': 'Resource not found',
            'timestamp': datetime.utcnow().isoformat()
        }), 404
    
    @app.errorhandler(422)
    def unprocessable_entity(error):
        return jsonify({
            'error': 'Unprocessable Entity',
            'message': str(error.description) if hasattr(error, 'description') else str(error),
            'timestamp': datetime.utcnow().isoformat()
        }), 422
    
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return jsonify({
            'error': 'Internal Server Error',
            'message': 'An unexpected error occurred',
            'timestamp': datetime.utcnow().isoformat()
        }), 500
    
    @app.errorhandler(503)
    def service_unavailable(error):
        return jsonify({
            'error': 'Service Unavailable',
            'message': 'AI Engine is unavailable',
            'timestamp': datetime.utcnow().isoformat()
        }), 503

def register_health_check(app):
    """Register health check endpoint"""
    
    @app.route('/health', methods=['GET'])
    def health_check():
        """Health check endpoint"""
        try:
            # Check database connection
            db.session.execute(text('SELECT 1'))
            db_status = 'healthy'
        except Exception as e:
            app.logger.error(f'Database health check failed: {str(e)}')
            db_status = 'unhealthy'

        return jsonify({
            'status': 'healthy' if db_status == 'healthy' else 'degraded',
            'database': db_status,
            'timestamp': datetime.utcnow().isoformat()
        }), 200 if db_status == 'healthy' else 503

def register_blueprints(app):
    """Register API blueprints"""
    from routes import positions_bp, kifus_bp, evaluation_bp
    from routes.auth import auth_bp
    app.register_blueprint(auth_bp)
    app.register_blueprint(positions_bp)
    app.register_blueprint(kifus_bp)
    app.register_blueprint(evaluation_bp)

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5000)
