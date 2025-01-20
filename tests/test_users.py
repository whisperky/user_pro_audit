import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_create_user():
    response = client.post(
        "/users",
        json={
            "name": "Test User",
            "email": "test@example.com",
            "password": "testpassword"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Test User"
    assert data["email"] == "test@example.com"
    assert "id" in data

def test_create_duplicate_user():
    # Create first user
    client.post(
        "/users",
        json={
            "name": "Duplicate User",
            "email": "duplicate@example.com",
            "password": "testpassword"
        }
    )
    
    # Try to create user with same email
    response = client.post(
        "/users",
        json={
            "name": "Duplicate User 2",
            "email": "duplicate@example.com",
            "password": "testpassword"
        }
    )
    assert response.status_code == 400

def test_login():
    # Create user
    client.post(
        "/users",
        json={
            "name": "Login Test",
            "email": "login@example.com",
            "password": "testpassword"
        }
    )
    
    # Login
    response = client.post(
        "/token",
        data={
            "username": "login@example.com",
            "password": "testpassword"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

def test_get_user_unauthorized():
    response = client.get("/users/1")
    assert response.status_code == 401

def test_get_user_not_found():
    # Login first
    response = client.post(
        "/token",
        data={
            "username": "login@example.com",
            "password": "testpassword"
        }
    )
    token = response.json()["access_token"]
    
    # Try to get non-existent user
    response = client.get(
        "/users/999",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 404
