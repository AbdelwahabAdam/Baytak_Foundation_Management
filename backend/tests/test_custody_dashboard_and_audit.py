from fastapi.testclient import TestClient


def test_custody_profiles_approvals_dashboard_and_audit(
    client: TestClient,
    admin_headers: dict[str, str],
    finance_headers: dict[str, str],
    staff_headers: dict[str, str],
    seeded_users,
) -> None:
    staff_id = seeded_users["staff"].id
    assignment = client.post(
        "/api/v1/custody",
        headers=admin_headers,
        json={
            "user_id": staff_id,
            "amount": "500.00",
            "assigned_at": "2026-01-15T08:00:00Z",
            "description": "Field support",
        },
    )
    assert assignment.status_code == 201
    assignment_id = assignment.json()["id"]

    listed = client.get(
        f"/api/v1/custody?user_id={staff_id}&amount_min=400",
        headers=finance_headers,
    )
    assert listed.status_code == 200
    assert listed.json()["total"] == 1
    assert client.get(f"/api/v1/custody/{assignment_id}", headers=staff_headers).status_code == 200

    updated = client.patch(
        f"/api/v1/custody/{assignment_id}",
        headers=admin_headers,
        json={"description": "Updated field support"},
    )
    assert updated.status_code == 200
    assert updated.json()["description"] == "Updated field support"

    assert client.get("/api/v1/profile/custody", headers=staff_headers).status_code == 200
    assert client.get("/api/v1/profile/custody-expenses", headers=staff_headers).json() == []
    assert client.get(f"/api/v1/custody/{assignment_id}/expenses", headers=staff_headers).json() == []

    expense_one = client.post(
        f"/api/v1/custody/{assignment_id}/expenses",
        headers=staff_headers,
        json={
            "title": "Medical supplies",
            "description": "First-aid materials",
            "amount": "120.00",
            "expense_date": "2026-01-16T09:00:00Z",
        },
    )
    assert expense_one.status_code == 201
    expense_one_id = expense_one.json()["id"]

    expense_two = client.post(
        f"/api/v1/profile/custody-expenses?assignment_id={assignment_id}",
        headers=staff_headers,
        json={
            "title": "Transport",
            "amount": "80.00",
            "expense_date": "2026-01-17T09:00:00Z",
        },
    )
    assert expense_two.status_code == 201
    expense_two_id = expense_two.json()["id"]

    expenses = client.get(f"/api/v1/custody/{assignment_id}/expenses", headers=staff_headers)
    assert expenses.status_code == 200
    assert len(expenses.json()) == 2
    assert len(client.get("/api/v1/profile/custody-expenses", headers=staff_headers).json()) == 2

    pending = client.get("/api/v1/approvals/custody-expenses", headers=finance_headers)
    assert pending.status_code == 200
    assert {item["id"] for item in pending.json()} == {expense_one_id, expense_two_id}
    assert client.post(
        f"/api/v1/approvals/custody-expenses/{expense_one_id}/reject",
        headers=finance_headers,
        json={"comment": "Receipt required"},
    ).status_code == 200
    approved = client.post(
        f"/api/v1/approvals/custody-expenses/{expense_two_id}/approve",
        headers=finance_headers,
        json={"comment": "Approved"},
    )
    assert approved.status_code == 200
    assert approved.json()["status"] == "approved"

    summary = client.get(f"/api/v1/custody/users/{staff_id}/summary", headers=finance_headers)
    assert summary.status_code == 200
    assert summary.json()["available_balance"] == "420.00"

    for path in (
        "/api/v1/dashboard/summary?period=month",
        "/api/v1/dashboard/donations-by-type?period=week",
        "/api/v1/dashboard/recent-donors?period=day&limit=5",
        "/api/v1/dashboard/custody-summary",
    ):
        assert client.get(path, headers=finance_headers).status_code == 200

    audit = client.get(
        "/api/v1/audit-logs?action=CUSTODY_ASSIGNED&entity_type=custody_assignment",
        headers=admin_headers,
    )
    assert audit.status_code == 200
    assert audit.json()["total"] == 1
