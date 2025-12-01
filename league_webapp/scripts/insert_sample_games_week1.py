
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app import create_app, db
from app.models import Game
from datetime import date, time

app = create_app()

SEASON = 2025
WEEK = 1
games_to_insert = [
    {
        'game_id': '2025_01_DAL_PHI', 'season': SEASON, 'week': WEEK, 'gameday': 'Thursday', 'game_date': date(2025, 9, 4), 'game_time': time(20, 15), 'home_team': 'PHI', 'away_team': 'DAL'
    },
    {
        'game_id': '2025_01_KC_LAC', 'season': SEASON, 'week': WEEK, 'gameday': 'Friday', 'game_date': date(2025, 9, 5), 'game_time': time(20, 15), 'home_team': 'LAC', 'away_team': 'KC'
    },
    {
        'game_id': '2025_01_BAL_BUF', 'season': SEASON, 'week': WEEK, 'gameday': 'Sunday', 'game_date': date(2025, 9, 7), 'game_time': time(13, 0), 'home_team': 'BUF', 'away_team': 'BAL'
    },
    {
        'game_id': '2025_01_MIN_CHI', 'season': SEASON, 'week': WEEK, 'gameday': 'Monday', 'game_date': date(2025, 9, 8), 'game_time': time(20, 15), 'home_team': 'CHI', 'away_team': 'MIN'
    },
]

with app.app_context():
    for g in games_to_insert:
        exists = Game.query.filter_by(game_id=g['game_id']).first()
        if not exists:
            game = Game(**g)
            db.session.add(game)
            print(f"Inserted game: {g['game_id']}")
        else:
            print(f"Game already exists: {g['game_id']}")
    db.session.commit()
    print("Done inserting games.")