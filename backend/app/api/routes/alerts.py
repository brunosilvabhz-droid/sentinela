from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_admin
from app.db.session import get_db
from datetime import datetime, timezone

from app.models.alert import Alert, AlertAcknowledgement, AlertAuditLog, AlertExecution, AlertOccurrence
from app.models.data_source import DataSource
from app.models.user import User
from app.schemas.alert import (
    AlertAcknowledgementCreate,
    AlertAcknowledgementRead,
    AlertAuditLogRead,
    AlertCreate,
    AlertExecutionRead,
    AlertExecutionWithAlertRead,
    AlertOccurrenceRead,
    AlertRead,
    AlertUpdate,
    PublicAlertOccurrenceRead,
)
from app.services.rule_engine import execute_alert
from app.services.tenant_limits import assert_can_create_alert

router = APIRouter(prefix="/alerts", tags=["alerts"])
VALID_CONDITIONS = {">", "<", "=", "==", ">=", "<=", "!="}
VALID_RULE_LOGIC = {"AND", "OR"}


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
    validate_alert_rules(payload.condition, payload.rules, payload.rule_logic)
    validate_whatsapp_recipient_limit(payload.channels, payload.recipients)
    if not any(channel in {"email", "whatsapp"} for channel in payload.channels):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Informe ao menos um canal valido")
    alert = Alert(tenant_id=target_tenant_id, **payload.model_dump())
    db.add(alert)
    db.flush()
    add_alert_audit(db, alert, current_user.id, "created", None, alert_snapshot(alert))
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
    before = alert_snapshot(alert)
    alert.is_active = False
    add_alert_audit(db, alert, current_user.id, "deactivated", before, alert_snapshot(alert))
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
    before = alert_snapshot(alert)
    update_data = payload.model_dump(exclude_unset=True)
    validate_alert_rules(
        update_data.get("condition", alert.condition),
        update_data.get("rules", alert.rules),
        update_data.get("rule_logic", alert.rule_logic),
    )
    validate_whatsapp_recipient_limit(
        update_data.get("channels", alert.channels),
        update_data.get("recipients", alert.recipients),
    )
    for key, value in update_data.items():
        setattr(alert, key, value)
    add_alert_audit(db, alert, current_user.id, "updated", before, alert_snapshot(alert))
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


@router.get("/occurrences", response_model=list[AlertOccurrenceRead])
def list_alert_occurrences(
    tenant_id: int | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[dict]:
    target_tenant_id = resolve_tenant_id(current_user, tenant_id)
    rows = (
        db.query(AlertOccurrence, Alert.name)
        .join(Alert, Alert.id == AlertOccurrence.alert_id)
        .filter(AlertOccurrence.tenant_id == target_tenant_id)
        .order_by(AlertOccurrence.last_seen_at.desc())
        .limit(100)
        .all()
    )
    return [{**occurrence.__dict__, "alert_name": alert_name} for occurrence, alert_name in rows]


@router.get("/acknowledgements", response_model=list[AlertAcknowledgementRead])
def list_alert_acknowledgements(
    tenant_id: int | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[dict]:
    target_tenant_id = resolve_tenant_id(current_user, tenant_id)
    rows = (
        db.query(AlertAcknowledgement, Alert.name)
        .join(Alert, Alert.id == AlertAcknowledgement.alert_id)
        .filter(AlertAcknowledgement.tenant_id == target_tenant_id)
        .order_by(AlertAcknowledgement.acknowledged_at.desc())
        .limit(100)
        .all()
    )
    return [{**ack.__dict__, "alert_name": alert_name} for ack, alert_name in rows]


@router.get("/audit-logs", response_model=list[AlertAuditLogRead])
def list_alert_audit_logs(
    tenant_id: int | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> list[dict]:
    target_tenant_id = resolve_tenant_id(current_user, tenant_id)
    rows = (
        db.query(AlertAuditLog, Alert.name)
        .join(Alert, Alert.id == AlertAuditLog.alert_id)
        .filter(AlertAuditLog.tenant_id == target_tenant_id)
        .order_by(AlertAuditLog.created_at.desc())
        .limit(100)
        .all()
    )
    return [{**log.__dict__, "alert_name": alert_name} for log, alert_name in rows]


@router.get("/ack/{token}", response_model=PublicAlertOccurrenceRead)
def read_public_acknowledgement(
    token: str,
    db: Session = Depends(get_db),
) -> dict:
    occurrence = get_occurrence_by_token(db, token)
    return {
        "alert_name": occurrence.alert.name,
        "source_name": occurrence.alert.data_source.name,
        "status": occurrence.status,
        "matched_count": occurrence.matched_count,
        "sample_records": occurrence.sample_records,
    }


@router.post("/ack/{token}", response_model=AlertAcknowledgementRead)
def confirm_public_acknowledgement(
    token: str,
    payload: AlertAcknowledgementCreate,
    db: Session = Depends(get_db),
) -> AlertAcknowledgement:
    occurrence = get_occurrence_by_token(db, token)
    now = datetime.now(timezone.utc)
    occurrence.status = "acknowledged"
    occurrence.acknowledged_at = now
    acknowledgement = AlertAcknowledgement(
        tenant_id=occurrence.tenant_id,
        alert_id=occurrence.alert_id,
        occurrence_id=occurrence.id,
        acknowledged_by_name=payload.acknowledged_by_name,
        acknowledged_by_email=payload.acknowledged_by_email,
        note=payload.note,
        acknowledged_at=now,
    )
    db.add(acknowledgement)
    db.commit()
    db.refresh(acknowledgement)
    return acknowledgement


def resolve_tenant_id(current_user: User, tenant_id: int | None) -> int:
    if current_user.role == "super_admin":
        if tenant_id is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="tenant_id e obrigatorio para admin geral")
        return tenant_id
    return current_user.tenant_id


def get_occurrence_by_token(db: Session, token: str) -> AlertOccurrence:
    occurrence = db.query(AlertOccurrence).filter(AlertOccurrence.ack_token == token).first()
    if not occurrence:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Confirmacao nao encontrada")
    return occurrence


def alert_snapshot(alert: Alert) -> dict:
    return {
        "name": alert.name,
        "data_source_id": alert.data_source_id,
        "column_name": alert.column_name,
        "condition": alert.condition,
        "threshold_value": alert.threshold_value,
        "rules": alert.rules,
        "rule_logic": alert.rule_logic,
        "frequency": alert.frequency,
        "recipients": alert.recipients,
        "channels": alert.channels,
        "is_active": alert.is_active,
    }


def add_alert_audit(
    db: Session,
    alert: Alert,
    user_id: int | None,
    action: str,
    before: dict | None,
    after: dict | None,
) -> None:
    db.add(
        AlertAuditLog(
            tenant_id=alert.tenant_id,
            alert_id=alert.id,
            user_id=user_id,
            action=action,
            before=before,
            after=after,
        )
    )


def validate_alert_rules(condition: str, rules: list | None, rule_logic: str | None) -> None:
    if condition not in VALID_CONDITIONS:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Condicao invalida")
    if (rule_logic or "AND").upper() not in VALID_RULE_LOGIC:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Operador logico invalido")
    for rule in rules or []:
        rule_condition = rule.condition if hasattr(rule, "condition") else rule.get("condition")
        rule_column = rule.column_name if hasattr(rule, "column_name") else rule.get("column_name")
        rule_value = rule.threshold_value if hasattr(rule, "threshold_value") else rule.get("threshold_value")
        if not str(rule_column or "").strip() or rule_condition not in VALID_CONDITIONS or not str(rule_value or "").strip():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Regra composta invalida")


def validate_whatsapp_recipient_limit(channels: list[str], recipients: list[str]) -> None:
    if "whatsapp" not in channels:
        return
    whatsapp_recipients = [recipient for recipient in recipients if is_whatsapp_recipient(recipient)]
    if len(whatsapp_recipients) > 3:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cada alerta pode ter no maximo 3 numeros de WhatsApp",
        )


def is_whatsapp_recipient(recipient: str) -> bool:
    value = recipient.strip().lower()
    return bool(value) and "@" not in value and (value.startswith("+") or value.startswith("whatsapp:"))
