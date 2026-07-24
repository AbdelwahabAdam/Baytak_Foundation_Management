from datetime import datetime

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy.orm import selectinload

from app.dependencies import AdminUser, CurrentUser, DbSession
from app.models import Task, TaskStatus, User
from app.schemas import Message, TaskCreate, TaskOut, TaskStatusUpdate, TaskUpdate
from app.services import add_audit_log

router = APIRouter(prefix="/tasks", tags=["Tasks"])


def _is_admin(user: User) -> bool:
    return any(role.name == "admin" for role in user.roles)


def get_task_or_404(db: DbSession, task_id: int) -> Task:
    item = (
        db.query(Task)
        .options(
            selectinload(Task.assigned_user),
            selectinload(Task.created_by),
        )
        .filter(Task.id == task_id)
        .first()
    )
    if not item:
        raise HTTPException(status_code=404, detail="Task not found")
    return item


def serialize_task(item: Task) -> TaskOut:
    return TaskOut.model_validate(item)


@router.get("", response_model=dict)
def list_tasks(
    current_user: CurrentUser,
    db: DbSession,
    assigned_user_id: int | None = Query(default=None),
    task_status: TaskStatus | None = Query(default=None, alias="status"),
    search: str | None = Query(default=None),
    start_date: datetime | None = Query(default=None),
    end_date: datetime | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
) -> dict:
    query = db.query(Task).options(
        selectinload(Task.assigned_user),
        selectinload(Task.created_by),
    )
    if not _is_admin(current_user):
        query = query.filter(Task.assigned_user_id == current_user.id)
    elif assigned_user_id:
        query = query.filter(Task.assigned_user_id == assigned_user_id)
    if task_status:
        query = query.filter(Task.status == task_status)
    if search:
        term = f"%{search.strip()}%"
        query = query.filter((Task.title.ilike(term)) | (Task.description.ilike(term)))
    if start_date:
        query = query.filter(Task.created_at >= start_date)
    if end_date:
        query = query.filter(Task.created_at <= end_date)
    total = query.count()
    items = (
        query.order_by(Task.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return {
        "items": [serialize_task(item) for item in items],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.post("", response_model=TaskOut, status_code=status.HTTP_201_CREATED)
def create_task(payload: TaskCreate, current_user: AdminUser, db: DbSession) -> TaskOut:
    assignee = (
        db.query(User)
        .filter(User.id == payload.assigned_user_id, User.is_active.is_(True))
        .first()
    )
    if not assignee:
        raise HTTPException(status_code=400, detail="Assigned user is not available")
    item = Task(
        title=payload.title.strip(),
        description=payload.description.strip() if payload.description else None,
        status=payload.status,
        priority=payload.priority,
        due_date=payload.due_date,
        assigned_user_id=payload.assigned_user_id,
        created_by_user_id=current_user.id,
    )
    db.add(item)
    db.flush()
    add_audit_log(
        db,
        actor_user_id=current_user.id,
        action="TASK_CREATED",
        entity_type="task",
        entity_id=item.id,
        new_value={
            "title": item.title,
            "assigned_user_id": item.assigned_user_id,
            "status": item.status.value,
        },
    )
    db.commit()
    return serialize_task(get_task_or_404(db, item.id))


@router.get("/{task_id}", response_model=TaskOut)
def get_task(task_id: int, current_user: CurrentUser, db: DbSession) -> TaskOut:
    item = get_task_or_404(db, task_id)
    if not _is_admin(current_user) and item.assigned_user_id != current_user.id:
        raise HTTPException(status_code=403, detail="You do not have access to this task")
    return serialize_task(item)


@router.patch("/{task_id}", response_model=TaskOut)
def update_task(
    task_id: int, payload: TaskUpdate, current_user: AdminUser, db: DbSession
) -> TaskOut:
    item = get_task_or_404(db, task_id)
    values = payload.model_dump(exclude_unset=True)
    if "title" in values and values["title"]:
        values["title"] = values["title"].strip()
    if "description" in values and values["description"]:
        values["description"] = values["description"].strip()
    if "assigned_user_id" in values and values["assigned_user_id"]:
        assignee = (
            db.query(User)
            .filter(User.id == values["assigned_user_id"], User.is_active.is_(True))
            .first()
        )
        if not assignee:
            raise HTTPException(status_code=400, detail="Assigned user is not available")
    old_value = {
        "title": item.title,
        "status": item.status.value,
        "assigned_user_id": item.assigned_user_id,
    }
    for field, value in values.items():
        setattr(item, field, value)
    add_audit_log(
        db,
        actor_user_id=current_user.id,
        action="TASK_UPDATED",
        entity_type="task",
        entity_id=item.id,
        old_value=old_value,
        new_value={key: getattr(value, "value", value) for key, value in values.items()},
    )
    db.commit()
    return serialize_task(get_task_or_404(db, item.id))


@router.patch("/{task_id}/status", response_model=TaskOut)
def update_task_status(
    task_id: int, payload: TaskStatusUpdate, current_user: CurrentUser, db: DbSession
) -> TaskOut:
    item = get_task_or_404(db, task_id)
    if not _is_admin(current_user) and item.assigned_user_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="Only the assigned user or an admin can update task status",
        )
    previous = item.status.value
    item.status = payload.status
    add_audit_log(
        db,
        actor_user_id=current_user.id,
        action="TASK_STATUS_UPDATED",
        entity_type="task",
        entity_id=item.id,
        old_value={"status": previous},
        new_value={"status": payload.status.value},
    )
    db.commit()
    return serialize_task(get_task_or_404(db, item.id))


@router.delete("/{task_id}", response_model=Message)
def cancel_task(task_id: int, current_user: AdminUser, db: DbSession) -> Message:
    item = get_task_or_404(db, task_id)
    if item.status == TaskStatus.cancelled:
        raise HTTPException(status_code=400, detail="Task is already cancelled")
    previous = item.status.value
    item.status = TaskStatus.cancelled
    add_audit_log(
        db,
        actor_user_id=current_user.id,
        action="TASK_CANCELLED",
        entity_type="task",
        entity_id=item.id,
        old_value={"status": previous},
        new_value={"status": TaskStatus.cancelled.value},
    )
    db.commit()
    return Message(message="Task cancelled")
