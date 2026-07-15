from datetime import datetime

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy.orm import selectinload

from app.dependencies import CurrentUser, DbSession, FinanceOrAdminUser
from app.models import (
    Donor,
    Donation,
    DonationNote,
    DonationStatus,
    DonationType,
)
from app.schemas import DonationCreate, DonationOut, DonationUpdate, Message, NoteCreate
from app.services import add_audit_log

router = APIRouter(prefix="/donations", tags=["Donations"])


def donation_query(db: DbSession):
    return db.query(Donation).options(
        selectinload(Donation.donor),
        selectinload(Donation.donation_type),
        selectinload(Donation.notes),
    )


def get_donation_or_404(db: DbSession, donation_id: int) -> Donation:
    donation = donation_query(db).filter(Donation.id == donation_id).first()
    if not donation:
        raise HTTPException(status_code=404, detail="Donation not found")
    return donation


def validate_donation_references(
    db: DbSession, donor_id: int, donation_type_id: int, allow_inactive_type: bool = False
) -> None:
    donor = db.query(Donor).filter(Donor.id == donor_id, Donor.is_deleted.is_(False)).first()
    if not donor:
        raise HTTPException(status_code=400, detail="Selected donor is not available")
    donation_type = db.query(DonationType).filter(DonationType.id == donation_type_id).first()
    if not donation_type or (not donation_type.is_active and not allow_inactive_type):
        raise HTTPException(status_code=400, detail="Selected donation type is not active")


def validate_receipt(db: DbSession, receipt_number: str | None, donation_id: int | None = None) -> None:
    if not receipt_number:
        return
    query = db.query(Donation).filter(Donation.receipt_number == receipt_number)
    if donation_id:
        query = query.filter(Donation.id != donation_id)
    if query.first():
        raise HTTPException(status_code=409, detail="Receipt number already exists")


@router.get("", response_model=dict)
def list_donations(
    _: CurrentUser,
    db: DbSession,
    amount_min: float | None = Query(default=None, ge=0),
    amount_max: float | None = Query(default=None, ge=0),
    donation_type_id: int | None = Query(default=None),
    donor_id: int | None = Query(default=None),
    start_date: datetime | None = Query(default=None),
    end_date: datetime | None = Query(default=None),
    donation_status: DonationStatus | None = Query(default=None, alias="status"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
) -> dict:
    query = donation_query(db)
    if amount_min is not None:
        query = query.filter(Donation.amount >= amount_min)
    if amount_max is not None:
        query = query.filter(Donation.amount <= amount_max)
    if donation_type_id:
        query = query.filter(Donation.donation_type_id == donation_type_id)
    if donor_id:
        query = query.filter(Donation.donor_id == donor_id)
    if start_date:
        query = query.filter(Donation.donation_date >= start_date)
    if end_date:
        query = query.filter(Donation.donation_date <= end_date)
    if donation_status:
        query = query.filter(Donation.status == donation_status)
    total = query.count()
    items = (
        query.order_by(Donation.donation_date.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return {
        "items": [DonationOut.model_validate(item) for item in items],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.post("", response_model=DonationOut, status_code=status.HTTP_201_CREATED)
def create_donation(
    payload: DonationCreate, current_user: CurrentUser, db: DbSession
) -> Donation:
    validate_donation_references(db, payload.donor_id, payload.donation_type_id)
    validate_receipt(db, payload.receipt_number)
    donation = Donation(**payload.model_dump(), created_by_user_id=current_user.id)
    db.add(donation)
    db.flush()
    add_audit_log(
        db,
        actor_user_id=current_user.id,
        action="DONATION_CREATED",
        entity_type="donation",
        entity_id=donation.id,
        new_value={
            "amount": str(donation.amount),
            "donor_id": donation.donor_id,
            "donation_type_id": donation.donation_type_id,
        },
    )
    db.commit()
    return get_donation_or_404(db, donation.id)


@router.get("/{donation_id}", response_model=DonationOut)
def get_donation(donation_id: int, _: CurrentUser, db: DbSession) -> Donation:
    return get_donation_or_404(db, donation_id)


@router.patch("/{donation_id}", response_model=DonationOut)
def update_donation(
    donation_id: int, payload: DonationUpdate, approver: FinanceOrAdminUser, db: DbSession
) -> Donation:
    donation = get_donation_or_404(db, donation_id)
    values = payload.model_dump(exclude_unset=True)
    donor_id = values.get("donor_id", donation.donor_id)
    type_id = values.get("donation_type_id", donation.donation_type_id)
    validate_donation_references(db, donor_id, type_id, allow_inactive_type=True)
    validate_receipt(db, values.get("receipt_number", donation.receipt_number), donation.id)
    old_value = {
        "amount": str(donation.amount),
        "status": donation.status.value,
        "donor_id": donation.donor_id,
        "donation_type_id": donation.donation_type_id,
    }
    for field, value in values.items():
        setattr(donation, field, value)
    add_audit_log(
        db,
        actor_user_id=approver.id,
        action="DONATION_UPDATED",
        entity_type="donation",
        entity_id=donation.id,
        old_value=old_value,
        new_value={key: str(value) for key, value in values.items()},
    )
    db.commit()
    return get_donation_or_404(db, donation.id)


@router.delete("/{donation_id}", response_model=Message)
def cancel_donation(
    donation_id: int, approver: FinanceOrAdminUser, db: DbSession
) -> Message:
    donation = get_donation_or_404(db, donation_id)
    if donation.status == DonationStatus.cancelled:
        raise HTTPException(status_code=400, detail="Donation is already cancelled")
    previous_status = donation.status.value
    donation.status = DonationStatus.cancelled
    add_audit_log(
        db,
        actor_user_id=approver.id,
        action="DONATION_CANCELLED",
        entity_type="donation",
        entity_id=donation.id,
        old_value={"status": previous_status},
        new_value={"status": DonationStatus.cancelled.value},
    )
    db.commit()
    return Message(message="Donation cancelled")


@router.post("/{donation_id}/notes", response_model=DonationOut)
def add_donation_note(
    donation_id: int, payload: NoteCreate, current_user: CurrentUser, db: DbSession
) -> Donation:
    donation = get_donation_or_404(db, donation_id)
    donation.notes.append(DonationNote(note=payload.note, created_by_user_id=current_user.id))
    add_audit_log(
        db,
        actor_user_id=current_user.id,
        action="DONATION_NOTE_CREATED",
        entity_type="donation",
        entity_id=donation.id,
    )
    db.commit()
    return get_donation_or_404(db, donation.id)
