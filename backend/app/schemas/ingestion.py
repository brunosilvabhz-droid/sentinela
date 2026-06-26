from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.common import ORMModel


class CollectorAgentCreate(BaseModel):
    tenant_id: int | None = None
    name: str


class CollectorAgentCreateResponse(ORMModel):
    id: int
    tenant_id: int
    name: str
    token: str
    is_active: bool
    created_at: datetime


class CollectorAgentRead(ORMModel):
    id: int
    tenant_id: int
    name: str
    is_active: bool
    last_seen_at: datetime | None
    created_at: datetime


class IngestionRecordIn(BaseModel):
    source_record_id: str
    payload: dict
    collected_at: datetime | None = None


class IngestionBatchCreate(BaseModel):
    data_source_id: int
    idempotency_key: str = Field(min_length=8, max_length=160)
    records: list[IngestionRecordIn]


class IngestionBatchRead(ORMModel):
    id: int
    tenant_id: int
    data_source_id: int
    agent_id: int | None
    idempotency_key: str
    status: str
    record_count: int
    error_message: str | None
    received_at: datetime
