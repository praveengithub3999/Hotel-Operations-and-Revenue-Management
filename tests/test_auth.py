from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_login_with_valid_credentials():
    response = client.post(
        "/auth/login",
        json={
            "username": "admin",
            "password": "admin123"
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert "access_token" in data
    assert data["token_type"] == "bearer"

def test_login_with_wrong_password():
    response = client.post(
        "/auth/login",
        json={
            "username": "admin",
            "password": "wrongpassword"
        }
    )

    assert response.status_code == 401


def test_login_with_unknown_user():
    response = client.post(
        "/auth/login",
        json={
            "username": "unknown_user",
            "password": "admin123"
        }
    )

    assert response.status_code == 401


def test_protected_endpoint_without_token():
    response = client.get("/hotels/")

    assert response.status_code == 401


def test_protected_endpoint_with_invalid_token():
    client.headers.update({
        "Authorization": "Bearer invalid-token"
    })

    response = client.get("/hotels/")

    assert response.status_code == 401

    client.headers.pop("Authorization", None)

def test_register_new_user():
    response = client.post(
        "/users/register",
        json={
            "username": "testuser",
            "email": "testuser@hotel.com",
            "password": "test123",
            "role": "STAFF"
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert data["username"] == "testuser"
    assert data["email"] == "testuser@hotel.com"
    assert data["role"] == "STAFF"
    assert "password_hash" not in data


def test_register_duplicate_user():
    response = client.post(
        "/users/register",
        json={
            "username": "admin",
            "email": "admin@hotel.com",
            "password": "admin123",
            "role": "ADMIN"
        }
    )

    assert response.status_code == 400