"""
Standings API endpoints
"""
from flask import request, jsonify
from . import api_bp
from ...services import StatsService


@api_bp.route('/standings', methods=['GET'])
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
