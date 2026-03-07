"""drop sessions

Revision ID: 0003_drop_sessions
Revises: 0002_user_auth_fields
Create Date: 2026-03-07

"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


revision = "0003_drop_sessions"
down_revision = "0002_user_auth_fields"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Drop the datapoints -> sessions reference first.
    # Postgres will drop the underlying FK constraint automatically when dropping the column.
    with op.batch_alter_table("datapoints") as batch:
        batch.drop_column("session_id")

    op.drop_table("sessions")


def downgrade() -> None:
    op.create_table(
        "sessions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=True,
        ),
        sa.Column("protocol_version", sa.String(length=64), nullable=False),
        sa.Column("prompt_plan", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )

    with op.batch_alter_table("datapoints") as batch:
        batch.add_column(sa.Column("session_id", postgresql.UUID(as_uuid=True), nullable=True))
        batch.create_foreign_key(
            "fk_datapoints_session_id_sessions",
            "sessions",
            ["session_id"],
            ["id"],
            ondelete="SET NULL",
        )
