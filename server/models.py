"""Database models and Marshmallow schemas."""
from datetime import datetime

from marshmallow import EXCLUDE, Schema, fields, validate

from config import bcrypt, db


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    _password_hash = db.Column(db.String, nullable=False)

    notes = db.relationship("Note", back_populates="user", cascade="all, delete-orphan")

    def set_password(self, password):
        """Hash and store the password. The plain text is never saved."""
        self._password_hash = bcrypt.generate_password_hash(password.encode("utf-8")).decode("utf-8")

    def authenticate(self, password):
        """Return True if the password matches the stored hash."""
        return bcrypt.check_password_hash(self._password_hash, password.encode("utf-8"))


class Note(db.Model):
    __tablename__ = "notes"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)

    user = db.relationship("User", back_populates="notes")


_not_blank = validate.Regexp(r"\S", error="Must not be blank.")


class UserSchema(Schema):
    id = fields.Int(dump_only=True)
    username = fields.Str(required=True, validate=[validate.Length(min=3, max=50), _not_blank])
    password = fields.Str(required=True, load_only=True, validate=validate.Length(min=8, max=128))


class NoteSchema(Schema):
    id = fields.Int(dump_only=True)
    title = fields.Str(required=True, validate=[validate.Length(max=120), _not_blank])
    content = fields.Str(required=True, validate=_not_blank)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)
    user_id = fields.Int(dump_only=True)


# EXCLUDE silently drops unknown keys, so clients cannot set fields like id or user_id.
user_schema = UserSchema(unknown=EXCLUDE)
note_schema = NoteSchema(unknown=EXCLUDE)
notes_schema = NoteSchema(many=True, unknown=EXCLUDE)
