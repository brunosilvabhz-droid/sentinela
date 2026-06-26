"""alert acknowledgements and audit logs

Revision ID: 0004_alert_acknowledgements_and_audit
Revises: 0003_tenant_source_limits_and_attributes
Create Date: 2026-06-26 00:00:01.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0004_alert_ack_audit"
down_revision: Union[str, None] = "0003_tenant_limits"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = set(inspector.get_table_names())

    if "alert_occurrences" not in tables:
        op.create_table(
            "alert_occurrences",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("tenant_id", sa.Integer(), nullable=False),
            sa.Column("alert_id", sa.Integer(), nullable=False),
            sa.Column("fingerprint", sa.String(length=64), nullable=False),
            sa.Column("ack_token", sa.String(length=96), nullable=False),
            sa.Column("status", sa.String(length=30), nullable=False),
            sa.Column("matched_count", sa.Integer(), nullable=False),
            sa.Column("sample_records", sa.JSON(), nullable=True),
            sa.Column("first_seen_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column("last_seen_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column("acknowledged_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
            sa.ForeignKeyConstraint(["alert_id"], ["alerts.id"]),
            sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("tenant_id", "alert_id", "fingerprint", name="uq_alert_occurrence_fingerprint"),
            sa.UniqueConstraint("ack_token"),
        )
        op.create_index(op.f("ix_alert_occurrences_ack_token"), "alert_occurrences", ["ack_token"], unique=False)
        op.create_index(op.f("ix_alert_occurrences_alert_id"), "alert_occurrences", ["alert_id"], unique=False)
        op.create_index(op.f("ix_alert_occurrences_fingerprint"), "alert_occurrences", ["fingerprint"], unique=False)
        op.create_index(op.f("ix_alert_occurrences_id"), "alert_occurrences", ["id"], unique=False)
        op.create_index(op.f("ix_alert_occurrences_tenant_id"), "alert_occurrences", ["tenant_id"], unique=False)

    execution_columns = {column["name"] for column in inspector.get_columns("alert_executions")}
    if "occurrence_id" not in execution_columns:
        op.add_column("alert_executions", sa.Column("occurrence_id", sa.Integer(), nullable=True))

    tables = set(sa.inspect(bind).get_table_names())
    if "alert_acknowledgements" not in tables:
        op.create_table(
            "alert_acknowledgements",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("tenant_id", sa.Integer(), nullable=False),
            sa.Column("alert_id", sa.Integer(), nullable=False),
            sa.Column("occurrence_id", sa.Integer(), nullable=False),
            sa.Column("acknowledged_by_name", sa.String(length=160), nullable=True),
            sa.Column("acknowledged_by_email", sa.String(length=255), nullable=True),
            sa.Column("note", sa.Text(), nullable=True),
            sa.Column("acknowledged_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.ForeignKeyConstraint(["alert_id"], ["alerts.id"]),
            sa.ForeignKeyConstraint(["occurrence_id"], ["alert_occurrences.id"]),
            sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(op.f("ix_alert_acknowledgements_id"), "alert_acknowledgements", ["id"], unique=False)
        op.create_index(op.f("ix_alert_acknowledgements_occurrence_id"), "alert_acknowledgements", ["occurrence_id"], unique=False)
        op.create_index(op.f("ix_alert_acknowledgements_tenant_id"), "alert_acknowledgements", ["tenant_id"], unique=False)

    if "alert_audit_logs" not in tables:
        op.create_table(
            "alert_audit_logs",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("tenant_id", sa.Integer(), nullable=False),
            sa.Column("alert_id", sa.Integer(), nullable=False),
            sa.Column("user_id", sa.Integer(), nullable=True),
            sa.Column("action", sa.String(length=40), nullable=False),
            sa.Column("before", sa.JSON(), nullable=True),
            sa.Column("after", sa.JSON(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.ForeignKeyConstraint(["alert_id"], ["alerts.id"]),
            sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(op.f("ix_alert_audit_logs_id"), "alert_audit_logs", ["id"], unique=False)
        op.create_index(op.f("ix_alert_audit_logs_tenant_id"), "alert_audit_logs", ["tenant_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_alert_audit_logs_tenant_id"), table_name="alert_audit_logs")
    op.drop_index(op.f("ix_alert_audit_logs_id"), table_name="alert_audit_logs")
    op.drop_table("alert_audit_logs")
    op.drop_index(op.f("ix_alert_acknowledgements_tenant_id"), table_name="alert_acknowledgements")
    op.drop_index(op.f("ix_alert_acknowledgements_occurrence_id"), table_name="alert_acknowledgements")
    op.drop_index(op.f("ix_alert_acknowledgements_id"), table_name="alert_acknowledgements")
    op.drop_table("alert_acknowledgements")
    op.drop_column("alert_executions", "occurrence_id")
    op.drop_index(op.f("ix_alert_occurrences_tenant_id"), table_name="alert_occurrences")
    op.drop_index(op.f("ix_alert_occurrences_id"), table_name="alert_occurrences")
    op.drop_index(op.f("ix_alert_occurrences_fingerprint"), table_name="alert_occurrences")
    op.drop_index(op.f("ix_alert_occurrences_alert_id"), table_name="alert_occurrences")
    op.drop_index(op.f("ix_alert_occurrences_ack_token"), table_name="alert_occurrences")
    op.drop_table("alert_occurrences")
