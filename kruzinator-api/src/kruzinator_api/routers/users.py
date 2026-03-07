from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Security, status
from sqlalchemy.ext.asyncio import AsyncSession

from .auth import get_current_active_user
from ..db import get_db_session
from ..models import User
from ..schemas import UserOut, UserResponse


router = APIRouter(prefix="/api/v1/users", tags=["users"])


@router.get("/me", response_model=UserOut)
async def get_me(
    current_user: UserResponse = Security(get_current_active_user, scopes=["me"]),
    db: AsyncSession = Depends(get_db_session),
) -> UserOut:
    user = await db.get(User, current_user.id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return UserOut(id=user.id, created_at=user.created_at)


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
async def delete_me(
    current_user: UserResponse = Security(get_current_active_user, scopes=["me"]),
    db: AsyncSession = Depends(get_db_session),
) -> None:
    user = await db.get(User, current_user.id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    await db.delete(user)
    await db.commit()
