from sqlalchemy.orm import Session

from app.models.collector import CollectorAgent, IngestedAttribute, IngestedRecord, IngestionBatch
from app.models.data_source import DataSource
from app.schemas.ingestion import IngestionBatchCreate


def ingest_batch(db: Session, agent: CollectorAgent, payload: IngestionBatchCreate) -> IngestionBatch:
    data_source = (
        db.query(DataSource)
        .filter(
            DataSource.id == payload.data_source_id,
            DataSource.tenant_id == agent.tenant_id,
            DataSource.is_active.is_(True),
        )
        .first()
    )
    if not data_source:
        raise ValueError("Fonte nao encontrada ou inativa para este agent")

    existing = (
        db.query(IngestionBatch)
        .filter(
            IngestionBatch.tenant_id == agent.tenant_id,
            IngestionBatch.data_source_id == payload.data_source_id,
            IngestionBatch.idempotency_key == payload.idempotency_key,
        )
        .first()
    )
    if existing:
        return existing

    batch = IngestionBatch(
        tenant_id=agent.tenant_id,
        data_source_id=payload.data_source_id,
        agent_id=agent.id,
        idempotency_key=payload.idempotency_key,
        status="received",
        record_count=len(payload.records),
    )
    db.add(batch)
    db.flush()

    for record in payload.records:
        existing_record = (
            db.query(IngestedRecord)
            .filter(
                IngestedRecord.tenant_id == agent.tenant_id,
                IngestedRecord.data_source_id == payload.data_source_id,
                IngestedRecord.source_record_id == record.source_record_id,
            )
            .first()
        )
        if existing_record:
            existing_record.payload = record.payload
            existing_record.batch_id = batch.id
            existing_record.collected_at = record.collected_at
            db.flush()
            _replace_record_attributes(db, existing_record, record.payload)
        else:
            ingested_record = IngestedRecord(
                tenant_id=agent.tenant_id,
                data_source_id=payload.data_source_id,
                batch_id=batch.id,
                source_record_id=record.source_record_id,
                payload=record.payload,
                collected_at=record.collected_at,
            )
            db.add(ingested_record)
            db.flush()
            _replace_record_attributes(db, ingested_record, record.payload)

    db.commit()
    db.refresh(batch)
    return batch


def _replace_record_attributes(db: Session, record: IngestedRecord, payload: dict) -> None:
    db.query(IngestedAttribute).filter(IngestedAttribute.record_id == record.id).delete()
    for name, value in payload.items():
        db.add(
            IngestedAttribute(
                tenant_id=record.tenant_id,
                data_source_id=record.data_source_id,
                record_id=record.id,
                source_record_id=record.source_record_id,
                attribute_name=str(name),
                attribute_value=None if value is None else str(value),
                attribute_type=type(value).__name__ if value is not None else None,
            )
        )
