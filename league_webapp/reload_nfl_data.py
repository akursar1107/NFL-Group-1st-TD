# reload_nfl_data.py
from app.data_loader import load_data_with_cache_web

if __name__ == "__main__":
    season = 2025  # Change this if you want a different season
    print(f"Reloading NFL data for season {season} (ignoring cache)...")
    load_data_with_cache_web(season, use_cache=False)
    print("Reload complete.")
