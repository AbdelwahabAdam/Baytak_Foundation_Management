"""Add warehouse and cases tables; standardize donations on EGP.

Revision ID: 0003_warehouse_cases_egp
Revises: 0002_password_reset_tokens
Create Date: 2026-07-22
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


revision: str = "0003_warehouse_cases_egp"
down_revision: str | Sequence[str] | None = "0002_password_reset_tokens"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

case_status = postgresql.ENUM(
    "open", "in_progress", "closed", "cancelled", name="case_status", create_type=False
)
case_priority = postgresql.ENUM(
    "low", "medium", "high", "urgent", name="case_priority", create_type=False
)


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    op.execute("UPDATE donations SET currency = 'EGP' WHERE currency IS DISTINCT FROM 'EGP'")
    op.alter_column(
        "donations",
        "currency",
        existing_type=sa.String(length=3),
        server_default="EGP",
        existing_nullable=False,
    )

    if not inspector.has_table("warehouse_items"):
        op.create_table(
            "warehouse_items",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("name", sa.String(length=150), nullable=False),
            sa.Column("sku", sa.String(length=80), nullable=True, unique=True),
            sa.Column("quantity", sa.Numeric(14, 2), nullable=False, server_default="0"),
            sa.Column("unit", sa.String(length=40), nullable=False, server_default="piece"),
            sa.Column("location", sa.String(length=150), nullable=True),
            sa.Column("notes", sa.Text(), nullable=True),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        )
        op.create_index("ix_warehouse_items_name", "warehouse_items", ["name"])

    if not inspector.has_table("aid_cases"):
        op.execute(
            """
            DO $$ BEGIN
                CREATE TYPE case_status AS ENUM ('open', 'in_progress', 'closed', 'cancelled');
            EXCEPTION
                WHEN duplicate_object THEN null;
            END $$;
            """
        )
        op.execute(
            """
            DO $$ BEGIN
                CREATE TYPE case_priority AS ENUM ('low', 'medium', 'high', 'urgent');
            EXCEPTION
                WHEN duplicate_object THEN null;
            END $$;
            """
        )
        op.create_table(
            "aid_cases",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("case_number", sa.String(length=50), nullable=False, unique=True),
            sa.Column("beneficiary_name", sa.String(length=200), nullable=False),
            sa.Column("phone", sa.String(length=50), nullable=True),
            sa.Column("category", sa.String(length=100), nullable=False),
            sa.Column("status", case_status, nullable=False, server_default="open"),
            sa.Column("priority", case_priority, nullable=False, server_default="medium"),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("requested_amount", sa.Numeric(14, 2), nullable=True),
            sa.Column("approved_amount", sa.Numeric(14, 2), nullable=True),
            sa.Column("created_by_user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
            sa.Column("assigned_user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        )
        op.create_index("ix_aid_cases_case_number", "aid_cases", ["case_number"])
        op.create_index("ix_aid_cases_beneficiary_name", "aid_cases", ["beneficiary_name"])
        op.create_index("ix_aid_cases_category", "aid_cases", ["category"])
        op.create_index("ix_aid_cases_status", "aid_cases", ["status"])
        op.create_index("ix_aid_cases_assigned_user_id", "aid_cases", ["assigned_user_id"])


def downgrade() -> None:
    op.drop_index("ix_aid_cases_assigned_user_id", table_name="aid_cases")
    op.drop_index("ix_aid_cases_status", table_name="aid_cases")
    op.drop_index("ix_aid_cases_category", table_name="aid_cases")
    op.drop_index("ix_aid_cases_beneficiary_name", table_name="aid_cases")
    op.drop_index("ix_aid_cases_case_number", table_name="aid_cases")
    op.drop_table("aid_cases")
    op.execute("DROP TYPE IF EXISTS case_priority")
    op.execute("DROP TYPE IF EXISTS case_status")
    op.drop_index("ix_warehouse_items_name", table_name="warehouse_items")
    op.drop_table("warehouse_items")
    op.alter_column(
        "donations",
        "currency",
        existing_type=sa.String(length=3),
        server_default="USD",
        existing_nullable=False,
    )
