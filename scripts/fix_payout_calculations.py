"""
Fix payout calculations for all graded picks
Recalculates payouts to include stake return for wins
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'league_webapp'))

from app import create_app, db
from app.models import Pick

def fix_payouts():
    """Recalculate all pick payouts"""
    app = create_app()
    with app.app_context():
        # Get all graded picks
        graded_picks = Pick.query.filter(Pick.result.in_(['W', 'L'])).all()
        
        print(f"Found {len(graded_picks)} graded picks to update")
        
        updated_wins = 0
        updated_losses = 0
        
        for pick in graded_picks:
            old_payout = pick.payout
            # Recalculate using the fixed method
            new_payout = pick.calculate_payout()
            
            if abs(old_payout - new_payout) > 0.01:  # Only update if changed
                pick.payout = new_payout
                
                if pick.result == 'W':
                    updated_wins += 1
                    print(f"  Win: {pick.player_name} - Odds:{pick.odds} - Old:${old_payout:.2f} -> New:${new_payout:.2f}")
                else:
                    updated_losses += 1
        
        # Commit changes
        db.session.commit()
        
        print(f"\n✅ Updated {updated_wins} winning picks")
        print(f"✅ Updated {updated_losses} losing picks")
        print(f"✅ Total updated: {updated_wins + updated_losses}")

if __name__ == '__main__':
    fix_payouts()
