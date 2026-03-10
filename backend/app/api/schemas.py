from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


# --- User ---

class UserResponse(BaseModel):
    id: str
    email: str
    name: Optional[str]
    picture: Optional[str]

    class Config:
        from_attributes = True


# --- Label ---

class LabelCreate(BaseModel):
    name: str
    description: Optional[str] = None
    genre_tags: Optional[dict] = None
    discovery_mode: Optional[str] = "emerging"


class LabelResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    genre_tags: Optional[dict]
    label_dna: Optional[dict]
    discovery_mode: Optional[str] = None
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

class PlatformEntry(BaseModel):
    platform: str
    platform_id: Optional[str] = None
    platform_url: Optional[str] = None


class RosterParsedArtist(BaseModel):
    name: str
    platform: Optional[str] = None
    platform_id: Optional[str] = None
    platform_url: Optional[str] = None
    genre_tags: Optional[list] = None
    additional_platforms: Optional[List[PlatformEntry]] = None


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
    extra: Optional[dict] = None

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


class CulturalProfileResponse(BaseModel):
    cultural_energy: Optional[float] = None
    sentiment: Optional[dict] = None
    engagement: Optional[dict] = None
    superfans: Optional[dict] = None
    cross_platform: Optional[dict] = None
    cultural_identity: Optional[dict] = None
    persona: Optional[dict] = None
    polarization: Optional[dict] = None
    evidence_snippets: Optional[List[dict]] = None
    breakout_signals: Optional[dict] = None
    fan_community: Optional[str] = None
    scores: Optional[dict] = None


class ArtistDetailResponse(ArtistResponse):
    snapshots: List[SnapshotResponse] = []
    latest_features: Optional[ArtistFeatureResponse] = None
    llm_brief: Optional[dict] = None
    feedback_history: Optional[list] = []
    label_stage: Optional[str] = None
    cultural_profile: Optional[CulturalProfileResponse] = None


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
    score_breakdown: Optional[dict] = None
    reasons: Optional[List[str]] = None
    stage: Optional[str] = None
    cultural_energy: Optional[float] = None
    breakout_candidate: Optional[bool] = None
    cultural_highlights: Optional[List[str]] = None
    roster_similarities: Optional[dict] = None


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
    artist_names: Optional[List[str]] = None
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


# --- Watchlists ---

class WatchlistCreate(BaseModel):
    name: str
    description: Optional[str] = None


class WatchlistResponse(BaseModel):
    id: str
    label_id: str
    name: str
    description: Optional[str]
    is_active: bool
    item_count: int = 0
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class WatchlistItemInput(BaseModel):
    artist_id: str
    notes: Optional[str] = None


class WatchlistItemResponse(BaseModel):
    artist_id: str
    artist_name: str
    image_url: Optional[str]
    stage: Optional[str]
    added_at: datetime
    notes: Optional[str] = None


class WatchlistDetailResponse(BaseModel):
    watchlist: WatchlistResponse
    items: List[WatchlistItemResponse]


# --- Alerts ---

class AlertStatusInput(BaseModel):
    status: str = Field(..., pattern="^(new|seen|dismissed)$")


class AlertResponse(BaseModel):
    id: str
    label_id: str
    artist_id: str
    artist_name: str
    rule_id: Optional[str]
    severity: str
    status: str
    title: str
    description: Optional[str]
    created_at: datetime
    context: Optional[dict] = None


# --- Workflow ---

class StageUpdateInput(BaseModel):
    stage: str = Field(..., pattern="^(new|review|shortlist|sign|pass|archive)$")
    notes: Optional[str] = None


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


# --- Simple Import ---

class SimpleImportInput(BaseModel):
    label_name: str
    artist_text: str


class ResolvedArtistProfile(BaseModel):
    name: str
    query_name: str
    image_url: Optional[str] = None
    genres: Optional[List[str]] = None
    spotify: Optional[PlatformEntry] = None
    youtube: Optional[PlatformEntry] = None
    soundcharts: Optional[PlatformEntry] = None
    spotify_followers: Optional[int] = None
    spotify_popularity: Optional[int] = None
    resolved: bool = False


class SimpleImportResolveResult(BaseModel):
    artists: List[ResolvedArtistProfile]
    warnings: List[str] = []


class SimpleImportConfirmInput(BaseModel):
    label_name: str
    artists: List[ResolvedArtistProfile]
    run_pipeline: bool = False
    discovery_mode: str = "emerging"
