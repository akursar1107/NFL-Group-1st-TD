import sys, os
ROOT = os.path.join(os.path.dirname(__file__), '..')
sys.path.insert(0, ROOT)

from league_webapp.app import create_app  # type: ignore

app = create_app()

with app.app_context():
    client = app.test_client()
    resp = client.get('/api/picks?season=2025&include_full_names=true')
    print('Status:', resp.status_code)
    if resp.is_json:
        data = resp.get_json()
        print('Total picks:', len(data.get('picks', [])))
        print('First 15 mappings:')
        for p in data.get('picks', [])[:15]:
            print(f"Pick ID {p['id']}: {p['player_name']} => {p.get('full_player_name')}")
    else:
        print('Non-JSON response snippet:', resp.data[:300])
