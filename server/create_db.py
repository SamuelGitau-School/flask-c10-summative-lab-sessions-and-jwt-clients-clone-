from app import app
from config import db

with app.app_context():
    db.create_all()
    print("Tables created.")
