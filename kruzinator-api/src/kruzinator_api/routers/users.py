from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..db import get_db_session
from ..models import Datapoint, Session, User
from ..schemas import UserCreate, UserOut, UserSummary


router = APIRouter(prefix="/api/v1/users", tags=["users"])


@router.post("", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def create_user(
    _payload: UserCreate,
    db: AsyncSession = Depends(get_db_session),
) -> UserOut:
    user = User()
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return UserOut(id=user.id, created_at=user.created_at)


@router.get("/{user_id}", response_model=UserSummary)
async def get_user(user_id: uuid.UUID, db: AsyncSession = Depends(get_db_session)) -> UserSummary:
    user = await db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    datapoints_count = await db.scalar(select(func.count()).select_from(Datapoint).where(Datapoint.user_id == user_id))
    sessions_count = await db.scalar(select(func.count()).select_from(Session).where(Session.user_id == user_id))

    return UserSummary(
        id=user.id,
        created_at=user.created_at,
        datapoints_count=int(datapoints_count or 0),
        sessions_count=int(sessions_count or 0),
    )


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(user_id: uuid.UUID, db: AsyncSession = Depends(get_db_session)) -> None:
    user = await db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    await db.delete(user)
    await db.commit()
