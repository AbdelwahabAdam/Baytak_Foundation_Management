from datetime import datetime, timezone
from decimal import Decimal

import app.db as db_module
from app.models import (
    Activity,
    ActivityStatus,
    ActivityTransaction,
    ActivityTransactionType,
    CustodyAssignment,
    CustodyExpense,
    CustodyStatus,
    Donation,
    DonationStatus,
    DonationType,
    Donor,
    ExpenseStatus,
    TransactionDirection,
    TransactionReferenceType,
    User,
)
from app.security import hash_password
from app.services import activity_totals, fund_balance


def test_fund_and_activity_balance_calculations(client) -> None:
    """Unit-level balance math: assignment is not expense; negative funds allowed."""
    session = db_module.SessionLocal()
    now = datetime.now(timezone.utc)
    try:
        admin = session.query(User).filter(User.email == "admin@test.local").first()
        assert admin is not None
        fund = DonationType(type_name="Zakat", description="Zakat fund", is_active=True)
        donor = Donor(
            first_name="Nora",
            last_name="Giver",
            normalized_full_name="nora giver",
            created_by_user_id=admin.id,
        )
        activity = Activity(
            name="Medical Caravan",
            description="Health outreach",
            activity_type="medical",
            status=ActivityStatus.active,
            created_by_user_id=admin.id,
        )
        session.add_all([fund, donor, activity])
        session.flush()

        donation = Donation(
            donor_id=donor.id,
            donation_type_id=fund.id,
            activity_id=activity.id,
            amount=Decimal("10000.00"),
            currency="EGP",
            donation_date=now,
            status=DonationStatus.confirmed,
            created_by_user_id=admin.id,
        )
        session.add(donation)
        session.flush()
        session.add(
            ActivityTransaction(
                activity_id=activity.id,
                transaction_direction=TransactionDirection.income,
                transaction_type=ActivityTransactionType.donation,
                amount=donation.amount,
                description="Donation link",
                reference_type=TransactionReferenceType.donation,
                reference_id=donation.id,
                transaction_date=donation.donation_date,
                created_by_user_id=admin.id,
            )
        )

        staff = User(
            first_name="Staff",
            last_name="User",
            email="balance-staff@test.local",
            password_hash=hash_password("UserPass123!"),
        )
        session.add(staff)
        session.flush()

        assignment = CustodyAssignment(
            user_id=staff.id,
            donation_type_id=fund.id,
            activity_id=activity.id,
            amount=Decimal("20000.00"),
            assigned_by_user_id=admin.id,
            description="Float",
            status=CustodyStatus.active,
        )
        session.add(assignment)
        session.flush()

        assert fund_balance(session, fund.id)["balance"] == Decimal("10000.00")

        expense = CustodyExpense(
            custody_assignment_id=assignment.id,
            user_id=staff.id,
            activity_id=activity.id,
            title="Medicines",
            amount=Decimal("13500.00"),
            expense_date=now,
            status=ExpenseStatus.approved,
        )
        session.add(expense)
        session.flush()
        session.add(
            ActivityTransaction(
                activity_id=activity.id,
                transaction_direction=TransactionDirection.expense,
                transaction_type=ActivityTransactionType.other,
                amount=expense.amount,
                description=expense.title,
                reference_type=TransactionReferenceType.custody_expense,
                reference_id=expense.id,
                transaction_date=expense.expense_date,
                created_by_user_id=admin.id,
            )
        )
        session.commit()

        fund_totals = fund_balance(session, fund.id)
        assert fund_totals["total_donations"] == Decimal("10000.00")
        assert fund_totals["approved_custody_expenses"] == Decimal("13500.00")
        assert fund_totals["balance"] == Decimal("-3500.00")

        activity_result = activity_totals(session, activity.id)
        assert activity_result["total_income"] == Decimal("10000.00")
        assert activity_result["total_expense"] == Decimal("13500.00")
        assert activity_result["balance"] == Decimal("-3500.00")
    finally:
        session.close()
