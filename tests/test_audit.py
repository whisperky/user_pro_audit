import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def get_auth_token():
    # Create and login user
    client.post(
        "/users",
        json={
            "name": "Audit Test",
            "email": "audit@example.com",
            "password": "testpassword"
        }
    )
    response = client.post(
        "/token",
        data={
            "username": "audit@example.com",
            "password": "testpassword"
        }
    )
    return response.json()["access_token"]

def test_user_audit_trail():
    # Get auth token
    token = get_auth_token()
    headers = {"Authorization": f"Bearer {token}"}
    
    # Create test user
    response = client.post(
        "/users",
        json={
            "name": "Audit Trail Test",
            "email": "audit_trail@example.com",
            "password": "testpassword"
        }
    )
    user_id = response.json()["id"]
    
    # Update user
    client.put(
        f"/users/{user_id}",
        headers=headers,
        json={
            "name": "Updated Name",
            "email": "audit_trail@example.com"
        }
    )
    
    # Get audit trail
    response = client.get(f"/audit/users/{user_id}", headers=headers)
    assert response.status_code == 200
    audit_trail = response.json()
    
    # Check audit entries
    assert len(audit_trail) >= 2  # Should have CREATE and UPDATE entries
    assert audit_trail[0]["action"] == "UPDATE"
    assert audit_trail[1]["action"] == "CREATE"

def test_restore_user_version():
    # Get auth token
    token = get_auth_token()
    headers = {"Authorization": f"Bearer {token}"}
    
    # Create test user
    response = client.post(
        "/users",
        json={
            "name": "Restore Test",
            "email": "restore@example.com",
            "password": "testpassword"
        }
    )
    user_id = response.json()["id"]
    
    # Update user
    client.put(
        f"/users/{user_id}",
        headers=headers,
        json={
            "name": "Updated Restore Test",
            "email": "restore@example.com"
        }
    )
    
    # Restore to version 1
    response = client.post(
        f"/audit/users/{user_id}/restore/1",
        headers=headers
    )
    assert response.status_code == 200
    
    # Check if user was restored
    response = client.get(f"/users/{user_id}", headers=headers)
    assert response.status_code == 200
    restored_user = response.json()
    assert restored_user["name"] == "Restore Test"
