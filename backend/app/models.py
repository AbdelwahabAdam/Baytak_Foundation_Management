import enum
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    JSON,
    Numeric,
    String,
    Table,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class DonationStatus(str, enum.Enum):
    confirmed = "confirmed"
    cancelled = "cancelled"
    refunded = "refunded"


class CaseStatus(str, enum.Enum):
    open = "open"
    in_progress = "in_progress"
    closed = "closed"
    cancelled = "cancelled"


class CasePriority(str, enum.Enum):
    low = "low"
    medium = "medium"
    high = "high"
    urgent = "urgent"


class ActivityStatus(str, enum.Enum):
    active = "active"
    inactive = "inactive"


class TransactionDirection(str, enum.Enum):
    income = "income"
    expense = "expense"


class ActivityTransactionType(str, enum.Enum):
    donation = "donation"
    sale = "sale"
    grant = "grant"
    manual_income = "manual_income"
    manual_expense = "manual_expense"
    purchase = "purchase"
    salary = "salary"
    maintenance = "maintenance"
    utilities = "utilities"
    transportation = "transportation"
    marketing = "marketing"
    other = "other"


class TransactionReferenceType(str, enum.Enum):
    donation = "donation"
    custody_expense = "custody_expense"
    manual = "manual"
    sale = "sale"
    grant = "grant"


class CustodyStatus(str, enum.Enum):
    active = "active"
    closed = "closed"
    cancelled = "cancelled"


class ExpenseStatus(str, enum.Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"


class ReportType(str, enum.Enum):
    donations = "donations"
    donors = "donors"
    custody = "custody"


class ReportFormat(str, enum.Enum):
    csv = "csv"
    pdf = "pdf"
    excel = "excel"


class GeneratedReportStatus(str, enum.Enum):
    pending = "pending"
    completed = "completed"
    failed = "failed"


user_roles = Table(
    "user_roles",
    Base.metadata,
    Column("user_id", ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column("role_id", ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True),
)


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now, server_default=func.now()
    )


class User(TimestampMixin, Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    first_name: Mapped[str] = mapped_column(String(100))
    last_name: Mapped[str] = mapped_column(String(100))
    phone_number: Mapped[str | None] = mapped_column(String(50))
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")
    roles: Mapped[list["Role"]] = relationship(secondary=user_roles, back_populates="users")
    created_donors: Mapped[list["Donor"]] = relationship(
        foreign_keys="Donor.created_by_user_id", back_populates="created_by"
    )

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}".strip()


class Role(Base):
    __tablename__ = "roles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    description: Mapped[str | None] = mapped_column(String(255))
    users: Mapped[list[User]] = relationship(secondary=user_roles, back_populates="roles")


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    token_jti: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, server_default=func.now()
    )


class PasswordResetToken(Base):
    __tablename__ = "password_reset_tokens"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    token_jti: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, server_default=func.now()
    )


class Donor(TimestampMixin, Base):
    __tablename__ = "donors"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    first_name: Mapped[str] = mapped_column(String(100), index=True)
    last_name: Mapped[str] = mapped_column(String(100), index=True)
    normalized_full_name: Mapped[str] = mapped_column(String(205), index=True)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    created_by_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    created_by: Mapped[User] = relationship(foreign_keys=[created_by_user_id], back_populates="created_donors")
    phones: Mapped[list["DonorPhone"]] = relationship(
        back_populates="donor", cascade="all, delete-orphan"
    )
    addresses: Mapped[list["DonorAddress"]] = relationship(
        back_populates="donor", cascade="all, delete-orphan"
    )
    notes: Mapped[list["DonorNote"]] = relationship(
        back_populates="donor", cascade="all, delete-orphan", order_by="DonorNote.created_at.desc()"
    )
    donations: Mapped[list["Donation"]] = relationship(back_populates="donor")


class DonorPhone(Base):
    __tablename__ = "donor_phone_numbers"
    __table_args__ = (Index("ix_donor_phone_numbers_phone_number", "phone_number"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    donor_id: Mapped[int] = mapped_column(ForeignKey("donors.id", ondelete="CASCADE"), index=True)
    phone_number: Mapped[str] = mapped_column(String(50))
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    donor: Mapped[Donor] = relationship(back_populates="phones")


class DonorAddress(Base):
    __tablename__ = "donor_addresses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    donor_id: Mapped[int] = mapped_column(ForeignKey("donors.id", ondelete="CASCADE"), index=True)
    address_line: Mapped[str] = mapped_column(Text)
    city: Mapped[str | None] = mapped_column(String(100))
    country: Mapped[str | None] = mapped_column(String(100))
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    donor: Mapped[Donor] = relationship(back_populates="addresses")


class DonorNote(Base):
    __tablename__ = "donor_notes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    donor_id: Mapped[int] = mapped_column(ForeignKey("donors.id", ondelete="CASCADE"), index=True)
    note: Mapped[str] = mapped_column(Text)
    created_by_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, server_default=func.now()
    )
    donor: Mapped[Donor] = relationship(back_populates="notes")
    created_by: Mapped[User] = relationship(foreign_keys=[created_by_user_id])


class DonationType(TimestampMixin, Base):
    __tablename__ = "donation_types"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    type_name: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    description: Mapped[str | None] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")
    donations: Mapped[list["Donation"]] = relationship(back_populates="donation_type")
    custody_assignments: Mapped[list["CustodyAssignment"]] = relationship(
        back_populates="donation_type"
    )


class Donation(TimestampMixin, Base):
    __tablename__ = "donations"
    __table_args__ = (
        Index("ix_donations_type_date", "donation_type_id", "donation_date"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    donor_id: Mapped[int] = mapped_column(ForeignKey("donors.id"), index=True)
    donation_type_id: Mapped[int] = mapped_column(ForeignKey("donation_types.id"), index=True)
    activity_id: Mapped[int | None] = mapped_column(
        ForeignKey("activities.id"), index=True, nullable=True
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), index=True)
    currency: Mapped[str] = mapped_column(String(3), default="EGP", server_default="EGP")
    donation_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    payment_method: Mapped[str | None] = mapped_column(String(100))
    receipt_number: Mapped[str | None] = mapped_column(String(100), unique=True)
    status: Mapped[DonationStatus] = mapped_column(
        Enum(DonationStatus, name="donation_status"), default=DonationStatus.confirmed
    )
    created_by_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    donor: Mapped[Donor] = relationship(back_populates="donations")
    donation_type: Mapped[DonationType] = relationship(back_populates="donations")
    activity: Mapped["Activity | None"] = relationship(back_populates="donations")
    created_by: Mapped[User] = relationship(foreign_keys=[created_by_user_id])
    notes: Mapped[list["DonationNote"]] = relationship(
        back_populates="donation", cascade="all, delete-orphan", order_by="DonationNote.created_at.desc()"
    )


class DonationNote(Base):
    __tablename__ = "donation_notes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    donation_id: Mapped[int] = mapped_column(ForeignKey("donations.id", ondelete="CASCADE"), index=True)
    note: Mapped[str] = mapped_column(Text)
    created_by_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, server_default=func.now()
    )
    donation: Mapped[Donation] = relationship(back_populates="notes")
    created_by: Mapped[User] = relationship(foreign_keys=[created_by_user_id])


class CustodyAssignment(TimestampMixin, Base):
    __tablename__ = "custody_assignments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    donation_type_id: Mapped[int | None] = mapped_column(
        ForeignKey("donation_types.id"), index=True, nullable=True
    )
    activity_id: Mapped[int | None] = mapped_column(
        ForeignKey("activities.id"), index=True, nullable=True
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    assigned_by_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    assigned_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    description: Mapped[str | None] = mapped_column(Text)
    status: Mapped[CustodyStatus] = mapped_column(
        Enum(CustodyStatus, name="custody_status"), default=CustodyStatus.active
    )
    user: Mapped[User] = relationship(foreign_keys=[user_id])
    assigned_by: Mapped[User] = relationship(foreign_keys=[assigned_by_user_id])
    donation_type: Mapped[DonationType | None] = relationship(
        foreign_keys=[donation_type_id], back_populates="custody_assignments"
    )
    activity: Mapped["Activity | None"] = relationship(back_populates="custody_assignments")
    expenses: Mapped[list["CustodyExpense"]] = relationship(
        back_populates="custody_assignment", cascade="all, delete-orphan"
    )


class CustodyExpense(TimestampMixin, Base):
    __tablename__ = "custody_expenses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    custody_assignment_id: Mapped[int] = mapped_column(
        ForeignKey("custody_assignments.id"), index=True
    )
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    activity_id: Mapped[int | None] = mapped_column(
        ForeignKey("activities.id"), index=True, nullable=True
    )
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text)
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    expense_date: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    status: Mapped[ExpenseStatus] = mapped_column(
        Enum(ExpenseStatus, name="expense_status"), default=ExpenseStatus.pending, index=True
    )
    submitted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    custody_assignment: Mapped[CustodyAssignment] = relationship(back_populates="expenses")
    user: Mapped[User] = relationship(foreign_keys=[user_id])
    activity: Mapped["Activity | None"] = relationship(back_populates="custody_expenses")
    approvals: Mapped[list["CustodyExpenseApproval"]] = relationship(
        back_populates="expense", cascade="all, delete-orphan", order_by="CustodyExpenseApproval.decided_at.desc()"
    )


class CustodyExpenseApproval(Base):
    __tablename__ = "custody_expense_approvals"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    custody_expense_id: Mapped[int] = mapped_column(
        ForeignKey("custody_expenses.id", ondelete="CASCADE"), index=True
    )
    approved_by_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    decision: Mapped[ExpenseStatus] = mapped_column(Enum(ExpenseStatus, name="approval_decision"))
    comment: Mapped[str | None] = mapped_column(Text)
    decided_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    expense: Mapped[CustodyExpense] = relationship(back_populates="approvals")
    approved_by: Mapped[User] = relationship(foreign_keys=[approved_by_user_id])


class ScheduledReport(TimestampMixin, Base):
    __tablename__ = "scheduled_reports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    report_type: Mapped[ReportType] = mapped_column(Enum(ReportType, name="report_type"))
    frequency: Mapped[str] = mapped_column(String(30))
    cron_expression: Mapped[str | None] = mapped_column(String(100))
    filters_json: Mapped[dict] = mapped_column(JSON, default=dict)
    recipients_json: Mapped[list] = mapped_column(JSON, default=list)
    format: Mapped[ReportFormat] = mapped_column(Enum(ReportFormat, name="report_format"))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")
    last_run_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    next_run_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_by_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))


class GeneratedReport(Base):
    __tablename__ = "generated_reports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    scheduled_report_id: Mapped[int | None] = mapped_column(ForeignKey("scheduled_reports.id"))
    report_type: Mapped[ReportType] = mapped_column(Enum(ReportType, name="generated_report_type"))
    file_path: Mapped[str | None] = mapped_column(String(500))
    format: Mapped[ReportFormat] = mapped_column(Enum(ReportFormat, name="generated_report_format"))
    generated_by_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    status: Mapped[GeneratedReportStatus] = mapped_column(
        Enum(GeneratedReportStatus, name="generated_report_status"),
        default=GeneratedReportStatus.completed,
    )
    error_message: Mapped[str | None] = mapped_column(Text)


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    actor_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), index=True)
    action: Mapped[str] = mapped_column(String(100), index=True)
    entity_type: Mapped[str] = mapped_column(String(100), index=True)
    entity_id: Mapped[str] = mapped_column(String(100), index=True)
    old_value_json: Mapped[dict | None] = mapped_column(JSON)
    new_value_json: Mapped[dict | None] = mapped_column(JSON)
    ip_address: Mapped[str | None] = mapped_column(String(64))
    user_agent: Mapped[str | None] = mapped_column(String(512))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, server_default=func.now()
    )


class WarehouseItem(TimestampMixin, Base):
    __tablename__ = "warehouse_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(150), index=True)
    sku: Mapped[str | None] = mapped_column(String(80), unique=True)
    quantity: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=0, server_default="0")
    unit: Mapped[str] = mapped_column(String(40), default="piece", server_default="piece")
    location: Mapped[str | None] = mapped_column(String(150))
    notes: Mapped[str | None] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")


class AidCase(TimestampMixin, Base):
    __tablename__ = "aid_cases"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    case_number: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    beneficiary_name: Mapped[str] = mapped_column(String(200), index=True)
    phone: Mapped[str | None] = mapped_column(String(50))
    category: Mapped[str] = mapped_column(String(100), index=True)
    status: Mapped[CaseStatus] = mapped_column(
        Enum(CaseStatus, name="case_status"), default=CaseStatus.open, index=True
    )
    priority: Mapped[CasePriority] = mapped_column(
        Enum(CasePriority, name="case_priority"), default=CasePriority.medium
    )
    description: Mapped[str | None] = mapped_column(Text)
    requested_amount: Mapped[Decimal | None] = mapped_column(Numeric(14, 2))
    approved_amount: Mapped[Decimal | None] = mapped_column(Numeric(14, 2))
    created_by_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    assigned_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), index=True)
    created_by: Mapped[User] = relationship(foreign_keys=[created_by_user_id])
    assigned_user: Mapped[User | None] = relationship(foreign_keys=[assigned_user_id])


class Activity(TimestampMixin, Base):
    __tablename__ = "activities"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(200), unique=True, index=True)
    description: Mapped[str | None] = mapped_column(Text)
    activity_type: Mapped[str] = mapped_column(String(100), index=True)
    status: Mapped[ActivityStatus] = mapped_column(
        Enum(ActivityStatus, name="activity_status"),
        default=ActivityStatus.active,
        index=True,
    )
    created_by_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    created_by: Mapped[User] = relationship(foreign_keys=[created_by_user_id])
    donations: Mapped[list["Donation"]] = relationship(back_populates="activity")
    custody_assignments: Mapped[list["CustodyAssignment"]] = relationship(back_populates="activity")
    custody_expenses: Mapped[list["CustodyExpense"]] = relationship(back_populates="activity")
    transactions: Mapped[list["ActivityTransaction"]] = relationship(
        back_populates="activity",
        cascade="all, delete-orphan",
        order_by="ActivityTransaction.transaction_date.desc()",
    )


class ActivityTransaction(TimestampMixin, Base):
    __tablename__ = "activity_transactions"
    __table_args__ = (
        Index("ix_activity_transactions_activity_date", "activity_id", "transaction_date"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    activity_id: Mapped[int] = mapped_column(ForeignKey("activities.id"), index=True)
    transaction_direction: Mapped[TransactionDirection] = mapped_column(
        Enum(TransactionDirection, name="transaction_direction"), index=True
    )
    transaction_type: Mapped[ActivityTransactionType] = mapped_column(
        Enum(ActivityTransactionType, name="activity_transaction_type"), index=True
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    description: Mapped[str | None] = mapped_column(Text)
    reference_type: Mapped[TransactionReferenceType | None] = mapped_column(
        Enum(TransactionReferenceType, name="transaction_reference_type"), nullable=True
    )
    reference_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    transaction_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    created_by_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    activity: Mapped[Activity] = relationship(back_populates="transactions")
    created_by: Mapped[User] = relationship(foreign_keys=[created_by_user_id])
