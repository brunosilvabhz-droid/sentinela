from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.collector import IngestedAttribute, IngestedRecord, IngestionBatch
from app.models.tenant import Tenant


def purge_expired_ingestion_data(db: Session) -> dict[str, int]:
    totals = {"attributes": 0, "records": 0, "batches": 0}
    tenants = db.query(Tenant).filter(Tenant.is_active.is_(True)).all()
    for tenant in tenants:
        retention_days = max(int(tenant.data_retention_days or 90), 1)
        cutoff = datetime.now(timezone.utc) - timedelta(days=retention_days)
        record_ids = select(IngestedRecord.id).where(
            IngestedRecord.tenant_id == tenant.id,
            IngestedRecord.ingested_at < cutoff,
        )
        totals["attributes"] += (
            db.query(IngestedAttribute)
            .filter(IngestedAttribute.tenant_id == tenant.id, IngestedAttribute.record_id.in_(record_ids))
            .delete(synchronize_session=False)
        )
        totals["records"] += (
            db.query(IngestedRecord)
            .filter(IngestedRecord.tenant_id == tenant.id, IngestedRecord.ingested_at < cutoff)
            .delete(synchronize_session=False)
        )
        batch_ids_with_records = select(IngestedRecord.batch_id).where(IngestedRecord.tenant_id == tenant.id)
        totals["batches"] += (
            db.query(IngestionBatch)
            .filter(
                IngestionBatch.tenant_id == tenant.id,
                IngestionBatch.received_at < cutoff,
                ~IngestionBatch.id.in_(batch_ids_with_records),
            )
            .delete(synchronize_session=False)
        )
    db.commit()
    return totals
