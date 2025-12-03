# path: backend/api/schemas.py
# version: v0.1
# purpose: autofill
from __future__ import annotations

from typing import Any, Generic, Optional, TypeVar, Literal

from pydantic import BaseModel


class ErrorInfo(BaseModel):
    code: int
    message: str


T = TypeVar("T")


class Envelope(BaseModel, Generic[T]):
    status: Literal["ok", "error"]
    data: Optional[T] = None
    error: Optional[ErrorInfo] = None
