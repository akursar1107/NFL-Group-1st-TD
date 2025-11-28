"""
NFL Core - Shared NFL data and statistics package

Used by both firstTD_CLI and league_webapp applications.
"""

__version__ = "1.0.0"

from .config import (
    API_KEY,
    SPORT,
    REGION,
    BASE_URL,
    API_TIMEOUT,
    MARKET_1ST_TD,
    ODDS_CACHE_DIR,
    ODDS_CACHE_EXPIRY,
    NFL_TEAM_MAP
)

from .data import (
    is_standalone_game,
    get_season_games,
    load_data_with_cache
)

from .stats import (
    get_first_td_scorers,
    get_player_season_stats,
    get_player_position,
    calculate_defense_rankings,
    calculate_fair_odds,
    get_red_zone_stats,
    get_opening_drive_stats,
    calculate_kelly_criterion,
    get_team_red_zone_splits,
    identify_funnel_defenses
)

__all__ = [
    # Config
    'API_KEY', 'SPORT', 'REGION', 'BASE_URL', 'API_TIMEOUT',
    'MARKET_1ST_TD', 'ODDS_CACHE_DIR', 'ODDS_CACHE_EXPIRY', 'NFL_TEAM_MAP',
    # Data
    'is_standalone_game', 'get_season_games', 'load_data_with_cache',
    # Stats
    'get_first_td_scorers', 'get_player_season_stats', 'get_player_position',
    'calculate_defense_rankings', 'calculate_fair_odds', 'get_red_zone_stats',
    'get_opening_drive_stats', 'calculate_kelly_criterion', 'get_team_red_zone_splits',
    'identify_funnel_defenses'
]
