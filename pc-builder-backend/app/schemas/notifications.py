from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field


class PriceAlertCreate(BaseModel):
    product_id: UUID
    target_price: Decimal = Field(gt=0)
    currency: str = Field(default="PLN", min_length=3, max_length=3)


class PriceAlertOut(BaseModel):
    id: UUID
    product_id: UUID
    target_price: Decimal
    currency: str
    is_active: bool
    last_notified_price: Decimal | None
    created_at: datetime


class NotificationOut(BaseModel):
    id: UUID
    kind: str
    title: str
    body: str
    data: dict
    read_at: datetime | None
    created_at: datetime
