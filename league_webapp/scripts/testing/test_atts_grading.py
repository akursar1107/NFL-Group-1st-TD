from app import create_app, db
from app.models import Pick, Game
from app.data_loader import load_data_with_cache_web, get_all_td_scorers
import sys

app = create_app()

with app.app_context():
    # Find a week with ATTS picks
    atts_picks = Pick.query.filter_by(pick_type='ATTS').all()
    
    if not atts_picks:
        print("No ATTS picks found")
        sys.exit(1)
    
    # Get week 2 (has ATTS picks)
    week = 2
    season = 2025
    
    print(f"Testing ATTS grading for Week {week}, {season} season\n")
    
    # Load data
    print("Loading NFL data...")
    schedule_df, pbp_df, roster_df = load_data_with_cache_web(season, use_cache=True)
    
    # Get games
    games = Game.query.filter_by(week=week, season=season).all()
    game_ids = [g.game_id for g in games]
    
    print(f"Found {len(games)} games in week {week}")
    
    # Get all TD scorers
    print("\nGetting all TD scorers...")
    all_td_map = get_all_td_scorers(pbp_df, target_game_ids=game_ids, roster_df=roster_df)
    
    print(f"Found TD data for {len(all_td_map)} games\n")
    
    # Display TD scorers
    for game_id, scorers in all_td_map.items():
        game = next((g for g in games if g.game_id == game_id), None)
        if game:
            scorer_names = [s['player'] for s in scorers]
            print(f"{game.away_team} @ {game.home_team}:")
            print(f"  TD Scorers: {', '.join(scorer_names)}")
    
    # Check ATTS picks for this week
    week_atts_picks = Pick.query.join(Game).filter(
        Game.week == week,
        Game.season == season,
        Pick.pick_type == 'ATTS'
    ).all()
    
    print(f"\nATTS picks for week {week}: {len(week_atts_picks)}")
    for pick in week_atts_picks:
        print(f"  {pick.user.username}: {pick.player_name} ({pick.game.away_team} @ {pick.game.home_team})")
