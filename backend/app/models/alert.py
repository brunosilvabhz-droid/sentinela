from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, JSON, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class Alert(Base):
    __tablename__ = "alerts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id"), index=True, nullable=False)
    data_source_id: Mapped[int] = mapped_column(ForeignKey("data_sources.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    column_name: Mapped[str] = mapped_column(String(160), nullable=False)
    condition: Mapped[str] = mapped_column(String(32), nullable=False)
    threshold_value: Mapped[str] = mapped_column(String(255), nullable=False)
    rules: Mapped[list | None] = mapped_column(JSON, nullable=True)
    rule_logic: Mapped[str] = mapped_column(String(3), default="AND", nullable=False)
    template_type: Mapped[str] = mapped_column(String(80), default="custom", nullable=False)
    message_template: Mapped[str | None] = mapped_column(Text, nullable=True)
    message_variables: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    dynamic_email_column: Mapped[str | None] = mapped_column(String(160), nullable=True)
    dynamic_whatsapp_column: Mapped[str | None] = mapped_column(String(160), nullable=True)
    frequency: Mapped[str] = mapped_column(String(120), default="*/15 * * * *", nullable=False)
    recipients: Mapped[list] = mapped_column(JSON, nullable=False)
    channels: Mapped[list] = mapped_column(JSON, nullable=False)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    last_run_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    tenant = relationship("Tenant", back_populates="alerts")
    data_source = relationship("DataSource", back_populates="alerts")
    executions = relationship("AlertExecution", back_populates="alert")


class AlertExecution(Base):
    __tablename__ = "alert_executions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id"), index=True, nullable=False)
    alert_id: Mapped[int] = mapped_column(ForeignKey("alerts.id"), nullable=False)
    occurrence_id: Mapped[int | None] = mapped_column(ForeignKey("alert_occurrences.id"), nullable=True)
    status: Mapped[str] = mapped_column(String(30), nullable=False)
    matched_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    sample_records: Mapped[list | None] = mapped_column(JSON, nullable=True)
    channels: Mapped[list | None] = mapped_column(JSON, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)

    alert = relationship("Alert", back_populates="executions")
    occurrence = relationship("AlertOccurrence")


class AlertOccurrence(Base):
    __tablename__ = "alert_occurrences"
    __table_args__ = (
        UniqueConstraint("tenant_id", "alert_id", "fingerprint", name="uq_alert_occurrence_fingerprint"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id"), index=True, nullable=False)
    alert_id: Mapped[int] = mapped_column(ForeignKey("alerts.id"), index=True, nullable=False)
    fingerprint: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    ack_token: Mapped[str] = mapped_column(String(96), unique=True, index=True, nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="open", nullable=False)
    matched_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    sample_records: Mapped[list | None] = mapped_column(JSON, nullable=True)
    first_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    acknowledged_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    assigned_to: Mapped[str | None] = mapped_column(String(160), nullable=True)
    resolution_note: Mapped[str | None] = mapped_column(Text, nullable=True)

    alert = relationship("Alert")


class AlertAcknowledgement(Base):
    __tablename__ = "alert_acknowledgements"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id"), index=True, nullable=False)
    alert_id: Mapped[int] = mapped_column(ForeignKey("alerts.id"), index=True, nullable=False)
    occurrence_id: Mapped[int] = mapped_column(ForeignKey("alert_occurrences.id"), index=True, nullable=False)
    acknowledged_by_name: Mapped[str | None] = mapped_column(String(160), nullable=True)
    acknowledged_by_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    acknowledged_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    alert = relationship("Alert")
    occurrence = relationship("AlertOccurrence")


class AlertAuditLog(Base):
    __tablename__ = "alert_audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id"), index=True, nullable=False)
    alert_id: Mapped[int] = mapped_column(ForeignKey("alerts.id"), index=True, nullable=False)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    action: Mapped[str] = mapped_column(String(40), nullable=False)
    before: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    after: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    alert = relationship("Alert")


class AlertDeliveryLog(Base):
    __tablename__ = "alert_delivery_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id"), index=True, nullable=False)
    alert_id: Mapped[int | None] = mapped_column(ForeignKey("alerts.id"), nullable=True)
    occurrence_id: Mapped[int | None] = mapped_column(ForeignKey("alert_occurrences.id"), nullable=True)
    channel: Mapped[str] = mapped_column(String(30), nullable=False)
    recipient: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False)
    provider: Mapped[str | None] = mapped_column(String(60), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    sent_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    alert = relationship("Alert")
    occurrence = relationship("AlertOccurrence")
