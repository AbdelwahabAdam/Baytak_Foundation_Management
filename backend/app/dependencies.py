from collections.abc import Callable
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jwt import ExpiredSignatureError, InvalidTokenError
from sqlalchemy.orm import Session, selectinload

from app.db import get_db
from app.models import User
from app.security import decode_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")
DbSession = Annotated[Session, Depends(get_db)]


def get_current_user(
    db: DbSession, token: Annotated[str, Depends(oauth2_scheme)]
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_token(token)
        if payload.get("type") != "access":
            raise credentials_exception
        user_id = int(payload.get("sub", ""))
    except (ValueError, ExpiredSignatureError, InvalidTokenError):
        raise credentials_exception
    user = (
        db.query(User)
        .options(selectinload(User.roles))
        .filter(User.id == user_id)
        .first()
    )
    if not user or not user.is_active:
        raise credentials_exception
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


def require_roles(*allowed_roles: str) -> Callable:
    def role_checker(current_user: CurrentUser) -> User:
        user_roles = {role.name for role in current_user.roles}
        if not user_roles.intersection(allowed_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to perform this action",
            )
        return current_user

    return role_checker


AdminUser = Annotated[User, Depends(require_roles("admin"))]
FinanceOrAdminUser = Annotated[User, Depends(require_roles("admin", "finance"))]
FinanceStaffOrAdmin = Annotated[User, Depends(require_roles("admin", "finance", "staff"))]
