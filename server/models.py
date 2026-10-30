"""Database models and Marshmallow schemas."""
from marshmallow import EXCLUDE, Schema, fields, validate

from config import bcrypt, db


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    _password_hash = db.Column(db.String, nullable=False)

    def set_password(self, password):
        """Hash and store the password. The plain text is never saved."""
        self._password_hash = bcrypt.generate_password_hash(password.encode("utf-8")).decode("utf-8")

    def authenticate(self, password):
        """Return True if the password matches the stored hash."""
        return bcrypt.check_password_hash(self._password_hash, password.encode("utf-8"))


_not_blank = validate.Regexp(r"\S", error="Must not be blank.")


class UserSchema(Schema):
    id = fields.Int(dump_only=True)
    username = fields.Str(required=True, validate=[validate.Length(min=3, max=50), _not_blank])
    password = fields.Str(required=True, load_only=True, validate=validate.Length(min=8, max=128))


# EXCLUDE silently drops unknown keys, so clients cannot set fields like id or user_id.
user_schema = UserSchema(unknown=EXCLUDE)
