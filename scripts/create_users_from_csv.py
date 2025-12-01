"""
Create users from the picker names in the legacy CSV
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'league_webapp'))

from app import create_app, db
from app.models import User

def create_users():
    """Create users for all pickers"""
    users_to_create = [
        {'username': 'phil', 'display_name': 'Phil', 'email': 'phil@example.com'},
        {'username': 'anders', 'display_name': 'Anders', 'email': 'anders@example.com'},
        {'username': 'neil', 'display_name': 'Neil', 'email': 'neil@example.com'},
        {'username': 'dan_c', 'display_name': 'Dan C', 'email': 'danc@example.com'},
        {'username': 'tony', 'display_name': 'Tony', 'email': 'tony@example.com'},
        {'username': 'luke', 'display_name': 'Luke', 'email': 'luke@example.com'},
        {'username': 'jeremy', 'display_name': 'Jeremy', 'email': 'jeremy@example.com'},
    ]
    
    app = create_app()
    with app.app_context():
        created = 0
        for user_data in users_to_create:
            # Check if user already exists
            existing = User.query.filter_by(username=user_data['username']).first()
            if existing:
                print(f"⚠️  User '{user_data['username']}' already exists (ID: {existing.id})")
                continue
            
            # Create new user
            new_user = User(
                username=user_data['username'],
                display_name=user_data['display_name'],
                email=user_data['email'],
                is_active=True
            )
            new_user.set_password('password123')  # Default password
            
            db.session.add(new_user)
            created += 1
            print(f"✅ Created user: {user_data['display_name']} ({user_data['username']})")
        
        db.session.commit()
        print(f"\n✅ Successfully created {created} users")
        
        # Show all users
        all_users = User.query.all()
        print(f"\nTotal users in database: {len(all_users)}")
        for user in all_users:
            print(f"  ID {user.id}: {user.username} ({user.display_name})")

if __name__ == '__main__':
    create_users()
