"""Add label pipeline status

Revision ID: 002
Revises: 001
Create Date: 2026-02-24
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("labels", sa.Column("pipeline_status", sa.String(20), server_default="idle"))
    op.add_column("labels", sa.Column("pipeline_started_at", sa.DateTime()))
    op.add_column("labels", sa.Column("pipeline_completed_at", sa.DateTime()))


def downgrade() -> None:
    op.drop_column("labels", "pipeline_completed_at")
    op.drop_column("labels", "pipeline_started_at")
    op.drop_column("labels", "pipeline_status")
