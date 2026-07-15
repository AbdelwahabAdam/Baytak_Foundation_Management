"""Create the initial charity management schema.

Revision ID: 0001_initial_schema
Revises:
Create Date: 2026-07-15
"""

from collections.abc import Sequence

from alembic import op

from app.db import Base
import app.models  # noqa: F401 - register metadata


revision: str = "0001_initial_schema"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    Base.metadata.create_all(bind=op.get_bind())


def downgrade() -> None:
    Base.metadata.drop_all(bind=op.get_bind())
