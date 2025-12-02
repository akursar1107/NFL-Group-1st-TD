"""
Grading service - handles all pick grading logic
Consolidates duplicate grading code from routes.py
"""
from datetime import datetime
from ..models import Game, Pick, MatchDecision
from .. import db
from ..data_loader import load_data_with_cache_web, get_current_nfl_week, get_all_td_scorers
from nfl_core.stats import get_first_td_scorers
from ..fuzzy_matcher import NameMatcher


class GradingService:
    """Service for grading NFL picks with fuzzy matching"""
    
    def __init__(self, auto_accept_threshold=0.85, medium_confidence_threshold=0.70):
        """
        Initialize grading service
        
        Args:
            auto_accept_threshold: Confidence score to auto-accept matches (default 0.85)
            medium_confidence_threshold: Minimum score to flag for review (default 0.70)
        """
        self.matcher = NameMatcher(auto_accept_threshold=auto_accept_threshold)
        self.medium_threshold = medium_confidence_threshold
    
    def grade_week(self, week_num, season=2025, use_cache=None, force_regrade=False):
        """
        Grade all picks for a specific week
        
        Args:
            week_num: Week number to grade
            season: NFL season year
            use_cache: Whether to use cached data (None = auto-detect)
            force_regrade: If True, re-grade already graded picks
            
        Returns:
            dict with grading results and statistics
        """
        # Auto-detect cache usage if not specified
        if use_cache is None:
            current_week = get_current_nfl_week(season)
            use_cache = (week_num < current_week)
        
        # Load NFL data
        schedule_df, pbp_df, roster_df = load_data_with_cache_web(season, use_cache=use_cache)
        
        # Get games for this week
        games = Game.query.filter_by(week=week_num, season=season).all()
        
        if not games:
            return {
                'success': False,
                'error': f'No games found for Week {week_num} in {season} season'
            }
        
        game_ids = [g.game_id for g in games]
        
        # Get first TD scorers
        first_td_map = get_first_td_scorers(pbp_df, target_game_ids=game_ids, roster_df=roster_df)
        
        if not first_td_map:
            return {
                'success': False,
                'error': 'No first TD data found. Games may not have been played yet.'
            }
        
        # Grade FTD picks
        ftd_results = self._grade_ftd_picks(games, first_td_map, force_regrade=force_regrade)
        
        # Grade ATTS picks
        all_td_map = get_all_td_scorers(pbp_df, target_game_ids=game_ids, roster_df=roster_df)
        atts_results = self._grade_atts_picks(games, all_td_map, force_regrade=force_regrade) if all_td_map else {
            'graded': 0, 'won': 0, 'lost': 0, 'needs_review': 0
        }
        
        # Commit all changes
        db.session.commit()
        
        return {
            'success': True,
            'week': week_num,
            'season': season,
            'games_graded': ftd_results['games_graded'],
            'ftd': ftd_results,
            'atts': atts_results,
            'total_graded': ftd_results['graded'] + atts_results['graded'],
            'total_won': ftd_results['won'] + atts_results['won'],
            'total_lost': ftd_results['lost'] + atts_results['lost'],
            'total_needs_review': ftd_results['needs_review'] + atts_results['needs_review']
        }
    
    def grade_all_weeks(self, season=2025, force_regrade=True):
        """
        Grade all weeks for a season
        
        Args:
            season: NFL season year
            force_regrade: If True, re-grade already graded picks (default True for this method)
            
        Returns:
            dict with grading results and statistics
        """
        # Always use cached data for bulk grading (more efficient)
        schedule_df, pbp_df, roster_df = load_data_with_cache_web(season, use_cache=True)
        
        # Get all games
        all_games = Game.query.filter_by(season=season).all()
        
        if not all_games:
            return {
                'success': False,
                'error': 'No games found to grade'
            }
        
        game_ids = [g.game_id for g in all_games]
        
        # Get first TD scorers for all games
        first_td_map = get_first_td_scorers(pbp_df, target_game_ids=game_ids, roster_df=roster_df)
        
        if not first_td_map:
            return {
                'success': False,
                'error': 'No first TD data found. Games may not have been played yet.'
            }
        
        # Grade FTD picks
        ftd_results = self._grade_ftd_picks(all_games, first_td_map, force_regrade=force_regrade)
        
        # Grade ATTS picks
        all_td_map = get_all_td_scorers(pbp_df, target_game_ids=game_ids, roster_df=roster_df)
        atts_results = self._grade_atts_picks(all_games, all_td_map, force_regrade=force_regrade) if all_td_map else {
            'graded': 0, 'won': 0, 'lost': 0, 'needs_review': 0
        }
        
        # Get unique weeks graded
        weeks_graded = set(g.week for g in all_games if g.game_id in first_td_map)
        
        # Commit all changes
        db.session.commit()
        
        return {
            'success': True,
            'season': season,
            'weeks_graded': sorted(weeks_graded),
            'games_graded': ftd_results['games_graded'],
            'ftd': ftd_results,
            'atts': atts_results,
            'total_graded': ftd_results['graded'] + atts_results['graded'],
            'total_won': ftd_results['won'] + atts_results['won'],
            'total_lost': ftd_results['lost'] + atts_results['lost'],
            'total_needs_review': ftd_results['needs_review'] + atts_results['needs_review']
        }
    
    def _grade_ftd_picks(self, games, first_td_map, force_regrade=False):
        """Grade First TD picks for given games"""
        games_graded = 0
        picks_graded = 0
        picks_won = 0
        picks_lost = 0
        needs_review = 0
        
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
                if pick.graded_at and not force_regrade:
                    continue  # Skip already graded unless force_regrade is True
                
                result = self._grade_single_pick(pick, [actual_player], actual_player)
                picks_graded += result['graded']
                picks_won += result['won']
                picks_lost += result['lost']
                needs_review += result['needs_review']
            
            games_graded += 1
        
        return {
            'games_graded': games_graded,
            'graded': picks_graded,
            'won': picks_won,
            'lost': picks_lost,
            'needs_review': needs_review
        }
    
    def _grade_atts_picks(self, games, all_td_map, force_regrade=False):
        """Grade Anytime TD Scorer picks for given games"""
        picks_graded = 0
        picks_won = 0
        picks_lost = 0
        needs_review = 0
        
        for game in games:
            if game.game_id not in all_td_map:
                continue
            
            td_scorers = all_td_map[game.game_id]
            
            if not td_scorers:
                continue
            
            # Extract scorer names for matching
            scorer_names = [s.get('player', '').strip() for s in td_scorers if s.get('player')]
            
            # Grade ATTS picks
            atts_picks = Pick.query.filter_by(game_id=game.id, pick_type='ATTS').all()
            
            for pick in atts_picks:
                if pick.graded_at and not force_regrade:
                    continue
                
                result = self._grade_single_pick(pick, scorer_names)
                picks_graded += result['graded']
                picks_won += result['won']
                picks_lost += result['lost']
                needs_review += result['needs_review']
        
        return {
            'graded': picks_graded,
            'won': picks_won,
            'lost': picks_lost,
            'needs_review': needs_review
        }
    
    def _grade_single_pick(self, pick, scorer_names, matched_scorer=None):
        """
        Grade a single pick using fuzzy matching
        
        Args:
            pick: Pick model instance
            scorer_names: List of potential scorer names to match against
            matched_scorer: Optional specific scorer name for display (FTD only)
            
        Returns:
            dict with grading counts
        """
        pick_player = pick.player_name.strip()
        
        # Use fuzzy matcher
        match_result = self.matcher.find_best_match(pick_player, scorer_names, min_score=0.0)
        
        result = {'graded': 0, 'won': 0, 'lost': 0, 'needs_review': 0}
        
        if match_result and match_result['score'] >= self.medium_threshold:
            # Create match decision record
            match_decision = MatchDecision(
                pick_id=pick.id,
                pick_name=pick_player,
                scorer_name=matched_scorer or match_result['matched_name'],
                match_score=match_result['score'],
                confidence=match_result['confidence'],
                match_reason=match_result['reason'],
                auto_accepted=match_result['auto_accept'],
                needs_review=not match_result['auto_accept']
            )
            db.session.add(match_decision)
            
            # Auto-accept high confidence matches
            if match_result['auto_accept']:
                pick.result = 'W'
                pick.payout = pick.calculate_payout()
                pick.graded_at = datetime.utcnow()
                result['graded'] = 1
                result['won'] = 1
            else:
                # Flag for manual review (medium confidence)
                result['needs_review'] = 1
        else:
            # No match or low confidence - mark as loss
            pick.result = 'L'
            pick.payout = -pick.stake
            pick.graded_at = datetime.utcnow()
            result['graded'] = 1
            result['lost'] = 1
        
        return result
