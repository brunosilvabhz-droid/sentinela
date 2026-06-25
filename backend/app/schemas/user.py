from datetime import datetime

from pydantic import BaseModel, EmailStr, Field

from app.schemas.common import ORMModel


class UserCreate(BaseModel):
    tenant_id: int
    name: str
    email: EmailStr
    password: str = Field(min_length=8)
    role: str = "user"


class UserUpdate(BaseModel):
    name: str | None = None
    role: str | None = None
    is_active: bool | None = None


class UserRead(ORMModel):
    id: int
    tenant_id: int
    name: str
    email: EmailStr
    role: str
    is_active: bool
    created_at: datetime
