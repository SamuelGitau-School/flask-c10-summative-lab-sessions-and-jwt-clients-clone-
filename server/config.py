"""App and extension setup. Kept separate so models.py and app.py can both
import from here without circular imports."""
import os
from datetime import timedelta

from flask import Flask
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate
from flask_restful import Api
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import MetaData

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URI", "sqlite:///app.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
# Signs the JWTs. Set a real random value via JWT_SECRET_KEY outside development.
app.config["JWT_SECRET_KEY"] = os.environ.get("JWT_SECRET_KEY", "dev-only-change-me-use-a-long-random-string")
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=24)
# Needed so Flask-RESTful lets JWT errors reach the handlers in app.py
# instead of turning them into a generic 500.
app.config["PROPAGATE_EXCEPTIONS"] = True
app.json.compact = False

# Naming convention keeps Alembic migrations deterministic.
metadata = MetaData(naming_convention={
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
})

db = SQLAlchemy(metadata=metadata)
db.init_app(app)
migrate = Migrate(app, db, directory="migration")
bcrypt = Bcrypt(app)
jwt = JWTManager(app)
api = Api(app)
