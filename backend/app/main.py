import logging
import time
from contextlib import asynccontextmanager

from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import Counter, Histogram
from prometheus_fastapi_instrumentator import Instrumentator
from sqlalchemy.orm import Session

from app.config import get_settings
from app.db import SessionLocal
from app.models import Role, User
from app.routers import (
    audit,
    auth,
    cases,
    custody,
    dashboard,
    donation_types,
    donations,
    donors,
    reports,
    users,
    warehouse,
)
from app.routers.reports import process_due_scheduled_reports
from app.security import hash_password

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
logger = logging.getLogger("baytak.api")

REQUEST_COUNT = Counter(
    "baytak_http_requests_total",
    "Total HTTP requests handled by the Baytak API",
    ["method", "endpoint", "status_code"],
)
REQUEST_LATENCY = Histogram(
    "baytak_http_request_duration_seconds",
    "HTTP request latency in seconds",
    ["method", "endpoint"],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10),
)


def seed_roles_and_admin(db: Session) -> None:
    role_definitions = {
        "admin": "Full system administration",
        "finance": "Financial management and approvals",
        "staff": "Day-to-day donor and expense work",
        "viewer": "Read-only access",
    }
    existing_roles = {role.name: role for role in db.query(Role).all()}
    for name, description in role_definitions.items():
        if name not in existing_roles:
            existing_roles[name] = Role(name=name, description=description)
            db.add(existing_roles[name])
    db.flush()

    settings = get_settings()
    admin = db.query(User).filter(User.email == settings.bootstrap_admin_email.lower()).first()
    if not admin:
        admin = User(
            first_name="System",
            last_name="Administrator",
            email=settings.bootstrap_admin_email.lower(),
            password_hash=hash_password(settings.bootstrap_admin_password),
            roles=[existing_roles["admin"]],
        )
        db.add(admin)
    db.commit()


@asynccontextmanager
async def lifespan(_: FastAPI):
    db = SessionLocal()
    try:
        seed_roles_and_admin(db)
    finally:
        db.close()
    scheduler: BackgroundScheduler | None = None
    if get_settings().scheduler_enabled:
        scheduler = BackgroundScheduler(timezone="UTC")
        scheduler.add_job(
            process_due_scheduled_reports,
            trigger="interval",
            minutes=1,
            id="scheduled-report-delivery",
            replace_existing=True,
        )
        scheduler.start()
        logger.info("Scheduled report delivery enabled")
    try:
        yield
    finally:
        if scheduler:
            scheduler.shutdown(wait=False)


settings = get_settings()
app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="API for donors, donations, custody accounting, and administration.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def log_and_observe_requests(request: Request, call_next):
    started = time.perf_counter()
    response = await call_next(request)
    elapsed = time.perf_counter() - started
    endpoint = request.url.path
    method = request.method
    status_code = str(response.status_code)
    REQUEST_COUNT.labels(method=method, endpoint=endpoint, status_code=status_code).inc()
    REQUEST_LATENCY.labels(method=method, endpoint=endpoint).observe(elapsed)
    if endpoint not in {"/health", "/metrics"}:
        logger.info(
            "method=%s path=%s status=%s duration_ms=%.1f",
            method,
            endpoint,
            status_code,
            elapsed * 1000,
        )
    return response


Instrumentator(
    should_group_status_codes=False,
    excluded_handlers=["/metrics", "/health"],
).instrument(app).expose(app, endpoint="/metrics", include_in_schema=False)


@app.get("/health", tags=["Health"])
def health_check() -> dict[str, str]:
    return {"status": "ok"}


api_prefix = "/api/v1"
app.include_router(auth.router, prefix=api_prefix)
app.include_router(users.profile_router, prefix=api_prefix)
app.include_router(users.users_router, prefix=api_prefix)
app.include_router(donors.router, prefix=api_prefix)
app.include_router(donation_types.router, prefix=api_prefix)
app.include_router(donations.router, prefix=api_prefix)
app.include_router(custody.profile_router, prefix=api_prefix)
app.include_router(custody.router, prefix=api_prefix)
app.include_router(custody.approvals_router, prefix=api_prefix)
app.include_router(dashboard.router, prefix=api_prefix)
app.include_router(reports.router, prefix=api_prefix)
app.include_router(reports.scheduled_router, prefix=api_prefix)
app.include_router(audit.router, prefix=api_prefix)
app.include_router(warehouse.router, prefix=api_prefix)
app.include_router(cases.router, prefix=api_prefix)
