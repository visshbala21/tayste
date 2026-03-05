"""Add cultural signals and artist cultural profiles tables

Revision ID: 007
Revises: 006
Create Date: 2026-03-04
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "007"
down_revision: Union[str, None] = "006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "cultural_signals",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("artist_id", sa.String(36), sa.ForeignKey("artists.id"), nullable=False),
        sa.Column("platform", sa.String(50), nullable=False),
        sa.Column("source_type", sa.String(50), nullable=False),
        sa.Column("source_id", sa.String(255), nullable=False),
        sa.Column("captured_at", sa.DateTime(), nullable=False),
        sa.Column("comment_count", sa.Integer(), nullable=True),
        sa.Column("view_count", sa.Integer(), nullable=True),
        sa.Column("like_count", sa.Integer(), nullable=True),
        sa.Column("reply_count", sa.Integer(), nullable=True),
        sa.Column("unique_commenters", sa.Integer(), nullable=True),
        sa.Column("repeat_commenters", sa.Integer(), nullable=True),
        sa.Column("sampled_comments", sa.JSON(), nullable=True),
        sa.Column("rule_sentiment", sa.JSON(), nullable=True),
        sa.Column("extra", sa.JSON(), nullable=True),
        sa.UniqueConstraint("artist_id", "platform", "source_id", name="uq_cultural_signal"),
    )
    op.create_index("ix_cultural_signal_artist_time", "cultural_signals", ["artist_id", "captured_at"])

    op.create_table(
        "artist_cultural_profiles",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("artist_id", sa.String(36), sa.ForeignKey("artists.id"), nullable=False),
        sa.Column("computed_at", sa.DateTime(), nullable=False),
        sa.Column("input_hash", sa.String(64), nullable=False),
        sa.Column("sentiment_strength", sa.Float(), nullable=True, server_default=sa.text("0.0")),
        sa.Column("engagement_density", sa.Float(), nullable=True, server_default=sa.text("0.0")),
        sa.Column("superfan_density", sa.Float(), nullable=True, server_default=sa.text("0.0")),
        sa.Column("cross_platform_presence", sa.Float(), nullable=True, server_default=sa.text("0.0")),
        sa.Column("thematic_clarity", sa.Float(), nullable=True, server_default=sa.text("0.0")),
        sa.Column("polarization_index", sa.Float(), nullable=True, server_default=sa.text("0.0")),
        sa.Column("cultural_energy", sa.Float(), nullable=True, server_default=sa.text("0.0")),
        sa.Column("breakout_candidate", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("sentiment_distribution", sa.JSON(), nullable=True),
        sa.Column("cultural_profile", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_cultural_profile_artist_time", "artist_cultural_profiles", ["artist_id", "computed_at"])
    op.create_index("ix_cultural_profile_hash", "artist_cultural_profiles", ["artist_id", "input_hash"])


def downgrade() -> None:
    op.drop_index("ix_cultural_profile_hash", table_name="artist_cultural_profiles")
    op.drop_index("ix_cultural_profile_artist_time", table_name="artist_cultural_profiles")
    op.drop_table("artist_cultural_profiles")
    op.drop_index("ix_cultural_signal_artist_time", table_name="cultural_signals")
    op.drop_table("cultural_signals")
