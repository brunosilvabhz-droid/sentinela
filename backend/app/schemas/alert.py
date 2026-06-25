from datetime import datetime

from pydantic import BaseModel

from app.schemas.common import ORMModel


class AlertCreate(BaseModel):
    data_source_id: int
    name: str
    column_name: str
    condition: str
    threshold_value: str
    frequency: str = "*/15 * * * *"
    recipients: list[str]
    channels: list[str]


class AlertUpdate(BaseModel):
    name: str | None = None
    column_name: str | None = None
    condition: str | None = None
    threshold_value: str | None = None
    frequency: str | None = None
    recipients: list[str] | None = None
    channels: list[str] | None = None
    is_active: bool | None = None


class AlertRead(ORMModel):
    id: int
    tenant_id: int
    data_source_id: int
    name: str
    column_name: str
    condition: str
    threshold_value: str
    frequency: str
    recipients: list[str]
    channels: list[str]
    is_active: bool
    created_at: datetime
    last_run_at: datetime | None


class AlertExecutionRead(ORMModel):
    id: int
    tenant_id: int
    alert_id: int
    status: str
    matched_count: int
    sample_records: list | None
    channels: list | None
    error_message: str | None
    started_at: datetime
    finished_at: datetime | None
    duration_ms: int | None


class AlertExecutionWithAlertRead(AlertExecutionRead):
    alert_name: str
