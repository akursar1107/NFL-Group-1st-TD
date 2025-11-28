"""
Automated grading script for weekly picks
Run this script on a schedule (e.g., Tuesdays at 4am EST)
"""
from app import create_app, db
from app.models import Game, Pick
from app.data_loader import load_data_with_cache_web, get_current_nfl_week, get_all_td_scorers
from datetime import datetime
from nfl_core.stats import get_first_td_scorers

def auto_grade_current_week(season=2025):
    """
    Automatically grade the most recently completed NFL week
    """
    app = create_app()
    
    with app.app_context():
        print(f"\n{'='*60}")
        print(f"Auto-grading for {season} season")
        print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*60}\n")
        
        # Get current NFL week
        current_week = get_current_nfl_week(season)
        
        # Grade the previous week (most recently completed)
        week_to_grade = current_week - 1
        
        if week_to_grade < 1:
            print("No completed weeks to grade yet.")
            return
        
        print(f"Current NFL week: {current_week}")
        print(f"Grading week: {week_to_grade}\n")
        
        # Load NFL data (always use cache for auto-grading)
        print("Loading NFL data from cache...")
        schedule_df, pbp_df, roster_df = load_data_with_cache_web(season, use_cache=True)
        print(f"Loaded {len(pbp_df)} play-by-play rows\n")
        
        # Get games for this week
        games = Game.query.filter_by(week=week_to_grade, season=season).all()
        
        if not games:
            print(f"No games found for Week {week_to_grade}")
            return
        
        print(f"Found {len(games)} games in Week {week_to_grade}")
        
        game_ids = [g.game_id for g in games]
        
        # Get first TD scorers
        print("Analyzing first TD scorers...")
        first_td_map = get_first_td_scorers(pbp_df, target_game_ids=game_ids, roster_df=roster_df)
        
        if not first_td_map:
            print("No first TD data found. Games may not have been played yet.")
            return
        
        print(f"Found first TD data for {len(first_td_map)} games\n")
        
        games_graded = 0
        picks_graded = 0
        picks_won = 0
        picks_lost = 0
        
        for game in games:
            if game.game_id not in first_td_map:
                continue
            
            td_data = first_td_map[game.game_id]
            actual_player = td_data.get('player', '').strip()
            
            if not actual_player:
                continue
            
            # Update game
            game.actual_first_td_player = actual_player
            game.actual_first_td_team = td_data.get('team', '')
            game.actual_first_td_player_id = td_data.get('player_id')
            game.is_final = True
            
            print(f"  {game.away_team} @ {game.home_team}: {actual_player}")
            
            # Grade picks
            picks = Pick.query.filter_by(game_id=game.id, pick_type='FTD').all()
            
            for pick in picks:
                if pick.graded_at:
                    continue  # Skip already graded picks
                
                pick_player = pick.player_name.strip()
                
                # Fuzzy match
                is_winner = False
                if pick_player.lower() == actual_player.lower():
                    is_winner = True
                elif pick_player.lower() in actual_player.lower() or actual_player.lower() in pick_player.lower():
                    if len(pick_player) > 3 and len(actual_player) > 3:
                        is_winner = True
                
                if is_winner:
                    pick.result = 'W'
                    pick.payout = pick.calculate_payout()
                    picks_won += 1
                    print(f"    ✓ {pick.user.username}: {pick_player} - WIN (${pick.payout:.2f})")
                else:
                    pick.result = 'L'
                    pick.payout = -pick.stake
                    picks_lost += 1
                    print(f"    ✗ {pick.user.username}: {pick_player} - LOSS")
                
                pick.graded_at = datetime.utcnow()
                picks_graded += 1
            
            games_graded += 1
        
        # === ATTS (Anytime TD Scorer) Grading ===
        print("\nGrading ATTS (Anytime TD) picks...")
        atts_picks_graded = 0
        atts_picks_won = 0
        atts_picks_lost = 0
        
        # Get all TD scorers for the week
        all_td_map = get_all_td_scorers(pbp_df, target_game_ids=game_ids, roster_df=roster_df)
        
        if all_td_map:
            print(f"Found ATTS data for {len(all_td_map)} games\n")
            
            for game in games:
                if game.game_id not in all_td_map:
                    continue
                
                td_scorers = all_td_map[game.game_id]  # List of {'player', 'team', 'player_id'}
                
                if not td_scorers:
                    continue
                
                scorer_names = [s.get('player', '') for s in td_scorers]
                print(f"  {game.away_team} @ {game.home_team}: ATTS - {', '.join(scorer_names)}")
                
                # Grade ATTS picks for this game
                atts_picks = Pick.query.filter_by(game_id=game.id, pick_type='ATTS').all()
                
                for pick in atts_picks:
                    if pick.graded_at:
                        continue
                    
                    pick_player = pick.player_name.strip()
                    
                    # Check if pick_player matches ANY TD scorer (fuzzy match)
                    is_winner = False
                    for scorer_data in td_scorers:
                        actual_player = scorer_data.get('player', '').strip()
                        
                        if not actual_player:
                            continue
                        
                        # Fuzzy match logic (same as FTD)
                        if pick_player.lower() == actual_player.lower():
                            is_winner = True
                            break
                        elif pick_player.lower() in actual_player.lower() or actual_player.lower() in pick_player.lower():
                            if len(pick_player) > 3 and len(actual_player) > 3:
                                is_winner = True
                                break
                    
                    if is_winner:
                        pick.result = 'W'
                        pick.payout = pick.calculate_payout()
                        atts_picks_won += 1
                        print(f"    ✓ {pick.user.username}: {pick_player} - WIN (${pick.payout:.2f})")
                    else:
                        pick.result = 'L'
                        pick.payout = -pick.stake
                        atts_picks_lost += 1
                        print(f"    ✗ {pick.user.username}: {pick_player} - LOSS")
                    
                    pick.graded_at = datetime.utcnow()
                    atts_picks_graded += 1
        else:
            print("No ATTS data found.")
        
        # Commit all changes
        db.session.commit()
        
        print(f"\n{'='*60}")
        print(f"Grading complete!")
        print(f"  Games graded: {games_graded}")
        print(f"  FTD picks graded: {picks_graded} ({picks_won} wins, {picks_lost} losses)")
        print(f"  ATTS picks graded: {atts_picks_graded} ({atts_picks_won} wins, {atts_picks_lost} losses)")
        print(f"  Total: {picks_graded + atts_picks_graded} picks, {picks_won + atts_picks_won} wins, {picks_lost + atts_picks_lost} losses")
        print(f"Finished at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*60}\n")

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Auto-grade NFL First TD picks')
    parser.add_argument('--season', type=int, default=2025, help='Season year (default: 2025)')
    parser.add_argument('--week', type=int, help='Specific week to grade (optional, defaults to current week - 1)')
    
    args = parser.parse_args()
    
    if args.week:
        # Grade specific week
        app = create_app()
        with app.app_context():
            print(f"Grading specific week: {args.week}")
            # Use the same logic but with specified week
            # (Implementation would be similar to auto_grade_current_week but with args.week)
    else:
        # Auto-grade current week
        auto_grade_current_week(args.season)
