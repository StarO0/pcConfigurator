from typing import Any
from uuid import UUID

from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.entities import AuditLog


async def audit(
    session: AsyncSession,
    request: Request,
    action: str,
    resource_type: str,
    resource_id: str | UUID | None = None,
    user_id: UUID | None = None,
    service_token_id: UUID | None = None,
    details: dict[str, Any] | None = None,
) -> None:
    session.add(
        AuditLog(
            actor_user_id=user_id,
            actor_service_token_id=service_token_id,
            action=action,
            resource_type=resource_type,
            resource_id=str(resource_id) if resource_id else None,
            request_id=getattr(request.state, "request_id", None),
            ip_address=request.client.host if request.client else None,
            details=details or {},
        )
    )
