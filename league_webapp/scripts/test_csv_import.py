"""
Script to test CSV import logic for picks, bypassing the webapp UI.
Usage: Run from project root or scripts folder.
"""

import os
import sys
import csv
# Ensure parent directory is in sys.path for app imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from flask import Flask
from app import db
from app.models import User, Game, Pick as PickModel
from app.fuzzy_matcher import NameMatcher
from app.data_loader import load_data_with_cache_web

# --- CONFIG ---
CSV_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../archive/First TD - 2025 (2).csv'))
SEASON = 2025

# --- FLASK APP CONTEXT ---
from app import create_app
app = create_app()

# --- MAIN LOGIC ---
def main():
    # Team name to code mapping
    team_name_map = {
        'DALLAS': 'DAL', 'PHILADELPHIA': 'PHI', 'KANSAS CITY': 'KC', 'LA CHARGERS': 'LAC',
        'BALTIMORE': 'BAL', 'BUFFALO': 'BUF', 'MINNESOTA': 'MIN', 'CHICAGO': 'CHI',
        'WASHINGTON': 'WAS', 'GREEN BAY': 'GB', 'ATLANTA': 'ATL', 'TAMPA BAY': 'TB',
        'HOUSTON': 'HOU', 'LAS VEGAS': 'LV', 'MIAMI': 'MIA', 'NY GIANTS': 'NYG',
        'DETROIT': 'DET', 'SEATTLE': 'SEA', 'ARIZONA': 'ARI', 'NY JETS': 'NYJ',
        'CINCINNATI': 'CIN', 'DENVER': 'DEN', 'SAN FRAN': 'SF', 'LA RAMS': 'LAR',
        'NEW ENGLAND': 'NE', 'JACKSONVILLE': 'JAX', 'PITTSBURGH': 'PIT', 'CAROLINA': 'CAR',
        'INDIANAPOLIS': 'IND'
    }

    def to_game_id(season, week, away, home):
        week_str = f"{int(week):02d}"
        away_code = team_name_map.get(away.strip().upper(), away.strip().upper()[:3])
        home_code = team_name_map.get(home.strip().upper(), home.strip().upper()[:3])
        return f"{season}_{week_str}_{away_code}_{home_code}"

    with app.app_context():
        # Load all games for season for game_id lookup
        games = Game.query.filter_by(season=SEASON).all()
        game_lookup = {}
        for g in games:
            key = (g.week, g.game_date.strftime('%Y-%m-%d') if g.game_date else '', g.away_team, g.home_team)
            game_lookup[key] = g.id

        # Load all users for user lookup
        users = {u.username: u.id for u in User.query.all()}

        # Fuzzy matcher for player names
        matcher = NameMatcher()
        # Get all possible scorer names from picks table (or roster if available)
        from sqlalchemy import text
        scorer_names = [row[0] for row in db.session.execute(text('SELECT DISTINCT player_name FROM picks'))]

        # Read CSV and auto-map columns
        imported = 0
        errors = []
        with open(CSV_PATH, newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            # Ensure header is read
            header = reader.fieldnames
            if header is None:
                # Try to read first row to populate fieldnames
                try:
                    first_row = next(reader)
                    header = reader.fieldnames
                except StopIteration:
                    print("CSV file is empty.")
                    return
            if header is None:
                print("CSV header could not be read. Please check the file format.")
                return
            # Auto-map columns using fuzzy matching
            expected = {
                'week': ['Week'],
                'gameday': ['Gameday'],
                'away': ['Vistor', 'Visitor'],
                'home': ['Home'],
                'picker': ['Picker'],
                'pick_type': ['pick_type', 'type', 'bet_type'],
                'player_name': ['Player'],
                'player_position': ['Position'],
                'odds_ftd': ['1st TD Odds'],
                'odds_atts': ['ATTS Odds'],
            }
            col_map = {}
            for key, options in expected.items():
                for col in header:
                    norm_col = col.strip().lower().replace(' ', '').replace('_', '')
                    for opt in options:
                        norm_opt = opt.strip().lower().replace(' ', '').replace('_', '')
                        if norm_col == norm_opt:
                            col_map[key] = col
                            break
                    if key in col_map:
                        break
            # Fallback: if not found, use first matching substring (but only if not already mapped and not a conflicting type)
            for key, options in expected.items():
                if key not in col_map:
                    for col in header:
                        for opt in options:
                            # Only allow substring match if column is not already mapped and not a conflicting type
                            norm_col = col.strip().lower().replace(' ', '').replace('_', '')
                            norm_opt = opt.strip().lower().replace(' ', '').replace('_', '')
                            if norm_opt in norm_col:
                                col_map[key] = col
                                break
                        if key in col_map:
                            break

            # Print CSV header and first 3 rows for debugging
            print(f"CSV Header: {reader.fieldnames}")
            sample_rows = []
            for i, row in enumerate(reader):
                if i < 3:
                    sample_rows.append(row)
            print(f"Sample CSV rows: {sample_rows}")
            # Reset reader for actual import
            csvfile.seek(0)
            reader = csv.DictReader(csvfile)
            # Print number of games fetched and a sample game record
            print(f"Number of games fetched: {len(game_lookup)}")
            if game_lookup:
                print(f"Sample game key: {list(game_lookup.keys())[0]}, Sample game_id: {list(game_lookup.values())[0]}")
            else:
                print("No games found in database. Game table may be empty or query is incorrect.")
            # Build normalized game_lookup for matching
            norm_game_lookup = {}
            for gk, gid in game_lookup.items():
                norm_gk = (gk[0], gk[1].strip(), gk[2].strip().upper(), gk[3].strip().upper())
                norm_game_lookup[norm_gk] = gid
            print(f"Available normalized game keys: {list(norm_game_lookup.keys())[:10]}")
            # Actual import loop
            for row in reader:
                # Only process Week 1
                week_val = row.get(col_map.get('week', ''), 0)
                try:
                    week_num = int(week_val)
                except Exception:
                    week_num = 0
                if week_num != 1:
                    continue
                # --- Use mapped columns ---
                week_val = row.get(col_map.get('week', ''), 0)
                # Handle playoff week codes
                playoff_map = {'WC': 18, 'DIV': 19, 'CHAMP': 20, 'SB': 21}
                try:
                    week = int(week_val)
                except Exception:
                    week = playoff_map.get(str(week_val).strip().upper(), 0)
                    if week == 0:
                        errors.append(f"Invalid week value: {week_val}")
                gameday = row.get(col_map.get('gameday', ''), '')
                away = row.get(col_map.get('away', ''), '')
                if not away:
                    away = row.get('Visitor', '')
                home = row.get(col_map.get('home', ''), '')
                picker = row.get(col_map.get('picker', ''), '').strip()
                player_name = row.get(col_map.get('player_name', ''), '').strip()
                player_position = row.get(col_map.get('player_position', ''), '').strip()
                # Pick type logic
                pick_type_val = row.get(col_map.get('pick_type', ''), '').strip().upper()
                if 'ATTD' in pick_type_val or 'ATTS' in pick_type_val:
                    pick_type = 'ATTD'
                else:
                    pick_type = 'FTD'
                # Odds logic
                odds_val_ftd = row.get(col_map.get('odds_ftd', ''), '')
                odds_val_atts = row.get(col_map.get('odds_atts', ''), '')
                try:
                    odds = int(odds_val_ftd) if pick_type == 'FTD' else int(odds_val_atts)
                except Exception:
                    odds = 0
                    errors.append(f"Invalid odds value: {odds_val_ftd if pick_type == 'FTD' else odds_val_atts}")
                stake = 1.0

                # --- Generate game_id ---
                # Convert to nflverse game_id format
                season = 2025  # You can make this dynamic if needed
                game_id_str = to_game_id(season, week, away, home)
                # Lookup by game_id string
                game_id = None
                for gk, gid in game_lookup.items():
                    if gid == game_id_str or gk == game_id_str:
                        game_id = gid
                        break
                if not game_id:
                    errors.append(f"No game_id for {game_id_str}")
                    if len(errors) < 5:
                        print(f"Sample available game keys: {list(game_lookup.values())[:5]}")
                    continue

                # --- Fuzzy match player name ---
                match_result = matcher.find_best_match(player_name, scorer_names)
                if match_result and match_result['matched_name']:
                    matched_name = match_result['matched_name']
                else:
                    errors.append(f"No match for player: {player_name}")
                    continue

                # --- User lookup ---
                user_id = users.get(picker)
                if not user_id:
                    # Create new user with default values
                    from app.models import User as UserModel
                    new_user = UserModel(username=picker, email=f"{picker}@example.com")
                    new_user.set_password("defaultpassword")
                    db.session.add(new_user)
                    db.session.commit()
                    user_id = new_user.id
                    users[picker] = user_id
                    print(f"Created new user: {picker} (id={user_id})")

                # --- Insert pick ---
                pick = PickModel(user_id, game_id, pick_type, matched_name, player_position, odds, stake)
                pick.result = 'Pending'
                pick.payout = 0.0
                db.session.add(pick)
                imported += 1

            db.session.commit()
        print(f"Imported {imported} picks.")
        if errors:
            print("Errors:")
            for e in errors:
                print(e)

if __name__ == '__main__':
    main()
