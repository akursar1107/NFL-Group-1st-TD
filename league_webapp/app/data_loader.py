"""
Modified data loading for web app - no interactive prompts
"""
import nflreadpy as nfl
import polars as pl
import os
import requests
import io

def load_data_with_cache_web(season: int, use_cache: bool = True) -> tuple[pl.DataFrame, pl.DataFrame, pl.DataFrame]:
    """
    Loads schedule, pbp, and roster data for web app (no interactive prompts).
    
    Args:
        season: NFL season year
        use_cache: If True, use cached data if available. If False, always download fresh.
    
    Returns:
        Tuple of (schedule_df, pbp_df, roster_df)
    """
    cache_dir = "../cache"
    os.makedirs(cache_dir, exist_ok=True)
    
    schedule_path = os.path.join(cache_dir, f"season_{season}_schedule.parquet")
    pbp_path = os.path.join(cache_dir, f"season_{season}_pbp.parquet")
    roster_path = os.path.join(cache_dir, f"season_{season}_roster.parquet")
    
    # Use cache if requested and files exist
    if use_cache and os.path.exists(schedule_path) and os.path.exists(pbp_path) and os.path.exists(roster_path):
        try:
            schedule_df = pl.read_parquet(schedule_path)
            pbp_df = pl.read_parquet(pbp_path)
            roster_df = pl.read_parquet(roster_path)
            return schedule_df, pbp_df, roster_df
        except Exception as e:
            print(f"Error loading cache: {e}. Downloading fresh data.")
    
    # Download fresh data
    # Schedule
    try:
        schedule_df = nfl.load_schedules(seasons=season)
        if not isinstance(schedule_df, pl.DataFrame):
            schedule_df = pl.from_pandas(schedule_df)
    except Exception as e:
        print(f"nflreadpy schedule load failed ({e}), trying manual download...")
        url = "https://github.com/nflverse/nfldata/raw/master/data/games.csv"
        r = requests.get(url)
        schedule_df = pl.read_csv(io.BytesIO(r.content))

    # PBP
    try:
        pbp_df = nfl.load_pbp(seasons=season)
        if not isinstance(pbp_df, pl.DataFrame):
            pbp_df = pl.from_pandas(pbp_df)
    except Exception as e:
        print(f"nflreadpy pbp load failed ({e}), trying manual download...")
        url = f"https://github.com/nflverse/nflverse-data/releases/download/pbp/play_by_play_{season}.parquet"
        r = requests.get(url)
        pbp_df = pl.read_parquet(io.BytesIO(r.content))
    
    # Filter PBP to only touchdown plays to reduce memory/storage
    print(f"Original PBP size: {pbp_df.height:,} plays")
    pbp_df = pbp_df.filter(
        (pl.col('touchdown') == 1) | 
        (pl.col('td_player_name').is_not_null())
    )
    print(f"Filtered to TD plays only: {pbp_df.height:,} plays")

    # Roster
    try:
        roster_df = nfl.load_rosters(seasons=season)
        if not isinstance(roster_df, pl.DataFrame):
            roster_df = pl.from_pandas(roster_df)
    except Exception as e:
        print(f"nflreadpy roster load failed ({e}), trying manual download...")
        url = f"https://github.com/nflverse/nflverse-data/releases/download/rosters/roster_{season}.parquet"
        r = requests.get(url)
        roster_df = pl.read_parquet(io.BytesIO(r.content))

    # Save to cache
    schedule_df.write_parquet(schedule_path)
    pbp_df.write_parquet(pbp_path)
    roster_df.write_parquet(roster_path)
    
    return schedule_df, pbp_df, roster_df

def get_current_nfl_week(season: int = 2025) -> int:
    """
    Determine the current NFL week based on today's date.
    Returns the week number (1-18) or 0 if season hasn't started.
    """
    from datetime import datetime, timezone
    
    # Load schedule to determine current week
    cache_dir = "../cache"
    schedule_path = os.path.join(cache_dir, f"season_{season}_schedule.parquet")
    
    if os.path.exists(schedule_path):
        try:
            schedule_df = pl.read_parquet(schedule_path)
        except:
            return 13  # Default fallback to week 13 (current as of Nov 2025)
    else:
        return 13  # Default fallback
    
    # Get today's date
    today = datetime.now(timezone.utc).date()
    
    # Filter schedule for games on or before today
    schedule_df = schedule_df.with_columns(
        pl.col("gameday").str.strptime(pl.Date, format="%Y-%m-%d", strict=False).alias("game_date")
    )
    
    past_games = schedule_df.filter(pl.col("game_date") <= today)
    
    if past_games.height == 0:
        return 0  # Season hasn't started
    
    # Get the latest week
    current_week = past_games.select(pl.col("week").max()).item()
    
    return int(current_week) if current_week else 13

def get_all_td_scorers(pbp_df: pl.DataFrame, target_game_ids: list[str] | None = None, roster_df: pl.DataFrame | None = None) -> dict:
    """
    Processes play-by-play data to find ALL touchdown scorers for specified games.
    Used for grading Anytime TD Scorer (ATTS) picks.
    
    Args:
        pbp_df: Play-by-play DataFrame
        target_game_ids: Optional list of game IDs to filter for
        roster_df: Optional roster DataFrame for player name lookup
        
    Returns:
        Dict mapping game_id to list of TD scorers:
        {game_id: [{'player': str, 'team': str, 'player_id': str}, ...]}
    """
    all_td_map = {}
    
    if pbp_df.height == 0:
        return all_td_map

    # Filter for only the games we care about
    if target_game_ids:
        pbp_df = pbp_df.filter(pl.col("game_id").is_in(target_game_ids))
        if pbp_df.height == 0:
            return all_td_map

    # Filter for touchdown plays
    td_plays = pbp_df.filter(
        (pl.col('touchdown') == 1) | 
        (pl.col('td_player_name').is_not_null())
    )

    if td_plays.height == 0:
        return all_td_map

    # Create ID to name mapping from roster
    id_to_name = {}
    if roster_df is not None and "gsis_id" in roster_df.columns and "full_name" in roster_df.columns:
        temp_df = roster_df.select(["gsis_id", "full_name"]).unique()
        for r in temp_df.to_dicts():
            if r["gsis_id"] and r["full_name"]:
                id_to_name[r["gsis_id"]] = r["full_name"]

    # Group by game_id to process each game
    for game_id in td_plays.select(pl.col("game_id").unique()).to_series():
        game_tds = td_plays.filter(pl.col("game_id") == game_id)
        scorers = []
        seen_players = set()  # Track unique players by ID or name
        
        for row in game_tds.to_dicts():
            player_id = row.get('td_player_id')
            scorer = None
            
            # 1. Try roster lookup
            if player_id and player_id in id_to_name:
                scorer = id_to_name[player_id]
            
            # 2. Try PBP columns if no roster match
            if not scorer:
                for key in ['fantasy_player_name', 'player_name', 'td_player_name', 'desc', 'description']:
                    if key in row and row.get(key):
                        scorer = str(row.get(key))
                        if key in ['desc', 'description'] and ' for ' in scorer:
                            scorer = scorer.split(' for ')[0].strip()
                        break
            
            # Get team
            team = row.get('td_team') or row.get('posteam') or "UNK"
            
            # Only add if we have a scorer and haven't seen this player yet
            if scorer:
                # Use player_id as unique key if available, otherwise use normalized name
                unique_key = player_id if player_id else scorer.lower().strip()
                
                if unique_key not in seen_players:
                    seen_players.add(unique_key)
                    scorers.append({
                        'player': scorer,
                        'team': team,
                        'player_id': player_id
                    })
        
        if scorers:
            all_td_map[game_id] = scorers
            
    return all_td_map
