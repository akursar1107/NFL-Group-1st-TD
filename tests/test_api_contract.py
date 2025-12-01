"""
API Contract Tests - Ensure React frontend compatibility

These tests verify that API endpoints return the expected JSON structure
that the React frontend depends on. If any of these tests fail, the React
app will likely break.

DO NOT change these tests without updating the React frontend.
"""
import pytest
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from league_webapp.app import create_app, db
from league_webapp.app.models import User, Game, Pick


@pytest.fixture
def app():
    """Create test Flask app"""
    app = create_app()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """Create test client"""
    return app.test_client()


class TestStandingsAPI:
    """Test /api/standings endpoint"""
    
    def test_standings_structure(self, client):
        """Verify standings endpoint returns correct structure"""
        response = client.get('/api/standings?season=2025')
        assert response.status_code == 200
        
        data = response.get_json()
        
        # Required top-level keys
        assert 'standings' in data
        assert 'season' in data
        assert 'stats' in data
        
        # Verify types
        assert isinstance(data['standings'], list)
        assert isinstance(data['season'], int)
        assert isinstance(data['stats'], dict)
        
        # Stats structure
        stats = data['stats']
        required_stats = ['total_players', 'total_ftd_picks', 'total_wins', 
                         'win_rate', 'league_ftd_bankroll', 'league_atts_bankroll',
                         'league_total_bankroll']
        for stat in required_stats:
            assert stat in stats


class TestPicksAPI:
    """Test /api/picks endpoints"""
    
    def test_get_picks_structure(self, client):
        """Verify picks endpoint returns correct structure"""
        response = client.get('/api/picks?season=2025')
        assert response.status_code == 200
        
        data = response.get_json()
        assert 'picks' in data
        assert isinstance(data['picks'], list)
    
    def test_create_pick_validation(self, client, app):
        """Verify pick creation requires correct fields"""
        # Create test user and game
        with app.app_context():
            user = User(username='testuser', email='test@test.com')
            game = Game(
                nfl_game_id='test_123',
                season=2025,
                week=1,
                home_team='KC',
                away_team='BUF',
                game_date='2025-09-05',
                game_time='20:20:00'
            )
            db.session.add_all([user, game])
            db.session.commit()
            user_id = user.id
            game_id = game.id
        
        # Missing required fields
        response = client.post('/api/picks', json={})
        assert response.status_code == 400
        
        # Valid pick
        response = client.post('/api/picks', json={
            'user_id': user_id,
            'game_id': game_id,
            'player_name': 'Patrick Mahomes',
            'player_position': 'QB',
            'pick_type': 'FTD',
            'odds': 10.0,
            'stake': 1.0
        })
        assert response.status_code in [200, 201]


class TestWeekDetailAPI:
    """Test /api/week-detail endpoint"""
    
    def test_week_detail_structure(self, client):
        """Verify week detail endpoint returns correct structure"""
        response = client.get('/api/week-detail?week=1&season=2025')
        assert response.status_code == 200
        
        data = response.get_json()
        
        # Required keys
        assert 'games' in data
        assert 'week' in data
        assert 'season' in data
        
        assert isinstance(data['games'], list)
        assert isinstance(data['week'], int)
        assert isinstance(data['season'], int)


class TestUsersAPI:
    """Test /api/users endpoint"""
    
    def test_users_structure(self, client):
        """Verify users endpoint returns correct structure"""
        response = client.get('/api/users')
        assert response.status_code == 200
        
        data = response.get_json()
        assert 'users' in data
        assert isinstance(data['users'], list)


class TestGamesAPI:
    """Test /api/games endpoint"""
    
    def test_games_structure(self, client):
        """Verify games endpoint returns correct structure"""
        response = client.get('/api/games?season=2025')
        assert response.status_code == 200
        
        data = response.get_json()
        assert 'games' in data
        assert isinstance(data['games'], list)


class TestWeeklyGamesAPI:
    """Test /api/weekly-games endpoint"""
    
    def test_weekly_games_structure(self, client):
        """Verify weekly games endpoint returns correct structure"""
        response = client.get('/api/weekly-games?week=1&season=2025')
        assert response.status_code == 200
        
        data = response.get_json()
        
        assert 'games' in data
        assert 'week' in data
        assert 'season' in data
        assert isinstance(data['games'], list)


class TestDashboardStatsAPI:
    """Test /api/admin/dashboard-stats endpoint"""
    
    def test_dashboard_stats_structure(self, client):
        """Verify dashboard stats endpoint returns correct structure"""
        response = client.get('/api/admin/dashboard-stats?season=2025')
        assert response.status_code == 200
        
        data = response.get_json()
        
        # Required fields
        required_fields = [
            'total_players', 'current_week', 'total_picks_this_week',
            'pending_picks', 'league_ftd_bankroll', 'league_atts_bankroll',
            'overall_win_rate', 'games_this_week', 'games_graded', 'recent_picks'
        ]
        
        for field in required_fields:
            assert field in data
        
        assert isinstance(data['recent_picks'], list)


class TestErrorResponses:
    """Test that error responses follow consistent format"""
    
    def test_404_error_format(self, client):
        """Verify 404 errors return consistent format"""
        response = client.get('/api/nonexistent')
        assert response.status_code == 404
    
    def test_400_error_format(self, client):
        """Verify 400 errors return error key"""
        response = client.post('/api/picks', json={'invalid': 'data'})
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data or 'message' in data


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
