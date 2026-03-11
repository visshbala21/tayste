"""Add label_candidates junction table for per-label candidate tracking.

Revision ID: 012
Revises: 011
Create Date: 2026-03-11
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "012"
down_revision: Union[str, None] = "011"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "label_candidates",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("label_id", sa.String(36), sa.ForeignKey("labels.id"), nullable=False),
        sa.Column("artist_id", sa.String(36), sa.ForeignKey("artists.id"), nullable=False),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.UniqueConstraint("label_id", "artist_id", name="uq_label_candidate"),
    )
    op.create_index(
        "ix_label_candidate_label",
        "label_candidates",
        ["label_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_label_candidate_label", table_name="label_candidates")
    op.drop_table("label_candidates")
