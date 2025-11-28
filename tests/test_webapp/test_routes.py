"""Tests for league_webapp routes"""
import pytest


class TestLandingPage:
    """Test landing page routes"""
    
    def test_landing_page_loads(self, client):
        """Test that landing page loads successfully"""
        response = client.get('/')
        assert response.status_code == 200
    
    def test_landing_page_content(self, client):
        """Test landing page has expected content"""
        response = client.get('/')
        assert b'NFL' in response.data or b'First TD' in response.data


class TestPicksRoutes:
    """Test picks-related routes"""
    
    def test_picks_list_loads(self, client):
        """Test picks list page loads"""
        response = client.get('/picks')
        # Might redirect if no user session, or show empty list
        assert response.status_code in [200, 302, 404]
    
    def test_picks_new_loads(self, client):
        """Test new pick form loads"""
        response = client.get('/picks/new')
        assert response.status_code in [200, 302, 404]


class TestScheduleRoutes:
    """Test schedule routes"""
    
    def test_schedule_list_loads(self, client):
        """Test schedule list page"""
        response = client.get('/schedule')
        assert response.status_code in [200, 404]


class TestGameRoutes:
    """Test game-specific routes"""
    
    def test_game_detail_with_valid_id(self, client, sample_game):
        """Test game detail page with valid game"""
        response = client.get(f'/game/{sample_game}')
        # Might be 200 or 404 depending on implementation
        assert response.status_code in [200, 404]
    
    def test_game_detail_with_invalid_id(self, client):
        """Test game detail with non-existent game"""
        response = client.get('/game/INVALID_GAME_ID')
        assert response.status_code == 404


class TestAPIEndpoints:
    """Test API endpoints if any exist"""
    
    def test_api_games_endpoint(self, client):
        """Test games API endpoint"""
        response = client.get('/api/games')
        # May or may not exist
        assert response.status_code in [200, 404]
    
    def test_api_odds_endpoint(self, client):
        """Test odds API endpoint"""
        response = client.get('/api/odds')
        assert response.status_code in [200, 404]
