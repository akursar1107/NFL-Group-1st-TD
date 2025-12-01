"""Test the game-touchdowns endpoint"""
import sys
sys.path.insert(0, 'C:\\Users\\akurs\\Desktop\\Vibe Coder\\main')

from app import create_app
import json

app = create_app()

with app.test_client() as client:
    # Get a game from Week 1 2024 to test
    print("Fetching Week 1 2024 games...")
    response = client.get('/api/weekly-games?season=2024&week=1')
    data = response.get_json()
    
    if data['games']:
        # Get the first completed game
        completed_games = [g for g in data['games'] if g['home_score'] is not None]
        if completed_games:
            test_game = completed_games[0]
            game_id = test_game['game_id']
            
            print(f"\nTesting game: {test_game['away_team']} @ {test_game['home_team']}")
            print(f"Final Score: {test_game['away_score']} - {test_game['home_score']}")
            print(f"Game ID: {game_id}\n")
            
            # Test the touchdown endpoint
            print(f"Fetching touchdowns for {game_id}...")
            td_response = client.get(f'/api/game-touchdowns/{game_id}?season=2024')
            td_data = td_response.get_json()
            
            print(f"\nStatus Code: {td_response.status_code}")
            print(f"Found {len(td_data.get('touchdowns', []))} touchdowns:\n")
            
            for td in td_data.get('touchdowns', []):
                first_td_marker = " ⭐ FIRST TD" if td['is_first_td'] else ""
                position = f" ({td['position']})" if td.get('position') else ""
                quarter_time = f"Q{td['quarter']} {td['time']}" if td.get('quarter') and td.get('time') else ""
                
                print(f"{td['order']}. {td['player']}{position} - {td['team']} {quarter_time}{first_td_marker}")
            
            if not td_data.get('touchdowns'):
                print("No touchdowns found (possible defensive game or data issue)")
        else:
            print("No completed games found in Week 1 2024")
    else:
        print("No games found")
