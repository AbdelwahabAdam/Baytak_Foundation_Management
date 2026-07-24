from datetime import datetime, timezone

from fastapi.testclient import TestClient

from app.models import User


def test_admin_assigns_task_and_user_updates_status(
    client: TestClient,
    seeded_users: dict[str, User],
    headers_for,
) -> None:
    admin_headers = headers_for("admin@test.local", "AdminPass123!")
    staff = seeded_users["staff"]
    staff_headers = headers_for("staff@test.local", "UserPass123!")

    create_response = client.post(
        "/api/v1/tasks",
        headers=admin_headers,
        json={
            "title": "Visit warehouse",
            "description": "Count food parcels",
            "assigned_user_id": staff.id,
            "priority": "high",
            "due_date": datetime.now(timezone.utc).isoformat(),
        },
    )
    assert create_response.status_code == 201, create_response.text
    task = create_response.json()
    assert task["title"] == "Visit warehouse"
    assert task["assigned_user"]["email"] == "staff@test.local"
    assert task["status"] == "pending"

    list_admin = client.get(
        f"/api/v1/tasks?assigned_user_id={staff.id}",
        headers=admin_headers,
    )
    assert list_admin.status_code == 200
    assert list_admin.json()["total"] >= 1

    list_staff = client.get("/api/v1/tasks", headers=staff_headers)
    assert list_staff.status_code == 200
    assert any(item["id"] == task["id"] for item in list_staff.json()["items"])

    status_response = client.patch(
        f"/api/v1/tasks/{task['id']}/status",
        headers=staff_headers,
        json={"status": "in_progress"},
    )
    assert status_response.status_code == 200
    assert status_response.json()["status"] == "in_progress"

    finance_headers = headers_for("finance@test.local", "UserPass123!")
    forbidden = client.patch(
        f"/api/v1/tasks/{task['id']}/status",
        headers=finance_headers,
        json={"status": "completed"},
    )
    assert forbidden.status_code == 403

    staff_cannot_create = client.post(
        "/api/v1/tasks",
        headers=staff_headers,
        json={"title": "Nope", "assigned_user_id": staff.id},
    )
    assert staff_cannot_create.status_code == 403


def test_admin_can_filter_tasks_by_date_range(
    client: TestClient,
    seeded_users: dict[str, User],
    headers_for,
) -> None:
    admin_headers = headers_for("admin@test.local", "AdminPass123!")
    staff = seeded_users["staff"]
    created = client.post(
        "/api/v1/tasks",
        headers=admin_headers,
        json={"title": "Dated filter task", "assigned_user_id": staff.id},
    )
    assert created.status_code == 201
    start = "2000-01-01T00:00:00Z"
    end = "2099-12-31T23:59:59Z"
    response = client.get(
        f"/api/v1/tasks?start_date={start}&end_date={end}&search=Dated filter",
        headers=admin_headers,
    )
    assert response.status_code == 200
    assert response.json()["total"] >= 1
