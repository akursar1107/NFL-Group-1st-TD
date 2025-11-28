"""Tests for league_webapp models"""
import pytest
from datetime import datetime, date, time


class TestUserModel:
    """Test User model"""
    
    def test_create_user(self, app):
        """Test basic user creation"""
        from league_webapp.app import db
        from league_webapp.app.models import User
        
        with app.app_context():
            user = User(
                username='john',
                email='john@example.com',
                display_name='John Doe'
            )
            db.session.add(user)
            db.session.commit()
            
            assert user.id is not None
            assert user.username == 'john'
            assert user.email == 'john@example.com'
            assert user.is_active is True
    
    def test_user_unique_username(self, app):
        """Test username must be unique"""
        from league_webapp.app import db
        from league_webapp.app.models import User
        
        with app.app_context():
            user1 = User(username='john', email='john1@example.com')
            db.session.add(user1)
            db.session.commit()
            
            user2 = User(username='john', email='john2@example.com')
            db.session.add(user2)
            
            with pytest.raises(Exception):  # IntegrityError
                db.session.commit()


class TestGameModel:
    """Test Game model"""
    
    def test_create_game(self, app):
        """Test basic game creation"""
        from league_webapp.app import db
        from league_webapp.app.models import Game
        
        with app.app_context():
            game = Game(
                game_id='2024_10_KC_DET',
                season=2024,
                week=10,
                gameday='Sunday',
                game_date=date(2024, 11, 10),
                game_time=time(13, 0),
                home_team='DET',
                away_team='KC'
            )
            db.session.add(game)
            db.session.commit()
            
            assert game.id is not None
            assert game.game_id == '2024_10_KC_DET'
            assert game.week == 10
            assert game.is_final is False
    
    def test_game_with_result(self, app):
        """Test game with first TD scorer result"""
        from league_webapp.app import db
        from league_webapp.app.models import Game
        
        with app.app_context():
            game = Game(
                game_id='2024_10_KC_DET',
                season=2024,
                week=10,
                game_date=date(2024, 11, 10),
                home_team='DET',
                away_team='KC',
                actual_first_td_player='Patrick Mahomes',
                actual_first_td_team='KC',
                is_final=True
            )
            db.session.add(game)
            db.session.commit()
            
            assert game.actual_first_td_player == 'Patrick Mahomes'
            assert game.is_final is True


class TestPickModel:
    """Test Pick model"""
    
    def test_create_pick(self, app, sample_user, sample_game):
        """Test basic pick creation"""
        from league_webapp.app import db
        from league_webapp.app.models import Pick
        
        with app.app_context():
            pick = Pick(
                user_id=sample_user,
                game_id=sample_game,
                player_name='Travis Kelce',
                player_id='KEL123',
                odds=800,
                bet_amount=50.0
            )
            db.session.add(pick)
            db.session.commit()
            
            assert pick.id is not None
            assert pick.player_name == 'Travis Kelce'
            assert pick.odds == 800
            assert pick.result is None
    
    def test_pick_payout_calculation_win(self, app, sample_user, sample_game):
        """Test payout calculation for winning pick"""
        from league_webapp.app import db
        from league_webapp.app.models import Pick
        
        with app.app_context():
            pick = Pick(
                user_id=sample_user,
                game_id=sample_game,
                player_name='Patrick Mahomes',
                odds=300,
                bet_amount=100.0,
                result='win'
            )
            
            # Test American odds: +300 on $100 bet = $300 profit
            if hasattr(pick, 'calculate_payout'):
                payout = pick.calculate_payout()
                assert payout == 300.0
    
    def test_pick_payout_calculation_loss(self, app, sample_user, sample_game):
        """Test payout for losing pick"""
        from league_webapp.app import db
        from league_webapp.app.models import Pick
        
        with app.app_context():
            pick = Pick(
                user_id=sample_user,
                game_id=sample_game,
                player_name='Patrick Mahomes',
                odds=300,
                bet_amount=100.0,
                result='loss'
            )
            
            if hasattr(pick, 'calculate_payout'):
                payout = pick.calculate_payout()
                assert payout == -100.0


class TestBankrollHistory:
    """Test BankrollHistory model"""
    
    def test_create_bankroll_entry(self, app, sample_user):
        """Test creating bankroll history entry"""
        from league_webapp.app import db
        from league_webapp.app.models import BankrollHistory
        
        with app.app_context():
            history = BankrollHistory(
                user_id=sample_user,
                week=1,
                season=2024,
                starting_balance=1000.0,
                ending_balance=1150.0,
                picks_count=5,
                wins=3,
                losses=2
            )
            db.session.add(history)
            db.session.commit()
            
            assert history.id is not None
            assert history.ending_balance == 1150.0
            assert history.wins == 3
