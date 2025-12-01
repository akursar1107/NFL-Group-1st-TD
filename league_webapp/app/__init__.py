from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_caching import Cache
from flask_login import LoginManager
from flask_cors import CORS
from .config import get_config
from .middleware import setup_monitoring

db = SQLAlchemy()
migrate = Migrate()
cache = Cache()
login_manager = LoginManager()

def create_app(config_name=None):
    """Application factory pattern"""
    app = Flask(__name__, instance_relative_config=True)
    
    # Load configuration
    config_class = get_config(config_name)
    app.config.from_object(config_class)
    
    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    cache.init_app(app, config={
        'CACHE_TYPE': app.config['CACHE_TYPE'],
        'CACHE_DEFAULT_TIMEOUT': app.config['CACHE_DEFAULT_TIMEOUT']
    })
    
    # Enable CORS for React frontend
    CORS(app, resources={r"/api/*": {"origins": "http://localhost:3000"}})
    
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
    
    # Set up performance monitoring
    setup_monitoring(app)
    
    # Create database tables
    with app.app_context():
        db.create_all()
    
    return app
