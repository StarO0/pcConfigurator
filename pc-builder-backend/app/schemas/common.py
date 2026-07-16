from typing import TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class MessageResponse(BaseModel):
    message: str


class Page[T](BaseModel):
    items: list[T]
    total: int
    limit: int = Field(ge=1)
    offset: int = Field(ge=0)
