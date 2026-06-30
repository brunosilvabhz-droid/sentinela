"""alert workflow and dynamic recipients

Revision ID: 0008_alert_workflow_dynamic
Revises: 0007_alert_message_templates
Create Date: 2026-06-30 00:00:03.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0008_alert_workflow_dynamic"
down_revision: Union[str, None] = "0007_alert_message_templates"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    alert_columns = {column["name"] for column in inspector.get_columns("alerts")}
    occurrence_columns = {column["name"] for column in inspector.get_columns("alert_occurrences")}
    if bind.dialect.name != "sqlite":
        op.alter_column("alerts", "condition", type_=sa.String(length=32), existing_type=sa.String(length=8))
    if "dynamic_email_column" not in alert_columns:
        op.add_column("alerts", sa.Column("dynamic_email_column", sa.String(length=160), nullable=True))
    if "dynamic_whatsapp_column" not in alert_columns:
        op.add_column("alerts", sa.Column("dynamic_whatsapp_column", sa.String(length=160), nullable=True))
    if "assigned_to" not in occurrence_columns:
        op.add_column("alert_occurrences", sa.Column("assigned_to", sa.String(length=160), nullable=True))
    if "resolution_note" not in occurrence_columns:
        op.add_column("alert_occurrences", sa.Column("resolution_note", sa.Text(), nullable=True))


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    alert_columns = {column["name"] for column in inspector.get_columns("alerts")}
    occurrence_columns = {column["name"] for column in inspector.get_columns("alert_occurrences")}
    if "resolution_note" in occurrence_columns:
        op.drop_column("alert_occurrences", "resolution_note")
    if "assigned_to" in occurrence_columns:
        op.drop_column("alert_occurrences", "assigned_to")
    if "dynamic_whatsapp_column" in alert_columns:
        op.drop_column("alerts", "dynamic_whatsapp_column")
    if "dynamic_email_column" in alert_columns:
        op.drop_column("alerts", "dynamic_email_column")
    if bind.dialect.name != "sqlite":
        op.alter_column("alerts", "condition", type_=sa.String(length=8), existing_type=sa.String(length=32))
