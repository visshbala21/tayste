"""Migrate from custom auth to Supabase Auth.

Drop email_verification_tokens table, replace users table with profiles table.
Update labels FK from users.id to profiles.id.

Revision ID: 008
Revises: 007
Create Date: 2026-03-08
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "008"
down_revision: Union[str, None] = "007"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Drop FK constraint on labels.user_id -> users.id
    op.drop_constraint("labels_user_id_fkey", "labels", type_="foreignkey")

    # 2. Drop email_verification_tokens table
    op.drop_table("email_verification_tokens")

    # 3. Create profiles table
    op.create_table(
        "profiles",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("email", sa.String(255), unique=True, nullable=False),
        sa.Column("name", sa.String(255), nullable=True),
        sa.Column("picture", sa.String(512), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now()),
    )

    # 4. Migrate existing user data into profiles
    op.execute("""
        INSERT INTO profiles (id, email, name, picture, is_active, created_at, updated_at)
        SELECT id, email, name, picture, is_active, created_at, updated_at
        FROM users
    """)

    # 5. Add FK constraint on labels.user_id -> profiles.id
    op.create_foreign_key(
        "labels_user_id_fkey", "labels", "profiles",
        ["user_id"], ["id"],
    )

    # 6. Drop old users table
    op.drop_table("users")


def downgrade() -> None:
    # Recreate users table
    op.create_table(
        "users",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("google_id", sa.String(255), unique=True, nullable=True),
        sa.Column("email", sa.String(255), unique=True, nullable=False),
        sa.Column("name", sa.String(255), nullable=True),
        sa.Column("picture", sa.String(512), nullable=True),
        sa.Column("password_hash", sa.String(255), nullable=True),
        sa.Column("email_verified", sa.Boolean(), server_default=sa.text("false")),
        sa.Column("auth_provider", sa.String(20), server_default=sa.text("'email'")),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now()),
    )

    # Migrate profile data back
    op.execute("""
        INSERT INTO users (id, email, name, picture, is_active, created_at, updated_at, email_verified, auth_provider)
        SELECT id, email, name, picture, is_active, created_at, updated_at, true, 'email'
        FROM profiles
    """)

    # Drop FK and re-create for users
    op.drop_constraint("labels_user_id_fkey", "labels", type_="foreignkey")
    op.create_foreign_key(
        "labels_user_id_fkey", "labels", "users",
        ["user_id"], ["id"],
    )

    # Drop profiles
    op.drop_table("profiles")

    # Recreate email_verification_tokens
    op.create_table(
        "email_verification_tokens",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("token_hash", sa.String(255), unique=True, nullable=False),
        sa.Column("token_type", sa.String(20), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("used_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
    )
