"""tenant source limits and ingested attributes

Revision ID: 0003_tenant_source_limits_and_attributes
Revises: 0002_add_ingestion_agent_tables
Create Date: 2026-06-26 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0003_tenant_limits"
down_revision: Union[str, None] = "0002_add_ingestion_agent_tables"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tenant_columns = {column["name"] for column in inspector.get_columns("tenants")}
    if "max_sources" not in tenant_columns:
        op.add_column("tenants", sa.Column("max_sources", sa.Integer(), nullable=False, server_default="3"))

    if "ingested_attributes" in inspector.get_table_names():
        return

    op.create_table(
        "ingested_attributes",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.Column("data_source_id", sa.Integer(), nullable=False),
        sa.Column("record_id", sa.Integer(), nullable=False),
        sa.Column("source_record_id", sa.String(length=255), nullable=False),
        sa.Column("attribute_name", sa.String(length=160), nullable=False),
        sa.Column("attribute_value", sa.Text(), nullable=True),
        sa.Column("attribute_type", sa.String(length=40), nullable=True),
        sa.Column("ingested_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["data_source_id"], ["data_sources.id"]),
        sa.ForeignKeyConstraint(["record_id"], ["ingested_records.id"]),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "data_source_id", "record_id", "attribute_name", name="uq_ingested_attribute_name"),
    )
    op.create_index(op.f("ix_ingested_attributes_attribute_name"), "ingested_attributes", ["attribute_name"], unique=False)
    op.create_index(op.f("ix_ingested_attributes_data_source_id"), "ingested_attributes", ["data_source_id"], unique=False)
    op.create_index(op.f("ix_ingested_attributes_id"), "ingested_attributes", ["id"], unique=False)
    op.create_index(op.f("ix_ingested_attributes_record_id"), "ingested_attributes", ["record_id"], unique=False)
    op.create_index(op.f("ix_ingested_attributes_source_record_id"), "ingested_attributes", ["source_record_id"], unique=False)
    op.create_index(op.f("ix_ingested_attributes_tenant_id"), "ingested_attributes", ["tenant_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_ingested_attributes_tenant_id"), table_name="ingested_attributes")
    op.drop_index(op.f("ix_ingested_attributes_source_record_id"), table_name="ingested_attributes")
    op.drop_index(op.f("ix_ingested_attributes_record_id"), table_name="ingested_attributes")
    op.drop_index(op.f("ix_ingested_attributes_id"), table_name="ingested_attributes")
    op.drop_index(op.f("ix_ingested_attributes_data_source_id"), table_name="ingested_attributes")
    op.drop_index(op.f("ix_ingested_attributes_attribute_name"), table_name="ingested_attributes")
    op.drop_table("ingested_attributes")
    op.drop_column("tenants", "max_sources")
