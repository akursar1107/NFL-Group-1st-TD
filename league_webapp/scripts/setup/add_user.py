"""
Add a new user to the database
"""
from app import create_app, db
from app.models import User

def add_user(username, email=None, display_name=None):
    """Add a new user to the database"""
    app = create_app()
    
    with app.app_context():
        # Check if user already exists
        existing = User.query.filter_by(username=username).first()
        if existing:
            print(f"❌ User '{username}' already exists")
            return
        
        # Create user
        if email is None:
            email = f"{username.lower().replace(' ', '')}@example.com"
        
        if display_name is None:
            display_name = username
        
        user = User(
            username=username,
            email=email,
            display_name=display_name
        )
        
        db.session.add(user)
        db.session.commit()
        
        print(f"✅ User '{username}' added successfully")
        print(f"   Email: {email}")
        print(f"   Display Name: {display_name}")

if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1:
        username = sys.argv[1]
        email = sys.argv[2] if len(sys.argv) > 2 else None
        display_name = sys.argv[3] if len(sys.argv) > 3 else None
    else:
        username = input("Enter username: ").strip()
        email = input("Enter email (press Enter for auto-generate): ").strip() or None
        display_name = input("Enter display name (press Enter to use username): ").strip() or None
    
    add_user(username, email, display_name)
