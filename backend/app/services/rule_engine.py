from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
import secrets
from time import perf_counter

import pandas as pd
from sqlalchemy.orm import Session

from app.models.alert import Alert, AlertExecution, AlertOccurrence
from app.models.collector import IngestedRecord
from app.services.data_loader import load_data_source
from app.services.notification_service import send_alert_notifications


@dataclass
class RuleResult:
    matched_count: int
    sample_records: list[dict]
    fingerprint: str
    matched_records: list[dict] | None = None


def evaluate_alert(alert: Alert, db: Session | None = None) -> RuleResult:
    if alert.data_source.source_type == "managed":
        if db is None:
            raise ValueError("Fonte gerenciada exige sessao de banco")
        dataframe = load_managed_dataframe(db, alert)
    else:
        dataframe = load_data_source(alert.data_source)
    rules = _alert_rules(alert)
    mask = None
    for rule in rules:
        column_name = rule["column_name"]
        if column_name not in dataframe.columns:
            raise ValueError(f"Coluna '{column_name}' nao existe na fonte")
        series = dataframe[column_name]
        threshold = None if rule["condition"] == "birthday_today" else _coerce_threshold(series, rule["threshold_value"])
        rule_mask = _build_mask(series, rule["condition"], threshold)
        if mask is None:
            mask = rule_mask
        elif (alert.rule_logic or "AND").upper() == "OR":
            mask = mask | rule_mask
        else:
            mask = mask & rule_mask
    if mask is None:
        raise ValueError("Alerta sem regras configuradas")
    matches = dataframe[mask]
    matched_records = matches.where(pd.notnull(matches), None).to_dict(orient="records")
    return RuleResult(
        matched_count=int(len(matches)),
        sample_records=matched_records[:10],
        fingerprint=_fingerprint_records(matched_records),
        matched_records=matched_records[:1000],
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
            occurrence = _get_or_create_occurrence(db, alert, result)
            execution.occurrence_id = occurrence.id
            if occurrence.status in {"acknowledged", "open"} and occurrence.first_seen_at != occurrence.last_seen_at:
                execution.status = "suppressed"
            else:
                send_alert_notifications(alert, result, occurrence, db)
                execution.status = "sent"
        else:
            _resolve_open_occurrences(db, alert)
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


def _get_or_create_occurrence(db: Session, alert: Alert, result: RuleResult) -> AlertOccurrence:
    now = datetime.now(timezone.utc)
    occurrence = (
        db.query(AlertOccurrence)
        .filter(
            AlertOccurrence.tenant_id == alert.tenant_id,
            AlertOccurrence.alert_id == alert.id,
            AlertOccurrence.fingerprint == result.fingerprint,
            AlertOccurrence.status.in_(["open", "acknowledged"]),
        )
        .first()
    )
    if occurrence:
        occurrence.last_seen_at = now
        occurrence.matched_count = result.matched_count
        occurrence.sample_records = result.sample_records
        db.flush()
        return occurrence

    occurrence = AlertOccurrence(
        tenant_id=alert.tenant_id,
        alert_id=alert.id,
        fingerprint=result.fingerprint,
        ack_token=secrets.token_urlsafe(32),
        status="open",
        matched_count=result.matched_count,
        sample_records=result.sample_records,
        first_seen_at=now,
        last_seen_at=now,
    )
    db.add(occurrence)
    db.flush()
    return occurrence


def _resolve_open_occurrences(db: Session, alert: Alert) -> None:
    now = datetime.now(timezone.utc)
    occurrences = (
        db.query(AlertOccurrence)
        .filter(
            AlertOccurrence.tenant_id == alert.tenant_id,
            AlertOccurrence.alert_id == alert.id,
            AlertOccurrence.status == "open",
        )
        .all()
    )
    for occurrence in occurrences:
        occurrence.status = "resolved"
        occurrence.resolved_at = now


def _fingerprint_records(records: list[dict]) -> str:
    canonical = json.dumps(records, sort_keys=True, default=str, ensure_ascii=True)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _coerce_threshold(series: pd.Series, value: str):
    numeric_series = pd.to_numeric(series, errors="coerce")
    if numeric_series.notna().any():
        return float(value)
    return value


def _build_mask(series: pd.Series, condition: str, threshold):
    if condition == "birthday_today":
        dates = pd.to_datetime(series, errors="coerce", dayfirst=True)
        today = datetime.now().date()
        return (dates.dt.day == today.day) & (dates.dt.month == today.month)
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


def _alert_rules(alert: Alert) -> list[dict[str, str]]:
    if alert.rules:
        return [
            {
                "column_name": str(rule.get("column_name", "")).strip(),
                "condition": str(rule.get("condition", "")).strip(),
                "threshold_value": str(rule.get("threshold_value", "")).strip(),
            }
            for rule in alert.rules
        ]
    return [
        {
            "column_name": alert.column_name,
            "condition": alert.condition,
            "threshold_value": alert.threshold_value,
        }
    ]


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
