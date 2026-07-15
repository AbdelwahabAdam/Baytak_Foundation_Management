from contextlib import asynccontextmanager

from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from app.config import get_settings
from app.db import SessionLocal
from app.models import Role, User
from app.routers import audit, auth, custody, dashboard, donation_types, donations, donors, reports, users
from app.routers.reports import process_due_scheduled_reports
from app.security import hash_password


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
