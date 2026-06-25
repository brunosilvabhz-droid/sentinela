from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.alert import Alert, AlertExecution
from app.models.user import User

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/summary")
def dashboard_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    total_executions = (
        db.query(AlertExecution)
        .filter(AlertExecution.tenant_id == current_user.tenant_id, AlertExecution.status == "sent")
        .count()
    )
    active_alerts = (
        db.query(Alert)
        .filter(Alert.tenant_id == current_user.tenant_id, Alert.is_active.is_(True))
        .count()
    )
    inactive_alerts = (
        db.query(Alert)
        .filter(Alert.tenant_id == current_user.tenant_id, Alert.is_active.is_(False))
        .count()
    )
    by_status = (
        db.query(AlertExecution.status, func.count(AlertExecution.id))
        .filter(AlertExecution.tenant_id == current_user.tenant_id)
        .group_by(AlertExecution.status)
        .all()
    )
    return {
        "sent_alerts": total_executions,
        "active_alerts": active_alerts,
        "inactive_alerts": inactive_alerts,
        "executions_by_status": {status: count for status, count in by_status},
    }
