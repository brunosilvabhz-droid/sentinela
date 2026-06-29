"""app settings

Revision ID: 0006_app_settings
Revises: 0005_alert_rules
Create Date: 2026-06-29 00:00:01.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0006_app_settings"
down_revision: Union[str, None] = "0005_alert_rules"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "app_settings" not in inspector.get_table_names():
        op.create_table(
            "app_settings",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("key", sa.String(length=80), nullable=False),
            sa.Column("value", sa.String(length=500), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("key"),
        )
        op.create_index(op.f("ix_app_settings_id"), "app_settings", ["id"], unique=False)
        op.create_index(op.f("ix_app_settings_key"), "app_settings", ["key"], unique=True)


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "app_settings" in inspector.get_table_names():
        op.drop_index(op.f("ix_app_settings_key"), table_name="app_settings")
        op.drop_index(op.f("ix_app_settings_id"), table_name="app_settings")
        op.drop_table("app_settings")
