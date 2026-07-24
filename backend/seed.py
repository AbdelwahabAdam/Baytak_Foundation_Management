"""Populate a local development database with realistic demonstration data.

Includes funds, donors, donations, activities/ledgers, custody, warehouse, and cases.

Run from Docker Compose:
    docker compose exec backend python seed.py

Force a refresh of demo marker-gated sections (still idempotent for unique keys):
    docker compose exec backend python seed.py --force
"""

from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import SessionLocal
from app.models import (
    Activity,
    ActivityStatus,
    ActivityTransaction,
    ActivityTransactionType,
    AidCase,
    AuditLog,
    CasePriority,
    CaseStatus,
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
    ReportFormat,
    ReportType,
    Role,
    ScheduledReport,
    Task,
    TaskPriority,
    TaskStatus,
    TransactionDirection,
    TransactionReferenceType,
    User,
    WarehouseItem,
)
from app.security import hash_password
from app.services import ensure_custody_expense_activity_transaction, ensure_donation_activity_transaction

DEMO_PASSWORD = "ChangeMe123!"
NOW = datetime.now(timezone.utc)
DEMO_MARKER = "DEMO_DATA_SEEDED_V2"

ROLE_DEFINITIONS = {
    "admin": "Full system administration",
    "finance": "Financial management and approvals",
    "staff": "Day-to-day donor and expense work",
    "viewer": "Read-only access",
}

USER_DEFINITIONS = [
    ("admin@charity.local", "System", "Administrator", "admin", "+20 100 000 0100"),
    ("finance@charity.local", "Maya", "Hassan", "finance", "+20 100 000 0101"),
    ("sami@charity.local", "Sami", "Nouri", "staff", "+20 100 000 0102"),
    ("lina@charity.local", "Lina", "Karim", "staff", "+20 100 000 0103"),
    ("viewer@charity.local", "Omar", "Jamal", "viewer", "+20 100 000 0104"),
]

DONATION_TYPE_DEFINITIONS = [
    ("Zakat", "Mandatory charitable giving allocated to eligible recipients."),
    ("Sadaqah", "General voluntary donations for community support."),
    ("Food aid", "Food parcels and essential household supplies."),
    ("Education", "School materials, tuition, and student support."),
    ("Medical support", "Treatment, medicine, and urgent medical care."),
    ("Emergency relief", "Rapid assistance during local emergencies."),
    ("Workshop Donation", "Support for handicrafts and skills programmes."),
]

DONOR_DEFINITIONS = [
    ("Amina", "Rahman", "+20 100 555 1001", "Nasr City", "Egypt"),
    ("Yusuf", "Al-Karim", "+20 100 555 1002", "Heliopolis", "Egypt"),
    ("Noor", "Haddad", "+20 100 555 1003", "Maadi", "Egypt"),
    ("Fatima", "Saleh", "+20 100 555 1004", "Dokki", "Egypt"),
    ("Adam", "Ibrahim", "+20 100 555 1005", "6th of October", "Egypt"),
    ("Layla", "Mansour", "+20 100 555 1006", "Giza", "Egypt"),
    ("Hassan", "Qasim", "+20 100 555 1007", "Alexandria", "Egypt"),
    ("Maryam", "Rashid", "+20 100 555 1008", "Mansoura", "Egypt"),
    ("Khalid", "Nasser", "+20 100 555 1009", "Tanta", "Egypt"),
    ("Sara", "Mahmoud", "+20 100 555 1010", "Assiut", "Egypt"),
    ("Ibrahim", "Farouk", "+20 100 555 1011", "Zagazig", "Egypt"),
    ("Huda", "Aziz", "+20 100 555 1012", "Suez", "Egypt"),
]

ACTIVITY_DEFINITIONS = [
    (
        "Handicrafts Workshop",
        "Skills training and product sales for women artisans.",
        "workshop",
    ),
    (
        "Medical Caravan",
        "Mobile clinics offering free checkups and medicines.",
        "medical",
    ),
    (
        "Food Kitchen",
        "Daily meals for families in need.",
        "kitchen",
    ),
    (
        "Ramadan Campaign",
        "Seasonal food packs and iftar support.",
        "campaign",
    ),
    (
        "Education Program",
        "School kits, tutoring, and scholarship support.",
        "education",
    ),
]

WAREHOUSE_DEFINITIONS = [
    ("Rice bags 25kg", "WH-RICE-25", 120, "bag", "Aisle A"),
    ("Cooking oil 1L", "WH-OIL-1L", 340, "bottle", "Aisle A"),
    ("School kits", "WH-EDU-KIT", 85, "kit", "Aisle B"),
    ("First-aid packs", "WH-MED-FA", 60, "pack", "Aisle C"),
    ("Blankets", "WH-BLKT", 150, "piece", "Aisle D"),
]

CASE_DEFINITIONS = [
    ("CASE-SEED-001", "Mona Adel", "+20 101 222 3001", "Medical", CaseStatus.open, CasePriority.high, 8000, 5000),
    ("CASE-SEED-002", "Karim Fathy", "+20 101 222 3002", "Education", CaseStatus.in_progress, CasePriority.medium, 3500, 3500),
    ("CASE-SEED-003", "Salma Youssef", "+20 101 222 3003", "Food aid", CaseStatus.open, CasePriority.urgent, 2000, None),
    ("CASE-SEED-004", "Tarek Nabil", "+20 101 222 3004", "Housing", CaseStatus.closed, CasePriority.low, 12000, 10000),
    ("CASE-SEED-005", "Nour El-Din", "+20 101 222 3005", "Emergency", CaseStatus.open, CasePriority.high, 4500, None),
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


def get_or_create_donation_types(db: Session) -> dict[str, DonationType]:
    result: dict[str, DonationType] = {}
    for type_name, description in DONATION_TYPE_DEFINITIONS:
        donation_type = db.scalar(
            select(DonationType).where(DonationType.type_name == type_name)
        )
        if not donation_type:
            donation_type = DonationType(
                type_name=type_name, description=description, is_active=True
            )
            db.add(donation_type)
        result[type_name] = donation_type
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


def get_or_create_activities(db: Session, admin: User) -> dict[str, Activity]:
    activities: dict[str, Activity] = {}
    for name, description, activity_type in ACTIVITY_DEFINITIONS:
        activity = db.scalar(select(Activity).where(Activity.name == name))
        if not activity:
            activity = Activity(
                name=name,
                description=description,
                activity_type=activity_type,
                status=ActivityStatus.active,
                created_by_user_id=admin.id,
            )
            db.add(activity)
        activities[name] = activity
    db.flush()
    return activities


def link_existing_donations_to_activities(
    db: Session,
    activities: dict[str, Activity],
    created_by_user_id: int,
) -> int:
    """Attach unlinked confirmed donations to activities and post ledger rows."""
    activity_list = list(activities.values())
    donations = db.scalars(
        select(Donation).where(
            Donation.activity_id.is_(None),
            Donation.status == DonationStatus.confirmed,
        )
    ).all()
    linked = 0
    for index, donation in enumerate(donations):
        activity = activity_list[index % len(activity_list)]
        donation.activity_id = activity.id
        ensure_donation_activity_transaction(
            db, donation=donation, created_by_user_id=created_by_user_id
        )
        linked += 1
    db.flush()
    return linked


def create_donations(
    db: Session,
    donors: list[Donor],
    donation_types: dict[str, DonationType],
    activities: dict[str, Activity],
    created_by_user_id: int,
) -> int:
    type_list = list(donation_types.values())
    activity_cycle = [
        activities["Handicrafts Workshop"],
        activities["Medical Caravan"],
        activities["Food Kitchen"],
        activities["Ramadan Campaign"],
        activities["Education Program"],
        None,
    ]
    amounts = [1250, 2500, 750, 5000, 1800, 600, 3500, 900, 2200, 1000, 4250, 1500]
    donations_created = 0
    for index, donor in enumerate(donors):
        receipt_number = f"SEED-2026-{index + 1:03}"
        if db.scalar(select(Donation.id).where(Donation.receipt_number == receipt_number)):
            continue
        donation_type = type_list[index % len(type_list)]
        activity = activity_cycle[index % len(activity_cycle)]
        donation = Donation(
            donor_id=donor.id,
            donation_type_id=donation_type.id,
            activity_id=activity.id if activity else None,
            amount=Decimal(str(amounts[index])),
            currency="EGP",
            donation_date=NOW - timedelta(days=index * 3 + 1),
            payment_method=["Bank transfer", "Cash", "Card"][index % 3],
            receipt_number=receipt_number,
            status=DonationStatus.cancelled if index == len(donors) - 1 else DonationStatus.confirmed,
            created_by_user_id=created_by_user_id,
        )
        db.add(donation)
        db.flush()
        ensure_donation_activity_transaction(
            db, donation=donation, created_by_user_id=created_by_user_id
        )
        donations_created += 1
    db.flush()
    return donations_created


def create_activity_ledger(
    db: Session,
    activities: dict[str, Activity],
    admin: User,
    finance: User,
) -> int:
    """Add grants, sales, and direct expenses so activity pages look populated."""
    specs = [
        (
            "Handicrafts Workshop",
            [
                ("grant", "Partner skills grant", "4500.00", 20),
                ("sale", "Handmade product sales weekend", "2800.00", 8),
                ("purchase", "Raw materials purchase", "1600.00", 12),
                ("marketing", "Workshop flyer printing", "350.00", 10),
            ],
        ),
        (
            "Medical Caravan",
            [
                ("grant", "Health NGO contribution", "12000.00", 18),
                ("manual_income", "Clinic day cash donations", "900.00", 5),
                ("purchase", "Medicines restock", "5400.00", 7),
                ("transportation", "Caravan fuel and drivers", "1800.00", 6),
                ("salary", "Volunteer doctor stipends", "3200.00", 4),
            ],
        ),
        (
            "Food Kitchen",
            [
                ("grant", "Food bank monthly grant", "8000.00", 15),
                ("manual_income", "Community meal sponsorships", "2100.00", 3),
                ("purchase", "Kitchen groceries", "4700.00", 2),
                ("utilities", "Gas and electricity", "650.00", 1),
                ("maintenance", "Kitchen equipment repair", "420.00", 9),
            ],
        ),
        (
            "Ramadan Campaign",
            [
                ("grant", "Corporate Ramadan sponsorship", "15000.00", 25),
                ("manual_income", "Iftar table sponsorships", "3600.00", 14),
                ("purchase", "Food pack assembly", "9200.00", 11),
                ("other", "Distribution volunteers meals", "780.00", 10),
            ],
        ),
        (
            "Education Program",
            [
                ("grant", "Back-to-school foundation grant", "7000.00", 22),
                ("sale", "Charity bazaar book sale", "1100.00", 16),
                ("purchase", "School kits bulk order", "4300.00", 13),
                ("salary", "Tutor honoraria", "2500.00", 8),
            ],
        ),
    ]
    created = 0
    for activity_name, rows in specs:
        activity = activities[activity_name]
        for tx_type, description, amount, days_ago in rows:
            exists = db.scalar(
                select(ActivityTransaction.id).where(
                    ActivityTransaction.activity_id == activity.id,
                    ActivityTransaction.description == description,
                )
            )
            if exists:
                continue
            transaction_type = ActivityTransactionType(tx_type)
            direction = (
                TransactionDirection.income
                if transaction_type
                in {
                    ActivityTransactionType.grant,
                    ActivityTransactionType.sale,
                    ActivityTransactionType.manual_income,
                    ActivityTransactionType.donation,
                }
                else TransactionDirection.expense
            )
            reference_type = {
                ActivityTransactionType.grant: TransactionReferenceType.grant,
                ActivityTransactionType.sale: TransactionReferenceType.sale,
            }.get(transaction_type, TransactionReferenceType.manual)
            db.add(
                ActivityTransaction(
                    activity_id=activity.id,
                    transaction_direction=direction,
                    transaction_type=transaction_type,
                    amount=Decimal(amount),
                    description=description,
                    reference_type=reference_type,
                    transaction_date=NOW - timedelta(days=days_ago),
                    created_by_user_id=finance.id if direction == TransactionDirection.income else admin.id,
                )
            )
            created += 1
    db.flush()
    return created


def create_custody_data(
    db: Session,
    users: dict[str, User],
    donation_types: dict[str, DonationType],
    activities: dict[str, Activity],
    admin: User,
) -> int:
    custody_specs = [
        (
            users["sami@charity.local"],
            donation_types["Food aid"],
            activities["Food Kitchen"],
            Decimal("9000.00"),
            "Food kitchen field float",
        ),
        (
            users["lina@charity.local"],
            donation_types["Education"],
            activities["Education Program"],
            Decimal("6500.00"),
            "Education supplies programme",
        ),
        (
            users["sami@charity.local"],
            donation_types["Medical support"],
            activities["Medical Caravan"],
            Decimal("12000.00"),
            "Medical caravan custody",
        ),
    ]
    assignments_created = 0
    finance = users["finance@charity.local"]
    for user, fund, activity, amount, description in custody_specs:
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
            donation_type_id=fund.id,
            activity_id=activity.id,
            amount=amount,
            assigned_by_user_id=admin.id,
            assigned_at=NOW - timedelta(days=10 if "Food" in description else 6),
            description=description,
        )
        db.add(assignment)
        db.flush()
        assignments_created += 1

        approved_expense = CustodyExpense(
            custody_assignment_id=assignment.id,
            user_id=user.id,
            activity_id=activity.id,
            title="Programme supplies",
            description="Seeded demonstration expense approved by finance.",
            amount=Decimal("1850.50"),
            expense_date=NOW - timedelta(days=4),
            status=ExpenseStatus.approved,
        )
        pending_expense = CustodyExpense(
            custody_assignment_id=assignment.id,
            user_id=user.id,
            activity_id=activity.id,
            title="Transport reimbursement",
            description="Seeded demonstration expense awaiting review.",
            amount=Decimal("720.00"),
            expense_date=NOW - timedelta(days=1),
            status=ExpenseStatus.pending,
        )
        rejected_expense = CustodyExpense(
            custody_assignment_id=assignment.id,
            user_id=user.id,
            activity_id=activity.id,
            title="Unapproved purchase",
            description="Seeded demonstration expense rejected by finance.",
            amount=Decimal("480.00"),
            expense_date=NOW - timedelta(days=2),
            status=ExpenseStatus.rejected,
        )
        db.add_all([approved_expense, pending_expense, rejected_expense])
        db.flush()
        db.add_all(
            [
                CustodyExpenseApproval(
                    custody_expense_id=approved_expense.id,
                    approved_by_user_id=finance.id,
                    decision=ExpenseStatus.approved,
                    comment="Receipts verified.",
                ),
                CustodyExpenseApproval(
                    custody_expense_id=rejected_expense.id,
                    approved_by_user_id=finance.id,
                    decision=ExpenseStatus.rejected,
                    comment="Outside the assigned programme scope.",
                ),
            ]
        )
        ensure_custody_expense_activity_transaction(
            db, expense=approved_expense, created_by_user_id=finance.id
        )
    return assignments_created


def create_warehouse(db: Session) -> int:
    created = 0
    for name, sku, qty, unit, location in WAREHOUSE_DEFINITIONS:
        item = db.scalar(select(WarehouseItem).where(WarehouseItem.sku == sku))
        if item:
            continue
        db.add(
            WarehouseItem(
                name=name,
                sku=sku,
                quantity=Decimal(str(qty)),
                unit=unit,
                location=location,
                notes="Seeded inventory for local demos.",
                is_active=True,
            )
        )
        created += 1
    db.flush()
    return created


def create_cases(db: Session, admin: User, staff: User) -> int:
    created = 0
    for (
        case_number,
        beneficiary,
        phone,
        category,
        status,
        priority,
        requested,
        approved,
    ) in CASE_DEFINITIONS:
        existing = db.scalar(select(AidCase).where(AidCase.case_number == case_number))
        if existing:
            continue
        db.add(
            AidCase(
                case_number=case_number,
                beneficiary_name=beneficiary,
                phone=phone,
                category=category,
                status=status,
                priority=priority,
                description=f"Seeded {category.lower()} support case for {beneficiary}.",
                requested_amount=Decimal(str(requested)),
                approved_amount=Decimal(str(approved)) if approved is not None else None,
                created_by_user_id=admin.id,
                assigned_user_id=staff.id,
            )
        )
        created += 1
    db.flush()
    return created


def create_tasks(db: Session, admin: User, users: dict[str, User]) -> int:
    specs = [
        (
            "Prepare Education Program donor report",
            "Compile confirmed donations linked to Education Program for the finance review.",
            TaskStatus.in_progress,
            TaskPriority.high,
            users["sami@charity.local"],
            NOW + timedelta(days=3),
        ),
        (
            "Follow up medical caravan suppliers",
            "Confirm medicine delivery dates and update the warehouse list.",
            TaskStatus.pending,
            TaskPriority.medium,
            users["lina@charity.local"],
            NOW + timedelta(days=5),
        ),
        (
            "Review pending custody expenses",
            "Check staff custody submissions and prepare notes for approvals.",
            TaskStatus.pending,
            TaskPriority.high,
            users["finance@charity.local"],
            NOW + timedelta(days=2),
        ),
        (
            "Archive closed feeding cases",
            "Mark completed food-aid cases and attach final notes.",
            TaskStatus.completed,
            TaskPriority.low,
            users["sami@charity.local"],
            NOW - timedelta(days=1),
        ),
    ]
    created = 0
    for title, description, status, priority, assignee, due_date in specs:
        existing = db.scalar(select(Task).where(Task.title == title))
        if existing:
            continue
        db.add(
            Task(
                title=title,
                description=description,
                status=status,
                priority=priority,
                due_date=due_date,
                assigned_user_id=assignee.id,
                created_by_user_id=admin.id,
            )
        )
        created += 1
    db.flush()
    return created


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


def seed(*, force: bool = False) -> None:
    with SessionLocal() as db:
        already = db.scalar(select(AuditLog.id).where(AuditLog.action == DEMO_MARKER))
        if already and not force:
            print("Demo marker already present; filling any missing idempotent records…")

        roles = get_or_create_roles(db)
        users = get_or_create_users(db, roles)
        admin = users["admin@charity.local"]
        finance = users["finance@charity.local"]
        staff = users["sami@charity.local"]
        donation_types = get_or_create_donation_types(db)
        donors = create_donors(db, admin.id)
        activities = get_or_create_activities(db, admin)
        donations_created = create_donations(db, donors, donation_types, activities, admin.id)
        donations_linked = link_existing_donations_to_activities(db, activities, admin.id)
        ledger_created = create_activity_ledger(db, activities, admin, finance)
        custody_created = create_custody_data(db, users, donation_types, activities, admin)
        warehouse_created = create_warehouse(db)
        cases_created = create_cases(db, admin, staff)
        tasks_created = create_tasks(db, admin, users)
        create_scheduled_report(db, admin)

        if not already:
            db.add(
                AuditLog(
                    actor_user_id=admin.id,
                    action=DEMO_MARKER,
                    entity_type="system",
                    entity_id="local-development",
                    new_value_json={
                        "users": len(users),
                        "donors": len(donors),
                        "activities": len(activities),
                        "donations_created": donations_created,
                        "activity_transactions_created": ledger_created,
                        "custody_assignments_created": custody_created,
                        "warehouse_created": warehouse_created,
                        "cases_created": cases_created,
                        "tasks_created": tasks_created,
                    },
                )
            )
        db.commit()
        print(
            "Seeded demo data:\n"
            f"  users={len(users)}\n"
            f"  donors={len(donors)}\n"
            f"  funds={len(donation_types)}\n"
            f"  activities={len(activities)}\n"
            f"  donations_added={donations_created}\n"
            f"  donations_linked_to_activities={donations_linked}\n"
            f"  activity_transactions_added={ledger_created}\n"
            f"  custody_assignments_added={custody_created}\n"
            f"  warehouse_items_added={warehouse_created}\n"
            f"  cases_added={cases_created}\n"
            f"  tasks_added={tasks_created}"
        )
        print(f"Login password for all seeded users: {DEMO_PASSWORD}")
        print("Accounts: admin@charity.local, finance@charity.local, sami@charity.local, lina@charity.local, viewer@charity.local")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed Baytak demo data")
    parser.add_argument(
        "--force",
        action="store_true",
        help="Continue even if the V2 demo marker already exists (still idempotent).",
    )
    args = parser.parse_args()
    seed(force=args.force)
