from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import require_admin
from app.core.security import hash_password
from app.db.session import get_db
from app.models.tenant import Tenant
from app.models.user import User
from app.schemas.tenant import TenantCreate, TenantRead
from app.schemas.user import UserCreate, UserRead

router = APIRouter(prefix="/tenants", tags=["tenants"])


@router.post("", response_model=TenantRead)
def create_tenant(payload: TenantCreate, db: Session = Depends(get_db)) -> Tenant:
    tenant = Tenant(**payload.model_dump())
    db.add(tenant)
    db.commit()
    db.refresh(tenant)
    return tenant


@router.get("/me", response_model=TenantRead)
def read_my_tenant(current_user: User = Depends(require_admin)) -> Tenant:
    return current_user.tenant


@router.post("/{tenant_id}/users", response_model=UserRead)
def create_initial_or_tenant_user(
    tenant_id: int,
    payload: UserCreate,
    db: Session = Depends(get_db),
) -> User:
    if payload.tenant_id != tenant_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="tenant_id divergente")
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant nao encontrado")
    user = User(
        tenant_id=tenant_id,
        name=payload.name,
        email=payload.email,
        hashed_password=hash_password(payload.password),
        role=payload.role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
