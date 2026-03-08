from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.models.tables import User, EmailVerificationToken
from app.models.base import new_uuid
from app.auth.google import verify_google_token
from app.auth.jwt import create_access_token
from app.auth.dependencies import get_current_user
from app.auth.password import hash_password, verify_password, generate_token, hash_token
from app.services.email import send_verification_email, send_password_reset_email
from app.config import get_settings

auth_router = APIRouter(prefix="/auth", tags=["auth"])


# ---------- Schemas ----------

class GoogleTokenInput(BaseModel):
    token: str


class SignupInput(BaseModel):
    name: str
    email: EmailStr
    password: str


class SigninInput(BaseModel):
    email: EmailStr
    password: str


class VerifyEmailInput(BaseModel):
    token: str


class ForgotPasswordInput(BaseModel):
    email: EmailStr


class ResetPasswordInput(BaseModel):
    token: str
    password: str


class ResendVerificationInput(BaseModel):
    email: EmailStr


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict


class UserResponse(BaseModel):
    id: str
    email: str
    name: str | None
    picture: str | None
    email_verified: bool
    auth_provider: str

    class Config:
        from_attributes = True


class MessageResponse(BaseModel):
    message: str


# ---------- Helpers ----------

async def _create_and_send_verification_token(
    db: AsyncSession, user: User, token_type: str = "verify_email"
) -> None:
    settings = get_settings()
    raw_token = generate_token()

    if token_type == "verify_email":
        expiry_hours = settings.email_verification_expiry_hours
    else:
        expiry_hours = settings.password_reset_expiry_hours

    evt = EmailVerificationToken(
        id=new_uuid(),
        user_id=user.id,
        token_hash=hash_token(raw_token),
        token_type=token_type,
        expires_at=datetime.utcnow() + timedelta(hours=expiry_hours),
    )
    db.add(evt)
    await db.flush()

    if token_type == "verify_email":
        send_verification_email(user.email, user.name, raw_token)
    else:
        send_password_reset_email(user.email, user.name, raw_token)


async def _consume_token(db: AsyncSession, raw_token: str, expected_type: str) -> EmailVerificationToken:
    hashed = hash_token(raw_token)
    result = await db.execute(
        select(EmailVerificationToken).where(
            EmailVerificationToken.token_hash == hashed,
            EmailVerificationToken.token_type == expected_type,
        )
    )
    evt = result.scalar_one_or_none()

    if not evt:
        raise HTTPException(status_code=400, detail="Invalid token")
    if evt.used_at is not None:
        raise HTTPException(status_code=400, detail="Token already used")
    if evt.expires_at < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Token expired")

    evt.used_at = datetime.utcnow()
    await db.flush()
    return evt


# ---------- Email/Password Endpoints ----------

@auth_router.post("/signup", response_model=MessageResponse)
async def signup(data: SignupInput, db: AsyncSession = Depends(get_db)):
    if len(data.password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters")

    result = await db.execute(select(User).where(User.email == data.email))
    existing = result.scalar_one_or_none()

    if existing:
        if existing.auth_provider == "google":
            raise HTTPException(
                status_code=400,
                detail="This email is already registered with Google. Please sign in with Google.",
            )
        raise HTTPException(status_code=400, detail="Email already registered")

    user = User(
        id=new_uuid(),
        email=data.email,
        name=data.name,
        password_hash=hash_password(data.password),
        email_verified=False,
        auth_provider="email",
    )
    db.add(user)
    await db.flush()

    await _create_and_send_verification_token(db, user, "verify_email")
    await db.commit()

    return MessageResponse(message="Account created. Please check your email to verify.")


@auth_router.post("/signin", response_model=AuthResponse)
async def signin(data: SigninInput, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == data.email))
    user = result.scalar_one_or_none()

    if not user or not user.password_hash:
        raise HTTPException(status_code=401, detail="Invalid email or password")

    if not verify_password(data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account is deactivated")

    if not user.email_verified:
        raise HTTPException(status_code=403, detail="Please verify your email before signing in")

    access_token = create_access_token(user.id)
    return AuthResponse(
        access_token=access_token,
        user={
            "id": user.id,
            "email": user.email,
            "name": user.name,
            "picture": user.picture,
            "email_verified": user.email_verified,
            "auth_provider": user.auth_provider,
        },
    )


@auth_router.post("/verify-email", response_model=MessageResponse)
async def verify_email(data: VerifyEmailInput, db: AsyncSession = Depends(get_db)):
    evt = await _consume_token(db, data.token, "verify_email")

    user = await db.get(User, evt.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.email_verified = True
    await db.commit()

    return MessageResponse(message="Email verified successfully")


@auth_router.post("/forgot-password", response_model=MessageResponse)
async def forgot_password(data: ForgotPasswordInput, db: AsyncSession = Depends(get_db)):
    # Always return success to prevent email enumeration
    result = await db.execute(select(User).where(User.email == data.email))
    user = result.scalar_one_or_none()

    if user and user.password_hash:
        await _create_and_send_verification_token(db, user, "reset_password")
        await db.commit()

    return MessageResponse(message="If that email is registered, a reset link has been sent.")


@auth_router.post("/reset-password", response_model=MessageResponse)
async def reset_password(data: ResetPasswordInput, db: AsyncSession = Depends(get_db)):
    if len(data.password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters")

    evt = await _consume_token(db, data.token, "reset_password")

    user = await db.get(User, evt.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.password_hash = hash_password(data.password)
    await db.commit()

    return MessageResponse(message="Password reset successfully")


@auth_router.post("/resend-verification", response_model=MessageResponse)
async def resend_verification(data: ResendVerificationInput, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == data.email))
    user = result.scalar_one_or_none()

    if user and not user.email_verified and user.auth_provider == "email":
        await _create_and_send_verification_token(db, user, "verify_email")
        await db.commit()

    return MessageResponse(message="If that email needs verification, a new link has been sent.")


# ---------- Google OAuth (updated) ----------

@auth_router.post("/google", response_model=AuthResponse)
async def google_auth(data: GoogleTokenInput, db: AsyncSession = Depends(get_db)):
    try:
        google_info = verify_google_token(data.token)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid Google token")

    # Check if user exists by google_id
    result = await db.execute(
        select(User).where(User.google_id == google_info["google_id"])
    )
    user = result.scalar_one_or_none()

    if not user:
        # Check if an email-only user exists with the same email (account linking)
        result = await db.execute(
            select(User).where(User.email == google_info["email"])
        )
        user = result.scalar_one_or_none()

        if user:
            # Link Google account to existing email user
            user.google_id = google_info["google_id"]
            user.email_verified = True
            user.auth_provider = "google"
            user.name = google_info.get("name") or user.name
            user.picture = google_info.get("picture") or user.picture
            await db.flush()
        else:
            # Create new Google user
            user = User(
                id=new_uuid(),
                google_id=google_info["google_id"],
                email=google_info["email"],
                name=google_info.get("name"),
                picture=google_info.get("picture"),
                email_verified=True,
                auth_provider="google",
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
            "email_verified": user.email_verified,
            "auth_provider": user.auth_provider,
        },
    )


# ---------- Me ----------

@auth_router.get("/me", response_model=UserResponse)
async def get_me(user: User = Depends(get_current_user)):
    return user
