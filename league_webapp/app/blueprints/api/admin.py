"""
Admin API endpoints - Dashboard stats, grading, admin operations
"""
from flask import request, jsonify
from sqlalchemy import func
from marshmallow import ValidationError
import csv
import io
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


@api_bp.route('/grade-by-type', methods=['POST'])
def grade_by_type():
    """Grade all pending picks of a specific type (FTD or ATTS) for a given season"""
    data = request.get_json()
    
    pick_type = data.get('pick_type')
    season = data.get('season', 2025)
    
    # Validate pick_type
    if pick_type not in ['FTD', 'ATTS']:
        return jsonify({'error': 'pick_type must be "FTD" or "ATTS"'}), 400
    
    try:
        from ...services.grading_service import GradingService
        
        grading_service = GradingService()
        result = grading_service.grade_by_pick_type(pick_type, season)
        
        if not result['success']:
            return jsonify({'error': result.get('error', 'Failed to grade picks')}), 400
        
        return jsonify({
            'message': result.get('message', f'Successfully graded {result["graded"]} {pick_type} pick(s)'),
            'season': result['season'],
            'pick_type': result['pick_type'],
            'weeks_graded': len(result.get('weeks_graded', [])),
            'total_graded': result['graded'],
            'total_won': result['won'],
            'total_lost': result['lost'],
            'total_needs_review': result.get('needs_review', 0)
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


@api_bp.route('/import-picks', methods=['POST'])
def import_picks():
    """Import picks from CSV file"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not file.filename.endswith('.csv'):
            return jsonify({'error': 'File must be a CSV'}), 400
        
        # Read CSV file
        stream = io.StringIO(file.stream.read().decode("UTF8"), newline=None)
        csv_reader = csv.DictReader(stream)
        
        imported_count = 0
        skipped_count = 0
        errors = []
        
        for row_num, row in enumerate(csv_reader, start=2):  # Start at 2 to account for header
            try:
                # Extract and validate data
                user_id = int(row.get('user_id', 0))
                game_id = int(row.get('game_id', 0))
                pick_type = row.get('pick_type', '').strip().upper()
                player_name = row.get('player_name', '').strip()
                odds_str = row.get('odds', '').strip()
                stake_str = row.get('stake', '1.00').strip()
                
                # Validate required fields
                if not user_id or not game_id or not pick_type or not player_name:
                    errors.append(f"Row {row_num}: Missing required fields")
                    continue
                
                # Validate pick type
                if pick_type not in ['FTD', 'ATTS']:
                    errors.append(f"Row {row_num}: Invalid pick_type '{pick_type}', must be FTD or ATTS")
                    continue
                
                # Parse odds (remove + sign if present)
                odds_str = odds_str.replace('+', '')
                try:
                    odds = int(odds_str)
                except ValueError:
                    errors.append(f"Row {row_num}: Invalid odds '{odds_str}'")
                    continue
                
                # Parse stake
                try:
                    stake = float(stake_str)
                except ValueError:
                    errors.append(f"Row {row_num}: Invalid stake '{stake_str}'")
                    continue
                
                # Check if user exists
                user = User.query.get(user_id)
                if not user:
                    errors.append(f"Row {row_num}: User ID {user_id} not found")
                    continue
                
                # Check if game exists
                game = Game.query.get(game_id)
                if not game:
                    errors.append(f"Row {row_num}: Game ID {game_id} not found")
                    continue
                
                # Check for duplicate pick
                existing_pick = PickModel.query.filter_by(
                    user_id=user_id,
                    game_id=game_id,
                    pick_type=pick_type
                ).first()
                
                if existing_pick:
                    skipped_count += 1
                    continue
                
                # Auto-detect player position
                from ...fuzzy_matcher import NameMatcher
                from ...data_loader import load_data_with_cache_web
                
                try:
                    _, _, roster_df = load_data_with_cache_web(game.season, use_cache=True)
                    game_rosters = roster_df.filter(
                        (roster_df['team'] == game.home_team) | 
                        (roster_df['team'] == game.away_team)
                    )
                    
                    if len(game_rosters) > 0:
                        players = game_rosters.select(['player_name', 'position']).to_dicts()
                        player_names = [p['player_name'] for p in players]
                        
                        matcher = NameMatcher()
                        match_result = matcher.find_best_match(player_name, player_names, min_score=0.70)
                        
                        if match_result and match_result['auto_accept']:
                            matched_player = next((p for p in players if p['player_name'] == match_result['matched_name']), None)
                            if matched_player and matched_player['position']:
                                position = matched_player['position']
                                if position in ['QB', 'RB', 'WR', 'TE']:
                                    player_position = position
                                elif position in ['FB', 'HB']:
                                    player_position = 'RB'
                                else:
                                    player_position = 'UNK'
                            else:
                                player_position = 'UNK'
                        else:
                            player_position = 'UNK'
                    else:
                        player_position = 'UNK'
                except Exception:
                    player_position = 'UNK'
                
                # Create new pick
                new_pick = PickModel(
                    user_id=user_id,
                    game_id=game_id,
                    pick_type=pick_type,
                    player_name=player_name,
                    player_position=player_position,
                    odds=odds,
                    stake=stake,
                    result='Pending',
                    payout=0.0
                )
                
                db.session.add(new_pick)
                imported_count += 1
                
            except Exception as e:
                errors.append(f"Row {row_num}: {str(e)}")
                continue
        
        # Commit all picks
        db.session.commit()
        
        return jsonify({
            'message': f'Successfully imported {imported_count} picks',
            'imported_count': imported_count,
            'skipped_count': skipped_count,
            'errors': errors
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@api_bp.route('/regrade-all', methods=['POST'])
def regrade_all():
    """Re-grade all picks for the entire season"""
    season = request.args.get('season', 2025, type=int)
    
    try:
        from ...services.grading_service import GradingService
        
        grading_service = GradingService()
        result = grading_service.grade_all_weeks(season)
        
        if not result['success']:
            return jsonify({'error': result['error']}), 400
        
        return jsonify({
            'message': f"Successfully re-graded all picks for {season} season",
            'season': result['season'],
            'weeks_graded': result['weeks_graded'],
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


@api_bp.route('/pending-reviews', methods=['GET'])
def get_pending_reviews():
    """Get all match decisions that need manual review"""
    season = request.args.get('season', 2025, type=int)
    
    try:
        from ...models import MatchDecision
        from datetime import datetime
        
        # Query match decisions that need review
        pending_reviews = db.session.query(MatchDecision).join(
            PickModel, MatchDecision.pick_id == PickModel.id
        ).join(
            Game, PickModel.game_id == Game.id
        ).join(
            User, PickModel.user_id == User.id
        ).filter(
            MatchDecision.needs_review == True,
            MatchDecision.reviewed_at == None,
            Game.season == season
        ).all()
        
        reviews_data = []
        for decision in pending_reviews:
            pick = decision.pick
            game = pick.game
            user = pick.user
            
            reviews_data.append({
                'id': decision.id,
                'pick_id': pick.id,
                'user_name': user.display_name or user.username,
                'game_info': f"{game.away_team} @ {game.home_team}",
                'week': game.week,
                'pick_type': pick.pick_type,
                'pick_name': decision.pick_name,
                'scorer_name': decision.scorer_name,
                'confidence_score': round(decision.confidence_score, 2),
                'match_reason': decision.match_reason,
                'odds': pick.odds,
                'stake': float(pick.stake),
                'created_at': decision.created_at.isoformat() if decision.created_at else None
            })
        
        return jsonify({
            'pending_reviews': reviews_data,
            'total_pending': len(reviews_data)
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@api_bp.route('/review-match/<int:decision_id>', methods=['POST'])
def review_match(decision_id):
    """Accept or reject a match decision"""
    from ...models import MatchDecision
    from datetime import datetime
    
    data = request.get_json()
    decision = data.get('decision')  # 'accept' or 'reject'
    
    if decision not in ['accept', 'reject']:
        return jsonify({'error': "Decision must be 'accept' or 'reject'"}), 400
    
    try:
        # Get the match decision
        match_decision = MatchDecision.query.get(decision_id)
        if not match_decision:
            return jsonify({'error': 'Match decision not found'}), 404
        
        if match_decision.reviewed_at:
            return jsonify({'error': 'This match has already been reviewed'}), 400
        
        # Get the associated pick
        pick = PickModel.query.get(match_decision.pick_id)
        if not pick:
            return jsonify({'error': 'Associated pick not found'}), 404
        
        # Update match decision
        match_decision.reviewed_at = datetime.utcnow()
        match_decision.review_decision = decision
        # Note: reviewed_by would need user authentication to set properly
        
        # Update pick based on decision
        if decision == 'accept':
            # Match accepted - mark as win
            pick.result = 'W'
            pick.payout = pick.calculate_payout()
            pick.graded_at = datetime.utcnow()
        else:
            # Match rejected - mark as loss
            pick.result = 'L'
            pick.payout = -pick.stake
            pick.graded_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            'message': f"Match decision {decision}ed successfully",
            'pick_id': pick.id,
            'result': pick.result,
            'payout': float(pick.payout)
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@api_bp.route('/delete-all-picks', methods=['DELETE'])
def delete_all_picks():
    """Delete all picks for a specific season"""
    from ...models import MatchDecision
    
    season = request.args.get('season', 2025, type=int)
    
    try:
        # Get all picks for the season
        picks_to_delete = db.session.query(PickModel).join(Game).filter(
            Game.season == season
        ).all()
        
        deleted_count = len(picks_to_delete)
        
        # Delete associated match decisions first (due to foreign key)
        for pick in picks_to_delete:
            MatchDecision.query.filter_by(pick_id=pick.id).delete()
        
        # Delete the picks
        db.session.query(PickModel).filter(
            PickModel.id.in_([p.id for p in picks_to_delete])
        ).delete(synchronize_session=False)
        
        db.session.commit()
        
        return jsonify({
            'message': f'Successfully deleted {deleted_count} picks for {season} season',
            'deleted_count': deleted_count,
            'season': season
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
