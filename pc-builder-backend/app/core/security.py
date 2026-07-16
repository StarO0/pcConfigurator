from __future__ import annotations

import hashlib
import hmac
import secrets
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import jwt
from jwt.exceptions import InvalidTokenError
from pwdlib import PasswordHash

from app.core.config import settings

password_hash = PasswordHash.recommended()
DUMMY_HASH = password_hash.hash("dummy-password-for-timing-protection")


@dataclass(slots=True)
class AccessTokenClaims:
    user_id: UUID
    session_id: UUID
    role: str
    expires_at: datetime


def hash_password(password: str) -> str:
    return password_hash.hash(password)


def verify_password(password: str, hashed_password: str) -> bool:
    return password_hash.verify(password, hashed_password)


def create_access_token(user_id: UUID, session_id: UUID, role: str) -> tuple[str, datetime]:
    expires = datetime.now(UTC) + timedelta(minutes=settings.access_token_expire_minutes)
    payload = {
        "sub": str(user_id),
        "sid": str(session_id),
        "role": role,
        "jti": str(uuid4()),
        "iat": datetime.now(UTC),
        "exp": expires,
        "type": "access",
    }
    token = jwt.encode(payload, settings.secret_key_value, algorithm=settings.jwt_algorithm)
    return token, expires


def decode_access_token(token: str) -> AccessTokenClaims | None:
    try:
        payload = jwt.decode(
            token,
            settings.secret_key_value,
            algorithms=[settings.jwt_algorithm],
            options={"require": ["sub", "sid", "exp", "type"]},
        )
        if payload.get("type") != "access":
            return None
        return AccessTokenClaims(
            user_id=UUID(payload["sub"]),
            session_id=UUID(payload["sid"]),
            role=str(payload.get("role", "user")),
            expires_at=datetime.fromtimestamp(payload["exp"], tz=UTC),
        )
    except (InvalidTokenError, KeyError, TypeError, ValueError):
        return None


def generate_opaque_token(bytes_count: int = 48) -> str:
    return secrets.token_urlsafe(bytes_count)


def token_hash(token: str) -> str:
    return hmac.new(
        settings.token_pepper_value.encode(),
        token.encode(),
        hashlib.sha256,
    ).hexdigest()


def constant_time_token_match(token: str, expected_hash: str) -> bool:
    return hmac.compare_digest(token_hash(token), expected_hash)


def utcnow() -> datetime:
    return datetime.now(UTC)
