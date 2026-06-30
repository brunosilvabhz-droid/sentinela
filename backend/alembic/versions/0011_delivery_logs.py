"""delivery logs

Revision ID: 0011_delivery_logs
Revises: 0010_tenant_whatsapp
Create Date: 2026-06-30 00:00:06.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0011_delivery_logs"
down_revision: Union[str, None] = "0010_tenant_whatsapp"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "alert_delivery_logs" not in inspector.get_table_names():
        op.create_table(
            "alert_delivery_logs",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("tenant_id", sa.Integer(), nullable=False),
            sa.Column("alert_id", sa.Integer(), nullable=True),
            sa.Column("occurrence_id", sa.Integer(), nullable=True),
            sa.Column("channel", sa.String(length=30), nullable=False),
            sa.Column("recipient", sa.String(length=255), nullable=False),
            sa.Column("status", sa.String(length=30), nullable=False),
            sa.Column("provider", sa.String(length=60), nullable=True),
            sa.Column("error_message", sa.Text(), nullable=True),
            sa.Column("sent_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
            sa.ForeignKeyConstraint(["alert_id"], ["alerts.id"]),
            sa.ForeignKeyConstraint(["occurrence_id"], ["alert_occurrences.id"]),
            sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(op.f("ix_alert_delivery_logs_id"), "alert_delivery_logs", ["id"], unique=False)
        op.create_index(op.f("ix_alert_delivery_logs_tenant_id"), "alert_delivery_logs", ["tenant_id"], unique=False)


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "alert_delivery_logs" in inspector.get_table_names():
        op.drop_index(op.f("ix_alert_delivery_logs_tenant_id"), table_name="alert_delivery_logs")
        op.drop_index(op.f("ix_alert_delivery_logs_id"), table_name="alert_delivery_logs")
        op.drop_table("alert_delivery_logs")
