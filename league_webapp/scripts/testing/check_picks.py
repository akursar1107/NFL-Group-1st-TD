from app import create_app, db
from app.models import Pick

app = create_app()

with app.app_context():
    ftd_count = Pick.query.filter_by(pick_type='FTD').count()
    atts_count = Pick.query.filter_by(pick_type='ATTS').count()
    
    print(f"FTD picks: {ftd_count}")
    print(f"ATTS picks: {atts_count}")
    
    if atts_count > 0:
        print("\nSample ATTS picks:")
        atts_samples = Pick.query.filter_by(pick_type='ATTS').limit(5).all()
        for pick in atts_samples:
            print(f"  Week {pick.game.week}: {pick.user.username} - {pick.player_name} ({pick.result})")
