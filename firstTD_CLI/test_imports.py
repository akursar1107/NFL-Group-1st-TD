#!/usr/bin/env python
"""Test that nfl_core package imports work correctly"""

try:
    from nfl_core.stats import get_first_td_scorers, calculate_fair_odds
    from nfl_core.data import load_data_with_cache
    from nfl_core.config import API_KEY, NFL_TEAM_MAP
    print("✅ firstTD_CLI: All nfl_core imports successful!")
    print(f"   - stats module: get_first_td_scorers, calculate_fair_odds")
    print(f"   - data module: load_data_with_cache")
    print(f"   - config module: API_KEY, NFL_TEAM_MAP ({len(NFL_TEAM_MAP)} teams)")
except ImportError as e:
    print(f"❌ Import failed: {e}")
    exit(1)
