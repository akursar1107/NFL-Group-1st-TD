import os
from datetime import timedelta

class Config:
    """Flask configuration"""
    # Secret key for sessions
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    
    # CSRF Protection
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = None  # No time limit for CSRF tokens
    
    # Session Security
    SESSION_COOKIE_SECURE = os.environ.get('FLASK_ENV') == 'production'  # HTTPS only in production
    SESSION_COOKIE_HTTPONLY = True  # Prevent XSS
    SESSION_COOKIE_SAMESITE = 'Lax'  # CSRF protection
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    
    # Database
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DATABASE_URL',
        'sqlite:///C:/Users/akurs/Desktop/Vibe Coder/main/league_webapp/instance/league.db'
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # SQLAlchemy connection pooling (optimized for SQLite)
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 10,
        'pool_recycle': 3600,
        'pool_pre_ping': True,  # Verify connections before using
    }
    
    # NFL Data
    ODDS_API_KEY = os.environ.get('ODDS_API_KEY', '')
    SPORT = "americanfootball_nfl"
    REGION = 'us'
    
    # Season config
    CURRENT_SEASON = 2025
