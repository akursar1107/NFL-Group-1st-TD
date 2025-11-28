"""
Database reset script - Drops all tables and recreates schema with users only
"""
from app import create_app, db
from app.models import User

def reset_database():
    """Drop all tables, recreate schema, and re-seed users"""
    app = create_app()
    
    with app.app_context():
        print("⚠️  WARNING: This will delete ALL data in the database!")
        confirm = input("Type 'YES' to continue: ")
        
        if confirm != 'YES':
            print("❌ Reset cancelled")
            return
        
        # Drop all tables
        print("\n🗑️  Dropping all tables...")
        db.drop_all()
        
        # Recreate schema
        print("🔨 Creating new tables...")
        db.create_all()
        
        # Create league users
        print("👥 Creating league users...")
        users = [
            User(username='Phil', email='phil@example.com', display_name='Phil'),
            User(username='Anders', email='anders@example.com', display_name='Anders'),
            User(username='Neil', email='neil@example.com', display_name='Neil'),
            User(username='Dan C', email='danc@example.com', display_name='Dan C'),
            User(username='Tony', email='tony@example.com', display_name='Tony'),
            User(username='Luke', email='luke@example.com', display_name='Luke'),
            User(username='Jeremy', email='jeremy@example.com', display_name='Jeremy'),
        ]
        db.session.add_all(users)
        db.session.commit()
        
        print(f"\n✅ Database reset complete!")
        print(f"   - Created {len(users)} users: {', '.join(u.username for u in users)}")
        print(f"   - Games table: empty")
        print(f"   - Picks table: empty")
        print(f"   - Bankroll history table: empty")

if __name__ == '__main__':
    reset_database()
