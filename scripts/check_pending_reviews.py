#!/usr/bin/env python
"""Check for pending match decisions that need review"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Set working directory to project root
os.chdir(os.path.join(os.path.dirname(__file__), '..'))

from league_webapp.app import create_app, db
from league_webapp.app.models import MatchDecision, Pick, Game, User

def main():
    app = create_app()
    
    with app.app_context():
        # Query pending reviews
        pending_reviews = db.session.query(MatchDecision).join(
            Pick, MatchDecision.pick_id == Pick.id
        ).join(
            Game, Pick.game_id == Game.id
        ).join(
            User, Pick.user_id == User.id
        ).filter(
            MatchDecision.needs_review == True,
            MatchDecision.reviewed_at == None
        ).all()
        
        print(f"\n{'='*80}")
        print(f"Pending Reviews: {len(pending_reviews)}")
        print(f"{'='*80}\n")
        
        if not pending_reviews:
            print("✅ No pending reviews - all matches have been reviewed or auto-accepted")
            return
        
        for decision in pending_reviews:
            pick = decision.pick
            game = pick.game
            user = pick.user
            
            print(f"Review ID: {decision.id}")
            print(f"  User: {user.display_name or user.username}")
            print(f"  Game: {game.away_team} @ {game.home_team} (Week {game.week})")
            print(f"  Pick Type: {pick.pick_type}")
            print(f"  Pick Name: {decision.pick_name}")
            print(f"  Scorer Name: {decision.scorer_name}")
            print(f"  Confidence: {decision.confidence} ({decision.match_score:.2f})")
            print(f"  Reason: {decision.match_reason}")
            print(f"  Odds: {pick.odds:+d}")
            print(f"  Stake: ${pick.stake:.2f}")
            print()

if __name__ == '__main__':
    main()
