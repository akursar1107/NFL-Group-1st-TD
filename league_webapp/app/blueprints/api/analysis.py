"""
Analysis API endpoints - Best bets, player analysis, data import
"""
from flask import request, jsonify
from datetime import datetime
from . import api_bp
from ...data_loader import load_data_with_cache_web
from ...routes import get_nfl_stats_data
from ...odds_fetcher import get_odds_api_event_ids_for_season, fetch_odds_data, get_best_odds_for_game
from nfl_core.stats import (
    get_first_td_scorers, 
    get_player_season_stats, 
    calculate_defense_rankings,
    get_red_zone_stats,
    get_opening_drive_stats,
    identify_funnel_defenses,
    calculate_fair_odds,
    calculate_kelly_criterion
)
from nfl_core.config import API_KEY
import polars as pl


@api_bp.route('/analysis', methods=['GET'])
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


@api_bp.route('/best-bets', methods=['GET'])
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
