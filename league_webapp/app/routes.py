from flask import Blueprint, render_template, jsonify, redirect, url_for, flash, request
from .models import User, Game, Pick, MatchDecision
from . import db, cache
from sqlalchemy import func, case
from sqlalchemy.orm import joinedload
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
from .services.grading_service import GradingService
from .services.match_review_service import MatchReviewService
import polars as pl

bp = Blueprint('main', __name__)

# Shared helper function for loading NFL statistics
@cache.memoize(timeout=300)  # Cache for 5 minutes
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
        
        total_picks = (ftd.total if ftd else 0) + (atts.total if atts else 0)
        
        # Skip users with 0 picks
        if total_picks == 0:
            continue
        
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
            'total_picks': total_picks
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
    
    # Get all games for this week and season with picks eagerly loaded (avoid N+1 queries)
    games = Game.query.options(joinedload(Game.picks).joinedload(Pick.user)).filter_by(
        week=week_num, season=season
    ).order_by(Game.game_date, Game.game_time).all()
    
    if not games:
        return render_template('week.html', week=week_num, season=season, games=[], message="No games found for this week")
    
    # Build game data with picks (now using eager-loaded data)
    games_data = []
    for game in games:
        # Filter picks for FTD type (already loaded)
        ftd_picks = [p for p in game.picks if p.pick_type == 'FTD']
        
        game_info = {
            'game': game,
            'picks': ftd_picks,
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
    # Get season from form or default to 2025
    season_str = request.form.get('season', '2025')
    season = int(season_str) if season_str and season_str.strip() else 2025
    
    try:
        # Use grading service
        grading_service = GradingService()
        result = grading_service.grade_week(week_num, season)
        
        if not result['success']:
            flash(result['error'], 'warning')
            return redirect(url_for('main.week_view', week_num=week_num, season=season))
        
        # Build flash message
        total = result['total_graded']
        won = result['total_won']
        lost = result['total_lost']
        review = result['total_needs_review']
        games = result['games_graded']
        ftd = result['ftd']['graded']
        atts = result['atts']['graded']
        
        if review > 0:
            flash(f'Graded {total} picks across {games} games: {won} wins, {lost} losses, {review} need review (FTD: {ftd}, ATTS: {atts})', 'warning')
        else:
            flash(f'Graded {total} picks across {games} games: {won} wins, {lost} losses (FTD: {ftd}, ATTS: {atts})', 'success')
        
    except Exception as e:
        flash(f'Error grading week: {str(e)}', 'danger')
    
    return redirect(url_for('main.week_view', week_num=week_num, season=season))

@bp.route('/admin/grade-current-week', methods=['POST'])
def grade_current_week():
    """Admin route to quickly grade the current week (or most recent week with pending picks)"""
    season = 2025
    current_week = get_current_nfl_week(season)
    
    # Optimized: Find most recent week with pending picks in single query
    week_to_grade_result = db.session.query(Game.week).join(Pick).filter(
        Game.season == season,
        Pick.result == 'Pending'
    ).order_by(Game.week.desc()).first()
    
    if not week_to_grade_result:
        flash('No pending picks to grade for this season', 'warning')
        return redirect(url_for('main.index'))
    
    week_to_grade = week_to_grade_result[0]
    
    if week_to_grade < 1:
        flash('No week available to grade yet', 'warning')
        return redirect(url_for('main.index'))
    
    try:
        # Use grading service (same as grade_week_route)
        grading_service = GradingService()
        result = grading_service.grade_week(week_to_grade, season, use_cache=False)
        
        if not result['success']:
            flash(result['error'], 'warning')
            return redirect(url_for('main.index'))
        
        # Build flash message
        total = result['total_graded']
        won = result['total_won']
        lost = result['total_lost']
        review = result['total_needs_review']
        
        if review > 0:
            flash(f'Graded Week {week_to_grade}: {total} picks, {won} wins, {lost} losses, {review} need review', 'warning')
        else:
            flash(f'Graded Week {week_to_grade}: {total} picks, {won} wins, {lost} losses', 'success')
        
    except Exception as e:
        flash(f'Error grading: {str(e)}', 'danger')
    
    return redirect(url_for('main.index'))

@bp.route('/admin/grade-all', methods=['POST'])
def grade_all_weeks():
    """Admin route to grade all weeks at once"""
    # Get season from form or default to 2025
    season_str = request.form.get('season', '2025')
    season = int(season_str) if season_str and season_str.strip() else 2025
    
    try:
        # Use grading service
        grading_service = GradingService()
        result = grading_service.grade_all_weeks(season)
        
        if not result['success']:
            flash(result['error'], 'warning')
            return redirect(request.referrer or url_for('main.index'))
        
        # Build flash message
        total = result['total_graded']
        won = result['total_won']
        lost = result['total_lost']
        review = result['total_needs_review']
        games = result['games_graded']
        weeks = len(result['weeks_graded'])
        ftd = result['ftd']['graded']
        atts = result['atts']['graded']
        
        if review > 0:
            flash(f'Graded {total} picks across {games} games in {weeks} weeks: {won} wins, {lost} losses, {review} need review (FTD: {ftd}, ATTS: {atts})', 'warning')
        else:
            flash(f'Graded {total} picks across {games} games in {weeks} weeks: {won} wins, {lost} losses (FTD: {ftd}, ATTS: {atts})', 'success')
        
    except Exception as e:
        flash(f'Error grading all weeks: {str(e)}', 'danger')
    
    # Redirect back to all-picks page if that's where we came from
    return redirect(request.referrer or url_for('main.index'))

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
            if roster_df is not None and not roster_df.is_empty():
                player_match = roster_df.filter(pl.col('full_name').str.to_lowercase() == player_name.lower())
                if not player_match.is_empty():
                    pick.player_position = player_match[0, 'position']
            
            # Recalculate payout if the pick has been graded
            if pick.result in ('W', 'L', 'Push'):
                pick.payout = pick.calculate_payout()
            
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

@bp.route('/api/team-history/<int:season>/<team>')
@bp.route('/api/team-history/<int:season>/<team>/<week>')
def team_history_api(season, team, week='ALL'):
    """
    API endpoint for team first TD history.
    Returns all games for a specific team and season with first TD scorer info.
    If team is 'ALL', returns all games in the season.
    If week is provided, filters to that specific week.
    """
    try:
        # Load NFL data for the requested season
        stats_data = get_nfl_stats_data(season, use_cache=True)
        schedule_df = stats_data['schedule_df']
        first_td_map = stats_data['first_td_map']
        roster_df = stats_data['roster_df']
        
        # Handle "ALL" teams vs specific team
        if team == 'ALL':
            # Get all games
            team_games = schedule_df.sort('week')
        else:
            # Filter schedule for this team
            team_games = schedule_df.filter(
                (pl.col('home_team') == team) | (pl.col('away_team') == team)
            ).sort('week')
            
            if team_games.height == 0:
                return jsonify({'error': f'No games found for {team} in {season} season'})
        
        # Filter by week if specified
        if week != 'ALL':
            try:
                week_num = int(week)
                team_games = team_games.filter(pl.col('week') == week_num)
            except ValueError:
                pass
        
        games_list = []
        total_first_tds = 0
        
        for game in team_games.to_dicts():
            week = game.get('week', '?')
            home_team = game.get('home_team', '')
            away_team = game.get('away_team', '')
            gameday = game.get('gameday', '')
            gametime = game.get('gametime', '')
            
            # Determine if standalone
            is_standalone = False
            if gameday:
                try:
                    from datetime import datetime as dt_parser
                    game_date = dt_parser.strptime(str(gameday), '%Y-%m-%d')
                    day_of_week = game_date.weekday()
                    
                    if day_of_week != 6:
                        is_standalone = True
                    elif day_of_week == 6:
                        if gametime and isinstance(gametime, str):
                            hour = int(gametime.split(':')[0]) if ':' in gametime else 0
                            if hour >= 20:
                                is_standalone = True
                except:
                    pass
            
            # Get first TD scorer for this game
            game_id = game.get('game_id', '')
            first_td_scorer = None
            first_td_team = None
            position = None
            
            if game_id and game_id in first_td_map:
                scorer_info = first_td_map[game_id]
                first_td_team = scorer_info['team']
                first_td_scorer = scorer_info['player']
                
                # For specific team filter, only count if they scored
                if team == 'ALL' or first_td_team == team:
                    total_first_tds += 1
                
                # Get position
                player_id = scorer_info.get('player_id', '')
                if player_id:
                    position = get_player_position(player_id, first_td_scorer, roster_df)
            
            # Build game info based on view type
            if team == 'ALL':
                games_list.append({
                    'week': week,
                    'home_team': home_team,
                    'away_team': away_team,
                    'is_standalone': is_standalone,
                    'first_td_scorer': first_td_scorer,
                    'first_td_team': first_td_team,
                    'position': position
                })
            else:
                opponent = away_team if home_team == team else home_team
                location = 'H' if home_team == team else 'A'
                # Only include scorer if this team scored
                scorer = first_td_scorer if first_td_team == team else None
                pos = position if first_td_team == team else None
                
                games_list.append({
                    'week': week,
                    'opponent': opponent,
                    'location': location,
                    'is_standalone': is_standalone,
                    'first_td_scorer': scorer,
                    'position': pos
                })
        
        return jsonify({
            'team': team,
            'season': season,
            'games': games_list,
            'total_first_tds': total_first_tds
        })
        
    except Exception as e:
        print(f"Error in team_history_api: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@bp.route('/admin/all-picks')
@bp.route('/admin/all-picks/<int:season>')
def all_picks_admin(season=None):
    """Admin page showing all picks for mass editing (ADMIN ONLY - enforcement TODO)"""
    # TODO: Add @admin_required decorator when authentication is implemented
    
    if season is None:
        season = 2025
    
    # Get all available seasons
    available_seasons = db.session.query(Game.season).distinct().order_by(Game.season.desc()).all()
    available_seasons = [s[0] for s in available_seasons]
    
    # Get all picks for the season with related data eagerly loaded (avoid N+1 queries)
    picks = Pick.query.options(
        joinedload(Pick.game),
        joinedload(Pick.user)
    ).join(Game).join(User).filter(
        Game.season == season
    ).order_by(
        Game.week.desc(),
        Game.game_date.desc(),
        User.username,
        Pick.pick_type
    ).all()
    
    return render_template('admin_all_picks.html',
                         picks=picks,
                         season=season,
                         available_seasons=available_seasons)

@bp.route('/api/standardize-picks/<int:season>', methods=['POST'])
def standardize_picks(season):
    """
    API endpoint to standardize player names and fill missing positions.
    Returns suggested changes for admin review.
    Uses fuzzy matching for accurate player identification.
    """
    from .fuzzy_matcher import NameMatcher
    
    try:
        # Load roster data
        schedule_df, pbp_df, roster_df = load_data_with_cache_web(season, use_cache=True)
        
        # Get all picks for this season
        picks = Pick.query.join(Game).filter(Game.season == season).all()
        
        suggestions = []
        missing_atts = []
        
        # Initialize fuzzy matcher
        matcher = NameMatcher(auto_accept_threshold=0.85)
        
        # Check for missing ATTS picks
        ftd_picks = [p for p in picks if p.pick_type == 'FTD']
        for ftd_pick in ftd_picks:
            # Check if corresponding ATTS pick exists
            atts_exists = any(
                p.user_id == ftd_pick.user_id and 
                p.game_id == ftd_pick.game_id and 
                p.pick_type == 'ATTS'
                for p in picks
            )
            
            if not atts_exists:
                missing_atts.append({
                    'ftd_pick_id': ftd_pick.id,
                    'user': ftd_pick.user.username,
                    'user_id': ftd_pick.user_id,
                    'game_id': ftd_pick.game_id,
                    'week': ftd_pick.game.week,
                    'game': f"{ftd_pick.game.away_team} @ {ftd_pick.game.home_team}",
                    'player_name': ftd_pick.player_name,
                    'player_position': ftd_pick.player_position,
                    'odds': ftd_pick.odds,
                    'stake': ftd_pick.stake
                })
        
        # Get all roster names for fuzzy matching
        roster_names = []
        roster_lookup = {}
        if roster_df is not None and not roster_df.is_empty():
            for row in roster_df.iter_rows(named=True):
                full_name = row.get('full_name', '')
                position = row.get('position', '')
                if full_name:
                    roster_names.append(full_name)
                    roster_lookup[full_name] = position
        
        for pick in picks:
            changes = {}
            
            # Check player name standardization
            player_name = pick.player_name.strip()
            
            if roster_df is not None and not roster_df.is_empty():
                # Always use fuzzy matcher to find best match
                match_result = matcher.find_best_match(player_name, roster_names, min_score=0.70)
                
                if match_result and match_result['confidence'] in ['high', 'exact']:
                    suggested_name = match_result['matched_name']
                    suggested_pos = roster_lookup.get(suggested_name)
                    
                    # Suggest name change if different from current (standardize to full name)
                    if suggested_name != player_name:
                        changes['player_name'] = {
                            'current': player_name,
                            'suggested': suggested_name,
                            'confidence': match_result['confidence'],
                            'score': round(match_result['score'], 3)
                        }
                    
                    # Fill position if missing
                    if not pick.player_position and suggested_pos:
                        changes['player_position'] = {
                            'current': pick.player_position,
                            'suggested': suggested_pos
                        }
            
            if changes:
                suggestions.append({
                    'pick_id': pick.id,
                    'user': pick.user.username,
                    'week': pick.game.week,
                    'game': f"{pick.game.away_team} @ {pick.game.home_team}",
                    'changes': changes
                })
        
        return jsonify({
            'success': True,
            'suggestions': suggestions,
            'missing_atts': missing_atts,
            'total': len(suggestions),
            'total_missing_atts': len(missing_atts)
        })
        
    except Exception as e:
        print(f"Error standardizing picks: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@bp.route('/api/apply-standardization', methods=['POST'])
def apply_standardization():
    """Apply approved standardization changes to picks"""
    try:
        data = request.get_json()
        approved_changes = data.get('changes', [])
        create_atts = data.get('create_atts', [])
        
        updated_count = 0
        created_count = 0
        
        # Apply field changes to existing picks
        for change in approved_changes:
            pick = Pick.query.get(change['pick_id'])
            if not pick:
                continue
            
            changes = change.get('changes', {})
            
            if 'player_name' in changes:
                pick.player_name = changes['player_name']['suggested']
            
            if 'player_position' in changes:
                pick.player_position = changes['player_position']['suggested']
            
            updated_count += 1
        
        # Create missing ATTS picks
        for atts_data in create_atts:
            new_pick = Pick(
                user_id=atts_data['user_id'],
                game_id=atts_data['game_id'],
                pick_type='ATTS',
                player_name=atts_data['player_name'],
                player_position=atts_data.get('player_position'),
                odds=atts_data['odds'],
                stake=atts_data['stake']
            )
            db.session.add(new_pick)
            created_count += 1
        
        db.session.commit()
        
        message = f'Successfully updated {updated_count} pick(s)'
        if created_count > 0:
            message += f' and created {created_count} ATTS pick(s)'
        
        return jsonify({
            'success': True,
            'updated': updated_count,
            'created': created_count,
            'message': message
        })
        
    except Exception as e:
        db.session.rollback()
        print(f"Error applying standardization: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@bp.route('/admin/match-review')
def match_review():
    """Admin page to review fuzzy matches that need manual approval"""
    # Get sort parameter
    sort_by = request.args.get('sort', 'date')
    
    # Use match review service
    review_service = MatchReviewService()
    pending_matches = review_service.get_pending_matches(sort_by)
    all_matches = review_service.get_all_matches(sort_by)
    stats = review_service.get_review_stats()
    
    return render_template('admin_match_review.html',
                          pending_matches=pending_matches,
                          all_matches=all_matches,
                          stats=stats,
                          current_sort=sort_by)

@bp.route('/admin/match-review/<int:match_id>', methods=['POST'])
def review_match(match_id):
    """Approve or reject a specific fuzzy match"""
    decision = request.form.get('decision')  # 'approve' or 'reject'
    
    if decision not in ['approve', 'reject']:
        flash('Invalid decision', 'danger')
        return redirect(url_for('main.match_review'))
    
    review_service = MatchReviewService()
    
    if decision == 'approve':
        success, message = review_service.approve_match(match_id)
        flash(message, 'success' if success else 'danger')
    else:
        success, message = review_service.reject_match(match_id)
        flash(message, 'warning' if success else 'danger')
    
    return redirect(url_for('main.match_review'))

@bp.route('/admin/match-review/bulk-approve', methods=['POST'])
def bulk_approve_matches():
    """Approve all pending matches"""
    review_service = MatchReviewService()
    success, count, message = review_service.bulk_approve_pending()
    flash(message, 'success' if success else 'danger')
    return redirect(url_for('main.match_review'))

@bp.route('/admin/match-review/bulk-reject', methods=['POST'])
def bulk_reject_matches():
    """Reject all pending matches"""
    review_service = MatchReviewService()
    success, count, message = review_service.bulk_reject_pending()
    flash(message, 'warning' if success else 'danger')
    return redirect(url_for('main.match_review'))

@bp.route('/admin/match-review/<int:match_id>/revert', methods=['POST'])
def revert_match(match_id):
    """Revert a manually approved/rejected match back to pending review"""
    review_service = MatchReviewService()
    success, message = review_service.revert_match(match_id)
    flash(message, 'info' if success else 'warning')
    return redirect(url_for('main.match_review'))

@bp.route('/admin/match-review/bulk-revert-approved', methods=['POST'])
def bulk_revert_approved():
    """Revert all manually approved matches back to pending review"""
    review_service = MatchReviewService()
    success, count, message = review_service.bulk_revert_approved()
    flash(message, 'info' if success else 'danger')
    return redirect(url_for('main.match_review'))
        match.needs_review = False
        
        pick = match.pick
        pick.result = 'W'
        pick.payout = pick.calculate_payout()
        pick.graded_at = datetime.utcnow()
@bp.route('/api/health')
def health():
    """Health check endpoint"""
    return jsonify({'status': 'ok', 'database': 'connected'})

@bp.route('/api/match-stats')
def match_stats():
    """API endpoint for fuzzy match statistics"""
    from .fuzzy_matcher import NameMatcher
    
    # Get all match decisions
    all_matches = MatchDecision.query.all()
    
    if not all_matches:
        return jsonify({
            'total': 0,
            'message': 'No match data available yet'
        })
    
    # Build match dict for stats calculation
    matches_dict = {}
    for m in all_matches:
        matches_dict[m.pick_name] = {
            'matched_name': m.scorer_name,
            'score': m.match_score,
            'confidence': m.confidence,
            'auto_accept': m.auto_accepted
        }
    
    # Use NameMatcher to calculate stats
    matcher = NameMatcher()
    stats = matcher.get_confidence_stats(matches_dict)
    
    # Add additional detailed stats
    stats['by_confidence'] = {
        'exact': {
            'count': sum(1 for m in all_matches if m.confidence == 'exact'),
            'auto_accepted': sum(1 for m in all_matches if m.confidence == 'exact' and m.auto_accepted),
            'approved': sum(1 for m in all_matches if m.confidence == 'exact' and m.manual_decision == 'approved'),
            'rejected': sum(1 for m in all_matches if m.confidence == 'exact' and m.manual_decision == 'rejected'),
        },
        'high': {
            'count': sum(1 for m in all_matches if m.confidence == 'high'),
            'auto_accepted': sum(1 for m in all_matches if m.confidence == 'high' and m.auto_accepted),
            'approved': sum(1 for m in all_matches if m.confidence == 'high' and m.manual_decision == 'approved'),
            'rejected': sum(1 for m in all_matches if m.confidence == 'high' and m.manual_decision == 'rejected'),
        },
        'medium': {
            'count': sum(1 for m in all_matches if m.confidence == 'medium'),
            'auto_accepted': sum(1 for m in all_matches if m.confidence == 'medium' and m.auto_accepted),
            'approved': sum(1 for m in all_matches if m.confidence == 'medium' and m.manual_decision == 'approved'),
            'rejected': sum(1 for m in all_matches if m.confidence == 'medium' and m.manual_decision == 'rejected'),
        },
        'low': {
            'count': sum(1 for m in all_matches if m.confidence == 'low'),
            'auto_accepted': sum(1 for m in all_matches if m.confidence == 'low' and m.auto_accepted),
            'approved': sum(1 for m in all_matches if m.confidence == 'low' and m.manual_decision == 'approved'),
            'rejected': sum(1 for m in all_matches if m.confidence == 'low' and m.manual_decision == 'rejected'),
        }
    }
    
    # Score distribution
    score_ranges = {
        '0.95-1.00': sum(1 for m in all_matches if 0.95 <= m.match_score <= 1.0),
        '0.85-0.95': sum(1 for m in all_matches if 0.85 <= m.match_score < 0.95),
        '0.70-0.85': sum(1 for m in all_matches if 0.70 <= m.match_score < 0.85),
        '0.50-0.70': sum(1 for m in all_matches if 0.50 <= m.match_score < 0.70),
        '0.00-0.50': sum(1 for m in all_matches if m.match_score < 0.50),
    }
    stats['score_distribution'] = score_ranges
    
    # Manual review accuracy (how often did manual reviews agree with the algorithm suggestion?)
    manual_reviews = [m for m in all_matches if m.manual_decision]
    if manual_reviews:
        # Consider "approved" as agreeing with the match suggestion
        stats['manual_review_accuracy'] = {
            'total_reviews': len(manual_reviews),
            'approved': sum(1 for m in manual_reviews if m.manual_decision == 'approved'),
            'rejected': sum(1 for m in manual_reviews if m.manual_decision == 'rejected'),
            'approval_rate': sum(1 for m in manual_reviews if m.manual_decision == 'approved') / len(manual_reviews)
        }
    
    return jsonify(stats)
