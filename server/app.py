"""Routes for JWT auth and user-owned Notes (CRUD + pagination)."""
from typing import cast

from flask import request
from flask_jwt_extended import create_access_token, current_user, jwt_required
from flask_restful import Resource
from marshmallow import ValidationError
from sqlalchemy.exc import IntegrityError

from config import api, app, db, jwt
from models import Note, User, note_schema, notes_schema, user_schema


# ---------- Helpers ----------

def errors_response(messages, status):
    """Every error uses the shape {"errors": [str, ...]} so the client can list them."""
    return {"errors": messages}, status


def flatten_errors(messages):
    """Turn Marshmallow's {field: [msgs]} into ["field: msg", ...]."""
    return [f"{field}: {msg}" for field, msgs in messages.items() for msg in msgs]


def json_body():
    """Return the JSON object body, or None if missing/not an object."""
    data = request.get_json(silent=True)
    return data if isinstance(data, dict) else None


# ---------- JWT callbacks ----------

@jwt.user_lookup_loader
def load_user(_header, payload):
    """Make current_user the User whose id is stored in the token."""
    return db.session.get(User, int(payload["sub"]))


@jwt.unauthorized_loader
def missing_token(_reason):
    return errors_response(["Missing or malformed Authorization header"], 401)


@jwt.invalid_token_loader
def invalid_token(_reason):
    return errors_response(["Invalid token"], 401)


@jwt.expired_token_loader
def expired_token(_header, _payload):
    return errors_response(["Token has expired"], 401)


@jwt.user_lookup_error_loader
def user_not_found(_header, _payload):
    return errors_response(["User no longer exists"], 401)


# ---------- Auth ----------

def auth_response(user, status):
    """The client expects {token, user} after signup and login."""
    token = create_access_token(identity=str(user.id))
    return {"token": token, "user": user_schema.dump(user)}, status


class Signup(Resource):
    def post(self):
        data = json_body()
        if data is None:
            return errors_response(["JSON body required"], 400)
        try:
            valid = cast(dict, user_schema.load(data))
        except ValidationError as err:
            return errors_response(flatten_errors(err.messages), 422)

        confirmation = data.get("password_confirmation")
        if confirmation is not None and confirmation != valid["password"]:
            return errors_response(["password_confirmation: Passwords do not match."], 422)

        username = valid["username"].strip()
        if db.session.execute(db.select(User).filter_by(username=username)).scalar_one_or_none():
            return errors_response(["Username already taken"], 409)

        user = User(username=username)
        user.set_password(valid["password"])
        db.session.add(user)
        try:
            db.session.commit()
        except IntegrityError:  # race on the unique constraint
            db.session.rollback()
            return errors_response(["Username already taken"], 409)

        return auth_response(user, 201)


class Login(Resource):
    def post(self):
        data = json_body() or {}
        username, password = data.get("username"), data.get("password")
        if not isinstance(username, str) or not isinstance(password, str):
            return errors_response(["Username and password required"], 400)

        user = db.session.execute(db.select(User).filter_by(username=username.strip())).scalar_one_or_none()
        # Same message for unknown user and bad password.
        if user is None or not user.authenticate(password):
            return errors_response(["Invalid username or password"], 401)

        return auth_response(user, 200)


class Me(Resource):
    """Lets the client restore a logged-in user from a stored token."""
    method_decorators = [jwt_required()]

    def get(self):
        return user_schema.dump(current_user), 200


# ---------- Notes ----------

def get_owned_note(note_id):
    """Fetch a note only if it belongs to the current user.

    Other users' notes return None (-> 404) so their existence isn't revealed.
    """
    return db.session.execute(
        db.select(Note).filter_by(id=note_id, user_id=current_user.id)
    ).scalar_one_or_none()


DEFAULT_PER_PAGE = 10
MAX_PER_PAGE = 100


class NoteList(Resource):
    method_decorators = [jwt_required()]

    def get(self):
        """Paginated list of the current user's notes. Query: ?page=1&per_page=10"""
        try:
            page = int(request.args.get("page", 1))
            per_page = int(request.args.get("per_page", DEFAULT_PER_PAGE))
        except ValueError:
            return errors_response(["page and per_page must be integers"], 400)
        if page < 1 or per_page < 1:
            return errors_response(["page and per_page must be positive"], 400)
        per_page = min(per_page, MAX_PER_PAGE)

        query = (
            db.select(Note)
            .filter_by(user_id=current_user.id)
            .order_by(Note.created_at.desc(), Note.id.desc())
        )
        pagination = db.paginate(query, page=page, per_page=per_page, error_out=False)
        return {
            "items": notes_schema.dump(pagination.items),
            "page": pagination.page,
            "per_page": pagination.per_page,
            "total": pagination.total,
            "pages": pagination.pages,
            "has_next": pagination.has_next,
            "has_prev": pagination.has_prev,
        }, 200

    def post(self):
        data = json_body()
        if data is None:
            return errors_response(["JSON body required"], 400)
        try:
            valid = cast(dict, note_schema.load(data))
        except ValidationError as err:
            return errors_response(flatten_errors(err.messages), 422)

        # user_id always comes from the token, never from the request.
        note = Note(title=valid["title"].strip(), content=valid["content"], user_id=current_user.id)
        db.session.add(note)
        db.session.commit()
        return note_schema.dump(note), 201


class NoteDetail(Resource):
    method_decorators = [jwt_required()]

    def get(self, note_id):
        note = get_owned_note(note_id)
        if note is None:
            return errors_response(["Note not found"], 404)
        return note_schema.dump(note), 200

    def patch(self, note_id):
        note = get_owned_note(note_id)
        if note is None:
            return errors_response(["Note not found"], 404)
        data = json_body()
        if data is None:
            return errors_response(["JSON body required"], 400)
        try:
            valid = cast(dict, note_schema.load(data, partial=True))
        except ValidationError as err:
            return errors_response(flatten_errors(err.messages), 422)

        if "title" in valid:
            note.title = valid["title"].strip()
        if "content" in valid:
            note.content = valid["content"]
        db.session.commit()
        return note_schema.dump(note), 200

    def delete(self, note_id):
        note = get_owned_note(note_id)
        if note is None:
            return errors_response(["Note not found"], 404)
        db.session.delete(note)
        db.session.commit()
        return "", 204


api.add_resource(Signup, "/signup")
api.add_resource(Login, "/login")
api.add_resource(Me, "/me")
api.add_resource(NoteList, "/notes")
api.add_resource(NoteDetail, "/notes/<int:note_id>")


if __name__ == "__main__":
    app.run(port=5555, debug=True)
