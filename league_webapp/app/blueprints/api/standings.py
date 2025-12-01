"""
Standings API endpoints
"""
from flask import request, jsonify
import logging
from . import api_bp
from ...services import StatsService
from ...error_handlers import handle_api_errors, success_response, error_response

logger = logging.getLogger(__name__)


@api_bp.route('/standings', methods=['GET'])
@handle_api_errors
def get_standings():
    season = request.args.get('season', 2025, type=int)
    logger.info(f"Fetching standings for season {season}")
    
    # Use StatsService for cleaner code
    standings = StatsService.calculate_standings(season)
    stats = StatsService.calculate_league_stats(standings)
    
    logger.info(f"Successfully retrieved standings for {len(standings)} players")
    return success_response({
        'standings': standings,
        'season': season,
        'stats': stats
    })
