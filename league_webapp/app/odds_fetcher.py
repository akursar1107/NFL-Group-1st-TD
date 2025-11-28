"""
Odds fetching functionality for the web application.
Adapted from firstTD_CLI/odds.py with webapp-specific caching.
"""
import requests
import os
import json
from datetime import datetime, timedelta
import pytz
import polars as pl
from nfl_core.config import (
    API_KEY, BASE_URL, SPORT, REGION, API_TIMEOUT, 
    MARKET_1ST_TD, ODDS_CACHE_EXPIRY, NFL_TEAM_MAP
)


def get_odds_api_event_ids_for_season(schedule_df: pl.DataFrame, api_key: str = None) -> dict:
    """
    Fetches all upcoming NFL events from the Odds API once and maps them to nflreadpy game_ids.
    
    Args:
        schedule_df: Polars DataFrame with NFL schedule
        api_key: The Odds API key (defaults to config.API_KEY)
    
    Returns:
        Dict mapping nflreadpy game_id to Odds API event_id
    """
    if api_key is None:
        api_key = API_KEY
        
    if not api_key:
        print("Warning: No ODDS_API_KEY found in environment")
        return {}
    
    odds_api_event_map = {}
    
    url = f'{BASE_URL}/{SPORT}/events'
    params = {
        'apiKey': api_key,
        'regions': REGION,
        'dateFormat': 'iso',
        'upcoming': 'true'
    }
    
    try:
        resp = requests.get(url, params=params, timeout=API_TIMEOUT)
        resp.raise_for_status()
        odds_events = resp.json()
    except Exception as e:
        print(f"Error fetching Odds API events: {e}")
        return odds_api_event_map

    # Prepare nflreadpy schedule for matching
    nfl_games_for_matching = schedule_df.select([
        pl.col("game_id"),
        pl.col("gameday").str.replace("Z", "+00:00").str.to_datetime(format="%Y-%m-%d", strict=False).alias("nfl_date_dt"),
        pl.col("away_team").replace(NFL_TEAM_MAP, default=pl.col("away_team")).alias("away_team_full"),
        pl.col("home_team").replace(NFL_TEAM_MAP, default=pl.col("home_team")).alias("home_team_full")
    ]).to_dicts()

    for nfl_game in nfl_games_for_matching:
        nfl_game_id = nfl_game['game_id']
        nfl_date = nfl_game['nfl_date_dt']
        nfl_away_full = nfl_game['away_team_full']
        nfl_home_full = nfl_game['home_team_full']

        if not nfl_date:
            continue

        for odds_event in odds_events:
            odds_event_id = odds_event['id']
            odds_home_team = odds_event['home_team']
            odds_away_team = odds_event['away_team']
            odds_commence_time_str = odds_event['commence_time']

            try:
                odds_commence_dt = datetime.fromisoformat(odds_commence_time_str.replace('Z', '+00:00')).astimezone(pytz.utc)
                nfl_date_utc = nfl_date.replace(tzinfo=pytz.utc)
                
                # Check if dates match (allow for 1 day difference due to timezone/late games)
                nfl_date_date = nfl_date_utc.date()
                odds_date_date = odds_commence_dt.date()
                date_match = (nfl_date_date == odds_date_date) or \
                             (odds_date_date == nfl_date_date + timedelta(days=1))
                
                home_match = (nfl_home_full.lower() in odds_home_team.lower()) or \
                             (odds_home_team.lower() in nfl_home_full.lower())
                away_match = (nfl_away_full.lower() in odds_away_team.lower()) or \
                             (odds_away_team.lower() in nfl_away_full.lower())

                if date_match and home_match and away_match:
                    odds_api_event_map[nfl_game_id] = odds_event_id
                    break
            except (ValueError, AttributeError):
                continue
    
    return odds_api_event_map


def fetch_odds_data(event_id: str, api_key: str = None, cache_dir: str = None):
    """
    Fetches odds data for a given event_id, with file-based caching.
    
    Args:
        event_id: The Odds API event ID
        api_key: The Odds API key (defaults to config.API_KEY)
        cache_dir: Directory for caching (defaults to ../cache/odds)
    
    Returns:
        Dict with odds data or None on failure
    """
    if api_key is None:
        api_key = API_KEY
        
    if cache_dir is None:
        # Use path relative to webapp app directory
        cache_dir = os.path.join(os.path.dirname(__file__), '../../cache/odds')
    
    # Ensure cache directory exists
    os.makedirs(cache_dir, exist_ok=True)
    cache_file = os.path.join(cache_dir, f"{event_id}.json")
    
    # Check cache
    if os.path.exists(cache_file):
        file_age = datetime.now().timestamp() - os.path.getmtime(cache_file)
        if file_age < ODDS_CACHE_EXPIRY:
            try:
                with open(cache_file, 'r') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                print(f"Cache file {cache_file} corrupted, fetching fresh data...")

    # Fetch from API
    url = f"{BASE_URL}/{SPORT}/events/{event_id}/odds"
    params = {
        "apiKey": api_key,
        "markets": MARKET_1ST_TD,
        "regions": REGION,
        "oddsFormat": "american"
    }
    
    try:
        response = requests.get(url, params=params, timeout=API_TIMEOUT)
        response.raise_for_status()
        data = response.json()
        
        # Save to cache
        with open(cache_file, 'w') as f:
            json.dump(data, f)
            
        return data
    except Exception as e:
        print(f"Error fetching odds for event ID {event_id}: {e}")
        
        # Try to return stale cache if available
        if os.path.exists(cache_file):
            try:
                with open(cache_file, 'r') as f:
                    print("Returning stale cached data...")
                    return json.load(f)
            except json.JSONDecodeError:
                pass
        
        return None


def get_best_odds_for_game(odds_data: dict) -> dict:
    """
    Processes odds data to find the best price for each player across all bookmakers.
    
    Args:
        odds_data: Raw odds data from fetch_odds_data()
    
    Returns:
        Dict mapping player name to {'price': int, 'bookmaker': str}
    """
    if not odds_data or "bookmakers" not in odds_data:
        return {}
    
    best_prices = {}
    
    for bookmaker in odds_data.get("bookmakers", []):
        bm_title = bookmaker['title']
        
        for market in bookmaker.get('markets', []):
            if market['key'] == MARKET_1ST_TD:
                for outcome in market['outcomes']:
                    player = outcome.get('description', outcome['name'])
                    price = outcome['price']
                    
                    # Keep highest odds (best for bettor)
                    if player not in best_prices or price > best_prices[player]['price']:
                        best_prices[player] = {
                            'price': price,
                            'bookmaker': bm_title
                        }
    
    return best_prices
