import smtplib
from email.message import EmailMessage
import json
import re
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from twilio.rest import Client
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.alert import Alert, AlertOccurrence
from app.models.app_setting import AppSetting


def send_alert_notifications(alert: Alert, result, occurrence: AlertOccurrence, db: Session) -> None:
    settings = get_settings()
    acknowledgement_url = f"{settings.frontend_public_url.rstrip('/')}/ack/{occurrence.ack_token}"
    subject = f"[SENTINELA] Alerta disparado: {alert.name}"
    body = build_alert_message(alert, result, acknowledgement_url)
    if has_dynamic_recipients(alert):
        send_dynamic_notifications(alert, result, subject, acknowledgement_url)
    else:
        if "email" in alert.channels:
            send_email(alert.recipients, subject, body)
        if "whatsapp" in alert.channels:
            send_whatsapp(alert.recipients, body)

    copy_email = get_app_setting(db, "alert_copy_email")
    copy_whatsapp = get_app_setting(db, "alert_copy_whatsapp")
    if copy_email:
        send_email([copy_email], f"[COPIA OPERACIONAL] {subject}", body)
    if copy_whatsapp:
        send_whatsapp([copy_whatsapp], f"[COPIA OPERACIONAL]\n{body}")


def send_email(recipients: list[str], subject: str, body: str) -> None:
    settings = get_settings()
    if not settings.smtp_host:
        return
    message = EmailMessage()
    message["From"] = settings.smtp_from_email
    message["To"] = ", ".join([r for r in recipients if "@" in r])
    message["Subject"] = subject
    message.set_content(body)
    if not message["To"]:
        return

    with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as smtp:
        if settings.smtp_username:
            smtp.starttls()
            smtp.login(settings.smtp_username, settings.smtp_password)
        smtp.send_message(message)


def send_whatsapp(recipients: list[str], body: str) -> None:
    settings = get_settings()
    if settings.whatsapp_provider.lower() == "twilio":
        send_whatsapp_twilio(recipients, body)
        return
    send_whatsapp_meta(recipients, body)


def has_dynamic_recipients(alert: Alert) -> bool:
    return bool(alert.dynamic_email_column or alert.dynamic_whatsapp_column)


def send_dynamic_notifications(alert: Alert, result, subject: str, acknowledgement_url: str) -> None:
    for record in result.matched_records or result.sample_records:
        body = build_alert_message_for_record(alert, result, acknowledgement_url, record)
        email = str(record.get(alert.dynamic_email_column or "", "") or "").strip()
        whatsapp = str(record.get(alert.dynamic_whatsapp_column or "", "") or "").strip()
        if "email" in alert.channels and email:
            send_email([email], subject, body)
        if "whatsapp" in alert.channels and whatsapp:
            send_whatsapp([whatsapp], body)


def send_whatsapp_meta(recipients: list[str], body: str) -> None:
    settings = get_settings()
    if not settings.meta_whatsapp_token or not settings.meta_whatsapp_phone_number_id:
        return

    for recipient in recipients:
        phone_number = normalize_whatsapp_number(recipient)
        if not phone_number:
            continue
        payload = build_meta_whatsapp_payload(phone_number, body)
        request = Request(
            f"https://graph.facebook.com/{settings.meta_whatsapp_api_version}/{settings.meta_whatsapp_phone_number_id}/messages",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {settings.meta_whatsapp_token}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with urlopen(request, timeout=20) as response:
                response.read()
        except HTTPError as exc:
            error_body = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"Erro ao enviar WhatsApp pela Meta: {exc.code} {error_body}") from exc


def send_whatsapp_twilio(recipients: list[str], body: str) -> None:
    settings = get_settings()
    if not settings.twilio_account_sid or not settings.twilio_auth_token:
        return

    client = Client(settings.twilio_account_sid, settings.twilio_auth_token)
    for recipient in recipients:
        if recipient.startswith("whatsapp:"):
            to = recipient
        elif recipient.startswith("+"):
            to = f"whatsapp:{recipient}"
        else:
            continue
        client.messages.create(from_=settings.twilio_whatsapp_from, to=to, body=body)


def build_meta_whatsapp_payload(phone_number: str, body: str) -> dict:
    settings = get_settings()
    payload: dict = {
        "messaging_product": "whatsapp",
        "to": phone_number,
    }
    if settings.meta_whatsapp_template_name:
        payload.update(
            {
                "type": "template",
                "template": {
                    "name": settings.meta_whatsapp_template_name,
                    "language": {"code": settings.meta_whatsapp_template_language},
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
