from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.models.tables import User
from app.models.base import new_uuid
from app.auth.google import verify_google_token
from app.auth.jwt import create_access_token
from app.auth.dependencies import get_current_user

auth_router = APIRouter(prefix="/auth", tags=["auth"])


class GoogleTokenInput(BaseModel):
    token: str


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict


class UserResponse(BaseModel):
    id: str
    email: str
    name: str | None
    picture: str | None

    class Config:
        from_attributes = True


@auth_router.post("/google", response_model=AuthResponse)
async def google_auth(data: GoogleTokenInput, db: AsyncSession = Depends(get_db)):
    try:
        google_info = verify_google_token(data.token)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid Google token")

    result = await db.execute(
        select(User).where(User.google_id == google_info["google_id"])
    )
    user = result.scalar_one_or_none()

    if not user:
        user = User(
            id=new_uuid(),
            google_id=google_info["google_id"],
            email=google_info["email"],
            name=google_info.get("name"),
            picture=google_info.get("picture"),
        )
        db.add(user)
        await db.flush()
    else:
        user.name = google_info.get("name") or user.name
        user.picture = google_info.get("picture") or user.picture
        await db.flush()

    await db.commit()

    access_token = create_access_token(user.id)
    return AuthResponse(
        access_token=access_token,
        user={
            "id": user.id,
            "email": user.email,
            "name": user.name,
            "picture": user.picture,
        },
    )


@auth_router.get("/me", response_model=UserResponse)
async def get_me(user: User = Depends(get_current_user)):
    return user
