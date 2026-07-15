from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import (
    AuditLog,
    CustodyAssignment,
    CustodyExpense,
    ExpenseStatus,
)


def add_audit_log(
    db: Session,
    *,
    actor_user_id: int | None,
    action: str,
    entity_type: str,
    entity_id: int | str,
    old_value: dict | None = None,
    new_value: dict | None = None,
) -> None:
    db.add(
        AuditLog(
            actor_user_id=actor_user_id,
            action=action,
            entity_type=entity_type,
            entity_id=str(entity_id),
            old_value_json=old_value,
            new_value_json=new_value,
        )
    )


def custody_balance(db: Session, assignment_id: int, lock: bool = False) -> Decimal:
    statement = select(CustodyAssignment).where(CustodyAssignment.id == assignment_id)
    if lock:
        statement = statement.with_for_update()
    assignment = db.scalar(statement)
    if not assignment:
        return Decimal("0")
    approved_total = db.scalar(
        select(func.coalesce(func.sum(CustodyExpense.amount), 0)).where(
            CustodyExpense.custody_assignment_id == assignment_id,
            CustodyExpense.status == ExpenseStatus.approved,
        )
    )
    return Decimal(assignment.amount) - Decimal(approved_total or 0)


def custody_summary(db: Session, user_id: int) -> dict[str, Decimal]:
    assignment_total = db.scalar(
        select(func.coalesce(func.sum(CustodyAssignment.amount), 0)).where(
            CustodyAssignment.user_id == user_id
        )
    )
    approved_total = db.scalar(
        select(func.coalesce(func.sum(CustodyExpense.amount), 0))
        .join(CustodyAssignment)
        .where(
            CustodyAssignment.user_id == user_id,
            CustodyExpense.status == ExpenseStatus.approved,
        )
    )
    pending_total = db.scalar(
        select(func.coalesce(func.sum(CustodyExpense.amount), 0))
        .join(CustodyAssignment)
        .where(
            CustodyAssignment.user_id == user_id,
            CustodyExpense.status == ExpenseStatus.pending,
        )
    )
    assigned = Decimal(assignment_total or 0)
    approved = Decimal(approved_total or 0)
    return {
        "assigned_total": assigned,
        "approved_expenses_total": approved,
        "available_balance": assigned - approved,
        "pending_expenses_total": Decimal(pending_total or 0),
    }
