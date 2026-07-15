from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy.orm import selectinload

from app.dependencies import AdminUser, CurrentUser, DbSession
from app.models import RefreshToken, Role, User
from app.schemas import (
    Message,
    ProfileUpdate,
    RoleOut,
    UserCreate,
    UserOut,
    UserUpdate,
)
from app.security import hash_password
from app.services import add_audit_log

users_router = APIRouter(prefix="/users", tags=["Users"])
profile_router = APIRouter(prefix="/profile", tags=["Profile"])


def get_user_or_404(db: DbSession, user_id: int) -> User:
    user = (
        db.query(User)
        .options(selectinload(User.roles))
        .filter(User.id == user_id)
        .first()
    )
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@profile_router.get("", response_model=UserOut)
def get_profile(current_user: CurrentUser) -> User:
    return current_user


@profile_router.patch("", response_model=UserOut)
def update_profile(
    payload: ProfileUpdate, current_user: CurrentUser, db: DbSession
) -> User:
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(current_user, field, value)
    add_audit_log(
        db,
        actor_user_id=current_user.id,
        action="PROFILE_UPDATED",
        entity_type="user",
        entity_id=current_user.id,
    )
    db.commit()
    db.refresh(current_user)
    return current_user


@users_router.get("", response_model=list[UserOut])
def list_users(
    _: AdminUser,
    db: DbSession,
    search: str | None = Query(default=None),
    active_only: bool = Query(default=False),
) -> list[User]:
    query = db.query(User).options(selectinload(User.roles))
    if search:
        like = f"%{search.strip()}%"
        query = query.filter(
            User.first_name.ilike(like)
            | User.last_name.ilike(like)
            | User.email.ilike(like)
        )
    if active_only:
        query = query.filter(User.is_active.is_(True))
    return query.order_by(User.first_name, User.last_name).all()


@users_router.post("", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def create_user(payload: UserCreate, admin: AdminUser, db: DbSession) -> User:
    if db.query(User).filter(User.email == payload.email.lower()).first():
        raise HTTPException(status_code=409, detail="A user with this email already exists")
    roles = db.query(Role).filter(Role.id.in_(payload.role_ids)).all() if payload.role_ids else []
    if len(roles) != len(set(payload.role_ids)):
        raise HTTPException(status_code=400, detail="One or more roles do not exist")
    user = User(
        **payload.model_dump(exclude={"password", "role_ids", "email"}),
        email=payload.email.lower(),
        password_hash=hash_password(payload.password),
        roles=roles,
    )
    db.add(user)
    db.flush()
    add_audit_log(
        db,
        actor_user_id=admin.id,
        action="USER_CREATED",
        entity_type="user",
        entity_id=user.id,
        new_value={"email": user.email, "roles": [role.name for role in roles]},
    )
    db.commit()
    db.refresh(user)
    return user


@users_router.get("/roles", response_model=list[RoleOut])
def list_roles(_: AdminUser, db: DbSession) -> list[Role]:
    return db.query(Role).order_by(Role.name).all()


@users_router.get("/{user_id}", response_model=UserOut)
def get_user(user_id: int, _: AdminUser, db: DbSession) -> User:
    return get_user_or_404(db, user_id)


@users_router.patch("/{user_id}", response_model=UserOut)
def update_user(
    user_id: int, payload: UserUpdate, admin: AdminUser, db: DbSession
) -> User:
    user = get_user_or_404(db, user_id)
    values = payload.model_dump(exclude_unset=True)
    if "email" in values and values["email"]:
        values["email"] = values["email"].lower()
        duplicate = db.query(User).filter(User.email == values["email"], User.id != user_id).first()
        if duplicate:
            raise HTTPException(status_code=409, detail="A user with this email already exists")
    for field, value in values.items():
        setattr(user, field, value)
    add_audit_log(
        db,
        actor_user_id=admin.id,
        action="USER_UPDATED",
        entity_type="user",
        entity_id=user.id,
        new_value=values,
    )
    db.commit()
    db.refresh(user)
    return user


@users_router.post("/{user_id}/roles", response_model=UserOut)
def assign_roles(
    user_id: int, role_ids: list[int], admin: AdminUser, db: DbSession
) -> User:
    user = get_user_or_404(db, user_id)
    roles = db.query(Role).filter(Role.id.in_(role_ids)).all()
    if len(roles) != len(set(role_ids)):
        raise HTTPException(status_code=400, detail="One or more roles do not exist")
    user.roles = roles
    add_audit_log(
        db,
        actor_user_id=admin.id,
        action="USER_ROLES_UPDATED",
        entity_type="user",
        entity_id=user.id,
        new_value={"roles": [role.name for role in roles]},
    )
    db.commit()
    db.refresh(user)
    return user


@users_router.delete("/{user_id}/roles/{role_id}", response_model=UserOut)
def remove_role(user_id: int, role_id: int, admin: AdminUser, db: DbSession) -> User:
    user = get_user_or_404(db, user_id)
    role = next((item for item in user.roles if item.id == role_id), None)
    if not role:
        raise HTTPException(status_code=404, detail="Role is not assigned to this user")
    if role.name == "admin" and user.id == admin.id:
        raise HTTPException(status_code=400, detail="You cannot remove your own admin role")
    user.roles.remove(role)
    add_audit_log(
        db,
        actor_user_id=admin.id,
        action="USER_ROLE_REMOVED",
        entity_type="user",
        entity_id=user.id,
        new_value={"role": role.name},
    )
    db.commit()
    db.refresh(user)
    return user


@users_router.post("/{user_id}/disable", response_model=Message)
def disable_user(user_id: int, admin: AdminUser, db: DbSession) -> Message:
    user = get_user_or_404(db, user_id)
    if user.id == admin.id:
        raise HTTPException(status_code=400, detail="You cannot disable your own account")
    user.is_active = False
    db.query(RefreshToken).filter(
        RefreshToken.user_id == user.id, RefreshToken.revoked_at.is_(None)
    ).update({"revoked_at": datetime.now(timezone.utc)})
    add_audit_log(
        db,
        actor_user_id=admin.id,
        action="USER_DISABLED",
        entity_type="user",
        entity_id=user.id,
    )
    db.commit()
    return Message(message="User disabled")


@users_router.post("/{user_id}/reset-password", response_model=Message)
def reset_password(
    user_id: int, new_password: str = Query(min_length=8), admin: AdminUser = None, db: DbSession = None
) -> Message:
    user = get_user_or_404(db, user_id)
    user.password_hash = hash_password(new_password)
    db.query(RefreshToken).filter(
        RefreshToken.user_id == user.id, RefreshToken.revoked_at.is_(None)
    ).update({"revoked_at": datetime.now(timezone.utc)})
    add_audit_log(
        db,
        actor_user_id=admin.id,
        action="PASSWORD_RESET_BY_ADMIN",
        entity_type="user",
        entity_id=user.id,
    )
    db.commit()
    return Message(message="Password reset successfully")
