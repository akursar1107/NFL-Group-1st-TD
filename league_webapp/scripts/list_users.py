from league_webapp.app import create_app, db, models

app = create_app()
with app.app_context():
    users = models.User.query.all()
    print("\nUser List:")
    for u in users:
        print(f"ID: {u.id}, Username: {u.username}, Email: {u.email}, Display Name: {u.display_name}, Admin: {u.is_admin}, Active: {u.is_active}")
