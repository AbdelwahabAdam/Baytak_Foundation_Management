from datetime import datetime
from decimal import Decimal
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models import (
    ActivityStatus,
    ActivityTransactionType,
    CasePriority,
    CaseStatus,
    CustodyStatus,
    DonationStatus,
    ExpenseStatus,
    ReportFormat,
    ReportType,
    TransactionDirection,
    TransactionReferenceType,
)


class Schema(BaseModel):
    model_config = ConfigDict(from_attributes=True)


EmailAddress = Annotated[
    str,
    Field(
        min_length=3,
        max_length=255,
        pattern=r"^[^@\s]+@[^@\s]+$",
        description="An email-shaped identifier; local internal domains are allowed.",
    ),
]


class Message(Schema):
    message: str


class TokenPair(Schema):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class LoginRequest(Schema):
    email: EmailAddress
    password: str = Field(min_length=1)


class RefreshRequest(Schema):
    refresh_token: str


class PasswordChange(Schema):
    current_password: str = Field(min_length=1)
    new_password: str = Field(min_length=8, max_length=128)


class PasswordResetRequest(Schema):
    email: EmailAddress


class PasswordResetConfirm(Schema):
    token: str = Field(min_length=20, max_length=4096)
    new_password: str = Field(min_length=8, max_length=128)


class RoleOut(Schema):
    id: int
    name: str
    description: str | None = None


class UserBase(Schema):
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    phone_number: str | None = Field(default=None, max_length=50)
    email: EmailAddress


class UserCreate(UserBase):
    password: str = Field(min_length=8, max_length=128)
    role_ids: list[int] = Field(default_factory=list)


class UserUpdate(Schema):
    first_name: str | None = Field(default=None, min_length=1, max_length=100)
    last_name: str | None = Field(default=None, min_length=1, max_length=100)
    phone_number: str | None = Field(default=None, max_length=50)
    email: EmailAddress | None = None
    is_active: bool | None = None


class ProfileUpdate(Schema):
    first_name: str | None = Field(default=None, min_length=1, max_length=100)
    last_name: str | None = Field(default=None, min_length=1, max_length=100)
    phone_number: str | None = Field(default=None, max_length=50)


class UserOut(UserBase):
    id: int
    is_active: bool
    roles: list[RoleOut]
    created_at: datetime
    updated_at: datetime


class PhoneInput(Schema):
    phone_number: str = Field(min_length=3, max_length=50)
    is_primary: bool = False


class PhoneOut(PhoneInput):
    id: int


class AddressInput(Schema):
    address_line: str = Field(min_length=1)
    city: str | None = Field(default=None, max_length=100)
    country: str | None = Field(default=None, max_length=100)
    is_primary: bool = False


class AddressOut(AddressInput):
    id: int


class DonorNoteOut(Schema):
    id: int
    note: str
    created_by_user_id: int
    created_at: datetime


class DonorCreate(Schema):
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    phones: list[PhoneInput] = Field(default_factory=list)
    addresses: list[AddressInput] = Field(default_factory=list)


class DonorUpdate(Schema):
    first_name: str | None = Field(default=None, min_length=1, max_length=100)
    last_name: str | None = Field(default=None, min_length=1, max_length=100)
    phones: list[PhoneInput] | None = None
    addresses: list[AddressInput] | None = None


class DonorListItem(Schema):
    id: int
    first_name: str
    last_name: str
    normalized_full_name: str
    phones: list[PhoneOut]
    created_at: datetime
    updated_at: datetime
    total_amount_donated: Decimal = Decimal("0")
    last_donation_type: str | None = None


class DonorOut(DonorListItem):
    addresses: list[AddressOut]
    notes: list[DonorNoteOut]
    created_by_user_id: int


class NoteCreate(Schema):
    note: str = Field(min_length=1)


class DonationTypeCreate(Schema):
    type_name: str = Field(min_length=1, max_length=100)
    description: str | None = None
    is_active: bool = True


class DonationTypeUpdate(Schema):
    type_name: str | None = Field(default=None, min_length=1, max_length=100)
    description: str | None = None
    is_active: bool | None = None


class DonationTypeOut(Schema):
    id: int
    type_name: str
    description: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime


class DonationCreate(Schema):
    donor_id: int
    donation_type_id: int
    activity_id: int | None = None
    amount: Decimal = Field(gt=0, max_digits=14, decimal_places=2)
    currency: str = Field(default="EGP", min_length=3, max_length=3)
    donation_date: datetime
    payment_method: str | None = Field(default=None, max_length=100)
    receipt_number: str | None = Field(default=None, max_length=100)
    status: DonationStatus = DonationStatus.confirmed


class DonationUpdate(Schema):
    donor_id: int | None = None
    donation_type_id: int | None = None
    activity_id: int | None = None
    amount: Decimal | None = Field(default=None, gt=0, max_digits=14, decimal_places=2)
    currency: str | None = Field(default=None, min_length=3, max_length=3)
    donation_date: datetime | None = None
    payment_method: str | None = Field(default=None, max_length=100)
    receipt_number: str | None = Field(default=None, max_length=100)
    status: DonationStatus | None = None


class DonationNoteOut(Schema):
    id: int
    note: str
    created_by_user_id: int
    created_at: datetime


class DonorShort(Schema):
    id: int
    first_name: str
    last_name: str


class ActivityShort(Schema):
    id: int
    name: str
    status: ActivityStatus


class DonationOut(Schema):
    id: int
    donor_id: int
    donation_type_id: int
    activity_id: int | None = None
    amount: Decimal
    currency: str
    donation_date: datetime
    payment_method: str | None
    receipt_number: str | None
    status: DonationStatus
    created_by_user_id: int
    created_at: datetime
    updated_at: datetime
    donor: DonorShort
    donation_type: DonationTypeOut
    activity: ActivityShort | None = None
    notes: list[DonationNoteOut] = Field(default_factory=list)


class CustodyCreate(Schema):
    user_id: int
    donation_type_id: int
    activity_id: int | None = None
    amount: Decimal = Field(gt=0, max_digits=14, decimal_places=2)
    assigned_at: datetime | None = None
    description: str | None = None


class CustodyUpdate(Schema):
    description: str | None = None
    status: CustodyStatus | None = None


class ExpenseCreate(Schema):
    title: str = Field(min_length=1, max_length=255)
    description: str | None = None
    amount: Decimal = Field(gt=0, max_digits=14, decimal_places=2)
    expense_date: datetime


class ApprovalCreate(Schema):
    comment: str | None = None


class ApprovalOut(Schema):
    id: int
    approved_by_user_id: int
    decision: ExpenseStatus
    comment: str | None
    decided_at: datetime


class CustodyExpenseOut(Schema):
    id: int
    custody_assignment_id: int
    user_id: int
    activity_id: int | None = None
    title: str
    description: str | None
    amount: Decimal
    expense_date: datetime
    status: ExpenseStatus
    submitted_at: datetime
    created_at: datetime
    updated_at: datetime
    approvals: list[ApprovalOut] = Field(default_factory=list)


class CustodyOut(Schema):
    id: int
    user_id: int
    recipient_name: str
    recipient_email: str
    donation_type_id: int | None = None
    donation_type_name: str | None = None
    activity_id: int | None = None
    activity_name: str | None = None
    amount: Decimal
    assigned_by_user_id: int
    assigned_by_name: str
    assigned_at: datetime
    description: str | None
    status: CustodyStatus
    created_at: datetime
    updated_at: datetime
    expenses: list[CustodyExpenseOut] = Field(default_factory=list)
    available_balance: Decimal = Decimal("0")


class CustodySummary(Schema):
    user_id: int
    assigned_total: Decimal
    approved_expenses_total: Decimal
    available_balance: Decimal
    pending_expenses_total: Decimal


class ReportGenerate(Schema):
    report_type: ReportType
    format: ReportFormat = ReportFormat.csv
    start_date: datetime
    end_date: datetime
    donation_type_id: int | None = None
    donor_id: int | None = None

    @model_validator(mode="after")
    def validate_date_range(self) -> "ReportGenerate":
        if self.end_date < self.start_date:
            raise ValueError("end_date must be on or after start_date")
        return self


class ScheduledReportCreate(Schema):
    name: str = Field(min_length=1, max_length=255)
    report_type: ReportType
    frequency: str = Field(pattern="^(weekly|monthly|yearly|custom)$")
    cron_expression: str | None = None
    filters_json: dict = Field(default_factory=dict)
    recipients_json: list[EmailAddress] = Field(default_factory=list)
    format: ReportFormat = ReportFormat.csv
    is_active: bool = True


class ScheduledReportUpdate(Schema):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    report_type: ReportType | None = None
    frequency: str | None = Field(default=None, pattern="^(weekly|monthly|yearly|custom)$")
    cron_expression: str | None = None
    filters_json: dict | None = None
    recipients_json: list[EmailAddress] | None = None
    format: ReportFormat | None = None
    is_active: bool | None = None


class ScheduledReportOut(Schema):
    id: int
    name: str
    report_type: ReportType
    frequency: str
    cron_expression: str | None
    filters_json: dict
    recipients_json: list
    format: ReportFormat
    is_active: bool
    last_run_at: datetime | None
    next_run_at: datetime | None
    created_by_user_id: int
    created_at: datetime
    updated_at: datetime


class AuditLogOut(Schema):
    id: int
    actor_user_id: int | None
    action: str
    entity_type: str
    entity_id: str
    old_value_json: dict | None
    new_value_json: dict | None
    created_at: datetime


class WarehouseItemCreate(Schema):
    name: str = Field(min_length=1, max_length=150)
    sku: str | None = Field(default=None, max_length=80)
    quantity: Decimal = Field(default=0, ge=0, max_digits=14, decimal_places=2)
    unit: str = Field(default="piece", min_length=1, max_length=40)
    location: str | None = Field(default=None, max_length=150)
    notes: str | None = None
    is_active: bool = True


class WarehouseItemUpdate(Schema):
    name: str | None = Field(default=None, min_length=1, max_length=150)
    sku: str | None = Field(default=None, max_length=80)
    quantity: Decimal | None = Field(default=None, ge=0, max_digits=14, decimal_places=2)
    unit: str | None = Field(default=None, min_length=1, max_length=40)
    location: str | None = Field(default=None, max_length=150)
    notes: str | None = None
    is_active: bool | None = None


class WarehouseItemOut(Schema):
    id: int
    name: str
    sku: str | None
    quantity: Decimal
    unit: str
    location: str | None
    notes: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime


class AidCaseCreate(Schema):
    case_number: str | None = Field(default=None, max_length=50)
    beneficiary_name: str = Field(min_length=1, max_length=200)
    phone: str | None = Field(default=None, max_length=50)
    category: str = Field(min_length=1, max_length=100)
    status: CaseStatus = CaseStatus.open
    priority: CasePriority = CasePriority.medium
    description: str | None = None
    requested_amount: Decimal | None = Field(default=None, ge=0, max_digits=14, decimal_places=2)
    approved_amount: Decimal | None = Field(default=None, ge=0, max_digits=14, decimal_places=2)
    assigned_user_id: int | None = None


class AidCaseUpdate(Schema):
    case_number: str | None = Field(default=None, max_length=50)
    beneficiary_name: str | None = Field(default=None, min_length=1, max_length=200)
    phone: str | None = Field(default=None, max_length=50)
    category: str | None = Field(default=None, min_length=1, max_length=100)
    status: CaseStatus | None = None
    priority: CasePriority | None = None
    description: str | None = None
    requested_amount: Decimal | None = Field(default=None, ge=0, max_digits=14, decimal_places=2)
    approved_amount: Decimal | None = Field(default=None, ge=0, max_digits=14, decimal_places=2)
    assigned_user_id: int | None = None


class AidCaseOut(Schema):
    id: int
    case_number: str
    beneficiary_name: str
    phone: str | None
    category: str
    status: CaseStatus
    priority: CasePriority
    description: str | None
    requested_amount: Decimal | None
    approved_amount: Decimal | None
    created_by_user_id: int
    assigned_user_id: int | None
    created_at: datetime
    updated_at: datetime


class ActivityCreate(Schema):
    name: str = Field(min_length=1, max_length=200)
    description: str | None = None
    activity_type: str = Field(min_length=1, max_length=100)
    status: ActivityStatus = ActivityStatus.active


class ActivityUpdate(Schema):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = None
    activity_type: str | None = Field(default=None, min_length=1, max_length=100)
    status: ActivityStatus | None = None


class ActivityOut(Schema):
    id: int
    name: str
    description: str | None
    activity_type: str
    status: ActivityStatus
    created_by_user_id: int
    created_at: datetime
    updated_at: datetime
    total_income: Decimal = Decimal("0")
    total_expense: Decimal = Decimal("0")
    balance: Decimal = Decimal("0")
    transaction_count: int = 0


class ActivitySummary(Schema):
    total_income: Decimal
    total_expense: Decimal
    balance: Decimal
    donations: Decimal = Decimal("0")
    sales: Decimal = Decimal("0")
    grants: Decimal = Decimal("0")
    expenses: Decimal = Decimal("0")


class ActivityTransactionCreate(Schema):
    transaction_type: ActivityTransactionType
    amount: Decimal | None = Field(default=None, gt=0, max_digits=14, decimal_places=2)
    description: str | None = None
    reference_type: TransactionReferenceType | None = None
    reference_id: int | None = None
    transaction_date: datetime | None = None

    @model_validator(mode="after")
    def validate_create(self) -> "ActivityTransactionCreate":
        if self.transaction_type == ActivityTransactionType.donation:
            if not self.reference_id:
                raise ValueError("reference_id (donation id) is required for donation transactions")
            return self
        if self.amount is None:
            raise ValueError("amount is required for non-donation transactions")
        return self


class ActivityTransactionOut(Schema):
    id: int
    activity_id: int
    transaction_direction: TransactionDirection
    transaction_type: ActivityTransactionType
    amount: Decimal
    description: str | None
    reference_type: TransactionReferenceType | None
    reference_id: int | None
    transaction_date: datetime
    created_by_user_id: int
    created_at: datetime
    updated_at: datetime
    running_balance: Decimal | None = None
