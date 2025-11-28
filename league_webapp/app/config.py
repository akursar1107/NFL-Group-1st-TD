import os
from datetime import timedelta

class Config:
    """Flask configuration"""
    # Secret key for sessions
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    
    # Database
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///league.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # SQLAlchemy connection pooling (optimized for SQLite)
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 10,
        'pool_recycle': 3600,
        'pool_pre_ping': True,  # Verify connections before using
    }
    
    # Session config
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    
    # NFL Data
    ODDS_API_KEY = os.environ.get('ODDS_API_KEY', '')
    SPORT = "americanfootball_nfl"
    REGION = 'us'
    
    # Season config
    CURRENT_SEASON = 2025
