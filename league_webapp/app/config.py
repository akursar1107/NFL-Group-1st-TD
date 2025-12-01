import os
from datetime import timedelta

class Config:
    """Base configuration with common settings"""
    # Secret key for sessions
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    
    # CSRF Protection
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = None  # No time limit for CSRF tokens
    
    # Session Security
    SESSION_COOKIE_HTTPONLY = True  # Prevent XSS
    SESSION_COOKIE_SAMESITE = 'Lax'  # CSRF protection
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    
    # Database
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # NFL Data
    ODDS_API_KEY = os.environ.get('ODDS_API_KEY', '')
    SPORT = "americanfootball_nfl"
    REGION = 'us'
    
    # Season config
    CURRENT_SEASON = 2025
    
    # Cache settings (overridden in subclasses)
    CACHE_TYPE = 'SimpleCache'
    CACHE_DEFAULT_TIMEOUT = 300
    
    # Logging
    LOG_LEVEL = 'INFO'


class DevelopmentConfig(Config):
    """Development environment configuration"""
    DEBUG = True
    TESTING = False
    
    # Session Security (relaxed for local development)
    SESSION_COOKIE_SECURE = False  # Allow HTTP
    
    # Database - Use absolute path that works in Docker and locally
    # In Docker: /app/instance/league.db
    # Locally: relative to the league_webapp directory
    base_dir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
    instance_path = os.path.join(base_dir, '..', 'instance')
    db_path = os.path.join(instance_path, 'league.db')
    
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DATABASE_URL',
        f'sqlite:///{db_path}'
    )
    
    # SQLAlchemy connection pooling (optimized for SQLite)
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 5,
        'pool_recycle': 3600,
        'pool_pre_ping': True,
    }
    
    # Cache (short timeouts for dev)
    CACHE_TYPE = 'SimpleCache'
    CACHE_DEFAULT_TIMEOUT = 60  # 1 minute cache in dev
    
    # Logging
    LOG_LEVEL = 'DEBUG'
    SQLALCHEMY_ECHO = False  # Set to True to see all SQL queries


class ProductionConfig(Config):
    """Production environment configuration"""
    DEBUG = False
    TESTING = False
    
    # Session Security (strict for production)
    SESSION_COOKIE_SECURE = True  # HTTPS only
    
    # Database
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DATABASE_URL',
        'sqlite:///instance/league.db'  # Relative path in production
    )
    
    # SQLAlchemy connection pooling
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 10,
        'pool_recycle': 3600,
        'pool_pre_ping': True,
        'connect_args': {'timeout': 30}  # Longer timeout for production
    }
    
    # Cache (longer timeouts for production)
    CACHE_TYPE = 'SimpleCache'
    CACHE_DEFAULT_TIMEOUT = 300  # 5 minutes
    
    # Logging
    LOG_LEVEL = 'WARNING'
    SQLALCHEMY_ECHO = False


class TestingConfig(Config):
    """Testing environment configuration"""
    DEBUG = True
    TESTING = True
    
    # Session Security
    SESSION_COOKIE_SECURE = False
    WTF_CSRF_ENABLED = False  # Disable CSRF for testing
    
    # Database (in-memory for tests)
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    
    # SQLAlchemy
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 1,
        'pool_recycle': 3600,
    }
    
    # Cache (no caching in tests)
    CACHE_TYPE = 'NullCache'
    CACHE_DEFAULT_TIMEOUT = 0
    
    # Logging
    LOG_LEVEL = 'DEBUG'
    SQLALCHEMY_ECHO = False


# Configuration dictionary for easy lookup
config_by_name = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}


def get_config(config_name=None):
    """Get configuration class based on environment variable or parameter"""
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')
    
    return config_by_name.get(config_name, DevelopmentConfig)

