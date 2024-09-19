
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from app.database import engine

from app.main import app

client = TestClient(app)

@pytest.fixture(scope="function", autouse=True)
def setup_and_teardown():
    yield
    # Truncate the "user" table after each test
    with engine.begin() as connection:
        connection.execute(text('TRUNCATE "user" CASCADE'))



def test_create_user():
    user_data = {
        "username": "testuser",
        "email": "testuser@example.com",
        "name": "Test User",
        "is_active": True
    }
    response = client.post("/user/", json=user_data)
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["username"] == "testuser"
    assert data["email"] == "testuser@example.com"
    assert data["name"] == "Test User"
    assert data["is_active"] == True

def test_create_user_missing_required_fields():
    # Missing username
    user_data = {
        "email": "testuser@example.com",
        "name": "Test User"
    }
    response = client.post("/user/", json=user_data)
    assert response.status_code == 422  # Unprocessable Entity

    # Missing email
    user_data = {
        "username": "testuser",
        "name": "Test User"
    }
    response = client.post("/user/", json=user_data)
    assert response.status_code == 422

def test_create_user_invalid_email():
    user_data = {
        "username": "testuser",
        "email": "invalid-email",
        "name": "Test User"
    }
    response = client.post("/user/", json=user_data)
    assert response.status_code == 422

def test_create_user_duplicate_username():
    user_data = {
        "username": "duplicateuser",
        "email": "user1@example.com",
        "name": "User 1"
    }
    response = client.post("/user/", json=user_data)
    assert response.status_code == 200

    # Attempt to create another user with the same username
    user_data = {
        "username": "duplicateuser",
        "email": "user2@example.com",
        "name": "User 2"
    }
    response = client.post("/user/", json=user_data)
    assert response.status_code == 400

def test_create_user_duplicate_email():
    user_data = {
        "username": "user1",
        "email": "duplicate@example.com",
        "name": "User 1"
    }
    response = client.post("/user/", json=user_data)
    assert response.status_code == 200

    # Attempt to create another user with the same email
    user_data = {
        "username": "user2",
        "email": "duplicate@example.com",
        "name": "User 2"
    }
    response = client.post("/user/", json=user_data)
    assert response.status_code == 400

def test_read_user():
    # First, create a user
    user_data = {
        "username": "testuser2",
        "email": "testuser2@example.com",
        "name": "Test User 2"
    }
    response = client.post("/user/", json=user_data)
    user_id = response.json()["id"]

    # Now, read the user
    response = client.get(f"/user/{user_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "testuser2"
    assert data["email"] == "testuser2@example.com"

def test_update_user():
    # Create a user
    user_data = {
        "username": "testuser3",
        "email": "testuser3@example.com",
        "name": "Test User 3"
    }
    response = client.post("/user/", json=user_data)
    user_id = response.json()["id"]

    # Update the user
    update_data = {
        "email": "updated@example.com",
        "name": "Updated User"
    }
    response = client.put(f"/user/{user_id}", json=update_data)
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "updated@example.com"
    assert data["name"] == "Updated User"

def test_update_user_duplicate_email():
    # Create two users
    user1_data = {
        "username": "user1",
        "email": "user1@example.com",
        "name": "User 1"
    }
    response = client.post("/user/", json=user1_data)
    user1_id = response.json()["id"]

    user2_data = {
        "username": "user2",
        "email": "user2@example.com",
        "name": "User 2"
    }
    response = client.post("/user/", json=user2_data)
    user2_id = response.json()["id"]

    # Attempt to update user2's email to user1's email
    update_data = {
        "email": "user1@example.com"
    }
    response = client.put(f"/user/{user2_id}", json=update_data)
    assert response.status_code == 400

def test_delete_user():
    # Create a user
    user_data = {
        "username": "testuser4",
        "email": "testuser4@example.com",
        "name": "Test User 4"
    }
    response = client.post("/user/", json=user_data)
    user_id = response.json()["id"]

    # Delete the user
    response = client.delete(f"/user/{user_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["detail"] == "User deleted successfully"

    # Verify the user is deleted
    response = client.get(f"/user/{user_id}")
    assert response.status_code == 404

def test_list_users():
    # Create multiple users
    for i in range(5):
        user_data = {
            "username": f"testuser{i}",
            "email": f"testuser{i}@example.com",
            "name": f"Test User {i}"
        }
        client.post("/user/", json=user_data)

    # List users
    response = client.get("/user/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 5

def test_search_user_by_email():
    # Create a user
    user_data = {
        "username": "testuser5",
        "email": "testuser5@example.com",
        "name": "Test User 5"
    }
    client.post("/user/", json=user_data)

    # Search by email
    response = client.get("/user/search/email/testuser5@example.com")
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "testuser5"

def test_search_user_by_username():
    # Create a user
    user_data = {
        "username": "testuser6",
        "email": "testuser6@example.com",
        "name": "Test User 6"
    }
    client.post("/user/", json=user_data)

    # Search by username
    response = client.get("/user/search/username/testuser6")
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "testuser6@example.com"

def test_activate_user():
    # Create a user with is_active=False
    user_data = {
        "username": "testuser7",
        "email": "testuser7@example.com",
        "name": "Test User 7",
        "is_active": False
    }
    response = client.post("/user/", json=user_data)
    user_id = response.json()["id"]

    # Activate the user
    response = client.put(f"/user/{user_id}/activate")
    assert response.status_code == 200
    data = response.json()
    assert data["detail"] == "User activated successfully"
    assert data["user"]["is_active"] == True

def test_deactivate_user():
    # Create a user with is_active=True
    user_data = {
        "username": "testuser8",
        "email": "testuser8@example.com",
        "name": "Test User 8",
        "is_active": True
    }
    response = client.post("/user/", json=user_data)
    user_id = response.json()["id"]

    # Deactivate the user
    response = client.put(f"/user/{user_id}/deactivate")
    assert response.status_code == 200
    data = response.json()
    assert data["detail"] == "User deactivated successfully"
    assert data["user"]["is_active"] == False

def test_user_not_found():
    # Attempt to get a non-existent user
    response = client.get("/user/999")
    assert response.status_code == 404
    data = response.json()
    assert data["detail"] == "User not found"

def test_update_user_not_found():
    # Attempt to update a non-existent user
    update_data = {
        "email": "nonexistent@example.com",
        "name": "Nonexistent User"
    }
    response = client.put("/user/999", json=update_data)
    assert response.status_code == 404
    data = response.json()
    assert data["detail"] == "User not found"

def test_delete_user_not_found():
    # Attempt to delete a non-existent user
    response = client.delete("/user/999")
    assert response.status_code == 404
    data = response.json()
    assert data["detail"] == "User not found"

def test_invalid_limit_offset():
    # Test invalid limit and offset values
    response = client.get("/user/?limit=-1")
    assert response.status_code == 422  # Unprocessable Entity

    response = client.get("/user/?offset=-1")
    assert response.status_code == 422

def test_list_users_pagination():
    # Create 50 users
    for i in range(50):
        user_data = {
            "username": f"user{i}",
            "email": f"user{i}@example.com",
            "name": f"User {i}"
        }
        client.post("/user/", json=user_data)

    # Test pagination
    response = client.get("/user/?offset=10&limit=5")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 5
    assert data[0]["username"] == "user10"

def test_create_user_name_optional():
    user_data = {
        "username": "testuser_no_name",
        "email": "testuser_no_name@example.com"
    }
    response = client.post("/user/", json=user_data)
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "testuser_no_name"
    assert data["email"] == "testuser_no_name@example.com"
    assert data["name"] is None

def test_update_user_clear_name():
    # Create a user with a name
    user_data = {
        "username": "testuser9",
        "email": "testuser9@example.com",
        "name": "Test User 9"
    }
    response = client.post("/user/", json=user_data)
    user_id = response.json()["id"]

    # Update the user, setting name to None
    update_data = {
        "name": None
    }
    response = client.put(f"/user/{user_id}", json=update_data)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] is None

def test_create_user_username_too_long():
    user_data = {
        "username": "a" * 51,  # Exceeds max_length of 50
        "email": "testuser@example.com",
        "name": "Test User"
    }
    response = client.post("/user/", json=user_data)
    assert response.status_code == 422

def test_create_user_username_too_short():
    user_data = {
        "username": "",  # min_length is 1
        "email": "testuser@example.com",
        "name": "Test User"
    }
    response = client.post("/user/", json=user_data)
    assert response.status_code == 422

def test_create_user_name_too_long():
    user_data = {
        "username": "testuser",
        "email": "testuser@example.com",
        "name": "a" * 101  # Exceeds max_length of 100
    }
    response = client.post("/user/", json=user_data)
    assert response.status_code == 422

def test_create_user_invalid_is_active():
    user_data = {
        "username": "testuser",
        "email": "testuser@example.com",
        "name": "Test User",
        "is_active": "not_a_boolean"
    }
    response = client.post("/user/", json=user_data)
    assert response.status_code == 422

def test_read_user_invalid_id():
    response = client.get("/user/not_an_id")
    assert response.status_code == 422

def test_search_user_by_email_not_found():
    response = client.get("/user/search/email/nonexistent@example.com")
    assert response.status_code == 404
    data = response.json()
    assert data["detail"] == "User not found"

def test_search_user_by_username_not_found():
    response = client.get("/user/search/username/nonexistentuser")
    assert response.status_code == 404
    data = response.json()
    assert data["detail"] == "User not found"
