from datetime import datetime
from decimal import Decimal

from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from app.models import (
    ActivityTransaction,
    ActivityTransactionType,
    AuditLog,
    CustodyAssignment,
    CustodyExpense,
    Donation,
    DonationStatus,
    ExpenseStatus,
    TransactionDirection,
    TransactionReferenceType,
)

INCOME_TRANSACTION_TYPES = {
    ActivityTransactionType.donation,
    ActivityTransactionType.sale,
    ActivityTransactionType.grant,
    ActivityTransactionType.manual_income,
}

EXPENSE_TRANSACTION_TYPES = {
    ActivityTransactionType.manual_expense,
    ActivityTransactionType.purchase,
    ActivityTransactionType.salary,
    ActivityTransactionType.maintenance,
    ActivityTransactionType.utilities,
    ActivityTransactionType.transportation,
    ActivityTransactionType.marketing,
    ActivityTransactionType.other,
}


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


def direction_for_transaction_type(
    transaction_type: ActivityTransactionType,
) -> TransactionDirection:
    if transaction_type in INCOME_TRANSACTION_TYPES:
        return TransactionDirection.income
    if transaction_type in EXPENSE_TRANSACTION_TYPES:
        return TransactionDirection.expense
    raise ValueError(f"Unsupported activity transaction type: {transaction_type}")


def activity_totals(db: Session, activity_id: int) -> dict[str, Decimal]:
    """Compute activity ledger totals. Balances are never stored."""
    income_total = db.scalar(
        select(func.coalesce(func.sum(ActivityTransaction.amount), 0)).where(
            ActivityTransaction.activity_id == activity_id,
            ActivityTransaction.transaction_direction == TransactionDirection.income,
        )
    )
    expense_total = db.scalar(
        select(func.coalesce(func.sum(ActivityTransaction.amount), 0)).where(
            ActivityTransaction.activity_id == activity_id,
            ActivityTransaction.transaction_direction == TransactionDirection.expense,
        )
    )
    income = Decimal(income_total or 0)
    expense = Decimal(expense_total or 0)
    return {
        "total_income": income,
        "total_expense": expense,
        "balance": income - expense,
    }


def activity_type_breakdown(db: Session, activity_id: int) -> dict[str, Decimal]:
    rows = (
        db.query(
            ActivityTransaction.transaction_type,
            func.coalesce(func.sum(ActivityTransaction.amount), 0).label("amount"),
        )
        .filter(ActivityTransaction.activity_id == activity_id)
        .group_by(ActivityTransaction.transaction_type)
        .all()
    )
    breakdown = {item.value: Decimal("0") for item in ActivityTransactionType}
    for row in rows:
        breakdown[row.transaction_type.value] = Decimal(row.amount or 0)
    return breakdown


def fund_balance(db: Session, donation_type_id: int) -> dict[str, Decimal]:
    """
    Fund (= donation type) balance.
    Negative balances are valid. Custody assignment amount is NOT an expense.
    Only approved custody expenses reduce fund balance.
    """
    donations_total = db.scalar(
        select(func.coalesce(func.sum(Donation.amount), 0)).where(
            Donation.donation_type_id == donation_type_id,
            Donation.status == DonationStatus.confirmed,
        )
    )
    approved_custody_expenses = db.scalar(
        select(func.coalesce(func.sum(CustodyExpense.amount), 0))
        .join(CustodyAssignment)
        .where(
            CustodyAssignment.donation_type_id == donation_type_id,
            CustodyExpense.status == ExpenseStatus.approved,
        )
    )
    income = Decimal(donations_total or 0)
    expenses = Decimal(approved_custody_expenses or 0)
    return {
        "total_donations": income,
        "approved_custody_expenses": expenses,
        "direct_fund_expenses": Decimal("0"),
        "balance": income - expenses,
    }


def ensure_donation_activity_transaction(
    db: Session,
    *,
    donation: Donation,
    created_by_user_id: int,
) -> ActivityTransaction | None:
    """Post an income ledger row when a donation is linked to an activity."""
    # Remove prior donation ledger links so a donation appears on at most one activity.
    (
        db.query(ActivityTransaction)
        .filter(
            ActivityTransaction.reference_type == TransactionReferenceType.donation,
            ActivityTransaction.reference_id == donation.id,
        )
        .delete(synchronize_session=False)
    )
    if not donation.activity_id:
        return None
    if donation.status != DonationStatus.confirmed:
        return None
    transaction = ActivityTransaction(
        activity_id=donation.activity_id,
        transaction_direction=TransactionDirection.income,
        transaction_type=ActivityTransactionType.donation,
        amount=donation.amount,
        description=f"تبرع #{donation.id}" if donation.id else "تبرع",
        reference_type=TransactionReferenceType.donation,
        reference_id=donation.id,
        transaction_date=donation.donation_date,
        created_by_user_id=created_by_user_id,
    )
    db.add(transaction)
    return transaction


def remove_donation_activity_transaction(db: Session, donation_id: int) -> None:
    (
        db.query(ActivityTransaction)
        .filter(
            ActivityTransaction.reference_type == TransactionReferenceType.donation,
            ActivityTransaction.reference_id == donation_id,
        )
        .delete(synchronize_session=False)
    )


def ensure_custody_expense_activity_transaction(
    db: Session,
    *,
    expense: CustodyExpense,
    created_by_user_id: int,
) -> ActivityTransaction | None:
    """Post an expense ledger row when an approved custody expense belongs to an activity."""
    activity_id = expense.activity_id
    if not activity_id and expense.custody_assignment:
        activity_id = expense.custody_assignment.activity_id
    if not activity_id:
        return None
    if expense.status != ExpenseStatus.approved:
        return None
    existing = (
        db.query(ActivityTransaction)
        .filter(
            ActivityTransaction.activity_id == activity_id,
            ActivityTransaction.reference_type == TransactionReferenceType.custody_expense,
            ActivityTransaction.reference_id == expense.id,
        )
        .first()
    )
    if existing:
        existing.amount = expense.amount
        existing.transaction_date = expense.expense_date
        return existing
    transaction = ActivityTransaction(
        activity_id=activity_id,
        transaction_direction=TransactionDirection.expense,
        transaction_type=ActivityTransactionType.other,
        amount=expense.amount,
        description=expense.title,
        reference_type=TransactionReferenceType.custody_expense,
        reference_id=expense.id,
        transaction_date=expense.expense_date,
        created_by_user_id=created_by_user_id,
    )
    db.add(transaction)
    return transaction


def remove_custody_expense_activity_transaction(db: Session, expense_id: int) -> None:
    (
        db.query(ActivityTransaction)
        .filter(
            ActivityTransaction.reference_type == TransactionReferenceType.custody_expense,
            ActivityTransaction.reference_id == expense_id,
        )
        .delete(synchronize_session=False)
    )


def activity_monthly_summary(db: Session, activity_id: int) -> list[dict]:
    month_expr = func.strftime("%Y-%m", ActivityTransaction.transaction_date)
    # SQLite-compatible month key; Postgres uses to_char — detect dialect.
    bind = db.get_bind()
    if bind.dialect.name == "postgresql":
        month_expr = func.to_char(ActivityTransaction.transaction_date, "YYYY-MM")
    rows = (
        db.query(
            month_expr.label("month"),
            func.coalesce(
                func.sum(
                    case(
                        (
                            ActivityTransaction.transaction_direction
                            == TransactionDirection.income,
                            ActivityTransaction.amount,
                        ),
                        else_=0,
                    )
                ),
                0,
            ).label("income"),
            func.coalesce(
                func.sum(
                    case(
                        (
                            ActivityTransaction.transaction_direction
                            == TransactionDirection.expense,
                            ActivityTransaction.amount,
                        ),
                        else_=0,
                    )
                ),
                0,
            ).label("expense"),
        )
        .filter(ActivityTransaction.activity_id == activity_id)
        .group_by(month_expr)
        .order_by(month_expr)
        .all()
    )
    return [
        {
            "month": row.month,
            "income": Decimal(row.income or 0),
            "expense": Decimal(row.expense or 0),
            "balance": Decimal(row.income or 0) - Decimal(row.expense or 0),
        }
        for row in rows
    ]


def create_activity_transaction(
    db: Session,
    *,
    activity_id: int,
    transaction_type: ActivityTransactionType,
    amount: Decimal,
    description: str | None,
    transaction_date: datetime,
    created_by_user_id: int,
    reference_type: TransactionReferenceType | None = None,
    reference_id: int | None = None,
) -> ActivityTransaction:
    direction = direction_for_transaction_type(transaction_type)
    transaction = ActivityTransaction(
        activity_id=activity_id,
        transaction_direction=direction,
        transaction_type=transaction_type,
        amount=amount,
        description=description,
        reference_type=reference_type,
        reference_id=reference_id,
        transaction_date=transaction_date,
        created_by_user_id=created_by_user_id,
    )
    db.add(transaction)
    return transaction

