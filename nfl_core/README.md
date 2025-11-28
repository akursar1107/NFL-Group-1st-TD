# NFL Core Package

Shared NFL statistics, data loading, and configuration utilities used by both the CLI and web applications.

## Installation

Install as editable package for development:

```bash
pip install -e .
```

## Usage

### Import Functions

```python
from nfl_core.stats import get_first_td_scorers, calculate_fair_odds
from nfl_core.data import load_data_with_cache
from nfl_core.config import API_KEY, NFL_TEAM_MAP
```

### Available Modules

#### config.py
- `API_KEY`: Odds API key (from environment variable)
- `SPORT`, `REGION`, `BASE_URL`: API constants
- `NFL_TEAM_MAP`: Team abbreviation to full name mapping

#### data.py
- `is_standalone_game()`: Polars expression for primetime/non-Sunday games
- `get_season_games(season: int)`: Load schedule with standalone flag
- `load_data_with_cache(season: int, cache_dir: str, use_cache: bool)`: Load schedule/pbp/roster with caching

#### stats.py
- `get_first_td_scorers()`: Process play-by-play for first TD scorer
- `get_player_season_stats()`: Calculate probabilities by player
- `get_player_position()`: Roster position lookup
- `calculate_defense_rankings()`: Defense vs position rankings
- `calculate_fair_odds()`: Convert probability to American odds
- `get_red_zone_stats()`: Red zone opportunities and TDs
- `get_opening_drive_stats()`: Opening drive usage
- `calculate_kelly_criterion()`: Bet sizing formula
- `get_team_red_zone_splits()`: Run/pass percentages
- `identify_funnel_defenses()`: Pass/run funnel classification

## Dependencies

- nflreadpy: NFL data loading
- polars: Fast DataFrame operations
- requests: HTTP API calls
