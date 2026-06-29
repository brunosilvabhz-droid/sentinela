from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import require_super_admin
from app.db.session import get_db
from app.models.app_setting import AppSetting
from app.models.user import User
from app.schemas.settings import AlertCopySettings

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


def get_setting(db: Session, key: str) -> str:
    setting = db.query(AppSetting).filter(AppSetting.key == key).first()
    return setting.value if setting else ""


def set_setting(db: Session, key: str, value: str) -> None:
    setting = db.query(AppSetting).filter(AppSetting.key == key).first()
    if setting:
        setting.value = value.strip()
        return
    db.add(AppSetting(key=key, value=value.strip()))
