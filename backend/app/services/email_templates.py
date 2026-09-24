"""The account emails, as HTML with a plain-text twin.

Written for mail clients, not browsers: tables for layout, every style inline,
no web fonts, and no SVG (Gmail drops it). The logo is a PNG embedded in the
message itself (`cid:logo`, see mailer.py) rather than fetched from a URL,
because many clients block remote images until the reader allows them.

The button has a solid indigo fill with the site's gradient layered on top:
clients that ignore gradients - Outlook - still draw a readable button.

Every value that comes from a person (their name, an address) is escaped.
A name is whatever the student typed at registration.
"""

from __future__ import annotations

from dataclasses import dataclass
from html import escape

INK = "#0f1b33"
BODY = "#3b4a66"
MUTED = "#6b7a94"
LINE = "#e3e8f2"
PAGE = "#f4f6fb"
ACCENT = "#6366F1"
GRADIENT = "linear-gradient(135deg,#8B5CF6 0%,#6366F1 55%,#0EA5E9 100%)"
FONT = "'Segoe UI',Roboto,Helvetica,Arial,sans-serif"


@dataclass(frozen=True)
class Email:
    subject: str
    text: str
    html: str


def _action_email(
    *,
    subject: str,
    title: str,
    greeting_name: str,
    paragraphs: list[str],
    button: str,
    link: str,
    note: str,
    footnote: str,
) -> Email:
    """One heading, a few sentences, one button - the shape of every account email.

    `paragraphs`, `note` and `footnote` are plain text; they are escaped here.
    """
    text = "\n\n".join(
        [f"Hi {greeting_name},", *paragraphs, f"{button}:\n{link}", note, footnote, "- Code Guru"]
    ) + "\n"

    def p(content: str, *, size: int = 15, color: str = BODY, margin: str = "0 0 16px") -> str:
        return (
            f'<p style="margin:{margin};font-family:{FONT};font-size:{size}px;'
            f'line-height:1.6;color:{color};">{content}</p>'
        )

    safe_link = escape(link, quote=True)
    body_paragraphs = "".join(p(escape(paragraph)) for paragraph in paragraphs)

    html = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="color-scheme" content="light">
<meta name="supported-color-schemes" content="light">
<title>{escape(subject)}</title>
</head>
<body style="margin:0;padding:0;background:{PAGE};">
<div style="display:none;max-height:0;overflow:hidden;opacity:0;">{escape(paragraphs[0])}</div>
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="background:{PAGE};">
  <tr>
    <td align="center" style="padding:32px 16px;">
      <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="max-width:520px;">
        <tr>
          <td style="padding:0 4px 20px;">
            <table role="presentation" cellpadding="0" cellspacing="0" border="0">
              <tr>
                <td style="vertical-align:middle;">
                  <img src="cid:logo" width="40" height="40" alt="" style="display:block;border:0;border-radius:10px;">
                </td>
                <td style="vertical-align:middle;padding-left:12px;">
                  <div style="font-family:{FONT};font-size:17px;font-weight:800;color:{INK};line-height:1.2;">Code Guru</div>
                  <div style="font-family:{FONT};font-size:11px;font-weight:600;letter-spacing:1.5px;color:{MUTED};line-height:1.4;">ADAPTIVE JAVA PRACTICE</div>
                </td>
              </tr>
            </table>
          </td>
        </tr>
        <tr>
          <td style="background:#ffffff;border:1px solid {LINE};border-radius:16px;padding:36px 32px;">
            <h1 style="margin:0 0 20px;font-family:{FONT};font-size:23px;font-weight:800;line-height:1.3;color:{INK};">{escape(title)}</h1>
            {p(f"Hi {escape(greeting_name)},")}
            {body_paragraphs}
            <table role="presentation" cellpadding="0" cellspacing="0" border="0" style="margin:28px 0 24px;">
              <tr>
                <td align="center" bgcolor="{ACCENT}" style="border-radius:10px;background:{ACCENT};background-image:{GRADIENT};">
                  <a href="{safe_link}" target="_blank" style="display:inline-block;padding:14px 28px;font-family:{FONT};font-size:15px;font-weight:700;color:#ffffff;text-decoration:none;border-radius:10px;">{escape(button)}</a>
                </td>
              </tr>
            </table>
            {p(escape(note), size=14, color=MUTED, margin="0 0 24px")}
            <div style="border-top:1px solid {LINE};margin:0 0 20px;"></div>
            {p("Button not working? Copy this link into your browser:", size=13, color=MUTED, margin="0 0 6px")}
            {p(f'<a href="{safe_link}" target="_blank" style="color:{ACCENT};word-break:break-all;">{safe_link}</a>', size=13, color=MUTED, margin="0")}
          </td>
        </tr>
        <tr>
          <td style="padding:20px 8px 0;">
            {p(escape(footnote), size=12, color=MUTED, margin="0 0 8px")}
            {p("Code Guru &middot; adaptive Java practice", size=12, color=MUTED, margin="0")}
          </td>
        </tr>
      </table>
    </td>
  </tr>
</table>
</body>
</html>
"""
    return Email(subject=subject, text=text, html=html)


def password_reset_email(*, name: str, account_email: str, link: str, minutes: int) -> Email:
    return _action_email(
        subject="Reset your Code Guru password",
        title="Reset your password",
        greeting_name=name,
        paragraphs=[
            f"We received a request to reset the password for your Code Guru account, {account_email}.",
            "Use the link below to choose a new one. You will be signed out on every device, "
            "and can then sign in with the new password.",
        ],
        button="Choose a new password",
        link=link,
        note=f"This link works once and expires in {minutes} minutes.",
        footnote="Didn't ask for this? You can safely ignore this email. Your password has not changed.",
    )


def recovery_email_confirmation(*, name: str, account_email: str, link: str, hours: int) -> Email:
    return _action_email(
        subject="Confirm your Code Guru recovery email",
        title="Confirm your recovery email",
        greeting_name=name,
        paragraphs=[
            f"The Code Guru account {account_email} would like to use this address to recover "
            "its password.",
            "Once you confirm, password-reset links for that account will be sent here as well.",
        ],
        button="Confirm this address",
        link=link,
        note=f"This link works once and expires in {hours} hours.",
        footnote="Don't recognise this account? You can safely ignore this email. Nothing will change.",
    )
