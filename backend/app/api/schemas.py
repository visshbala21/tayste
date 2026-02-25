from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


# --- Label ---

class LabelCreate(BaseModel):
    name: str
    description: Optional[str] = None
    genre_tags: Optional[dict] = None


class LabelResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    genre_tags: Optional[dict]
    label_dna: Optional[dict]
    pipeline_status: Optional[str] = None
    pipeline_started_at: Optional[datetime] = None
    pipeline_completed_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


# --- Roster ---

class RosterArtist(BaseModel):
    name: str
    platform: str = "youtube"
    platform_id: str
    platform_url: Optional[str] = None
    genre_tags: Optional[list] = None


class RosterInput(BaseModel):
    artists: List[RosterArtist]


# --- Roster Import ---

class RosterParsedArtist(BaseModel):
    name: str
    platform: Optional[str] = None
    platform_id: Optional[str] = None
    platform_url: Optional[str] = None
    genre_tags: Optional[list] = None


class RosterParseOutput(BaseModel):
    artists: List[RosterParsedArtist]


class RosterImportInput(BaseModel):
    raw_text: str
    default_platform: str = "youtube"
    resolve_missing: bool = True
    dry_run: bool = False
    run_pipeline: bool = False


class RosterConfirmInput(BaseModel):
    label: LabelCreate
    artists: List[RosterParsedArtist]
    default_platform: str = "youtube"
    run_pipeline: bool = False


class RosterConfirmExistingInput(BaseModel):
    artists: List[RosterParsedArtist]
    default_platform: str = "youtube"
    run_pipeline: bool = False


class LabelImportInput(BaseModel):
    label: LabelCreate
    raw_text: str
    default_platform: str = "youtube"
    resolve_missing: bool = True
    dry_run: bool = False
    run_pipeline: bool = False


class RosterImportResult(BaseModel):
    label_id: Optional[str] = None
    label_name: Optional[str] = None
    parsed_count: int
    created_count: int
    skipped_count: int
    parsed: List[RosterParsedArtist]
    created: List[dict]
    skipped: List[dict]
    warnings: List[str] = []


# --- Artist ---

class PlatformAccountResponse(BaseModel):
    platform: str
    platform_id: str
    platform_url: Optional[str]

    class Config:
        from_attributes = True


class SnapshotResponse(BaseModel):
    platform: str
    captured_at: datetime
    followers: Optional[int]
    views: Optional[int]
    likes: Optional[int]
    comments: Optional[int]
    engagement_rate: Optional[float]

    class Config:
        from_attributes = True


class ArtistFeatureResponse(BaseModel):
    computed_at: datetime
    growth_7d: Optional[float]
    growth_30d: Optional[float]
    acceleration: Optional[float]
    engagement_rate: Optional[float]
    momentum_score: Optional[float]
    risk_score: Optional[float]
    risk_flags: Optional[list]

    class Config:
        from_attributes = True


class ArtistResponse(BaseModel):
    id: str
    name: str
    bio: Optional[str]
    genre_tags: Optional[list]
    image_url: Optional[str]
    is_candidate: bool
    platform_accounts: List[PlatformAccountResponse] = []
    created_at: datetime

    class Config:
        from_attributes = True


class ArtistDetailResponse(ArtistResponse):
    snapshots: List[SnapshotResponse] = []
    latest_features: Optional[ArtistFeatureResponse] = None
    llm_brief: Optional[dict] = None
    feedback_history: Optional[list] = []


# --- Scout Feed ---

class ScoutFeedItem(BaseModel):
    artist_id: str
    artist_name: str
    image_url: Optional[str]
    fit_score: float
    momentum_score: float
    risk_score: float
    final_score: float
    nearest_roster_artist: Optional[str]
    growth_7d: Optional[float]
    growth_30d: Optional[float]
    genre_tags: Optional[list]


class ScoutFeedResponse(BaseModel):
    label_id: str
    batch_id: str
    items: List[ScoutFeedItem]
    total: int


# --- Taste Map ---

class ClusterInfo(BaseModel):
    cluster_id: str
    cluster_index: int
    cluster_name: Optional[str]
    artist_ids: list
    centroid: Optional[list] = None


class TasteMapResponse(BaseModel):
    label_id: str
    label_name: str
    label_dna: Optional[dict]
    clusters: List[ClusterInfo]


# --- Feedback ---

class FeedbackInput(BaseModel):
    artist_id: str
    recommendation_id: Optional[str] = None
    action: str = Field(..., pattern="^(shortlist|pass|archive|sign)$")
    notes: Optional[str] = None
    context: Optional[dict] = None


class FeedbackResponse(BaseModel):
    id: str
    label_id: str
    artist_id: str
    action: str
    notes: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


# --- LLM ---

class LabelDNAOutput(BaseModel):
    cluster_names: List[str]
    label_thesis_bullets: List[str]
    search_seed_queries: List[str]


class QueryExpansionOutput(BaseModel):
    youtube_queries: List[str]
    tiktok_tags: List[str]


class ArtistBriefOutput(BaseModel):
    what_is_happening: str
    why_fit: str
    risks_unknowns: str
    next_actions: List[str]
