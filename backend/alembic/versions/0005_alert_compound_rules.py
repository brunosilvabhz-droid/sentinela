"""alert compound rules

Revision ID: 0005_alert_rules
Revises: 0004_alert_ack_audit
Create Date: 2026-06-29 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0005_alert_rules"
down_revision: Union[str, None] = "0004_alert_ack_audit"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = {column["name"] for column in inspector.get_columns("alerts")}

    if "rules" not in columns:
        op.add_column("alerts", sa.Column("rules", sa.JSON(), nullable=True))
    if "rule_logic" not in columns:
        op.add_column("alerts", sa.Column("rule_logic", sa.String(length=3), server_default="AND", nullable=False))


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = {column["name"] for column in inspector.get_columns("alerts")}

    if "rule_logic" in columns:
        op.drop_column("alerts", "rule_logic")
    if "rules" in columns:
        op.drop_column("alerts", "rules")
