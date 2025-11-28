"""
Auto-grade picks for a specific week using NFL play-by-play data
"""
from datetime import datetime
from app import create_app, db
from app.models import User, Game, Pick
from nfl_core.data import load_data_with_cache
from nfl_core.stats import get_first_td_scorers

def grade_week(week_num, season=2025):
    """
    Grade all picks for a specific week
    """
    app = create_app()
    
    with app.app_context():
        print(f"\n{'='*60}")
        print(f"GRADING WEEK {week_num} - {season} SEASON")
        print(f"{'='*60}\n")
        
        # Load NFL data
        print("Loading NFL data...")
        schedule_df, pbp_df, roster_df = load_data_with_cache(season)
        
        # Get games for this week
        games = Game.query.filter_by(week=week_num, season=season).all()
        
        if not games:
            print(f"❌ No games found for Week {week_num}")
            return
        
        print(f"Found {len(games)} games for Week {week_num}")
        
        # Get game IDs to grade
        game_ids = [g.game_id for g in games]
        
        # Get first TD scorers from play-by-play data
        print("\nAnalyzing play-by-play data for first TD scorers...")
        first_td_map = get_first_td_scorers(pbp_df, target_game_ids=game_ids, roster_df=roster_df)
        
        if not first_td_map:
            print("❌ No first TD data found. Games may not have been played yet.")
            return
        
        print(f"Found first TD scorers for {len(first_td_map)} games")
        
        # Grade each game
        games_graded = 0
        picks_graded = 0
        picks_won = 0
        picks_lost = 0
        
        for game in games:
            # Check if this game has a first TD scorer
            if game.game_id not in first_td_map:
                print(f"⏭️  Skipping {game.away_team}@{game.home_team} - No first TD data yet")
                continue
            
            # Get actual first TD scorer
            td_data = first_td_map[game.game_id]
            actual_player = td_data.get('player', '').strip()
            actual_team = td_data.get('team', '')
            actual_player_id = td_data.get('player_id')
            
            if not actual_player:
                print(f"⚠️  {game.away_team}@{game.home_team} - Invalid first TD data")
                continue
            
            print(f"\n🏈 {game.away_team} @ {game.home_team}")
            print(f"   First TD: {actual_player} ({actual_team})")
            
            # Update game record
            game.actual_first_td_player = actual_player
            game.actual_first_td_team = actual_team
            game.actual_first_td_player_id = actual_player_id
            game.is_final = True
            
            # Get all FTD picks for this game
            picks = Pick.query.filter_by(game_id=game.id, pick_type='FTD').all()
            
            if not picks:
                print(f"   No picks to grade")
                games_graded += 1
                continue
            
            # Grade each pick
            for pick in picks:
                # Skip if already graded
                if pick.graded_at:
                    continue
                
                pick_player = pick.player_name.strip()
                
                # Fuzzy match (case-insensitive, handle common variations)
                is_winner = False
                
                # Exact match (case-insensitive)
                if pick_player.lower() == actual_player.lower():
                    is_winner = True
                # Handle common name variations
                elif pick_player.lower() in actual_player.lower() or actual_player.lower() in pick_player.lower():
                    # Only match if substantial overlap (avoid false positives)
                    if len(pick_player) > 3 and len(actual_player) > 3:
                        is_winner = True
                
                if is_winner:
                    pick.result = 'W'
                    pick.payout = pick.calculate_payout()
                    picks_won += 1
                    print(f"   ✅ {pick.user.username}: {pick_player} ({pick.odds:+d}) - WIN (${pick.payout:.2f})")
                else:
                    pick.result = 'L'
                    pick.payout = -pick.stake
                    picks_lost += 1
                    print(f"   ❌ {pick.user.username}: {pick_player} ({pick.odds:+d}) - LOSS")
                
                pick.graded_at = datetime.utcnow()
                picks_graded += 1
            
            games_graded += 1
        
        # Commit all changes
        db.session.commit()
        
        # Print summary
        print(f"\n{'='*60}")
        print(f"GRADING COMPLETE")
        print(f"{'='*60}")
        print(f"Games Graded: {games_graded}")
        print(f"Picks Graded: {picks_graded}")
        print(f"  ✅ Wins: {picks_won}")
        print(f"  ❌ Losses: {picks_lost}")
        
        if picks_graded > 0:
            win_rate = (picks_won / picks_graded) * 100
            print(f"  📊 Win Rate: {win_rate:.1f}%")
        
        print(f"\n✅ Week {week_num} grading complete!\n")

if __name__ == '__main__':
    # Default to current week if not specified
    import sys
    
    if len(sys.argv) > 1:
        week = int(sys.argv[1])
    else:
        # Ask for week
        week_input = input("Enter week number to grade (1-18): ")
        week = int(week_input)
    
    grade_week(week)
