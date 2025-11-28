"""Pytest configuration and shared fixtures"""
import pytest
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

@pytest.fixture
def app():
    """Create test Flask app"""
    os.environ['FLASK_ENV'] = 'testing'
    
    from league_webapp.app import create_app, db
    
    app = create_app()
    app.config.update({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'WTF_CSRF_ENABLED': False,
        'SECRET_KEY': 'test-secret-key'
    })
    
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    """Test client for making requests"""
    return app.test_client()

@pytest.fixture
def runner(app):
    """CLI runner for testing commands"""
    return app.test_cli_runner()

@pytest.fixture
def sample_user(app):
    """Create a sample user for testing"""
    from league_webapp.app import db
    from league_webapp.app.models import User
    
    with app.app_context():
        user = User(
            username='testuser',
            email='test@example.com',
            display_name='Test User'
        )
        db.session.add(user)
        db.session.commit()
        
        # Refresh to get the ID
        db.session.refresh(user)
        user_id = user.id
        
    return user_id

@pytest.fixture
def sample_game(app):
    """Create a sample game for testing"""
    from league_webapp.app import db
    from league_webapp.app.models import Game
    from datetime import date
    
    with app.app_context():
        game = Game(
            game_id='2024_10_KC_DET',
            week=10,
            season=2024,
            home_team='DET',
            away_team='KC',
            game_date=date(2024, 11, 10)
        )
        db.session.add(game)
        db.session.commit()
        
        db.session.refresh(game)
        game_id = game.id
        
    return game_id

@pytest.fixture
def sample_pick(app, sample_user, sample_game):
    """Create a sample pick for testing"""
    from league_webapp.app import db
    from league_webapp.app.models import Pick
    
    with app.app_context():
        pick = Pick(
            user_id=sample_user,
            game_id=sample_game,
            pick_type='FTD',
            player_name='Patrick Mahomes',
            odds=300,
            stake=1.0
        )
        db.session.add(pick)
        db.session.commit()
        
        db.session.refresh(pick)
        pick_id = pick.id
        
    return pick_id
