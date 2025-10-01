from fastapi.testclient import TestClient


def test_register_user(client: TestClient):
    response = client.post("/auth/register", json={"login": "newuser", "password": "newpassword"})
    assert response.status_code == 201
    data = response.json()
    assert data["login"] == "newuser"
    assert "id" in data
    assert "is_moderator" in data


def test_register_existing_user_fails(client: TestClient, test_user_token_headers):
    response = client.post("/auth/register", json={"login": "testuser", "password": "password"})
    assert response.status_code == 400
    assert "already registered" in response.json()["detail"]


def test_login_wrong_password(client: TestClient):
    client.post("/auth/register", json={"login": "login_user", "password": "password"})
    response = client.post("/auth/token", data={"username": "login_user", "password": "wrongpassword"})
    assert response.status_code == 401


def test_get_me(client: TestClient, test_user_token_headers):
    response = client.get("/auth/users/me", headers=test_user_token_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["login"] == "testuser"


def test_update_me(client: TestClient, test_user_token_headers):
    response = client.put("/auth/users/me", json={"login": "updateduser"}, headers=test_user_token_headers)
    assert response.status_code == 200
    assert response.json()["login"] == "updateduser"

    response = client.post("/auth/token", data={"username": "testuser", "password": "password"})
    assert response.status_code == 401

    response = client.post("/auth/token", data={"username": "updateduser", "password": "password"})
    assert response.status_code == 200