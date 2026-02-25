from sqlalchemy import (
    String,
    Integer,
    Float,
    Boolean,
    Text,
    ForeignKey,
    DateTime,
    Index,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import JSONB
from pgvector.sqlalchemy import Vector
from datetime import datetime
from typing import Optional, List
from app.models.base import Base, TimestampMixin, new_uuid


class Label(Base, TimestampMixin):
    __tablename__ = "labels"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    genre_tags: Mapped[Optional[dict]] = mapped_column(JSONB, default=dict)
    label_dna: Mapped[Optional[dict]] = mapped_column(JSONB)  # LabelDNAOutput
    pipeline_status: Mapped[str] = mapped_column(String(20), default="idle")
    pipeline_started_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    pipeline_completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)

    roster_memberships: Mapped[List["RosterMembership"]] = relationship(back_populates="label")
    clusters: Mapped[List["LabelCluster"]] = relationship(back_populates="label")
    recommendations: Mapped[List["Recommendation"]] = relationship(back_populates="label")
    feedback: Mapped[List["Feedback"]] = relationship(back_populates="label")


class Artist(Base, TimestampMixin):
    __tablename__ = "artists"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    bio: Mapped[Optional[str]] = mapped_column(Text)
    genre_tags: Mapped[Optional[dict]] = mapped_column(JSONB, default=list)
    image_url: Mapped[Optional[str]] = mapped_column(String(512))
    is_candidate: Mapped[bool] = mapped_column(Boolean, default=False)

    platform_accounts: Mapped[List["PlatformAccount"]] = relationship(back_populates="artist")
    roster_memberships: Mapped[List["RosterMembership"]] = relationship(back_populates="artist")
    snapshots: Mapped[List["Snapshot"]] = relationship(back_populates="artist")
    embeddings: Mapped[List["Embedding"]] = relationship(back_populates="artist")
    features: Mapped[List["ArtistFeature"]] = relationship(back_populates="artist")
    recommendations: Mapped[List["Recommendation"]] = relationship(back_populates="artist")
    llm_briefs: Mapped[List["ArtistLLMBrief"]] = relationship(back_populates="artist")


class PlatformAccount(Base, TimestampMixin):
    __tablename__ = "platform_accounts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    artist_id: Mapped[str] = mapped_column(ForeignKey("artists.id"), nullable=False)
    platform: Mapped[str] = mapped_column(String(50), nullable=False)  # youtube, spotify, tiktok
    platform_id: Mapped[str] = mapped_column(String(255), nullable=False)
    platform_url: Mapped[Optional[str]] = mapped_column(String(512))
    platform_metadata: Mapped[Optional[dict]] = mapped_column(JSONB, default=dict)

    artist: Mapped["Artist"] = relationship(back_populates="platform_accounts")

    __table_args__ = (
        UniqueConstraint("platform", "platform_id", name="uq_platform_account"),
    )


class RosterMembership(Base, TimestampMixin):
    __tablename__ = "roster_memberships"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    label_id: Mapped[str] = mapped_column(ForeignKey("labels.id"), nullable=False)
    artist_id: Mapped[str] = mapped_column(ForeignKey("artists.id"), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    label: Mapped["Label"] = relationship(back_populates="roster_memberships")
    artist: Mapped["Artist"] = relationship(back_populates="roster_memberships")

    __table_args__ = (
        UniqueConstraint("label_id", "artist_id", name="uq_roster_membership"),
    )


class Snapshot(Base):
    """Append-only time-series metrics snapshot."""
    __tablename__ = "snapshots"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    artist_id: Mapped[str] = mapped_column(ForeignKey("artists.id"), nullable=False)
    platform: Mapped[str] = mapped_column(String(50), nullable=False)
    captured_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    followers: Mapped[Optional[int]] = mapped_column(Integer)
    views: Mapped[Optional[int]] = mapped_column(Integer)
    likes: Mapped[Optional[int]] = mapped_column(Integer)
    comments: Mapped[Optional[int]] = mapped_column(Integer)
    shares: Mapped[Optional[int]] = mapped_column(Integer)
    engagement_rate: Mapped[Optional[float]] = mapped_column(Float)
    extra_metrics: Mapped[Optional[dict]] = mapped_column(JSONB, default=dict)

    artist: Mapped["Artist"] = relationship(back_populates="snapshots")

    __table_args__ = (
        Index("ix_snapshot_artist_platform_time", "artist_id", "platform", "captured_at"),
    )


class Embedding(Base, TimestampMixin):
    __tablename__ = "embeddings"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    artist_id: Mapped[str] = mapped_column(ForeignKey("artists.id"), nullable=False)
    provider: Mapped[str] = mapped_column(String(50), nullable=False, default="metric")
    vector = mapped_column(Vector(128))
    metadata_: Mapped[Optional[dict]] = mapped_column("metadata", JSONB, default=dict)

    artist: Mapped["Artist"] = relationship(back_populates="embeddings")

    __table_args__ = (
        Index("ix_embedding_artist_provider", "artist_id", "provider"),
    )


class LabelCluster(Base, TimestampMixin):
    __tablename__ = "label_clusters"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    label_id: Mapped[str] = mapped_column(ForeignKey("labels.id"), nullable=False)
    cluster_index: Mapped[int] = mapped_column(Integer, nullable=False)
    centroid = mapped_column(Vector(128))
    cluster_name: Mapped[Optional[str]] = mapped_column(String(255))
    artist_ids: Mapped[Optional[dict]] = mapped_column(JSONB, default=list)
    metadata_: Mapped[Optional[dict]] = mapped_column("metadata", JSONB, default=dict)

    label: Mapped["Label"] = relationship(back_populates="clusters")


class ArtistFeature(Base, TimestampMixin):
    __tablename__ = "artist_features"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    artist_id: Mapped[str] = mapped_column(ForeignKey("artists.id"), nullable=False)
    computed_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    growth_7d: Mapped[Optional[float]] = mapped_column(Float, default=0.0)
    growth_30d: Mapped[Optional[float]] = mapped_column(Float, default=0.0)
    acceleration: Mapped[Optional[float]] = mapped_column(Float, default=0.0)
    engagement_rate: Mapped[Optional[float]] = mapped_column(Float, default=0.0)
    momentum_score: Mapped[Optional[float]] = mapped_column(Float, default=0.0)
    risk_score: Mapped[Optional[float]] = mapped_column(Float, default=0.0)
    risk_flags: Mapped[Optional[dict]] = mapped_column(JSONB, default=list)
    extra: Mapped[Optional[dict]] = mapped_column(JSONB, default=dict)

    artist: Mapped["Artist"] = relationship(back_populates="features")

    __table_args__ = (
        Index("ix_artist_features_artist_time", "artist_id", "computed_at"),
    )


class Recommendation(Base, TimestampMixin):
    __tablename__ = "recommendations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    label_id: Mapped[str] = mapped_column(ForeignKey("labels.id"), nullable=False)
    artist_id: Mapped[str] = mapped_column(ForeignKey("artists.id"), nullable=False)
    batch_id: Mapped[str] = mapped_column(String(36), nullable=False)  # group recommendations per run

    fit_score: Mapped[float] = mapped_column(Float, nullable=False)
    momentum_score: Mapped[float] = mapped_column(Float, nullable=False)
    risk_score: Mapped[float] = mapped_column(Float, nullable=False)
    final_score: Mapped[float] = mapped_column(Float, nullable=False)

    nearest_cluster_id: Mapped[Optional[str]] = mapped_column(String(36))
    nearest_roster_artist_id: Mapped[Optional[str]] = mapped_column(String(36))
    score_breakdown: Mapped[Optional[dict]] = mapped_column(JSONB, default=dict)

    label: Mapped["Label"] = relationship(back_populates="recommendations")
    artist: Mapped["Artist"] = relationship(back_populates="recommendations")

    __table_args__ = (
        Index("ix_recommendation_label_batch", "label_id", "batch_id"),
    )


class Feedback(Base, TimestampMixin):
    __tablename__ = "feedback"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    label_id: Mapped[str] = mapped_column(ForeignKey("labels.id"), nullable=False)
    artist_id: Mapped[str] = mapped_column(ForeignKey("artists.id"), nullable=False)
    recommendation_id: Mapped[Optional[str]] = mapped_column(String(36))
    action: Mapped[str] = mapped_column(String(50), nullable=False)  # shortlist, pass, archive, sign
    notes: Mapped[Optional[str]] = mapped_column(Text)
    context: Mapped[Optional[dict]] = mapped_column(JSONB, default=dict)

    label: Mapped["Label"] = relationship(back_populates="feedback")


class ArtistLLMBrief(Base, TimestampMixin):
    __tablename__ = "artist_llm_briefs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    artist_id: Mapped[str] = mapped_column(ForeignKey("artists.id"), nullable=False)
    label_id: Mapped[Optional[str]] = mapped_column(String(36))
    input_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    brief: Mapped[dict] = mapped_column(JSONB, nullable=False)  # ArtistBriefOutput

    artist: Mapped["Artist"] = relationship(back_populates="llm_briefs")

    __table_args__ = (
        Index("ix_llm_brief_artist_hash", "artist_id", "input_hash"),
    )
