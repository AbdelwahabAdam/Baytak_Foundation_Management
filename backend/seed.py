"""Populate a local development database with realistic demonstration data.

Run from Docker Compose:
    docker compose exec backend python seed.py
"""

from datetime import datetime, timedelta, timezone
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import SessionLocal
from app.models import (
    AuditLog,
    CustodyAssignment,
    CustodyExpense,
    CustodyExpenseApproval,
    Donation,
    DonationStatus,
    DonationType,
    Donor,
    DonorAddress,
    DonorPhone,
    ExpenseStatus,
    Role,
    ScheduledReport,
    ReportFormat,
    ReportType,
    User,
)
from app.security import hash_password


DEMO_PASSWORD = "ChangeMe123!"
NOW = datetime.now(timezone.utc)

ROLE_DEFINITIONS = {
    "admin": "Full system administration",
    "finance": "Financial management and approvals",
    "staff": "Day-to-day donor and expense work",
    "viewer": "Read-only access",
}

USER_DEFINITIONS = [
    ("admin@charity.local", "System", "Administrator", "admin", "+1 555 0100"),
    ("finance@charity.local", "Maya", "Hassan", "finance", "+1 555 0101"),
    ("sami@charity.local", "Sami", "Nouri", "staff", "+1 555 0102"),
    ("lina@charity.local", "Lina", "Karim", "staff", "+1 555 0103"),
    ("viewer@charity.local", "Omar", "Jamal", "viewer", "+1 555 0104"),
]

DONATION_TYPE_DEFINITIONS = [
    ("Zakat", "Mandatory charitable giving allocated to eligible recipients."),
    ("Sadaqah", "General voluntary donations for community support."),
    ("Food aid", "Food parcels and essential household supplies."),
    ("Education", "School materials, tuition, and student support."),
    ("Medical support", "Treatment, medicine, and urgent medical care."),
    ("Emergency relief", "Rapid assistance during local emergencies."),
]

DONOR_DEFINITIONS = [
    ("Amina", "Rahman", "+1 555 1001", "North District", "United States"),
    ("Yusuf", "Al-Karim", "+1 555 1002", "Central District", "United States"),
    ("Noor", "Haddad", "+1 555 1003", "West District", "United States"),
    ("Fatima", "Saleh", "+1 555 1004", "East District", "United States"),
    ("Adam", "Ibrahim", "+1 555 1005", "North District", "United States"),
    ("Layla", "Mansour", "+1 555 1006", "Riverside", "United States"),
    ("Hassan", "Qasim", "+1 555 1007", "Central District", "United States"),
    ("Maryam", "Rashid", "+1 555 1008", "West District", "United States"),
    ("Khalid", "Nasser", "+1 555 1009", "Old Town", "United States"),
    ("Sara", "Mahmoud", "+1 555 1010", "Riverside", "United States"),
    ("Ibrahim", "Farouk", "+1 555 1011", "East District", "United States"),
    ("Huda", "Aziz", "+1 555 1012", "North District", "United States"),
]


def get_or_create_roles(db: Session) -> dict[str, Role]:
    roles = {role.name: role for role in db.scalars(select(Role)).all()}
    for name, description in ROLE_DEFINITIONS.items():
        if name not in roles:
            roles[name] = Role(name=name, description=description)
            db.add(roles[name])
    db.flush()
    return roles


def get_or_create_users(db: Session, roles: dict[str, Role]) -> dict[str, User]:
    users: dict[str, User] = {}
    for email, first_name, last_name, role_name, phone_number in USER_DEFINITIONS:
        user = db.scalar(select(User).where(User.email == email))
        if not user:
            user = User(
                email=email,
                first_name=first_name,
                last_name=last_name,
                phone_number=phone_number,
                password_hash=hash_password(DEMO_PASSWORD),
                roles=[roles[role_name]],
            )
            db.add(user)
        users[email] = user
    db.flush()
    return users


def get_or_create_donation_types(db: Session) -> list[DonationType]:
    result: list[DonationType] = []
    for type_name, description in DONATION_TYPE_DEFINITIONS:
        donation_type = db.scalar(
            select(DonationType).where(DonationType.type_name == type_name)
        )
        if not donation_type:
            donation_type = DonationType(
                type_name=type_name, description=description, is_active=True
            )
            db.add(donation_type)
        result.append(donation_type)
    db.flush()
    return result


def create_donors(db: Session, created_by_user_id: int) -> list[Donor]:
    donors: list[Donor] = []
    for first_name, last_name, phone, city, country in DONOR_DEFINITIONS:
        normalized_name = f"{first_name} {last_name}".lower()
        donor = db.scalar(
            select(Donor).where(
                Donor.normalized_full_name == normalized_name,
                Donor.is_deleted.is_(False),
            )
        )
        if not donor:
            donor = Donor(
                first_name=first_name,
                last_name=last_name,
                normalized_full_name=normalized_name,
                created_by_user_id=created_by_user_id,
                phones=[DonorPhone(phone_number=phone, is_primary=True)],
                addresses=[
                    DonorAddress(
                        address_line=f"{100 + len(donors)} Community Way",
                        city=city,
                        country=country,
                        is_primary=True,
                    )
                ],
            )
            db.add(donor)
        donors.append(donor)
    db.flush()
    return donors


def create_donations(
    db: Session,
    donors: list[Donor],
    donation_types: list[DonationType],
    created_by_user_id: int,
) -> int:
    donations_created = 0
    amounts = [125, 250, 75, 500, 180, 60, 350, 90, 220, 100, 425, 150]
    for index, donor in enumerate(donors):
        receipt_number = f"SEED-2026-{index + 1:03}"
        if db.scalar(select(Donation.id).where(Donation.receipt_number == receipt_number)):
            continue
        donation_type = donation_types[index % len(donation_types)]
        donation = Donation(
            donor_id=donor.id,
            donation_type_id=donation_type.id,
            amount=Decimal(str(amounts[index])),
            currency="EGP",
            donation_date=NOW - timedelta(days=index * 4 + 2),
            payment_method=["Bank transfer", "Cash", "Card"][index % 3],
            receipt_number=receipt_number,
            status=DonationStatus.cancelled if index == len(donors) - 1 else DonationStatus.confirmed,
            created_by_user_id=created_by_user_id,
        )
        db.add(donation)
        donations_created += 1
    db.flush()
    return donations_created


def create_custody_data(db: Session, users: dict[str, User], admin: User) -> int:
    custody_specs = [
        (users["sami@charity.local"], Decimal("900.00"), "Food aid distribution"),
        (users["lina@charity.local"], Decimal("650.00"), "Education supplies programme"),
    ]
    assignments_created = 0
    for user, amount, description in custody_specs:
        assignment = db.scalar(
            select(CustodyAssignment).where(
                CustodyAssignment.user_id == user.id,
                CustodyAssignment.description == description,
            )
        )
        if assignment:
            continue
        assignment = CustodyAssignment(
            user_id=user.id,
            amount=amount,
            assigned_by_user_id=admin.id,
            assigned_at=NOW - timedelta(days=10 if user.email.startswith("sami") else 6),
            description=description,
        )
        db.add(assignment)
        db.flush()
        assignments_created += 1

        approved_expense = CustodyExpense(
            custody_assignment_id=assignment.id,
            user_id=user.id,
            title="Programme supplies",
            description="Seeded demonstration expense approved by finance.",
            amount=Decimal("185.50"),
            expense_date=NOW - timedelta(days=4),
            status=ExpenseStatus.approved,
        )
        pending_expense = CustodyExpense(
            custody_assignment_id=assignment.id,
            user_id=user.id,
            title="Transport reimbursement",
            description="Seeded demonstration expense awaiting review.",
            amount=Decimal("72.00"),
            expense_date=NOW - timedelta(days=1),
            status=ExpenseStatus.pending,
        )
        rejected_expense = CustodyExpense(
            custody_assignment_id=assignment.id,
            user_id=user.id,
            title="Unapproved purchase",
            description="Seeded demonstration expense rejected by finance.",
            amount=Decimal("48.00"),
            expense_date=NOW - timedelta(days=2),
            status=ExpenseStatus.rejected,
        )
        db.add_all([approved_expense, pending_expense, rejected_expense])
        db.flush()
        db.add_all(
            [
                CustodyExpenseApproval(
                    custody_expense_id=approved_expense.id,
                    approved_by_user_id=users["finance@charity.local"].id,
                    decision=ExpenseStatus.approved,
                    comment="Receipts verified.",
                ),
                CustodyExpenseApproval(
                    custody_expense_id=rejected_expense.id,
                    approved_by_user_id=users["finance@charity.local"].id,
                    decision=ExpenseStatus.rejected,
                    comment="Outside the assigned programme scope.",
                ),
            ]
        )
    return assignments_created


def create_scheduled_report(db: Session, admin: User) -> None:
    existing = db.scalar(
        select(ScheduledReport).where(ScheduledReport.name == "Monthly donation summary")
    )
    if not existing:
        db.add(
            ScheduledReport(
                name="Monthly donation summary",
                report_type=ReportType.donations,
                frequency="monthly",
                filters_json={"window": "last_30_days"},
                recipients_json=["finance@charity.local"],
                format=ReportFormat.csv,
                next_run_at=NOW + timedelta(days=30),
                created_by_user_id=admin.id,
            )
        )


def seed() -> None:
    with SessionLocal() as db:
        if db.scalar(
            select(AuditLog.id).where(AuditLog.action == "DEMO_DATA_SEEDED")
        ):
            print("Demo data already exists; nothing added.")
            return

        roles = get_or_create_roles(db)
        users = get_or_create_users(db, roles)
        admin = users["admin@charity.local"]
        donation_types = get_or_create_donation_types(db)
        donors = create_donors(db, admin.id)
        donations_created = create_donations(db, donors, donation_types, admin.id)
        custody_created = create_custody_data(db, users, admin)
        create_scheduled_report(db, admin)
        db.add(
            AuditLog(
                actor_user_id=admin.id,
                action="DEMO_DATA_SEEDED",
                entity_type="system",
                entity_id="local-development",
                new_value_json={
                    "users": len(users),
                    "donors": len(donors),
                    "donations_created": donations_created,
                    "custody_assignments_created": custody_created,
                },
            )
        )
        db.commit()
        print(
            f"Seeded {len(users)} users, {len(donors)} donors, "
            f"{donations_created} donations, and {custody_created} custody assignments."
        )
        print(f"All seeded users use the password: {DEMO_PASSWORD}")


if __name__ == "__main__":
    seed()
