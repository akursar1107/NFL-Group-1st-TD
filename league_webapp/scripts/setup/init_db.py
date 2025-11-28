"""
Database initialization script for NFL First TD League Web App
"""
from app import create_app, db
from app.models import User, Game, Pick, BankrollHistory
from datetime import date, time

def init_database():
    """Initialize database with test data"""
    app = create_app()
    
    with app.app_context():
        # Drop all tables and recreate
        print("Dropping existing tables...")
        db.drop_all()
        
        print("Creating new tables...")
        db.create_all()
        
        # Create test users
        print("Creating test users...")
        users = [
            User(username='Phil', email='phil@example.com', display_name='Phil'),
            User(username='Anders', email='anders@example.com', display_name='Anders'),
            User(username='Neil', email='neil@example.com', display_name='Neil'),
            User(username='Dan C', email='danc@example.com', display_name='Dan C'),
            User(username='Tony', email='tony@example.com', display_name='Tony'),
            User(username='Luke', email='luke@example.com', display_name='Luke'),
            User(username='Jeremy', email='jeremy@example.com', display_name='Jeremy'),
        ]
        db.session.add_all(users)
        db.session.commit()
        
        # Create a test game (Week 13)
        print("Creating test game...")
        game = Game(
            game_id='2025_13_GB_DET',
            season=2025,
            week=13,
            gameday='Thursday',
            game_date=date(2025, 11, 28),
            game_time=time(12, 30),
            home_team='DET',
            away_team='GB',
            is_standalone=True
        )
        db.session.add(game)
        db.session.commit()
        
        # Create test picks for this game
        print("Creating test picks...")
        jeremy = User.query.filter_by(username='Jeremy').first()
        
        pick1 = Pick(
            user_id=jeremy.id,
            game_id=game.id,
            pick_type='FTD',
            player_name='Wicks',
            player_position='WR',
            odds=2200,
            stake=1.0,
            result='Pending'
        )
        
        pick2 = Pick(
            user_id=jeremy.id,
            game_id=game.id,
            pick_type='ATTS',
            player_name='Wicks',
            player_position='WR',
            odds=330,
            stake=1.0,
            result='Pending'
        )
        
        db.session.add_all([pick1, pick2])
        db.session.commit()
        
        print("\n✅ Database initialized successfully!")
        print(f"   - Created {len(users)} users")
        print(f"   - Created 1 test game (Week 13: GB @ DET)")
        print(f"   - Created 2 test picks (Jeremy: Wicks FTD + ATTS)")
        print("\nRun the app with: python run.py")

if __name__ == '__main__':
    init_database()
