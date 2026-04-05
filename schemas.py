from datetime import datetime
from typing import Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class APIResponse(BaseModel, Generic[T]):
    success: bool = True
    code: int = 0
    message: str = "ok"
    data: T | None = None


class ReceiveRequest(BaseModel):
    source_text: str = Field(..., min_length=1, max_length=5000)
    source_lang: str = Field(..., min_length=2, max_length=16)
    target_lang: str = Field(..., min_length=2, max_length=16)


class ReceiveResponse(BaseModel):
    message_id: int
    status: str


class TranslateRequest(BaseModel):
    message_id: int


class MessageData(BaseModel):
    id: int
    source_text: str
    source_lang: str
    target_lang: str
    translated_text: str | None
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
