"""
Convert legacy First TD CSV format to webapp import format
Usage: python convert_legacy_picks.py <input_file> <output_file>
"""
import csv
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'league_webapp'))

from app import create_app, db
from app.models import User, Game

def get_user_id_map():
    """Create mapping of picker names to user IDs"""
    app = create_app()
    with app.app_context():
        users = User.query.all()
        # Try to match display names or usernames
        user_map = {}
        for user in users:
            # Add variations of names
            if user.display_name:
                user_map[user.display_name.strip().lower()] = user.id
            user_map[user.username.strip().lower()] = user.id
        return user_map

def get_game_id_map(season=2025):
    """Create mapping of (week, away_team, home_team) to game IDs"""
    app = create_app()
    with app.app_context():
        games = Game.query.filter_by(season=season).all()
        game_map = {}
        for game in games:
            key = (game.week, game.away_team, game.home_team)
            game_map[key] = game.id
        return game_map

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
        'la rams': 'LA',  # Changed from LAR to LA
        'los angeles rams': 'LA',  # Changed from LAR to LA
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

def convert_csv(input_file, output_file):
    """Convert legacy CSV to webapp import format"""
    user_map = get_user_id_map()
    game_map = get_game_id_map()
    
    print(f"Loaded {len(user_map)} users")
    print(f"Loaded {len(game_map)} games")
    print(f"\nUser mapping: {user_map}")
    
    output_rows = []
    skipped_rows = []
    
    with open(input_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        
        for row_num, row in enumerate(reader, start=2):
            # Skip empty or summary rows
            if not row.get('Week') or not row['Week'].isdigit():
                continue
            
            week = int(row['Week'])
            picker = row['Picker'].strip()
            visitor = normalize_team_name(row['Vistor'])  # Note: CSV has typo "Vistor"
            home = normalize_team_name(row['Home'])
            player = row['Player'].strip()
            ftd_odds_str = row['1st TD Odds'].strip()
            atts_choice = row.get('ATTS', '').strip().upper()
            atts_odds_str = row.get('ATTS Odds', '').strip()
            
            # Skip if no player selected
            if not player:
                continue
            
            # Get user ID
            user_id = user_map.get(picker.lower())
            if not user_id:
                skipped_rows.append(f"Row {row_num}: Unknown picker '{picker}'")
                continue
            
            # Get game ID
            game_key = (week, visitor, home)
            game_id = game_map.get(game_key)
            if not game_id:
                skipped_rows.append(f"Row {row_num}: Game not found - Week {week}, {visitor} @ {home}")
                continue
            
            # Add FTD pick if odds exist
            ftd_odds = parse_odds(ftd_odds_str)
            if ftd_odds:
                output_rows.append({
                    'user_id': user_id,
                    'game_id': game_id,
                    'pick_type': 'FTD',
                    'player_name': player,
                    'odds': ftd_odds,
                    'stake': '1.00'
                })
            
            # Add ATTS pick if chosen
            if atts_choice == 'YES':
                atts_odds = parse_odds(atts_odds_str)
                if atts_odds:
                    output_rows.append({
                        'user_id': user_id,
                        'game_id': game_id,
                        'pick_type': 'ATTS',
                        'player_name': player,
                        'odds': atts_odds,
                        'stake': '1.00'
                    })
    
    # Write output CSV
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        fieldnames = ['user_id', 'game_id', 'pick_type', 'player_name', 'odds', 'stake']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(output_rows)
    
    print(f"\n✅ Successfully converted {len(output_rows)} picks to {output_file}")
    
    if skipped_rows:
        print(f"\n⚠️  Skipped {len(skipped_rows)} rows:")
        for skip in skipped_rows[:10]:  # Show first 10
            print(f"  {skip}")
        if len(skipped_rows) > 10:
            print(f"  ... and {len(skipped_rows) - 10} more")

if __name__ == '__main__':
    if len(sys.argv) != 3:
        print("Usage: python convert_legacy_picks.py <input_file> <output_file>")
        print("Example: python convert_legacy_picks.py 'First TD - 2025 (2).csv' picks_import.csv")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    
    if not os.path.exists(input_file):
        print(f"Error: Input file '{input_file}' not found")
        sys.exit(1)
    
    convert_csv(input_file, output_file)
