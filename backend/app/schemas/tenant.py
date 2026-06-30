from datetime import datetime

from pydantic import BaseModel
from pydantic import computed_field

from app.schemas.common import ORMModel


class TenantCreate(BaseModel):
    name: str
    document: str | None = None
    plan: str = "free"
    max_sources: int = 3
    max_alerts: int = 5
    max_upload_mb: int = 10
    data_retention_days: int = 90
    whatsapp_provider: str = "meta"
    meta_whatsapp_token: str | None = None
    meta_whatsapp_phone_number_id: str | None = None
    meta_whatsapp_api_version: str = "v20.0"
    meta_whatsapp_template_name: str | None = None
    meta_whatsapp_template_language: str = "pt_BR"
    whatsapp_is_active: bool = True


class TenantSignup(BaseModel):
    company_name: str
    document: str | None = None
    plan: str = "free"
    max_sources: int = 3
    max_alerts: int = 5
    max_upload_mb: int = 10
    data_retention_days: int = 90
    whatsapp_provider: str = "meta"
    meta_whatsapp_token: str | None = None
    meta_whatsapp_phone_number_id: str | None = None
    meta_whatsapp_api_version: str = "v20.0"
    meta_whatsapp_template_name: str | None = None
    meta_whatsapp_template_language: str = "pt_BR"
    whatsapp_is_active: bool = True
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
    whatsapp_provider: str | None = None
    meta_whatsapp_token: str | None = None
    meta_whatsapp_phone_number_id: str | None = None
    meta_whatsapp_api_version: str | None = None
    meta_whatsapp_template_name: str | None = None
    meta_whatsapp_template_language: str | None = None
    whatsapp_is_active: bool | None = None
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
    whatsapp_provider: str
    meta_whatsapp_phone_number_id: str | None
    meta_whatsapp_api_version: str
    meta_whatsapp_template_name: str | None
    meta_whatsapp_template_language: str
    whatsapp_is_active: bool
    is_active: bool
    created_at: datetime

    @computed_field
    @property
    def whatsapp_configured(self) -> bool:
        return bool(self.meta_whatsapp_phone_number_id)
