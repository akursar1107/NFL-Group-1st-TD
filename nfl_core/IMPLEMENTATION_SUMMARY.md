# nfl_core Shared Package Implementation Summary

## ✅ Completed

### Package Structure Created
- `main/nfl_core/` - Shared NFL statistics and data utilities package
- Files created:
  - `__init__.py` - Package initialization with exports
  - `config.py` - API configuration and NFL_TEAM_MAP
  - `data.py` - NFL data loading functions (3 functions)
  - `stats.py` - NFL statistics functions (10 functions)
  - `setup.py` - Package installation configuration
  - `requirements.txt` - Package dependencies
  - `README.md` - Package documentation

### Package Installation
- Installed as editable package in workspace venv:
  ```
  pip install -e main/nfl_core
  ```
- Both firstTD_CLI and league_webapp use the same venv

### Import Updates - firstTD_CLI
Updated 3 files to use nfl_core imports:
1. `main.py` - Changed from `from config/data/stats import ...` to `from nfl_core.* import ...`
2. `ui.py` - Updated imports for MARKET_1ST_TD, calculate_fair_odds, etc.
3. `odds.py` - Updated config imports

### Import Updates - league_webapp
Updated 4 files to remove sys.path.insert() hacks:
1. `grade_week.py` - Removed sys.path.insert(), now imports from nfl_core
2. `auto_grade.py` - Removed sys.path.insert(), now imports from nfl_core
3. `app/routes.py` - Removed sys.path.insert(), now imports from nfl_core
4. `scripts/testing/test_atts_grading.py` - Removed sys.path.insert()

All files now use clean imports:
```python
from nfl_core.stats import get_first_td_scorers
from nfl_core.data import load_data_with_cache
from nfl_core.config import API_KEY, NFL_TEAM_MAP
```

### Verification
- ✅ firstTD_CLI imports working - test_imports.py passed
- ✅ league_webapp imports working - test_imports.py passed
- ✅ No more sys.path.insert() in any file
- ✅ Single source of truth for NFL grading logic

## Benefits Achieved

### 1. Code Deduplication
- Before: stats.py duplicated in both apps
- After: Single stats.py in nfl_core shared by both

### 2. Cleaner Imports
- Before: `sys.path.insert(0, r'c:\Users\akurs\Desktop\Vibe Coder\main\firstTD_CLI')`
- After: `from nfl_core.stats import get_first_td_scorers`

### 3. Maintainability
- Changes to grading logic only need to be made once
- Both apps automatically get updates
- Easier to test and debug

### 4. Portability
- No hardcoded absolute paths
- Works on any machine after `pip install -e nfl_core`
- Proper Python package structure

## Package Contents

### nfl_core.config
- `API_KEY` - Odds API key from environment
- `SPORT`, `REGION`, `BASE_URL` - API constants
- `NFL_TEAM_MAP` - Team abbreviations to full names (32 teams)

### nfl_core.data
- `is_standalone_game()` - Polars expression for primetime games
- `get_season_games(season)` - Load schedule with standalone flag
- `load_data_with_cache(season, cache_dir, use_cache)` - Load schedule/pbp/roster

### nfl_core.stats (10 functions)
1. `get_first_td_scorers()` - Core grading function
2. `get_player_season_stats()` - Calculate TD probabilities
3. `get_player_position()` - Position lookup from roster
4. `calculate_defense_rankings()` - Defense vs position rankings
5. `calculate_fair_odds()` - Convert probability to American odds
6. `get_red_zone_stats()` - Red zone opportunities and TDs
7. `get_opening_drive_stats()` - Opening drive usage
8. `calculate_kelly_criterion()` - Bet sizing formula
9. `get_team_red_zone_splits()` - Team run/pass percentages
10. `identify_funnel_defenses()` - Pass/run funnel classification

## Dependencies
- nflreadpy - NFL play-by-play data
- polars - Fast DataFrame operations
- requests - HTTP API calls

## Usage Example

```python
# In firstTD_CLI or league_webapp
from nfl_core.data import load_data_with_cache
from nfl_core.stats import get_first_td_scorers

# Load data
schedule_df, pbp_df, roster_df = load_data_with_cache(2025)

# Get first TD scorers
first_td_map = get_first_td_scorers(pbp_df, roster_df=roster_df)
```

## Next Steps (Optional Future Improvements)

### 1. Testing
- Add unit tests for nfl_core functions
- Test different seasons and edge cases
- Verify probability calculations

### 2. Documentation
- Add docstring examples to all functions
- Create usage guide with real examples
- Document data formats and return types

### 3. Optimization
- Profile performance bottlenecks
- Add caching for expensive calculations
- Optimize Polars queries

### 4. Expansion
- Add more advanced statistics
- Support playoff games
- Add player injury data integration

## File Changes Log

### Created (7 files)
- `main/nfl_core/__init__.py`
- `main/nfl_core/config.py`
- `main/nfl_core/data.py`
- `main/nfl_core/stats.py`
- `main/nfl_core/setup.py`
- `main/nfl_core/requirements.txt`
- `main/nfl_core/README.md`

### Modified (7 files)
- `main/firstTD_CLI/main.py` - Updated imports
- `main/firstTD_CLI/ui.py` - Updated imports
- `main/firstTD_CLI/odds.py` - Updated imports
- `main/league_webapp/grade_week.py` - Removed sys.path, updated imports
- `main/league_webapp/auto_grade.py` - Removed sys.path, updated imports
- `main/league_webapp/app/routes.py` - Removed sys.path, updated imports
- `main/league_webapp/scripts/testing/test_atts_grading.py` - Removed sys.path

### Not Modified (Kept Separate)
- `main/league_webapp/app/nfl_utils/` - Web-specific utilities (unused)
- `main/firstTD_CLI/config.py` - CLI-specific config (can be removed if unused)
- `main/firstTD_CLI/data.py` - CLI-specific data functions (can be removed if unused)
- `main/firstTD_CLI/stats.py` - Original CLI stats (can be removed if unused)

## Cleanup Recommendations

### Safe to Remove (After Testing)
If firstTD_CLI only uses nfl_core imports, these original files can be archived:
- `main/firstTD_CLI/config.py` → archive/
- `main/firstTD_CLI/data.py` → archive/
- `main/firstTD_CLI/stats.py` → archive/

These are now duplicates of nfl_core modules.

### Keep Separate
- `main/firstTD_CLI/odds.py` - CLI-specific odds fetching
- `main/firstTD_CLI/ui.py` - CLI-specific display formatting
- `main/league_webapp/app/data_loader.py` - Web-specific data loading wrapper

## Success Metrics

✅ All imports working in both applications
✅ No sys.path.insert() calls remaining
✅ Single source of truth for grading logic
✅ Proper Python package structure
✅ Editable installation for development
✅ Clean, maintainable codebase
