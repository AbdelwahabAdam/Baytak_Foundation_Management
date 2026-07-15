from urllib.parse import parse_qs, urlparse

from fastapi.testclient import TestClient

from app import emailing


def test_health_login_refresh_logout_and_password_reset_email(client: TestClient, monkeypatch) -> None:
    assert client.get("/health").json() == {"status": "ok"}
    assert client.post(
        "/api/v1/auth/login",
        json={"email": "admin@test.local", "password": "wrong"},
    ).status_code == 401

    login = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@test.local", "password": "AdminPass123!"},
    )
    assert login.status_code == 200
    tokens = login.json()
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    refresh = client.post("/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert refresh.status_code == 200
    assert refresh.json()["access_token"] != tokens["access_token"]

    logout = client.post(
        "/api/v1/auth/logout",
        headers=headers,
        json={"refresh_token": tokens["refresh_token"]},
    )
    assert logout.status_code == 200
    assert client.post("/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]}).status_code == 401

    sent: list[dict] = []
    monkeypatch.setattr(
        "app.routers.auth.send_password_reset_email",
        lambda **kwargs: sent.append(kwargs),
    )
    unknown = client.post("/api/v1/auth/forgot-password", json={"email": "unknown@test.local"})
    assert unknown.status_code == 200
    assert sent == []

    forgot = client.post("/api/v1/auth/forgot-password", json={"email": "admin@test.local"})
    assert forgot.status_code == 200
    assert len(sent) == 1
    assert sent[0]["recipient"] == "admin@test.local"
    reset_token = parse_qs(urlparse(sent[0]["reset_url"]).query)["token"][0]

    reset = client.post(
        "/api/v1/auth/reset-password",
        json={"token": reset_token, "new_password": "NewAdminPass123!"},
    )
    assert reset.status_code == 200
    assert client.post(
        "/api/v1/auth/reset-password",
        json={"token": reset_token, "new_password": "AnotherPass123!"},
    ).status_code == 400
    assert client.post(
        "/api/v1/auth/login",
        json={"email": "admin@test.local", "password": "NewAdminPass123!"},
    ).status_code == 200


def test_authenticated_password_change(client: TestClient, admin_headers: dict[str, str]) -> None:
    response = client.post(
        "/api/v1/auth/change-password",
        headers=admin_headers,
        json={"current_password": "AdminPass123!", "new_password": "ChangedPass123!"},
    )
    assert response.status_code == 200
    assert client.post(
        "/api/v1/auth/login",
        json={"email": "admin@test.local", "password": "ChangedPass123!"},
    ).status_code == 200


def test_email_builder_embeds_logo_and_sends_attachment(monkeypatch) -> None:
    sent_messages = []

    class FakeSMTP:
        def __init__(self, *_args, **_kwargs) -> None:
            pass

        def __enter__(self):
            return self

        def __exit__(self, *_args) -> None:
            return None

        def ehlo(self) -> None:
            return None

        def starttls(self) -> None:
            return None

        def login(self, *_args) -> None:
            return None

        def send_message(self, message) -> None:
            sent_messages.append(message)

    monkeypatch.setattr(emailing.smtplib, "SMTP", FakeSMTP)
    emailing.send_email(
        recipients=["recipient@test.local"],
        subject="Test subject",
        text="Plain text body",
        html="<p>HTML body</p>",
        attachments=[("report.csv", b"amount\n10\n", "text", "csv")],
    )

    assert len(sent_messages) == 1
    message = sent_messages[0]
    content_ids = [part.get("Content-ID") for part in message.walk()]
    filenames = [part.get_filename() for part in message.walk()]
    assert f"<{emailing.BRAND_LOGO_CID}>" in content_ids
    assert "report.csv" in filenames
