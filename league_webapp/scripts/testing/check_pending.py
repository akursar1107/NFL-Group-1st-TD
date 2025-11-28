from app.data_loader import get_current_nfl_week
from app.models import Game, Pick
from app import create_app, db

app = create_app()

with app.app_context():
    current_week = get_current_nfl_week(2025)
    
    print(f'Current Week: {current_week}')
    
    # Check Week 13 (current week) for pending picks
    games_week13 = Game.query.filter_by(week=13, season=2025).all()
    print(f'\nWeek 13 Games: {len(games_week13)}')
    for g in games_week13[:3]:
        print(f'  {g.game_id}: {g.away_team} @ {g.home_team}')
    
    pending_week13 = Pick.query.join(Game).filter(
        Game.week == 13,
        Game.season == 2025,
        Pick.result == 'Pending'
    ).all()
    
    print(f'\nPending picks for Week 13: {len(pending_week13)}')
    if pending_week13:
        for p in pending_week13[:5]:
            print(f'  {p.user.username} - {p.player_name} ({p.pick_type})')
    
    # Check all picks for any week
    all_pending = Pick.query.join(Game).filter(
        Game.season == 2025,
        Pick.result == 'Pending'
    ).all()
    print(f'\nTotal pending picks for 2025 season: {len(all_pending)}')
    if all_pending:
        weeks_with_pending = set()
        for p in all_pending:
            weeks_with_pending.add(p.game.week)
        print(f'Weeks with pending picks: {sorted(weeks_with_pending)}')
