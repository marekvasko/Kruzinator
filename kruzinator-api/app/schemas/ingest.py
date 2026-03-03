from __future__ import annotations

from datetime import datetime
from typing import Annotated, Any, Dict, List, Literal, Optional, Union
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

NonEmptyStr = Annotated[str, Field(min_length=1)]
ISODateTime = datetime

CanvasPixels = Annotated[int, Field(ge=1, le=16384)]
DevicePixelRatio = Annotated[float, Field(gt=0.0, le=10.0)]

Ms = Annotated[int, Field(ge=0, le=24 * 60 * 60 * 1000)]
PointCount = Annotated[int, Field(ge=2, le=20000)]


class DeviceInfo(BaseModel):
    model_config = ConfigDict(extra='forbid')

    platform: Literal['ios', 'android', 'web']
    os_version: Optional[str] = Field(default=None, max_length=64)
    model: Optional[str] = Field(default=None, max_length=128)
    device_id: Optional[str] = Field(default=None, max_length=128)
    user_agent: Optional[str] = Field(default=None, max_length=512)


class AppInfo(BaseModel):
    model_config = ConfigDict(extra='forbid')

    app_version: NonEmptyStr = Field(max_length=64)
    build_number: Optional[str] = Field(default=None, max_length=64)
    client_ts: Optional[ISODateTime] = None


class CanvasInfo(BaseModel):
    model_config = ConfigDict(extra='forbid')

    width_px: CanvasPixels
    height_px: CanvasPixels
    dpr: DevicePixelRatio = Field(default=1.0)
    orientation: Optional[Literal['portrait', 'landscape']] = None


class IngestContext(BaseModel):
    model_config = ConfigDict(extra='forbid')

    session_id: Optional[UUID] = None
    task_id: Optional[str] = Field(default=None, max_length=64)
    locale: Optional[str] = Field(default=None, max_length=32)


class IngestMetadata(BaseModel):
    model_config = ConfigDict(extra='forbid')

    device: DeviceInfo
    app: AppInfo
    canvas: CanvasInfo
    context: Optional[IngestContext] = None


class StrokePoint(BaseModel):
    model_config = ConfigDict(extra='forbid')

    x: float = Field(ge=-1e6, le=1e6)
    y: float = Field(ge=-1e6, le=1e6)
    t_ms: Ms
    pressure: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    tilt_x: Optional[float] = Field(default=None, ge=-90.0, le=90.0)
    tilt_y: Optional[float] = Field(default=None, ge=-90.0, le=90.0)
    azimuth: Optional[float] = Field(default=None, ge=0.0, le=360.0)
    event: Optional[Literal['down', 'move', 'up', 'cancel']] = None


class RawTimeseries(BaseModel):
    model_config = ConfigDict(extra='forbid')

    format: Literal['raw_points'] = 'raw_points'
    points: Annotated[List[StrokePoint], Field(min_length=2, max_length=20000)]


class PackedDeltaTimeseries(BaseModel):
    model_config = ConfigDict(extra='forbid')

    format: Literal['packed_deltas'] = 'packed_deltas'
    origin_x: float = Field(ge=-1e6, le=1e6)
    origin_y: float = Field(ge=-1e6, le=1e6)
    origin_t_ms: Ms = 0
    dx: Annotated[List[int], Field(min_length=1, max_length=20000)]
    dy: Annotated[List[int], Field(min_length=1, max_length=20000)]
    dt_ms: Annotated[List[int], Field(min_length=1, max_length=20000)]
    pressure_q: Optional[Annotated[List[int], Field(min_length=1, max_length=20000)]] = None
    units: Literal['px_scaled_1', 'px_scaled_10', 'px_scaled_100', 'norm_10000'] = 'px_scaled_10'

    @model_validator(mode='after')
    def validate_lengths(self) -> 'PackedDeltaTimeseries':
        if not (len(self.dx) == len(self.dy) == len(self.dt_ms)):
            raise ValueError('dx, dy, and dt_ms must have the same length')
        if self.pressure_q is not None and len(self.pressure_q) != len(self.dx):
            raise ValueError('pressure_q must have the same length as dx')
        return self


Timeseries = Annotated[Union[RawTimeseries, PackedDeltaTimeseries], Field(discriminator='format')]


class InlinePayload(BaseModel):
    model_config = ConfigDict(extra='forbid')

    kind: Literal['inline'] = 'inline'
    timeseries: Timeseries


class GzipBase64Payload(BaseModel):
    model_config = ConfigDict(extra='forbid')

    kind: Literal['gzip_base64'] = 'gzip_base64'
    content_type: Literal['application/msgpack', 'application/json'] = 'application/msgpack'
    gz_b64: NonEmptyStr = Field(description='Gzip-compressed bytes encoded as base64')
    schema_version: Annotated[int, Field(ge=1, le=100)] = 1


IngestPayload = Annotated[Union[InlinePayload, GzipBase64Payload], Field(discriminator='kind')]


class PreviewImage(BaseModel):
    model_config = ConfigDict(extra='forbid')

    kind: Literal['png_base64'] = 'png_base64'
    png_b64: NonEmptyStr = Field(description='PNG bytes encoded as base64')
    width_px: CanvasPixels
    height_px: CanvasPixels


class IngestDatapointRequest(BaseModel):
    model_config = ConfigDict(extra='forbid')

    metadata: IngestMetadata
    payload: IngestPayload
    client_metrics: Optional[Dict[str, Any]] = None
    preview: Optional[PreviewImage] = None
    idempotency_key: Optional[str] = Field(default=None, max_length=128)


class EarnedBadge(BaseModel):
    model_config = ConfigDict(extra='forbid')

    code: NonEmptyStr = Field(max_length=64)
    earned_at: ISODateTime


class IngestDatapointResponse(BaseModel):
    model_config = ConfigDict(extra='forbid')

    datapoint_id: UUID
    received_at: ISODateTime
    accepted: bool
    quality_score: Annotated[float, Field(ge=0.0, le=1.0)] = 0.0
    earned_points: Annotated[int, Field(ge=0, le=1000)] = 0
    new_badges: List[EarnedBadge] = Field(default_factory=list)
    server_metrics: Optional[Dict[str, Any]] = None


class IngestBatchRequest(BaseModel):
    model_config = ConfigDict(extra='forbid')

    metadata: IngestMetadata
    items: Annotated[List[IngestDatapointRequest], Field(min_length=1, max_length=200)]


class IngestBatchResponseItem(BaseModel):
    model_config = ConfigDict(extra='forbid')

    client_idempotency_key: Optional[str] = None
    result: IngestDatapointResponse


class IngestBatchResponse(BaseModel):
    model_config = ConfigDict(extra='forbid')

    results: List[IngestBatchResponseItem]
