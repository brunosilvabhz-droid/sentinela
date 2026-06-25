from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import create_access_token, verify_password
from app.models.user import User


def authenticate_user(db: Session, email: str, password: str) -> str:
    user = db.query(User).filter(User.email == email, User.is_active.is_(True)).first()
    if not user or not verify_password(password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Email ou senha invalidos")
    return create_access_token(subject=str(user.id), tenant_id=user.tenant_id, role=user.role)
