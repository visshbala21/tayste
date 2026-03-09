from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.models.tables import Profile, Label
from app.auth.jwt import decode_supabase_token

bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> Profile:
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )
    token = credentials.credentials
    try:
        payload = decode_supabase_token(token)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")
    profile = await db.get(Profile, user_id)
    if not profile or not profile.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive")
    return profile


async def get_optional_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> Profile | None:
    """Like get_current_user but returns None instead of raising 401."""
    if credentials is None:
        return None
    try:
        payload = decode_supabase_token(credentials.credentials)
    except Exception:
        return None
    user_id = payload.get("sub")
    if not user_id:
        return None
    profile = await db.get(Profile, user_id)
    if not profile or not profile.is_active:
        return None
    return profile


async def verify_label_ownership(label: Label, user: Profile | None) -> None:
    if user is None:
        return  # No auth = no ownership check
    # Labels with no owner (user_id=NULL) are accessible to any authenticated user
    if label.user_id is not None and label.user_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this label",
        )
