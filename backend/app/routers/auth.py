from datetime import datetime, timedelta, timezone
import smtplib
from urllib.parse import urlencode

from fastapi import APIRouter, HTTPException, status
from jwt import ExpiredSignatureError, InvalidTokenError
from sqlalchemy.orm import selectinload

from app.config import get_settings
from app.dependencies import CurrentUser, DbSession
from app.emailing import send_password_reset_email
from app.models import PasswordResetToken, RefreshToken, User
from app.schemas import (
    LoginRequest,
    Message,
    PasswordChange,
    PasswordResetConfirm,
    PasswordResetRequest,
    RefreshRequest,
    TokenPair,
)
from app.security import create_token, decode_token, verify_password, hash_password
from app.services import add_audit_log

router = APIRouter(prefix="/auth", tags=["Authentication"])


def is_expired(expires_at: datetime) -> bool:
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    return expires_at <= datetime.now(timezone.utc)


def issue_token_pair(db: DbSession, user: User) -> TokenPair:
    settings = get_settings()
    access_token, _, _ = create_token(
        user, "access", timedelta(minutes=settings.access_token_minutes)
    )
    refresh_token, token_jti, expires_at = create_token(
        user, "refresh", timedelta(days=settings.refresh_token_days)
    )
    db.add(
        RefreshToken(token_jti=token_jti, user_id=user.id, expires_at=expires_at)
    )
    return TokenPair(access_token=access_token, refresh_token=refresh_token)


@router.post("/login", response_model=TokenPair)
def login(payload: LoginRequest, db: DbSession) -> TokenPair:
    user = (
        db.query(User)
        .options(selectinload(User.roles))
        .filter(User.email == payload.email.lower())
        .first()
    )
    if not user or not user.is_active or not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )
    tokens = issue_token_pair(db, user)
    add_audit_log(
        db,
        actor_user_id=user.id,
        action="USER_LOGGED_IN",
        entity_type="user",
        entity_id=user.id,
    )
    db.commit()
    return tokens


@router.post("/refresh", response_model=TokenPair)
def refresh(payload: RefreshRequest, db: DbSession) -> TokenPair:
    try:
        claims = decode_token(payload.refresh_token)
        if claims.get("type") != "refresh":
            raise ValueError
        token_jti = claims["jti"]
        user_id = int(claims["sub"])
    except (ValueError, KeyError, ExpiredSignatureError, InvalidTokenError):
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")

    record = db.query(RefreshToken).filter(RefreshToken.token_jti == token_jti).first()
    user = (
        db.query(User)
        .options(selectinload(User.roles))
        .filter(User.id == user_id)
        .first()
    )
    if (
        not record
        or record.revoked_at
        or is_expired(record.expires_at)
        or not user
        or not user.is_active
    ):
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")

    record.revoked_at = datetime.now(timezone.utc)
    tokens = issue_token_pair(db, user)
    db.commit()
    return tokens


@router.post("/logout", response_model=Message)
def logout(payload: RefreshRequest, current_user: CurrentUser, db: DbSession) -> Message:
    try:
        claims = decode_token(payload.refresh_token)
        if claims.get("type") != "refresh" or int(claims["sub"]) != current_user.id:
            raise ValueError
        token_jti = claims["jti"]
    except (ValueError, KeyError, ExpiredSignatureError, InvalidTokenError):
        raise HTTPException(status_code=400, detail="Invalid refresh token")

    record = db.query(RefreshToken).filter(RefreshToken.token_jti == token_jti).first()
    if record:
        record.revoked_at = datetime.now(timezone.utc)
    add_audit_log(
        db,
        actor_user_id=current_user.id,
        action="USER_LOGGED_OUT",
        entity_type="user",
        entity_id=current_user.id,
    )
    db.commit()
    return Message(message="Logged out successfully")


@router.post("/forgot-password", response_model=Message)
def request_password_reset(payload: PasswordResetRequest, db: DbSession) -> Message:
    confirmation = "If an active account uses that email, a password reset link has been sent."
    user = (
        db.query(User)
        .options(selectinload(User.roles))
        .filter(User.email == payload.email.lower(), User.is_active.is_(True))
        .first()
    )
    if not user:
        return Message(message=confirmation)

    settings = get_settings()
    token, token_jti, expires_at = create_token(
        user,
        "password_reset",
        timedelta(minutes=settings.password_reset_minutes),
    )
    now = datetime.now(timezone.utc)
    db.query(PasswordResetToken).filter(
        PasswordResetToken.user_id == user.id,
        PasswordResetToken.used_at.is_(None),
    ).update({"used_at": now})
    db.add(
        PasswordResetToken(
            token_jti=token_jti,
            user_id=user.id,
            expires_at=expires_at,
        )
    )
    add_audit_log(
        db,
        actor_user_id=user.id,
        action="PASSWORD_RESET_REQUESTED",
        entity_type="user",
        entity_id=user.id,
    )
    db.commit()

    reset_url = (
        f"{settings.frontend_app_url.rstrip('/')}/reset-password?"
        f"{urlencode({'token': token})}"
    )
    try:
        send_password_reset_email(
            recipient=user.email,
            recipient_name=user.full_name,
            reset_url=reset_url,
        )
    except (OSError, RuntimeError, smtplib.SMTPException) as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Password reset email could not be sent. Check the SMTP configuration.",
        ) from error
    return Message(message=confirmation)


@router.post("/reset-password", response_model=Message)
def reset_password(payload: PasswordResetConfirm, db: DbSession) -> Message:
    try:
        claims = decode_token(payload.token)
        if claims.get("type") != "password_reset":
            raise ValueError
        token_jti = claims["jti"]
        user_id = int(claims["sub"])
    except (ValueError, KeyError, ExpiredSignatureError, InvalidTokenError):
        raise HTTPException(status_code=400, detail="This password reset link is invalid or expired")

    now = datetime.now(timezone.utc)
    token_record = db.query(PasswordResetToken).filter(
        PasswordResetToken.token_jti == token_jti,
        PasswordResetToken.user_id == user_id,
    ).first()
    user = db.query(User).filter(User.id == user_id, User.is_active.is_(True)).first()
    if (
        not token_record
        or token_record.used_at
        or is_expired(token_record.expires_at)
        or not user
    ):
        raise HTTPException(status_code=400, detail="This password reset link is invalid or expired")

    user.password_hash = hash_password(payload.new_password)
    token_record.used_at = now
    db.query(PasswordResetToken).filter(
        PasswordResetToken.user_id == user.id,
        PasswordResetToken.used_at.is_(None),
    ).update({"used_at": now})
    db.query(RefreshToken).filter(
        RefreshToken.user_id == user.id,
        RefreshToken.revoked_at.is_(None),
    ).update({"revoked_at": now})
    add_audit_log(
        db,
        actor_user_id=user.id,
        action="PASSWORD_RESET_COMPLETED",
        entity_type="user",
        entity_id=user.id,
    )
    db.commit()
    return Message(message="Password updated. Please sign in with your new password.")


@router.post("/change-password", response_model=Message)
def change_password(
    payload: PasswordChange, current_user: CurrentUser, db: DbSession
) -> Message:
    if not verify_password(payload.current_password, current_user.password_hash):
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    current_user.password_hash = hash_password(payload.new_password)
    now = datetime.now(timezone.utc)
    db.query(RefreshToken).filter(
        RefreshToken.user_id == current_user.id, RefreshToken.revoked_at.is_(None)
    ).update({"revoked_at": now})
    db.query(PasswordResetToken).filter(
        PasswordResetToken.user_id == current_user.id,
        PasswordResetToken.used_at.is_(None),
    ).update({"used_at": now})
    add_audit_log(
        db,
        actor_user_id=current_user.id,
        action="PASSWORD_CHANGED",
        entity_type="user",
        entity_id=current_user.id,
    )
    db.commit()
    return Message(message="Password changed. Please sign in again.")
