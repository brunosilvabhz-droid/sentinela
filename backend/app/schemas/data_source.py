from datetime import datetime

from pydantic import BaseModel

from app.schemas.common import ORMModel


class DataSourceCreate(BaseModel):
    name: str
    source_type: str
    file_path: str | None = None
    connection_uri: str | None = None
    table_name: str | None = None
    config: dict | None = None


class DataSourceUpdate(BaseModel):
    name: str | None = None
    is_active: bool | None = None
    config: dict | None = None


class DataSourceRead(ORMModel):
    id: int
    tenant_id: int
    name: str
    source_type: str
    file_path: str | None
    connection_uri: str | None
    table_name: str | None
    config: dict | None
    is_active: bool
    created_at: datetime


class DataSourcePreview(BaseModel):
    columns: list[str]
    rows: list[dict]
    total_preview_rows: int
