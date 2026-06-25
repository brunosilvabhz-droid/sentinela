"""initial schema

Revision ID: 0001_initial_schema
Revises:
Create Date: 2026-06-25 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0001_initial_schema"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "tenants",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=160), nullable=False),
        sa.Column("document", sa.String(length=32), nullable=True),
        sa.Column("plan", sa.String(length=32), nullable=False),
        sa.Column("max_alerts", sa.Integer(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("document"),
    )
    op.create_index(op.f("ix_tenants_id"), "tenants", ["id"], unique=False)

    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("hashed_password", sa.String(length=255), nullable=False),
        sa.Column("role", sa.String(length=20), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "email", name="uq_users_tenant_email"),
    )
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=False)
    op.create_index(op.f("ix_users_id"), "users", ["id"], unique=False)
    op.create_index(op.f("ix_users_tenant_id"), "users", ["tenant_id"], unique=False)

    op.create_table(
        "data_sources",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=160), nullable=False),
        sa.Column("source_type", sa.String(length=30), nullable=False),
        sa.Column("file_path", sa.Text(), nullable=True),
        sa.Column("connection_uri", sa.Text(), nullable=True),
        sa.Column("table_name", sa.String(length=160), nullable=True),
        sa.Column("config", sa.JSON(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_data_sources_id"), "data_sources", ["id"], unique=False)
    op.create_index(op.f("ix_data_sources_tenant_id"), "data_sources", ["tenant_id"], unique=False)

    op.create_table(
        "alerts",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.Column("data_source_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=160), nullable=False),
        sa.Column("column_name", sa.String(length=160), nullable=False),
        sa.Column("condition", sa.String(length=8), nullable=False),
        sa.Column("threshold_value", sa.String(length=255), nullable=False),
        sa.Column("frequency", sa.String(length=120), nullable=False),
        sa.Column("recipients", sa.JSON(), nullable=False),
        sa.Column("channels", sa.JSON(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("last_run_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["data_source_id"], ["data_sources.id"]),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_alerts_id"), "alerts", ["id"], unique=False)
    op.create_index(op.f("ix_alerts_tenant_id"), "alerts", ["tenant_id"], unique=False)

    op.create_table(
        "alert_executions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.Column("alert_id", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("matched_count", sa.Integer(), nullable=False),
        sa.Column("sample_records", sa.JSON(), nullable=True),
        sa.Column("channels", sa.JSON(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("duration_ms", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["alert_id"], ["alerts.id"]),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_alert_executions_id"), "alert_executions", ["id"], unique=False)
    op.create_index(op.f("ix_alert_executions_tenant_id"), "alert_executions", ["tenant_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_alert_executions_tenant_id"), table_name="alert_executions")
    op.drop_index(op.f("ix_alert_executions_id"), table_name="alert_executions")
    op.drop_table("alert_executions")
    op.drop_index(op.f("ix_alerts_tenant_id"), table_name="alerts")
    op.drop_index(op.f("ix_alerts_id"), table_name="alerts")
    op.drop_table("alerts")
    op.drop_index(op.f("ix_data_sources_tenant_id"), table_name="data_sources")
    op.drop_index(op.f("ix_data_sources_id"), table_name="data_sources")
    op.drop_table("data_sources")
    op.drop_index(op.f("ix_users_tenant_id"), table_name="users")
    op.drop_index(op.f("ix_users_id"), table_name="users")
    op.drop_index(op.f("ix_users_email"), table_name="users")
    op.drop_table("users")
    op.drop_index(op.f("ix_tenants_id"), table_name="tenants")
    op.drop_table("tenants")
