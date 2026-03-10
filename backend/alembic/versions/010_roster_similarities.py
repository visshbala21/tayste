"""Add roster_similarities JSONB column to recommendations table.

Stores {roster_artist_id: normalized_cosine_similarity} for filtering by
similarity to specific roster artists.

Revision ID: 010
Revises: 009
Create Date: 2026-03-09
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB


# revision identifiers, used by Alembic.
revision: str = "010"
down_revision: Union[str, None] = "009"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "recommendations",
        sa.Column("roster_similarities", JSONB, nullable=True),
    )


def downgrade() -> None:
    op.drop_column("recommendations", "roster_similarities")
