"""
Quick verification script to check imported data
"""
from app import create_app, db
from app.models import User, Game, Pick
from sqlalchemy import func

app = create_app()

with app.app_context():
    print("\n" + "="*60)
    print("DATABASE VERIFICATION")
    print("="*60)
    
    # User summary
    print("\n📊 USERS:")
    users = User.query.all()
    for user in users:
        ftd_count = Pick.query.filter_by(user_id=user.id, pick_type='FTD').count()
        atts_count = Pick.query.filter_by(user_id=user.id, pick_type='ATTS').count()
        wins = Pick.query.filter_by(user_id=user.id, pick_type='FTD', result='W').count()
        losses = Pick.query.filter_by(user_id=user.id, pick_type='FTD', result='L').count()
        pending = Pick.query.filter_by(user_id=user.id, pick_type='FTD', result='Pending').count()
        
        print(f"  {user.username:10s} - FTD: {ftd_count:2d} ({wins}W/{losses}L/{pending}P), ATTS: {atts_count:2d}")
    
    # Game summary
    print(f"\n🏈 GAMES: {Game.query.count()} total")
    games_by_week = db.session.query(
        Game.week, func.count(Game.id)
    ).group_by(Game.week).order_by(Game.week).all()
    
    print("  Weeks with games:")
    for week, count in games_by_week:
        print(f"    Week {week:2d}: {count} games")
    
    # Pick summary
    total_picks = Pick.query.count()
    ftd_picks = Pick.query.filter_by(pick_type='FTD').count()
    atts_picks = Pick.query.filter_by(pick_type='ATTS').count()
    
    print(f"\n🎯 PICKS: {total_picks} total")
    print(f"  - FTD picks: {ftd_picks}")
    print(f"  - ATTS picks: {atts_picks}")
    
    # Results breakdown
    print("\n📈 RESULTS (FTD only):")
    wins = Pick.query.filter_by(pick_type='FTD', result='W').count()
    losses = Pick.query.filter_by(pick_type='FTD', result='L').count()
    pending = Pick.query.filter_by(pick_type='FTD', result='Pending').count()
    
    print(f"  Wins: {wins}")
    print(f"  Losses: {losses}")
    print(f"  Pending: {pending}")
    
    # Sample picks
    print("\n🔍 SAMPLE PICKS (First 5):")
    sample_picks = Pick.query.filter_by(pick_type='FTD').limit(5).all()
    for pick in sample_picks:
        game = Game.query.get(pick.game_id)
        print(f"  Week {game.week}: {pick.user.username} picked {pick.player_name} ({pick.odds:+d}) - {pick.result}")
    
    print("\n" + "="*60)
