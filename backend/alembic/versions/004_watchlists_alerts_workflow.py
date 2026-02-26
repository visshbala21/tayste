"""Add watchlists, alerts, and workflow state

Revision ID: 004
Revises: 003
Create Date: 2026-02-26
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "004"
down_revision: Union[str, None] = "003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "label_artist_states",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("label_id", sa.String(36), sa.ForeignKey("labels.id"), nullable=False),
        sa.Column("artist_id", sa.String(36), sa.ForeignKey("artists.id"), nullable=False),
        sa.Column("stage", sa.String(32), nullable=False, server_default="new"),
        sa.Column("notes", sa.Text),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now()),
        sa.UniqueConstraint("label_id", "artist_id", name="uq_label_artist_state"),
    )
    op.create_index("ix_label_artist_state_label_stage", "label_artist_states", ["label_id", "stage"])

    op.create_table(
        "watchlists",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("label_id", sa.String(36), sa.ForeignKey("labels.id"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text),
        sa.Column("is_active", sa.Boolean, server_default="true"),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now()),
        sa.UniqueConstraint("label_id", "name", name="uq_watchlist_label_name"),
    )
    op.create_index("ix_watchlist_label", "watchlists", ["label_id"])

    op.create_table(
        "watchlist_items",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("watchlist_id", sa.String(36), sa.ForeignKey("watchlists.id"), nullable=False),
        sa.Column("artist_id", sa.String(36), sa.ForeignKey("artists.id"), nullable=False),
        sa.Column("source", sa.String(50), server_default="manual"),
        sa.Column("notes", sa.Text),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now()),
        sa.UniqueConstraint("watchlist_id", "artist_id", name="uq_watchlist_item"),
    )
    op.create_index("ix_watchlist_item_watchlist", "watchlist_items", ["watchlist_id"])

    op.create_table(
        "alert_rules",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("label_id", sa.String(36), sa.ForeignKey("labels.id"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("severity", sa.String(20), server_default="medium"),
        sa.Column("is_active", sa.Boolean, server_default="true"),
        sa.Column("criteria", postgresql.JSONB, server_default="{}"),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now()),
    )
    op.create_index("ix_alert_rule_label", "alert_rules", ["label_id"])

    op.create_table(
        "alerts",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("label_id", sa.String(36), sa.ForeignKey("labels.id"), nullable=False),
        sa.Column("artist_id", sa.String(36), sa.ForeignKey("artists.id"), nullable=False),
        sa.Column("watchlist_id", sa.String(36), sa.ForeignKey("watchlists.id")),
        sa.Column("rule_id", sa.String(36), sa.ForeignKey("alert_rules.id")),
        sa.Column("severity", sa.String(20), server_default="medium"),
        sa.Column("status", sa.String(20), server_default="new"),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text),
        sa.Column("context", postgresql.JSONB, server_default="{}"),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now()),
    )
    op.create_index("ix_alert_label_status_created", "alerts", ["label_id", "status", "created_at"])


def downgrade() -> None:
    op.drop_index("ix_alert_label_status_created", table_name="alerts")
    op.drop_table("alerts")
    op.drop_index("ix_alert_rule_label", table_name="alert_rules")
    op.drop_table("alert_rules")
    op.drop_index("ix_watchlist_item_watchlist", table_name="watchlist_items")
    op.drop_table("watchlist_items")
    op.drop_index("ix_watchlist_label", table_name="watchlists")
    op.drop_table("watchlists")
    op.drop_index("ix_label_artist_state_label_stage", table_name="label_artist_states")
    op.drop_table("label_artist_states")
