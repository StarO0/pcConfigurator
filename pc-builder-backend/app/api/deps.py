from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Annotated

from fastapi import Depends, Header, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import user_id_ctx
from app.core.security import decode_access_token, token_hash
from app.db.session import get_db
from app.models.entities import AuthSession, ServiceToken, User

bearer = HTTPBearer(auto_error=False)
DbSession = Annotated[AsyncSession, Depends(get_db)]


@dataclass(slots=True)
class AuthContext:
    user: User
    auth_session: AuthSession


async def get_optional_auth_context(
    session: DbSession,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
) -> AuthContext | None:
    if credentials is None:
        return None
    claims = decode_access_token(credentials.credentials)
    if claims is None:
        return None
    result = await session.execute(
        select(User, AuthSession)
        .join(AuthSession, AuthSession.user_id == User.id)
        .where(
            User.id == claims.user_id,
            User.is_active.is_(True),
            AuthSession.id == claims.session_id,
            AuthSession.revoked_at.is_(None),
            AuthSession.expires_at > datetime.now(UTC),
        )
    )
    row = result.one_or_none()
    if row is None:
        return None
    user, auth_session = row
    user_id_ctx.set(str(user.id))
    return AuthContext(user=user, auth_session=auth_session)


async def get_auth_context(
    context: Annotated[AuthContext | None, Depends(get_optional_auth_context)],
) -> AuthContext:
    if context is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Требуется авторизация",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return context


async def get_current_user(context: Annotated[AuthContext, Depends(get_auth_context)]) -> User:
    return context.user


async def get_admin_user(user: Annotated[User, Depends(get_current_user)]) -> User:
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Требуются права администратора")
    return user


async def get_optional_user(
    context: Annotated[AuthContext | None, Depends(get_optional_auth_context)],
) -> User | None:
    return context.user if context else None


async def get_service_token(
    session: DbSession,
    raw_token: Annotated[str | None, Header(alias="X-Service-Token")] = None,
) -> ServiceToken | None:
    if not raw_token:
        return None
    item = await session.scalar(
        select(ServiceToken).where(
            ServiceToken.is_active.is_(True),
            ServiceToken.token_hash == token_hash(raw_token),
        )
    )
    if item is None:
        return None
    now = datetime.now(UTC)
    if item.expires_at:
        expires = item.expires_at if item.expires_at.tzinfo else item.expires_at.replace(tzinfo=UTC)
        if expires <= now:
            return None
    item.last_used_at = now
    return item


CurrentUser = Annotated[User, Depends(get_current_user)]
OptionalUser = Annotated[User | None, Depends(get_optional_user)]
CurrentAuth = Annotated[AuthContext, Depends(get_auth_context)]
AdminUser = Annotated[User, Depends(get_admin_user)]
ServiceAuth = Annotated[ServiceToken | None, Depends(get_service_token)]
