from fastapi.testclient import TestClient


def _create_fund(client: TestClient, headers: dict[str, str], name: str = "Sadakat") -> int:
    response = client.post(
        "/api/v1/donation-types",
        headers=headers,
        json={"type_name": name, "description": "Fund", "is_active": True},
    )
    assert response.status_code == 201, response.text
    return response.json()["id"]


def _create_donor(client: TestClient, headers: dict[str, str]) -> int:
    response = client.post(
        "/api/v1/donors",
        headers=headers,
        json={
            "first_name": "Ali",
            "last_name": "Donor",
            "phones": [{"phone_number": "+201000000001", "is_primary": True}],
        },
    )
    assert response.status_code == 201, response.text
    return response.json()["id"]


def test_activities_ledger_and_negative_fund_balance(
    client: TestClient,
    admin_headers: dict[str, str],
    finance_headers: dict[str, str],
    staff_headers: dict[str, str],
    seeded_users,
) -> None:
    fund_id = _create_fund(client, admin_headers)
    donor_id = _create_donor(client, staff_headers)

    activity = client.post(
        "/api/v1/activities",
        headers=finance_headers,
        json={
            "name": "Handicrafts Workshop",
            "description": "Workshop project",
            "activity_type": "workshop",
            "status": "active",
        },
    )
    assert activity.status_code == 201, activity.text
    activity_id = activity.json()["id"]

    donation = client.post(
        "/api/v1/donations",
        headers=staff_headers,
        json={
            "donor_id": donor_id,
            "donation_type_id": fund_id,
            "activity_id": activity_id,
            "amount": "10000.00",
            "currency": "EGP",
            "donation_date": "2026-01-10T10:00:00Z",
            "status": "confirmed",
        },
    )
    assert donation.status_code == 201, donation.text
    donation_id = donation.json()["id"]
    assert donation.json()["activity_id"] == activity_id

    grant = client.post(
        f"/api/v1/activities/{activity_id}/transactions",
        headers=staff_headers,
        json={
            "transaction_type": "grant",
            "amount": "2000.00",
            "description": "Partner grant",
            "transaction_date": "2026-01-11T10:00:00Z",
        },
    )
    assert grant.status_code == 201, grant.text

    expense = client.post(
        f"/api/v1/activities/{activity_id}/transactions",
        headers=staff_headers,
        json={
            "transaction_type": "purchase",
            "amount": "3500.00",
            "description": "Materials",
            "transaction_date": "2026-01-12T10:00:00Z",
        },
    )
    assert expense.status_code == 201, expense.text

    summary = client.get(f"/api/v1/activities/{activity_id}/summary", headers=finance_headers)
    assert summary.status_code == 200
    body = summary.json()
    assert body["total_income"] == "12000.00"
    assert body["total_expense"] == "3500.00"
    assert body["balance"] == "8500.00"
    assert body["donations"] == "10000.00"
    assert body["grants"] == "2000.00"

    txs = client.get(f"/api/v1/activities/{activity_id}/transactions", headers=finance_headers)
    assert txs.status_code == 200
    assert txs.json()["total"] == 3

    reports = client.get(f"/api/v1/activities/{activity_id}/reports", headers=finance_headers)
    assert reports.status_code == 200
    assert reports.json()["profit_loss"]["profit_loss"] == "8500.00"

    second_activity = client.post(
        "/api/v1/activities",
        headers=admin_headers,
        json={"name": "Food Kitchen", "activity_type": "kitchen", "status": "active"},
    ).json()["id"]
    unlinked = client.post(
        "/api/v1/donations",
        headers=staff_headers,
        json={
            "donor_id": donor_id,
            "donation_type_id": fund_id,
            "amount": "500.00",
            "currency": "EGP",
            "donation_date": "2026-01-13T10:00:00Z",
            "status": "confirmed",
        },
    )
    assert unlinked.status_code == 201
    linked = client.post(
        f"/api/v1/activities/{second_activity}/transactions",
        headers=finance_headers,
        json={
            "transaction_type": "donation",
            "reference_id": unlinked.json()["id"],
        },
    )
    assert linked.status_code == 201, linked.text
    assert (
        client.get(f"/api/v1/donations/{unlinked.json()['id']}", headers=finance_headers).json()[
            "activity_id"
        ]
        == second_activity
    )
    donation_count = client.get("/api/v1/donations", headers=finance_headers).json()["total"]
    assert donation_count == 2

    staff_id = seeded_users["staff"].id
    assignment = client.post(
        "/api/v1/custody",
        headers=admin_headers,
        json={
            "user_id": staff_id,
            "donation_type_id": fund_id,
            "activity_id": activity_id,
            "amount": "20000.00",
            "assigned_at": "2026-01-14T08:00:00Z",
            "description": "Workshop float",
        },
    )
    assert assignment.status_code == 201, assignment.text
    assignment_id = assignment.json()["id"]
    assert assignment.json()["donation_type_id"] == fund_id
    assert assignment.json()["activity_id"] == activity_id

    # Assignment is NOT an expense — fund still at donations only.
    funds_before = client.get("/api/v1/dashboard/fund-balances", headers=finance_headers)
    assert funds_before.status_code == 200
    sadakat_before = next(item for item in funds_before.json() if item["id"] == fund_id)
    assert sadakat_before["balance"] == "10500.00"

    custody_expense = client.post(
        f"/api/v1/custody/{assignment_id}/expenses",
        headers=staff_headers,
        json={
            "title": "Workshop materials",
            "amount": "13500.00",
            "expense_date": "2026-01-15T09:00:00Z",
        },
    )
    assert custody_expense.status_code == 201, custody_expense.text
    assert custody_expense.json()["activity_id"] == activity_id
    assert "donation_type_id" not in custody_expense.json()

    approved = client.post(
        f"/api/v1/approvals/custody-expenses/{custody_expense.json()['id']}/approve",
        headers=finance_headers,
        json={"comment": "OK"},
    )
    assert approved.status_code == 200, approved.text

    funds_after = client.get("/api/v1/dashboard/fund-balances", headers=finance_headers)
    sadakat = next(item for item in funds_after.json() if item["id"] == fund_id)
    assert sadakat["total_donations"] == "10500.00"
    assert sadakat["approved_custody_expenses"] == "13500.00"
    assert sadakat["balance"] == "-3000.00"

    activity_summary = client.get(
        f"/api/v1/activities/{activity_id}/summary", headers=finance_headers
    ).json()
    assert activity_summary["total_income"] == "12000.00"
    assert activity_summary["total_expense"] == "17000.00"
    assert activity_summary["balance"] == "-5000.00"

    dashboard = client.get("/api/v1/dashboard/activities-summary", headers=finance_headers)
    assert dashboard.status_code == 200
    assert dashboard.json()["activities_count"] >= 2

    viewer_login = client.post(
        "/api/v1/auth/login",
        json={"email": "viewer@test.local", "password": "UserPass123!"},
    )
    assert viewer_login.status_code == 200
    viewer_headers = {"Authorization": f"Bearer {viewer_login.json()['access_token']}"}
    assert client.get("/api/v1/activities", headers=viewer_headers).status_code == 200
    assert (
        client.post(
            "/api/v1/activities",
            headers=viewer_headers,
            json={"name": "Denied", "activity_type": "x"},
        ).status_code
        == 403
    )

    assert (
        client.get(f"/api/v1/donations/{donation_id}", headers=finance_headers).json()[
            "activity_id"
        ]
        == activity_id
    )


def test_custody_requires_donation_type_fund(
    client: TestClient,
    admin_headers: dict[str, str],
    seeded_users,
) -> None:
    response = client.post(
        "/api/v1/custody",
        headers=admin_headers,
        json={
            "user_id": seeded_users["staff"].id,
            "amount": "100.00",
            "assigned_at": "2026-01-15T08:00:00Z",
        },
    )
    assert response.status_code == 422
