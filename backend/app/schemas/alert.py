from datetime import datetime

from pydantic import BaseModel

from app.schemas.common import ORMModel


class AlertRule(BaseModel):
    column_name: str
    condition: str
    threshold_value: str


class AlertCreate(BaseModel):
    data_source_id: int
    name: str
    column_name: str
    condition: str
    threshold_value: str
    rules: list[AlertRule] | None = None
    rule_logic: str = "AND"
    template_type: str = "custom"
    message_template: str | None = None
    message_variables: dict[str, str] | None = None
    dynamic_email_column: str | None = None
    dynamic_whatsapp_column: str | None = None
    frequency: str = "*/15 * * * *"
    recipients: list[str]
    channels: list[str]


class AlertUpdate(BaseModel):
    name: str | None = None
    column_name: str | None = None
    condition: str | None = None
    threshold_value: str | None = None
    rules: list[AlertRule] | None = None
    rule_logic: str | None = None
    template_type: str | None = None
    message_template: str | None = None
    message_variables: dict[str, str] | None = None
    dynamic_email_column: str | None = None
    dynamic_whatsapp_column: str | None = None
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
    rules: list[dict] | None = None
    rule_logic: str
    template_type: str
    message_template: str | None
    message_variables: dict | None
    dynamic_email_column: str | None
    dynamic_whatsapp_column: str | None
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
    occurrence_id: int | None = None
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


class AlertOccurrenceRead(ORMModel):
    id: int
    tenant_id: int
    alert_id: int
    fingerprint: str
    status: str
    matched_count: int
    sample_records: list | None
    first_seen_at: datetime
    last_seen_at: datetime
    acknowledged_at: datetime | None
    resolved_at: datetime | None
    assigned_to: str | None
    resolution_note: str | None
    alert_name: str | None = None


class AlertOccurrenceUpdate(BaseModel):
    status: str | None = None
    assigned_to: str | None = None
    resolution_note: str | None = None


class AlertSimulationRead(BaseModel):
    matched_count: int
    sample_records: list
    sample_messages: list[str]
    dynamic_recipients: list[dict[str, str]]


class AlertAcknowledgementCreate(BaseModel):
    acknowledged_by_name: str | None = None
    acknowledged_by_email: str | None = None
    note: str | None = None


class AlertAcknowledgementRead(ORMModel):
    id: int
    tenant_id: int
    alert_id: int
    occurrence_id: int
    acknowledged_by_name: str | None
    acknowledged_by_email: str | None
    note: str | None
    acknowledged_at: datetime
    alert_name: str | None = None


class AlertAuditLogRead(ORMModel):
    id: int
    tenant_id: int
    alert_id: int
    user_id: int | None
    action: str
    before: dict | None
    after: dict | None
    created_at: datetime
    alert_name: str | None = None


class PublicAlertOccurrenceRead(BaseModel):
    alert_name: str
    source_name: str
    status: str
    matched_count: int
    sample_records: list | None
