from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class Point(BaseModel):
    x: float
    y: float
    tMs: int = Field(ge=0)

    pressure: float | None = None
    tiltX: float | None = None
    tiltY: float | None = None
    azimuth: float | None = None


class UserCreate(BaseModel):
    pass


class UserOut(BaseModel):
    id: uuid.UUID
    created_at: datetime


class UserSummary(BaseModel):
    id: uuid.UUID
    created_at: datetime
    datapoints_count: int
    sessions_count: int


class SessionCreate(BaseModel):
    user_id: uuid.UUID | None = None
    protocol_version: str = "v1"
    prompt_plan: dict[str, Any] = Field(default_factory=dict)


class SessionOut(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID | None
    protocol_version: str
    prompt_plan: dict[str, Any]
    started_at: datetime


class DatapointCreate(BaseModel):
    user_id: uuid.UUID
    session_id: uuid.UUID | None = None

    capture_label: str = ""
    protocol_version: str = "v1"

    metadata: dict[str, Any] = Field(default_factory=dict)
    points: list[Point]


class DatapointOut(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    session_id: uuid.UUID | None
    created_at: datetime
    capture_label: str
    protocol_version: str
    metadata: dict[str, Any]
    features: dict[str, Any]


class DatapointRawOut(BaseModel):
    id: uuid.UUID
    raw: dict[str, Any]


class DatapointListItem(BaseModel):
    id: uuid.UUID
    created_at: datetime
    capture_label: str
    protocol_version: str
    metadata: dict[str, Any]
    features: dict[str, Any]


class TagCreate(BaseModel):
    tag: str | None = None
    note: str | None = None


class TagOut(BaseModel):
    id: uuid.UUID
    datapoint_id: uuid.UUID
    created_at: datetime
    tag: str | None
    note: str | None


class ExportRequest(BaseModel):
    user_ids: list[uuid.UUID] | None = None
    protocol_version: str | None = None
    created_from: datetime | None = None
    created_to: datetime | None = None
