from app import create_app, db
from app.models import Game
from datetime import date, time

app = create_app()

with app.app_context():
    # Add missing Week 13 games
    missing_games = [
        {
            'game_id': '2025_13_DEN_WAS',
            'season': 2025,
            'week': 13,
            'gameday': 'Sunday',
            'game_date': date(2025, 11, 30),
            'game_time': time(13, 0),  # 1pm ET
            'home_team': 'WAS',
            'away_team': 'DEN',
            'is_standalone': True
        },
        {
            'game_id': '2025_13_NYG_NE',
            'season': 2025,
            'week': 13,
            'gameday': 'Monday',
            'game_date': date(2025, 12, 1),
            'game_time': time(20, 15),  # 8:15pm ET
            'home_team': 'NE',
            'away_team': 'NYG',
            'is_standalone': True
        }
    ]
    
    for game_data in missing_games:
        # Check if exists
        existing = Game.query.filter_by(game_id=game_data['game_id']).first()
        if existing:
            print(f"Game already exists: {game_data['away_team']} @ {game_data['home_team']}")
        else:
            new_game = Game(**game_data)
            db.session.add(new_game)
            print(f"✓ Added: {game_data['away_team']} @ {game_data['home_team']} ({game_data['gameday']})")
    
    db.session.commit()
    print("\nDone!")
    
    # Verify
    all_w13 = Game.query.filter_by(week=13, season=2025, is_standalone=True).order_by(Game.game_date, Game.game_time).all()
    print(f"\nWeek 13 standalone games ({len(all_w13)}):")
    for g in all_w13:
        print(f"  {g.away_team} @ {g.home_team} ({g.gameday})")
