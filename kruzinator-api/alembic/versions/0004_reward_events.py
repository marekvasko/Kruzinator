"""reward events ledger

Revision ID: 0004_reward_events
Revises: 0003_drop_sessions
Create Date: 2026-03-07

"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


revision = "0004_reward_events"
down_revision = "0003_drop_sessions"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "reward_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "datapoint_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("datapoints.id", ondelete="CASCADE"),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("points", sa.Integer(), nullable=False),
        sa.Column("reason", sa.String(length=64), nullable=False),
        sa.Column("details", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
    )

    op.create_index(
        "ix_reward_events_user_created",
        "reward_events",
        ["user_id", "created_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_reward_events_user_created", table_name="reward_events")
    op.drop_table("reward_events")
