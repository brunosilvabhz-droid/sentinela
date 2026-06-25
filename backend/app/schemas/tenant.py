from datetime import datetime

from pydantic import BaseModel

from app.schemas.common import ORMModel


class TenantCreate(BaseModel):
    name: str
    document: str | None = None
    plan: str = "free"
    max_alerts: int = 5


class TenantRead(ORMModel):
    id: int
    name: str
    document: str | None
    plan: str
    max_alerts: int
    is_active: bool
    created_at: datetime
