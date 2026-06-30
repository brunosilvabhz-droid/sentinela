"""tenant whatsapp settings

Revision ID: 0010_tenant_whatsapp
Revises: 0009_tenant_data_limits
Create Date: 2026-06-30 00:00:05.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0010_tenant_whatsapp"
down_revision: Union[str, None] = "0009_tenant_data_limits"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = {column["name"] for column in inspector.get_columns("tenants")}
    if "whatsapp_provider" not in columns:
        op.add_column("tenants", sa.Column("whatsapp_provider", sa.String(length=30), server_default="meta", nullable=False))
    if "meta_whatsapp_token" not in columns:
        op.add_column("tenants", sa.Column("meta_whatsapp_token", sa.Text(), nullable=True))
    if "meta_whatsapp_phone_number_id" not in columns:
        op.add_column("tenants", sa.Column("meta_whatsapp_phone_number_id", sa.String(length=120), nullable=True))
    if "meta_whatsapp_api_version" not in columns:
        op.add_column("tenants", sa.Column("meta_whatsapp_api_version", sa.String(length=20), server_default="v20.0", nullable=False))
    if "meta_whatsapp_template_name" not in columns:
        op.add_column("tenants", sa.Column("meta_whatsapp_template_name", sa.String(length=120), nullable=True))
    if "meta_whatsapp_template_language" not in columns:
        op.add_column("tenants", sa.Column("meta_whatsapp_template_language", sa.String(length=20), server_default="pt_BR", nullable=False))
    if "whatsapp_is_active" not in columns:
        op.add_column("tenants", sa.Column("whatsapp_is_active", sa.Boolean(), server_default=sa.true(), nullable=False))


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = {column["name"] for column in inspector.get_columns("tenants")}
    for column_name in [
        "whatsapp_is_active",
        "meta_whatsapp_template_language",
        "meta_whatsapp_template_name",
        "meta_whatsapp_api_version",
        "meta_whatsapp_phone_number_id",
        "meta_whatsapp_token",
        "whatsapp_provider",
    ]:
        if column_name in columns:
            op.drop_column("tenants", column_name)
