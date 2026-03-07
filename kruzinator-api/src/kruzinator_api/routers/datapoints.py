from __future__ import annotations

import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Security, status
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from .auth import get_current_active_user
from ..config import get_settings
from ..db import get_db_session
from ..features import compute_features
from ..models import Datapoint, DatapointTag, RewardEvent
from ..schemas import (
    DatapointCreate,
    DatapointMetadata,
    DatapointListItem,
    DatapointOut,
    DatapointRawOut,
    TagCreate,
    TagOut,
    UserResponse,
)


router = APIRouter(prefix="/api/v1", tags=["datapoints"])


def _ensure_owner_or_404(datapoint: Datapoint, current_user: UserResponse) -> None:
    if datapoint.user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Datapoint not found")


@router.post("/datapoints", response_model=DatapointOut, status_code=status.HTTP_201_CREATED)
async def create_datapoint(
    payload: DatapointCreate,
    current_user: UserResponse = Security(get_current_active_user, scopes=["me"]),
    db: AsyncSession = Depends(get_db_session),
) -> DatapointOut:
    settings = get_settings()

    points = [p.model_dump() for p in payload.points]
    features = compute_features(points)
    raw = {
        "points": points,
        "sampling": payload.metadata.sampling,
    }

    datapoint = Datapoint(
        user_id=current_user.id,
        capture_label=payload.capture_label,
        protocol_version=payload.protocol_version,
        context=payload.metadata.model_dump(mode="json"),
        raw=raw,
        features=features,
    )
    db.add(datapoint)

    # Flush so datapoint.id is available for the reward event.
    await db.flush()

    reward = RewardEvent(
        user_id=current_user.id,
        datapoint_id=datapoint.id,
        points=settings.rewards.points_per_datapoint,
        reason="datapoint_created",
        details={"protocol_version": payload.protocol_version, "capture_label": payload.capture_label},
    )
    db.add(reward)

    await db.commit()
    await db.refresh(datapoint)

    return DatapointOut(
        id=datapoint.id,
        created_at=datapoint.created_at,
        capture_label=datapoint.capture_label,
        protocol_version=datapoint.protocol_version,
        metadata=DatapointMetadata.model_validate(datapoint.context),
        features=datapoint.features,
    )


@router.get("/datapoints", response_model=list[DatapointListItem])
async def list_datapoints(
    protocol_version: str | None = None,
    capture_label: str | None = None,
    created_from: datetime | None = None,
    created_to: datetime | None = None,
    label_key: str | None = None,
    label_value: str | None = None,
    current_user: UserResponse = Security(get_current_active_user, scopes=["me"]),
    db: AsyncSession = Depends(get_db_session),
) -> list[DatapointListItem]:
    stmt = select(Datapoint).where(Datapoint.user_id == current_user.id)
    if protocol_version:
        stmt = stmt.where(Datapoint.protocol_version == protocol_version)
    if capture_label:
        stmt = stmt.where(Datapoint.capture_label == capture_label)
    if created_from:
        stmt = stmt.where(Datapoint.created_at >= created_from)
    if created_to:
        stmt = stmt.where(Datapoint.created_at <= created_to)
    if label_key and label_value:
        stmt = stmt.where(
            or_(
                Datapoint.context[label_key].astext == label_value,
                Datapoint.context["labels"][label_key].astext == label_value,
            )
        )

    stmt = stmt.order_by(Datapoint.created_at.desc())
    rows = (await db.execute(stmt)).scalars().all()

    return [
        DatapointListItem(
            id=r.id,
            created_at=r.created_at,
            capture_label=r.capture_label,
            protocol_version=r.protocol_version,
            metadata=DatapointMetadata.model_validate(r.context),
            features=r.features,
        )
        for r in rows
    ]


@router.get("/datapoints/{datapoint_id}", response_model=DatapointOut)
async def get_datapoint(
    datapoint_id: uuid.UUID,
    current_user: UserResponse = Security(get_current_active_user, scopes=["me"]),
    db: AsyncSession = Depends(get_db_session),
) -> DatapointOut:
    datapoint = await db.get(Datapoint, datapoint_id)
    if datapoint is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Datapoint not found")

    _ensure_owner_or_404(datapoint, current_user)

    return DatapointOut(
        id=datapoint.id,
        created_at=datapoint.created_at,
        capture_label=datapoint.capture_label,
        protocol_version=datapoint.protocol_version,
        metadata=DatapointMetadata.model_validate(datapoint.context),
        features=datapoint.features,
    )


@router.get("/datapoints/{datapoint_id}/raw", response_model=DatapointRawOut)
async def get_datapoint_raw(
    datapoint_id: uuid.UUID,
    current_user: UserResponse = Security(get_current_active_user, scopes=["me"]),
    db: AsyncSession = Depends(get_db_session),
) -> DatapointRawOut:
    datapoint = await db.get(Datapoint, datapoint_id)
    if datapoint is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Datapoint not found")

    _ensure_owner_or_404(datapoint, current_user)
    return DatapointRawOut(id=datapoint.id, raw=datapoint.raw)


@router.post("/datapoints/{datapoint_id}/tags", response_model=TagOut, status_code=status.HTTP_201_CREATED)
async def add_tag(
    datapoint_id: uuid.UUID,
    payload: TagCreate,
    current_user: UserResponse = Security(get_current_active_user, scopes=["me"]),
    db: AsyncSession = Depends(get_db_session),
) -> TagOut:
    datapoint = await db.get(Datapoint, datapoint_id)
    if datapoint is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Datapoint not found")

    _ensure_owner_or_404(datapoint, current_user)

    tag = DatapointTag(datapoint_id=datapoint_id, tag=payload.tag, note=payload.note)
    db.add(tag)
    await db.commit()
    await db.refresh(tag)
    return TagOut(
        id=tag.id,
        datapoint_id=tag.datapoint_id,
        created_at=tag.created_at,
        tag=tag.tag,
        note=tag.note,
    )


@router.delete("/datapoints/{datapoint_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_datapoint(
    datapoint_id: uuid.UUID,
    current_user: UserResponse = Security(get_current_active_user, scopes=["me"]),
    db: AsyncSession = Depends(get_db_session),
) -> None:
    datapoint = await db.get(Datapoint, datapoint_id)
    if datapoint is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Datapoint not found")

    _ensure_owner_or_404(datapoint, current_user)

    await db.delete(datapoint)
    await db.commit()
