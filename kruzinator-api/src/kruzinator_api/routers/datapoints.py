from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..db import get_db_session
from ..features import compute_features
from ..models import Datapoint, DatapointTag, Session, User
from ..schemas import (
    DatapointCreate,
    DatapointListItem,
    DatapointOut,
    DatapointRawOut,
    TagCreate,
    TagOut,
)


router = APIRouter(prefix="/api/v1", tags=["datapoints"])


@router.post("/datapoints", response_model=DatapointOut, status_code=status.HTTP_201_CREATED)
async def create_datapoint(payload: DatapointCreate, db: AsyncSession = Depends(get_db_session)) -> DatapointOut:
    user = await db.get(User, payload.user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if payload.session_id is not None:
        session = await db.get(Session, payload.session_id)
        if session is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")

    points = [p.model_dump() for p in payload.points]
    features = compute_features(points)
    raw = {
        "points": points,
        "sampling": payload.metadata.get("sampling"),
    }

    datapoint = Datapoint(
        user_id=payload.user_id,
        session_id=payload.session_id,
        capture_label=payload.capture_label,
        protocol_version=payload.protocol_version,
        context=payload.metadata,
        raw=raw,
        features=features,
    )
    db.add(datapoint)
    await db.commit()
    await db.refresh(datapoint)

    return DatapointOut(
        id=datapoint.id,
        user_id=datapoint.user_id,
        session_id=datapoint.session_id,
        created_at=datapoint.created_at,
        capture_label=datapoint.capture_label,
        protocol_version=datapoint.protocol_version,
        metadata=datapoint.context,
        features=datapoint.features,
    )


@router.get("/users/{user_id}/datapoints", response_model=list[DatapointListItem])
async def list_user_datapoints(user_id: uuid.UUID, db: AsyncSession = Depends(get_db_session)) -> list[DatapointListItem]:
    user = await db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    rows = (await db.execute(select(Datapoint).where(Datapoint.user_id == user_id).order_by(Datapoint.created_at.desc()))).scalars().all()
    return [
        DatapointListItem(
            id=r.id,
            created_at=r.created_at,
            capture_label=r.capture_label,
            protocol_version=r.protocol_version,
            metadata=r.context,
            features=r.features,
        )
        for r in rows
    ]


@router.get("/datapoints/{datapoint_id}", response_model=DatapointOut)
async def get_datapoint(datapoint_id: uuid.UUID, db: AsyncSession = Depends(get_db_session)) -> DatapointOut:
    datapoint = await db.get(Datapoint, datapoint_id)
    if datapoint is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Datapoint not found")

    return DatapointOut(
        id=datapoint.id,
        user_id=datapoint.user_id,
        session_id=datapoint.session_id,
        created_at=datapoint.created_at,
        capture_label=datapoint.capture_label,
        protocol_version=datapoint.protocol_version,
        metadata=datapoint.context,
        features=datapoint.features,
    )


@router.get("/datapoints/{datapoint_id}/raw", response_model=DatapointRawOut)
async def get_datapoint_raw(datapoint_id: uuid.UUID, db: AsyncSession = Depends(get_db_session)) -> DatapointRawOut:
    datapoint = await db.get(Datapoint, datapoint_id)
    if datapoint is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Datapoint not found")
    return DatapointRawOut(id=datapoint.id, raw=datapoint.raw)


@router.post("/datapoints/{datapoint_id}/tags", response_model=TagOut, status_code=status.HTTP_201_CREATED)
async def add_tag(
    datapoint_id: uuid.UUID,
    payload: TagCreate,
    db: AsyncSession = Depends(get_db_session),
) -> TagOut:
    datapoint = await db.get(Datapoint, datapoint_id)
    if datapoint is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Datapoint not found")

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
