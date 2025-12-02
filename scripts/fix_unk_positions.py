"""
Script to fix UNK positions in the database by using roster fuzzy matching.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from league_webapp.app import create_app
from league_webapp.app.models import Pick, db
from league_webapp.app.data_loader import load_data_with_cache_web
from league_webapp.app.fuzzy_matcher import NameMatcher

def fix_unk_positions():
    app = create_app()
    
    with app.app_context():
        # Get all picks with UNK position
        unk_picks = Pick.query.filter_by(player_position='UNK').all()
        
        print(f'Found {len(unk_picks)} picks with UNK position')
        
        if not unk_picks:
            print('No UNK positions to fix!')
            return
        
        # Group by season to load roster data once per season
        picks_by_season = {}
        for pick in unk_picks:
            season = pick.game.season
            if season not in picks_by_season:
                picks_by_season[season] = []
            picks_by_season[season].append(pick)
        
        updated_count = 0
        
        for season, picks in picks_by_season.items():
            print(f'\nProcessing {len(picks)} picks from season {season}...')
            
            try:
                _, _, roster_df = load_data_with_cache_web(season, use_cache=True)
                matcher = NameMatcher()
                
                for pick in picks:
                    try:
                        # Filter roster to game teams
                        game_roster = roster_df.filter(
                            (roster_df['team'] == pick.game.home_team) |
                            (roster_df['team'] == pick.game.away_team)
                        )
                        
                        if len(game_roster) == 0:
                            print(f'  No roster data for game {pick.game_id}')
                            continue
                        
                        # Build candidate names
                        full_names = game_roster['full_name'].to_list() if 'full_name' in game_roster.columns else []
                        football_names = game_roster['football_name'].to_list() if 'football_name' in game_roster.columns else []
                        first_names = game_roster['first_name'].to_list() if 'first_name' in game_roster.columns else []
                        last_names = game_roster['last_name'].to_list() if 'last_name' in game_roster.columns else []
                        positions = game_roster['position'].to_list() if 'position' in game_roster.columns else []
                        
                        candidate_names = []
                        candidate_names.extend(full_names)
                        candidate_names.extend([fn for fn in football_names if fn])
                        candidate_names.extend([f"{fn} {ln}" for fn, ln in zip(first_names, last_names) if fn and ln])
                        candidate_names.extend([ln for ln in last_names if ln])
                        
                        # Deduplicate
                        seen = set()
                        ordered_candidates = []
                        for n in candidate_names:
                            nl = n.lower()
                            if nl not in seen:
                                seen.add(nl)
                                ordered_candidates.append(n)
                        
                        # Try to match
                        match_result = matcher.find_best_match(pick.player_name.strip(), ordered_candidates, min_score=0.60)
                        
                        if match_result and match_result['score'] >= 0.70:
                            matched_name = match_result['matched_name']
                            
                            # Find the position for this matched name
                            position = None
                            for i, full in enumerate(full_names):
                                if full == matched_name and i < len(positions):
                                    position = positions[i]
                                    break
                            
                            # Check football_names if not found
                            if not position:
                                for i, fn in enumerate(football_names):
                                    if fn == matched_name and i < len(positions):
                                        position = positions[i]
                                        break
                            
                            # Check last_names if still not found
                            if not position:
                                for i, ln in enumerate(last_names):
                                    if ln == matched_name and i < len(positions):
                                        position = positions[i]
                                        break
                            
                            if position:
                                # Map position to standard codes
                                if position in ['QB', 'RB', 'WR', 'TE']:
                                    pick.player_position = position
                                    print(f'  ✓ Pick {pick.id}: {pick.player_name} -> {matched_name} ({position})')
                                    updated_count += 1
                                elif position in ['FB', 'HB']:
                                    pick.player_position = 'RB'
                                    print(f'  ✓ Pick {pick.id}: {pick.player_name} -> {matched_name} ({position} -> RB)')
                                    updated_count += 1
                                else:
                                    print(f'  ✗ Pick {pick.id}: {pick.player_name} -> {matched_name} (invalid position: {position})')
                            else:
                                print(f'  ✗ Pick {pick.id}: {pick.player_name} -> matched to {matched_name} but no position found')
                        else:
                            print(f'  ✗ Pick {pick.id}: {pick.player_name} -> no good match (best score: {match_result["score"] if match_result else 0:.2f})')
                    
                    except Exception as e:
                        print(f'  Error processing pick {pick.id} ({pick.player_name}): {e}')
                        
            except Exception as e:
                print(f'Error loading roster data for season {season}: {e}')
        
        if updated_count > 0:
            print(f'\n\nCommitting {updated_count} position updates...')
            db.session.commit()
            print('✓ Done!')
        else:
            print('\nNo positions were updated.')

if __name__ == '__main__':
    fix_unk_positions()
