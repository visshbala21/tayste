"""Add batch_id to label_clusters for per-run history.

Revision ID: 011
Revises: 010
Create Date: 2026-03-09
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "011"
down_revision: Union[str, None] = "010"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "label_clusters",
        sa.Column("batch_id", sa.String(36), nullable=True),
    )
    op.create_index(
        "ix_label_cluster_batch",
        "label_clusters",
        ["label_id", "batch_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_label_cluster_batch", table_name="label_clusters")
    op.drop_column("label_clusters", "batch_id")
