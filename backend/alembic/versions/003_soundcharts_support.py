"""Add index for platform account lookups

Revision ID: 003
Revises: 002
Create Date: 2026-02-25
"""
from typing import Sequence, Union
from alembic import op

revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index(
        "ix_platform_accounts_platform_platformid",
        "platform_accounts",
        ["platform", "platform_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_platform_accounts_platform_platformid", table_name="platform_accounts")
