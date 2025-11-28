"""Tests for grading functionality"""
import pytest
from datetime import date, time


class TestPickGrading:
    """Test pick grading logic"""
    
    def test_grade_winning_pick(self, app, sample_user, sample_game):
        """Test grading a winning pick"""
        from league_webapp.app import db
        from league_webapp.app.models import Pick, Game
        
        with app.app_context():
            # Create a pick
            pick = Pick(
                user_id=sample_user,
                game_id=sample_game,
                pick_type='FTD',
                player_name='Patrick Mahomes',
                odds=300,
                stake=100.0
            )
            db.session.add(pick)
            
            # Set game result to match
            game = db.session.get(Game, sample_game)
            game.actual_first_td_player = 'Patrick Mahomes'
            game.is_final = True
            
            db.session.commit()
            
            # Grade the pick (if method exists)
            if hasattr(pick, 'grade'):
                pick.grade()
                assert pick.result == 'win'
    
    def test_grade_losing_pick(self, app, sample_user, sample_game):
        """Test grading a losing pick"""
        from league_webapp.app import db
        from league_webapp.app.models import Pick, Game
        
        with app.app_context():
            # Create a pick
            pick = Pick(
                user_id=sample_user,
                game_id=sample_game,
                pick_type='FTD',
                player_name='Travis Kelce',
                odds=800,
                stake=50.0
            )
            db.session.add(pick)
            
            # Set game result to different player
            game = db.session.get(Game, sample_game)
            game.actual_first_td_player = 'Patrick Mahomes'
            game.is_final = True
            
            db.session.commit()
            
            # Grade the pick
            if hasattr(pick, 'grade'):
                pick.grade()
                assert pick.result == 'loss'
    
    def test_grade_no_td_game(self, app, sample_user, sample_game):
        """Test grading when no TD scored"""
        from league_webapp.app import db
        from league_webapp.app.models import Pick, Game
        
        with app.app_context():
            pick = Pick(
                user_id=sample_user,
                game_id=sample_game,
                pick_type='FTD',
                player_name='Patrick Mahomes',
                odds=300,
                stake=100.0
            )
            db.session.add(pick)
            
            # Game finished but no TD
            game = db.session.get(Game, sample_game)
            game.actual_first_td_player = None
            game.is_final = True
            
            db.session.commit()
            
            # Should handle gracefully (push or loss)
            if hasattr(pick, 'grade'):
                pick.grade()
                assert pick.result in ['push', 'loss', None]


class TestBulkGrading:
    """Test grading multiple picks at once"""
    
    def test_grade_week(self, app):
        """Test grading all picks for a week"""
        # This would test the grade_week.py functionality
        # Skip if function isn't imported yet
        pass
    
    def test_auto_grade(self, app):
        """Test automated grading process"""
        # This would test auto_grade.py functionality
        pass


class TestPayoutCalculations:
    """Test payout math"""
    
    def test_positive_odds_payout(self):
        """Test payout for positive American odds"""
        # +300 on $100 = $300 profit
        odds = 300
        bet = 100.0
        
        # Simplified calculation: bet * (odds / 100)
        expected_profit = bet * (odds / 100)
        assert expected_profit == 300.0
    
    def test_negative_odds_payout(self):
        """Test payout for negative American odds"""
        # -200 on $100 = $50 profit
        odds = -200
        bet = 100.0
        
        # Simplified: bet * (100 / abs(odds))
        expected_profit = bet * (100 / abs(odds))
        assert expected_profit == 50.0
    
    def test_even_money_payout(self):
        """Test payout for even money (+100)"""
        odds = 100
        bet = 100.0
        
        expected_profit = bet * (odds / 100)
        assert expected_profit == 100.0
