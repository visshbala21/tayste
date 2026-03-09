import jwt
from app.config import get_settings


def decode_supabase_token(token: str) -> dict:
    """Verify and decode a Supabase-issued JWT."""
    settings = get_settings()
    return jwt.decode(
        token,
        settings.supabase_jwt_secret,
        algorithms=["HS256"],
        audience="authenticated",
    )
