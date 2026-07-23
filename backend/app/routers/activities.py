import logging
from datetime import datetime
from decimal import Decimal

from fastapi import APIRouter, HTTPException, Query, status
from prometheus_client import Counter
from sqlalchemy import func

from app.dependencies import CurrentUser, DbSession, FinanceOrAdminUser, FinanceStaffOrAdmin
from app.models import (
    Activity,
    ActivityStatus,
    ActivityTransaction,
    ActivityTransactionType,
    Donation,
    DonationStatus,
    TransactionDirection,
    TransactionReferenceType,
)
from app.schemas import (
    ActivityCreate,
    ActivityOut,
    ActivitySummary,
    ActivityTransactionCreate,
    ActivityTransactionOut,
    ActivityUpdate,
    Message,
)
from app.services import (
    activity_monthly_summary,
    activity_totals,
    activity_type_breakdown,
    add_audit_log,
    create_activity_transaction,
    direction_for_transaction_type,
    ensure_donation_activity_transaction,
)

logger = logging.getLogger("baytak.activities")

ACTIVITY_OPS = Counter(
    "baytak_activity_operations_total",
    "Activity module operations",
    ["operation", "result"],
)

router = APIRouter(prefix="/activities", tags=["Activities"])


def get_activity_or_404(db: DbSession, activity_id: int) -> Activity:
    activity = db.query(Activity).filter(Activity.id == activity_id).first()
    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found")
    return activity


def serialize_activity(db: DbSession, activity: Activity) -> dict:
    totals = activity_totals(db, activity.id)
    tx_count = (
        db.query(func.count(ActivityTransaction.id))
        .filter(ActivityTransaction.activity_id == activity.id)
        .scalar()
        or 0
    )
    return ActivityOut.model_validate(
        {
            "id": activity.id,
            "name": activity.name,
            "description": activity.description,
            "activity_type": activity.activity_type,
            "status": activity.status,
            "created_by_user_id": activity.created_by_user_id,
            "created_at": activity.created_at,
            "updated_at": activity.updated_at,
            "total_income": totals["total_income"],
            "total_expense": totals["total_expense"],
            "balance": totals["balance"],
            "transaction_count": tx_count,
        }
    ).model_dump()


@router.get("", response_model=dict)
def list_activities(
    _: CurrentUser,
    db: DbSession,
    search: str | None = Query(default=None),
    activity_status: ActivityStatus | None = Query(default=None, alias="status"),
    activity_type: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
) -> dict:
    query = db.query(Activity)
    if search:
        term = f"%{search.strip()}%"
        query = query.filter(
            (Activity.name.ilike(term))
            | (Activity.description.ilike(term))
            | (Activity.activity_type.ilike(term))
        )
    if activity_status:
        query = query.filter(Activity.status == activity_status)
    if activity_type:
        query = query.filter(Activity.activity_type.ilike(f"%{activity_type.strip()}%"))
    total = query.count()
    items = (
        query.order_by(Activity.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return {
        "items": [serialize_activity(db, item) for item in items],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.post("", response_model=ActivityOut, status_code=status.HTTP_201_CREATED)
def create_activity(
    payload: ActivityCreate, current_user: FinanceStaffOrAdmin, db: DbSession
) -> dict:
    name = payload.name.strip()
    if db.query(Activity).filter(Activity.name == name).first():
        ACTIVITY_OPS.labels(operation="create", result="conflict").inc()
        raise HTTPException(status_code=409, detail="An activity with this name already exists")
    activity = Activity(
        name=name,
        description=payload.description,
        activity_type=payload.activity_type.strip(),
        status=payload.status,
        created_by_user_id=current_user.id,
    )
    db.add(activity)
    db.flush()
    add_audit_log(
        db,
        actor_user_id=current_user.id,
        action="ACTIVITY_CREATED",
        entity_type="activity",
        entity_id=activity.id,
        new_value={"name": activity.name, "activity_type": activity.activity_type},
    )
    db.commit()
    ACTIVITY_OPS.labels(operation="create", result="success").inc()
    logger.info("activity_created id=%s name=%s by=%s", activity.id, activity.name, current_user.id)
    return serialize_activity(db, get_activity_or_404(db, activity.id))


@router.get("/{activity_id}", response_model=ActivityOut)
def get_activity(activity_id: int, _: CurrentUser, db: DbSession) -> dict:
    return serialize_activity(db, get_activity_or_404(db, activity_id))


@router.patch("/{activity_id}", response_model=ActivityOut)
def update_activity(
    activity_id: int, payload: ActivityUpdate, current_user: FinanceOrAdminUser, db: DbSession
) -> dict:
    activity = get_activity_or_404(db, activity_id)
    values = payload.model_dump(exclude_unset=True)
    if "name" in values and values["name"]:
        values["name"] = values["name"].strip()
        conflict = (
            db.query(Activity)
            .filter(Activity.name == values["name"], Activity.id != activity.id)
            .first()
        )
        if conflict:
            raise HTTPException(status_code=409, detail="An activity with this name already exists")
    if "activity_type" in values and values["activity_type"]:
        values["activity_type"] = values["activity_type"].strip()
    for field, value in values.items():
        setattr(activity, field, value)
    add_audit_log(
        db,
        actor_user_id=current_user.id,
        action="ACTIVITY_UPDATED",
        entity_type="activity",
        entity_id=activity.id,
        new_value={key: str(value) for key, value in values.items()},
    )
    db.commit()
    ACTIVITY_OPS.labels(operation="update", result="success").inc()
    logger.info("activity_updated id=%s by=%s", activity.id, current_user.id)
    return serialize_activity(db, get_activity_or_404(db, activity.id))


@router.delete("/{activity_id}", response_model=Message)
def deactivate_activity(
    activity_id: int, current_user: FinanceOrAdminUser, db: DbSession
) -> Message:
    activity = get_activity_or_404(db, activity_id)
    activity.status = ActivityStatus.inactive
    add_audit_log(
        db,
        actor_user_id=current_user.id,
        action="ACTIVITY_DEACTIVATED",
        entity_type="activity",
        entity_id=activity.id,
    )
    db.commit()
    ACTIVITY_OPS.labels(operation="deactivate", result="success").inc()
    logger.info("activity_deactivated id=%s by=%s", activity.id, current_user.id)
    return Message(message="Activity deactivated")


@router.get("/{activity_id}/summary", response_model=ActivitySummary)
def activity_summary(activity_id: int, _: CurrentUser, db: DbSession) -> dict:
    get_activity_or_404(db, activity_id)
    totals = activity_totals(db, activity_id)
    breakdown = activity_type_breakdown(db, activity_id)
    expense_keys = (
        ActivityTransactionType.manual_expense,
        ActivityTransactionType.purchase,
        ActivityTransactionType.salary,
        ActivityTransactionType.maintenance,
        ActivityTransactionType.utilities,
        ActivityTransactionType.transportation,
        ActivityTransactionType.marketing,
        ActivityTransactionType.other,
    )
    expenses = sum((breakdown[key.value] for key in expense_keys), Decimal("0"))
    return {
        "total_income": totals["total_income"],
        "total_expense": totals["total_expense"],
        "balance": totals["balance"],
        "donations": breakdown[ActivityTransactionType.donation.value],
        "sales": breakdown[ActivityTransactionType.sale.value],
        "grants": breakdown[ActivityTransactionType.grant.value],
        "expenses": expenses,
    }


def _transactions_with_running_balance(
    transactions: list[ActivityTransaction],
) -> list[dict]:
    chronological = sorted(
        transactions,
        key=lambda item: (item.transaction_date, item.id),
    )
    running = Decimal("0")
    balances: dict[int, Decimal] = {}
    for item in chronological:
        if item.transaction_direction == TransactionDirection.income:
            running += Decimal(item.amount)
        else:
            running -= Decimal(item.amount)
        balances[item.id] = running
    return [
        ActivityTransactionOut.model_validate(
            {
                **{
                    "id": item.id,
                    "activity_id": item.activity_id,
                    "transaction_direction": item.transaction_direction,
                    "transaction_type": item.transaction_type,
                    "amount": item.amount,
                    "description": item.description,
                    "reference_type": item.reference_type,
                    "reference_id": item.reference_id,
                    "transaction_date": item.transaction_date,
                    "created_by_user_id": item.created_by_user_id,
                    "created_at": item.created_at,
                    "updated_at": item.updated_at,
                    "running_balance": balances[item.id],
                }
            }
        ).model_dump()
        for item in transactions
    ]


@router.get("/{activity_id}/transactions", response_model=dict)
def list_transactions(
    activity_id: int,
    _: CurrentUser,
    db: DbSession,
    direction: TransactionDirection | None = Query(default=None),
    transaction_type: ActivityTransactionType | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=200),
) -> dict:
    get_activity_or_404(db, activity_id)
    query = db.query(ActivityTransaction).filter(ActivityTransaction.activity_id == activity_id)
    if direction:
        query = query.filter(ActivityTransaction.transaction_direction == direction)
    if transaction_type:
        query = query.filter(ActivityTransaction.transaction_type == transaction_type)
    total = query.count()
    items = (
        query.order_by(
            ActivityTransaction.transaction_date.desc(),
            ActivityTransaction.id.desc(),
        )
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    # Running balance requires full chronological context for the page set.
    all_for_balance = (
        db.query(ActivityTransaction)
        .filter(ActivityTransaction.activity_id == activity_id)
        .order_by(ActivityTransaction.transaction_date.asc(), ActivityTransaction.id.asc())
        .all()
    )
    balance_map = {
        row["id"]: row["running_balance"]
        for row in _transactions_with_running_balance(all_for_balance)
    }
    serialized = []
    for item in items:
        payload = ActivityTransactionOut.model_validate(item).model_dump()
        payload["running_balance"] = balance_map.get(item.id)
        serialized.append(payload)
    return {"items": serialized, "total": total, "page": page, "page_size": page_size}


@router.post(
    "/{activity_id}/transactions",
    response_model=ActivityTransactionOut,
    status_code=status.HTTP_201_CREATED,
)
def create_transaction(
    activity_id: int,
    payload: ActivityTransactionCreate,
    current_user: FinanceStaffOrAdmin,
    db: DbSession,
) -> dict:
    get_activity_or_404(db, activity_id)
    transaction_date = payload.transaction_date or datetime.now().astimezone()

    if payload.transaction_type == ActivityTransactionType.donation:
        donation = db.query(Donation).filter(Donation.id == payload.reference_id).first()
        if not donation:
            raise HTTPException(status_code=400, detail="Referenced donation was not found")
        if donation.status != DonationStatus.confirmed:
            raise HTTPException(status_code=400, detail="Only confirmed donations can be linked")
        # Link existing donation — do not duplicate donation records.
        donation.activity_id = activity_id
        transaction = ensure_donation_activity_transaction(
            db, donation=donation, created_by_user_id=current_user.id
        )
        if not transaction:
            raise HTTPException(status_code=400, detail="Unable to link donation to activity")
        add_audit_log(
            db,
            actor_user_id=current_user.id,
            action="ACTIVITY_DONATION_LINKED",
            entity_type="activity_transaction",
            entity_id=transaction.id,
            new_value={"donation_id": donation.id, "activity_id": activity_id},
        )
        db.commit()
        db.refresh(transaction)
        ACTIVITY_OPS.labels(operation="link_donation", result="success").inc()
        logger.info(
            "activity_donation_linked activity_id=%s donation_id=%s tx_id=%s",
            activity_id,
            donation.id,
            transaction.id,
        )
        return ActivityTransactionOut.model_validate(transaction).model_dump()

    direction = direction_for_transaction_type(payload.transaction_type)
    reference_type = payload.reference_type
    if reference_type is None:
        if payload.transaction_type == ActivityTransactionType.sale:
            reference_type = TransactionReferenceType.sale
        elif payload.transaction_type == ActivityTransactionType.grant:
            reference_type = TransactionReferenceType.grant
        else:
            reference_type = TransactionReferenceType.manual

    transaction = create_activity_transaction(
        db,
        activity_id=activity_id,
        transaction_type=payload.transaction_type,
        amount=payload.amount or Decimal("0"),
        description=payload.description,
        transaction_date=transaction_date,
        created_by_user_id=current_user.id,
        reference_type=reference_type,
        reference_id=payload.reference_id,
    )
    db.flush()
    add_audit_log(
        db,
        actor_user_id=current_user.id,
        action="ACTIVITY_TRANSACTION_CREATED",
        entity_type="activity_transaction",
        entity_id=transaction.id,
        new_value={
            "direction": direction.value,
            "type": payload.transaction_type.value,
            "amount": str(transaction.amount),
        },
    )
    db.commit()
    db.refresh(transaction)
    ACTIVITY_OPS.labels(operation="create_transaction", result="success").inc()
    logger.info(
        "activity_transaction_created activity_id=%s tx_id=%s type=%s amount=%s",
        activity_id,
        transaction.id,
        payload.transaction_type.value,
        transaction.amount,
    )
    return ActivityTransactionOut.model_validate(transaction).model_dump()


@router.get("/{activity_id}/reports", response_model=dict)
def activity_reports(activity_id: int, _: CurrentUser, db: DbSession) -> dict:
    get_activity_or_404(db, activity_id)
    totals = activity_totals(db, activity_id)
    breakdown = activity_type_breakdown(db, activity_id)
    monthly = activity_monthly_summary(db, activity_id)
    expense_by_category = {
        key: value
        for key, value in breakdown.items()
        if key
        in {
            "manual_expense",
            "purchase",
            "salary",
            "maintenance",
            "utilities",
            "transportation",
            "marketing",
            "other",
        }
        and value > 0
    }
    income_statement = {
        "income": {
            "donations": breakdown["donation"],
            "sales": breakdown["sale"],
            "grants": breakdown["grant"],
            "manual_income": breakdown["manual_income"],
            "total": totals["total_income"],
        },
        "expenses": {
            **expense_by_category,
            "total": totals["total_expense"],
        },
        "net": totals["balance"],
    }
    cash_flow = {
        "inflows": totals["total_income"],
        "outflows": totals["total_expense"],
        "net_cash_flow": totals["balance"],
    }
    ACTIVITY_OPS.labels(operation="reports", result="success").inc()
    return {
        "income_statement": income_statement,
        "expense_by_category": expense_by_category,
        "cash_flow": cash_flow,
        "monthly_summary": monthly,
        "profit_loss": {
            "income": totals["total_income"],
            "expense": totals["total_expense"],
            "profit_loss": totals["balance"],
        },
    }
