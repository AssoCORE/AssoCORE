"""Async email delivery.

`send_mail()` is the single outbound path for all email in AssoCORE.

Behaviour when MAIL_ENABLED=false (the default): logs at INFO and returns False
without connecting — safe on a bare dev box with no SMTP anywhere.

Behaviour on transport failure: logs at ERROR and returns False. The caller
decides whether that matters; a courtesy side-effect (event confirmation) should
swallow it; a password-reset that silently fails leaves the user stuck — see the
forgot-password endpoint for how to surface that correctly without breaking
enumeration safety.
"""

import logging
import os
from email.message import EmailMessage

log = logging.getLogger(__name__)

MAIL_ENABLED = os.getenv("MAIL_ENABLED", "false").lower() in ("1", "true", "yes")
SMTP_HOST = os.getenv("SMTP_HOST", "mailpit")
SMTP_PORT = int(os.getenv("SMTP_PORT", "1025"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
SMTP_STARTTLS = os.getenv("SMTP_STARTTLS", "false").lower() in ("1", "true", "yes")
MAIL_FROM = os.getenv("MAIL_FROM", "no-reply@assocore.local")
MAIL_FROM_NAME = os.getenv("MAIL_FROM_NAME", "AssoCORE")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")


async def send_mail(
    to: str,
    subject: str,
    body: str,
    html: str | None = None,
) -> bool:
    """Send an email. Returns True on success, False otherwise. Never raises."""
    if not MAIL_ENABLED:
        log.info("MAIL_ENABLED=false — skipping send to %s: %s", to, subject)
        return False

    msg = EmailMessage()
    msg["From"] = f"{MAIL_FROM_NAME} <{MAIL_FROM}>"
    msg["To"] = to
    msg["Subject"] = subject
    msg.set_content(body)
    if html:
        msg.add_alternative(html, subtype="html")

    try:
        import aiosmtplib

        await aiosmtplib.send(
            msg,
            hostname=SMTP_HOST,
            port=SMTP_PORT,
            username=SMTP_USER or None,
            password=SMTP_PASSWORD or None,
            start_tls=SMTP_STARTTLS,
        )
        return True
    except Exception:
        log.error("Failed to send mail to %s (subject: %s)", to, subject, exc_info=True)
        return False
