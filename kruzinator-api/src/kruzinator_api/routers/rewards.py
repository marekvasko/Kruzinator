from __future__ import annotations

from fastapi import APIRouter, Depends, Security
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from .auth import get_current_active_user
from ..config import Settings, get_settings
from ..db import get_db_session
from ..models import RewardEvent
from ..schemas import RewardEventOut, RewardSummaryOut, UserResponse


router = APIRouter(prefix="/api/v1", tags=["rewards"])


@router.get("/rewards/me", response_model=RewardSummaryOut)
async def get_my_rewards(
    current_user: UserResponse = Security(get_current_active_user, scopes=["me"]),
    settings: Settings = Depends(get_settings),
    db: AsyncSession = Depends(get_db_session),
) -> RewardSummaryOut:
    total_points = (
        await db.execute(
            select(func.coalesce(func.sum(RewardEvent.points), 0)).where(RewardEvent.user_id == current_user.id)
        )
    ).scalar_one()

    points_per_level = max(int(settings.rewards.points_per_level), 1)
    level = 1 + (int(total_points) // points_per_level)
    next_level_at = int(level * points_per_level)

    return RewardSummaryOut(
        total_points=int(total_points),
        level=int(level),
        points_per_level=points_per_level,
        next_level_at=next_level_at,
    )


@router.get("/rewards/events", response_model=list[RewardEventOut])
async def list_my_reward_events(
    current_user: UserResponse = Security(get_current_active_user, scopes=["me"]),
    db: AsyncSession = Depends(get_db_session),
) -> list[RewardEventOut]:
    stmt = (
        select(RewardEvent)
        .where(RewardEvent.user_id == current_user.id)
        .order_by(RewardEvent.created_at.desc())
    )
    events = (await db.execute(stmt)).scalars().all()

    return [
        RewardEventOut(
            id=e.id,
            created_at=e.created_at,
            points=e.points,
            reason=e.reason,
            datapoint_id=e.datapoint_id,
            details=e.details or {},
        )
        for e in events
    ]
