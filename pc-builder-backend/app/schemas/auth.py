from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, field_validator


class RegisterRequest(BaseModel):
    email: EmailStr
    display_name: str = Field(min_length=2, max_length=100)
    password: str = Field(min_length=10, max_length=128)

    @field_validator("password")
    @classmethod
    def password_strength(cls, value: str) -> str:
        groups = [
            any(char.islower() for char in value),
            any(char.isupper() for char in value),
            any(char.isdigit() for char in value),
        ]
        if sum(groups) < 2:
            raise ValueError("Пароль должен содержать символы минимум двух разных типов")
        return value


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class RefreshRequest(BaseModel):
    refresh_token: str = Field(min_length=32, max_length=500)


class LogoutRequest(BaseModel):
    refresh_token: str | None = Field(default=None, min_length=32, max_length=500)
    all_sessions: bool = False


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_at: datetime


class UserOut(BaseModel):
    id: UUID
    email: EmailStr
    display_name: str
    role: Literal["user", "admin"]
    is_active: bool
    is_verified: bool
    created_at: datetime


class UpdateProfileRequest(BaseModel):
    display_name: str = Field(min_length=2, max_length=100)


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(min_length=10, max_length=128)


class PasswordResetRequest(BaseModel):
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    token: str = Field(min_length=32, max_length=500)
    new_password: str = Field(min_length=10, max_length=128)


class VerifyEmailRequest(BaseModel):
    token: str = Field(min_length=32, max_length=500)


class SessionOut(BaseModel):
    id: UUID
    user_agent: str | None
    ip_address: str | None
    expires_at: datetime
    last_used_at: datetime
    created_at: datetime
    current: bool = False


class OneTimeTokenDebugResponse(BaseModel):
    message: str
    token: str | None = None
