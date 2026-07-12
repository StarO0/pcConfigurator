from datetime import UTC, datetime
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import func, select

from app.api.deps import CurrentUser, DbSession
from app.models.entities import Notification, PriceAlert, Product
from app.schemas.common import MessageResponse, Page
from app.schemas.notifications import NotificationOut, PriceAlertCreate, PriceAlertOut

router = APIRouter(tags=["notifications"])


@router.post("/price-alerts", response_model=PriceAlertOut)
async def create_price_alert(
    payload: PriceAlertCreate, session: DbSession, user: CurrentUser
) -> PriceAlertOut:
    if await session.get(Product, payload.product_id) is None:
        raise HTTPException(status_code=404, detail="Товар не найден")
    item = await session.scalar(
        select(PriceAlert).where(
            PriceAlert.user_id == user.id,
            PriceAlert.product_id == payload.product_id,
            PriceAlert.currency == payload.currency.upper(),
        )
    )
    if item is None:
        item = PriceAlert(
            user_id=user.id,
            product_id=payload.product_id,
            target_price=payload.target_price,
            currency=payload.currency.upper(),
        )
        session.add(item)
    else:
        item.target_price = payload.target_price
        item.is_active = True
    await session.commit()
    await session.refresh(item)
    return PriceAlertOut.model_validate(item, from_attributes=True)


@router.get("/price-alerts", response_model=list[PriceAlertOut])
async def list_price_alerts(session: DbSession, user: CurrentUser) -> list[PriceAlertOut]:
    result = await session.execute(
        select(PriceAlert)
        .where(PriceAlert.user_id == user.id)
        .order_by(PriceAlert.created_at.desc())
    )
    return [PriceAlertOut.model_validate(item, from_attributes=True) for item in result.scalars()]


@router.delete("/price-alerts/{alert_id}", response_model=MessageResponse)
async def delete_price_alert(
    alert_id: UUID, session: DbSession, user: CurrentUser
) -> MessageResponse:
    item = await session.scalar(
        select(PriceAlert).where(PriceAlert.id == alert_id, PriceAlert.user_id == user.id)
    )
    if item is None:
        raise HTTPException(status_code=404, detail="Уведомление о цене не найдено")
    await session.delete(item)
    await session.commit()
    return MessageResponse(message="Уведомление удалено")


@router.get("/notifications", response_model=Page[NotificationOut])
async def list_notifications(
    session: DbSession,
    user: CurrentUser,
    unread_only: bool = False,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> Page[NotificationOut]:
    filters = [Notification.user_id == user.id]
    if unread_only:
        filters.append(Notification.read_at.is_(None))
    total = await session.scalar(select(func.count(Notification.id)).where(*filters)) or 0
    result = await session.execute(
        select(Notification)
        .where(*filters)
        .order_by(Notification.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    return Page[NotificationOut](
        items=[
            NotificationOut.model_validate(item, from_attributes=True) for item in result.scalars()
        ],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.post("/notifications/{notification_id}/read", response_model=NotificationOut)
async def mark_notification_read(
    notification_id: UUID, session: DbSession, user: CurrentUser
) -> NotificationOut:
    item = await session.scalar(
        select(Notification).where(
            Notification.id == notification_id, Notification.user_id == user.id
        )
    )
    if item is None:
        raise HTTPException(status_code=404, detail="Уведомление не найдено")
    item.read_at = datetime.now(UTC)
    await session.commit()
    return NotificationOut.model_validate(item, from_attributes=True)
