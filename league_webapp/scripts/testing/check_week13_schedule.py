import nflreadpy as nfl
import polars as pl

# Load schedule
schedule = nfl.load_schedules(seasons=2025)
if not isinstance(schedule, pl.DataFrame):
    schedule = pl.from_pandas(schedule)

# Filter for Week 13
w13 = schedule.filter(pl.col('week') == 13)

print(f'Week 13 games from nflreadpy ({w13.height} total):')
games = w13.select(['game_id', 'away_team', 'home_team', 'gameday']).to_dicts()
for g in sorted(games, key=lambda x: x['gameday']):
    print(f'  {g["away_team"]} @ {g["home_team"]} ({g["gameday"]})')
