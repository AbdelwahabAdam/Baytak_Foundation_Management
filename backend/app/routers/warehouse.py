from decimal import Decimal

from fastapi import APIRouter, HTTPException, Query, status

from app.dependencies import CurrentUser, DbSession
from app.models import WarehouseItem
from app.schemas import Message, WarehouseItemCreate, WarehouseItemOut, WarehouseItemUpdate
from app.services import add_audit_log

router = APIRouter(prefix="/warehouse", tags=["Warehouse"])


def get_item_or_404(db: DbSession, item_id: int) -> WarehouseItem:
    item = db.query(WarehouseItem).filter(WarehouseItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Warehouse item not found")
    return item


@router.get("", response_model=list[WarehouseItemOut])
def list_warehouse_items(
    _: CurrentUser,
    db: DbSession,
    search: str | None = Query(default=None),
    include_inactive: bool = Query(default=True),
) -> list[WarehouseItem]:
    query = db.query(WarehouseItem)
    if search:
        term = f"%{search.strip()}%"
        query = query.filter(
            (WarehouseItem.name.ilike(term))
            | (WarehouseItem.sku.ilike(term))
            | (WarehouseItem.location.ilike(term))
        )
    if not include_inactive:
        query = query.filter(WarehouseItem.is_active.is_(True))
    return query.order_by(WarehouseItem.name).all()


@router.post("", response_model=WarehouseItemOut, status_code=status.HTTP_201_CREATED)
def create_warehouse_item(
    payload: WarehouseItemCreate, current_user: CurrentUser, db: DbSession
) -> WarehouseItem:
    sku = payload.sku.strip() if payload.sku else None
    if sku and db.query(WarehouseItem).filter(WarehouseItem.sku == sku).first():
        raise HTTPException(status_code=409, detail="A warehouse item with this SKU already exists")
    item = WarehouseItem(
        name=payload.name.strip(),
        sku=sku,
        quantity=payload.quantity,
        unit=payload.unit.strip(),
        location=payload.location.strip() if payload.location else None,
        notes=payload.notes,
        is_active=payload.is_active,
    )
    db.add(item)
    db.flush()
    add_audit_log(
        db,
        actor_user_id=current_user.id,
        action="WAREHOUSE_ITEM_CREATED",
        entity_type="warehouse_item",
        entity_id=item.id,
        new_value={"name": item.name, "quantity": str(item.quantity)},
    )
    db.commit()
    db.refresh(item)
    return item


@router.get("/{item_id}", response_model=WarehouseItemOut)
def get_warehouse_item(item_id: int, _: CurrentUser, db: DbSession) -> WarehouseItem:
    return get_item_or_404(db, item_id)


@router.patch("/{item_id}", response_model=WarehouseItemOut)
def update_warehouse_item(
    item_id: int, payload: WarehouseItemUpdate, current_user: CurrentUser, db: DbSession
) -> WarehouseItem:
    item = get_item_or_404(db, item_id)
    values = payload.model_dump(exclude_unset=True)
    if "name" in values and values["name"]:
        values["name"] = values["name"].strip()
    if "unit" in values and values["unit"]:
        values["unit"] = values["unit"].strip()
    if "location" in values and values["location"]:
        values["location"] = values["location"].strip()
    if "sku" in values:
        sku = values["sku"].strip() if values["sku"] else None
        if sku:
            duplicate = (
                db.query(WarehouseItem)
                .filter(WarehouseItem.sku == sku, WarehouseItem.id != item_id)
                .first()
            )
            if duplicate:
                raise HTTPException(status_code=409, detail="A warehouse item with this SKU already exists")
        values["sku"] = sku
    old_value = {"name": item.name, "quantity": str(item.quantity), "is_active": item.is_active}
    for field, value in values.items():
        setattr(item, field, value)
    add_audit_log(
        db,
        actor_user_id=current_user.id,
        action="WAREHOUSE_ITEM_UPDATED",
        entity_type="warehouse_item",
        entity_id=item.id,
        old_value=old_value,
        new_value={key: str(value) if isinstance(value, Decimal) else value for key, value in values.items()},
    )
    db.commit()
    db.refresh(item)
    return item


@router.delete("/{item_id}", response_model=Message)
def deactivate_warehouse_item(
    item_id: int, current_user: CurrentUser, db: DbSession
) -> Message:
    item = get_item_or_404(db, item_id)
    item.is_active = False
    add_audit_log(
        db,
        actor_user_id=current_user.id,
        action="WAREHOUSE_ITEM_DEACTIVATED",
        entity_type="warehouse_item",
        entity_id=item.id,
    )
    db.commit()
    return Message(message="Warehouse item deactivated")
