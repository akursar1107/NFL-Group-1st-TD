
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app import create_app, db
from app.models import Game

app = create_app()

SEASON = 2025
WEEK = 1

with app.app_context():
    games = Game.query.filter_by(season=SEASON, week=WEEK).all()
    print(f"Found {len(games)} games for season {SEASON}, week {WEEK}:")
    for g in games:
        print(f"game_id: {g.game_id}, home: {g.home_team}, away: {g.away_team}, week: {g.week}, season: {g.season}")
    if len(games) == 0:
        print("No games found for 2025 Week 1. Printing all games in database for troubleshooting:")
        all_games = Game.query.all()
        for g in all_games:
            print(f"game_id: {g.game_id}, home: {g.home_team}, away: {g.away_team}, week: {g.week}, season: {g.season}")
        if len(all_games) == 0:
            print("Game table is completely empty. You need to import games into the database.")
