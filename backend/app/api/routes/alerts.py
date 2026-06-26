from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_admin
from app.db.session import get_db
from app.models.alert import Alert, AlertExecution
from app.models.data_source import DataSource
from app.models.user import User
from app.schemas.alert import AlertCreate, AlertExecutionRead, AlertExecutionWithAlertRead, AlertRead, AlertUpdate
from app.services.rule_engine import execute_alert
from app.services.tenant_limits import assert_can_create_alert

router = APIRouter(prefix="/alerts", tags=["alerts"])


@router.get("", response_model=list[AlertRead])
def list_alerts(
    tenant_id: int | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> list[Alert]:
    target_tenant_id = resolve_tenant_id(current_user, tenant_id)
    return db.query(Alert).filter(Alert.tenant_id == target_tenant_id).all()


@router.get("/executions", response_model=list[AlertExecutionWithAlertRead])
def list_all_alert_executions(
    tenant_id: int | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[dict]:
    target_tenant_id = resolve_tenant_id(current_user, tenant_id)
    rows = (
        db.query(AlertExecution, Alert.name)
        .join(Alert, Alert.id == AlertExecution.alert_id)
        .filter(AlertExecution.tenant_id == target_tenant_id)
        .order_by(AlertExecution.started_at.desc())
        .limit(100)
        .all()
    )
    return [
        {
            **execution.__dict__,
            "alert_name": alert_name,
        }
        for execution, alert_name in rows
    ]


@router.post("", response_model=AlertRead)
def create_alert(
    payload: AlertCreate,
    tenant_id: int | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> Alert:
    target_tenant_id = resolve_tenant_id(current_user, tenant_id)
    tenant = current_user.tenant if current_user.tenant_id == target_tenant_id else None
    if tenant is None:
        from app.models.tenant import Tenant

        tenant = db.query(Tenant).filter(Tenant.id == target_tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Empresa nao encontrada")
    assert_can_create_alert(db, tenant)
    data_source = (
        db.query(DataSource)
        .filter(DataSource.id == payload.data_source_id, DataSource.tenant_id == target_tenant_id)
        .first()
    )
    if not data_source:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Fonte nao encontrada")
    if payload.condition not in {">", "<", "=", "==", ">=", "<=", "!="}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Condicao invalida")
    if not any(channel in {"email", "whatsapp"} for channel in payload.channels):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Informe ao menos um canal valido")
    alert = Alert(tenant_id=target_tenant_id, **payload.model_dump())
    db.add(alert)
    db.commit()
    db.refresh(alert)
    return alert


@router.delete("/{alert_id}", response_model=AlertRead)
def delete_alert(
    alert_id: int,
    tenant_id: int | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> Alert:
    target_tenant_id = resolve_tenant_id(current_user, tenant_id)
    alert = db.query(Alert).filter(Alert.id == alert_id, Alert.tenant_id == target_tenant_id).first()
    if not alert:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alerta nao encontrado")
    alert.is_active = False
    db.commit()
    db.refresh(alert)
    return alert


@router.patch("/{alert_id}", response_model=AlertRead)
def update_alert(
    alert_id: int,
    payload: AlertUpdate,
    tenant_id: int | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> Alert:
    target_tenant_id = resolve_tenant_id(current_user, tenant_id)
    alert = db.query(Alert).filter(Alert.id == alert_id, Alert.tenant_id == target_tenant_id).first()
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
    tenant_id: int | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> AlertExecution:
    target_tenant_id = resolve_tenant_id(current_user, tenant_id)
    alert = db.query(Alert).filter(Alert.id == alert_id, Alert.tenant_id == target_tenant_id).first()
    if not alert:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alerta nao encontrado")
    return execute_alert(db, alert)


@router.get("/{alert_id}/executions", response_model=list[AlertExecutionRead])
def list_alert_executions(
    alert_id: int,
    tenant_id: int | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[AlertExecution]:
    target_tenant_id = resolve_tenant_id(current_user, tenant_id)
    return (
        db.query(AlertExecution)
        .filter(AlertExecution.alert_id == alert_id, AlertExecution.tenant_id == target_tenant_id)
        .order_by(AlertExecution.started_at.desc())
        .limit(100)
        .all()
    )


def resolve_tenant_id(current_user: User, tenant_id: int | None) -> int:
    if current_user.role == "super_admin":
        if tenant_id is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="tenant_id e obrigatorio para admin geral")
        return tenant_id
    return current_user.tenant_id
