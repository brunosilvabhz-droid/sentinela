from datetime import datetime, timedelta, timezone

from croniter import croniter

from app.db.session import SessionLocal
from app.models.alert import Alert
from app.services.data_retention import purge_expired_ingestion_data
from app.services.rule_engine import execute_alert
from app.workers.celery_app import celery_app


@celery_app.task(name="app.workers.tasks.run_alert")
def run_alert(alert_id: int) -> int | None:
    db = SessionLocal()
    try:
        alert = db.query(Alert).filter(Alert.id == alert_id, Alert.is_active.is_(True)).first()
        if not alert:
            return None
        execution = execute_alert(db, alert)
        return execution.id
    finally:
        db.close()


@celery_app.task(name="app.workers.tasks.dispatch_due_alerts")
def dispatch_due_alerts() -> int:
    db = SessionLocal()
    dispatched = 0
    now = datetime.now(timezone.utc)
    try:
        alerts = db.query(Alert).filter(Alert.is_active.is_(True)).all()
        for alert in alerts:
            if _is_due(alert, now):
                run_alert.delay(alert.id)
                dispatched += 1
        return dispatched
    finally:
        db.close()


@celery_app.task(name="app.workers.tasks.purge_ingestion_data")
def purge_ingestion_data() -> dict[str, int]:
    db = SessionLocal()
    try:
        return purge_expired_ingestion_data(db)
    finally:
        db.close()


def _is_due(alert: Alert, now: datetime) -> bool:
    if not alert.last_run_at:
        return True

    frequency = alert.frequency.strip()
    if frequency.endswith("m") and frequency[:-1].isdigit():
        minutes = int(frequency[:-1])
        return alert.last_run_at <= now - timedelta(minutes=minutes)

    if frequency.endswith("h") and frequency[:-1].isdigit():
        hours = int(frequency[:-1])
        return alert.last_run_at <= now - timedelta(hours=hours)

    previous_tick = croniter(frequency, now).get_prev(datetime)
    return alert.last_run_at <= previous_tick
