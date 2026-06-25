from dataclasses import dataclass
from datetime import datetime, timezone
from time import perf_counter

import pandas as pd
from sqlalchemy.orm import Session

from app.models.alert import Alert, AlertExecution
from app.models.collector import IngestedRecord
from app.services.data_loader import load_data_source
from app.services.notification_service import send_alert_notifications


@dataclass
class RuleResult:
    matched_count: int
    sample_records: list[dict]


def evaluate_alert(alert: Alert, db: Session | None = None) -> RuleResult:
    if alert.data_source.source_type == "managed":
        if db is None:
            raise ValueError("Fonte gerenciada exige sessao de banco")
        dataframe = load_managed_dataframe(db, alert)
    else:
        dataframe = load_data_source(alert.data_source)
    if alert.column_name not in dataframe.columns:
        raise ValueError(f"Coluna '{alert.column_name}' nao existe na fonte")

    series = dataframe[alert.column_name]
    threshold = _coerce_threshold(series, alert.threshold_value)
    mask = _build_mask(series, alert.condition, threshold)
    matches = dataframe[mask]
    return RuleResult(
        matched_count=int(len(matches)),
        sample_records=matches.head(10).where(pd.notnull(matches), None).to_dict(orient="records"),
    )


def execute_alert(db: Session, alert: Alert) -> AlertExecution:
    started = perf_counter()
    execution = AlertExecution(
        tenant_id=alert.tenant_id,
        alert_id=alert.id,
        status="running",
        channels=alert.channels,
    )
    db.add(execution)
    db.commit()
    db.refresh(execution)

    try:
        result = evaluate_alert(alert, db)
        execution.matched_count = result.matched_count
        execution.sample_records = result.sample_records
        if result.matched_count > 0:
            send_alert_notifications(alert, result)
            execution.status = "sent"
        else:
            execution.status = "no_match"
        alert.last_run_at = datetime.now(timezone.utc)
    except Exception as exc:  # noqa: BLE001
        execution.status = "error"
        execution.error_message = str(exc)
    finally:
        execution.finished_at = datetime.now(timezone.utc)
        execution.duration_ms = int((perf_counter() - started) * 1000)
        db.commit()
        db.refresh(execution)
    return execution


def _coerce_threshold(series: pd.Series, value: str):
    numeric_series = pd.to_numeric(series, errors="coerce")
    if numeric_series.notna().any():
        return float(value)
    return value


def _build_mask(series: pd.Series, condition: str, threshold):
    comparable = pd.to_numeric(series, errors="coerce") if isinstance(threshold, float) else series.astype(str)
    if condition == ">":
        return comparable > threshold
    if condition == "<":
        return comparable < threshold
    if condition in {"=", "=="}:
        return comparable == threshold
    if condition == ">=":
        return comparable >= threshold
    if condition == "<=":
        return comparable <= threshold
    if condition == "!=":
        return comparable != threshold
    raise ValueError(f"Condicao nao suportada: {condition}")


def load_managed_dataframe(db: Session, alert: Alert) -> pd.DataFrame:
    rows = (
        db.query(IngestedRecord.payload)
        .filter(
            IngestedRecord.tenant_id == alert.tenant_id,
            IngestedRecord.data_source_id == alert.data_source_id,
        )
        .order_by(IngestedRecord.ingested_at.desc())
        .limit(100000)
        .all()
    )
    payloads = [row[0] for row in rows]
    return pd.DataFrame(payloads)
