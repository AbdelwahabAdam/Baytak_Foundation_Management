from datetime import datetime, timedelta, timezone
from decimal import Decimal

from fastapi import APIRouter, Query
from sqlalchemy import func

from app.dependencies import DbSession, FinanceOrAdminUser
from app.models import (
    Activity,
    ActivityTransaction,
    CustodyAssignment,
    CustodyExpense,
    Donation,
    DonationStatus,
    DonationType,
    Donor,
    ExpenseStatus,
    TransactionDirection,
)

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


def date_range(
    period: str | None, start_date: datetime | None, end_date: datetime | None
) -> tuple[datetime, datetime]:
    now = datetime.now(timezone.utc)
    if start_date and end_date:
        return start_date, end_date
    ranges = {
        "day": timedelta(days=1),
        "week": timedelta(days=7),
        "month": timedelta(days=30),
    }
    return now - ranges.get(period or "month", timedelta(days=30)), now


def donation_filter(
    db: DbSession, period: str | None, start_date: datetime | None, end_date: datetime | None
):
    start, end = date_range(period, start_date, end_date)
    return (
        db.query(Donation)
        .filter(
            Donation.status == DonationStatus.confirmed,
            Donation.donation_date >= start,
            Donation.donation_date <= end,
        ),
        start,
        end,
    )


@router.get("/summary", response_model=dict)
def summary(
    _: FinanceOrAdminUser,
    db: DbSession,
    period: str = Query(default="month", pattern="^(day|week|month)$"),
    start_date: datetime | None = None,
    end_date: datetime | None = None,
) -> dict:
    donations, start, end = donation_filter(db, period, start_date, end_date)
    total_donations = donations.with_entities(func.coalesce(func.sum(Donation.amount), 0)).scalar()
    donor_count = donations.with_entities(func.count(func.distinct(Donation.donor_id))).scalar()
    total_custody = db.query(func.coalesce(func.sum(CustodyAssignment.amount), 0)).scalar()
    approved_expenses = (
        db.query(func.coalesce(func.sum(CustodyExpense.amount), 0))
        .filter(CustodyExpense.status == ExpenseStatus.approved)
        .scalar()
    )
    pending_expenses = (
        db.query(func.count(CustodyExpense.id))
        .filter(CustodyExpense.status == ExpenseStatus.pending)
        .scalar()
    )
    return {
        "period": {"start_date": start, "end_date": end},
        "total_donations": Decimal(total_donations or 0),
        "total_donors": donor_count or 0,
        "total_custody": Decimal(total_custody or 0),
        "custody_balance": Decimal(total_custody or 0) - Decimal(approved_expenses or 0),
        "pending_custody_expenses": pending_expenses or 0,
        "activities_count": db.query(func.count(Activity.id)).scalar() or 0,
        "activity_total_income": Decimal(
            db.query(func.coalesce(func.sum(ActivityTransaction.amount), 0))
            .filter(ActivityTransaction.transaction_direction == TransactionDirection.income)
            .scalar()
            or 0
        ),
        "activity_total_expense": Decimal(
            db.query(func.coalesce(func.sum(ActivityTransaction.amount), 0))
            .filter(ActivityTransaction.transaction_direction == TransactionDirection.expense)
            .scalar()
            or 0
        ),
    }


@router.get("/donations-by-type", response_model=list[dict])
def donations_by_type(
    _: FinanceOrAdminUser,
    db: DbSession,
    period: str = Query(default="month", pattern="^(day|week|month)$"),
    start_date: datetime | None = None,
    end_date: datetime | None = None,
) -> list[dict]:
    donations, _, _ = donation_filter(db, period, start_date, end_date)
    rows = (
        donations.join(DonationType)
        .with_entities(
            DonationType.id,
            DonationType.type_name,
            func.coalesce(func.sum(Donation.amount), 0).label("amount"),
            func.count(Donation.id).label("count"),
        )
        .group_by(DonationType.id, DonationType.type_name)
        .order_by(func.sum(Donation.amount).desc())
        .all()
    )
    return [
        {"id": row.id, "type_name": row.type_name, "amount": row.amount, "count": row.count}
        for row in rows
    ]


@router.get("/recent-donors", response_model=list[dict])
def recent_donors(
    _: FinanceOrAdminUser,
    db: DbSession,
    period: str = Query(default="month", pattern="^(day|week|month)$"),
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    limit: int = Query(default=8, ge=1, le=50),
) -> list[dict]:
    donations, _, _ = donation_filter(db, period, start_date, end_date)
    rows = (
        donations.join(Donor)
        .with_entities(
            Donor.id,
            Donor.first_name,
            Donor.last_name,
            func.max(Donation.donation_date).label("last_donation_at"),
            func.sum(Donation.amount).label("total_amount"),
        )
        .group_by(Donor.id, Donor.first_name, Donor.last_name)
        .order_by(func.max(Donation.donation_date).desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "id": row.id,
            "name": f"{row.first_name} {row.last_name}",
            "last_donation_at": row.last_donation_at,
            "total_amount": row.total_amount,
        }
        for row in rows
    ]


@router.get("/custody-summary", response_model=dict)
def custody_summary(
    _: FinanceOrAdminUser, db: DbSession
) -> dict:
    total_assigned = db.query(func.coalesce(func.sum(CustodyAssignment.amount), 0)).scalar()
    approved = (
        db.query(func.coalesce(func.sum(CustodyExpense.amount), 0))
        .filter(CustodyExpense.status == ExpenseStatus.approved)
        .scalar()
    )
    pending = (
        db.query(func.coalesce(func.sum(CustodyExpense.amount), 0))
        .filter(CustodyExpense.status == ExpenseStatus.pending)
        .scalar()
    )
    return {
        "total_assigned": Decimal(total_assigned or 0),
        "approved_expenses": Decimal(approved or 0),
        "pending_expenses": Decimal(pending or 0),
        "available_balance": Decimal(total_assigned or 0) - Decimal(approved or 0),
    }


@router.get("/activities-summary", response_model=dict)
def activities_summary(_: FinanceOrAdminUser, db: DbSession) -> dict:
    income = Decimal(
        db.query(func.coalesce(func.sum(ActivityTransaction.amount), 0))
        .filter(ActivityTransaction.transaction_direction == TransactionDirection.income)
        .scalar()
        or 0
    )
    expense = Decimal(
        db.query(func.coalesce(func.sum(ActivityTransaction.amount), 0))
        .filter(ActivityTransaction.transaction_direction == TransactionDirection.expense)
        .scalar()
        or 0
    )
    top_activities = []
    activities = db.query(Activity).order_by(Activity.created_at.desc()).limit(20).all()
    for activity in activities:
        act_income = Decimal(
            db.query(func.coalesce(func.sum(ActivityTransaction.amount), 0))
            .filter(
                ActivityTransaction.activity_id == activity.id,
                ActivityTransaction.transaction_direction == TransactionDirection.income,
            )
            .scalar()
            or 0
        )
        act_expense = Decimal(
            db.query(func.coalesce(func.sum(ActivityTransaction.amount), 0))
            .filter(
                ActivityTransaction.activity_id == activity.id,
                ActivityTransaction.transaction_direction == TransactionDirection.expense,
            )
            .scalar()
            or 0
        )
        top_activities.append(
            {
                "id": activity.id,
                "name": activity.name,
                "income": act_income,
                "expense": act_expense,
                "balance": act_income - act_expense,
            }
        )
    top_activities.sort(key=lambda item: item["income"], reverse=True)
    return {
        "activities_count": db.query(func.count(Activity.id)).scalar() or 0,
        "total_income": income,
        "total_expense": expense,
        "balance": income - expense,
        "top_activities": top_activities[:8],
        "income_by_activity": [
            {"id": item["id"], "name": item["name"], "amount": item["income"]}
            for item in top_activities
            if item["income"] > 0
        ][:8],
        "expense_by_activity": [
            {"id": item["id"], "name": item["name"], "amount": item["expense"]}
            for item in sorted(top_activities, key=lambda item: item["expense"], reverse=True)
            if item["expense"] > 0
        ][:8],
    }


@router.get("/fund-balances", response_model=list[dict])
def fund_balances(_: FinanceOrAdminUser, db: DbSession) -> list[dict]:
    from app.services import fund_balance

    funds = db.query(DonationType).order_by(DonationType.type_name).all()
    return [
        {
            "id": fund.id,
            "type_name": fund.type_name,
            **fund_balance(db, fund.id),
        }
        for fund in funds
    ]

