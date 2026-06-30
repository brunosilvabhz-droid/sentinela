from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class Tenant(Base):
    __tablename__ = "tenants"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    document: Mapped[str | None] = mapped_column(String(32), unique=True, nullable=True)
    plan: Mapped[str] = mapped_column(String(32), default="free", nullable=False)
    max_sources: Mapped[int] = mapped_column(Integer, default=3, nullable=False)
    max_alerts: Mapped[int] = mapped_column(Integer, default=5, nullable=False)
    max_upload_mb: Mapped[int] = mapped_column(Integer, default=10, nullable=False)
    data_retention_days: Mapped[int] = mapped_column(Integer, default=90, nullable=False)
    whatsapp_provider: Mapped[str] = mapped_column(String(30), default="meta", nullable=False)
    meta_whatsapp_token: Mapped[str | None] = mapped_column(Text, nullable=True)
    meta_whatsapp_phone_number_id: Mapped[str | None] = mapped_column(String(120), nullable=True)
    meta_whatsapp_api_version: Mapped[str] = mapped_column(String(20), default="v20.0", nullable=False)
    meta_whatsapp_template_name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    meta_whatsapp_template_language: Mapped[str] = mapped_column(String(20), default="pt_BR", nullable=False)
    whatsapp_is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    users = relationship("User", back_populates="tenant")
    data_sources = relationship("DataSource", back_populates="tenant")
    alerts = relationship("Alert", back_populates="tenant")
