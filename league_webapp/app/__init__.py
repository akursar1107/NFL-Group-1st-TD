from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_caching import Cache
from app.config import Config

db = SQLAlchemy()
cache = Cache()

def create_app(config_class=Config):
    """Application factory pattern"""
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(config_class)
    
    # Initialize extensions
    db.init_app(app)
    cache.init_app(app, config={'CACHE_TYPE': 'SimpleCache', 'CACHE_DEFAULT_TIMEOUT': 300})
    
    # Register blueprints (will add routes later)
    from app import routes
    app.register_blueprint(routes.bp)
    
    # Create database tables
    with app.app_context():
        db.create_all()
    
    return app
