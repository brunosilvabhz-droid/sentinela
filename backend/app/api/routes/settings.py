from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import require_super_admin
from app.db.session import get_db
from app.models.app_setting import AppSetting
from app.models.tenant import Tenant
from app.models.user import User
from app.schemas.settings import AlertCopySettings, NotificationTestRequest, NotificationTestResponse
from app.services.notification_service import send_test_email, send_test_whatsapp

router = APIRouter(prefix="/settings", tags=["settings"])

ALERT_COPY_EMAIL_KEY = "alert_copy_email"
ALERT_COPY_WHATSAPP_KEY = "alert_copy_whatsapp"


@router.get("/alert-copy", response_model=AlertCopySettings)
def read_alert_copy_settings(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_super_admin),
) -> AlertCopySettings:
    return AlertCopySettings(
        alert_copy_email=get_setting(db, ALERT_COPY_EMAIL_KEY),
        alert_copy_whatsapp=get_setting(db, ALERT_COPY_WHATSAPP_KEY),
    )


@router.put("/alert-copy", response_model=AlertCopySettings)
def update_alert_copy_settings(
    payload: AlertCopySettings,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_super_admin),
) -> AlertCopySettings:
    set_setting(db, ALERT_COPY_EMAIL_KEY, payload.alert_copy_email or "")
    set_setting(db, ALERT_COPY_WHATSAPP_KEY, payload.alert_copy_whatsapp or "")
    db.commit()
    return read_alert_copy_settings(db, current_user)


@router.post("/test-email", response_model=NotificationTestResponse)
def test_email_channel(
    payload: NotificationTestRequest,
    current_user: User = Depends(require_super_admin),
) -> NotificationTestResponse:
    try:
        provider = send_test_email(payload.recipient, "[SENTINELA] Teste de e-mail", payload.message)
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return NotificationTestResponse(status="sent", recipient=payload.recipient, provider=provider)


@router.post("/test-whatsapp", response_model=NotificationTestResponse)
def test_whatsapp_channel(
    payload: NotificationTestRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_super_admin),
) -> NotificationTestResponse:
    if payload.tenant_id is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="tenant_id e obrigatorio para testar WhatsApp")
    tenant = db.query(Tenant).filter(Tenant.id == payload.tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Empresa nao encontrada")
    try:
        provider = send_test_whatsapp(payload.recipient, payload.message, tenant, payload.template_parameters or [])
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return NotificationTestResponse(
        status="sent",
        recipient=payload.recipient,
        provider=provider,
        detail="Template enviado com parametros." if payload.template_parameters else None,
    )


def get_setting(db: Session, key: str) -> str:
    setting = db.query(AppSetting).filter(AppSetting.key == key).first()
    return setting.value if setting else ""


def set_setting(db: Session, key: str, value: str) -> None:
    setting = db.query(AppSetting).filter(AppSetting.key == key).first()
    if setting:
        setting.value = value.strip()
        return
    db.add(AppSetting(key=key, value=value.strip()))
