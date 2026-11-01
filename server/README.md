# Notes API

## Description

A Flask REST API for a personal productivity app. Users register and log in
(**JWT** authentication, passwords hashed with Flask-Bcrypt) and manage their
own **notes** with full CRUD and a paginated index. Every note belongs to one
user, and all note routes are scoped to the user in the token, so nobody can
read, edit or delete anyone else's notes.

**Stack:** Flask, Flask-RESTful, Flask-SQLAlchemy, Flask-Migrate, Flask-Bcrypt,
Flask-JWT-Extended, Marshmallow, SQLite.

## Installation

All commands below are run from the `server/` folder.

```bash
git clone <your-repo-url> && cd <your-repo>/server
pipenv install
pipenv shell

export FLASK_APP=app.py
flask db upgrade        # apply the migrations
python seed.py          # optional: demo data
```

If you ever change the models, create a new migration with
`flask db migrate -m "message"` and then `flask db upgrade`. See
`migration/README.md` for how the migration folder works.

**Quick alternative (development only):** `python create_db.py` builds the
tables straight from the models without migrations. It only creates missing
tables and never alters existing ones, so use either this or `flask db upgrade`
on a given database file, not both (delete `app.db` when switching).

Seeded demo users: `alice`, `bob`, `carol` (password `password123`), 25 notes each.

Optional environment variables: `JWT_SECRET_KEY` (set a long random value
outside development) and `DATABASE_URI` (default `sqlite:///app.db`).

## Running

```bash
python app.py        # serves on http://localhost:5555
# or
flask run
```

Run the tests with `pytest`.

### With the React client

The JWT client in `client-with-jwt` (next to this folder) proxies API calls to port 5555:

```bash
cd ../client-with-jwt && npm install && npm start
```

## Authentication

Log in or sign up to receive a token, then send it on every protected request:

```
Authorization: Bearer <token>
```

Tokens expire after 24 hours. Logging out is handled by the client discarding
its token, so there is no logout endpoint. A missing, malformed, invalid or
expired token returns `401`.

All errors use the same shape, which is what the client expects:

```json
{"errors": ["Invalid username or password"]}
```

## Endpoints

### Auth

| Method | Route | Description | Success | Errors |
|---|---|---|---|---|
| POST | `/signup` | Create an account. Body: `{username, password, password_confirmation}` (username 3-50 chars, password 8+; confirmation must match if sent) | 201 `{token, user}` | 400, 409 username taken, 422 validation |
| POST | `/login` | Log in. Body: `{username, password}` | 200 `{token, user}` | 400, 401 bad credentials |
| GET | `/me` | Return the user the token belongs to (restores a session on page load) | 200 user | 401 |

### Notes (token required, current user's notes only)

| Method | Route | Description | Success | Errors |
|---|---|---|---|---|
| GET | `/notes?page=1&per_page=10` | Paginated list, newest first (`per_page` max 100) | 200 | 400 bad params, 401 |
| POST | `/notes` | Create. Body: `{title, content}` | 201 note | 400, 401, 422 |
| GET | `/notes/<id>` | Fetch one note | 200 note | 401, 404 |
| PATCH | `/notes/<id>` | Partial update of `title` and/or `content` | 200 note | 400, 401, 404, 422 |
| DELETE | `/notes/<id>` | Delete a note | 204 | 401, 404 |

A note that exists but belongs to someone else returns **404**, the same as a
missing note, so its existence isn't revealed.

**Paginated response shape**

```json
{
  "items": [{"id": 1, "title": "...", "content": "...", "created_at": "...", "updated_at": "...", "user_id": 1}],
  "page": 1, "per_page": 10, "total": 25, "pages": 3, "has_next": true, "has_prev": false
}
```

## Project structure

```
server/
├── app.py          routes, JWT callbacks and error helpers
├── config.py       app, db, migrate, bcrypt, jwt, api setup
├── models.py       User and Note models, Marshmallow schemas
├── create_db.py    dev shortcut: create tables without migrations
├── seed.py         demo data
├── migration/      Flask-Migrate / Alembic (see migration/README.md)
│   └── version/    one file per schema change
└── tests/          pytest suite
```
