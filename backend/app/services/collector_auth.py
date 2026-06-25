import hashlib
import secrets
from datetime import datetime, timezone

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.collector import CollectorAgent


def generate_agent_token() -> str:
    return f"sentinela_agent_{secrets.token_urlsafe(32)}"


def hash_agent_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def authenticate_agent(
    token: str | None = Header(default=None, alias="X-Agent-Token"),
    db: Session = Depends(get_db),
) -> CollectorAgent:
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="X-Agent-Token obrigatorio")
    token_hash = hash_agent_token(token)
    agent = (
        db.query(CollectorAgent)
        .filter(CollectorAgent.token_hash == token_hash, CollectorAgent.is_active.is_(True))
        .first()
    )
    if not agent:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Agent token invalido")
    agent.last_seen_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(agent)
    return agent
