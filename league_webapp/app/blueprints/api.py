from flask import Blueprint, request, jsonify
from ..data_loader import load_data_with_cache_web
from ..routes import get_nfl_stats_data
from ..models import User, Game, Pick as PickModel
from .. import db, cache
from ..services import StatsService
from sqlalchemy import func, case
from datetime import datetime
from nfl_core.stats import (
    get_first_td_scorers, 
    get_player_season_stats, 
    calculate_defense_rankings,
    get_red_zone_stats,
    get_opening_drive_stats,
    get_team_red_zone_splits,
    identify_funnel_defenses,
    calculate_fair_odds,
    calculate_kelly_criterion
)
from nfl_core.config import API_KEY
from ..odds_fetcher import get_odds_api_event_ids_for_season, fetch_odds_data, get_best_odds_for_game
import polars as pl

api_bp = Blueprint('api', __name__)

@api_bp.route('/analysis', methods=['GET'])
@cache.cached(timeout=300, query_string=True)  # Cache for 5 minutes per season
def get_analysis():
    season = request.args.get('season', 2025, type=int)
    try:
        stats_data = get_nfl_stats_data(season, use_cache=True)
        player_database = []
        roster_df = stats_data['roster_df']
        player_stats_full = stats_data['player_stats_full']
        player_stats_recent = stats_data['player_stats_recent']
        first_td_map = stats_data['first_td_map']
        schedule_df = stats_data['schedule_df']
        defense_data = stats_data['defense_rankings']
        team_data = stats_data.get('team_data', None)
        trends_data = stats_data.get('trends_data', None)
        history_data = stats_data.get('history_data', None)
        for player_name in player_stats_full.keys():
            stats_full = player_stats_full[player_name]
            stats_recent = player_stats_recent.get(player_name, {'first_tds': 0, 'team_games': 0})
            player_id = stats_full.get('player_id', '')
            position = None
            team = None
            if roster_df is not None and roster_df.height > 0:
                player_rows = roster_df.filter((roster_df['gsis_id'] == player_id) | (roster_df['full_name'].str.to_lowercase() == player_name.lower()))
                if player_rows.height > 0:
                    team = player_rows[0, 'team'] if 'team' in player_rows.columns else None
                    position = player_rows[0, 'position'] if 'position' in player_rows.columns else None
            player_database.append({
                'name': player_name,
                'position': position,
                'team': team,
                'stats_full': stats_full,
                'stats_recent': stats_recent
            })
        return jsonify({
            'season': season,
            'player_data': player_database,
            'defense_data': defense_data,
            'team_data': team_data,
            'trends_data': trends_data,
            'history_data': history_data,
            'error': None
        }), 200
    except Exception as e:
        return jsonify({ 'error': str(e) }), 500

@api_bp.route('/import-data', methods=['POST'])
def import_data():
    data = request.get_json(force=True)
    season = data.get('season', 2025)
    try:
        load_data_with_cache_web(season, use_cache=False)
        return jsonify({ 'message': f'Data import for season {season} successful.' }), 200
    except Exception as e:
        return jsonify({ 'message': f'Import failed: {str(e)}' }), 500

@api_bp.route('/standings', methods=['GET'])
@cache.cached(timeout=60, query_string=True)  # Cache for 1 minute per season
def get_standings():
    season = request.args.get('season', 2025, type=int)
    try:
        # Use StatsService for cleaner code
        standings = StatsService.calculate_standings(season)
        stats = StatsService.calculate_league_stats(standings)
        
        return jsonify({
            'standings': standings,
            'season': season,
            'stats': stats
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/best-bets', methods=['GET'])
@cache.cached(timeout=1800, query_string=True)  # Cache for 30 minutes (odds API limit)
def get_best_bets():
    season = request.args.get('season', 2025, type=int)
    try:
        if not API_KEY:
            return jsonify({'error': 'API key not configured', 'bets': []}), 200
        
        schedule_df, pbp_df, roster_df = load_data_with_cache_web(season, use_cache=True)
        if schedule_df.height == 0:
            return jsonify({'error': 'No schedule data available', 'bets': []}), 200
        
        today_str = datetime.now().strftime("%Y-%m-%d")
        future_games = schedule_df.filter(pl.col("gameday") >= today_str)
        if future_games.height == 0:
            return jsonify({'error': 'No upcoming games found', 'bets': []}), 200
        
        try:
            week_val = future_games["week"].cast(pl.Int64).min()
            current_week = int(week_val) if week_val is not None else 1
        except Exception:
            current_week = 1
        
        week_games = schedule_df.filter(pl.col("week").cast(pl.Int64) == current_week)
        first_td_map = get_first_td_scorers(pbp_df, target_game_ids=None, roster_df=roster_df)
        player_stats = get_player_season_stats(schedule_df, first_td_map, last_n_games=5)
        defense_rankings = calculate_defense_rankings(schedule_df, first_td_map, roster_df)
        funnel_defenses = identify_funnel_defenses(defense_rankings) or {}
        rz_stats = get_red_zone_stats(pbp_df, roster_df) or {}
        od_stats = get_opening_drive_stats(pbp_df, roster_df) or {}
        
        odds_event_map = get_odds_api_event_ids_for_season(schedule_df, API_KEY)
        all_bets = []
        
        for game_dict in week_games.to_dicts():
            game_id = game_dict['game_id']
            home_team = game_dict['home_team']
            away_team = game_dict['away_team']
            
            event_id = odds_event_map.get(game_id)
            if not event_id:
                continue
            
            odds_data = fetch_odds_data(event_id, API_KEY)
            if not odds_data:
                continue
            
            for player_name, stats in player_stats.items():
                if stats['team_games'] < 3:
                    continue
                
                prob = stats.get('prob', 0)
                if prob < 0.01:
                    continue
                
                position = None
                team = None
                if roster_df is not None:
                    player_rows = roster_df.filter(
                        roster_df['full_name'].str.to_lowercase() == player_name.lower()
                    )
                    if player_rows.height > 0:
                        team = player_rows[0, 'team']
                        position = player_rows[0, 'position']
                
                if team not in [home_team, away_team]:
                    continue
                
                opp_team = away_team if team == home_team else home_team
                best_odds_info = get_best_odds_for_game(odds_data, player_name)
                
                if not best_odds_info or best_odds_info['odds'] <= 0:
                    continue
                
                fair_odds = calculate_fair_odds(prob)
                ev = prob * best_odds_info['odds'] - 1
                kelly = calculate_kelly_criterion(prob, best_odds_info['odds'])
                
                rz_info = rz_stats.get(player_name, {})
                od_info = od_stats.get(player_name, {})
                funnel_type = funnel_defenses.get(opp_team)
                
                all_bets.append({
                    'player': player_name,
                    'team': team,
                    'opponent': opp_team,
                    'position': position,
                    'prob': round(prob * 100, 1),
                    'fair_odds': round(fair_odds, 0),
                    'best_odds': best_odds_info['odds'],
                    'sportsbook': best_odds_info['sportsbook'],
                    'ev': round(ev * 100, 1),
                    'kelly': round(kelly * 100, 1),
                    'first_tds': stats['first_tds'],
                    'games': stats['team_games'],
                    'rz_opps': rz_info.get('rz_opps', 0),
                    'rz_tds': rz_info.get('rz_tds', 0),
                    'od_opps': od_info.get('od_opps', 0),
                    'od_tds': od_info.get('od_tds', 0),
                    'funnel_type': funnel_type,
                    'game_id': game_id
                })
        
        all_bets.sort(key=lambda x: x['ev'], reverse=True)
        positive_ev_bets = [b for b in all_bets if b['ev'] > 0]
        
        return jsonify({
            'bets': positive_ev_bets,
            'week': current_week,
            'season': season,
            'last_updated': datetime.now().isoformat()
        }), 200
    except Exception as e:
        return jsonify({'error': str(e), 'bets': []}), 500

@api_bp.route('/weekly-games', methods=['GET'])
@cache.cached(timeout=300, query_string=True)  # Cache for 5 minutes
def get_weekly_games():
    season = request.args.get('season', 2025, type=int)
    week = request.args.get('week', type=int)
    try:
        schedule_df, _, roster_df = load_data_with_cache_web(season, use_cache=True)
        
        if week is None:
            today_str = datetime.now().strftime("%Y-%m-%d")
            future_games = schedule_df.filter(pl.col("gameday") >= today_str)
            if future_games.height > 0:
                week_val = future_games["week"].cast(pl.Int64).min()
                week = int(week_val) if week_val is not None else 1
            else:
                week = 1
        
        week_games = schedule_df.filter(pl.col("week").cast(pl.Int64) == week)
        games = []
        
        for game in week_games.to_dicts():
            games.append({
                'game_id': game['game_id'],
                'week': game['week'],
                'gameday': game['gameday'],
                'home_team': game['home_team'],
                'away_team': game['away_team'],
                'home_score': game.get('home_score'),
                'away_score': game.get('away_score'),
                'game_type': game.get('game_type', 'REG')
            })
        
        return jsonify({
            'games': games,
            'week': week,
            'season': season
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/week-detail', methods=['GET'])
@cache.cached(timeout=60, query_string=True)  # Cache for 1 minute
def get_week_detail():
    season = request.args.get('season', 2025, type=int)
    week = request.args.get('week', type=int)
    
    if week is None:
        return jsonify({'error': 'Week parameter is required'}), 400
    
    try:
        games = Game.query.filter_by(
            week=week, 
            season=season
        ).order_by(Game.game_date, Game.game_time).all()
        
        if not games:
            return jsonify({
                'games': [],
                'week': week,
                'season': season,
                'available_weeks': [],
                'message': 'No games found for this week'
            }), 200
        
        games_data = []
        for game in games:
            ftd_picks = PickModel.query.filter_by(
                game_id=game.id, 
                pick_type='FTD'
            ).join(User).order_by(User.username).all()
            
            atts_picks = PickModel.query.filter_by(
                game_id=game.id,
                pick_type='ATTS'
            ).join(User).order_by(User.username).all()
            
            ftd_picks_data = []
            for pick in ftd_picks:
                ftd_picks_data.append({
                    'id': pick.id,
                    'user_id': pick.user_id,
                    'username': pick.user.username,
                    'player_name': pick.player_name,
                    'player_position': pick.player_position,
                    'odds': pick.odds,
                    'stake': float(pick.stake),
                    'result': pick.result,
                    'payout': float(pick.payout) if pick.payout else 0.0,
                    'graded_at': pick.graded_at.isoformat() if pick.graded_at else None
                })
            
            atts_picks_data = []
            for pick in atts_picks:
                atts_picks_data.append({
                    'id': pick.id,
                    'user_id': pick.user_id,
                    'username': pick.user.username,
                    'player_name': pick.player_name,
                    'player_position': pick.player_position,
                    'odds': pick.odds,
                    'stake': float(pick.stake),
                    'result': pick.result,
                    'payout': float(pick.payout) if pick.payout else 0.0,
                    'graded_at': pick.graded_at.isoformat() if pick.graded_at else None
                })
            
            games_data.append({
                'game_id': game.game_id,
                'db_id': game.id,
                'week': game.week,
                'matchup': f"{game.away_team} @ {game.home_team}",
                'home_team': game.home_team,
                'away_team': game.away_team,
                'game_date': game.game_date.isoformat() if game.game_date else None,
                'game_time': game.game_time.strftime('%H:%M:%S') if game.game_time else None,
                'is_final': game.is_final,
                'home_score': None,
                'away_score': None,
                'actual_first_td_player': game.actual_first_td_player,
                'ftd_picks': ftd_picks_data,
                'atts_picks': atts_picks_data,
                'total_picks': len(ftd_picks_data) + len(atts_picks_data)
            })
        
        all_weeks = db.session.query(Game.week).filter_by(
            season=season
        ).distinct().order_by(Game.week).all()
        available_weeks = [w[0] for w in all_weeks]
        
        return jsonify({
            'games': games_data,
            'week': week,
            'season': season,
            'available_weeks': available_weeks
        }), 200
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@api_bp.route('/picks', methods=['GET'])
@cache.cached(timeout=60, query_string=True)  # Cache for 1 minute
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
        
        # Clear relevant caches
        cache.clear()
        
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
        
        # Clear relevant caches
        cache.clear()
        
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
        
        # Clear relevant caches
        cache.clear()
        
        return jsonify({'message': 'Pick deleted successfully'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@api_bp.route('/users', methods=['GET'])
@cache.cached(timeout=300)  # Cache for 5 minutes
def get_users():
    try:
        users = User.query.filter_by(is_active=True).order_by(User.username).all()
        
        users_data = []
        for user in users:
            users_data.append({
                'id': user.id,
                'username': user.username,
                'display_name': user.display_name or user.username
            })
        
        return jsonify({'users': users_data}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/games', methods=['GET'])
@cache.cached(timeout=300, query_string=True)  # Cache for 5 minutes
def get_games():
    season = request.args.get('season', 2025, type=int)
    week = request.args.get('week', type=int)
    
    try:
        query = Game.query.filter_by(season=season)
        
        if week:
            query = query.filter_by(week=week)
        
        games = query.order_by(Game.week, Game.game_date, Game.game_time).all()
        
        games_data = []
        for game in games:
            games_data.append({
                'id': game.id,
                'game_id': game.game_id,
                'week': game.week,
                'season': game.season,
                'matchup': f"{game.away_team} @ {game.home_team}",
                'home_team': game.home_team,
                'away_team': game.away_team,
                'game_date': game.game_date.isoformat() if game.game_date else None,
                'game_time': game.game_time.isoformat() if game.game_time else None,
                'is_final': game.is_final
            })
        
        return jsonify({'games': games_data}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/grade-week', methods=['POST'])
def grade_week():
    data = request.get_json()
    week = data.get('week')
    season = data.get('season', 2025)
    
    if not week:
        return jsonify({'error': 'Week parameter is required'}), 400
    
    try:
        from ..services.grading_service import GradingService
        
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

@api_bp.route('/user/<int:user_id>', methods=['GET'])
@cache.cached(timeout=60, query_string=True)  # Cache for 1 minute
def get_user_detail(user_id):
    season = request.args.get('season', 2025, type=int)
    
    try:
        user = User.query.get_or_404(user_id)
        
        # Get all picks for this user in the season
        picks = PickModel.query.join(Game).filter(
            PickModel.user_id == user_id,
            Game.season == season
        ).order_by(Game.week, Game.game_date, Game.game_time).all()
        
        # Calculate overall stats
        ftd_picks = [p for p in picks if p.pick_type == 'FTD']
        atts_picks = [p for p in picks if p.pick_type == 'ATTS']
        
        ftd_wins = sum(1 for p in ftd_picks if p.result == 'W')
        ftd_losses = sum(1 for p in ftd_picks if p.result == 'L')
        ftd_pending = sum(1 for p in ftd_picks if p.result == 'Pending')
        ftd_bankroll = sum(float(p.payout) for p in ftd_picks)
        
        atts_wins = sum(1 for p in atts_picks if p.result == 'W')
        atts_losses = sum(1 for p in atts_picks if p.result == 'L')
        atts_pending = sum(1 for p in atts_picks if p.result == 'Pending')
        atts_bankroll = sum(float(p.payout) for p in atts_picks)
        
        # Get weekly breakdown
        weekly_stats = {}
        for pick in picks:
            week = pick.game.week
            if week not in weekly_stats:
                weekly_stats[week] = {
                    'week': week,
                    'ftd_wins': 0,
                    'ftd_losses': 0,
                    'ftd_pending': 0,
                    'ftd_bankroll': 0.0,
                    'atts_wins': 0,
                    'atts_losses': 0,
                    'atts_pending': 0,
                    'atts_bankroll': 0.0,
                    'total_picks': 0
                }
            
            weekly_stats[week]['total_picks'] += 1
            
            if pick.pick_type == 'FTD':
                if pick.result == 'W':
                    weekly_stats[week]['ftd_wins'] += 1
                elif pick.result == 'L':
                    weekly_stats[week]['ftd_losses'] += 1
                elif pick.result == 'Pending':
                    weekly_stats[week]['ftd_pending'] += 1
                weekly_stats[week]['ftd_bankroll'] += float(pick.payout)
            else:  # ATTS
                if pick.result == 'W':
                    weekly_stats[week]['atts_wins'] += 1
                elif pick.result == 'L':
                    weekly_stats[week]['atts_losses'] += 1
                elif pick.result == 'Pending':
                    weekly_stats[week]['atts_pending'] += 1
                weekly_stats[week]['atts_bankroll'] += float(pick.payout)
        
        # Format all picks for detailed view
        picks_data = []
        for pick in picks:
            picks_data.append({
                'id': pick.id,
                'week': pick.game.week,
                'game_matchup': f"{pick.game.away_team} @ {pick.game.home_team}",
                'game_date': pick.game.game_date.isoformat() if pick.game.game_date else None,
                'pick_type': pick.pick_type,
                'player_name': pick.player_name,
                'player_position': pick.player_position,
                'odds': pick.odds,
                'stake': float(pick.stake),
                'result': pick.result,
                'payout': float(pick.payout),
                'graded_at': pick.graded_at.isoformat() if pick.graded_at else None,
                'is_final': pick.game.is_final
            })
        
        return jsonify({
            'user': {
                'id': user.id,
                'username': user.username,
                'display_name': user.display_name or user.username
            },
            'season': season,
            'stats': {
                'ftd': {
                    'wins': ftd_wins,
                    'losses': ftd_losses,
                    'pending': ftd_pending,
                    'bankroll': round(ftd_bankroll, 2),
                    'total_picks': len(ftd_picks),
                    'win_rate': round((ftd_wins / (ftd_wins + ftd_losses) * 100) if (ftd_wins + ftd_losses) > 0 else 0, 1)
                },
                'atts': {
                    'wins': atts_wins,
                    'losses': atts_losses,
                    'pending': atts_pending,
                    'bankroll': round(atts_bankroll, 2),
                    'total_picks': len(atts_picks),
                    'win_rate': round((atts_wins / (atts_wins + atts_losses) * 100) if (atts_wins + atts_losses) > 0 else 0, 1)
                },
                'total': {
                    'picks': len(picks),
                    'wins': ftd_wins + atts_wins,
                    'losses': ftd_losses + atts_losses,
                    'pending': ftd_pending + atts_pending,
                    'bankroll': round(ftd_bankroll + atts_bankroll, 2)
                }
            },
            'weekly_stats': sorted(weekly_stats.values(), key=lambda x: x['week']),
            'picks': picks_data
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
