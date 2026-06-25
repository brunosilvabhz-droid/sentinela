from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.alert import Alert
from app.models.tenant import Tenant


def assert_can_create_alert(db: Session, tenant: Tenant) -> None:
    active_alerts = (
        db.query(Alert)
        .filter(Alert.tenant_id == tenant.id, Alert.is_active.is_(True))
        .count()
    )
    if active_alerts >= tenant.max_alerts:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail=f"Limite do plano atingido: {tenant.max_alerts} alertas ativos",
        )
