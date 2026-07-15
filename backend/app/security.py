from datetime import datetime, timedelta, timezone
from uuid import uuid4

import jwt
from pwdlib import PasswordHash

from app.config import get_settings
from app.models import User

password_hash = PasswordHash.recommended()


def hash_password(password: str) -> str:
    return password_hash.hash(password)


def verify_password(password: str, hashed_password: str) -> bool:
    return password_hash.verify(password, hashed_password)


def create_token(user: User, token_type: str, expires_delta: timedelta) -> tuple[str, str, datetime]:
    settings = get_settings()
    expires_at = datetime.now(timezone.utc) + expires_delta
    jti = str(uuid4())
    payload = {
        "sub": str(user.id),
        "email": user.email,
        "roles": [role.name for role in user.roles],
        "type": token_type,
        "jti": jti,
        "exp": expires_at,
    }
    return (
        jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm),
        jti,
        expires_at,
    )


def decode_token(token: str) -> dict:
    settings = get_settings()
    return jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
