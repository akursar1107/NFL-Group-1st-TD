import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'league_webapp'))

from app import create_app, db
from app.services.grading_service import GradingService
from app.models import Pick, Game

app = create_app()
with app.app_context():
    # Re-grade Week 11
    gs = GradingService()
    result = gs.grade_week(11, 2025, use_cache=True, force_regrade=True)
    
    print('Week 11 Re-grading Results:')
    print(f'  Games graded: {result["games_graded"]}')
    print(f'  Total picks: {result["total_graded"]}')
    print(f'  Wins: {result["total_won"]}')
    print(f'  Losses: {result["total_lost"]}')
    print()
    
    # Check the specific picks
    picks = Pick.query.join(Game).filter(Game.week == 11, Game.season == 2025).all()
    print('Week 11 Picks After Re-grading:')
    for pick in picks:
        print(f'  {pick.user.username}: {pick.player_name} - {pick.result} - Payout: ${pick.payout:.2f}')
