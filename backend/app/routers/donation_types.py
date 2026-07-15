from fastapi import APIRouter, HTTPException, Query, status

from app.dependencies import AdminUser, CurrentUser, DbSession
from app.models import DonationType
from app.schemas import DonationTypeCreate, DonationTypeOut, DonationTypeUpdate, Message
from app.services import add_audit_log

router = APIRouter(prefix="/donation-types", tags=["Donation Types"])


def get_type_or_404(db: DbSession, donation_type_id: int) -> DonationType:
    item = db.query(DonationType).filter(DonationType.id == donation_type_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Donation type not found")
    return item


@router.get("", response_model=list[DonationTypeOut])
def list_donation_types(
    _: CurrentUser,
    db: DbSession,
    search: str | None = Query(default=None),
    include_inactive: bool = Query(default=True),
) -> list[DonationType]:
    query = db.query(DonationType)
    if search:
        query = query.filter(DonationType.type_name.ilike(f"%{search.strip()}%"))
    if not include_inactive:
        query = query.filter(DonationType.is_active.is_(True))
    return query.order_by(DonationType.type_name).all()


@router.post("", response_model=DonationTypeOut, status_code=status.HTTP_201_CREATED)
def create_donation_type(
    payload: DonationTypeCreate, admin: AdminUser, db: DbSession
) -> DonationType:
    if db.query(DonationType).filter(DonationType.type_name.ilike(payload.type_name.strip())).first():
        raise HTTPException(status_code=409, detail="A donation type with this name already exists")
    item = DonationType(
        **payload.model_dump(exclude={"type_name"}),
        type_name=payload.type_name.strip(),
    )
    db.add(item)
    db.flush()
    add_audit_log(
        db,
        actor_user_id=admin.id,
        action="DONATION_TYPE_CREATED",
        entity_type="donation_type",
        entity_id=item.id,
        new_value={"name": item.type_name},
    )
    db.commit()
    db.refresh(item)
    return item


@router.get("/{donation_type_id}", response_model=DonationTypeOut)
def get_donation_type(
    donation_type_id: int, _: CurrentUser, db: DbSession
) -> DonationType:
    return get_type_or_404(db, donation_type_id)


@router.patch("/{donation_type_id}", response_model=DonationTypeOut)
def update_donation_type(
    donation_type_id: int, payload: DonationTypeUpdate, admin: AdminUser, db: DbSession
) -> DonationType:
    item = get_type_or_404(db, donation_type_id)
    values = payload.model_dump(exclude_unset=True)
    if "type_name" in values and values["type_name"]:
        values["type_name"] = values["type_name"].strip()
        duplicate = (
            db.query(DonationType)
            .filter(
                DonationType.type_name.ilike(values["type_name"]),
                DonationType.id != donation_type_id,
            )
            .first()
        )
        if duplicate:
            raise HTTPException(status_code=409, detail="A donation type with this name already exists")
    for field, value in values.items():
        setattr(item, field, value)
    add_audit_log(
        db,
        actor_user_id=admin.id,
        action="DONATION_TYPE_UPDATED",
        entity_type="donation_type",
        entity_id=item.id,
        new_value=values,
    )
    db.commit()
    db.refresh(item)
    return item


@router.delete("/{donation_type_id}", response_model=Message)
def deactivate_donation_type(
    donation_type_id: int, admin: AdminUser, db: DbSession
) -> Message:
    item = get_type_or_404(db, donation_type_id)
    item.is_active = False
    add_audit_log(
        db,
        actor_user_id=admin.id,
        action="DONATION_TYPE_DEACTIVATED",
        entity_type="donation_type",
        entity_id=item.id,
    )
    db.commit()
    return Message(message="Donation type deactivated")
