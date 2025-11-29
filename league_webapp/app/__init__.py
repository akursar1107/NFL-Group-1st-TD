from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_caching import Cache
from flask_login import LoginManager
from .config import Config

db = SQLAlchemy()
cache = Cache()
login_manager = LoginManager()

def create_app(config_class=Config):
    """Application factory pattern"""
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(config_class)
    
    # Initialize extensions
    db.init_app(app)
    cache.init_app(app, config={'CACHE_TYPE': 'SimpleCache', 'CACHE_DEFAULT_TIMEOUT': 300})
    
    # Initialize Flask-Login
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'info'
    
    # User loader callback for Flask-Login
    @login_manager.user_loader
    def load_user(user_id):
        from .models import User
        return User.query.get(int(user_id))
    
    # Register blueprints
    from .blueprints.main import main_bp
    from .blueprints.admin import admin_bp
    from .blueprints.api import api_bp
    app.register_blueprint(main_bp)
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(api_bp, url_prefix='/api')
    print('Blueprints registered!')
    from . import auth
    app.register_blueprint(auth.auth_bp)
    
    # Create database tables
    with app.app_context():
        db.create_all()
    
    return app
