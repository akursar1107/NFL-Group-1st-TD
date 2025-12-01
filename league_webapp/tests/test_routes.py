
import sys
import os
import pytest
from flask import url_for
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'app')))
from app import create_app, db
from app.models import User

@pytest.fixture(scope='module')
def test_client():
    flask_app = create_app()
    flask_app.config['TESTING'] = True
    flask_app.config['WTF_CSRF_ENABLED'] = False
    flask_app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    with flask_app.app_context():
        db.create_all()
        # Create a test admin user
        existing_admin = User.query.filter_by(username='admin').first()
        if not existing_admin:
            admin = User()
            admin.username = 'admin'
            admin.email = 'admin@example.com'
            admin.display_name = 'Admin'
            admin.is_admin = True
            admin.is_active = True
            admin.set_password('password')
            db.session.add(admin)
            db.session.commit()
    with flask_app.test_client() as testing_client:
        yield testing_client

# List of routes to test (GET only for now, add POST later)
ROUTES = [
    # Admin Tools & Dashboard
    ('/admin/', True),
    ('/admin/sitemap', True),
    ('/admin/grade-current-week', True),
    ('/admin/grade-all', True),
    ('/admin/all-picks', True),
    ('/admin/picks/new', True),
    ('/admin/match-review', True),
    # Data Quality & Match Review
    ('/admin/match-review/bulk-approve', True),
    ('/admin/match-review/bulk-reject', True),
    ('/admin/match-review/bulk-revert-approved', True),
    # Picks & User Management
    ('/user/1', False),
    # Main Pages & Analysis
    ('/', False),
    ('/best-bets', False),
    ('/analysis', False),
    # API Endpoints
    ('/api/health', False),
    ('/api/match-stats', False),
]

def login_admin(client):
    return client.post('/auth/login', data={
        'username': 'admin',
        'password': 'password'
    }, follow_redirects=True)

def test_routes(test_client):
    for route, admin_required in ROUTES:
        if admin_required:
            login_admin(test_client)
        # Use POST for routes that require it
        post_routes = [
            '/admin/grade-current-week',
            '/admin/grade-all',
            '/admin/match-review/bulk-approve',
            '/admin/match-review/bulk-reject',
            '/admin/match-review/bulk-revert-approved'
        ]
        if route in post_routes:
            response = test_client.post(route)
        else:
            response = test_client.get(route)
        if response.status_code not in (200, 302, 401, 403):
            print(f"Route {route} failed with {response.status_code}")
            print(response.data.decode())
        assert response.status_code in (200, 302, 401, 403), f"Route {route} failed with {response.status_code}"
