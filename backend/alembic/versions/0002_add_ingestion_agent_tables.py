"""add ingestion agent tables

Revision ID: 0002_add_ingestion_agent_tables
Revises: 0001_initial_schema
Create Date: 2026-06-25 00:00:01.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0002_add_ingestion_agent_tables"
down_revision: Union[str, None] = "0001_initial_schema"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "collector_agents",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=160), nullable=False),
        sa.Column("token_hash", sa.String(length=128), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("token_hash"),
    )
    op.create_index(op.f("ix_collector_agents_id"), "collector_agents", ["id"], unique=False)
    op.create_index(op.f("ix_collector_agents_tenant_id"), "collector_agents", ["tenant_id"], unique=False)

    op.create_table(
        "ingestion_batches",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.Column("data_source_id", sa.Integer(), nullable=False),
        sa.Column("agent_id", sa.Integer(), nullable=True),
        sa.Column("idempotency_key", sa.String(length=160), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("record_count", sa.Integer(), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("received_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["agent_id"], ["collector_agents.id"]),
        sa.ForeignKeyConstraint(["data_source_id"], ["data_sources.id"]),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "data_source_id", "idempotency_key", name="uq_ingestion_batch_idempotency"),
    )
    op.create_index(op.f("ix_ingestion_batches_data_source_id"), "ingestion_batches", ["data_source_id"], unique=False)
    op.create_index(op.f("ix_ingestion_batches_id"), "ingestion_batches", ["id"], unique=False)
    op.create_index(op.f("ix_ingestion_batches_tenant_id"), "ingestion_batches", ["tenant_id"], unique=False)

    op.create_table(
        "ingested_records",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.Column("data_source_id", sa.Integer(), nullable=False),
        sa.Column("batch_id", sa.Integer(), nullable=False),
        sa.Column("source_record_id", sa.String(length=255), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("collected_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ingested_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["batch_id"], ["ingestion_batches.id"]),
        sa.ForeignKeyConstraint(["data_source_id"], ["data_sources.id"]),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "data_source_id", "source_record_id", name="uq_ingested_record_source_id"),
    )
    op.create_index(op.f("ix_ingested_records_data_source_id"), "ingested_records", ["data_source_id"], unique=False)
    op.create_index(op.f("ix_ingested_records_id"), "ingested_records", ["id"], unique=False)
    op.create_index(op.f("ix_ingested_records_tenant_id"), "ingested_records", ["tenant_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_ingested_records_tenant_id"), table_name="ingested_records")
    op.drop_index(op.f("ix_ingested_records_id"), table_name="ingested_records")
    op.drop_index(op.f("ix_ingested_records_data_source_id"), table_name="ingested_records")
    op.drop_table("ingested_records")
    op.drop_index(op.f("ix_ingestion_batches_tenant_id"), table_name="ingestion_batches")
    op.drop_index(op.f("ix_ingestion_batches_id"), table_name="ingestion_batches")
    op.drop_index(op.f("ix_ingestion_batches_data_source_id"), table_name="ingestion_batches")
    op.drop_table("ingestion_batches")
    op.drop_index(op.f("ix_collector_agents_tenant_id"), table_name="collector_agents")
    op.drop_index(op.f("ix_collector_agents_id"), table_name="collector_agents")
    op.drop_table("collector_agents")
