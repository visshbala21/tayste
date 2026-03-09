"""Add discovery_mode column to labels table.

Supports 'emerging' (strict micro-artist filters) and 'open' (relaxed filters for established labels).

Revision ID: 009
Revises: 008
Create Date: 2026-03-08
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "009"
down_revision: Union[str, None] = "008"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "labels",
        sa.Column("discovery_mode", sa.String(20), nullable=False, server_default="emerging"),
    )


def downgrade() -> None:
    op.drop_column("labels", "discovery_mode")
