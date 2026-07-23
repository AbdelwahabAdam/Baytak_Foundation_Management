import os
from collections.abc import Callable, Generator

os.environ.update(
    {
        "DATABASE_URL": "sqlite+pysqlite://",
        "JWT_SECRET_KEY": "test-only-jwt-secret-key-that-is-long-enough",
        "BOOTSTRAP_ADMIN_EMAIL": "admin@test.local",
        "BOOTSTRAP_ADMIN_PASSWORD": "AdminPass123!",
        "SCHEDULER_ENABLED": "false",
        "SMTP_HOST": "smtp.test.local",
        "SMTP_USERNAME": "mailer@test.local",
        "SMTP_PASSWORD": "test-password",
        "SMTP_FROM": "mailer@test.local",
        "FRONTEND_APP_URL": "https://app.test.local",
    }
)

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.config import get_settings

get_settings.cache_clear()

import app.db as db_module

test_engine = create_engine(
    "sqlite+pysqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestSessionLocal = sessionmaker(
    bind=test_engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
)
db_module.engine = test_engine
db_module.SessionLocal = TestSessionLocal

from app.main import app
from app.models import Base, Role, User
from app.routers import reports as reports_router
from app.security import hash_password
import app.main as main_module

main_module.SessionLocal = TestSessionLocal
reports_router.SessionLocal = TestSessionLocal


@pytest.fixture()
def client(tmp_path) -> Generator[TestClient, None, None]:
    get_settings().report_storage_path = str(tmp_path / "reports")
    # File-backed SQLite is more reliable than bare in-memory across pooled connections.
    db_path = tmp_path / "test.db"
    file_engine = create_engine(
        f"sqlite+pysqlite:///{db_path}",
        connect_args={"check_same_thread": False},
    )
    FileSessionLocal = sessionmaker(
        bind=file_engine,
        autoflush=False,
        autocommit=False,
        expire_on_commit=False,
    )
    db_module.engine = file_engine
    db_module.SessionLocal = FileSessionLocal
    main_module.SessionLocal = FileSessionLocal
    reports_router.SessionLocal = FileSessionLocal
    global TestSessionLocal
    TestSessionLocal = FileSessionLocal
    Base.metadata.drop_all(file_engine)
    Base.metadata.create_all(file_engine)
    with TestClient(app) as test_client:
        yield test_client
    Base.metadata.drop_all(file_engine)
    file_engine.dispose()


@pytest.fixture()
def seeded_users(client: TestClient) -> dict[str, User]:
    session: Session = TestSessionLocal()
    try:
        roles = {role.name: role for role in session.query(Role).all()}
        password = hash_password("UserPass123!")
        finance = User(
            first_name="Fiona",
            last_name="Finance",
            email="finance@test.local",
            password_hash=password,
            roles=[roles["finance"]],
        )
        staff = User(
            first_name="Sam",
            last_name="Staff",
            email="staff@test.local",
            password_hash=password,
            roles=[roles["staff"]],
        )
        viewer = User(
            first_name="Vera",
            last_name="Viewer",
            email="viewer@test.local",
            password_hash=password,
            roles=[roles["viewer"]],
        )
        session.add_all([finance, staff, viewer])
        session.commit()
        return {"finance": finance, "staff": staff, "viewer": viewer}
    finally:
        session.close()


@pytest.fixture()
def headers_for(client: TestClient) -> Callable[[str, str], dict[str, str]]:
    def build(email: str, password: str) -> dict[str, str]:
        response = client.post("/api/v1/auth/login", json={"email": email, "password": password})
        assert response.status_code == 200, response.text
        return {"Authorization": f"Bearer {response.json()['access_token']}"}

    return build


@pytest.fixture()
def admin_headers(headers_for: Callable[[str, str], dict[str, str]]) -> dict[str, str]:
    return headers_for("admin@test.local", "AdminPass123!")


@pytest.fixture()
def finance_headers(
    seeded_users: dict[str, User],
    headers_for: Callable[[str, str], dict[str, str]],
) -> dict[str, str]:
    return headers_for(seeded_users["finance"].email, "UserPass123!")


@pytest.fixture()
def staff_headers(
    seeded_users: dict[str, User],
    headers_for: Callable[[str, str], dict[str, str]],
) -> dict[str, str]:
    return headers_for(seeded_users["staff"].email, "UserPass123!")


@pytest.fixture()
def viewer_headers(
    seeded_users: dict[str, User],
    headers_for: Callable[[str, str], dict[str, str]],
) -> dict[str, str]:
    return headers_for(seeded_users["viewer"].email, "UserPass123!")
