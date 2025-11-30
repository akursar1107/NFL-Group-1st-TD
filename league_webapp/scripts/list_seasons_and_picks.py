
import sys
import os
import glob
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from league_webapp.app import create_app, db
from league_webapp.app.models import Game, Pick

def inspect_db(db_path):
    print(f"\nInspecting: {db_path}")
    # Temporarily override SQLALCHEMY_DATABASE_URI
    os.environ['DATABASE_URL'] = f'sqlite:///{db_path}'
    app = create_app()
    ctx = app.app_context()
    ctx.push()
    try:
        seasons = db.session.query(Game.season).distinct().order_by(Game.season).all()
        if not seasons:
            print("  No seasons found in the database.")
        else:
            for s in seasons:
                pick_count = db.session.query(Pick).join(Game).filter(Game.season == s[0]).count()
                print(f"  Season: {s[0]} | Picks: {pick_count}")
    except Exception as e:
        print(f"  Error reading DB: {e}")
    finally:
        ctx.pop()

if __name__ == "__main__":
    # List all .db files in the workspace
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    db_files = []
    for root, dirs, files in os.walk(base_dir):
        for file in files:
            if file.endswith('.db'):
                db_files.append(os.path.join(root, file))
    if not db_files:
        print("No .db files found in the workspace.")
    for db_path in db_files:
        inspect_db(db_path)
