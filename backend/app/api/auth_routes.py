from fastapi import APIRouter, Depends
from pydantic import BaseModel
from app.models.tables import Profile
from app.auth.dependencies import get_current_user

auth_router = APIRouter(prefix="/auth", tags=["auth"])


class UserResponse(BaseModel):
    id: str
    email: str
    name: str | None
    picture: str | None

    class Config:
        from_attributes = True


@auth_router.get("/me", response_model=UserResponse)
async def get_me(user: Profile = Depends(get_current_user)):
    return user
