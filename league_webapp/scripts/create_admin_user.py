import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app import db, create_app
from app.models import User

app = create_app()
with app.app_context():
    if not User.query.filter_by(username='admin').first():
        admin = User()
        admin.username = 'admin'
        admin.email = 'admin@example.com'
        admin.display_name = 'Admin'
        admin.is_admin = True
        admin.set_password('password')
        db.session.add(admin)
        db.session.commit()
        print('Admin user created.')
    else:
        print('Admin user already exists.')
