"""Add financial activities, ledgers, and fund-based custody links.

Revision ID: 0004_activities_fund_custody
Revises: 0003_warehouse_cases_egp
Create Date: 2026-07-23
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


revision: str = "0004_activities_fund_custody"
down_revision: str | Sequence[str] | None = "0003_warehouse_cases_egp"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

activity_status = postgresql.ENUM("active", "inactive", name="activity_status", create_type=False)
transaction_direction = postgresql.ENUM(
    "income", "expense", name="transaction_direction", create_type=False
)
activity_transaction_type = postgresql.ENUM(
    "donation",
    "sale",
    "grant",
    "manual_income",
    "manual_expense",
    "purchase",
    "salary",
    "maintenance",
    "utilities",
    "transportation",
    "marketing",
    "other",
    name="activity_transaction_type",
    create_type=False,
)
transaction_reference_type = postgresql.ENUM(
    "donation",
    "custody_expense",
    "manual",
    "sale",
    "grant",
    name="transaction_reference_type",
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

    _create_enum("activity_status", "'active', 'inactive'")
    _create_enum("transaction_direction", "'income', 'expense'")
    _create_enum(
        "activity_transaction_type",
        "'donation', 'sale', 'grant', 'manual_income', 'manual_expense', "
        "'purchase', 'salary', 'maintenance', 'utilities', 'transportation', 'marketing', 'other'",
    )
    _create_enum(
        "transaction_reference_type",
        "'donation', 'custody_expense', 'manual', 'sale', 'grant'",
    )

    if not inspector.has_table("activities"):
        op.create_table(
            "activities",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("name", sa.String(length=200), nullable=False, unique=True),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("activity_type", sa.String(length=100), nullable=False),
            sa.Column("status", activity_status, nullable=False, server_default="active"),
            sa.Column("created_by_user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        )
        op.create_index("ix_activities_name", "activities", ["name"])
        op.create_index("ix_activities_activity_type", "activities", ["activity_type"])
        op.create_index("ix_activities_status", "activities", ["status"])

    if not inspector.has_table("activity_transactions"):
        op.create_table(
            "activity_transactions",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("activity_id", sa.Integer(), sa.ForeignKey("activities.id"), nullable=False),
            sa.Column("transaction_direction", transaction_direction, nullable=False),
            sa.Column("transaction_type", activity_transaction_type, nullable=False),
            sa.Column("amount", sa.Numeric(14, 2), nullable=False),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("reference_type", transaction_reference_type, nullable=True),
            sa.Column("reference_id", sa.Integer(), nullable=True),
            sa.Column("transaction_date", sa.DateTime(timezone=True), nullable=False),
            sa.Column("created_by_user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        )
        op.create_index("ix_activity_transactions_activity_id", "activity_transactions", ["activity_id"])
        op.create_index("ix_activity_transactions_direction", "activity_transactions", ["transaction_direction"])
        op.create_index("ix_activity_transactions_type", "activity_transactions", ["transaction_type"])
        op.create_index("ix_activity_transactions_reference_id", "activity_transactions", ["reference_id"])
        op.create_index("ix_activity_transactions_date", "activity_transactions", ["transaction_date"])
        op.create_index(
            "ix_activity_transactions_activity_date",
            "activity_transactions",
            ["activity_id", "transaction_date"],
        )

    donation_columns = {col["name"] for col in inspector.get_columns("donations")}
    if "activity_id" not in donation_columns:
        op.add_column("donations", sa.Column("activity_id", sa.Integer(), nullable=True))
        op.create_foreign_key(
            "fk_donations_activity_id",
            "donations",
            "activities",
            ["activity_id"],
            ["id"],
        )
        op.create_index("ix_donations_activity_id", "donations", ["activity_id"])

    custody_columns = {col["name"] for col in inspector.get_columns("custody_assignments")}
    if "donation_type_id" not in custody_columns:
        op.add_column("custody_assignments", sa.Column("donation_type_id", sa.Integer(), nullable=True))
        op.create_foreign_key(
            "fk_custody_assignments_donation_type_id",
            "custody_assignments",
            "donation_types",
            ["donation_type_id"],
            ["id"],
        )
        op.create_index("ix_custody_assignments_donation_type_id", "custody_assignments", ["donation_type_id"])
    if "activity_id" not in custody_columns:
        op.add_column("custody_assignments", sa.Column("activity_id", sa.Integer(), nullable=True))
        op.create_foreign_key(
            "fk_custody_assignments_activity_id",
            "custody_assignments",
            "activities",
            ["activity_id"],
            ["id"],
        )
        op.create_index("ix_custody_assignments_activity_id", "custody_assignments", ["activity_id"])

    # Backfill fund for existing assignments so fund-based custody remains consistent.
    op.execute(
        """
        UPDATE custody_assignments
        SET donation_type_id = (
            SELECT id FROM donation_types ORDER BY id ASC LIMIT 1
        )
        WHERE donation_type_id IS NULL
          AND EXISTS (SELECT 1 FROM donation_types)
        """
    )

    expense_columns = {col["name"] for col in inspector.get_columns("custody_expenses")}
    if "activity_id" not in expense_columns:
        op.add_column("custody_expenses", sa.Column("activity_id", sa.Integer(), nullable=True))
        op.create_foreign_key(
            "fk_custody_expenses_activity_id",
            "custody_expenses",
            "activities",
            ["activity_id"],
            ["id"],
        )
        op.create_index("ix_custody_expenses_activity_id", "custody_expenses", ["activity_id"])
        op.execute(
            """
            UPDATE custody_expenses ce
            SET activity_id = ca.activity_id
            FROM custody_assignments ca
            WHERE ce.custody_assignment_id = ca.id
              AND ce.activity_id IS NULL
            """
        )


def downgrade() -> None:
    op.drop_constraint("fk_custody_expenses_activity_id", "custody_expenses", type_="foreignkey")
    op.drop_index("ix_custody_expenses_activity_id", table_name="custody_expenses")
    op.drop_column("custody_expenses", "activity_id")

    op.drop_constraint("fk_custody_assignments_activity_id", "custody_assignments", type_="foreignkey")
    op.drop_index("ix_custody_assignments_activity_id", table_name="custody_assignments")
    op.drop_column("custody_assignments", "activity_id")

    op.drop_constraint("fk_custody_assignments_donation_type_id", "custody_assignments", type_="foreignkey")
    op.drop_index("ix_custody_assignments_donation_type_id", table_name="custody_assignments")
    op.drop_column("custody_assignments", "donation_type_id")

    op.drop_constraint("fk_donations_activity_id", "donations", type_="foreignkey")
    op.drop_index("ix_donations_activity_id", table_name="donations")
    op.drop_column("donations", "activity_id")

    op.drop_index("ix_activity_transactions_activity_date", table_name="activity_transactions")
    op.drop_index("ix_activity_transactions_date", table_name="activity_transactions")
    op.drop_index("ix_activity_transactions_reference_id", table_name="activity_transactions")
    op.drop_index("ix_activity_transactions_type", table_name="activity_transactions")
    op.drop_index("ix_activity_transactions_direction", table_name="activity_transactions")
    op.drop_index("ix_activity_transactions_activity_id", table_name="activity_transactions")
    op.drop_table("activity_transactions")

    op.drop_index("ix_activities_status", table_name="activities")
    op.drop_index("ix_activities_activity_type", table_name="activities")
    op.drop_index("ix_activities_name", table_name="activities")
    op.drop_table("activities")

    op.execute("DROP TYPE IF EXISTS transaction_reference_type")
    op.execute("DROP TYPE IF EXISTS activity_transaction_type")
    op.execute("DROP TYPE IF EXISTS transaction_direction")
    op.execute("DROP TYPE IF EXISTS activity_status")
