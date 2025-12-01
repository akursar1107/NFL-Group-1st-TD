"""
Analysis API endpoints - Best bets, player analysis, data import
"""
from flask import request, jsonify
from datetime import datetime
from marshmallow import ValidationError
from . import api_bp
from ...data_loader import load_data_with_cache_web
from ...routes import get_nfl_stats_data
from ...odds_fetcher import get_odds_api_event_ids_for_season, fetch_odds_data, get_best_odds_for_game
from ...validators import ImportDataSchema
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
    """
    API ENDPOINT - Used by React app at localhost:3000
    
    ⚠️ Returns JSON data, NOT HTML
    ⚠️ Percentages returned as numbers (91.7), not decimals (0.917)
    
    React component should display as: {value}% (NOT {value * 100}%)
    """
    season = request.args.get('season', 2025, type=int)
    try:
        stats_data = get_nfl_stats_data(season, use_cache=True)
        player_database = []
        roster_df = stats_data['roster_df']
        player_stats_full = stats_data['player_stats_full']
        player_stats_recent = stats_data['player_stats_recent']
        first_td_map = stats_data['first_td_map']
        schedule_df = stats_data['schedule_df']
        defense_rankings = stats_data['defense_rankings']
        rz_stats = stats_data['rz_stats']
        od_stats = stats_data['od_stats']
        team_rz_splits = stats_data['team_rz_splits']
        funnel_defenses = stats_data['funnel_defenses']
        
        # Build player database
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
            
            # Get RZ and OD stats
            rz_info = rz_stats.get(player_name, {})
            od_info = od_stats.get(player_name, {})
            rz_rate = round((rz_info.get('rz_tds', 0) / rz_info.get('rz_opps', 1) * 100), 1) if rz_info.get('rz_opps', 0) > 0 else 0
            od_rate = round((od_info.get('od_tds', 0) / od_info.get('od_opps', 1) * 100), 1) if od_info.get('od_opps', 0) > 0 else 0
            
            player_database.append({
                'name': player_name,
                'position': position,
                'team': team,
                'stats_full': stats_full,
                'stats_recent': stats_recent,
                'rz_rate': rz_rate,
                'rz_tds': rz_info.get('rz_tds', 0),
                'rz_opps': rz_info.get('rz_opps', 0),
                'od_rate': od_rate,
                'od_tds': od_info.get('od_tds', 0),
                'od_opps': od_info.get('od_opps', 0)
            })
        
        # Build team data with home/away splits
        team_data = []
        team_ftd_counts = {}
        team_home_ftd = {}
        team_away_ftd = {}
        team_games = {}
        team_home_games = {}
        team_away_games = {}
        
        for ftd_info in first_td_map.values():
            team = ftd_info.get('team')
            is_home = ftd_info.get('is_home_game', False)
            if team:
                team_ftd_counts[team] = team_ftd_counts.get(team, 0) + 1
                if is_home:
                    team_home_ftd[team] = team_home_ftd.get(team, 0) + 1
                else:
                    team_away_ftd[team] = team_away_ftd.get(team, 0) + 1
        
        # Count only completed games (those with first TD data)
        completed_game_ids = set(first_td_map.keys())
        if schedule_df is not None and schedule_df.height > 0:
            # Filter to only completed games
            completed_schedule = schedule_df.filter(schedule_df['game_id'].is_in(list(completed_game_ids)))
            for game_dict in completed_schedule.to_dicts():
                home = game_dict.get('home_team')
                away = game_dict.get('away_team')
                if home:
                    team_games[home] = team_games.get(home, 0) + 1
                    team_home_games[home] = team_home_games.get(home, 0) + 1
                if away:
                    team_games[away] = team_games.get(away, 0) + 1
                    team_away_games[away] = team_away_games.get(away, 0) + 1
        
        for team in team_games.keys():
            ftds = team_ftd_counts.get(team, 0)
            games = team_games.get(team, 0)
            home_ftds = team_home_ftd.get(team, 0)
            away_ftds = team_away_ftd.get(team, 0)
            home_games = team_home_games.get(team, 0)
            away_games = team_away_games.get(team, 0)
            
            success_pct = round((ftds / games * 100), 1) if games > 0 else 0
            home_ftd_pct = round((home_ftds / home_games * 100), 1) if home_games > 0 else 0
            away_ftd_pct = round((away_ftds / away_games * 100), 1) if away_games > 0 else 0
            ha_diff = round(home_ftd_pct - away_ftd_pct, 1)
            
            # Get team RZ splits
            rz_split = team_rz_splits.get(team, {})
            rz_pass_pct = round(rz_split.get('pass_pct', 0), 1)
            rz_run_pct = round(rz_split.get('run_pct', 0), 1)
            
            team_data.append({
                'team': team,
                'games': games,
                'first_tds': ftds,
                'success_pct': success_pct,
                'home_ftd_pct': home_ftd_pct,
                'away_ftd_pct': away_ftd_pct,
                'ha_diff': ha_diff,
                'rz_pass_pct': rz_pass_pct,
                'rz_run_pct': rz_run_pct
            })
        
        team_data.sort(key=lambda x: x['success_pct'], reverse=True)
        
        # Calculate defense stats (counts of TDs allowed by position)
        defense_stats = {}
        all_teams = set(schedule_df["home_team"].unique().to_list() + schedule_df["away_team"].unique().to_list())
        for t in all_teams:
            defense_stats[t] = {'WR': 0, 'RB': 0, 'TE': 0, 'QB': 0, 'Other': 0, 'Total': 0}
        
        games_df = schedule_df.filter(pl.col("game_id").is_in(list(first_td_map.keys())))
        game_map = {row['game_id']: {'home': row['home_team'], 'away': row['away_team']} for row in games_df.select(['game_id', 'home_team', 'away_team']).to_dicts()}
        
        for game_id, data in first_td_map.items():
            if game_id not in game_map: continue
            
            scorer_team = data['team']
            player_id = data.get('player_id')
            player_name = data['player']
            
            game_info = game_map[game_id]
            if scorer_team == game_info['home']: defense_team = game_info['away']
            elif scorer_team == game_info['away']: defense_team = game_info['home']
            else: continue
            
            # Get position
            pos = 'Other'
            if roster_df is not None and roster_df.height > 0:
                if player_id:
                    player_rows = roster_df.filter(roster_df['gsis_id'] == player_id)
                    if player_rows.height > 0 and 'position' in player_rows.columns:
                        pos = player_rows[0, 'position'] or 'Other'
                if pos == 'Other' and player_name:
                    player_rows = roster_df.filter(roster_df['full_name'].str.to_lowercase() == player_name.lower())
                    if player_rows.height > 0 and 'position' in player_rows.columns:
                        pos = player_rows[0, 'position'] or 'Other'
            
            if pos not in ['WR', 'RB', 'TE', 'QB']: pos = 'Other'
            
            if defense_team in defense_stats:
                defense_stats[defense_team][pos] += 1
                defense_stats[defense_team]['Total'] += 1
        
        # Build defense data as array with correct field names
        defense_data = []
        for team, rankings in defense_rankings.items():
            # Calculate average rank
            ranks = [rankings.get('QB', 0), rankings.get('RB', 0), rankings.get('WR', 0), rankings.get('TE', 0)]
            avg_rank = round(sum(r for r in ranks if r > 0) / len([r for r in ranks if r > 0]), 1) if any(r > 0 for r in ranks) else 0
            
            defense_data.append({
                'defense': team,
                'qb_rank': rankings.get('QB', 0),
                'rb_rank': rankings.get('RB', 0),
                'wr_rank': rankings.get('WR', 0),
                'te_rank': rankings.get('TE', 0),
                'avg_rank': avg_rank,
                'funnel_type': funnel_defenses.get(team, 'Balanced'),
                'ftds_allowed': defense_stats.get(team, {}),
            })
        
        # Build trends data
        hot_players = []
        for player_name, stats_recent in player_stats_recent.items():
            if stats_recent.get('first_tds', 0) >= 2 and stats_recent.get('team_games', 0) >= 3:
                position = None
                team = None
                if roster_df is not None and roster_df.height > 0:
                    player_rows = roster_df.filter(roster_df['full_name'].str.to_lowercase() == player_name.lower())
                    if player_rows.height > 0:
                        team = player_rows[0, 'team'] if 'team' in player_rows.columns else None
                        position = player_rows[0, 'position'] if 'position' in player_rows.columns else None
                
                hot_players.append({
                    'name': player_name,
                    'team': team,
                    'position': position,
                    'first_tds': stats_recent['first_tds']
                })
        
        hot_players.sort(key=lambda x: x['first_tds'], reverse=True)
        
        weekly_scorers = []
        if schedule_df is not None and schedule_df.height > 0:
            for ftd_info in first_td_map.values():
                game_id = ftd_info.get('game_id')
                if game_id:
                    game_rows = schedule_df.filter(pl.col('game_id') == game_id)
                    if game_rows.height > 0:
                        week = game_rows[0, 'week'] if 'week' in game_rows.columns else None
                        weekly_scorers.append({
                            'week': week,
                            'player': ftd_info.get('player'),
                            'team': ftd_info.get('team'),
                            'position': ftd_info.get('position')
                        })
        
        trends_data = {
            'hot_players': hot_players[:10],
            'weekly_scorers': weekly_scorers
        }
        
        # Build history data
        history_results = []
        all_teams = set()
        
        for game_id, ftd_info in first_td_map.items():
            game_rows = schedule_df.filter(pl.col('game_id') == game_id)
            if game_rows.height > 0:
                week = game_rows[0, 'week'] if 'week' in game_rows.columns else None
                home_team = game_rows[0, 'home_team'] if 'home_team' in game_rows.columns else None
                away_team = game_rows[0, 'away_team'] if 'away_team' in game_rows.columns else None
                game_date = game_rows[0, 'gameday'] if 'gameday' in game_rows.columns else None
                game_time = game_rows[0, 'gametime'] if 'gametime' in game_rows.columns else None
                
                player = ftd_info.get('player')
                team = ftd_info.get('team')
                
                if team:
                    all_teams.add(team)
                
                # Determine if home or away and opponent
                is_home = team == home_team
                opponent = away_team if is_home else home_team
                
                # Determine if standalone based on gameday
                is_standalone = False
                if game_date:
                    try:
                        from datetime import datetime as dt_parser
                        game_datetime = dt_parser.strptime(str(game_date), '%Y-%m-%d')
                        day_of_week = game_datetime.weekday()  # 0=Monday, 6=Sunday
                        
                        # Standalone is any game that isn't Sunday afternoon
                        if day_of_week != 6:
                            # Mon-Sat games are all standalone
                            is_standalone = True
                        elif day_of_week == 6 and game_time:
                            # Sunday games - check time
                            hour = int(str(game_time).split(':')[0]) if ':' in str(game_time) else 0
                            # SNF (8:20 PM or later) is standalone
                            if hour >= 20:
                                is_standalone = True
                    except:
                        pass
                
                # Get position from roster
                position = None
                player_id = ftd_info.get('player_id')
                if roster_df is not None and roster_df.height > 0:
                    if player_id:
                        player_rows = roster_df.filter(roster_df['gsis_id'] == player_id)
                        if player_rows.height > 0:
                            position = player_rows[0, 'position'] if 'position' in player_rows.columns else None
                    if not position and player:
                        player_rows = roster_df.filter(roster_df['full_name'].str.to_lowercase() == player.lower())
                        if player_rows.height > 0:
                            position = player_rows[0, 'position'] if 'position' in player_rows.columns else None
                
                history_results.append({
                    'season': season,
                    'week': week,
                    'team': team,
                    'player': player,
                    'position': position,
                    'opponent': opponent,
                    'is_home': is_home,
                    'game_date': str(game_date) if game_date else None,
                    'is_standalone': is_standalone
                })
        
        history_data = {
            'results': history_results,
            'teams': sorted(list(all_teams))
        }
        
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
    
    # Validate input
    schema = ImportDataSchema()
    try:
        validated_data = schema.load(data)
    except ValidationError as err:
        return jsonify({'error': 'Validation failed', 'details': err.messages}), 400
    
    season = validated_data['season']
    
    try:
        # Load parquet data
        schedule_df, pbp_df, roster_df = load_data_with_cache_web(season, use_cache=False)
        
        # Import games into database
        from ...models import Game
        from ... import db
        from datetime import datetime
        
        games_added = 0
        games_updated = 0
        
        for game_dict in schedule_df.to_dicts():
            game_id = game_dict.get('game_id')
            if not game_id:
                continue
            
            # Check if game exists
            existing_game = Game.query.filter_by(game_id=game_id).first()
            
            # Parse date and time
            gameday_str = game_dict.get('gameday', '')
            gametime_str = game_dict.get('gametime', '')
            
            try:
                game_date = datetime.strptime(str(gameday_str), '%Y-%m-%d').date() if gameday_str else None
            except:
                game_date = None
            
            try:
                game_time = datetime.strptime(str(gametime_str), '%H:%M').time() if gametime_str and ':' in str(gametime_str) else None
            except:
                game_time = None
            
            # Determine if standalone
            is_standalone = False
            if game_date:
                day_of_week = game_date.weekday()  # 0=Monday, 6=Sunday
                if day_of_week != 6:  # Not Sunday
                    is_standalone = True
                elif day_of_week == 6 and game_time:  # Sunday
                    # SNF starts at 20:00 or later
                    if game_time.hour >= 20:
                        is_standalone = True
            
            if existing_game:
                # Update existing game
                existing_game.season = game_dict.get('season', season)
                existing_game.week = game_dict.get('week')
                existing_game.gameday = game_dict.get('gameday')
                existing_game.game_date = game_date
                existing_game.game_time = game_time
                existing_game.home_team = game_dict.get('home_team')
                existing_game.away_team = game_dict.get('away_team')
                existing_game.is_standalone = is_standalone
                games_updated += 1
            else:
                # Create new game
                new_game = Game(
                    game_id=game_id,
                    season=game_dict.get('season', season),
                    week=game_dict.get('week'),
                    gameday=game_dict.get('gameday'),
                    game_date=game_date,
                    game_time=game_time,
                    home_team=game_dict.get('home_team'),
                    away_team=game_dict.get('away_team'),
                    is_standalone=is_standalone
                )
                db.session.add(new_game)
                games_added += 1
        
        db.session.commit()
        
        return jsonify({ 
            'message': f'Data import for season {season} successful. Added {games_added} games, updated {games_updated} games.' 
        }), 200
    except Exception as e:
        db.session.rollback()
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
