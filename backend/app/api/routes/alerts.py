from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.alert import Alert, AlertExecution
from app.models.data_source import DataSource
from app.models.user import User
from app.schemas.alert import AlertCreate, AlertExecutionRead, AlertRead, AlertUpdate
from app.services.rule_engine import execute_alert
from app.services.tenant_limits import assert_can_create_alert

router = APIRouter(prefix="/alerts", tags=["alerts"])


@router.get("", response_model=list[AlertRead])
def list_alerts(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[Alert]:
    return db.query(Alert).filter(Alert.tenant_id == current_user.tenant_id).all()


@router.post("", response_model=AlertRead)
def create_alert(
    payload: AlertCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Alert:
    assert_can_create_alert(db, current_user.tenant)
    data_source = (
        db.query(DataSource)
        .filter(DataSource.id == payload.data_source_id, DataSource.tenant_id == current_user.tenant_id)
        .first()
    )
    if not data_source:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Fonte nao encontrada")
    alert = Alert(tenant_id=current_user.tenant_id, **payload.model_dump())
    db.add(alert)
    db.commit()
    db.refresh(alert)
    return alert


@router.patch("/{alert_id}", response_model=AlertRead)
def update_alert(
    alert_id: int,
    payload: AlertUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Alert:
    alert = db.query(Alert).filter(Alert.id == alert_id, Alert.tenant_id == current_user.tenant_id).first()
    if not alert:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alerta nao encontrado")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(alert, key, value)
    db.commit()
    db.refresh(alert)
    return alert


@router.post("/{alert_id}/run", response_model=AlertExecutionRead)
def run_alert_now(
    alert_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AlertExecution:
    alert = db.query(Alert).filter(Alert.id == alert_id, Alert.tenant_id == current_user.tenant_id).first()
    if not alert:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alerta nao encontrado")
    return execute_alert(db, alert)


@router.get("/{alert_id}/executions", response_model=list[AlertExecutionRead])
def list_alert_executions(
    alert_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[AlertExecution]:
    return (
        db.query(AlertExecution)
        .filter(AlertExecution.alert_id == alert_id, AlertExecution.tenant_id == current_user.tenant_id)
        .order_by(AlertExecution.started_at.desc())
        .limit(100)
        .all()
    )
