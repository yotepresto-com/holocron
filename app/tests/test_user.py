import pytest
from fastapi.testclient import TestClient
from app.main import app  # Adjust this import based on the actual location of your FastAPI app
from app.schemas import UserCreate, UserUpdate

client = TestClient(app)


@pytest.fixture(scope="module")
def new_user():
    user_data = {"username": "testuser", "email": "test@test.com", "password": "password123"}
    return user_data


# Test user creation
def test_create_user(new_user):
    response = client.post("/user/", json=new_user)
    print(response)
    print(response.text)
    assert response.status_code == 200
    assert response.json()["username"] == new_user["username"]
    return response.json()["id"]  # Return the created user's ID for further tests


# Test search user
def test_search_user(new_user):
    response = client.get(f"/user/search/username/{new_user['username']}")
    print(response)
    assert response.status_code == 200
    users = response.json()
    assert isinstance(users, list)  # Check if it's a list
    assert len(users) > 0
    assert users[0]["username"] == new_user["username"]
    return users[0]["id"]  # Return the found user's ID


# Test read user
def test_read_user(new_user):
    user_id = test_search_user(new_user)  # Get user ID from search
    response = client.get(f"/user/{user_id}")
    assert response.status_code == 200
    assert response.json()["id"] == user_id


# Test update user
def test_update_user(new_user):
    user_id = test_search_user(new_user)  # Get user ID from search
    user_update = {"username": "updateduser"}
    response = client.put(f"/user/{user_id}", json=user_update)
    assert response.status_code == 200
    assert response.json()["username"] == user_update["username"]


# Test delete user
def test_delete_user(new_user):
    user_id = test_search_user(new_user)  # Get user ID from search
    response = client.delete(f"/user/{user_id}")
    assert response.status_code == 200
    assert response.json()["detail"] == "User deleted successfully"


# Test list users
def test_list_users():
    response = client.get("/user/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)  # Check if it's a list
