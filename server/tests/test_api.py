import os
os.environ["DATABASE_URI"] = "sqlite:///:memory:"

from datetime import timedelta

import pytest
from flask_jwt_extended import create_access_token

import app as _routes  # registers routes
from config import app, db


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.app_context():
        db.drop_all()
        db.create_all()
    return app.test_client()


def signup(c, name):
    return c.post("/signup", json={
        "username": name, "password": "password123", "password_confirmation": "password123",
    })


def bearer(response):
    return {"Authorization": f"Bearer {response.get_json()['token']}"}


def test_auth_required_and_error_shape(client):
    for r in (client.get("/notes"), client.post("/notes", json={"title": "a", "content": "b"}), client.get("/me")):
        assert r.status_code == 401
        assert isinstance(r.get_json()["errors"], list)
    assert client.get("/me", headers={"Authorization": "Bearer nonsense"}).status_code == 401


def test_expired_token_rejected(client):
    signup(client, "alice")
    with app.app_context():
        token = create_access_token(identity="1", expires_delta=timedelta(seconds=-1))
    r = client.get("/notes", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 401 and r.get_json()["errors"] == ["Token has expired"]


def test_signup_login_me(client):
    r = signup(client, "alice")
    body = r.get_json()
    assert r.status_code == 201 and body["user"]["username"] == "alice" and body["token"]
    assert "password" not in body["user"]
    assert signup(client, "alice").status_code == 409
    bad = client.post("/signup", json={"username": "bob", "password": "password123", "password_confirmation": "nope"})
    assert bad.status_code == 422 and isinstance(bad.get_json()["errors"], list)
    assert client.post("/signup", json={"username": "x", "password": "short"}).status_code == 422
    assert client.post("/login", json={"username": "alice", "password": "wrong"}).status_code == 401
    login = client.post("/login", json={"username": "alice", "password": "password123"})
    assert login.status_code == 200 and login.get_json()["token"]
    me = client.get("/me", headers=bearer(login))
    assert me.status_code == 200 and me.get_json()["username"] == "alice"


def test_crud_and_pagination(client):
    h = bearer(signup(client, "alice"))
    for i in range(12):
        assert client.post("/notes", json={"title": f"t{i}", "content": "c"}, headers=h).status_code == 201
    r = client.get("/notes?page=2&per_page=5", headers=h).get_json()
    assert len(r["items"]) == 5 and r["total"] == 12 and r["pages"] == 3
    nid = r["items"][0]["id"]
    assert client.patch(f"/notes/{nid}", json={"title": "new"}, headers=h).get_json()["title"] == "new"
    assert client.delete(f"/notes/{nid}", headers=h).status_code == 204
    assert client.get(f"/notes/{nid}", headers=h).status_code == 404
    assert client.post("/notes", json={"title": "", "content": "c"}, headers=h).status_code == 422
    assert client.get("/notes?page=abc", headers=h).status_code == 400


def test_users_cannot_touch_each_others_notes(client):
    alice = bearer(signup(client, "alice"))
    nid = client.post("/notes", json={"title": "secret", "content": "x"}, headers=alice).get_json()["id"]
    bob = bearer(signup(client, "bob"))
    assert client.get("/notes", headers=bob).get_json()["total"] == 0
    assert client.get(f"/notes/{nid}", headers=bob).status_code == 404
    assert client.patch(f"/notes/{nid}", json={"title": "hax"}, headers=bob).status_code == 404
    assert client.delete(f"/notes/{nid}", headers=bob).status_code == 404
    # user_id in the body is ignored
    r = client.post("/notes", json={"title": "t", "content": "c", "user_id": 1}, headers=bob).get_json()
    assert r["user_id"] != 1
    # alice's note is still intact
    assert client.get(f"/notes/{nid}", headers=alice).status_code == 200
