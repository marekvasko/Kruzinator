"""add auth fields to users

Revision ID: 0002_user_auth_fields
Revises: 0001_init
Create Date: 2026-03-07

"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


revision = "0002_user_auth_fields"
down_revision = "0001_init"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add columns as nullable first to allow backfill for existing rows.
    op.add_column("users", sa.Column("anonnymous_name", sa.String(length=128), nullable=True))
    op.add_column("users", sa.Column("hashed_password", sa.String(length=256), nullable=True))
    op.add_column(
        "users",
        sa.Column("refresh_token_jti", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.add_column(
        "users",
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
    )
    op.add_column(
        "users",
        sa.Column("is_admin", sa.Boolean(), server_default=sa.text("false"), nullable=False),
    )

    # Backfill anonymous names for pre-existing users (if any) using a deterministic unique value.
    op.execute("UPDATE users SET anonnymous_name = 'user-' || id::text WHERE anonnymous_name IS NULL")

    op.alter_column("users", "anonnymous_name", nullable=False)
    op.create_unique_constraint("uq_users_anonnymous_name", "users", ["anonnymous_name"])


def downgrade() -> None:
    op.drop_constraint("uq_users_anonnymous_name", "users", type_="unique")
    op.drop_column("users", "is_admin")
    op.drop_column("users", "is_active")
    op.drop_column("users", "refresh_token_jti")
    op.drop_column("users", "hashed_password")
    op.drop_column("users", "anonnymous_name")
