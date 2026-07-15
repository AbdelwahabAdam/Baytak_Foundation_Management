from datetime import datetime
from decimal import Decimal
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models import (
    CustodyStatus,
    DonationStatus,
    ExpenseStatus,
    ReportFormat,
    ReportType,
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
    amount: Decimal = Field(gt=0, max_digits=14, decimal_places=2)
    currency: str = Field(default="USD", min_length=3, max_length=3)
    donation_date: datetime
    payment_method: str | None = Field(default=None, max_length=100)
    receipt_number: str | None = Field(default=None, max_length=100)
    status: DonationStatus = DonationStatus.confirmed


class DonationUpdate(Schema):
    donor_id: int | None = None
    donation_type_id: int | None = None
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


class DonationOut(Schema):
    id: int
    donor_id: int
    donation_type_id: int
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
    notes: list[DonationNoteOut] = Field(default_factory=list)


class CustodyCreate(Schema):
    user_id: int
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
