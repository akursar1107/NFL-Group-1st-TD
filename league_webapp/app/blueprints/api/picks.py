"""
Picks API endpoints - Create, read, update, delete picks
"""
from flask import request, jsonify
from marshmallow import ValidationError
from . import api_bp
from ...models import User, Game, Pick as PickModel
from ... import db
from ...validators import PickCreateSchema, PickUpdateSchema
from ...data_loader import load_data_with_cache_web
from ...fuzzy_matcher import NameMatcher


def get_player_position(player_name: str, game: Game) -> str:
    """
    Use fuzzy matching to find player position from roster data.
    
    Args:
        player_name: Name of the player
        game: Game object to get season and teams
    
    Returns:
        Position code (QB, RB, WR, TE) or 'UNK' if not found
    """
    try:
        # Load roster data for the season
        _, _, roster_df = load_data_with_cache_web(game.season, use_cache=True)
        
        # Filter to only players from the game's teams (don't filter by week - roster 'week' represents transactions)
        game_rosters = roster_df.filter(
            (roster_df['team'] == game.home_team) | 
            (roster_df['team'] == game.away_team)
        )
        
        if len(game_rosters) == 0:
            return 'UNK'
        
        # Get player names and positions
        # Roster schema uses full_name (and optionally football_name), not player_name
        base_cols = ['full_name', 'position']
        players_raw = game_rosters.select(base_cols).to_dicts()
        # Build candidate names list (full_name + any football_name alias + first_last + last_name)
        candidate_names = []
        # Extract additional columns safely
        first_names = game_rosters['first_name'].to_list() if 'first_name' in game_rosters.columns else []
        last_names = game_rosters['last_name'].to_list() if 'last_name' in game_rosters.columns else []
        football_names = game_rosters['football_name'].to_list() if 'football_name' in game_rosters.columns else []
        full_names = [p['full_name'] for p in players_raw]
        candidate_names.extend(full_names)
        candidate_names.extend([fn for fn in football_names if fn])
        candidate_names.extend([f"{fn} {ln}" for fn, ln in zip(first_names, last_names) if fn and ln])
        candidate_names.extend([ln for ln in last_names if ln])
        # Deduplicate while preserving order
        seen = set()
        ordered_candidates = []
        for n in candidate_names:
            nl = n.lower()
            if nl not in seen:
                seen.add(nl)
                ordered_candidates.append(n)
        
        # Use fuzzy matcher to find best match
        matcher = NameMatcher()
        match_result = matcher.find_best_match(player_name, ordered_candidates, min_score=0.70)
        
        if match_result and match_result['auto_accept']:
            # Find the position for the matched player via full_name fallback
            matched_player = next((p for p in players_raw if p['full_name'] == match_result['matched_name']), None)
            if matched_player and matched_player.get('position'):
                position = matched_player['position']
                # Map position to our standard codes
                if position in ['QB', 'RB', 'WR', 'TE']:
                    return position
                elif position in ['FB', 'HB']:
                    return 'RB'
                else:
                    return 'UNK'
        
        return 'UNK'
    except Exception as e:
        print(f"Error getting player position: {e}")
        return 'UNK'


@api_bp.route('/picks', methods=['GET'])
def get_picks():
    season = request.args.get('season', 2025, type=int)
    week = request.args.get('week', type=int)
    user_id = request.args.get('user_id', type=int)
    include_full_names = request.args.get('include_full_names', 'false').lower() == 'true'
    
    try:
        query = PickModel.query.join(Game)
        
        if season:
            query = query.filter(Game.season == season)
        if week:
            query = query.filter(Game.week == week)
        if user_id:
            query = query.filter(PickModel.user_id == user_id)
        
        picks = query.order_by(Game.week, Game.game_date, Game.game_time).all()
        
        # Load roster dataframe once if we need to enrich names
        roster_df = None
        matcher = None
        if include_full_names:
            try:
                _, _, roster_df = load_data_with_cache_web(season, use_cache=True)
                matcher = NameMatcher()
            except Exception as e:
                print(f"Failed loading roster data for full name enrichment: {e}")
                roster_df = None
                matcher = None
                include_full_names = False  # disable enrichment gracefully
        
        picks_data = []
        for pick in picks:
            full_player_name = pick.player_name
            # Attempt enrichment only if requested and we have roster data
            if include_full_names and roster_df is not None and matcher is not None:
                try:
                    # Filter roster to game teams (don't filter by week - roster 'week' represents transactions)
                    game_roster = roster_df.filter(
                        (roster_df['team'] == pick.game.home_team) |
                        (roster_df['team'] == pick.game.away_team)
                    )
                    if len(game_roster) > 0:
                        # Build candidate list similar to get_player_position
                        full_names = game_roster['full_name'].to_list() if 'full_name' in game_roster.columns else []
                        football_names = game_roster['football_name'].to_list() if 'football_name' in game_roster.columns else []
                        first_names = game_roster['first_name'].to_list() if 'first_name' in game_roster.columns else []
                        last_names = game_roster['last_name'].to_list() if 'last_name' in game_roster.columns else []
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

                        original = pick.player_name.strip()
                        tokens = original.replace('.', '').split()
                        lowered_original = original.lower()

                        # 1. Exact (case-insensitive) full-name match
                        exact_map = {n.lower(): n for n in full_names}
                        if lowered_original in exact_map:
                            full_player_name = exact_map[lowered_original]
                        else:
                            # 2. Single-word last name match (unique)
                            if len(tokens) == 1:
                                matching_indices = [i for i, ln in enumerate(last_names) if ln and ln.lower() == tokens[0].lower()]
                                if len(matching_indices) == 1:
                                    full_player_name = full_names[matching_indices[0]]
                                else:
                                    # Single-word unique first name match
                                    first_matches = [i for i, fn in enumerate(first_names) if fn and fn.lower().replace('.', '') == tokens[0].lower()]
                                    if len(first_matches) == 1:
                                        idx = first_matches[0]
                                        # If the stored full_name is just the first name, synthesize first + last
                                        if idx < len(last_names) and full_names[idx] and len(full_names[idx].split()) == 1 and last_names[idx]:
                                            full_player_name = f"{full_names[idx]} {last_names[idx]}"
                                        else:
                                            full_player_name = full_names[idx]
                                    else:
                                        # Fallback fuzzy
                                        match_result = matcher.find_best_match(original, ordered_candidates, min_score=0.60)
                                        if match_result and match_result['score'] >= 0.70:
                                            full_player_name = match_result['matched_name']
                            else:
                                # 3. Two-token abbreviation/prefix logic (e.g., "TJ Hock")
                                if len(tokens) == 2:
                                    t0, t1 = tokens[0].lower(), tokens[1].lower()
                                    matched_index = None
                                    for i, (fn, ln) in enumerate(zip(first_names, last_names)):
                                        if not fn or not ln:
                                            continue
                                        fn_norm = fn.lower().replace('.', '')
                                        # Incorporate football_name and initials for abbreviation matching
                                        fb_name = football_names[i] if i < len(football_names) else None
                                        fb_norm = fb_name.lower().replace('.', '') if fb_name else ''
                                        initials = ''.join([part[0] for part in fn.split() if part]).lower()
                                        ln_norm = ln.lower().replace('.', '')
                                        first_variants = [fn_norm, fb_norm, initials]
                                        if any(v.startswith(t0) for v in first_variants if v) and ln_norm.startswith(t1):
                                            matched_index = i
                                            break
                                    if matched_index is not None:
                                        # Synthesize if necessary
                                        if full_names[matched_index] and len(full_names[matched_index].split()) == 1:
                                            full_player_name = f"{full_names[matched_index]} {last_names[matched_index]}"
                                        else:
                                            full_player_name = full_names[matched_index]
                                    else:
                                        match_result = matcher.find_best_match(original, ordered_candidates, min_score=0.60)
                                        if match_result and match_result['score'] >= 0.70:
                                            full_player_name = match_result['matched_name']
                                else:
                                    # General fallback fuzzy
                                    match_result = matcher.find_best_match(original, ordered_candidates, min_score=0.60)
                                    if match_result and match_result['score'] >= 0.70:
                                        full_player_name = match_result['matched_name']

                        # Post-processing upgrade: if matched name is a single token but original had >1 tokens
                        if include_full_names:
                            orig_tokens = tokens
                            if len(orig_tokens) >= 2 and len(full_player_name.split()) == 1:
                                # Try upgrade using first_name + last_name combo
                                # Find candidate row where first name or last name matches and other token fuzzy matches
                                import difflib
                                target_first = orig_tokens[0].lower()
                                target_second = orig_tokens[1].lower()
                                best_upgrade = None
                                for fn, ln, full in zip(first_names, last_names, full_names):
                                    if not fn or not ln:
                                        continue
                                    fn_norm = fn.lower().replace('.', '')
                                    ln_norm = ln.lower().replace('.', '')
                                    # Condition: matched token equals fn or ln
                                    if full_player_name.lower() in {fn_norm, ln_norm}:
                                        # Compute closeness of other token to ln or fn
                                        ratio_ln = difflib.SequenceMatcher(None, target_second, ln_norm).ratio()
                                        ratio_fn = difflib.SequenceMatcher(None, target_second, fn_norm).ratio()
                                        # Accept if decent similarity or original second token is 'jr' and full contains 'jr'
                                        if ratio_ln >= 0.6 or ratio_fn >= 0.6 or target_second in {'jr', 'jr.'} and ('jr' in full.lower()):
                                            best_upgrade = full
                                            break
                                if best_upgrade:
                                    full_player_name = best_upgrade
                            # Special case: original tokens include 'jr' but matched lacks it; try find full name with Jr
                            if any(t in {'jr', 'jr.'} for t in orig_tokens) and 'jr' not in full_player_name.lower():
                                for full in full_names:
                                    if 'jr' in full.lower() and orig_tokens[0].lower() in full.lower():
                                        full_player_name = full
                                        break
                            # If still single token and we can synthesize from unique first name + last name
                            if len(full_player_name.split()) == 1:
                                # Find matching first name row
                                for fn, ln, full in zip(first_names, last_names, full_names):
                                    if fn and ln and full_player_name.lower() == fn.lower().replace('.', ''):
                                        synthesized = f"{fn} {ln}"
                                        full_player_name = synthesized
                                        break
                except Exception as e:
                    # Fail silently, keep original name
                    print(f"Full name enrichment error for pick {pick.id}: {e}")
            picks_data.append({
                'id': pick.id,
                'user_id': pick.user_id,
                'username': pick.user.username,
                'game_id': pick.game_id,
                'game_matchup': f"{pick.game.away_team} @ {pick.game.home_team}",
                'week': pick.game.week,
                'pick_type': pick.pick_type,
                'player_name': pick.player_name,
                'full_player_name': full_player_name if include_full_names else None,
                'player_position': pick.player_position,
                'odds': pick.odds,
                'stake': float(pick.stake),
                'result': pick.result,
                'payout': float(pick.payout) if pick.payout else 0.0,
                'graded_at': pick.graded_at.isoformat() if pick.graded_at else None
            })
        
        return jsonify({'picks': picks_data}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@api_bp.route('/picks', methods=['POST'])
def create_pick():
    data = request.get_json()
    
    # Validate input
    schema = PickCreateSchema()
    try:
        validated_data = schema.load(data)
    except ValidationError as err:
        return jsonify({'error': 'Validation failed', 'details': err.messages}), 400
    
    try:
        user_id = validated_data['user_id']
        game_id = validated_data['game_id']
        pick_type = validated_data['pick_type']
        player_name = validated_data['player_name'].strip()
        player_position = validated_data['player_position']
        odds = validated_data['odds']
        stake = validated_data['stake']
        
        # Get the game to access season and teams for position lookup
        game = Game.query.get(game_id)
        if not game:
            return jsonify({'error': 'Game not found'}), 404
        
        # If position is UNK (default), try to auto-detect from roster
        if player_position == 'UNK':
            player_position = get_player_position(player_name, game)
        
        existing_pick = PickModel.query.filter_by(
            user_id=user_id,
            game_id=game_id,
            pick_type=pick_type
        ).first()
        
        if existing_pick:
            return jsonify({'error': 'Pick already exists for this user/game/type'}), 409
        
        new_pick = PickModel(
            user_id=user_id,
            game_id=game_id,
            pick_type=pick_type,
            player_name=player_name,
            player_position=player_position,
            odds=int(odds),
            stake=float(stake),
            result='Pending',
            payout=0.0
        )
        
        db.session.add(new_pick)
        db.session.commit()
        
        return jsonify({
            'message': 'Pick created successfully',
            'pick_id': new_pick.id,
            'player_position': player_position
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@api_bp.route('/picks/<int:pick_id>', methods=['PUT'])
def update_pick(pick_id):
    data = request.get_json()
    
    # Validate input
    schema = PickUpdateSchema()
    try:
        validated_data = schema.load(data)
    except ValidationError as err:
        return jsonify({'error': 'Validation failed', 'details': err.messages}), 400
    
    try:
        pick = PickModel.query.get_or_404(pick_id)
        
        if 'player_name' in validated_data:
            pick.player_name = validated_data['player_name'].strip()
        if 'player_position' in validated_data:
            pick.player_position = validated_data['player_position']
        if 'pick_type' in validated_data:
            pick.pick_type = validated_data['pick_type']
        if 'odds' in validated_data:
            pick.odds = validated_data['odds']
        if 'stake' in validated_data:
            pick.stake = validated_data['stake']
        
        db.session.commit()
        
        return jsonify({'message': 'Pick updated successfully'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@api_bp.route('/picks/<int:pick_id>', methods=['DELETE'])
def delete_pick(pick_id):
    try:
        pick = PickModel.query.get_or_404(pick_id)
        
        db.session.delete(pick)
        db.session.commit()
        
        return jsonify({'message': 'Pick deleted successfully'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
