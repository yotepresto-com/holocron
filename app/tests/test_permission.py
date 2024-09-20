import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.permission import Permission

client = TestClient(app)


def test_catalog_permissions_endpoint():
    response = client.get("/permission/")
    assert (
        response.status_code == 200
    ), f"Unexpected status code: {response.status_code}"

    # Get the list of permissions from the response
    response_data = response.json()
    assert isinstance(response_data, list), "Response is not a list"

    # Extract permission values from the Permission Enum and from response_data
    expected_permissions = [permission.value for permission in Permission]
    response_permissions = [permission["name"] for permission in response_data]

    # Check that all expected permissions are in the response
    missing_permissions = set(expected_permissions) - set(response_permissions)
    unexpected_permissions = set(response_permissions) - set(expected_permissions)

    assert (
        not missing_permissions
    ), f"Missing permissions in response: {missing_permissions}"
    assert (
        not unexpected_permissions
    ), f"Unexpected permissions in response: {unexpected_permissions}"
