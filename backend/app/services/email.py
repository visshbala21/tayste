import httpx
from app.config import get_settings


def _send_email(to_email: str, subject: str, html: str) -> None:
    settings = get_settings()
    if not settings.sendgrid_api_key:
        raise RuntimeError("SENDGRID_API_KEY is not configured")

    httpx.post(
        "https://api.sendgrid.com/v3/mail/send",
        headers={
            "Authorization": f"Bearer {settings.sendgrid_api_key}",
            "Content-Type": "application/json",
        },
        json={
            "personalizations": [{"to": [{"email": to_email}]}],
            "from": {"email": settings.from_email},
            "subject": subject,
            "content": [{"type": "text/html", "value": html}],
        },
        timeout=15,
    ).raise_for_status()


def send_verification_email(to_email: str, name: str | None, token: str) -> None:
    settings = get_settings()
    verify_url = f"{settings.frontend_url}/verify-email?token={token}"

    _send_email(
        to_email=to_email,
        subject="Verify your Tayste account",
        html=f"""
        <div style="font-family: sans-serif; max-width: 480px; margin: 0 auto;">
            <h2>Welcome to Tayste{f', {name}' if name else ''}!</h2>
            <p>Please verify your email address by clicking the button below:</p>
            <a href="{verify_url}" style="display: inline-block; background: #7c3aed; color: white; padding: 12px 24px; border-radius: 8px; text-decoration: none; font-weight: 600;">
                Verify Email
            </a>
            <p style="margin-top: 24px; color: #666; font-size: 14px;">
                Or copy this link: {verify_url}
            </p>
            <p style="color: #999; font-size: 12px;">This link expires in {settings.email_verification_expiry_hours} hours.</p>
        </div>
        """,
    )


def send_password_reset_email(to_email: str, name: str | None, token: str) -> None:
    settings = get_settings()
    reset_url = f"{settings.frontend_url}/reset-password?token={token}"

    _send_email(
        to_email=to_email,
        subject="Reset your Tayste password",
        html=f"""
        <div style="font-family: sans-serif; max-width: 480px; margin: 0 auto;">
            <h2>Password Reset</h2>
            <p>Hi{f' {name}' if name else ''}, we received a request to reset your password.</p>
            <a href="{reset_url}" style="display: inline-block; background: #7c3aed; color: white; padding: 12px 24px; border-radius: 8px; text-decoration: none; font-weight: 600;">
                Reset Password
            </a>
            <p style="margin-top: 24px; color: #666; font-size: 14px;">
                Or copy this link: {reset_url}
            </p>
            <p style="color: #999; font-size: 12px;">This link expires in {settings.password_reset_expiry_hours} hour(s). If you didn't request this, ignore this email.</p>
        </div>
        """,
    )
