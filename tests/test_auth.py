from __future__ import annotations

from backend.models.user import User


def test_register_success(client):
    response = client.post(
        "/auth/register",
        json={"username": "alice", "password": "123456", "nickname": "Alice"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["code"] == 0
    assert data["message"] == "success"
    assert data["data"]["token_type"] == "bearer"
    assert isinstance(data["data"]["access_token"], str)
    assert len(data["data"]["access_token"]) > 20


def test_register_duplicate_username(client):
    client.post("/auth/register", json={"username": "alice", "password": "123456"})
    response = client.post("/auth/register", json={"username": "alice", "password": "123456"})
    assert response.status_code == 400
    data = response.json()
    assert data["code"] == 400
    assert data["message"] == "username already exists"


def test_login_success(client):
    client.post("/auth/register", json={"username": "bob", "password": "123456"})
    response = client.post("/auth/login", json={"username": "bob", "password": "123456"})
    assert response.status_code == 200
    data = response.json()
    assert data["code"] == 0
    assert data["message"] == "success"
    assert data["data"]["token_type"] == "bearer"
    assert isinstance(data["data"]["access_token"], str)


def test_login_invalid_password(client):
    client.post("/auth/register", json={"username": "charlie", "password": "123456"})
    response = client.post("/auth/login", json={"username": "charlie", "password": "wrong-password"})
    assert response.status_code == 401
    data = response.json()
    assert data["code"] == 401
    assert data["message"] == "invalid credentials"


def test_register_validation_error(client):
    response = client.post("/auth/register", json={"username": "ab"})
    assert response.status_code == 422
    data = response.json()
    assert data["code"] == 422
    assert data["message"] == "validation error"


def test_password_is_hashed(client, db_session):
    client.post("/auth/register", json={"username": "david", "password": "123456"})
    user = db_session.query(User).filter(User.username == "david").one()
    assert user.password_hash != "123456"
    assert user.password_hash.startswith("pbkdf2_sha256$")
