from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..db import get_db_session
from ..models import Session, User
from ..schemas import SessionCreate, SessionOut


router = APIRouter(prefix="/api/v1/sessions", tags=["sessions"])


@router.post("", response_model=SessionOut, status_code=status.HTTP_201_CREATED)
async def create_session(payload: SessionCreate, db: AsyncSession = Depends(get_db_session)) -> SessionOut:
    if payload.user_id is not None:
        user = await db.get(User, payload.user_id)
        if user is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    session = Session(
        user_id=payload.user_id,
        protocol_version=payload.protocol_version,
        prompt_plan=payload.prompt_plan,
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)
    return SessionOut(
        id=session.id,
        user_id=session.user_id,
        protocol_version=session.protocol_version,
        prompt_plan=session.prompt_plan,
        started_at=session.started_at,
    )
