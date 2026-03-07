from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Literal

from pydantic import AliasChoices, BaseModel, ConfigDict, Field


class Point(BaseModel):
    x: float
    y: float
    tMs: int = Field(ge=0)

    pressure: float | None = None
    tiltX: float | None = None
    tiltY: float | None = None
    azimuth: float | None = None


class UserRequest(BaseModel):
    anonnymous_name: str
    password: str | None = None


class UserResponse(BaseModel):
    id: uuid.UUID
    username: str = Field(
        validation_alias=AliasChoices("username", "anonnymous_name"),
        serialization_alias="username",
    )
    is_active: bool = True
    is_admin: bool = False


class User(UserResponse):
    hashed_password: str | None = None
    refresh_token_jti: uuid.UUID | None = None
    is_active: bool = True
    is_admin: bool = False


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    refresh_token: str | None = None


class UserOut(BaseModel):
    id: uuid.UUID
    created_at: datetime


class RegisterRequest(BaseModel):
    username: str
    password: str


Hand = Literal["left", "right", "unknown"]
Direction = Literal["clockwise", "counterclockwise", "unknown"]
Tool = Literal["index", "thumb", "stylus", "mouse", "unknown"]
InputType = Literal["touch", "pen", "mouse", "unknown"]
SamplingMode = Literal["raw", "time", "distance", "hybrid"]


class CanvasInfo(BaseModel):
    width: int | None = None
    height: int | None = None
    dpr: float | None = None


class DeviceInfo(BaseModel):
    platform: str | None = None
    user_agent: str | None = None
    language: str | None = None


class DatapointMetadata(BaseModel):
    model_config = ConfigDict(extra="allow")

    app_version: str | None = None
    input_type: InputType | None = None
    sampling: SamplingMode | None = None

    hand: Hand | None = None
    tool: Tool | None = None
    direction: Direction | None = None

    canvas: CanvasInfo | None = None
    device: DeviceInfo | None = None

    # Flexible per-protocol labels; this is where we expect things like
    # {"hand": "right", "direction": "clockwise"} if you prefer a flat label bag.
    labels: dict[str, Any] = Field(default_factory=dict)


class DatapointCreate(BaseModel):
    capture_label: str = ""
    protocol_version: str = "v1"

    metadata: DatapointMetadata = Field(default_factory=DatapointMetadata)
    points: list[Point]


class DatapointOut(BaseModel):
    id: uuid.UUID
    created_at: datetime
    capture_label: str
    protocol_version: str
    metadata: DatapointMetadata
    features: dict[str, Any]


class DatapointRawOut(BaseModel):
    id: uuid.UUID
    raw: dict[str, Any]


class DatapointListItem(BaseModel):
    id: uuid.UUID
    created_at: datetime
    capture_label: str
    protocol_version: str
    metadata: DatapointMetadata
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
    protocol_version: str | None = None
    created_from: datetime | None = None
    created_to: datetime | None = None
    labels: dict[str, Any] | None = None


class RewardEventOut(BaseModel):
    id: uuid.UUID
    created_at: datetime
    points: int
    reason: str
    datapoint_id: uuid.UUID | None = None
    details: dict[str, Any] = Field(default_factory=dict)


class RewardSummaryOut(BaseModel):
    total_points: int
    level: int
    points_per_level: int
    next_level_at: int
