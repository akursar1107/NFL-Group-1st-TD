"""
Migration script to add MatchDecision table for fuzzy matching.

Run this script to add the new match_decisions table to your database.
"""

import sys
import os

# Add the parent directory to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from app.models import MatchDecision

def migrate():
    """Create the MatchDecision table"""
    app = create_app()
    
    with app.app_context():
        print("Creating MatchDecision table...")
        
        # Create the table
        db.create_all()
        
        print("✓ Migration completed successfully!")
        print("The match_decisions table has been created.")
        
        # Show table info
        inspector = db.inspect(db.engine)
        if 'match_decisions' in inspector.get_table_names():
            columns = inspector.get_columns('match_decisions')
            print(f"\nTable structure ({len(columns)} columns):")
            for col in columns:
                print(f"  - {col['name']}: {col['type']}")
        else:
            print("\n⚠ Warning: Table not found in database")

if __name__ == '__main__':
    migrate()
