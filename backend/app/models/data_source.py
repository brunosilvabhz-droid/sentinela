from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, JSON, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class DataSource(Base):
    __tablename__ = "data_sources"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id"), index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    source_type: Mapped[str] = mapped_column(String(30), nullable=False)
    file_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    connection_uri: Mapped[str | None] = mapped_column(Text, nullable=True)
    table_name: Mapped[str | None] = mapped_column(String(160), nullable=True)
    config: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    tenant = relationship("Tenant", back_populates="data_sources")
    alerts = relationship("Alert", back_populates="data_source")
