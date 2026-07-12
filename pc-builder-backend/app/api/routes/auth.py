from __future__ import annotations

import hashlib
import logging
from datetime import UTC, datetime, timedelta
from uuid import UUID

from fastapi import APIRouter, HTTPException, Request, status
from sqlalchemy import delete, select, update

from app.api.deps import CurrentAuth, CurrentUser, DbSession
from app.core.config import settings
from app.core.security import (
    DUMMY_HASH,
    create_access_token,
    generate_opaque_token,
    hash_password,
    token_hash,
    verify_password,
)
from app.models.entities import AuthSession, OneTimeToken, RefreshTokenHistory, User
from app.schemas.auth import (
    ChangePasswordRequest,
    LoginRequest,
    LogoutRequest,
    OneTimeTokenDebugResponse,
    PasswordResetConfirm,
    PasswordResetRequest,
    RefreshRequest,
    RegisterRequest,
    SessionOut,
    TokenResponse,
    UpdateProfileRequest,
    UserOut,
    VerifyEmailRequest,
)
from app.schemas.common import MessageResponse
from app.services.audit import audit
from app.services.cache import cache
from app.services.email import email_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])


def aware(value: datetime) -> datetime:
    return value if value.tzinfo else value.replace(tzinfo=UTC)


async def send_email_safely(operation: str, call) -> None:
    try:
        await call
    except Exception:
        logger.exception("email_delivery_failed operation=%s", operation)


def user_out(user: User) -> UserOut:
    return UserOut(
        id=user.id,
        email=user.email,
        display_name=user.display_name,
        role=user.role,
        is_active=user.is_active,
        is_verified=user.is_verified,
        created_at=user.created_at,
    )


async def issue_token_pair(session: DbSession, user: User, request: Request) -> TokenResponse:
    refresh_token = generate_opaque_token()
    auth_session = AuthSession(
        user_id=user.id,
        refresh_token_hash=token_hash(refresh_token),
        user_agent=request.headers.get("user-agent", "")[:500] or None,
        ip_address=request.client.host if request.client else None,
        expires_at=datetime.now(UTC) + timedelta(days=settings.refresh_token_expire_days),
    )
    session.add(auth_session)
    await session.flush()
    access_token, expires_at = create_access_token(user.id, auth_session.id, user.role)
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_at=expires_at,
    )


async def create_one_time_token(
    session: DbSession,
    user: User,
    purpose: str,
    expires_at: datetime,
) -> str:
    await session.execute(
        update(OneTimeToken)
        .where(
            OneTimeToken.user_id == user.id,
            OneTimeToken.purpose == purpose,
            OneTimeToken.used_at.is_(None),
        )
        .values(used_at=datetime.now(UTC))
    )
    raw = generate_opaque_token(40)
    session.add(
        OneTimeToken(
            user_id=user.id,
            purpose=purpose,
            token_hash=token_hash(raw),
            expires_at=expires_at,
        )
    )
    return raw


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(payload: RegisterRequest, session: DbSession, request: Request) -> TokenResponse:
    email = payload.email.lower().strip()
    if await session.scalar(select(User).where(User.email == email)):
        raise HTTPException(status_code=409, detail="Пользователь с таким email уже существует")
    user = User(
        email=email,
        display_name=payload.display_name.strip(),
        password_hash=hash_password(payload.password),
    )
    session.add(user)
    await session.flush()
    verification_token = await create_one_time_token(
        session,
        user,
        "verify_email",
        datetime.now(UTC) + timedelta(hours=settings.email_verify_expire_hours),
    )
    response = await issue_token_pair(session, user, request)
    await audit(session, request, "auth.register", "user", user.id, user_id=user.id)
    await session.commit()
    await send_email_safely(
        "verification", email_service.send_verification(user.email, verification_token)
    )
    return response


@router.post("/login", response_model=TokenResponse)
async def login(payload: LoginRequest, session: DbSession, request: Request) -> TokenResponse:
    email_fingerprint = hashlib.sha256(payload.email.lower().strip().encode()).hexdigest()
    identity = f"login:{request.client.host if request.client else 'unknown'}:{email_fingerprint}"
    attempts = await cache.increment_window(identity, 900)
    if attempts > settings.login_attempts_per_15_minutes:
        raise HTTPException(status_code=429, detail="Слишком много попыток входа")
    user = await session.scalar(select(User).where(User.email == payload.email.lower().strip()))
    if user is None:
        verify_password(payload.password, DUMMY_HASH)
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Неверный email или пароль")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Аккаунт отключён")
    user.last_login_at = datetime.now(UTC)
    await cache.delete(identity)
    response = await issue_token_pair(session, user, request)
    await audit(session, request, "auth.login", "user", user.id, user_id=user.id)
    await session.commit()
    return response


@router.post("/refresh", response_model=TokenResponse)
async def refresh(payload: RefreshRequest, session: DbSession, request: Request) -> TokenResponse:
    hashed = token_hash(payload.refresh_token)
    result = await session.execute(
        select(AuthSession, User)
        .join(User, User.id == AuthSession.user_id)
        .where(AuthSession.refresh_token_hash == hashed)
    )
    row = result.one_or_none()
    if row is None:
        reused = await session.scalar(
            select(RefreshTokenHistory).where(RefreshTokenHistory.token_hash == hashed)
        )
        if reused is not None:
            await session.execute(
                update(AuthSession)
                .where(AuthSession.user_id == reused.user_id)
                .values(revoked_at=datetime.now(UTC))
            )
            await session.commit()
            raise HTTPException(
                status_code=401,
                detail="Обнаружено повторное использование refresh token; все сессии завершены",
            )
        raise HTTPException(status_code=401, detail="Недействительный refresh token")
    auth_session, user = row
    if (
        auth_session.revoked_at
        or aware(auth_session.expires_at) <= datetime.now(UTC)
        or not user.is_active
    ):
        raise HTTPException(status_code=401, detail="Сессия завершена")

    new_refresh = generate_opaque_token()
    session.add(
        RefreshTokenHistory(
            session_id=auth_session.id,
            user_id=user.id,
            token_hash=auth_session.refresh_token_hash,
        )
    )
    auth_session.refresh_token_hash = token_hash(new_refresh)
    auth_session.last_used_at = datetime.now(UTC)
    auth_session.expires_at = datetime.now(UTC) + timedelta(days=settings.refresh_token_expire_days)
    auth_session.user_agent = request.headers.get("user-agent", "")[:500] or auth_session.user_agent
    auth_session.ip_address = request.client.host if request.client else auth_session.ip_address
    access, expires = create_access_token(user.id, auth_session.id, user.role)
    await session.commit()
    return TokenResponse(access_token=access, refresh_token=new_refresh, expires_at=expires)


@router.post("/logout", response_model=MessageResponse)
async def logout(
    payload: LogoutRequest, session: DbSession, request: Request, auth: CurrentAuth
) -> MessageResponse:
    now = datetime.now(UTC)
    if payload.all_sessions:
        await session.execute(
            update(AuthSession).where(AuthSession.user_id == auth.user.id).values(revoked_at=now)
        )
    elif payload.refresh_token:
        await session.execute(
            update(AuthSession)
            .where(
                AuthSession.user_id == auth.user.id,
                AuthSession.refresh_token_hash == token_hash(payload.refresh_token),
            )
            .values(revoked_at=now)
        )
    else:
        auth.auth_session.revoked_at = now
    await audit(
        session, request, "auth.logout", "session", auth.auth_session.id, user_id=auth.user.id
    )
    await session.commit()
    return MessageResponse(message="Выход выполнен")


@router.get("/me", response_model=UserOut)
async def me(user: CurrentUser) -> UserOut:
    return user_out(user)


@router.patch("/me", response_model=UserOut)
async def update_profile(
    payload: UpdateProfileRequest, session: DbSession, request: Request, user: CurrentUser
) -> UserOut:
    user.display_name = payload.display_name.strip()
    await audit(session, request, "user.profile_update", "user", user.id, user_id=user.id)
    await session.commit()
    return user_out(user)


@router.post("/change-password", response_model=MessageResponse)
async def change_password(
    payload: ChangePasswordRequest, session: DbSession, request: Request, auth: CurrentAuth
) -> MessageResponse:
    if not verify_password(payload.current_password, auth.user.password_hash):
        raise HTTPException(status_code=400, detail="Текущий пароль неверен")
    auth.user.password_hash = hash_password(payload.new_password)
    await session.execute(
        update(AuthSession)
        .where(AuthSession.user_id == auth.user.id, AuthSession.id != auth.auth_session.id)
        .values(revoked_at=datetime.now(UTC))
    )
    await audit(
        session, request, "user.password_change", "user", auth.user.id, user_id=auth.user.id
    )
    await session.commit()
    return MessageResponse(message="Пароль изменён; остальные сессии завершены")


@router.post("/forgot-password", response_model=OneTimeTokenDebugResponse)
async def forgot_password(
    payload: PasswordResetRequest, session: DbSession
) -> OneTimeTokenDebugResponse:
    user = await session.scalar(select(User).where(User.email == payload.email.lower().strip()))
    exposed: str | None = None
    if user and user.is_active:
        raw = await create_one_time_token(
            session,
            user,
            "password_reset",
            datetime.now(UTC) + timedelta(minutes=settings.password_reset_expire_minutes),
        )
        await session.commit()
        await send_email_safely(
            "password_reset", email_service.send_password_reset(user.email, raw)
        )
        if settings.demo_expose_one_time_tokens:
            exposed = raw
    return OneTimeTokenDebugResponse(
        message="Если аккаунт существует, инструкция отправлена",
        token=exposed,
    )


@router.post("/reset-password", response_model=MessageResponse)
async def reset_password(payload: PasswordResetConfirm, session: DbSession) -> MessageResponse:
    item = await session.scalar(
        select(OneTimeToken).where(
            OneTimeToken.token_hash == token_hash(payload.token),
            OneTimeToken.purpose == "password_reset",
            OneTimeToken.used_at.is_(None),
        )
    )
    if item is None or aware(item.expires_at) <= datetime.now(UTC):
        raise HTTPException(status_code=400, detail="Токен недействителен или истёк")
    user = await session.get(User, item.user_id)
    if user is None:
        raise HTTPException(status_code=400, detail="Токен недействителен")
    user.password_hash = hash_password(payload.new_password)
    item.used_at = datetime.now(UTC)
    await session.execute(
        update(AuthSession)
        .where(AuthSession.user_id == user.id)
        .values(revoked_at=datetime.now(UTC))
    )
    await session.commit()
    return MessageResponse(message="Пароль изменён. Войдите заново")


@router.post("/request-verification", response_model=OneTimeTokenDebugResponse)
async def request_verification(session: DbSession, user: CurrentUser) -> OneTimeTokenDebugResponse:
    if user.is_verified:
        return OneTimeTokenDebugResponse(message="Email уже подтверждён")
    raw = await create_one_time_token(
        session,
        user,
        "verify_email",
        datetime.now(UTC) + timedelta(hours=settings.email_verify_expire_hours),
    )
    await session.commit()
    await send_email_safely("verification", email_service.send_verification(user.email, raw))
    return OneTimeTokenDebugResponse(
        message="Письмо отправлено",
        token=raw if settings.demo_expose_one_time_tokens else None,
    )


@router.post("/verify-email", response_model=MessageResponse)
async def verify_email(payload: VerifyEmailRequest, session: DbSession) -> MessageResponse:
    item = await session.scalar(
        select(OneTimeToken).where(
            OneTimeToken.token_hash == token_hash(payload.token),
            OneTimeToken.purpose == "verify_email",
            OneTimeToken.used_at.is_(None),
        )
    )
    if item is None or aware(item.expires_at) <= datetime.now(UTC):
        raise HTTPException(status_code=400, detail="Токен недействителен или истёк")
    user = await session.get(User, item.user_id)
    if user is None:
        raise HTTPException(status_code=400, detail="Токен недействителен")
    user.is_verified = True
    item.used_at = datetime.now(UTC)
    await session.commit()
    return MessageResponse(message="Email подтверждён")


@router.get("/sessions", response_model=list[SessionOut])
async def sessions(session: DbSession, auth: CurrentAuth) -> list[SessionOut]:
    result = await session.execute(
        select(AuthSession)
        .where(AuthSession.user_id == auth.user.id, AuthSession.revoked_at.is_(None))
        .order_by(AuthSession.last_used_at.desc())
    )
    return [
        SessionOut(
            id=item.id,
            user_agent=item.user_agent,
            ip_address=item.ip_address,
            expires_at=item.expires_at,
            last_used_at=item.last_used_at,
            created_at=item.created_at,
            current=item.id == auth.auth_session.id,
        )
        for item in result.scalars()
    ]


@router.delete("/sessions/{session_id}", response_model=MessageResponse)
async def revoke_session(
    session_id: UUID, session: DbSession, auth: CurrentAuth
) -> MessageResponse:
    result = await session.execute(
        update(AuthSession)
        .where(AuthSession.id == session_id, AuthSession.user_id == auth.user.id)
        .values(revoked_at=datetime.now(UTC))
    )
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Сессия не найдена")
    await session.commit()
    return MessageResponse(message="Сессия завершена")


@router.delete("/me", response_model=MessageResponse)
async def delete_account(
    session: DbSession, request: Request, user: CurrentUser
) -> MessageResponse:
    user.is_active = False
    user.email = f"deleted-{user.id}@invalid.local"
    user.display_name = "Deleted user"
    await session.execute(delete(OneTimeToken).where(OneTimeToken.user_id == user.id))
    await session.execute(
        update(AuthSession)
        .where(AuthSession.user_id == user.id)
        .values(revoked_at=datetime.now(UTC))
    )
    await audit(session, request, "user.delete", "user", user.id, user_id=user.id)
    await session.commit()
    return MessageResponse(message="Аккаунт отключён и персональные данные обезличены")
