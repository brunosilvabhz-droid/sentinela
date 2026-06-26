from datetime import datetime

from pydantic import BaseModel

from app.schemas.common import ORMModel


class TenantCreate(BaseModel):
    name: str
    document: str | None = None
    plan: str = "free"
    max_sources: int = 3
    max_alerts: int = 5


class TenantSignup(BaseModel):
    company_name: str
    document: str | None = None
    plan: str = "free"
    max_sources: int = 3
    max_alerts: int = 5
    admin_name: str
    admin_email: str
    admin_password: str


class TenantUpdate(BaseModel):
    name: str | None = None
    document: str | None = None
    plan: str | None = None
    max_sources: int | None = None
    max_alerts: int | None = None
    is_active: bool | None = None


class TenantRead(ORMModel):
    id: int
    name: str
    document: str | None
    plan: str
    max_sources: int
    max_alerts: int
    is_active: bool
    created_at: datetime
