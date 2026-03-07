from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    anonnymous_name: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    hashed_password: Mapped[str | None] = mapped_column(String(256), nullable=True)
    refresh_token_jti: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    is_active: Mapped[bool] = mapped_column(default=True)
    is_admin: Mapped[bool] = mapped_column(default=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    datapoints: Mapped[list[Datapoint]] = relationship(back_populates="user", cascade="all, delete-orphan")
    reward_events: Mapped[list[RewardEvent]] = relationship(
        back_populates="user",
        order_by="RewardEvent.created_at.asc()",
        passive_deletes=True,
    )


class Datapoint(Base):
    __tablename__ = "datapoints"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    capture_label: Mapped[str] = mapped_column(String(128), default="")
    protocol_version: Mapped[str] = mapped_column(String(64), default="v1")

    context: Mapped[dict] = mapped_column("metadata", JSONB, default=dict)
    raw: Mapped[dict] = mapped_column(JSONB)
    features: Mapped[dict] = mapped_column(JSONB, default=dict)

    user: Mapped[User] = relationship(back_populates="datapoints")
    tags: Mapped[list[DatapointTag]] = relationship(
        back_populates="datapoint",
        cascade="all, delete-orphan",
        order_by="DatapointTag.created_at.asc()",
    )
    reward_events: Mapped[list[RewardEvent]] = relationship(
        back_populates="datapoint",
        order_by="RewardEvent.created_at.asc()",
        passive_deletes=True,
    )


Index("ix_datapoints_user_created", Datapoint.user_id, Datapoint.created_at)


class DatapointTag(Base):
    __tablename__ = "datapoint_tags"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    datapoint_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("datapoints.id", ondelete="CASCADE"),
    )

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    tag: Mapped[str | None] = mapped_column(String(64), nullable=True)
    note: Mapped[str | None] = mapped_column(Text(), nullable=True)

    datapoint: Mapped[Datapoint] = relationship(back_populates="tags")


class RewardEvent(Base):
    __tablename__ = "reward_events"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    datapoint_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("datapoints.id", ondelete="CASCADE"),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    points: Mapped[int] = mapped_column(Integer, nullable=False)
    reason: Mapped[str] = mapped_column(String(64), nullable=False)
    details: Mapped[dict] = mapped_column(JSONB, default=dict)

    user: Mapped[User] = relationship(back_populates="reward_events")
    datapoint: Mapped[Datapoint | None] = relationship(back_populates="reward_events")


Index("ix_reward_events_user_created", RewardEvent.user_id, RewardEvent.created_at)
