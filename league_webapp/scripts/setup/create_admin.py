"""
Script to create an admin user for the NFL First TD League web application.
Run this script to create your first admin account or add additional admins.

Usage:
    cd league_webapp
    python scripts/setup/create_admin.py
"""
import sys
from pathlib import Path

# Add parent directory to path to import app
parent_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(parent_dir))

from app import create_app, db
from app.models import User
from getpass import getpass

def create_admin():
    """Interactive script to create an admin user"""
    app = create_app()
    
    with app.app_context():
        print("=" * 60)
        print("NFL First TD League - Create Admin User")
        print("=" * 60)
        print()
        
        # Get user input
        username = input("Enter username: ").strip()
        
        if not username:
            print("Error: Username cannot be empty")
            return
        
        # Check if user already exists
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            print(f"Error: User '{username}' already exists")
            
            # Ask if they want to make this user an admin
            if not existing_user.is_admin:
                make_admin = input("Would you like to make this user an admin? (y/n): ").strip().lower()
                if make_admin == 'y':
                    existing_user.is_admin = True
                    db.session.commit()
                    print(f"Success! User '{username}' is now an admin.")
                else:
                    print("Operation cancelled.")
            else:
                print(f"Note: User '{username}' is already an admin.")
            
            return
        
        email = input("Enter email: ").strip()
        display_name = input("Enter display name (optional, press Enter to use username): ").strip()
        
        if not display_name:
            display_name = username
        
        # Get password with confirmation
        while True:
            password = getpass("Enter password (min 8 characters): ")
            
            if len(password) < 8:
                print("Error: Password must be at least 8 characters")
                continue
            
            confirm_password = getpass("Confirm password: ")
            
            if password != confirm_password:
                print("Error: Passwords do not match. Please try again.")
                continue
            
            break
        
        # Create user
        try:
            user = User(
                username=username,
                email=email,
                display_name=display_name,
                is_admin=True,
                is_active=True
            )
            user.set_password(password)
            
            db.session.add(user)
            db.session.commit()
            
            print()
            print("=" * 60)
            print("SUCCESS!")
            print("=" * 60)
            print(f"Admin user created successfully:")
            print(f"  Username: {username}")
            print(f"  Email: {email}")
            print(f"  Display Name: {display_name}")
            print(f"  Admin: Yes")
            print()
            print(f"You can now login at: /login")
            print("=" * 60)
            
        except Exception as e:
            db.session.rollback()
            print(f"Error creating user: {e}")
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    create_admin()
