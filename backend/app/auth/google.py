from google.oauth2 import id_token
from google.auth.transport import requests
from app.config import get_settings


def verify_google_token(token: str) -> dict:
    """Verify a Google ID token and return the payload (sub, email, name, picture)."""
    settings = get_settings()
    idinfo = id_token.verify_oauth2_token(
        token, requests.Request(), settings.google_client_id
    )
    return {
        "google_id": idinfo["sub"],
        "email": idinfo["email"],
        "name": idinfo.get("name"),
        "picture": idinfo.get("picture"),
    }
