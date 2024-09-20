import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy import text
from app.core.permission import Permission
from app.database import engine
from app.main import app

client = TestClient(app)


@pytest.fixture(scope="function", autouse=True)
def setup_and_teardown():
    yield
    # Truncate the "user" table after each test
    with engine.begin() as connection:
        connection.execute(text("TRUNCATE role CASCADE"))
        connection.execute(text("TRUNCATE role_permission CASCADE"))
        connection.execute(text("TRUNCATE user_role CASCADE"))


@pytest.fixture
def role_data():
    return {
        "name": "superadmin",
        "description": "Administrator role with full permissions",
        "permissions": [
            Permission.CREATE_ROLE,
            Permission.READ_ROLE,
            Permission.DELETE_ROLE,
        ],
    }


def test_create_role(role_data):
    response = client.post("/roles/", json=role_data)
    print(response)
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["name"] == role_data["name"]
    assert data["description"] == role_data["description"]
    assert set(data["permissions"]) == set(
        [perm.value for perm in role_data["permissions"]]
    )


def test_create_role_duplicate(role_data):
    # Create role
    client.post("/roles/", json=role_data)
    # Attempt to create the same role again
    response = client.post("/roles/", json=role_data)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["detail"] == "Role with this name already exists"


def test_list_roles(role_data):
    # Create Role
    client.post("/roles/", json=role_data)
    # Query role
    response = client.get("/roles/")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1  # At least one role exists
    # Check the first role matches
    first_role = data[0]
    assert first_role["name"] == role_data["name"]


def test_read_role():
    # First, create a role to read
    role_payload = {
        "name": "editor",
        "description": "Editor role with limited permissions",
        "permissions": [Permission.READ_USER, Permission.CREATE_USER],
    }
    create_response = client.post("/roles/", json=role_payload)
    assert create_response.status_code == status.HTTP_201_CREATED
    role_id = create_response.json()["id"]

    # Now, read the role
    response = client.get(f"/roles/{role_id}")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["id"] == role_id
    assert data["name"] == role_payload["name"]
    assert data["description"] == role_payload["description"]
    assert set(data["permissions"]) == set(
        [perm.value for perm in role_payload["permissions"]]
    )


def test_read_role_not_found():
    response = client.get("/roles/9999")  # Assuming this ID doesn't exist
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "Role not found"


def test_update_role():
    # First, create a role to update
    create_response = client.post(
        "/roles/",
        json={
            "name": "user",
            "description": "User role",
            "permissions": [Permission.READ_ROLE],
        },
    )
    assert create_response.status_code == status.HTTP_201_CREATED
    role_id = create_response.json()["id"]

    # Update the role
    updated_role_data = {
        "name": "modifieduser",
        "description": "User role modified",
        "permissions": [Permission.CREATE_ROLE, Permission.READ_ROLE],
    }
    response = client.put(f"/roles/{role_id}", json=updated_role_data)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["name"] == updated_role_data["name"]
    assert data["description"] == updated_role_data["description"]
    assert set(data["permissions"]) == set(
        [perm.value for perm in updated_role_data["permissions"]]
    )


def test_update_role_duplicate_name():
    # Create two roles
    role1 = {
        "name": "role1",
        "description": "First role",
        "permissions": [Permission.READ_ROLE],
    }
    role2 = {
        "name": "role2",
        "description": "Second role",
        "permissions": [Permission.CREATE_ROLE],
    }

    create_response1 = client.post("/roles/", json=role1)
    assert create_response1.status_code == status.HTTP_201_CREATED
    role1_id = create_response1.json()["id"]

    create_response2 = client.post("/roles/", json=role2)
    assert create_response2.status_code == status.HTTP_201_CREATED
    role2_id = create_response2.json()["id"]

    # Attempt to update role2's name to role1's name
    update_payload = {"name": "role1"}
    response = client.put(f"/roles/{role2_id}", json=update_payload)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["detail"] == "Role with this name already exists"


def test_delete_role():
    # First, create a role to delete
    create_response = client.post(
        "/roles/",
        json={
            "name": "temp_role",
            "description": "Temporary role",
            "permissions": [Permission.READ_ROLE],
        },
    )
    assert create_response.status_code == status.HTTP_201_CREATED
    role_id = create_response.json()["id"]

    # Delete the role
    response = client.delete(f"/roles/{role_id}")
    assert response.status_code == status.HTTP_204_NO_CONTENT

    # Ensure the role is deleted
    get_response = client.get(f"/roles/{role_id}")
    assert get_response.status_code == status.HTTP_404_NOT_FOUND
