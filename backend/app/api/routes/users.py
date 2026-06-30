from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_admin
from app.core.security import hash_password
from app.db.session import get_db
from app.models.tenant import Tenant
from app.models.user import User
from app.schemas.user import UserCreate, UserRead, UserUpdate

router = APIRouter(prefix="/users", tags=["users"])


@router.get("", response_model=list[UserRead])
def list_users(
    tenant_id: int | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> list[User]:
    target_tenant_id = resolve_user_tenant_id(current_user, tenant_id)
    return db.query(User).filter(User.tenant_id == target_tenant_id).all()


@router.post("", response_model=UserRead)
def create_user(
    payload: UserCreate,
    tenant_id: int | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> User:
    target_tenant_id = resolve_user_tenant_id(current_user, tenant_id or payload.tenant_id)
    if payload.role not in {"admin", "user"}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Perfil invalido")
    if db.query(User).filter(User.email == payload.email).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email ja cadastrado")
    if not db.query(Tenant).filter(Tenant.id == target_tenant_id).first():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Empresa nao encontrada")
    user = User(
        tenant_id=target_tenant_id,
        name=payload.name,
        email=payload.email,
        hashed_password=hash_password(payload.password),
        role=payload.role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.get("/me", response_model=UserRead)
def read_me(current_user: User = Depends(get_current_user)) -> User:
    return current_user


@router.patch("/{user_id}", response_model=UserRead)
def update_user(
    user_id: int,
    payload: UserUpdate,
    tenant_id: int | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> User:
    target_tenant_id = resolve_user_tenant_id(current_user, tenant_id)
    user = db.query(User).filter(User.id == user_id, User.tenant_id == target_tenant_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario nao encontrado")
    if payload.role and payload.role not in {"admin", "user"}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Perfil invalido")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(user, key, value)
    db.commit()
    db.refresh(user)
    return user


def resolve_user_tenant_id(current_user: User, tenant_id: int | None) -> int:
    if current_user.role == "super_admin":
        if tenant_id is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="tenant_id e obrigatorio para admin geral")
        return tenant_id
    return current_user.tenant_id
