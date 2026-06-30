from datetime import datetime

from pydantic import BaseModel

from app.schemas.common import ORMModel


class TenantCreate(BaseModel):
    name: str
    document: str | None = None
    plan: str = "free"
    max_sources: int = 3
    max_alerts: int = 5
    max_upload_mb: int = 10
    data_retention_days: int = 90


class TenantSignup(BaseModel):
    company_name: str
    document: str | None = None
    plan: str = "free"
    max_sources: int = 3
    max_alerts: int = 5
    max_upload_mb: int = 10
    data_retention_days: int = 90
    admin_name: str
    admin_email: str
    admin_password: str


class TenantUpdate(BaseModel):
    name: str | None = None
    document: str | None = None
    plan: str | None = None
    max_sources: int | None = None
    max_alerts: int | None = None
    max_upload_mb: int | None = None
    data_retention_days: int | None = None
    is_active: bool | None = None


class TenantRead(ORMModel):
    id: int
    name: str
    document: str | None
    plan: str
    max_sources: int
    max_alerts: int
    max_upload_mb: int
    data_retention_days: int
    is_active: bool
    created_at: datetime
