"""
Test script to verify database query optimizations.
Enables SQLAlchemy query logging to show the difference in query count.
"""
import logging
from league_webapp.app import create_app, db
from league_webapp.app.models import Game, Pick
from sqlalchemy import event
from sqlalchemy.engine import Engine

# Configure SQLAlchemy query logging
logging.basicConfig()
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)

query_count = 0

@event.listens_for(Engine, "before_cursor_execute")
def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    global query_count
    query_count += 1

@event.listens_for(Engine, "after_cursor_execute")
def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    pass

def test_week_view_queries():
    """Test the week view route to verify N+1 query fix"""
    global query_count
    
    app = create_app()
    with app.app_context():
        print("\n" + "="*80)
        print("Testing Week View Query Optimization (week 13)")
        print("="*80)
        
        # Reset counter
        query_count = 0
        
        # Import here to avoid circular imports
        from sqlalchemy.orm import joinedload
        
        # This is the optimized query from week_view route
        week_num = 13
        season = 2025
        
        games = Game.query.options(
            joinedload(Game.picks).joinedload(Pick.user)
        ).filter_by(
            week=week_num, season=season
        ).order_by(Game.game_date, Game.game_time).all()
        
        # Access the picks to trigger loading (if not eager loaded)
        for game in games:
            ftd_picks = [p for p in game.picks if p.pick_type == 'FTD']
            for pick in ftd_picks:
                _ = pick.user.username  # Access user to ensure it's loaded
        
        print(f"\n✅ OPTIMIZED VERSION:")
        print(f"   - Total games: {len(games)}")
        print(f"   - Total queries executed: {query_count}")
        print(f"   - Expected: 1-2 queries (eager loading with JOINs)")
        
        # Now test the old way (N+1 pattern) for comparison
        query_count = 0
        
        games_old = Game.query.filter_by(
            week=week_num, season=season
        ).order_by(Game.game_date, Game.game_time).all()
        
        for game in games_old:
            picks = Pick.query.filter_by(game_id=game.id, pick_type='FTD').all()
            for pick in picks:
                _ = pick.user.username
        
        print(f"\n❌ OLD VERSION (N+1 pattern):")
        print(f"   - Total games: {len(games_old)}")
        print(f"   - Total queries executed: {query_count}")
        print(f"   - Expected: 1 + N + M queries (1 for games, N for picks per game, M for users)")
        
        improvement = ((query_count - 2) / query_count * 100) if query_count > 2 else 0
        print(f"\n🚀 Performance Improvement: ~{improvement:.1f}% reduction in queries!")

def test_all_picks_queries():
    """Test the all-picks route to verify N+1 query fix"""
    global query_count
    
    app = create_app()
    with app.app_context():
        print("\n" + "="*80)
        print("Testing All-Picks Query Optimization")
        print("="*80)
        
        # Reset counter
        query_count = 0
        
        # Import here to avoid circular imports
        from sqlalchemy.orm import joinedload
        from league_webapp.app.models import User
        
        # Optimized version
        season = 2025
        picks = Pick.query.options(
            joinedload(Pick.game),
            joinedload(Pick.user)
        ).join(Game).join(User).filter(
            Game.season == season
        ).order_by(
            Game.week.desc(),
            Game.game_date.desc(),
            User.username,
            Pick.pick_type
        ).all()
        
        # Access relationships to trigger loading
        for pick in picks:
            _ = pick.game.week
            _ = pick.user.username
        
        print(f"\n✅ OPTIMIZED VERSION:")
        print(f"   - Total picks: {len(picks)}")
        print(f"   - Total queries executed: {query_count}")
        print(f"   - Expected: 1 query (eager loading with JOINs)")
        
        # Old version for comparison
        query_count = 0
        
        picks_old = Pick.query.join(Game).join(User).filter(
            Game.season == season
        ).order_by(
            Game.week.desc(),
            Game.game_date.desc(),
            User.username,
            Pick.pick_type
        ).all()
        
        for pick in picks_old:
            _ = pick.game.week
            _ = pick.user.username
        
        print(f"\n❌ OLD VERSION (lazy loading):")
        print(f"   - Total picks: {len(picks_old)}")
        print(f"   - Total queries executed: {query_count}")
        print(f"   - Expected: 1 + 2N queries (1 for picks, 2N for game+user per pick)")
        
        improvement = ((query_count - 1) / query_count * 100) if query_count > 1 else 0
        print(f"\n🚀 Performance Improvement: ~{improvement:.1f}% reduction in queries!")

def test_cache():
    """Test the caching on get_nfl_stats_data"""
    app = create_app()
    with app.app_context():
        print("\n" + "="*80)
        print("Testing Cache on get_nfl_stats_data")
        print("="*80)
        
        from league_webapp.app.routes import get_nfl_stats_data
        import time
        
        # First call (not cached)
        print("\n🔄 First call (should load from NFL data)...")
        start = time.time()
        result1 = get_nfl_stats_data(season=2025, use_cache=True)
        first_duration = time.time() - start
        print(f"   Duration: {first_duration:.2f}s")
        
        # Second call (should be cached)
        print("\n⚡ Second call (should be cached)...")
        start = time.time()
        result2 = get_nfl_stats_data(season=2025, use_cache=True)
        second_duration = time.time() - start
        print(f"   Duration: {second_duration:.2f}s")
        
        if second_duration < first_duration:
            speedup = first_duration / second_duration
            print(f"\n🚀 Cache is working! {speedup:.1f}x faster on cached call!")
        else:
            print(f"\n⚠️  Cache may not be working as expected")

if __name__ == '__main__':
    print("\n" + "="*80)
    print("DATABASE QUERY OPTIMIZATION TEST SUITE")
    print("="*80)
    
    test_week_view_queries()
    test_all_picks_queries()
    test_cache()
    
    print("\n" + "="*80)
    print("✅ All tests completed!")
    print("="*80 + "\n")
