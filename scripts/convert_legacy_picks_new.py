"""
Convert legacy First TD CSV format to database picks
Usage: python convert_legacy_picks_new.py <input_file>

Creates picks directly in the database:
- Every row creates 2 picks: FTD + ATTS
- Uses game rosters to enrich player names and get positions
- FTD odds from "1st TD Odds" column (required)
- ATTS odds from "ATTS Odds" column (optional, None if missing)
"""
import csv
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from league_webapp.app import create_app, db
from league_webapp.app.models import User, Game, Pick
from league_webapp.app.data_loader import load_data_with_cache_web
from league_webapp.app.fuzzy_matcher import NameMatcher


def normalize_team_name(team_name):
    """Normalize team names to match database format"""
    team_map = {
        'kansas city': 'KC',
        'la chargers': 'LAC',
        'los angeles chargers': 'LAC',
        'green bay': 'GB',
        'tampa bay': 'TB',
        'new england': 'NE',
        'las vegas': 'LV',
        'san fran': 'SF',
        'san francisco': 'SF',
        'la rams': 'LA',
        'los angeles rams': 'LA',
        'ny giants': 'NYG',
        'new york giants': 'NYG',
        'ny jets': 'NYJ',
        'new york jets': 'NYJ',
        'philadelphia': 'PHI',
        'pittsburgh': 'PIT',
        'seattle': 'SEA',
        'arizona': 'ARI',
        'dallas': 'DAL',
        'miami': 'MIA',
        'baltimore': 'BAL',
        'buffalo': 'BUF',
        'cincinnati': 'CIN',
        'denver': 'DEN',
        'houston': 'HOU',
        'atlanta': 'ATL',
        'minnesota': 'MIN',
        'chicago': 'CHI',
        'washington': 'WAS',
        'detriot': 'DET',  # Note: typo in CSV
        'detroit': 'DET',
        'jacksonville': 'JAX',
        'carolina': 'CAR',
        'cleveland': 'CLE',
        'indianapolis': 'IND',
        'tennessee': 'TEN',
        'new orleans': 'NO'
    }
    return team_map.get(team_name.strip().lower(), team_name.upper())


def parse_odds(odds_str):
    """Parse odds string to integer (e.g., '900' -> 900, '+900' -> 900, '-110' -> -110)"""
    if not odds_str or odds_str.strip() == '':
        return None
    odds_str = odds_str.strip().replace('+', '')
    try:
        return int(odds_str)
    except ValueError:
        return None


def get_player_info_from_roster(player_name, game, roster_df, matcher):
    """
    Get enriched player name and position from game rosters.
    Returns (full_name, position) or (original_name, 'UNK') if not found.
    """
    try:
        # Filter roster to game teams only (don't filter by week - roster 'week' represents transactions, not game availability)
        game_roster = roster_df.filter(
            (roster_df['team'] == game.home_team) |
            (roster_df['team'] == game.away_team)
        )
        
        if len(game_roster) == 0:
            return player_name, 'UNK'
        
        # Build candidate names with position mapping
        full_names = game_roster['full_name'].to_list() if 'full_name' in game_roster.columns else []
        football_names = game_roster['football_name'].to_list() if 'football_name' in game_roster.columns else []
        first_names = game_roster['first_name'].to_list() if 'first_name' in game_roster.columns else []
        last_names = game_roster['last_name'].to_list() if 'last_name' in game_roster.columns else []
        positions = game_roster['position'].to_list() if 'position' in game_roster.columns else []
        
        # Build name-to-position mapping
        name_to_position = {}
        for i in range(len(positions)):
            if i < len(full_names) and full_names[i]:
                name_to_position[full_names[i]] = positions[i]
            if i < len(football_names) and football_names[i]:
                name_to_position[football_names[i]] = positions[i]
            if i < len(first_names) and i < len(last_names) and first_names[i] and last_names[i]:
                name_to_position[f"{first_names[i]} {last_names[i]}"] = positions[i]
            if i < len(last_names) and last_names[i]:
                name_to_position[last_names[i]] = positions[i]
        
        # Get unique candidate names
        candidate_names = list(name_to_position.keys())
        
        # Try to match
        match_result = matcher.find_best_match(player_name.strip(), candidate_names, min_score=0.60)
        
        if match_result and match_result['score'] >= 0.70:
            matched_name = match_result['matched_name']
            position = name_to_position.get(matched_name)
            
            if position:
                # Map position to standard codes
                if position in ['QB', 'RB', 'WR', 'TE']:
                    return matched_name, position
                elif position in ['FB', 'HB']:
                    return matched_name, 'RB'
        
        return player_name, 'UNK'
    
    except Exception as e:
        print(f"  Error enriching player '{player_name}': {e}")
        return player_name, 'UNK'


def convert_csv(input_file, season=2025):
    """Convert legacy CSV and create picks in database"""
    app = create_app()
    
    with app.app_context():
        # Load users
        users = User.query.all()
        user_map = {}
        for user in users:
            if user.display_name:
                user_map[user.display_name.strip().lower()] = user.id
            user_map[user.username.strip().lower()] = user.id
        
        print(f"Loaded {len(user_map)} users")
        
        # Load games
        games = Game.query.filter_by(season=season).all()
        game_map = {}
        for game in games:
            key = (game.week, game.away_team, game.home_team)
            game_map[key] = game
        
        print(f"Loaded {len(game_map)} games for season {season}")
        
        # Load roster data once
        print(f"Loading roster data for season {season}...")
        _, _, roster_df = load_data_with_cache_web(season, use_cache=True)
        matcher = NameMatcher()
        print(f"Roster data loaded")
        
        picks_created = []
        skipped_rows = []
        
        with open(input_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            for row_num, row in enumerate(reader, start=2):
                # Skip empty or summary rows
                if not row.get('Week') or not row['Week'].strip().isdigit():
                    continue
                
                week = int(row['Week'])
                picker = row['Picker'].strip()
                visitor = normalize_team_name(row['Vistor'])  # Note: CSV has typo "Vistor"
                home = normalize_team_name(row['Home'])
                player = row['Player'].strip()
                ftd_odds_str = row['1st TD Odds'].strip()
                atts_odds_str = row.get('ATTS Odds', '').strip()
                
                # Skip if no player selected
                if not player:
                    continue
                
                # Get user ID
                user_id = user_map.get(picker.lower())
                if not user_id:
                    skipped_rows.append(f"Row {row_num}: Unknown picker '{picker}'")
                    continue
                
                # Get game
                game_key = (week, visitor, home)
                game = game_map.get(game_key)
                if not game:
                    skipped_rows.append(f"Row {row_num}: Game not found - Week {week}, {visitor} @ {home}")
                    continue
                
                # Parse odds
                ftd_odds = parse_odds(ftd_odds_str)
                atts_odds = parse_odds(atts_odds_str)
                
                if not ftd_odds:
                    skipped_rows.append(f"Row {row_num}: Missing FTD odds for {picker} - {player}")
                    continue
                
                # Get enriched player info from roster
                enriched_name, position = get_player_info_from_roster(player, game, roster_df, matcher)
                
                print(f"Row {row_num}: {picker} - {player} -> {enriched_name} ({position})")
                
                # Create FTD pick
                ftd_pick = Pick(
                    user_id=user_id,
                    game_id=game.id,
                    pick_type='FTD',
                    player_name=enriched_name,
                    player_position=position,
                    odds=ftd_odds,
                    stake=1.00,
                    result='Pending',
                    payout=0.0
                )
                db.session.add(ftd_pick)
                picks_created.append(f"FTD: {picker} - {enriched_name} @ {ftd_odds}")
                
                # Create ATTS pick (always, use +100 as default if odds missing)
                atts_odds_value = atts_odds if atts_odds is not None else 100
                atts_pick = Pick(
                    user_id=user_id,
                    game_id=game.id,
                    pick_type='ATTS',
                    player_name=enriched_name,
                    player_position=position,
                    odds=atts_odds_value,
                    stake=1.00,
                    result='Pending',
                    payout=0.0
                )
                db.session.add(atts_pick)
                odds_display = f"{atts_odds}" if atts_odds is not None else "100 (default)"
                picks_created.append(f"ATTS: {picker} - {enriched_name} @ {odds_display}")
        
        # Commit all picks
        print(f"\n{'='*60}")
        print(f"Creating {len(picks_created)} picks in database...")
        db.session.commit()
        print(f"Successfully created {len(picks_created)} picks")
        
        if skipped_rows:
            print(f"\nSkipped {len(skipped_rows)} rows:")
            for skip in skipped_rows[:10]:
                print(f"  {skip}")
            if len(skipped_rows) > 10:
                print(f"  ... and {len(skipped_rows) - 10} more")


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: python convert_legacy_picks_new.py <input_file>")
        print("Example: python convert_legacy_picks_new.py '../First TD - 2025 (2).csv'")
        sys.exit(1)
    
    input_file = sys.argv[1]
    
    if not os.path.exists(input_file):
        print(f"Error: Input file '{input_file}' not found")
        sys.exit(1)
    
    convert_csv(input_file)
