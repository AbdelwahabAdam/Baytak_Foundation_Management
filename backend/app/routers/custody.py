from datetime import datetime
from decimal import Decimal

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

from app.dependencies import AdminUser, CurrentUser, DbSession, FinanceOrAdminUser
from app.models import (
    CustodyAssignment,
    CustodyExpense,
    CustodyExpenseApproval,
    CustodyStatus,
    ExpenseStatus,
    User,
)
from app.schemas import (
    ApprovalCreate,
    CustodyCreate,
    CustodyExpenseOut,
    CustodyOut,
    CustodySummary,
    CustodyUpdate,
    ExpenseCreate,
)
from app.services import add_audit_log, custody_balance, custody_summary

router = APIRouter(prefix="/custody", tags=["Custody"])
profile_router = APIRouter(prefix="/profile", tags=["Profile"])
approvals_router = APIRouter(prefix="/approvals", tags=["Approvals"])


def custody_query(db: DbSession):
    return db.query(CustodyAssignment).options(
        selectinload(CustodyAssignment.user),
        selectinload(CustodyAssignment.assigned_by),
        selectinload(CustodyAssignment.expenses).selectinload(CustodyExpense.approvals),
    )


def get_custody_or_404(db: DbSession, assignment_id: int) -> CustodyAssignment:
    assignment = custody_query(db).filter(CustodyAssignment.id == assignment_id).first()
    if not assignment:
        raise HTTPException(status_code=404, detail="Custody assignment not found")
    return assignment


def assert_owner_or_finance(user: User, assignment: CustodyAssignment) -> None:
    roles = {role.name for role in user.roles}
    if assignment.user_id != user.id and not roles.intersection({"admin", "finance"}):
        raise HTTPException(status_code=403, detail="You do not have access to this custody assignment")


def serialize_custody(db: DbSession, assignment: CustodyAssignment) -> dict:
    return CustodyOut.model_validate({
        "id": assignment.id,
        "user_id": assignment.user_id,
        "recipient_name": assignment.user.full_name,
        "recipient_email": assignment.user.email,
        "amount": assignment.amount,
        "assigned_by_user_id": assignment.assigned_by_user_id,
        "assigned_by_name": assignment.assigned_by.full_name,
        "assigned_at": assignment.assigned_at,
        "description": assignment.description,
        "status": assignment.status,
        "created_at": assignment.created_at,
        "updated_at": assignment.updated_at,
        "expenses": assignment.expenses,
        "available_balance": custody_balance(db, assignment.id),
    }).model_dump()


@router.get("", response_model=dict)
def list_custody(
    _: FinanceOrAdminUser,
    db: DbSession,
    user_id: int | None = Query(default=None),
    start_date: datetime | None = Query(default=None),
    end_date: datetime | None = Query(default=None),
    amount_min: float | None = Query(default=None, ge=0),
    amount_max: float | None = Query(default=None, ge=0),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
) -> dict:
    query = custody_query(db)
    if user_id:
        query = query.filter(CustodyAssignment.user_id == user_id)
    if start_date:
        query = query.filter(CustodyAssignment.assigned_at >= start_date)
    if end_date:
        query = query.filter(CustodyAssignment.assigned_at <= end_date)
    if amount_min is not None:
        query = query.filter(CustodyAssignment.amount >= amount_min)
    if amount_max is not None:
        query = query.filter(CustodyAssignment.amount <= amount_max)
    total = query.count()
    items = (
        query.order_by(CustodyAssignment.assigned_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return {
        "items": [serialize_custody(db, item) for item in items],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.post("", response_model=CustodyOut, status_code=status.HTTP_201_CREATED)
def create_custody(
    payload: CustodyCreate, admin: AdminUser, db: DbSession
) -> dict:
    recipient = db.query(User).filter(User.id == payload.user_id, User.is_active.is_(True)).first()
    if not recipient:
        raise HTTPException(status_code=400, detail="Selected active user does not exist")
    assignment = CustodyAssignment(
        **payload.model_dump(exclude={"assigned_at"}),
        assigned_at=payload.assigned_at or datetime.now().astimezone(),
        assigned_by_user_id=admin.id,
    )
    db.add(assignment)
    db.flush()
    add_audit_log(
        db,
        actor_user_id=admin.id,
        action="CUSTODY_ASSIGNED",
        entity_type="custody_assignment",
        entity_id=assignment.id,
        new_value={"user_id": assignment.user_id, "amount": str(assignment.amount)},
    )
    db.commit()
    return serialize_custody(db, get_custody_or_404(db, assignment.id))


@router.get("/{assignment_id}", response_model=CustodyOut)
def get_custody(
    assignment_id: int, current_user: CurrentUser, db: DbSession
) -> dict:
    assignment = get_custody_or_404(db, assignment_id)
    assert_owner_or_finance(current_user, assignment)
    return serialize_custody(db, assignment)


@router.patch("/{assignment_id}", response_model=CustodyOut)
def update_custody(
    assignment_id: int, payload: CustodyUpdate, admin: AdminUser, db: DbSession
) -> dict:
    assignment = get_custody_or_404(db, assignment_id)
    values = payload.model_dump(exclude_unset=True)
    if values.get("status") == CustodyStatus.closed and custody_balance(db, assignment.id) != Decimal("0"):
        raise HTTPException(status_code=400, detail="Only a fully spent assignment can be closed")
    for field, value in values.items():
        setattr(assignment, field, value)
    add_audit_log(
        db,
        actor_user_id=admin.id,
        action="CUSTODY_UPDATED",
        entity_type="custody_assignment",
        entity_id=assignment.id,
        new_value={key: str(value) for key, value in values.items()},
    )
    db.commit()
    return serialize_custody(db, get_custody_or_404(db, assignment.id))


@router.get("/{assignment_id}/expenses", response_model=list[CustodyExpenseOut])
def list_expenses(
    assignment_id: int, current_user: CurrentUser, db: DbSession
) -> list[CustodyExpense]:
    assignment = get_custody_or_404(db, assignment_id)
    assert_owner_or_finance(current_user, assignment)
    return assignment.expenses


def submit_expense(
    assignment_id: int, payload: ExpenseCreate, current_user: User, db: DbSession
) -> CustodyExpense:
    assignment = db.scalar(
        select(CustodyAssignment)
        .where(CustodyAssignment.id == assignment_id)
        .with_for_update()
    )
    if not assignment:
        raise HTTPException(status_code=404, detail="Custody assignment not found")
    assert_owner_or_finance(current_user, assignment)
    if assignment.user_id != current_user.id and "admin" not in {role.name for role in current_user.roles}:
        raise HTTPException(status_code=403, detail="Expenses can only be submitted by the assigned user")
    if assignment.status != CustodyStatus.active:
        raise HTTPException(status_code=400, detail="Expenses can only be added to active custody")
    reserved_total = db.scalar(
        select(func.coalesce(func.sum(CustodyExpense.amount), 0)).where(
            CustodyExpense.custody_assignment_id == assignment.id,
            CustodyExpense.status.in_([ExpenseStatus.pending, ExpenseStatus.approved]),
        )
    )
    if Decimal(reserved_total or 0) + payload.amount > Decimal(assignment.amount):
        raise HTTPException(status_code=400, detail="Expense exceeds the remaining custody amount")
    expense = CustodyExpense(
        custody_assignment_id=assignment.id,
        user_id=current_user.id,
        **payload.model_dump(),
    )
    db.add(expense)
    db.flush()
    add_audit_log(
        db,
        actor_user_id=current_user.id,
        action="CUSTODY_EXPENSE_SUBMITTED",
        entity_type="custody_expense",
        entity_id=expense.id,
        new_value={"amount": str(expense.amount), "assignment_id": assignment.id},
    )
    db.commit()
    return (
        db.query(CustodyExpense)
        .options(selectinload(CustodyExpense.approvals))
        .filter(CustodyExpense.id == expense.id)
        .first()
    )


@router.post(
    "/{assignment_id}/expenses",
    response_model=CustodyExpenseOut,
    status_code=status.HTTP_201_CREATED,
)
def create_expense(
    assignment_id: int, payload: ExpenseCreate, current_user: CurrentUser, db: DbSession
) -> CustodyExpense:
    return submit_expense(assignment_id, payload, current_user, db)


@profile_router.get("/custody", response_model=list[CustodyOut])
def get_own_custody(current_user: CurrentUser, db: DbSession) -> list[dict]:
    assignments = (
        custody_query(db)
        .filter(CustodyAssignment.user_id == current_user.id)
        .order_by(CustodyAssignment.assigned_at.desc())
        .all()
    )
    return [serialize_custody(db, assignment) for assignment in assignments]


@profile_router.get("/custody-expenses", response_model=list[CustodyExpenseOut])
def get_own_expenses(current_user: CurrentUser, db: DbSession) -> list[CustodyExpense]:
    return (
        db.query(CustodyExpense)
        .options(selectinload(CustodyExpense.approvals))
        .filter(CustodyExpense.user_id == current_user.id)
        .order_by(CustodyExpense.submitted_at.desc())
        .all()
    )


@profile_router.post(
    "/custody-expenses",
    response_model=CustodyExpenseOut,
    status_code=status.HTTP_201_CREATED,
)
def create_own_expense(
    assignment_id: int,
    payload: ExpenseCreate,
    current_user: CurrentUser,
    db: DbSession,
) -> CustodyExpense:
    return submit_expense(assignment_id, payload, current_user, db)


@router.get("/users/{user_id}/summary", response_model=CustodySummary)
def get_user_custody_summary(
    user_id: int, _: FinanceOrAdminUser, db: DbSession
) -> dict:
    if not db.query(User.id).filter(User.id == user_id).first():
        raise HTTPException(status_code=404, detail="User not found")
    return {"user_id": user_id, **custody_summary(db, user_id)}


@approvals_router.get("/custody-expenses", response_model=list[CustodyExpenseOut])
def list_pending_expenses(
    _: FinanceOrAdminUser, db: DbSession
) -> list[CustodyExpense]:
    return (
        db.query(CustodyExpense)
        .options(selectinload(CustodyExpense.approvals))
        .filter(CustodyExpense.status == ExpenseStatus.pending)
        .order_by(CustodyExpense.submitted_at)
        .all()
    )


def decide_expense(
    expense_id: int,
    decision: ExpenseStatus,
    payload: ApprovalCreate,
    approver: User,
    db: DbSession,
) -> CustodyExpense:
    expense = db.scalar(
        select(CustodyExpense)
        .where(CustodyExpense.id == expense_id)
        .with_for_update()
    )
    if not expense:
        raise HTTPException(status_code=404, detail="Custody expense not found")
    if expense.status != ExpenseStatus.pending:
        raise HTTPException(status_code=400, detail="This expense has already been decided")
    assignment = db.scalar(
        select(CustodyAssignment)
        .where(CustodyAssignment.id == expense.custody_assignment_id)
        .with_for_update()
    )
    if decision == ExpenseStatus.approved and custody_balance(db, assignment.id) < expense.amount:
        raise HTTPException(status_code=400, detail="Approval would exceed available custody")
    expense.status = decision
    db.add(
        CustodyExpenseApproval(
            custody_expense_id=expense.id,
            approved_by_user_id=approver.id,
            decision=decision,
            comment=payload.comment,
        )
    )
    add_audit_log(
        db,
        actor_user_id=approver.id,
        action=f"CUSTODY_EXPENSE_{decision.value.upper()}",
        entity_type="custody_expense",
        entity_id=expense.id,
        new_value={"decision": decision.value, "comment": payload.comment},
    )
    db.commit()
    return (
        db.query(CustodyExpense)
        .options(selectinload(CustodyExpense.approvals))
        .filter(CustodyExpense.id == expense.id)
        .first()
    )


@approvals_router.post("/custody-expenses/{expense_id}/approve", response_model=CustodyExpenseOut)
def approve_expense(
    expense_id: int, payload: ApprovalCreate, approver: FinanceOrAdminUser, db: DbSession
) -> CustodyExpense:
    return decide_expense(expense_id, ExpenseStatus.approved, payload, approver, db)


@approvals_router.post("/custody-expenses/{expense_id}/reject", response_model=CustodyExpenseOut)
def reject_expense(
    expense_id: int, payload: ApprovalCreate, approver: FinanceOrAdminUser, db: DbSession
) -> CustodyExpense:
    return decide_expense(expense_id, ExpenseStatus.rejected, payload, approver, db)
