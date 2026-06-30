from pydantic import BaseModel


class AlertCopySettings(BaseModel):
    alert_copy_email: str | None = None
    alert_copy_whatsapp: str | None = None


class NotificationTestRequest(BaseModel):
    tenant_id: int | None = None
    recipient: str
    message: str = "Teste SENTINELA: canal configurado com sucesso."


class NotificationTestResponse(BaseModel):
    status: str
    recipient: str
    provider: str | None = None
