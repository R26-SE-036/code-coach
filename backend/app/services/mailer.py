"""Sending account email: password reset and recovery-address confirmation.

Plain SMTP with STARTTLS (or implicit TLS on 465), which is what Gmail's app
passwords speak. No provider SDK, so moving to another SMTP service later is a
settings change.

Never raises. The callers run it after the response has been sent, and a
student who asked for a reset link must get the same answer whether or not
the mail server was reachable - the answer must not reveal whether the account
exists, and a mail failure is not theirs to act on. Failures are logged.
"""

from __future__ import annotations

import logging
import smtplib
from email.message import EmailMessage
from pathlib import Path

from app.core.config import get_settings

logger = logging.getLogger(__name__)

# The logo shown at the top of every HTML email, embedded as `cid:logo`.
LOGO = Path(__file__).resolve().parent.parent / "static" / "email-logo.png"


def _redact(address: str) -> str:
    name, _, domain = address.partition("@")
    return f"{name[:2]}***@{domain}"


def send_mail(
    recipients: list[str],
    subject: str,
    body: str,
    *,
    link: str = "",
    html: str | None = None,
) -> bool:
    """Send `body` as plain text, with `html` as the richer alternative if given.

    Clients show the HTML when they can and the text otherwise, so both must
    say everything - see email_templates.py, which writes them as a pair.
    """
    settings = get_settings()
    recipients = [address for address in dict.fromkeys(recipients) if address]
    if not recipients:
        return False

    sender = settings.mail_from or settings.smtp_username
    if not (settings.smtp_host and sender):
        logger.warning(
            "Email is not configured (SMTP_HOST / MAIL_FROM); not sending %r to %s.",
            subject,
            ", ".join(_redact(address) for address in recipients),
        )
        if settings.mail_log_links and link:
            logger.warning("MAIL_LOG_LINKS is on - the link was: %s", link)
        return False

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = f"Code Guru <{sender}>"
    message["To"] = ", ".join(recipients)
    message.set_content(body)
    if html is not None:
        message.add_alternative(html, subtype="html")
        if LOGO.exists():
            # Attached to the HTML part, so it is shown inline, not as a file.
            # `inline` and no file name: given a name it is sent as an
            # attachment, which some clients list under the message.
            message.get_payload()[1].add_related(
                LOGO.read_bytes(), "image", "png", cid="<logo>", disposition="inline"
            )

    try:
        if settings.smtp_port == 465:
            server: smtplib.SMTP = smtplib.SMTP_SSL(settings.smtp_host, settings.smtp_port, timeout=15)
        else:
            server = smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=15)
            server.starttls()
        with server:
            if settings.smtp_username and settings.smtp_password:
                server.login(settings.smtp_username, settings.smtp_password)
            server.send_message(message)
    except (OSError, smtplib.SMTPException) as error:
        logger.error("Could not send %r: %s", subject, error)
        return False

    return True
