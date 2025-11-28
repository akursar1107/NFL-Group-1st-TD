from app import create_app, db
from app.models import Pick, Game

app = create_app()

with app.app_context():
    # Check Week 13 picks
    week13_picks = Pick.query.join(Game).filter(
        Game.week == 13,
        Game.season == 2025
    ).all()
    
    print('Week 13 Picks:')
    for p in week13_picks:
        print(f'  {p.user.username} - {p.player_name} ({p.pick_type}): {p.result} (${p.payout:.2f})')
    
    # Check remaining pending picks
    pending_all = Pick.query.join(Game).filter(
        Game.season == 2025,
        Pick.result == 'Pending'
    ).count()
    
    print(f'\nRemaining pending picks: {pending_all}')
    
    # Show which weeks still have pending picks
    weeks_with_pending = db.session.query(Game.week).join(Pick).filter(
        Game.season == 2025,
        Pick.result == 'Pending'
    ).distinct().order_by(Game.week).all()
    
    if weeks_with_pending:
        print(f'Weeks with pending picks: {[w[0] for w in weeks_with_pending]}')
