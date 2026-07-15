from decimal import Decimal

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import func
from sqlalchemy.orm import selectinload

from app.dependencies import AdminUser, CurrentUser, DbSession
from app.models import Donor, DonorAddress, DonorNote, DonorPhone, Donation, DonationStatus
from app.schemas import DonorCreate, DonorListItem, DonorOut, DonorUpdate, Message, NoteCreate
from app.services import add_audit_log

router = APIRouter(prefix="/donors", tags=["Donors"])


def normal_name(first_name: str, last_name: str) -> str:
    return f"{first_name} {last_name}".strip().lower()


def get_donor_or_404(db: DbSession, donor_id: int) -> Donor:
    donor = (
        db.query(Donor)
        .options(
            selectinload(Donor.phones),
            selectinload(Donor.addresses),
            selectinload(Donor.notes),
        )
        .filter(Donor.id == donor_id, Donor.is_deleted.is_(False))
        .first()
    )
    if not donor:
        raise HTTPException(status_code=404, detail="Donor not found")
    return donor


def donor_totals(db: DbSession, donor_id: int) -> tuple[Decimal, str | None]:
    total = db.query(func.coalesce(func.sum(Donation.amount), 0)).filter(
        Donation.donor_id == donor_id, Donation.status == DonationStatus.confirmed
    ).scalar()
    latest = (
        db.query(Donation)
        .options(selectinload(Donation.donation_type))
        .filter(Donation.donor_id == donor_id, Donation.status == DonationStatus.confirmed)
        .order_by(Donation.donation_date.desc())
        .first()
    )
    return Decimal(total or 0), latest.donation_type.type_name if latest else None


def serialize_donor(db: DbSession, donor: Donor, detailed: bool = False) -> dict:
    total, last_type = donor_totals(db, donor.id)
    result = {
        "id": donor.id,
        "first_name": donor.first_name,
        "last_name": donor.last_name,
        "normalized_full_name": donor.normalized_full_name,
        "phones": donor.phones,
        "created_at": donor.created_at,
        "updated_at": donor.updated_at,
        "total_amount_donated": total,
        "last_donation_type": last_type,
    }
    if detailed:
        result.update(
            {
                "addresses": donor.addresses,
                "notes": donor.notes,
                "created_by_user_id": donor.created_by_user_id,
            }
        )
    return result


def build_contacts(payload: DonorCreate | DonorUpdate) -> tuple[list[DonorPhone], list[DonorAddress]]:
    phones = []
    for index, phone in enumerate(payload.phones or []):
        phones.append(
            DonorPhone(
                phone_number=phone.phone_number,
                is_primary=phone.is_primary or index == 0,
            )
        )
    addresses = []
    for index, address in enumerate(payload.addresses or []):
        addresses.append(
            DonorAddress(
                address_line=address.address_line,
                city=address.city,
                country=address.country,
                is_primary=address.is_primary or index == 0,
            )
        )
    return phones, addresses


@router.get("", response_model=dict)
def list_donors(
    _: CurrentUser,
    db: DbSession,
    name: str | None = Query(default=None),
    phone: str | None = Query(default=None),
    donor_id: int | None = Query(default=None, alias="id"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
) -> dict:
    query = db.query(Donor).options(selectinload(Donor.phones)).filter(Donor.is_deleted.is_(False))
    if name:
        query = query.filter(Donor.normalized_full_name.ilike(f"%{name.strip().lower()}%"))
    if phone:
        query = query.join(DonorPhone).filter(DonorPhone.phone_number.ilike(f"%{phone.strip()}%"))
    if donor_id:
        query = query.filter(Donor.id == donor_id)
    query = query.distinct()
    total = query.count()
    donors = query.order_by(Donor.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return {
        "items": [DonorListItem.model_validate(serialize_donor(db, donor)) for donor in donors],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.post("", response_model=DonorOut, status_code=status.HTTP_201_CREATED)
def create_donor(payload: DonorCreate, current_user: CurrentUser, db: DbSession) -> dict:
    phones, addresses = build_contacts(payload)
    donor = Donor(
        first_name=payload.first_name,
        last_name=payload.last_name,
        normalized_full_name=normal_name(payload.first_name, payload.last_name),
        created_by_user_id=current_user.id,
        phones=phones,
        addresses=addresses,
    )
    db.add(donor)
    db.flush()
    add_audit_log(
        db,
        actor_user_id=current_user.id,
        action="DONOR_CREATED",
        entity_type="donor",
        entity_id=donor.id,
        new_value={"name": donor.normalized_full_name},
    )
    db.commit()
    return serialize_donor(db, get_donor_or_404(db, donor.id), detailed=True)


@router.get("/{donor_id}", response_model=DonorOut)
def get_donor(donor_id: int, _: CurrentUser, db: DbSession) -> dict:
    return serialize_donor(db, get_donor_or_404(db, donor_id), detailed=True)


@router.patch("/{donor_id}", response_model=DonorOut)
def update_donor(
    donor_id: int, payload: DonorUpdate, current_user: CurrentUser, db: DbSession
) -> dict:
    donor = get_donor_or_404(db, donor_id)
    values = payload.model_dump(exclude_unset=True, exclude={"phones", "addresses"})
    for field, value in values.items():
        setattr(donor, field, value)
    if "first_name" in values or "last_name" in values:
        donor.normalized_full_name = normal_name(donor.first_name, donor.last_name)
    if payload.phones is not None:
        donor.phones.clear()
        phones, _ = build_contacts(payload)
        donor.phones = phones
    if payload.addresses is not None:
        donor.addresses.clear()
        _, addresses = build_contacts(payload)
        donor.addresses = addresses
    add_audit_log(
        db,
        actor_user_id=current_user.id,
        action="DONOR_UPDATED",
        entity_type="donor",
        entity_id=donor.id,
        new_value=values,
    )
    db.commit()
    return serialize_donor(db, get_donor_or_404(db, donor.id), detailed=True)


@router.delete("/{donor_id}", response_model=Message)
def delete_donor(donor_id: int, admin: AdminUser, db: DbSession) -> Message:
    donor = get_donor_or_404(db, donor_id)
    donor.is_deleted = True
    add_audit_log(
        db,
        actor_user_id=admin.id,
        action="DONOR_SOFT_DELETED",
        entity_type="donor",
        entity_id=donor.id,
    )
    db.commit()
    return Message(message="Donor archived")


@router.post("/{donor_id}/notes", response_model=DonorOut)
def add_donor_note(
    donor_id: int, payload: NoteCreate, current_user: CurrentUser, db: DbSession
) -> dict:
    donor = get_donor_or_404(db, donor_id)
    donor.notes.append(DonorNote(note=payload.note, created_by_user_id=current_user.id))
    add_audit_log(
        db,
        actor_user_id=current_user.id,
        action="DONOR_NOTE_CREATED",
        entity_type="donor",
        entity_id=donor.id,
    )
    db.commit()
    return serialize_donor(db, get_donor_or_404(db, donor.id), detailed=True)


@router.get("/{donor_id}/donations", response_model=list[dict])
def donor_donations(donor_id: int, _: CurrentUser, db: DbSession) -> list[dict]:
    get_donor_or_404(db, donor_id)
    donations = (
        db.query(Donation)
        .filter(Donation.donor_id == donor_id)
        .order_by(Donation.donation_date.desc())
        .all()
    )
    return [
        {
            "id": donation.id,
            "amount": donation.amount,
            "currency": donation.currency,
            "status": donation.status,
            "donation_date": donation.donation_date,
            "donation_type_id": donation.donation_type_id,
        }
        for donation in donations
    ]
