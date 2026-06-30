"""alert message templates

Revision ID: 0007_alert_message_templates
Revises: 0006_app_settings
Create Date: 2026-06-30 00:00:02.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0007_alert_message_templates"
down_revision: Union[str, None] = "0006_app_settings"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = {column["name"] for column in inspector.get_columns("alerts")}
    if "template_type" not in columns:
        op.add_column(
            "alerts",
            sa.Column("template_type", sa.String(length=80), server_default="custom", nullable=False),
        )
    if "message_template" not in columns:
        op.add_column("alerts", sa.Column("message_template", sa.Text(), nullable=True))
    if "message_variables" not in columns:
        op.add_column("alerts", sa.Column("message_variables", sa.JSON(), nullable=True))


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = {column["name"] for column in inspector.get_columns("alerts")}
    if "message_variables" in columns:
        op.drop_column("alerts", "message_variables")
    if "message_template" in columns:
        op.drop_column("alerts", "message_template")
    if "template_type" in columns:
        op.drop_column("alerts", "template_type")
