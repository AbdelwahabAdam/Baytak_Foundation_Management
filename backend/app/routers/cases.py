from fastapi import APIRouter, HTTPException, Query, status

from app.dependencies import CurrentUser, DbSession
from app.models import AidCase, CasePriority, CaseStatus, User
from app.schemas import AidCaseCreate, AidCaseOut, AidCaseUpdate, Message
from app.services import add_audit_log

router = APIRouter(prefix="/cases", tags=["Cases"])


def get_case_or_404(db: DbSession, case_id: int) -> AidCase:
    item = db.query(AidCase).filter(AidCase.id == case_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Case not found")
    return item


def next_case_number(db: DbSession) -> str:
    count = db.query(AidCase).count() + 1
    return f"CASE-{count:05d}"


@router.get("", response_model=dict)
def list_cases(
    _: CurrentUser,
    db: DbSession,
    search: str | None = Query(default=None),
    case_status: CaseStatus | None = Query(default=None, alias="status"),
    priority: CasePriority | None = Query(default=None),
    category: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
) -> dict:
    query = db.query(AidCase)
    if search:
        term = f"%{search.strip()}%"
        query = query.filter(
            (AidCase.beneficiary_name.ilike(term))
            | (AidCase.case_number.ilike(term))
            | (AidCase.phone.ilike(term))
            | (AidCase.category.ilike(term))
        )
    if case_status:
        query = query.filter(AidCase.status == case_status)
    if priority:
        query = query.filter(AidCase.priority == priority)
    if category:
        query = query.filter(AidCase.category.ilike(f"%{category.strip()}%"))
    total = query.count()
    items = (
        query.order_by(AidCase.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return {"items": items, "total": total, "page": page, "page_size": page_size}


@router.post("", response_model=AidCaseOut, status_code=status.HTTP_201_CREATED)
def create_case(payload: AidCaseCreate, current_user: CurrentUser, db: DbSession) -> AidCase:
    case_number = (payload.case_number or "").strip() or next_case_number(db)
    if db.query(AidCase).filter(AidCase.case_number == case_number).first():
        raise HTTPException(status_code=409, detail="A case with this number already exists")
    if payload.assigned_user_id:
        assignee = db.query(User).filter(User.id == payload.assigned_user_id, User.is_active.is_(True)).first()
        if not assignee:
            raise HTTPException(status_code=400, detail="Assigned user is not available")
    item = AidCase(
        case_number=case_number,
        beneficiary_name=payload.beneficiary_name.strip(),
        phone=payload.phone.strip() if payload.phone else None,
        category=payload.category.strip(),
        status=payload.status,
        priority=payload.priority,
        description=payload.description,
        requested_amount=payload.requested_amount,
        approved_amount=payload.approved_amount,
        created_by_user_id=current_user.id,
        assigned_user_id=payload.assigned_user_id,
    )
    db.add(item)
    db.flush()
    add_audit_log(
        db,
        actor_user_id=current_user.id,
        action="CASE_CREATED",
        entity_type="aid_case",
        entity_id=item.id,
        new_value={
            "case_number": item.case_number,
            "beneficiary_name": item.beneficiary_name,
            "status": item.status.value,
        },
    )
    db.commit()
    db.refresh(item)
    return item


@router.get("/{case_id}", response_model=AidCaseOut)
def get_case(case_id: int, _: CurrentUser, db: DbSession) -> AidCase:
    return get_case_or_404(db, case_id)


@router.patch("/{case_id}", response_model=AidCaseOut)
def update_case(
    case_id: int, payload: AidCaseUpdate, current_user: CurrentUser, db: DbSession
) -> AidCase:
    item = get_case_or_404(db, case_id)
    values = payload.model_dump(exclude_unset=True)
    if "case_number" in values and values["case_number"]:
        values["case_number"] = values["case_number"].strip()
        duplicate = (
            db.query(AidCase)
            .filter(AidCase.case_number == values["case_number"], AidCase.id != case_id)
            .first()
        )
        if duplicate:
            raise HTTPException(status_code=409, detail="A case with this number already exists")
    if "beneficiary_name" in values and values["beneficiary_name"]:
        values["beneficiary_name"] = values["beneficiary_name"].strip()
    if "category" in values and values["category"]:
        values["category"] = values["category"].strip()
    if "phone" in values and values["phone"]:
        values["phone"] = values["phone"].strip()
    if "assigned_user_id" in values and values["assigned_user_id"]:
        assignee = (
            db.query(User)
            .filter(User.id == values["assigned_user_id"], User.is_active.is_(True))
            .first()
        )
        if not assignee:
            raise HTTPException(status_code=400, detail="Assigned user is not available")
    old_value = {
        "status": item.status.value,
        "priority": item.priority.value,
        "beneficiary_name": item.beneficiary_name,
    }
    for field, value in values.items():
        setattr(item, field, value)
    add_audit_log(
        db,
        actor_user_id=current_user.id,
        action="CASE_UPDATED",
        entity_type="aid_case",
        entity_id=item.id,
        old_value=old_value,
        new_value={key: getattr(value, "value", value) for key, value in values.items()},
    )
    db.commit()
    db.refresh(item)
    return item


@router.delete("/{case_id}", response_model=Message)
def cancel_case(case_id: int, current_user: CurrentUser, db: DbSession) -> Message:
    item = get_case_or_404(db, case_id)
    if item.status == CaseStatus.cancelled:
        raise HTTPException(status_code=400, detail="Case is already cancelled")
    previous = item.status.value
    item.status = CaseStatus.cancelled
    add_audit_log(
        db,
        actor_user_id=current_user.id,
        action="CASE_CANCELLED",
        entity_type="aid_case",
        entity_id=item.id,
        old_value={"status": previous},
        new_value={"status": CaseStatus.cancelled.value},
    )
    db.commit()
    return Message(message="Case cancelled")
