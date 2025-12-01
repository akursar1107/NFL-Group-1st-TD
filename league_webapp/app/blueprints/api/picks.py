"""
Picks API endpoints - Create, read, update, delete picks
"""
from flask import request, jsonify
from . import api_bp
from ...models import User, Game, Pick as PickModel
from ... import db


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
    
    try:
        user_id = data.get('user_id')
        game_id = data.get('game_id')
        pick_type = data.get('pick_type', 'FTD')
        player_name = data.get('player_name', '').strip()
        player_position = data.get('player_position', 'UNK')
        odds = data.get('odds')
        stake = data.get('stake', 1.0)
        
        if not all([user_id, game_id, player_name, odds]):
            return jsonify({'error': 'Missing required fields: user_id, game_id, player_name, odds'}), 400
        
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
            'pick_id': new_pick.id
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@api_bp.route('/picks/<int:pick_id>', methods=['PUT'])
def update_pick(pick_id):
    data = request.get_json()
    
    try:
        pick = PickModel.query.get_or_404(pick_id)
        
        if 'player_name' in data:
            pick.player_name = data['player_name'].strip()
        if 'player_position' in data:
            pick.player_position = data['player_position']
        if 'pick_type' in data:
            pick.pick_type = data['pick_type']
        if 'odds' in data:
            pick.odds = int(data['odds'])
        if 'stake' in data:
            pick.stake = float(data['stake'])
        
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
