from fastapi.testclient import TestClient


def test_report_and_scheduled_report_endpoints(
    client: TestClient,
    finance_headers: dict[str, str],
    monkeypatch,
) -> None:
    for path in (
        "/api/v1/reports/donations?start_date=2026-01-01T00:00:00Z&end_date=2026-12-31T23:59:59Z",
        "/api/v1/reports/donors?start_date=2026-01-01T00:00:00Z&end_date=2026-12-31T23:59:59Z",
        "/api/v1/reports/custody?start_date=2026-01-01T00:00:00Z&end_date=2026-12-31T23:59:59Z",
    ):
        assert client.get(path, headers=finance_headers).status_code == 200

    generated = client.post(
        "/api/v1/reports/generate",
        headers=finance_headers,
        json={
            "report_type": "donations",
            "format": "csv",
            "start_date": "2026-01-01T00:00:00Z",
            "end_date": "2026-12-31T23:59:59Z",
        },
    )
    assert generated.status_code == 201
    generated_id = generated.json()["id"]

    history = client.get("/api/v1/reports/generated", headers=finance_headers)
    assert history.status_code == 200
    assert history.json()[0]["id"] == generated_id
    download = client.get(f"/api/v1/reports/generated/{generated_id}/download", headers=finance_headers)
    assert download.status_code == 200
    assert download.headers["content-type"].startswith("text/csv")
    assert b"No data for the selected filters" in download.content

    schedule = client.post(
        "/api/v1/scheduled-reports",
        headers=finance_headers,
        json={
            "name": "Monthly donation report",
            "report_type": "donations",
            "frequency": "monthly",
            "filters_json": {"window": "last_30_days"},
            "recipients_json": ["finance@test.local"],
            "format": "csv",
            "is_active": True,
        },
    )
    assert schedule.status_code == 201
    schedule_id = schedule.json()["id"]
    assert client.get("/api/v1/scheduled-reports", headers=finance_headers).status_code == 200

    updated = client.patch(
        f"/api/v1/scheduled-reports/{schedule_id}",
        headers=finance_headers,
        json={"name": "Updated monthly report", "frequency": "weekly"},
    )
    assert updated.status_code == 200
    assert updated.json()["frequency"] == "weekly"

    sent: list[dict] = []
    monkeypatch.setattr("app.routers.reports.send_email", lambda **kwargs: sent.append(kwargs))
    ran = client.post(f"/api/v1/scheduled-reports/{schedule_id}/run", headers=finance_headers)
    assert ran.status_code == 200
    assert ran.json()["status"] == "completed"
    assert len(sent) == 1
    assert sent[0]["attachments"][0][0].endswith(".csv")

    disabled = client.delete(f"/api/v1/scheduled-reports/{schedule_id}", headers=finance_headers)
    assert disabled.status_code == 204
