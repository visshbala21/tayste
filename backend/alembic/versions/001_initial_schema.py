"""Initial schema

Revision ID: 001
Revises: None
Create Date: 2025-01-01
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Enable pgvector extension
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.create_table(
        "labels",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text),
        sa.Column("genre_tags", postgresql.JSONB, server_default="{}"),
        sa.Column("label_dna", postgresql.JSONB),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now()),
    )

    op.create_table(
        "artists",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("bio", sa.Text),
        sa.Column("genre_tags", postgresql.JSONB, server_default="[]"),
        sa.Column("image_url", sa.String(512)),
        sa.Column("is_candidate", sa.Boolean, server_default="false"),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now()),
    )

    op.create_table(
        "platform_accounts",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("artist_id", sa.String(36), sa.ForeignKey("artists.id"), nullable=False),
        sa.Column("platform", sa.String(50), nullable=False),
        sa.Column("platform_id", sa.String(255), nullable=False),
        sa.Column("platform_url", sa.String(512)),
        sa.Column("platform_metadata", postgresql.JSONB, server_default="{}"),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now()),
        sa.UniqueConstraint("platform", "platform_id", name="uq_platform_account"),
    )

    op.create_table(
        "roster_memberships",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("label_id", sa.String(36), sa.ForeignKey("labels.id"), nullable=False),
        sa.Column("artist_id", sa.String(36), sa.ForeignKey("artists.id"), nullable=False),
        sa.Column("is_active", sa.Boolean, server_default="true"),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now()),
        sa.UniqueConstraint("label_id", "artist_id", name="uq_roster_membership"),
    )

    op.create_table(
        "snapshots",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("artist_id", sa.String(36), sa.ForeignKey("artists.id"), nullable=False),
        sa.Column("platform", sa.String(50), nullable=False),
        sa.Column("captured_at", sa.DateTime, nullable=False),
        sa.Column("followers", sa.Integer),
        sa.Column("views", sa.Integer),
        sa.Column("likes", sa.Integer),
        sa.Column("comments", sa.Integer),
        sa.Column("shares", sa.Integer),
        sa.Column("engagement_rate", sa.Float),
        sa.Column("extra_metrics", postgresql.JSONB, server_default="{}"),
    )
    op.create_index("ix_snapshot_artist_platform_time", "snapshots", ["artist_id", "platform", "captured_at"])

    op.execute("""
        CREATE TABLE embeddings (
            id VARCHAR(36) PRIMARY KEY,
            artist_id VARCHAR(36) NOT NULL REFERENCES artists(id),
            provider VARCHAR(50) NOT NULL DEFAULT 'metric',
            vector vector(128),
            metadata JSONB DEFAULT '{}',
            created_at TIMESTAMP DEFAULT now(),
            updated_at TIMESTAMP DEFAULT now()
        )
    """)
    op.create_index("ix_embedding_artist_provider", "embeddings", ["artist_id", "provider"])

    op.execute("""
        CREATE TABLE label_clusters (
            id VARCHAR(36) PRIMARY KEY,
            label_id VARCHAR(36) NOT NULL REFERENCES labels(id),
            cluster_index INTEGER NOT NULL,
            centroid vector(128),
            cluster_name VARCHAR(255),
            artist_ids JSONB DEFAULT '[]',
            metadata JSONB DEFAULT '{}',
            created_at TIMESTAMP DEFAULT now(),
            updated_at TIMESTAMP DEFAULT now()
        )
    """)

    op.create_table(
        "artist_features",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("artist_id", sa.String(36), sa.ForeignKey("artists.id"), nullable=False),
        sa.Column("computed_at", sa.DateTime, nullable=False),
        sa.Column("growth_7d", sa.Float, server_default="0"),
        sa.Column("growth_30d", sa.Float, server_default="0"),
        sa.Column("acceleration", sa.Float, server_default="0"),
        sa.Column("engagement_rate", sa.Float, server_default="0"),
        sa.Column("momentum_score", sa.Float, server_default="0"),
        sa.Column("risk_score", sa.Float, server_default="0"),
        sa.Column("risk_flags", postgresql.JSONB, server_default="[]"),
        sa.Column("extra", postgresql.JSONB, server_default="{}"),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now()),
    )
    op.create_index("ix_artist_features_artist_time", "artist_features", ["artist_id", "computed_at"])

    op.create_table(
        "recommendations",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("label_id", sa.String(36), sa.ForeignKey("labels.id"), nullable=False),
        sa.Column("artist_id", sa.String(36), sa.ForeignKey("artists.id"), nullable=False),
        sa.Column("batch_id", sa.String(36), nullable=False),
        sa.Column("fit_score", sa.Float, nullable=False),
        sa.Column("momentum_score", sa.Float, nullable=False),
        sa.Column("risk_score", sa.Float, nullable=False),
        sa.Column("final_score", sa.Float, nullable=False),
        sa.Column("nearest_cluster_id", sa.String(36)),
        sa.Column("nearest_roster_artist_id", sa.String(36)),
        sa.Column("score_breakdown", postgresql.JSONB, server_default="{}"),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now()),
    )
    op.create_index("ix_recommendation_label_batch", "recommendations", ["label_id", "batch_id"])

    op.create_table(
        "feedback",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("label_id", sa.String(36), sa.ForeignKey("labels.id"), nullable=False),
        sa.Column("artist_id", sa.String(36), sa.ForeignKey("artists.id"), nullable=False),
        sa.Column("recommendation_id", sa.String(36)),
        sa.Column("action", sa.String(50), nullable=False),
        sa.Column("notes", sa.Text),
        sa.Column("context", postgresql.JSONB, server_default="{}"),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now()),
    )

    op.create_table(
        "artist_llm_briefs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("artist_id", sa.String(36), sa.ForeignKey("artists.id"), nullable=False),
        sa.Column("label_id", sa.String(36)),
        sa.Column("input_hash", sa.String(64), nullable=False),
        sa.Column("brief", postgresql.JSONB, nullable=False),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now()),
    )
    op.create_index("ix_llm_brief_artist_hash", "artist_llm_briefs", ["artist_id", "input_hash"])


def downgrade() -> None:
    op.drop_table("artist_llm_briefs")
    op.drop_table("feedback")
    op.drop_table("recommendations")
    op.drop_table("artist_features")
    op.execute("DROP TABLE label_clusters")
    op.drop_table("embeddings")
    op.drop_table("snapshots")
    op.drop_table("roster_memberships")
    op.drop_table("platform_accounts")
    op.drop_table("artists")
    op.drop_table("labels")
