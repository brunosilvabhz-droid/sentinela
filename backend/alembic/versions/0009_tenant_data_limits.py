"""tenant data limits

Revision ID: 0009_tenant_data_limits
Revises: 0008_alert_workflow_dynamic
Create Date: 2026-06-30 00:00:04.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0009_tenant_data_limits"
down_revision: Union[str, None] = "0008_alert_workflow_dynamic"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = {column["name"] for column in inspector.get_columns("tenants")}
    if "max_upload_mb" not in columns:
        op.add_column("tenants", sa.Column("max_upload_mb", sa.Integer(), server_default="10", nullable=False))
    if "data_retention_days" not in columns:
        op.add_column("tenants", sa.Column("data_retention_days", sa.Integer(), server_default="90", nullable=False))


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = {column["name"] for column in inspector.get_columns("tenants")}
    if "data_retention_days" in columns:
        op.drop_column("tenants", "data_retention_days")
    if "max_upload_mb" in columns:
        op.drop_column("tenants", "max_upload_mb")
