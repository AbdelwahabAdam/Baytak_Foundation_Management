"""Add tasks for admin assignment and status tracking.

Revision ID: 0005_tasks
Revises: 0004_activities_fund_custody
Create Date: 2026-07-24
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


revision: str = "0005_tasks"
down_revision: str | Sequence[str] | None = "0004_activities_fund_custody"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

task_status = postgresql.ENUM(
    "pending",
    "in_progress",
    "completed",
    "cancelled",
    name="task_status",
    create_type=False,
)
task_priority = postgresql.ENUM(
    "low",
    "medium",
    "high",
    name="task_priority",
    create_type=False,
)


def _create_enum(name: str, values: str) -> None:
    op.execute(
        f"""
        DO $$ BEGIN
            CREATE TYPE {name} AS ENUM ({values});
        EXCEPTION
            WHEN duplicate_object THEN null;
            WHEN unique_violation THEN null;
        END $$;
        """
    )


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    _create_enum("task_status", "'pending', 'in_progress', 'completed', 'cancelled'")
    _create_enum("task_priority", "'low', 'medium', 'high'")

    if not inspector.has_table("tasks"):
        op.create_table(
            "tasks",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("title", sa.String(length=200), nullable=False),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column(
                "status",
                task_status,
                nullable=False,
                server_default="pending",
            ),
            sa.Column(
                "priority",
                task_priority,
                nullable=False,
                server_default="medium",
            ),
            sa.Column("due_date", sa.DateTime(timezone=True), nullable=True),
            sa.Column("assigned_user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
            sa.Column("created_by_user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("now()"),
                nullable=False,
            ),
            sa.Column(
                "updated_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("now()"),
                nullable=False,
            ),
        )
        op.create_index("ix_tasks_title", "tasks", ["title"])
        op.create_index("ix_tasks_status", "tasks", ["status"])
        op.create_index("ix_tasks_due_date", "tasks", ["due_date"])
        op.create_index("ix_tasks_assigned_user_id", "tasks", ["assigned_user_id"])


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if inspector.has_table("tasks"):
        op.drop_index("ix_tasks_assigned_user_id", table_name="tasks")
        op.drop_index("ix_tasks_due_date", table_name="tasks")
        op.drop_index("ix_tasks_status", table_name="tasks")
        op.drop_index("ix_tasks_title", table_name="tasks")
        op.drop_table("tasks")
    op.execute("DROP TYPE IF EXISTS task_priority")
    op.execute("DROP TYPE IF EXISTS task_status")
