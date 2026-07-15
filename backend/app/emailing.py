import smtplib
from collections.abc import Iterable
from email.message import EmailMessage
from email.utils import formataddr
from html import escape
from pathlib import Path

from app.config import get_settings

BRAND_LOGO_CID = "baytak-foundation-logo"
BRAND_LOGO_PATH = Path(__file__).with_name("assets") / "baytak-logo.png"


def send_email(
    *,
    recipients: Iterable[str],
    subject: str,
    text: str,
    html: str,
    attachments: Iterable[tuple[str, bytes, str, str]] = (),
) -> None:
    settings = get_settings()
    if not settings.smtp_host:
        raise RuntimeError("SMTP_HOST is not configured")
    sender = settings.smtp_from or settings.smtp_username
    if not sender:
        raise RuntimeError("Set SMTP_FROM or SMTP_USERNAME before sending email")

    recipient_list = list(recipients)
    if not recipient_list:
        raise RuntimeError("At least one email recipient is required")

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = formataddr((settings.app_name, sender))
    message["To"] = ", ".join(recipient_list)
    message.set_content(text)
    message.add_alternative(html, subtype="html")
    if BRAND_LOGO_PATH.is_file():
        html_part = message.get_payload()[-1]
        html_part.add_related(
            BRAND_LOGO_PATH.read_bytes(),
            maintype="image",
            subtype="png",
            cid=f"<{BRAND_LOGO_CID}>",
            filename="baytak-logo.png",
            disposition="inline",
        )
    for filename, content, maintype, subtype in attachments:
        message.add_attachment(
            content,
            maintype=maintype,
            subtype=subtype,
            filename=filename,
        )

    with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=30) as smtp:
        smtp.ehlo()
        if settings.smtp_starttls:
            smtp.starttls()
            smtp.ehlo()
        if settings.smtp_username and settings.smtp_password:
            smtp.login(settings.smtp_username, settings.smtp_password)
        smtp.send_message(message)


def email_layout(
    *,
    heading: str,
    body: str,
    eyebrow: str,
    preview_text: str,
    action_label: str | None = None,
    action_url: str | None = None,
    details: Iterable[tuple[str, str]] = (),
) -> str:
    settings = get_settings()
    brand_name = settings.app_name.removesuffix(" API")
    detail_rows = "".join(
        (
            '<tr>'
            f'<td style="color:#6b7c8f;font-size:12px;padding:8px 0">{escape(label)}</td>'
            f'<td align="right" style="color:#182f45;font-size:13px;font-weight:700;padding:8px 0;text-align:right">{escape(value)}</td>'
            "</tr>"
        )
        for label, value in details
    )
    detail_card = (
        '<table role="presentation" width="100%" cellspacing="0" cellpadding="0" '
        'style="background:#f3f7fb;border:1px solid #dce7f2;border-radius:8px;margin:22px 0">'
        f'<tbody>{detail_rows}</tbody></table>'
        if detail_rows
        else ""
    )
    action = ""
    if action_label and action_url:
        action = (
            '<table role="presentation" cellspacing="0" cellpadding="0" style="margin:28px 0 14px">'
            '<tr><td bgcolor="#1765a7" style="background:#1765a7;border-radius:7px">'
            f'<a href="{escape(action_url, quote=True)}" style="color:#ffffff;display:inline-block;'
            'font-size:14px;font-weight:700;letter-spacing:.01em;padding:14px 22px;text-decoration:none">'
            f"{escape(action_label)} &#8594;</a></td></tr></table>"
            '<p style="color:#7a8b9d;font-size:12px;line-height:1.55;margin:0">'
            "For security, this link can only be used once.</p>"
        )
    return f"""\
<!doctype html>
<html lang="en">
  <body style="background:#edf3fa;margin:0;padding:0">
    <div style="color:transparent;display:none;font-size:1px;line-height:1px;max-height:0;max-width:0;opacity:0;overflow:hidden">{escape(preview_text)}</div>
    <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background:#edf3fa;width:100%">
      <tr><td align="center" style="padding:32px 14px">
        <table role="presentation" width="600" cellspacing="0" cellpadding="0" style="max-width:600px;width:100%">
          <tr><td style="background:#123b65;border-radius:12px 12px 0 0;padding:24px 30px">
            <table role="presentation" width="100%" cellspacing="0" cellpadding="0">
              <tr>
                <td valign="middle" style="width:102px">
                  <img src="cid:{BRAND_LOGO_CID}" alt="{escape(brand_name)}" width="92" style="background:#ffffff;border-radius:7px;display:block;height:auto;width:92px" />
                </td>
                <td valign="middle">
                  <p style="color:#c9ddef;font-family:Arial,sans-serif;font-size:10px;font-weight:700;letter-spacing:.14em;margin:0 0 5px;text-transform:uppercase">{escape(eyebrow)}</p>
                  <p style="color:#ffffff;font-family:Arial,sans-serif;font-size:18px;font-weight:700;margin:0">{escape(brand_name)}</p>
                </td>
              </tr>
            </table>
          </td></tr>
          <tr><td style="background:#ffffff;padding:34px 30px 28px">
            <h1 style="color:#162b3d;font-family:Arial,sans-serif;font-size:27px;letter-spacing:-.02em;line-height:1.2;margin:0 0 18px">{escape(heading)}</h1>
            <div style="color:#4d6276;font-family:Arial,sans-serif;font-size:15px;line-height:1.7">{body}</div>
            {detail_card}
            {action}
          </td></tr>
          <tr><td style="background:#f8fafc;border-radius:0 0 12px 12px;padding:20px 30px">
            <p style="color:#718396;font-family:Arial,sans-serif;font-size:12px;line-height:1.6;margin:0">This is an automated message from {escape(brand_name)}. Please do not reply directly to this email.</p>
          </td></tr>
        </table>
      </td></tr>
    </table>
  </body>
</html>
"""


def send_password_reset_email(*, recipient: str, recipient_name: str, reset_url: str) -> None:
    settings = get_settings()
    greeting = escape(recipient_name or "there")
    expiration = settings.password_reset_minutes
    send_email(
        recipients=[recipient],
        subject=f"Reset your {settings.app_name} password",
        text=(
            f"Hello {recipient_name},\n\n"
            f"Use this link to reset your {settings.app_name} password: {reset_url}\n\n"
            f"This link expires in {expiration} minutes. If you did not request this, you can ignore this email."
        ),
        html=email_layout(
            heading="Reset your password",
            eyebrow="Account security",
            preview_text=f"Reset your {settings.app_name} password securely.",
            body=(
                f"<p>Hello {greeting},</p>"
                f"<p>We received a request to reset your {escape(settings.app_name)} password. "
                "Use the secure button below to choose a new password.</p>"
                "<p>If you did not request this, you can safely ignore this email—your password will remain unchanged.</p>"
            ),
            action_label="Reset password",
            action_url=reset_url,
            details=[
                ("Link expires", f"{expiration} minutes"),
                ("Account", recipient),
            ],
        ),
    )
