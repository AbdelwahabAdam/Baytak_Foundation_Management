from fastapi.testclient import TestClient


def test_profile_and_all_user_management_endpoints(
    client: TestClient,
    admin_headers: dict[str, str],
) -> None:
    assert client.get("/api/v1/profile").status_code == 401

    profile = client.get("/api/v1/profile", headers=admin_headers)
    assert profile.status_code == 200
    assert profile.json()["email"] == "admin@test.local"

    updated_profile = client.patch(
        "/api/v1/profile",
        headers=admin_headers,
        json={"first_name": "Updated", "phone_number": "+100000000"},
    )
    assert updated_profile.status_code == 200
    assert updated_profile.json()["first_name"] == "Updated"

    roles = client.get("/api/v1/users/roles", headers=admin_headers)
    assert roles.status_code == 200
    role_ids = {role["name"]: role["id"] for role in roles.json()}

    created = client.post(
        "/api/v1/users",
        headers=admin_headers,
        json={
            "first_name": "Test",
            "last_name": "User",
            "email": "test.user@test.local",
            "password": "UserPass123!",
            "phone_number": "+15550001",
            "role_ids": [role_ids["staff"]],
        },
    )
    assert created.status_code == 201
    user_id = created.json()["id"]

    listed = client.get("/api/v1/users?search=User&active_only=true", headers=admin_headers)
    assert listed.status_code == 200
    assert [user["id"] for user in listed.json()] == [user_id]

    fetched = client.get(f"/api/v1/users/{user_id}", headers=admin_headers)
    assert fetched.status_code == 200

    updated = client.patch(
        f"/api/v1/users/{user_id}",
        headers=admin_headers,
        json={"last_name": "Updated", "is_active": True},
    )
    assert updated.status_code == 200
    assert updated.json()["last_name"] == "Updated"

    assigned = client.post(
        f"/api/v1/users/{user_id}/roles",
        headers=admin_headers,
        json=[role_ids["staff"], role_ids["viewer"]],
    )
    assert assigned.status_code == 200
    assert {role["name"] for role in assigned.json()["roles"]} == {"staff", "viewer"}

    removed = client.delete(
        f"/api/v1/users/{user_id}/roles/{role_ids['viewer']}",
        headers=admin_headers,
    )
    assert removed.status_code == 200
    assert {role["name"] for role in removed.json()["roles"]} == {"staff"}

    reset = client.post(
        f"/api/v1/users/{user_id}/reset-password?new_password=ResetPass123!",
        headers=admin_headers,
    )
    assert reset.status_code == 200
    assert client.post(
        "/api/v1/auth/login",
        json={"email": "test.user@test.local", "password": "ResetPass123!"},
    ).status_code == 200

    disabled = client.post(f"/api/v1/users/{user_id}/disable", headers=admin_headers)
    assert disabled.status_code == 200
    assert client.get(f"/api/v1/users/{user_id}", headers=admin_headers).json()["is_active"] is False
