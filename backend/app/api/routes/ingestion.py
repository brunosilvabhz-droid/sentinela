from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_admin
from app.db.session import get_db
from app.models.collector import CollectorAgent
from app.models.data_source import DataSource
from app.models.user import User
from app.schemas.data_source import DataSourceRead, ManagedDataSourceCreate
from app.schemas.ingestion import (
    CollectorAgentCreate,
    CollectorAgentCreateResponse,
    CollectorAgentRead,
    IngestionBatchCreate,
    IngestionBatchRead,
)
from app.services.collector_auth import authenticate_agent, generate_agent_token, hash_agent_token
from app.services.ingestion_service import ingest_batch

router = APIRouter(prefix="/ingestion", tags=["ingestion"])


@router.post("/sources", response_model=DataSourceRead)
def create_managed_source(
    payload: ManagedDataSourceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DataSource:
    data_source = DataSource(
        tenant_id=current_user.tenant_id,
        name=payload.name,
        source_type="managed",
        config=payload.config or {},
    )
    db.add(data_source)
    db.commit()
    db.refresh(data_source)
    return data_source


@router.post("/agents", response_model=CollectorAgentCreateResponse)
def create_collector_agent(
    payload: CollectorAgentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> dict:
    token = generate_agent_token()
    agent = CollectorAgent(
        tenant_id=current_user.tenant_id,
        name=payload.name,
        token_hash=hash_agent_token(token),
    )
    db.add(agent)
    db.commit()
    db.refresh(agent)
    return {
        "id": agent.id,
        "tenant_id": agent.tenant_id,
        "name": agent.name,
        "token": token,
        "is_active": agent.is_active,
        "created_at": agent.created_at,
    }


@router.get("/agents", response_model=list[CollectorAgentRead])
def list_collector_agents(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> list[CollectorAgent]:
    return db.query(CollectorAgent).filter(CollectorAgent.tenant_id == current_user.tenant_id).all()


@router.post("/batches", response_model=IngestionBatchRead)
def receive_ingestion_batch(
    payload: IngestionBatchCreate,
    db: Session = Depends(get_db),
    agent: CollectorAgent = Depends(authenticate_agent),
) -> IngestionBatchRead:
    try:
        return ingest_batch(db, agent, payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
