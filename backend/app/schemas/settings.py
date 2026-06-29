from pydantic import BaseModel


class AlertCopySettings(BaseModel):
    alert_copy_email: str | None = None
    alert_copy_whatsapp: str | None = None
