"""
Games API endpoints - View games, weekly games, week details
"""
from flask import request, jsonify
from datetime import datetime
from . import api_bp
from ...data_loader import load_data_with_cache_web
from ...models import User, Game, Pick as PickModel
from ... import db
from nfl_core.stats import get_first_td_scorers
import polars as pl


@api_bp.route('/weekly-games', methods=['GET'])
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


@api_bp.route('/game-touchdowns/<game_id>', methods=['GET'])
def get_game_touchdowns(game_id):
    """Get all touchdown scorers for a specific game in order"""
    season = request.args.get('season', 2025, type=int)
    try:
        schedule_df, pbp_df, roster_df = load_data_with_cache_web(season, use_cache=True)
        
        # Filter PBP data for this specific game
        if pbp_df.height == 0:
            return jsonify({'touchdowns': [], 'game_id': game_id}), 200
        
        game_pbp = pbp_df.filter(pl.col('game_id') == game_id)
        
        if game_pbp.height == 0:
            return jsonify({'touchdowns': [], 'game_id': game_id}), 200
        
        # Get touchdown plays sorted by play_id
        td_plays = game_pbp.filter(
            (pl.col('touchdown') == 1) | 
            (pl.col('td_player_name').is_not_null())
        )
        
        if td_plays.height == 0:
            return jsonify({'touchdowns': [], 'game_id': game_id}), 200
        
        # Sort by play_id or time
        if 'play_id' in td_plays.columns:
            td_plays = td_plays.sort('play_id')
        else:
            td_plays = td_plays.sort(['qtr', 'time'])
        
        # Create a mapping from ID to Full Name
        id_to_name = {}
        if roster_df is not None and 'gsis_id' in roster_df.columns and 'full_name' in roster_df.columns:
            temp_df = roster_df.select(['gsis_id', 'full_name', 'position']).unique()
            for r in temp_df.to_dicts():
                if r['gsis_id'] and r['full_name']:
                    id_to_name[r['gsis_id']] = {
                        'name': r['full_name'],
                        'position': r.get('position')
                    }
        
        touchdowns = []
        for idx, row in enumerate(td_plays.to_dicts()):
            scorer = None
            player_id = row.get('td_player_id')
            team = row.get('td_team') or row.get('posteam') or 'UNK'
            position = None
            
            # Try roster lookup
            if player_id and player_id in id_to_name:
                scorer = id_to_name[player_id]['name']
                position = id_to_name[player_id]['position']
            
            # Try PBP columns if no roster match
            if not scorer:
                for key in ['fantasy_player_name', 'player_name', 'td_player_name', 'desc', 'description']:
                    if key in row and row.get(key):
                        scorer = str(row.get(key))
                        if key in ['desc', 'description'] and ' for ' in scorer:
                            scorer = scorer.split(' for ')[0].strip()
                        break
            
            if scorer:
                touchdowns.append({
                    'order': idx + 1,
                    'player': scorer,
                    'team': team,
                    'position': position,
                    'quarter': row.get('qtr'),
                    'time': row.get('time'),
                    'is_first_td': idx == 0
                })
        
        return jsonify({
            'touchdowns': touchdowns,
            'game_id': game_id
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e), 'touchdowns': [], 'game_id': game_id}), 500


@api_bp.route('/week-detail', methods=['GET'])
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


@api_bp.route('/games', methods=['GET'])
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


@api_bp.route('/users', methods=['GET'])
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


@api_bp.route('/user/<int:user_id>', methods=['GET'])
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
