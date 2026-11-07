import os
import smtplib
from email.message import EmailMessage


def smtp_is_configured() -> bool:
    return bool(os.getenv("SMTP_HOST") and os.getenv("SMTP_FROM") and os.getenv("SMTP_USERNAME") and os.getenv("SMTP_PASSWORD"))


def send_email(to_email: str, subject: str, body: str) -> bool:
    """Send mail when SMTP settings are configured; return False in local dev otherwise."""
    if not smtp_is_configured():
        return False
    host = os.environ["SMTP_HOST"]
    port = int(os.getenv("SMTP_PORT", "587"))
    msg = EmailMessage()
    msg["From"] = os.getenv("SMTP_FROM")
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.set_content(body)
    with smtplib.SMTP(host, port, timeout=20) as server:
        server.starttls()
        server.login(os.environ["SMTP_USERNAME"], os.environ["SMTP_PASSWORD"])
        server.send_message(msg)
    return True
