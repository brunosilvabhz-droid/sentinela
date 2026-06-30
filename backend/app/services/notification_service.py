import smtplib
from email.message import EmailMessage
import json
import re
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from twilio.rest import Client
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.alert import Alert, AlertDeliveryLog, AlertOccurrence
from app.models.app_setting import AppSetting
from app.models.tenant import Tenant


def send_alert_notifications(alert: Alert, result, occurrence: AlertOccurrence, db: Session) -> None:
    settings = get_settings()
    acknowledgement_url = f"{settings.frontend_public_url.rstrip('/')}/ack/{occurrence.ack_token}"
    subject = f"[SENTINELA] Alerta disparado: {alert.name}"
    body = build_alert_message(alert, result, acknowledgement_url)
    if has_dynamic_recipients(alert):
        send_dynamic_notifications(alert, result, subject, acknowledgement_url, db, occurrence)
    else:
        if "email" in alert.channels:
            send_email(alert.recipients, subject, body, db=db, alert=alert, occurrence=occurrence)
        if "whatsapp" in alert.channels:
            send_whatsapp(alert.recipients, body, alert.tenant, db=db, alert=alert, occurrence=occurrence)

    copy_email = get_app_setting(db, "alert_copy_email")
    copy_whatsapp = get_app_setting(db, "alert_copy_whatsapp")
    if copy_email:
        send_email([copy_email], f"[COPIA OPERACIONAL] {subject}", body)
    if copy_whatsapp:
        send_whatsapp([copy_whatsapp], f"[COPIA OPERACIONAL]\n{body}")


def send_email(
    recipients: list[str],
    subject: str,
    body: str,
    db: Session | None = None,
    alert: Alert | None = None,
    occurrence: AlertOccurrence | None = None,
) -> None:
    settings = get_settings()
    email_recipients = [recipient for recipient in recipients if "@" in recipient]
    if not settings.smtp_host:
        for recipient in email_recipients:
            log_delivery(db, alert, occurrence, "email", recipient, "skipped", "smtp", "SMTP nao configurado")
        return
    if not email_recipients:
        return

    for recipient in email_recipients:
        message = EmailMessage()
        message["From"] = settings.smtp_from_email
        message["To"] = recipient
        message["Subject"] = subject
        message.set_content(body)
        try:
            with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as smtp:
                if settings.smtp_username:
                    smtp.starttls()
                    smtp.login(settings.smtp_username, settings.smtp_password)
                smtp.send_message(message)
            log_delivery(db, alert, occurrence, "email", recipient, "sent", "smtp")
        except Exception as exc:  # noqa: BLE001
            log_delivery(db, alert, occurrence, "email", recipient, "error", "smtp", str(exc))


def send_whatsapp(
    recipients: list[str],
    body: str,
    tenant: Tenant | None = None,
    db: Session | None = None,
    alert: Alert | None = None,
    occurrence: AlertOccurrence | None = None,
) -> None:
    config = resolve_whatsapp_config(tenant)
    if not config.get("is_active", True):
        for recipient in recipients:
            log_delivery(db, alert, occurrence, "whatsapp", recipient, "skipped", config["provider"], "WhatsApp inativo")
        return
    if config["provider"].lower() == "twilio":
        send_whatsapp_twilio(recipients, body, db=db, alert=alert, occurrence=occurrence)
        return
    send_whatsapp_meta(recipients, body, config, db=db, alert=alert, occurrence=occurrence)


def has_dynamic_recipients(alert: Alert) -> bool:
    return bool(alert.dynamic_email_column or alert.dynamic_whatsapp_column)


def send_dynamic_notifications(
    alert: Alert,
    result,
    subject: str,
    acknowledgement_url: str,
    db: Session,
    occurrence: AlertOccurrence,
) -> None:
    for record in result.matched_records or result.sample_records:
        body = build_alert_message_for_record(alert, result, acknowledgement_url, record)
        email = str(record.get(alert.dynamic_email_column or "", "") or "").strip()
        whatsapp = str(record.get(alert.dynamic_whatsapp_column or "", "") or "").strip()
        if "email" in alert.channels and email:
            send_email([email], subject, body, db=db, alert=alert, occurrence=occurrence)
        if "whatsapp" in alert.channels and whatsapp:
            send_whatsapp([whatsapp], body, alert.tenant, db=db, alert=alert, occurrence=occurrence)


def send_whatsapp_meta(
    recipients: list[str],
    body: str,
    config: dict,
    db: Session | None = None,
    alert: Alert | None = None,
    occurrence: AlertOccurrence | None = None,
) -> None:
    if not config["token"] or not config["phone_number_id"]:
        for recipient in recipients:
            log_delivery(db, alert, occurrence, "whatsapp", recipient, "skipped", "meta", "Meta token ou phone_number_id nao configurado")
        return

    for recipient in recipients:
        phone_number = normalize_whatsapp_number(recipient)
        if not phone_number:
            log_delivery(db, alert, occurrence, "whatsapp", recipient, "skipped", "meta", "Numero de WhatsApp invalido")
            continue
        payload = build_meta_whatsapp_payload(phone_number, body, config)
        request = Request(
            f"https://graph.facebook.com/{config['api_version']}/{config['phone_number_id']}/messages",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {config['token']}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with urlopen(request, timeout=20) as response:
                response.read()
            log_delivery(db, alert, occurrence, "whatsapp", recipient, "sent", "meta")
        except HTTPError as exc:
            error_body = exc.read().decode("utf-8", errors="replace")
            log_delivery(db, alert, occurrence, "whatsapp", recipient, "error", "meta", f"{exc.code} {error_body}")
        except Exception as exc:  # noqa: BLE001
            log_delivery(db, alert, occurrence, "whatsapp", recipient, "error", "meta", str(exc))


def send_whatsapp_twilio(
    recipients: list[str],
    body: str,
    db: Session | None = None,
    alert: Alert | None = None,
    occurrence: AlertOccurrence | None = None,
) -> None:
    settings = get_settings()
    if not settings.twilio_account_sid or not settings.twilio_auth_token:
        for recipient in recipients:
            log_delivery(db, alert, occurrence, "whatsapp", recipient, "skipped", "twilio", "Twilio nao configurado")
        return

    client = Client(settings.twilio_account_sid, settings.twilio_auth_token)
    for recipient in recipients:
        if recipient.startswith("whatsapp:"):
            to = recipient
        elif recipient.startswith("+"):
            to = f"whatsapp:{recipient}"
        else:
            log_delivery(db, alert, occurrence, "whatsapp", recipient, "skipped", "twilio", "Numero de WhatsApp invalido")
            continue
        try:
            client.messages.create(from_=settings.twilio_whatsapp_from, to=to, body=body)
            log_delivery(db, alert, occurrence, "whatsapp", recipient, "sent", "twilio")
        except Exception as exc:  # noqa: BLE001
            log_delivery(db, alert, occurrence, "whatsapp", recipient, "error", "twilio", str(exc))


def log_delivery(
    db: Session | None,
    alert: Alert | None,
    occurrence: AlertOccurrence | None,
    channel: str,
    recipient: str,
    status: str,
    provider: str | None = None,
    error_message: str | None = None,
) -> None:
    if not db or not alert:
        return
    db.add(
        AlertDeliveryLog(
            tenant_id=alert.tenant_id,
            alert_id=alert.id,
            occurrence_id=occurrence.id if occurrence else None,
            channel=channel,
            recipient=recipient,
            status=status,
            provider=provider,
            error_message=error_message,
        )
    )
    db.flush()


def build_meta_whatsapp_payload(phone_number: str, body: str, config: dict) -> dict:
    payload: dict = {
        "messaging_product": "whatsapp",
        "to": phone_number,
    }
    if config["template_name"]:
        payload.update(
            {
                "type": "template",
                "template": {
                    "name": config["template_name"],
                    "language": {"code": config["template_language"]},
                    "components": [
                        {
                            "type": "body",
                            "parameters": [{"type": "text", "text": body[:1024]}],
                        }
                    ],
                },
            }
        )
        return payload
    payload.update({"type": "text", "text": {"preview_url": False, "body": body[:4096]}})
    return payload


def resolve_whatsapp_config(tenant: Tenant | None = None) -> dict:
    settings = get_settings()
    if tenant and tenant.whatsapp_provider == "meta" and tenant.meta_whatsapp_token and tenant.meta_whatsapp_phone_number_id:
        return {
            "provider": tenant.whatsapp_provider,
            "token": tenant.meta_whatsapp_token,
            "phone_number_id": tenant.meta_whatsapp_phone_number_id,
            "api_version": tenant.meta_whatsapp_api_version or "v20.0",
            "template_name": tenant.meta_whatsapp_template_name or "",
            "template_language": tenant.meta_whatsapp_template_language or "pt_BR",
            "is_active": tenant.whatsapp_is_active,
        }
    return {
        "provider": settings.whatsapp_provider,
        "token": settings.meta_whatsapp_token,
        "phone_number_id": settings.meta_whatsapp_phone_number_id,
        "api_version": settings.meta_whatsapp_api_version,
        "template_name": settings.meta_whatsapp_template_name,
        "template_language": settings.meta_whatsapp_template_language,
        "is_active": True,
    }


def normalize_whatsapp_number(recipient: str) -> str:
    value = recipient.strip()
    if not value or "@" in value:
        return ""
    if value.startswith("whatsapp:"):
        value = value.removeprefix("whatsapp:")
    digits = "".join(char for char in value if char.isdigit())
    return digits


def get_app_setting(db: Session, key: str) -> str:
    setting = db.query(AppSetting).filter(AppSetting.key == key).first()
    return setting.value.strip() if setting and setting.value else ""


def build_alert_message(alert: Alert, result, acknowledgement_url: str) -> str:
    return build_alert_message_for_record(
        alert,
        result,
        acknowledgement_url,
        result.sample_records[0] if result.sample_records else {},
    )


def build_alert_message_for_record(alert: Alert, result, acknowledgement_url: str, record: dict) -> str:
    if alert.message_template:
        rendered = render_message_template(
            alert.message_template,
            alert.message_variables or {},
            record,
        )
        return (
            f"{rendered}\n\n"
            f"Alerta: {alert.name}\n"
            f"Fonte: {alert.data_source.name}\n"
            f"Registros encontrados: {result.matched_count}\n"
            f"Confirmar leitura: {acknowledgement_url}"
        )
    return (
        f"O alerta '{alert.name}' encontrou {result.matched_count} registro(s).\n"
        f"Fonte: {alert.data_source.name}\n"
        f"Regra: {_format_alert_rules(alert)}\n"
        f"Confirmar leitura: {acknowledgement_url}\n"
        f"Amostra: {result.sample_records[:3]}"
    )


def preview_alert_messages(alert: Alert, result, acknowledgement_url: str = "https://app.impactocg.com/ack/exemplo") -> list[str]:
    return [
        build_alert_message_for_record(alert, result, acknowledgement_url, record)
        for record in (result.sample_records or [])[:3]
    ]


def render_message_template(template: str, variables: dict[str, str], record: dict) -> str:
    def replace(match: re.Match) -> str:
        variable_name = match.group(1).strip()
        column_name = variables.get(variable_name, variable_name)
        value = record.get(column_name, "")
        return "" if value is None else str(value)

    return re.sub(r"\{\{\s*([a-zA-Z0-9_]+)\s*\}\}", replace, template)


def _format_alert_rules(alert: Alert) -> str:
    rules = alert.rules or [
        {"column_name": alert.column_name, "condition": alert.condition, "threshold_value": alert.threshold_value}
    ]
    logic = alert.rule_logic or "AND"
    return " ".join(
        f"{'' if index == 0 else f'{logic} '}{rule.get('column_name')} {rule.get('condition')} {rule.get('threshold_value')}"
        for index, rule in enumerate(rules)
    )
