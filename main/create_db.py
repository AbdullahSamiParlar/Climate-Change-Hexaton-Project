from main import app, db

with app.app_context():
    db.drop_all()  # Drop all tables
    db.create_all()  # Recreate all tables
    print("Database reset successfully.")
