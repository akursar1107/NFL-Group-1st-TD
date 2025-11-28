"""
Import historical picks from CSV file into database
"""
import csv
from datetime import datetime, date, time as dt_time
from app import create_app, db
from app.models import User, Game, Pick, BankrollHistory
import polars as pl
import nflreadpy as nfl
import os

# Team abbreviation mapping (CSV -> nflverse)
TEAM_MAP = {
    'Dallas': 'DAL', 'Philadelphia': 'PHI', 'Kansas City': 'KC', 'LA Chargers': 'LAC',
    'Baltimore': 'BAL', 'Buffalo': 'BUF', 'Minnesota': 'MIN', 'Chicago': 'CHI',
    'Washington': 'WAS', 'Green Bay': 'GB', 'Atlanta': 'ATL', 'Tampa Bay': 'TB',
    'Houston': 'HOU', 'Las Vegas': 'LV', 'Miami': 'MIA', 'NY Giants': 'NYG',
    'Detriot': 'DET', 'Detroit': 'DET', 'Cincinnati': 'CIN', 'Seattle': 'SEA',
    'Arizona': 'ARI', 'NY Jets': 'NYJ', 'San Fran': 'SF', 'New England': 'NE',
    'Kansas City': 'KC', 'Jacksonville': 'JAX', 'LA Rams': 'LAR', 'Pittsburgh': 'PIT',
    'Denver': 'DEN', 'Carolina': 'CAR', 'Indianapolis': 'IND'
}

# Import log file
LOG_FILE = 'import_log.txt'

def log_decision(message):
    """Log import decisions to file"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(f"[{timestamp}] {message}\n")

def normalize_team(team_name):
    """Convert CSV team name to standard abbreviation"""
    if not team_name or team_name.strip() == '':
        return None
    
    # Already abbreviated
    if len(team_name) <= 3 and team_name.isupper():
        return team_name
    
    # Look up in map
    mapped = TEAM_MAP.get(team_name.strip())
    if not mapped:
        # Unknown team - prompt user
        print(f"\n⚠️  Unknown team name: '{team_name}'")
        print("Enter team abbreviation (e.g., 'DAL', 'PHI') or press Enter to skip:")
        user_input = input("> ").strip().upper()
        if user_input and len(user_input) <= 3:
            TEAM_MAP[team_name.strip()] = user_input
            log_decision(f"Team mapping: '{team_name}' -> '{user_input}' (user confirmed)")
            return user_input
        log_decision(f"Team mapping: '{team_name}' -> SKIPPED (user declined)")
        return None
    return mapped

def load_nfl_schedule(season=2025):
    """Load NFL schedule to get game dates/times"""
    print(f"Loading {season} NFL schedule...")
    # Use the web app data loader (no interactive prompts)
    from app.data_loader import load_data_with_cache_web
    
    schedule_df, _, _ = load_data_with_cache_web(season, use_cache=True)
    return schedule_df

def create_or_get_game(schedule_df, week, home_team, away_team, season=2025):
    """
    Create or retrieve game from database using schedule data
    """
    # Normalize team names
    home = normalize_team(home_team)
    away = normalize_team(away_team)
    
    if not home or not away:
        print(f"⚠️  Could not normalize teams: {away_team} @ {home_team}")
        return None
    
    # Create game_id in nflverse format
    game_id = f"{season}_{int(week):02d}_{away}_{home}"
    
    # Check if already exists
    game = Game.query.filter_by(game_id=game_id).first()
    if game:
        return game
    
    # Find in schedule
    schedule_game = schedule_df.filter(
        (pl.col('season') == season) &
        (pl.col('week') == int(week)) &
        (pl.col('home_team') == home) &
        (pl.col('away_team') == away)
    )
    
    if schedule_game.height == 0:
        # Game not found in schedule - prompt user
        print(f"\n⚠️  Game not found in NFL schedule:")
        print(f"   Week {week}: {away} @ {home}")
        print(f"   Expected game_id: {game_id}")
        print("\nOptions:")
        print("  1. Use expected game_id (create minimal record)")
        print("  2. Enter correct game_id manually")
        print("  3. Skip this game")
        
        choice = input("Select option (1-3): ").strip()
        
        if choice == '1':
            print(f"Creating minimal record for {game_id}")
            log_decision(f"Game created: {game_id} (not in schedule, using expected game_id)")
            game = Game(
                game_id=game_id,
                season=season,
                week=int(week),
                home_team=home,
                away_team=away,
                game_date=date(2025, 9, 1),  # Placeholder
                gameday='Unknown'
            )
            db.session.add(game)
            return game
        elif choice == '2':
            manual_game_id = input("Enter game_id (format: YYYY_WW_AWAY_HOME): ").strip()
            if manual_game_id:
                # Search for manually entered game_id
                manual_schedule = schedule_df.filter(pl.col('game_id') == manual_game_id)
                if manual_schedule.height > 0:
                    print(f"✅ Found game: {manual_game_id}")
                    log_decision(f"Game match: CSV row (Week {week} {away}@{home}) -> {manual_game_id} (user provided)")
                    # Recursively call with corrected teams
                    row = manual_schedule.to_dicts()[0]
                    return create_or_get_game(schedule_df, week, row['home_team'], row['away_team'], season)
                else:
                    print(f"❌ Game_id not found in schedule: {manual_game_id}")
                    log_decision(f"Game match: Invalid game_id provided: {manual_game_id}")
                    return None
        else:
            print("Skipping game")
            log_decision(f"Game skipped: Week {week} {away}@{home} (user chose to skip)")
            return None
    
    # Extract game details
    row = schedule_game.to_dicts()[0]
    
    # Parse gameday date
    gameday_str = row.get('gameday')
    game_date = datetime.strptime(gameday_str, '%Y-%m-%d').date() if gameday_str else date(2025, 9, 1)
    
    # Parse game time
    gametime_str = row.get('gametime')
    game_time = None
    if gametime_str:
        try:
            game_time = datetime.strptime(gametime_str, '%H:%M:%S').time()
        except:
            game_time = None
    
    # Determine gameday name
    weekday = row.get('weekday', 'Unknown')
    
    game = Game(
        game_id=game_id,
        season=season,
        week=int(week),
        gameday=weekday,
        game_date=game_date,
        game_time=game_time,
        home_team=home,
        away_team=away,
        is_standalone=(weekday in ['Thursday', 'Friday', 'Monday'] or 
                      (weekday == 'Saturday' and int(week) >= 16))
    )
    
    db.session.add(game)
    return game

def parse_odds(odds_str):
    """Convert odds string to integer (handle empty/invalid values)"""
    if not odds_str or odds_str.strip() == '':
        return None
    try:
        return int(float(odds_str))
    except:
        return None

def import_csv_picks(csv_path, season=2025):
    """
    Import picks from CSV file for a specific season
    """
    app = create_app()
    
    with app.app_context():
        # Initialize log file
        log_decision("="*60)
        log_decision(f"Starting CSV import from: {csv_path}")
        log_decision(f"Target season: {season}")
        log_decision("="*60)
        
        # Load NFL schedule
        schedule_df = load_nfl_schedule(season)
        
        print(f"\nReading CSV: {csv_path}")
        print(f"Importing for season: {season}")
        print(f"Import log: {LOG_FILE}")
        
        with open(csv_path, 'r', encoding='utf-8') as f:
            # Read raw lines to handle duplicate column names
            lines = f.readlines()
            header = lines[0].strip().split(',')
            
            # Rename duplicate "Odds" columns to be unique
            odds_count = 0
            unique_header = []
            for col in header:
                if col == 'Odds':
                    odds_count += 1
                    if odds_count == 1:
                        unique_header.append('1st TD Odds')
                    elif odds_count == 2:
                        unique_header.append('ATTS Odds')
                    else:
                        unique_header.append(f'Odds_{odds_count}')
                else:
                    unique_header.append(col)
            
            # Create CSV reader with fixed headers
            import io
            fixed_csv = io.StringIO('\n'.join([','.join(unique_header)] + lines[1:]))
            reader = csv.DictReader(fixed_csv)
            
            picks_created = 0
            games_created = 0
            
            for row_num, row in enumerate(reader, start=2):  # Start at 2 (header is row 1)
                # Skip empty rows or summary rows
                week = row.get('Week', '').strip()
                if not week or week == '' or week in ['WC', 'DIV', 'CHAMP', 'SB'] or not week.isdigit():
                    continue
                
                picker = row.get('Picker', '').strip()
                if not picker or picker == '':
                    continue
                
                visitor = row.get('Vistor', '').strip()  # Note: CSV has typo "Vistor"
                home = row.get('Home', '').strip()
                player = row.get('Player', '').strip()
                
                if not player or player == '':
                    continue  # Future week with no pick yet
                
                # Validate player name format
                if len(player) < 2:
                    print(f"\n⚠️  Suspicious player name on row {row_num}: '{player}'")
                    print(f"   Week {week}: {visitor} @ {home}")
                    print(f"   Picker: {picker}")
                    confirm = input("Use this player name anyway? (y/n): ").strip().lower()
                    if confirm != 'y':
                        corrected = input("Enter corrected player name (or press Enter to skip): ").strip()
                        if corrected:
                            log_decision(f"Player name: Row {row_num} '{player}' -> '{corrected}' (user corrected)")
                            player = corrected
                        else:
                            log_decision(f"Player name: Row {row_num} '{player}' SKIPPED (user declined)")
                            continue
                    else:
                        log_decision(f"Player name: Row {row_num} '{player}' ACCEPTED (user confirmed)")
                
                # Get or create user
                user = User.query.filter_by(username=picker).first()
                if not user:
                    print(f"⚠️  User not found: {picker} (row {row_num})")
                    continue
                
                # Get or create game
                game = create_or_get_game(schedule_df, week, home, visitor, season=season)
                if not game:
                    print(f"⚠️  Could not create game for row {row_num}")
                    continue
                
                if game.id is None:
                    db.session.flush()  # Get game.id for new games
                    games_created += 1
                
                # Parse FTD pick
                ftd_odds_str = row.get('1st TD Odds', '').strip()
                ftd_odds = parse_odds(ftd_odds_str)
                
                if ftd_odds:
                    result = row.get('Result', 'Pending').strip()
                    if result == '':
                        result = 'Pending'
                    elif result not in ['W', 'L', 'Pending', 'Push']:
                        result = 'Pending'
                    
                    # Check if pick already exists
                    existing_pick = Pick.query.filter_by(
                        user_id=user.id,
                        game_id=game.id,
                        pick_type='FTD'
                    ).first()
                    
                    if not existing_pick:
                        ftd_pick = Pick(
                            user_id=user.id,
                            game_id=game.id,
                            pick_type='FTD',
                            player_name=player,
                            player_position=row.get('Position', '').strip(),
                            odds=ftd_odds,
                            stake=1.0,
                            result=result,
                            submitted_at=datetime.utcnow()
                        )
                        
                        # Calculate payout
                        if result == 'W':
                            ftd_pick.payout = ftd_pick.calculate_payout()
                            ftd_pick.graded_at = datetime.utcnow()
                        elif result == 'L':
                            ftd_pick.payout = -1.0
                            ftd_pick.graded_at = datetime.utcnow()
                        
                        db.session.add(ftd_pick)
                        picks_created += 1
                
                # Parse ATTS pick
                atts = row.get('ATTS', '').strip()
                if atts and atts.upper() in ['YES', 'Y']:
                    atts_odds_str = row.get('ATTS Odds', '').strip()
                    atts_odds = parse_odds(atts_odds_str)
                    
                    if atts_odds:
                        # ATTS result tracking would be separate, default to Pending
                        existing_atts = Pick.query.filter_by(
                            user_id=user.id,
                            game_id=game.id,
                            pick_type='ATTS'
                        ).first()
                        
                        if not existing_atts:
                            atts_pick = Pick(
                                user_id=user.id,
                                game_id=game.id,
                                pick_type='ATTS',
                                player_name=player,
                                player_position=row.get('Position', '').strip(),
                                odds=atts_odds,
                                stake=1.0,
                                result='Pending',  # ATTS results need separate grading
                                submitted_at=datetime.utcnow()
                            )
                            db.session.add(atts_pick)
                            picks_created += 1
            
            # Commit all changes
            db.session.commit()
            
            print(f"\n✅ Import complete!")
            print(f"   - Created {games_created} games")
            print(f"   - Created {picks_created} picks")
            
            # Show summary
            total_users = User.query.count()
            total_games = Game.query.count()
            total_picks = Pick.query.count()
            
            print(f"\n📊 Database Summary:")
            print(f"   - Total Users: {total_users}")
            print(f"   - Total Games: {total_games}")
            print(f"   - Total Picks: {total_picks}")
            
            # Log final summary
            log_decision("="*60)
            log_decision(f"Import complete: {games_created} games, {picks_created} picks created")
            log_decision(f"Database totals: {total_users} users, {total_games} games, {total_picks} picks")
            log_decision("="*60)

if __name__ == '__main__':
    import sys
    
    # Check for command line arguments
    if len(sys.argv) > 1:
        csv_file = sys.argv[1]
    else:
        csv_file = r'c:\Users\akurs\Desktop\Vibe Coder\main\First TD - 2025 (1).csv'
    
    # Prompt for season
    season_input = input("Enter season year (default 2025): ").strip()
    season = int(season_input) if season_input else 2025
    
    import_csv_picks(csv_file, season=season)
