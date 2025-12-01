"""
Script to initialize the database schema for NFL First TD League webapp.
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from league_webapp.app import create_app, db

app = create_app()
with app.app_context():
    db.create_all()
    print("Database schema created successfully.")
