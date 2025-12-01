"""
Admin API endpoints - Dashboard stats, grading, admin operations
"""
from flask import request, jsonify
from sqlalchemy import func
from marshmallow import ValidationError
from . import api_bp
from ...models import User, Game, Pick as PickModel
from ... import db
from ...validators import GradeWeekSchema


@api_bp.route('/grade-week', methods=['POST'])
def grade_week():
    data = request.get_json()
    
    # Validate input
    schema = GradeWeekSchema()
    try:
        validated_data = schema.load(data)
    except ValidationError as err:
        return jsonify({'error': 'Validation failed', 'details': err.messages}), 400
    
    week = validated_data['week']
    season = validated_data['season']
    
    try:
        from ...services.grading_service import GradingService
        
        grading_service = GradingService()
        result = grading_service.grade_week(week, season)
        
        if not result['success']:
            return jsonify({'error': result['error']}), 400
        
        return jsonify({
            'message': f"Week {week} graded successfully",
            'week': result['week'],
            'season': result['season'],
            'games_graded': result['games_graded'],
            'total_graded': result['total_graded'],
            'total_won': result['total_won'],
            'total_lost': result['total_lost'],
            'total_needs_review': result['total_needs_review'],
            'ftd': {
                'graded': result['ftd']['graded'],
                'won': result['ftd']['won'],
                'lost': result['ftd']['lost']
            },
            'atts': {
                'graded': result['atts']['graded'],
                'won': result['atts']['won'],
                'lost': result['atts']['lost']
            }
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@api_bp.route('/admin/dashboard-stats', methods=['GET'])
def get_dashboard_stats():
    season = request.args.get('season', 2025, type=int)
    try:
        # Total active players
        total_players = db.session.query(User).filter(User.is_active == True).count()
        
        # Get current week (latest week in schedule for season)
        current_week = db.session.query(func.max(Game.week)).filter(Game.season == season).scalar() or 1
        
        # Total picks this week
        total_picks_this_week = db.session.query(PickModel).join(Game).filter(
            Game.season == season,
            Game.week == current_week
        ).count()
        
        # Pending picks (across entire season)
        pending_picks = db.session.query(PickModel).join(Game).filter(
            Game.season == season,
            PickModel.result == 'Pending'
        ).count()
        
        # League FTD bankroll
        league_ftd_bankroll = db.session.query(
            func.sum(PickModel.payout)
        ).join(Game).filter(
            PickModel.pick_type == 'FTD',
            Game.season == season
        ).scalar() or 0.0
        
        # League ATTS bankroll
        league_atts_bankroll = db.session.query(
            func.sum(PickModel.payout)
        ).join(Game).filter(
            PickModel.pick_type == 'ATTS',
            Game.season == season
        ).scalar() or 0.0
        
        # Overall win rate
        total_wins = db.session.query(PickModel).join(Game).filter(
            Game.season == season,
            PickModel.result == 'W'
        ).count()
        
        total_losses = db.session.query(PickModel).join(Game).filter(
            Game.season == season,
            PickModel.result == 'L'
        ).count()
        
        overall_win_rate = round((total_wins / (total_wins + total_losses) * 100) if (total_wins + total_losses) > 0 else 0, 1)
        
        # Games this week
        games_this_week = db.session.query(Game).filter(
            Game.season == season,
            Game.week == current_week
        ).count()
        
        # Games graded this week
        games_graded = db.session.query(Game).filter(
            Game.season == season,
            Game.week == current_week,
            Game.is_final == True
        ).count()
        
        # Recent picks (last 10)
        recent_picks = db.session.query(PickModel).join(Game).join(User).filter(
            Game.season == season
        ).order_by(PickModel.id.desc()).limit(10).all()
        
        recent_picks_data = []
        for pick in recent_picks:
            recent_picks_data.append({
                'id': pick.id,
                'user_name': pick.user.display_name or pick.user.username,
                'week': pick.game.week,
                'game': f"{pick.game.away_team} @ {pick.game.home_team}",
                'pick_type': pick.pick_type,
                'player_name': pick.player_name,
                'result': pick.result,
                'payout': float(pick.payout)
            })
        
        return jsonify({
            'total_players': total_players,
            'current_week': current_week,
            'total_picks_this_week': total_picks_this_week,
            'pending_picks': pending_picks,
            'league_ftd_bankroll': round(league_ftd_bankroll, 2),
            'league_atts_bankroll': round(league_atts_bankroll, 2),
            'overall_win_rate': overall_win_rate,
            'games_this_week': games_this_week,
            'games_graded': games_graded,
            'recent_picks': recent_picks_data
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
