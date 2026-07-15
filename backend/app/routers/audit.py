from datetime import datetime

from fastapi import APIRouter, Query

from app.dependencies import AdminUser, DbSession
from app.models import AuditLog
from app.schemas import AuditLogOut

router = APIRouter(prefix="/audit-logs", tags=["Audit Logs"])


@router.get("", response_model=dict)
def list_audit_logs(
    _: AdminUser,
    db: DbSession,
    action: str | None = Query(default=None),
    entity_type: str | None = Query(default=None),
    actor_user_id: int | None = Query(default=None),
    start_date: datetime | None = Query(default=None),
    end_date: datetime | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=100),
) -> dict:
    query = db.query(AuditLog)
    if action:
        query = query.filter(AuditLog.action == action)
    if entity_type:
        query = query.filter(AuditLog.entity_type == entity_type)
    if actor_user_id:
        query = query.filter(AuditLog.actor_user_id == actor_user_id)
    if start_date:
        query = query.filter(AuditLog.created_at >= start_date)
    if end_date:
        query = query.filter(AuditLog.created_at <= end_date)
    total = query.count()
    items = (
        query.order_by(AuditLog.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return {
        "items": [AuditLogOut.model_validate(item) for item in items],
        "total": total,
        "page": page,
        "page_size": page_size,
    }
