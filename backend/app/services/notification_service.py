import smtplib
from email.message import EmailMessage

from twilio.rest import Client
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.alert import Alert, AlertOccurrence
from app.models.app_setting import AppSetting


def send_alert_notifications(alert: Alert, result, occurrence: AlertOccurrence, db: Session) -> None:
    settings = get_settings()
    acknowledgement_url = f"{settings.frontend_public_url.rstrip('/')}/ack/{occurrence.ack_token}"
    subject = f"[SENTINELA] Alerta disparado: {alert.name}"
    body = (
        f"O alerta '{alert.name}' encontrou {result.matched_count} registro(s).\n"
        f"Fonte: {alert.data_source.name}\n"
        f"Regra: {_format_alert_rules(alert)}\n"
        f"Confirmar leitura: {acknowledgement_url}\n"
        f"Amostra: {result.sample_records[:3]}"
    )
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


def get_app_setting(db: Session, key: str) -> str:
    setting = db.query(AppSetting).filter(AppSetting.key == key).first()
    return setting.value.strip() if setting and setting.value else ""


def _format_alert_rules(alert: Alert) -> str:
    rules = alert.rules or [
        {"column_name": alert.column_name, "condition": alert.condition, "threshold_value": alert.threshold_value}
    ]
    logic = alert.rule_logic or "AND"
    return " ".join(
        f"{'' if index == 0 else f'{logic} '}{rule.get('column_name')} {rule.get('condition')} {rule.get('threshold_value')}"
        for index, rule in enumerate(rules)
    )
