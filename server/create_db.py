"""Create all tables straight from the models, without migrations.

A development shortcut: create_all() only creates missing tables and never
alters existing ones. Use either this or `flask db upgrade` on a given
database file, not both.
"""
from app import app
from config import db

with app.app_context():
    db.create_all()
    print("Tables created.")
