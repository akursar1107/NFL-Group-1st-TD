"""
Add authentication fields to User model
Run this migration to add password_hash, is_admin, and last_login columns
"""
import sys
from pathlib import Path

# Add parent directory to path to import app
parent_dir = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(parent_dir))

from league_webapp.app import create_app, db
from league_webapp.app.models import User
from sqlalchemy import text

def add_auth_columns():
    """Add authentication columns to users table"""
    app = create_app()
    
    with app.app_context():
        # Show database location
        print(f"Using database: {db.engine.url}")
        
        # Check if columns already exist
        inspector = db.inspect(db.engine)
        columns = [col['name'] for col in inspector.get_columns('users')]
        
        print("Current columns:", columns)
        
        # Add columns if they don't exist
        if 'password_hash' not in columns:
            print("Adding password_hash column...")
            with db.engine.connect() as conn:
                conn.execute(text('ALTER TABLE users ADD COLUMN password_hash VARCHAR(255)'))
                conn.commit()
        else:
            print("✓ password_hash column already exists")
        
        if 'is_admin' not in columns:
            print("Adding is_admin column...")
            with db.engine.connect() as conn:
                conn.execute(text('ALTER TABLE users ADD COLUMN is_admin BOOLEAN DEFAULT 0'))
                conn.commit()
        else:
            print("✓ is_admin column already exists")
        
        if 'last_login' not in columns:
            print("Adding last_login column...")
            with db.engine.connect() as conn:
                conn.execute(text('ALTER TABLE users ADD COLUMN last_login DATETIME'))
                conn.commit()
        else:
            print("✓ last_login column already exists")
        
        print("\n✅ Migration complete!")
        print("\nNext steps:")
        print("1. Run: python scripts/setup/create_admin.py")
        print("2. Set passwords for existing users")


if __name__ == '__main__':
    add_auth_columns()
