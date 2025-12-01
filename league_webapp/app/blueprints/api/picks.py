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
        
        # Filter to only players from the game's teams
        game_rosters = roster_df.filter(
            (roster_df['team'] == game.home_team) | 
            (roster_df['team'] == game.away_team)
        )
        
        if len(game_rosters) == 0:
            return 'UNK'
        
        # Get player names and positions
        players = game_rosters.select(['player_name', 'position']).to_dicts()
        player_names = [p['player_name'] for p in players]
        
        # Use fuzzy matcher to find best match
        matcher = NameMatcher()
        match_result = matcher.find_best_match(player_name, player_names, min_score=0.70)
        
        if match_result and match_result['auto_accept']:
            # Find the position for the matched player
            matched_player = next((p for p in players if p['player_name'] == match_result['matched_name']), None)
            if matched_player and matched_player['position']:
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
    
    try:
        query = PickModel.query.join(Game)
        
        if season:
            query = query.filter(Game.season == season)
        if week:
            query = query.filter(Game.week == week)
        if user_id:
            query = query.filter(PickModel.user_id == user_id)
        
        picks = query.order_by(Game.week, Game.game_date, Game.game_time).all()
        
        picks_data = []
        for pick in picks:
            picks_data.append({
                'id': pick.id,
                'user_id': pick.user_id,
                'username': pick.user.username,
                'game_id': pick.game_id,
                'game_matchup': f"{pick.game.away_team} @ {pick.game.home_team}",
                'week': pick.game.week,
                'pick_type': pick.pick_type,
                'player_name': pick.player_name,
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
