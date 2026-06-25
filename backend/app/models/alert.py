from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, JSON, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class Alert(Base):
    __tablename__ = "alerts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id"), index=True, nullable=False)
    data_source_id: Mapped[int] = mapped_column(ForeignKey("data_sources.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    column_name: Mapped[str] = mapped_column(String(160), nullable=False)
    condition: Mapped[str] = mapped_column(String(8), nullable=False)
    threshold_value: Mapped[str] = mapped_column(String(255), nullable=False)
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
    status: Mapped[str] = mapped_column(String(30), nullable=False)
    matched_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    sample_records: Mapped[list | None] = mapped_column(JSON, nullable=True)
    channels: Mapped[list | None] = mapped_column(JSON, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)

    alert = relationship("Alert", back_populates="executions")
