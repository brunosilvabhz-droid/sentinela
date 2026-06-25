import smtplib
from email.message import EmailMessage

from twilio.rest import Client

from app.core.config import get_settings
from app.models.alert import Alert


def send_alert_notifications(alert: Alert, result) -> None:
    subject = f"[SENTINELA] Alerta disparado: {alert.name}"
    body = (
        f"O alerta '{alert.name}' encontrou {result.matched_count} registro(s).\n"
        f"Fonte: {alert.data_source.name}\n"
        f"Regra: {alert.column_name} {alert.condition} {alert.threshold_value}\n"
        f"Amostra: {result.sample_records[:3]}"
    )
    if "email" in alert.channels:
        send_email(alert.recipients, subject, body)
    if "whatsapp" in alert.channels:
        send_whatsapp(alert.recipients, body)


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
