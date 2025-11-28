from flask import Blueprint, render_template, jsonify, redirect, url_for, flash, request
from .models import User, Game, Pick
from . import db, cache
from sqlalchemy import func, case
from nfl_core.stats import (
    get_first_td_scorers, 
    get_player_season_stats, 
    calculate_defense_rankings,
    get_red_zone_stats,
    get_opening_drive_stats,
    get_team_red_zone_splits,
    identify_funnel_defenses,
    calculate_fair_odds,
    get_player_position,
    calculate_kelly_criterion
)
from nfl_core.config import API_KEY, MARKET_1ST_TD
from datetime import datetime
from .data_loader import load_data_with_cache_web, get_current_nfl_week, get_all_td_scorers
from .odds_fetcher import get_odds_api_event_ids_for_season, fetch_odds_data, get_best_odds_for_game
import polars as pl

bp = Blueprint('main', __name__)

# Shared helper function for loading NFL statistics
def get_nfl_stats_data(season=2025, use_cache=True):
    """
    Load NFL data and calculate all statistics. Returns a dictionary with:
    - schedule_df, pbp_df, roster_df: raw DataFrames
    - first_td_map: {game_id: {player, team, player_id}}
    - player_stats: {player_name: {prob, first_tds, team_games, player_id}}
    - defense_rankings: {team: {position: rank}}
    - funnel_defenses: {team: 'Pass Funnel'/'Run Funnel'/None}
    - rz_stats: {player: {rz_opps, rz_tds}}
    - od_stats: {player: {od_opps, od_tds}}
    - team_rz_splits: {team: {pass_pct, run_pct, total_plays}}
    """
    # Load data
    schedule_df, pbp_df, roster_df = load_data_with_cache_web(season, use_cache=use_cache)
    
    # Get valid game IDs for this season only
    season_game_ids = schedule_df.select(pl.col('game_id')).to_series().to_list()
    
    # Calculate statistics
    first_td_map = get_first_td_scorers(pbp_df, target_game_ids=season_game_ids, roster_df=roster_df)
    player_stats_recent = get_player_season_stats(schedule_df, first_td_map, last_n_games=5)  # For Recent Form
    player_stats_full = get_player_season_stats(schedule_df, first_td_map, last_n_games=None)  # For full season data
    defense_rankings = calculate_defense_rankings(schedule_df, first_td_map, roster_df)
    funnel_defenses = identify_funnel_defenses(defense_rankings) or {}
    rz_stats = get_red_zone_stats(pbp_df, roster_df) or {}
    od_stats = get_opening_drive_stats(pbp_df, roster_df) or {}
    team_rz_splits = get_team_red_zone_splits(pbp_df) or {}
    
    return {
        'schedule_df': schedule_df,
        'pbp_df': pbp_df,
        'roster_df': roster_df,
        'first_td_map': first_td_map,
        'player_stats_recent': player_stats_recent,
        'player_stats_full': player_stats_full,
        'defense_rankings': defense_rankings,
        'funnel_defenses': funnel_defenses,
        'rz_stats': rz_stats,
        'od_stats': od_stats,
        'team_rz_splits': team_rz_splits
    }

@bp.route('/')
@bp.route('/season/<int:season>')
@cache.cached(timeout=300, query_string=True)
def index(season=None):
    """Home page - show current standings"""
    # Default to current season if not specified
    if season is None:
        season = 2025
    
    # Get all available seasons
    available_seasons = db.session.query(Game.season).distinct().order_by(Game.season.desc()).all()
    available_seasons = [s[0] for s in available_seasons]
    
    # Optimized query: calculate all stats in one database query per pick type
    # FTD stats
    ftd_stats = db.session.query(
        Pick.user_id,
        func.count(case((Pick.result == 'W', 1))).label('wins'),
        func.count(case((Pick.result == 'L', 1))).label('losses'),
        func.count(case((Pick.result == 'Pending', 1))).label('pending'),
        func.sum(Pick.payout).label('bankroll'),
        func.count(Pick.id).label('total')
    ).join(Game).filter(
        Pick.pick_type == 'FTD',
        Game.season == season
    ).group_by(Pick.user_id).all()
    
    # ATTS stats
    atts_stats = db.session.query(
        Pick.user_id,
        func.count(case((Pick.result == 'W', 1))).label('wins'),
        func.count(case((Pick.result == 'L', 1))).label('losses'),
        func.count(case((Pick.result == 'Pending', 1))).label('pending'),
        func.sum(Pick.payout).label('bankroll'),
        func.count(Pick.id).label('total')
    ).join(Game).filter(
        Pick.pick_type == 'ATTS',
        Game.season == season
    ).group_by(Pick.user_id).all()
    
    # Convert to dictionaries for easy lookup
    ftd_dict = {s.user_id: s for s in ftd_stats}
    atts_dict = {s.user_id: s for s in atts_stats}
    
    # Build standings
    users = User.query.filter_by(is_active=True).all()
    standings = []
    for user in users:
        ftd = ftd_dict.get(user.id)
        atts = atts_dict.get(user.id)
        
        standings.append({
            'user': user,
            'ftd_wins': ftd.wins if ftd else 0,
            'ftd_losses': ftd.losses if ftd else 0,
            'ftd_pending': ftd.pending if ftd else 0,
            'ftd_bankroll': float(ftd.bankroll) if ftd and ftd.bankroll else 0.0,
            'atts_wins': atts.wins if atts else 0,
            'atts_losses': atts.losses if atts else 0,
            'atts_pending': atts.pending if atts else 0,
            'atts_bankroll': float(atts.bankroll) if atts and atts.bankroll else 0.0,
            'total_picks': (ftd.total if ftd else 0) + (atts.total if atts else 0)
        })
    
    # Sort by FTD bankroll (descending)
    standings.sort(key=lambda x: x['ftd_bankroll'], reverse=True)
    
    return render_template('index.html', 
                         standings=standings, 
                         season=season, 
                         available_seasons=available_seasons)

@bp.route('/week/<int:week_num>')
@bp.route('/season/<int:season>/week/<int:week_num>')
def week_view(week_num, season=None):
    """Display all games and picks for a specific week"""
    # Default to current season if not specified
    if season is None:
        season = 2025
    
    # Get all games for this week and season
    games = Game.query.filter_by(week=week_num, season=season).order_by(Game.game_date, Game.game_time).all()
    
    if not games:
        return render_template('week.html', week=week_num, season=season, games=[], message="No games found for this week")
    
    # Build game data with picks
    games_data = []
    for game in games:
        picks = Pick.query.filter_by(game_id=game.id, pick_type='FTD').all()
        
        game_info = {
            'game': game,
            'picks': picks,
            'matchup': f"{game.away_team} @ {game.home_team}",
            'date': game.game_date.strftime('%a %m/%d') if game.game_date else 'TBD',
            'time': game.game_time.strftime('%I:%M %p') if game.game_time else '',
            'is_final': game.is_final,
            'actual_scorer': game.actual_first_td_player
        }
        games_data.append(game_info)
    
    # Get all weeks that have games for this season
    all_weeks = db.session.query(Game.week).filter_by(season=season).distinct().order_by(Game.week).all()
    available_weeks = [w[0] for w in all_weeks]
    
    return render_template('week.html', 
                         week=week_num,
                         season=season,
                         games=games_data,
                         available_weeks=available_weeks)

@bp.route('/admin/grade/<int:week_num>', methods=['POST'])
def grade_week_route(week_num):
    """Admin route to grade a specific week"""
    from flask import request
    
    # Get season from form or default to 2025
    season_str = request.form.get('season', '2025')
    season = int(season_str) if season_str and season_str.strip() else 2025
    
    try:
        # Determine if we should use cached data
        current_week = get_current_nfl_week(season)
        use_cache = (week_num < current_week)  # Use cache for past weeks, fresh data for current week
        
        # Load NFL data
        schedule_df, pbp_df, roster_df = load_data_with_cache_web(season, use_cache=use_cache)
        
        # Get games for this week
        games = Game.query.filter_by(week=week_num, season=season).all()
        
        if not games:
            flash(f'No games found for Week {week_num} in {season} season', 'warning')
            return redirect(url_for('main.week_view', week_num=week_num, season=season))
        
        game_ids = [g.game_id for g in games]
        
        # Get first TD scorers
        first_td_map = get_first_td_scorers(pbp_df, target_game_ids=game_ids, roster_df=roster_df)
        
        if not first_td_map:
            flash('No first TD data found. Games may not have been played yet.', 'warning')
            return redirect(url_for('main.week_view', week_num=week_num, season=season))
        
        games_graded = 0
        picks_graded = 0
        picks_won = 0
        picks_lost = 0
        
        for game in games:
            if game.game_id not in first_td_map:
                continue
            
            td_data = first_td_map[game.game_id]
            actual_player = td_data.get('player', '').strip()
            
            if not actual_player:
                continue
            
            # Update game
            game.actual_first_td_player = actual_player
            game.actual_first_td_team = td_data.get('team', '')
            game.actual_first_td_player_id = td_data.get('player_id')
            game.is_final = True
            
            # Grade picks
            picks = Pick.query.filter_by(game_id=game.id, pick_type='FTD').all()
            
            for pick in picks:
                if pick.graded_at:
                    continue
                
                pick_player = pick.player_name.strip()
                
                # Fuzzy match
                is_winner = False
                if pick_player.lower() == actual_player.lower():
                    is_winner = True
                elif pick_player.lower() in actual_player.lower() or actual_player.lower() in pick_player.lower():
                    if len(pick_player) > 3 and len(actual_player) > 3:
                        is_winner = True
                
                if is_winner:
                    pick.result = 'W'
                    pick.payout = pick.calculate_payout()
                    picks_won += 1
                else:
                    pick.result = 'L'
                    pick.payout = -pick.stake
                    picks_lost += 1
                
                pick.graded_at = datetime.utcnow()
                picks_graded += 1
            
            games_graded += 1
        
        # === ATTS (Anytime TD Scorer) Grading ===
        atts_picks_graded = 0
        atts_picks_won = 0
        atts_picks_lost = 0
        
        # Get all TD scorers for the week
        all_td_map = get_all_td_scorers(pbp_df, target_game_ids=game_ids, roster_df=roster_df)
        
        if all_td_map:
            for game in games:
                if game.game_id not in all_td_map:
                    continue
                
                td_scorers = all_td_map[game.game_id]  # List of {'player', 'team', 'player_id'}
                
                if not td_scorers:
                    continue
                
                # Grade ATTS picks for this game
                atts_picks = Pick.query.filter_by(game_id=game.id, pick_type='ATTS').all()
                
                for pick in atts_picks:
                    if pick.graded_at:
                        continue
                    
                    pick_player = pick.player_name.strip()
                    
                    # Check if pick_player matches ANY TD scorer (fuzzy match)
                    is_winner = False
                    for scorer_data in td_scorers:
                        actual_player = scorer_data.get('player', '').strip()
                        
                        if not actual_player:
                            continue
                        
                        # Fuzzy match logic (same as FTD)
                        if pick_player.lower() == actual_player.lower():
                            is_winner = True
                            break
                        elif pick_player.lower() in actual_player.lower() or actual_player.lower() in pick_player.lower():
                            if len(pick_player) > 3 and len(actual_player) > 3:
                                is_winner = True
                                break
                    
                    if is_winner:
                        pick.result = 'W'
                        pick.payout = pick.calculate_payout()
                        atts_picks_won += 1
                    else:
                        pick.result = 'L'
                        pick.payout = -pick.stake
                        atts_picks_lost += 1
                    
                    pick.graded_at = datetime.utcnow()
                    atts_picks_graded += 1
        
        db.session.commit()
        
        # Combined flash message
        total_graded = picks_graded + atts_picks_graded
        total_won = picks_won + atts_picks_won
        total_lost = picks_lost + atts_picks_lost
        
        flash(f'Graded {total_graded} picks across {games_graded} games: {total_won} wins, {total_lost} losses (FTD: {picks_graded}, ATTS: {atts_picks_graded})', 'success')
        
    except Exception as e:
        flash(f'Error grading week: {str(e)}', 'danger')
    
    return redirect(url_for('main.week_view', week_num=week_num, season=season))

@bp.route('/admin/grade-current-week', methods=['POST'])
def grade_current_week():
    """Admin route to quickly grade the current week (or most recent week with pending picks)"""
    season = 2025
    current_week = get_current_nfl_week(season)
    
    # Start with the previous week (current week - 1) as the default week to grade
    week_to_grade = current_week - 1
    
    # But check if there are pending picks for that week
    pending_count = Pick.query.join(Game).filter(
        Game.week == week_to_grade,
        Game.season == season,
        Pick.result == 'Pending'
    ).count()
    
    # If no pending picks for previous week, find the most recent week with pending picks
    if pending_count == 0:
        # Get all weeks with pending picks, ordered descending
        weeks_with_pending = db.session.query(Game.week).join(Pick).filter(
            Game.season == season,
            Pick.result == 'Pending'
        ).distinct().order_by(Game.week.desc()).all()
        
        if not weeks_with_pending:
            flash('No pending picks to grade for this season', 'warning')
            return redirect(url_for('main.index'))
        
        week_to_grade = weeks_with_pending[0][0]
    
    if week_to_grade < 1:
        flash('No week available to grade yet', 'warning')
        return redirect(url_for('main.index'))
    
    try:
        # Load data - use fresh data for current grading
        schedule_df, pbp_df, roster_df = load_data_with_cache_web(season, use_cache=False)
        
        # Get all games for the week to grade
        games = Game.query.filter_by(week=week_to_grade, season=season).all()
        
        if not games:
            flash(f'No games found for Week {week_to_grade}', 'warning')
            return redirect(url_for('main.index'))
        
        game_ids = [g.game_id for g in games]
        
        # Get first TD scorers for these games
        first_td_map = get_first_td_scorers(pbp_df, target_game_ids=game_ids, roster_df=roster_df)
        
        # Get all ATTS TD scorers for these games
        all_td_scorers = get_all_td_scorers(pbp_df, target_game_ids=game_ids, roster_df=roster_df)
        
        if not first_td_map and not all_td_scorers:
            flash(f'No TD data available for Week {week_to_grade}. Games may not be complete yet.', 'warning')
            return redirect(url_for('main.index'))
        
        total_picks_graded = 0
        total_picks_won = 0
        total_picks_lost = 0
        
        for game in games:
            # Grade FTD picks
            if game.game_id in first_td_map:
                td_data = first_td_map[game.game_id]
                actual_player = td_data.get('player', '').strip()
                
                pending_ftd_picks = Pick.query.filter_by(
                    game_id=game.id,
                    pick_type='FTD',
                    result='Pending'
                ).all()
                
                for pick in pending_ftd_picks:
                    if not actual_player or actual_player.lower() == 'none':
                        pick.result = 'L'
                        pick.payout = -pick.stake
                        total_picks_lost += 1
                    elif actual_player.lower() == pick.player_name.lower():
                        pick.result = 'W'
                        pick.payout = (pick.stake * pick.odds / 100) if pick.odds > 0 else (pick.stake * 100 / abs(pick.odds))
                        total_picks_won += 1
                    else:
                        pick.result = 'L'
                        pick.payout = -pick.stake
                        total_picks_lost += 1
                    total_picks_graded += 1
            
            # Grade ATTS picks
            if game.game_id in all_td_scorers:
                td_scorers = all_td_scorers[game.game_id]
                td_scorer_names = [s['player'].lower() for s in td_scorers]
                
                pending_atts_picks = Pick.query.filter_by(
                    game_id=game.id,
                    pick_type='ATTS',
                    result='Pending'
                ).all()
                
                for pick in pending_atts_picks:
                    if pick.player_name.lower() in td_scorer_names:
                        pick.result = 'W'
                        pick.payout = (pick.stake * pick.odds / 100) if pick.odds > 0 else (pick.stake * 100 / abs(pick.odds))
                        total_picks_won += 1
                    else:
                        pick.result = 'L'
                        pick.payout = -pick.stake
                        total_picks_lost += 1
                    total_picks_graded += 1
        
        db.session.commit()
        
        if total_picks_graded > 0:
            flash(f'✓ Week {week_to_grade} graded: {total_picks_graded} picks ({total_picks_won}W-{total_picks_lost}L)', 'success')
        else:
            flash(f'No picks graded for Week {week_to_grade}. Games may not be complete yet.', 'warning')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error grading week: {str(e)}', 'danger')
    
    return redirect(url_for('main.index'))

@bp.route('/admin/grade-all', methods=['POST'])
def grade_all_weeks():
    """Admin route to grade all weeks at once"""
    from flask import request
    
    # Get season from form or default to 2025
    season_str = request.form.get('season', '2025')
    season = int(season_str) if season_str and season_str.strip() else 2025
    
    try:
        # Always use cached data for bulk grading (more efficient)
        schedule_df, pbp_df, roster_df = load_data_with_cache_web(season, use_cache=True)
        
        # Get all games
        all_games = Game.query.filter_by(season=season).all()
        
        if not all_games:
            flash('No games found to grade', 'warning')
            return redirect(url_for('main.index'))
        
        game_ids = [g.game_id for g in all_games]
        
        # Get first TD scorers for all games
        first_td_map = get_first_td_scorers(pbp_df, target_game_ids=game_ids, roster_df=roster_df)
        
        if not first_td_map:
            flash('No first TD data found. Games may not have been played yet.', 'warning')
            return redirect(url_for('main.index'))
        
        total_games_graded = 0
        total_picks_graded = 0
        total_picks_won = 0
        total_picks_lost = 0
        weeks_graded = set()
        
        for game in all_games:
            if game.game_id not in first_td_map:
                continue
            
            td_data = first_td_map[game.game_id]
            actual_player = td_data.get('player', '').strip()
            
            if not actual_player:
                continue
            
            # Update game
            game.actual_first_td_player = actual_player
            game.actual_first_td_team = td_data.get('team', '')
            game.actual_first_td_player_id = td_data.get('player_id')
            game.is_final = True
            
            # Grade picks
            picks = Pick.query.filter_by(game_id=game.id, pick_type='FTD').all()
            
            for pick in picks:
                if pick.graded_at:
                    continue
                
                pick_player = pick.player_name.strip()
                
                # Fuzzy match
                is_winner = False
                if pick_player.lower() == actual_player.lower():
                    is_winner = True
                elif pick_player.lower() in actual_player.lower() or actual_player.lower() in pick_player.lower():
                    if len(pick_player) > 3 and len(actual_player) > 3:
                        is_winner = True
                
                if is_winner:
                    pick.result = 'W'
                    pick.payout = pick.calculate_payout()
                    total_picks_won += 1
                else:
                    pick.result = 'L'
                    pick.payout = -pick.stake
                    total_picks_lost += 1
                
                pick.graded_at = datetime.utcnow()
                total_picks_graded += 1
            
            total_games_graded += 1
            weeks_graded.add(game.week)
        
        db.session.commit()
        
        flash(f'Graded all weeks! {total_picks_graded} picks across {total_games_graded} games in {len(weeks_graded)} weeks: {total_picks_won} wins, {total_picks_lost} losses', 'success')
        
    except Exception as e:
        flash(f'Error grading all weeks: {str(e)}', 'danger')
    
    return redirect(url_for('main.index'))

@bp.route('/user/<int:user_id>')
@bp.route('/season/<int:season>/user/<int:user_id>')
def user_detail(user_id, season=None):
    """Display all picks for a specific user"""
    # Default to current season if not specified
    if season is None:
        season = 2025
    
    user = User.query.get_or_404(user_id)
    
    # Get all picks for this user in this season
    picks = Pick.query.filter_by(user_id=user.id).join(Game).filter(
        Game.season == season
    ).order_by(Game.week, Game.game_date, Game.game_time).all()
    
    # Group picks by week
    picks_by_week = {}
    for pick in picks:
        week = pick.game.week
        if week not in picks_by_week:
            picks_by_week[week] = []
        picks_by_week[week].append(pick)
    
    # Calculate user stats
    ftd_picks = [p for p in picks if p.pick_type == 'FTD']
    ftd_wins = sum(1 for p in ftd_picks if p.result == 'W')
    ftd_losses = sum(1 for p in ftd_picks if p.result == 'L')
    ftd_pending = sum(1 for p in ftd_picks if p.result == 'Pending')
    ftd_bankroll = sum(p.payout for p in ftd_picks if p.payout)
    
    atts_picks = [p for p in picks if p.pick_type == 'ATTS']
    atts_wins = sum(1 for p in atts_picks if p.result == 'W')
    atts_losses = sum(1 for p in atts_picks if p.result == 'L')
    atts_pending = sum(1 for p in atts_picks if p.result == 'Pending')
    atts_bankroll = sum(p.payout for p in atts_picks if p.payout)
    
    stats = {
        'ftd_wins': ftd_wins,
        'ftd_losses': ftd_losses,
        'ftd_pending': ftd_pending,
        'ftd_bankroll': ftd_bankroll,
        'ftd_win_rate': (ftd_wins / (ftd_wins + ftd_losses) * 100) if (ftd_wins + ftd_losses) > 0 else 0,
        'atts_wins': atts_wins,
        'atts_losses': atts_losses,
        'atts_pending': atts_pending,
        'atts_bankroll': atts_bankroll,
        'atts_win_rate': (atts_wins / (atts_wins + atts_losses) * 100) if (atts_wins + atts_losses) > 0 else 0,
        'total_picks': len(picks)
    }
    
    return render_template('user_detail.html', 
                         user=user, 
                         picks_by_week=picks_by_week, 
                         stats=stats,
                         season=season)

@bp.route('/admin/picks/new', methods=['GET', 'POST'])
def new_pick():
    """Admin page to add new picks"""
    from flask import request
    
    if request.method == 'POST':
        try:
            # Get form data
            user_id = request.form.get('user_id')
            game_id = request.form.get('game_id')
            player_name = request.form.get('player_name', '').strip()
            pick_type = request.form.get('pick_type', 'FTD')
            odds = request.form.get('odds')
            stake = request.form.get('stake', 1.0)
            
            # Validation
            if not all([user_id, game_id, player_name, odds]):
                flash('All fields are required', 'danger')
                return redirect(url_for('main.new_pick'))
            
            # Check for duplicate pick
            existing_pick = Pick.query.filter_by(
                user_id=int(user_id),
                game_id=int(game_id),
                pick_type=pick_type
            ).first()
            
            if existing_pick:
                flash(f'Pick already exists for this user/game/type. Edit or delete the existing pick instead.', 'warning')
                return redirect(url_for('main.new_pick'))
            
            # Get game to extract season
            game = Game.query.get(int(game_id))
            if not game:
                flash('Invalid game selected', 'danger')
                return redirect(url_for('main.new_pick'))
            
            # Look up player position from roster (optional)
            player_position = None
            try:
                schedule_df, pbp_df, roster_df = load_data_with_cache_web(game.season, use_cache=True)
                
                # Search roster for player
                if 'full_name' in roster_df.columns and 'position' in roster_df.columns:
                    player_lower = player_name.lower()
                    for row in roster_df.to_dicts():
                        roster_name = str(row.get('full_name', '')).lower()
                        if player_lower in roster_name or roster_name in player_lower:
                            if len(player_lower) > 3 and len(roster_name) > 3:
                                player_position = row.get('position')
                                break
            except Exception as e:
                print(f"Warning: Could not look up player position: {e}")
            
            # Create new pick
            new_pick = Pick(
                user_id=int(user_id),
                game_id=int(game_id),
                pick_type=pick_type,
                player_name=player_name,
                player_position=player_position or 'UNK',
                odds=int(odds),
                stake=float(stake),
                result='Pending',
                payout=0.0
            )
            
            db.session.add(new_pick)
            db.session.commit()
            
            user = User.query.get(int(user_id))
            odds_int = int(odds)
            odds_display = f'+{odds_int}' if odds_int > 0 else str(odds_int)
            flash(f'✓ Added {pick_type} pick: {user.username} - {player_name} ({odds_display}) for Week {game.week}', 'success')
            
            # Check if "Add Another" was clicked
            if request.form.get('add_another'):
                return redirect(url_for('main.new_pick'))
            else:
                return redirect(url_for('main.week_view', week_num=game.week, season=game.season))
                
        except Exception as e:
            flash(f'Error adding pick: {str(e)}', 'danger')
            return redirect(url_for('main.new_pick'))
    
    # GET request - show form
    # Get all users
    users = User.query.filter_by(is_active=True).order_by(User.username).all()
    
    # Get current/upcoming week games
    current_week = get_current_nfl_week(2025)
    season = 2025
    
    # Get standalone games for current week through week 18 (all upcoming)
    # This ensures we show all available games for pick entry
    games = Game.query.filter(
        Game.season == season,
        Game.week >= current_week,
        Game.is_standalone == True
    ).order_by(Game.week, Game.game_date, Game.game_time).all()
    
    return render_template('admin_new_pick.html', 
                         users=users, 
                         games=games,
                         current_week=current_week,
                         season=season)

@bp.route('/admin/picks/<int:pick_id>/edit', methods=['GET', 'POST'])
def edit_pick(pick_id):
    """Admin page to edit an existing pick"""
    from flask import request
    
    pick = Pick.query.get_or_404(pick_id)
    
    if request.method == 'POST':
        try:
            # Get form data
            player_name = request.form.get('player_name', '').strip()
            pick_type = request.form.get('pick_type', 'FTD')
            odds = request.form.get('odds')
            stake = request.form.get('stake', 1.0)
            
            # Validation
            if not all([player_name, odds]):
                flash('Player name and odds are required', 'danger')
                return redirect(url_for('main.edit_pick', pick_id=pick_id))
            
            # Update pick
            pick.player_name = player_name
            pick.pick_type = pick_type
            pick.odds = int(odds)
            pick.stake = float(stake)
            
            # Look up player position
            schedule_df, pbp_df, roster_df = load_data_with_cache_web(2025, use_cache=True)
            if roster_df is not None and not roster_df.empty:
                player_match = roster_df[roster_df['player_display_name'].str.lower() == player_name.lower()]
                if not player_match.empty:
                    pick.player_position = player_match.iloc[0]['position']
            
            db.session.commit()
            
            odds_int = int(odds)
            odds_display = f'+{odds_int}' if odds_int > 0 else str(odds_int)
            flash(f'✓ Updated {pick_type} pick: {pick.user.username} - {player_name} ({odds_display})', 'success')
            
            # Redirect back to the week view
            return redirect(url_for('main.week_view', week_num=pick.game.week, season=pick.game.season))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating pick: {str(e)}', 'danger')
            return redirect(url_for('main.edit_pick', pick_id=pick_id))
    
    # GET request - show edit form
    season = 2025
    current_week = get_current_nfl_week(season)
    
    # Get all users for dropdown
    users = User.query.order_by(User.username).all()
    
    # Get all upcoming standalone games for dropdown
    games = Game.query.filter(
        Game.season == season,
        Game.week >= current_week,
        Game.is_standalone == True
    ).order_by(Game.week, Game.game_date, Game.game_time).all()
    
    return render_template('admin_edit_pick.html', 
                         pick=pick,
                         users=users,
                         games=games,
                         current_week=current_week,
                         season=season)

@bp.route('/admin/picks/<int:pick_id>/delete', methods=['POST'])
def delete_pick(pick_id):
    """Admin route to delete a pick"""
    pick = Pick.query.get_or_404(pick_id)
    week_num = pick.game.week
    season = pick.game.season
    
    try:
        user_name = pick.user.username
        player_name = pick.player_name
        pick_type = pick.pick_type
        
        db.session.delete(pick)
        db.session.commit()
        
        flash(f'✓ Deleted {pick_type} pick: {user_name} - {player_name}', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting pick: {str(e)}', 'danger')
    
    return redirect(url_for('main.week_view', week_num=week_num, season=season))

@bp.route('/best-bets')
@bp.route('/best-bets/<int:season>')
def best_bets_scanner(season=None):
    """
    Best Bets Scanner - Find positive EV first touchdown bets for the current week.
    Public route available to all users.
    """
    # Default to current season
    if season is None:
        season = 2025
    
    # Check if API key is configured
    if not API_KEY:
        flash('Best Bets Scanner requires an Odds API key. Please configure ODDS_API_KEY environment variable.', 'warning')
        return render_template('best_bets.html', 
                             bets=[], 
                             error='API key not configured',
                             season=season,
                             week=None,
                             last_updated=None)
    
    try:
        # Load NFL data
        schedule_df, pbp_df, roster_df = load_data_with_cache_web(season, use_cache=True)
        
        if schedule_df.height == 0:
            return render_template('best_bets.html', 
                                 bets=[], 
                                 error='No schedule data available',
                                 season=season,
                                 week=None,
                                 last_updated=None)
        
        # Get current week
        import polars as pl
        today_str = datetime.now().strftime("%Y-%m-%d")
        future_games = schedule_df.filter(pl.col("gameday") >= today_str)
        
        if future_games.height == 0:
            return render_template('best_bets.html', 
                                 bets=[], 
                                 error='No upcoming games found',
                                 season=season,
                                 week=None,
                                 last_updated=None)
        
        current_week = int(future_games["week"].cast(pl.Int64).min())
        week_games = schedule_df.filter(pl.col("week").cast(pl.Int64) == current_week)
        
        # Calculate statistics (once for all games)
        print(f"Calculating stats for {season} season...")
        first_td_map = get_first_td_scorers(pbp_df, target_game_ids=None, roster_df=roster_df)
        player_stats = get_player_season_stats(schedule_df, first_td_map, last_n_games=5)
        defense_rankings = calculate_defense_rankings(schedule_df, first_td_map, roster_df)
        funnel_defenses = identify_funnel_defenses(defense_rankings) or {}
        rz_stats = get_red_zone_stats(pbp_df, roster_df) or {}
        od_stats = get_opening_drive_stats(pbp_df, roster_df) or {}
        team_rz_splits = get_team_red_zone_splits(pbp_df) or {}
        
        # Get odds API event mappings
        print("Fetching odds event IDs...")
        odds_event_map = get_odds_api_event_ids_for_season(schedule_df, API_KEY)
        
        # Collect all positive EV bets
        all_bets = []
        bankroll = 1000.0  # Default bankroll for Kelly calculations
        
        # Helper function for fuzzy player name matching
        def get_stats(player_name):
            if player_name in player_stats:
                return player_stats[player_name]
            # Fuzzy match
            for k, v in player_stats.items():
                if (k.lower() in player_name.lower() or player_name.lower() in k.lower()) and len(k) > 3 and len(player_name) > 3:
                    return v
            return None
        
        # Process each game
        for game in week_games.to_dicts():
            nfl_game_id = game['game_id']
            home_team = game['home_team']
            away_team = game['away_team']
            game_date = game.get('gameday', '')
            game_time = game.get('gametime', '')
            
            odds_event_id = odds_event_map.get(nfl_game_id)
            if not odds_event_id:
                continue
            
            print(f"Fetching odds for {away_team} @ {home_team}...")
            odds_data = fetch_odds_data(odds_event_id, API_KEY)
            
            if not odds_data:
                continue
            
            # Get best prices across all bookmakers
            best_prices = get_best_odds_for_game(odds_data)
            
            # Calculate EV for each player
            for player, price_data in best_prices.items():
                stats = get_stats(player)
                
                if stats:
                    prob = stats['prob']
                    odds = price_data['price']
                    bookmaker = price_data['bookmaker']
                    
                    # Calculate implied probability from odds
                    if odds > 0:
                        implied_prob = 100 / (odds + 100)
                    else:
                        implied_prob = abs(odds) / (abs(odds) + 100)
                    
                    # Calculate EV
                    ev = prob - implied_prob
                    ev_percent = ev * 100
                    
                    # Only include positive EV bets
                    if ev > 0:
                        # Calculate fair odds
                        fair_odds = calculate_fair_odds(prob)
                        
                        # Kelly Criterion
                        if odds > 0:
                            decimal_odds = (odds / 100) + 1
                        else:
                            decimal_odds = (100 / abs(odds)) + 1
                        
                        kelly_fraction = (prob * decimal_odds - 1) / (decimal_odds - 1)
                        kelly_bet = max(0, kelly_fraction * bankroll)
                        
                        # Get player position (need player_id from stats)
                        player_id = stats.get('player_id', '')
                        position = get_player_position(player_id, player, roster_df)
                        
                        # Get defense matchup info
                        def_rank = None
                        if position and position in defense_rankings.get(home_team, {}):
                            def_rank = defense_rankings[home_team][position]  # rank is the value, not a dict
                        
                        # Funnel defense check - value is directly 'Pass Funnel', 'Run Funnel', or None
                        funnel_type = funnel_defenses.get(home_team, '') or ''
                        
                        # Red zone and opening drive stats
                        rz_rate = rz_stats.get(player, {}).get('rate', 0)
                        od_rate = od_stats.get(player, {}).get('rate', 0)
                        
                        all_bets.append({
                            'game': f"{away_team} @ {home_team}",
                            'game_date': game_date,
                            'game_time': game_time,
                            'player': player,
                            'position': position or '?',
                            'odds': odds,
                            'bookmaker': bookmaker,
                            'your_prob': round(prob * 100, 1),
                            'implied_prob': round(implied_prob * 100, 1),
                            'fair_odds': fair_odds,
                            'ev_percent': round(ev_percent, 2),
                            'kelly_bet': round(kelly_bet, 2),
                            'recent_form': f"{stats.get('recent_tds', 0)}/{stats.get('recent_games', 0)}",
                            'rz_rate': round(rz_rate * 100, 1) if rz_rate else 0,
                            'od_rate': round(od_rate * 100, 1) if od_rate else 0,
                            'def_rank': def_rank,
                            'funnel': funnel_type,
                            'nfl_game_id': nfl_game_id
                        })
        
        # Sort by EV descending
        all_bets.sort(key=lambda x: x['ev_percent'], reverse=True)
        
        return render_template('best_bets.html',
                             bets=all_bets,
                             error=None,
                             season=season,
                             week=current_week,
                             last_updated=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                             bankroll=bankroll)
    
    except Exception as e:
        print(f"Error in best_bets_scanner: {e}")
        import traceback
        traceback.print_exc()
        return render_template('best_bets.html',
                             bets=[],
                             error=f'Error loading best bets: {str(e)}',
                             season=season,
                             week=None,
                             last_updated=None)

@bp.route('/analysis')
@bp.route('/analysis/<int:season>')
def analysis_page(season=None):
    """
    Analysis Page - Statistical research tools for First TD betting.
    Provides player research, team analysis, defense matchups, and trends.
    Public route available to all users.
    """
    # Default to current season
    if season is None:
        season = 2025
    
    try:
        # Load all NFL statistics (use fresh data if refresh param is set)
        use_cache = request.args.get('refresh') != '1'
        stats_data = get_nfl_stats_data(season, use_cache=use_cache)
        
        schedule_df = stats_data['schedule_df']
        pbp_df = stats_data['pbp_df']
        roster_df = stats_data['roster_df']
        first_td_map = stats_data['first_td_map']
        player_stats_recent = stats_data['player_stats_recent']
        player_stats_full = stats_data['player_stats_full']
        defense_rankings = stats_data['defense_rankings']
        funnel_defenses = stats_data['funnel_defenses']
        rz_stats = stats_data['rz_stats']
        od_stats = stats_data['od_stats']
        team_rz_splits = stats_data['team_rz_splits']
        
        if schedule_df.height == 0:
            return render_template('analysis.html',
                                 error='No schedule data available',
                                 season=season,
                                 player_data=None,
                                 team_data=None,
                                 defense_data=None,
                                 trends_data=None)
        
        # Get current week for context
        today_str = datetime.now().strftime("%Y-%m-%d")
        future_games = schedule_df.filter(pl.col("gameday") >= today_str)
        current_week = int(future_games["week"].cast(pl.Int64).min()) if future_games.height > 0 else 18
        
        # === PLAYER RESEARCH TAB DATA ===
        # Build comprehensive player database with all stats
        player_database = []
        for player_name in player_stats_full.keys():
            stats_full = player_stats_full[player_name]
            stats_recent = player_stats_recent.get(player_name, {'first_tds': 0, 'team_games': 0})
            
            player_id = stats_full.get('player_id', '')
            position = get_player_position(player_id, player_name, roster_df)
            
            # Get team from roster
            team = '?'
            if roster_df is not None and roster_df.height > 0:
                player_rows = roster_df.filter(
                    (pl.col('gsis_id') == player_id) |
                    (pl.col('full_name').str.to_lowercase() == player_name.lower())
                )
                if player_rows.height > 0:
                    team = player_rows[0, 'team'] if 'team' in player_rows.columns else '?'
            
            # First TD history (get games where this player scored first TD)
            ftd_games = []
            ftd_games_standalone = []
            
            from datetime import datetime as dt_parser
            
            for game_id, td_info in first_td_map.items():
                if td_info.get('player', '').lower() == player_name.lower():
                    # Get game details from schedule
                    game_row = schedule_df.filter(pl.col('game_id') == game_id)
                    if game_row.height > 0:
                        game = game_row.to_dicts()[0]
                        
                        # Determine if standalone based on gameday
                        is_standalone = False
                        gameday = game.get('gameday', '')
                        gametime = game.get('gametime', '')
                        
                        # Check if there's a gameday column (day of week)
                        if 'gameday' in game and gameday:
                            # gameday field contains the date like "2025-11-28"
                            try:
                                game_date = dt_parser.strptime(str(gameday), '%Y-%m-%d')
                                day_of_week = game_date.weekday()  # 0=Monday, 1=Tuesday, 2=Wednesday, 3=Thursday, 4=Friday, 5=Saturday, 6=Sunday
                                
                                # Standalone is any game that isn't Sunday afternoon
                                # Sunday is day 6, so standalone is everything except Sunday afternoon
                                if day_of_week != 6:
                                    # Monday, Tuesday, Wednesday, Thursday, Friday, Saturday games are all standalone
                                    is_standalone = True
                                elif day_of_week == 6:
                                    # Sunday games - check time to distinguish SNF from afternoon games
                                    if gametime and isinstance(gametime, str):
                                        hour = int(gametime.split(':')[0]) if ':' in gametime else 0
                                        # SNF typically starts at 20:20 or later (8:20 PM)
                                        if hour >= 20:
                                            is_standalone = True
                                        # Sunday afternoon games (typically 13:00 or 16:00) are NOT standalone
                                        else:
                                            is_standalone = False
                            except Exception as e:
                                # If parsing fails, not standalone
                                pass
                        
                        game_info = {
                            'week': game.get('week', '?'),
                            'opponent': game.get('away_team', '?') if game.get('home_team') == team else game.get('home_team', '?'),
                            'location': 'H' if game.get('home_team') == team else 'A',
                            'date': game.get('gameday', ''),
                            'is_standalone': is_standalone
                        }
                        
                        ftd_games.append(game_info)
                        if is_standalone:
                            ftd_games_standalone.append(game_info)
            
            # Sort FTD history by week descending (most recent first)
            ftd_games.sort(key=lambda x: x['week'], reverse=True)
            ftd_games_standalone.sort(key=lambda x: x['week'], reverse=True)
            
            # Calculate RZ and OD rates from stats
            rz_data = rz_stats.get(player_name, {})
            rz_opps = rz_data.get('rz_opps', 0)
            rz_tds = rz_data.get('rz_tds', 0)
            rz_rate = (rz_tds / rz_opps * 100) if rz_opps > 0 else 0
            
            od_data = od_stats.get(player_name, {})
            od_opps = od_data.get('od_opps', 0)
            od_tds = od_data.get('od_tds', 0)
            od_rate = (od_tds / od_opps * 100) if od_opps > 0 else 0
            
            player_database.append({
                'player': player_name,
                'player_id': player_id,
                'position': position or '?',
                'team': team,
                'probability_full': round(stats_full.get('prob', 0) * 100, 1),
                'probability_recent': round(stats_recent.get('prob', 0) * 100, 1) if stats_recent.get('team_games', 0) > 0 else 0,
                'recent_form': f"{stats_recent.get('first_tds', 0)}/{stats_recent.get('team_games', 0)}",
                'full_form': f"{stats_full.get('first_tds', 0)}/{stats_full.get('team_games', 0)}",
                'recent_tds': stats_recent.get('first_tds', 0),
                'full_tds': stats_full.get('first_tds', 0),
                'season_tds': len(ftd_games),
                'season_tds_standalone': len(ftd_games_standalone),
                'rz_rate': round(rz_rate, 1),
                'rz_opps': rz_opps,
                'rz_tds': rz_tds,
                'od_rate': round(od_rate, 1),
                'od_opps': od_opps,
                'od_tds': od_tds,
                'ftd_history': ftd_games[:10],  # Limit to 10 most recent
                'ftd_history_standalone': ftd_games_standalone[:10]
            })
        
        # Sort by full season probability descending
        player_database.sort(key=lambda x: x['probability_full'], reverse=True)
        
        # Get unique teams for filter dropdown
        unique_teams = sorted(set(player['team'] for player in player_database if player['team'] != '?'))
        
        # === TEAM ANALYSIS TAB DATA ===
        # Team First TD Leaderboard
        team_ftd_counts = {}
        team_ftd_home = {}
        team_ftd_away = {}
        
        for game_id, td_info in first_td_map.items():
            team = td_info.get('team', '')
            if team:
                # Get game details to determine home/away
                game_row = schedule_df.filter(pl.col('game_id') == game_id)
                if game_row.height > 0:
                    game = game_row.to_dicts()[0]
                    is_home = (game.get('home_team') == team)
                    
                    # Overall count
                    if team not in team_ftd_counts:
                        team_ftd_counts[team] = 0
                        team_ftd_home[team] = 0
                        team_ftd_away[team] = 0
                    
                    team_ftd_counts[team] += 1
                    if is_home:
                        team_ftd_home[team] += 1
                    else:
                        team_ftd_away[team] += 1
        
        # Calculate games played per team (all games in schedule)
        team_games_played = {}
        team_home_games = {}
        team_away_games = {}
        
        for game in schedule_df.to_dicts():
            home = game['home_team']
            away = game['away_team']
            week = game.get('week', 0)
            
            # Count all games (not just completed ones) up to current week
            if week <= current_week:
                team_games_played[home] = team_games_played.get(home, 0) + 1
                team_games_played[away] = team_games_played.get(away, 0) + 1
                team_home_games[home] = team_home_games.get(home, 0) + 1
                team_away_games[away] = team_away_games.get(away, 0) + 1
        
        team_leaderboard = []
        for team in team_ftd_counts.keys():
            ftd_count = team_ftd_counts.get(team, 0)
            ftd_home = team_ftd_home.get(team, 0)
            ftd_away = team_ftd_away.get(team, 0)
            
            games = team_games_played.get(team, 0)
            home_games = team_home_games.get(team, 0)
            away_games = team_away_games.get(team, 0)
            
            pct = (ftd_count / games * 100) if games > 0 else 0
            home_rate = (ftd_home / home_games * 100) if home_games > 0 else 0
            away_rate = (ftd_away / away_games * 100) if away_games > 0 else 0
            
            # Get red zone pass/run splits
            rz_pass_pct = team_rz_splits.get(team, {}).get('pass_pct', 0)
            rz_run_pct = team_rz_splits.get(team, {}).get('run_pct', 0)
            
            team_leaderboard.append({
                'team': team,
                'games': games,
                'first_tds': ftd_count,
                'pct': round(pct, 1),
                'home_rz_rate': round(home_rate, 1),
                'away_rz_rate': round(away_rate, 1),
                'split_diff': round(home_rate - away_rate, 1),
                'rz_pass_pct': round(rz_pass_pct, 1),
                'rz_run_pct': round(rz_run_pct, 1)
            })
        
        team_leaderboard.sort(key=lambda x: x['pct'], reverse=True)
        
        # === DEFENSE ANALYSIS TAB DATA ===
        # Defense vs Position Rankings
        positions = ['QB', 'RB', 'WR', 'TE']
        defense_matrix = []
        
        for team in sorted(defense_rankings.keys()):
            team_row = {'team': team}
            for pos in positions:
                rank = defense_rankings[team].get(pos, 99)
                team_row[pos] = rank
            
            # Add funnel type
            team_row['funnel'] = funnel_defenses.get(team, '') or ''
            
            defense_matrix.append(team_row)
        
        # Sort by average rank (lower is better)
        for row in defense_matrix:
            avg_rank = sum([row.get(pos, 99) for pos in positions]) / len(positions)
            row['avg_rank'] = round(avg_rank, 1)
        
        defense_matrix.sort(key=lambda x: x['avg_rank'])
        
        # === TRENDS & INSIGHTS TAB DATA ===
        # Hot Players (last 5 games significantly above season average)
        hot_players = []
        for player_name in player_stats_recent.keys():
            stats_recent = player_stats_recent[player_name]
            stats_full = player_stats_full.get(player_name, {'prob': 0})
            
            first_tds = stats_recent.get('first_tds', 0)
            team_games = stats_recent.get('team_games', 0)
            
            if team_games >= 3:  # Minimum 3 games sample
                recent_rate = first_tds / team_games
                season_rate = stats_full.get('prob', 0)
                
                # Hot if recent rate is 5%+ higher than season average
                if recent_rate > season_rate + 0.05:
                    player_id = stats_recent.get('player_id', '')
                    position = get_player_position(player_id, player_name, roster_df)
                    
                    hot_players.append({
                        'player': player_name,
                        'position': position or '?',
                        'recent_form': f"{first_tds}/{team_games}",
                        'recent_rate': round(recent_rate * 100, 1),
                        'season_rate': round(season_rate * 100, 1),
                        'diff': round((recent_rate - season_rate) * 100, 1)
                    })
        
        hot_players.sort(key=lambda x: x['diff'], reverse=True)
        
        # Weekly First TD Scorers table (all weeks)
        weekly_scorers = []
        for game_id, td_info in first_td_map.items():
            game_row = schedule_df.filter(pl.col('game_id') == game_id)
            if game_row.height > 0:
                game = game_row.to_dicts()[0]
                player = td_info.get('player', '')
                player_id = td_info.get('player_id', '')
                position = get_player_position(player_id, player, roster_df)
                
                weekly_scorers.append({
                    'week': game.get('week', '?'),
                    'player': player,
                    'position': position or '?',
                    'team': td_info.get('team', '?'),
                    'game': f"{game.get('away_team', '?')} @ {game.get('home_team', '?')}",
                    'date': game.get('gameday', '')
                })
        
        # Sort by week descending
        weekly_scorers.sort(key=lambda x: x['week'], reverse=True)
        
        return render_template('analysis.html',
                             error=None,
                             season=season,
                             current_week=current_week,
                             player_data={
                                 'players': player_database,
                                 'total_count': len(player_database),
                                 'teams': unique_teams
                             },
                             team_data={
                                 'leaderboard': team_leaderboard
                             },
                             defense_data={
                                 'matrix': defense_matrix,
                                 'positions': positions
                             },
                             trends_data={
                                 'hot_players': hot_players[:20],  # Top 20
                                 'weekly_scorers': weekly_scorers
                             },
                             last_updated=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    
    except Exception as e:
        print(f"Error in analysis_page: {e}")
        import traceback
        traceback.print_exc()
        return render_template('analysis.html',
                             error=f'Error loading analysis: {str(e)}',
                             season=season,
                             player_data=None,
                             team_data=None,
                             defense_data=None,
                             trends_data=None)

@bp.route('/api/health')
def health():
    """Health check endpoint"""
    return jsonify({'status': 'ok', 'database': 'connected'})
