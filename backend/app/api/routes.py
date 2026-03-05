import json
import logging
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.models.tables import (
    Label, Artist, PlatformAccount, RosterMembership,
    Snapshot, LabelCluster, ArtistFeature, Recommendation,
    Feedback, ArtistLLMBrief, Watchlist, WatchlistItem, Alert, LabelArtistState,
    AlertRule, User, ArtistCulturalProfile,
)
from app.models.base import new_uuid
from app.api.schemas import (
    LabelCreate, LabelResponse, RosterInput, RosterArtist,
    ArtistResponse, ArtistDetailResponse, PlatformAccountResponse,
    SnapshotResponse, ArtistFeatureResponse,
    ScoutFeedResponse, ScoutFeedItem,
    TasteMapResponse, ClusterInfo,
    FeedbackInput, FeedbackResponse,
    WatchlistCreate, WatchlistResponse, WatchlistDetailResponse,
    WatchlistItemInput, WatchlistItemResponse,
    AlertResponse, AlertStatusInput, StageUpdateInput,
    LabelImportInput, RosterImportInput, RosterImportResult, RosterParsedArtist,
    RosterConfirmInput, RosterConfirmExistingInput, CulturalProfileResponse,
)
from app.llm.roster_parse import parse_roster_text
from app.connectors.identity import detect_platform_from_url, extract_platform_id
from app.services.pipeline_queue import pipeline_queue
from app.services.roster_files import extract_text_from_upload
from app.auth.dependencies import get_current_user, get_optional_user, verify_label_ownership

logger = logging.getLogger(__name__)
router = APIRouter()


def _extract_youtube_channel_id(url: str) -> str | None:
    if not url:
        return None
    marker = "/channel/"
    if marker in url:
        part = url.split(marker, 1)[1]
        channel_id = part.split("/", 1)[0]
        if channel_id.startswith("UC"):
            return channel_id
    return None


def _format_growth(value: float | None) -> str | None:
    if value is None:
        return None
    sign = "+" if value > 0 else ""
    return f"{sign}{abs(value) * 100:.0f}%"


async def _ensure_default_watchlist(db: AsyncSession, label_id: str) -> Watchlist:
    result = await db.execute(
        select(Watchlist).where(Watchlist.label_id == label_id).limit(1)
    )
    watchlist = result.scalar_one_or_none()
    if watchlist:
        return watchlist
    watchlist = Watchlist(
        id=new_uuid(),
        label_id=label_id,
        name="Pipeline",
        description="Default watchlist for active scouting.",
        is_active=True,
    )
    db.add(watchlist)
    await db.flush()
    return watchlist


async def _upsert_stage(
    db: AsyncSession,
    label_id: str,
    artist_id: str,
    stage: str,
    notes: str | None = None,
) -> LabelArtistState:
    result = await db.execute(
        select(LabelArtistState).where(
            LabelArtistState.label_id == label_id,
            LabelArtistState.artist_id == artist_id,
        )
    )
    state = result.scalar_one_or_none()
    if state:
        state.stage = stage
        if notes:
            state.notes = notes
    else:
        state = LabelArtistState(
            id=new_uuid(),
            label_id=label_id,
            artist_id=artist_id,
            stage=stage,
            notes=notes,
        )
        db.add(state)
    await db.flush()
    return state


async def _resolve_missing_platform_ids(
    entries: list[RosterParsedArtist],
    default_platform: str,
) -> tuple[list[RosterParsedArtist], list[str]]:
    warnings: list[str] = []

    for entry in entries:
        platform = (entry.platform or default_platform).lower()
        if platform in {"none", "null", "unknown", ""}:
            platform = default_platform
        entry.platform = platform

        if platform in {"none", "null", "unknown", ""}:
            platform = default_platform
            entry.platform = platform

        if entry.platform_url:
            detected = detect_platform_from_url(entry.platform_url)
            if detected and detected != platform:
                platform = detected
                entry.platform = platform

        if entry.platform_url and not entry.platform_id:
            entry.platform_id = extract_platform_id(platform, entry.platform_url) or entry.platform_id

        if platform != "youtube":
            continue

        if entry.platform_id:
            continue

        if entry.platform_url:
            channel_id = _extract_youtube_channel_id(entry.platform_url)
            if channel_id:
                entry.platform_id = channel_id
                continue

        warnings.append(
            f"Missing YouTube channel ID for '{entry.name}'. "
            "Automatic YouTube lookups are disabled; provide a channel URL or ID explicitly."
        )

    return entries, warnings


async def _upsert_roster_entries(
    db: AsyncSession,
    label_id: str,
    entries: list[RosterParsedArtist],
    default_platform: str,
) -> tuple[list[dict], list[dict], list[str]]:
    created: list[dict] = []
    skipped: list[dict] = []
    warnings: list[str] = []

    for entry in entries:
        name = (entry.name or "").strip()
        if not name:
            skipped.append({"name": entry.name or "", "reason": "missing_name"})
            continue

        platform = (entry.platform or default_platform).lower()
        platform_id = entry.platform_id
        platform_url = entry.platform_url

        if platform_url:
            detected = detect_platform_from_url(platform_url)
            if detected:
                platform = detected
        if platform_url and not platform_id:
            platform_id = extract_platform_id(platform, platform_url) or platform_id
        genre_tags = entry.genre_tags or []

        artist = None
        artist_created = False
        if platform_id:
            result = await db.execute(
                select(Artist).join(PlatformAccount).where(
                    PlatformAccount.platform == platform,
                    PlatformAccount.platform_id == platform_id,
                )
            )
            artist = result.scalar_one_or_none()
        else:
            result = await db.execute(
                select(Artist).where(func.lower(Artist.name) == name.lower())
            )
            artist = result.scalar_one_or_none()

        if not artist:
            artist = Artist(
                id=new_uuid(),
                name=name,
                genre_tags=genre_tags,
                is_candidate=False,
            )
            db.add(artist)
            await db.flush()
            artist_created = True

        if platform_id:
            result = await db.execute(
                select(PlatformAccount).where(
                    PlatformAccount.artist_id == artist.id,
                    PlatformAccount.platform == platform,
                    PlatformAccount.platform_id == platform_id,
                )
            )
            account = result.scalar_one_or_none()
            if not account:
                account = PlatformAccount(
                    id=new_uuid(),
                    artist_id=artist.id,
                    platform=platform,
                    platform_id=platform_id,
                    platform_url=platform_url,
                )
                db.add(account)
        else:
            warnings.append(f"Missing platform ID for '{name}'; added as roster without connector account")

        # Create additional platform accounts (e.g. youtube_id, spotify_url)
        for extra in (entry.additional_platforms or []):
            extra_pid = extra.platform_id
            extra_url = extra.platform_url
            if extra_url and not extra_pid:
                extra_pid = extract_platform_id(extra.platform, extra_url) or extra_pid
            if extra_pid:
                result = await db.execute(
                    select(PlatformAccount).where(
                        PlatformAccount.artist_id == artist.id,
                        PlatformAccount.platform == extra.platform,
                        PlatformAccount.platform_id == extra_pid,
                    )
                )
                if not result.scalar_one_or_none():
                    db.add(PlatformAccount(
                        id=new_uuid(),
                        artist_id=artist.id,
                        platform=extra.platform,
                        platform_id=extra_pid,
                        platform_url=extra_url,
                    ))

        # Create roster membership if missing
        existing = await db.execute(
            select(RosterMembership).where(
                RosterMembership.label_id == label_id,
                RosterMembership.artist_id == artist.id,
            )
        )
        membership_created = False
        if not existing.scalar_one_or_none():
            membership = RosterMembership(
                id=new_uuid(), label_id=label_id, artist_id=artist.id,
            )
            db.add(membership)
            membership_created = True

        if artist_created or membership_created:
            created.append({
                "artist_id": artist.id,
                "name": artist.name,
                "platform": platform,
                "platform_id": platform_id,
            })
        else:
            skipped.append({"name": artist.name, "reason": "already_in_roster"})

    await db.flush()
    return created, skipped, warnings


async def _get_user_label(db: AsyncSession, label_id: str, user: User | None) -> Label:
    """Load a label and verify ownership. Raises 404 or 403."""
    label = await db.get(Label, label_id)
    if not label:
        raise HTTPException(status_code=404, detail="Label not found")
    if user is not None:
        await verify_label_ownership(label, user)
    return label


def _enqueue_pipeline(label_id: str):
    # Replace any running/queued pipeline with this one
    return pipeline_queue.enqueue(label_id, replace=True)

@router.post("/labels", response_model=LabelResponse)
async def create_label(data: LabelCreate, user: User | None = Depends(get_optional_user), db: AsyncSession = Depends(get_db)):
    label = Label(id=new_uuid(), name=data.name, description=data.description, genre_tags=data.genre_tags or {}, user_id=user.id if user else None)
    db.add(label)
    await db.flush()
    await _ensure_default_watchlist(db, label.id)
    await db.refresh(label)
    return label


@router.get("/labels", response_model=list[LabelResponse])
async def list_labels(user: User | None = Depends(get_optional_user), db: AsyncSession = Depends(get_db)):
    query = select(Label)
    if user:
        query = query.where(Label.user_id == user.id)
    result = await db.execute(query.order_by(Label.created_at.desc()))
    return result.scalars().all()


@router.get("/labels/{label_id}", response_model=LabelResponse)
async def get_label(label_id: str, user: User | None = Depends(get_optional_user), db: AsyncSession = Depends(get_db)):
    label = await _get_user_label(db, label_id, user)
    return label


@router.post("/labels/{label_id}/roster")
async def add_roster(label_id: str, data: RosterInput, user: User | None = Depends(get_optional_user), db: AsyncSession = Depends(get_db)):
    label = await _get_user_label(db, label_id, user)

    added = []
    for ra in data.artists:
        # Find or create artist
        result = await db.execute(
            select(Artist).join(PlatformAccount).where(
                PlatformAccount.platform == ra.platform,
                PlatformAccount.platform_id == ra.platform_id,
            )
        )
        artist = result.scalar_one_or_none()

        if not artist:
            artist = Artist(
                id=new_uuid(), name=ra.name,
                genre_tags=ra.genre_tags or [],
                is_candidate=False,
            )
            db.add(artist)
            await db.flush()

            account = PlatformAccount(
                id=new_uuid(), artist_id=artist.id,
                platform=ra.platform, platform_id=ra.platform_id,
                platform_url=ra.platform_url,
            )
            db.add(account)

        # Create roster membership
        existing = await db.execute(
            select(RosterMembership).where(
                RosterMembership.label_id == label_id,
                RosterMembership.artist_id == artist.id,
            )
        )
        if not existing.scalar_one_or_none():
            membership = RosterMembership(
                id=new_uuid(), label_id=label_id, artist_id=artist.id,
            )
            db.add(membership)

        added.append({"artist_id": artist.id, "name": artist.name})

    await db.flush()
    return {"added": added, "count": len(added)}


@router.post("/labels/import-text", response_model=RosterImportResult)
async def import_label_from_text(data: LabelImportInput, user: User | None = Depends(get_optional_user), db: AsyncSession = Depends(get_db)):
    parsed = parse_roster_text(data.raw_text, data.default_platform)
    entries = parsed.artists
    if not entries:
        resolve_warnings = ["No roster entries detected in input text"]
    else:
        resolve_warnings = []

    if data.resolve_missing and entries:
        entries, missing_warnings = await _resolve_missing_platform_ids(entries, data.default_platform)
        resolve_warnings += missing_warnings

    if data.dry_run:
        return RosterImportResult(
            label_id=None,
            label_name=data.label.name,
            parsed_count=len(entries),
            created_count=0,
            skipped_count=0,
            parsed=entries,
            created=[],
            skipped=[],
            warnings=resolve_warnings,
        )

    label = Label(
        id=new_uuid(),
        name=data.label.name,
        description=data.label.description,
        genre_tags=data.label.genre_tags or {},
        user_id=user.id if user else None,
    )
    db.add(label)
    await db.flush()
    await _ensure_default_watchlist(db, label.id)

    created, skipped, import_warnings = await _upsert_roster_entries(
        db, label.id, entries, data.default_platform
    )
    await db.commit()

    if data.run_pipeline:
        await _enqueue_pipeline(label.id)

    return RosterImportResult(
        label_id=label.id,
        label_name=label.name,
        parsed_count=len(entries),
        created_count=len(created),
        skipped_count=len(skipped),
        parsed=entries,
        created=created,
        skipped=skipped,
        warnings=resolve_warnings + import_warnings,
    )


@router.post("/labels/import-file", response_model=RosterImportResult)
async def import_label_from_file(
    file: UploadFile = File(...),
    label_name: str = Form(...),
    label_description: str | None = Form(None),
    label_genre_tags: str | None = Form(None),
    default_platform: str = Form("youtube"),
    resolve_missing: bool = Form(True),
    dry_run: bool = Form(False),
    run_pipeline: bool = Form(False),
    user: User | None = Depends(get_optional_user),
    db: AsyncSession = Depends(get_db),
):
    data = await file.read()
    raw_text, extract_warnings = extract_text_from_upload(file.filename, file.content_type, data)

    parsed = parse_roster_text(raw_text, default_platform)
    entries = parsed.artists
    if not entries:
        resolve_warnings = ["No roster entries detected in uploaded file"]
    else:
        resolve_warnings = []

    if resolve_missing and entries:
        entries, missing_warnings = await _resolve_missing_platform_ids(entries, default_platform)
        resolve_warnings += missing_warnings

    genre_tags = {}
    if label_genre_tags:
        try:
            genre_tags = json.loads(label_genre_tags)
        except Exception:
            extract_warnings.append("Label genre_tags is not valid JSON; ignoring")

    if dry_run:
        return RosterImportResult(
            label_id=None,
            label_name=label_name,
            parsed_count=len(entries),
            created_count=0,
            skipped_count=0,
            parsed=entries,
            created=[],
            skipped=[],
            warnings=extract_warnings + resolve_warnings,
        )

    label = Label(
        id=new_uuid(),
        name=label_name,
        description=label_description,
        genre_tags=genre_tags or {},
        user_id=user.id if user else None,
    )
    db.add(label)
    await db.flush()
    await _ensure_default_watchlist(db, label.id)

    created, skipped, import_warnings = await _upsert_roster_entries(
        db, label.id, entries, default_platform
    )
    await db.commit()

    if run_pipeline:
        await _enqueue_pipeline(label.id)

    return RosterImportResult(
        label_id=label.id,
        label_name=label.name,
        parsed_count=len(entries),
        created_count=len(created),
        skipped_count=len(skipped),
        parsed=entries,
        created=created,
        skipped=skipped,
        warnings=extract_warnings + resolve_warnings + import_warnings,
    )


@router.post("/labels/import-confirm", response_model=RosterImportResult)
async def import_label_from_confirm(data: RosterConfirmInput, user: User | None = Depends(get_optional_user), db: AsyncSession = Depends(get_db)):
    entries = data.artists
    if not entries:
        return RosterImportResult(
            label_id=None,
            label_name=data.label.name,
            parsed_count=0,
            created_count=0,
            skipped_count=0,
            parsed=[],
            created=[],
            skipped=[],
            warnings=["No roster entries provided"],
        )

    label = Label(
        id=new_uuid(),
        name=data.label.name,
        description=data.label.description,
        genre_tags=data.label.genre_tags or {},
        user_id=user.id if user else None,
    )
    db.add(label)
    await db.flush()
    await _ensure_default_watchlist(db, label.id)

    created, skipped, import_warnings = await _upsert_roster_entries(
        db, label.id, entries, data.default_platform
    )
    await db.commit()

    if data.run_pipeline:
        await _enqueue_pipeline(label.id)

    return RosterImportResult(
        label_id=label.id,
        label_name=label.name,
        parsed_count=len(entries),
        created_count=len(created),
        skipped_count=len(skipped),
        parsed=entries,
        created=created,
        skipped=skipped,
        warnings=import_warnings,
    )


@router.post("/labels/{label_id}/roster/import-text", response_model=RosterImportResult)
async def import_roster_from_text(
    label_id: str, data: RosterImportInput, user: User | None = Depends(get_optional_user), db: AsyncSession = Depends(get_db)
):
    label = await _get_user_label(db, label_id, user)

    parsed = parse_roster_text(data.raw_text, data.default_platform)
    entries = parsed.artists
    if not entries:
        resolve_warnings = ["No roster entries detected in input text"]
    else:
        resolve_warnings = []

    if data.resolve_missing and entries:
        entries, missing_warnings = await _resolve_missing_platform_ids(entries, data.default_platform)
        resolve_warnings += missing_warnings

    if data.dry_run:
        return RosterImportResult(
            label_id=label.id,
            label_name=label.name,
            parsed_count=len(entries),
            created_count=0,
            skipped_count=0,
            parsed=entries,
            created=[],
            skipped=[],
            warnings=resolve_warnings,
        )

    created, skipped, import_warnings = await _upsert_roster_entries(
        db, label.id, entries, data.default_platform
    )
    await db.commit()

    if data.run_pipeline:
        await _enqueue_pipeline(label.id)

    return RosterImportResult(
        label_id=label.id,
        label_name=label.name,
        parsed_count=len(entries),
        created_count=len(created),
        skipped_count=len(skipped),
        parsed=entries,
        created=created,
        skipped=skipped,
        warnings=resolve_warnings + import_warnings,
    )


@router.post("/labels/{label_id}/roster/import-file", response_model=RosterImportResult)
async def import_roster_from_file(
    label_id: str,
    file: UploadFile = File(...),
    default_platform: str = Form("youtube"),
    resolve_missing: bool = Form(True),
    dry_run: bool = Form(False),
    run_pipeline: bool = Form(False),
    user: User | None = Depends(get_optional_user),
    db: AsyncSession = Depends(get_db),
):
    label = await _get_user_label(db, label_id, user)

    data = await file.read()
    raw_text, extract_warnings = extract_text_from_upload(file.filename, file.content_type, data)

    parsed = parse_roster_text(raw_text, default_platform)
    entries = parsed.artists
    if not entries:
        resolve_warnings = ["No roster entries detected in uploaded file"]
    else:
        resolve_warnings = []

    if resolve_missing and entries:
        entries, missing_warnings = await _resolve_missing_platform_ids(entries, default_platform)
        resolve_warnings += missing_warnings

    if dry_run:
        return RosterImportResult(
            label_id=label.id,
            label_name=label.name,
            parsed_count=len(entries),
            created_count=0,
            skipped_count=0,
            parsed=entries,
            created=[],
            skipped=[],
            warnings=extract_warnings + resolve_warnings,
        )

    created, skipped, import_warnings = await _upsert_roster_entries(
        db, label.id, entries, default_platform
    )
    await db.commit()

    if run_pipeline:
        await _enqueue_pipeline(label.id)

    return RosterImportResult(
        label_id=label.id,
        label_name=label.name,
        parsed_count=len(entries),
        created_count=len(created),
        skipped_count=len(skipped),
        parsed=entries,
        created=created,
        skipped=skipped,
        warnings=extract_warnings + resolve_warnings + import_warnings,
    )


@router.post("/labels/{label_id}/roster/import-confirm", response_model=RosterImportResult)
async def import_roster_from_confirm(
    label_id: str, data: RosterConfirmExistingInput, user: User | None = Depends(get_optional_user), db: AsyncSession = Depends(get_db)
):
    label = await _get_user_label(db, label_id, user)

    entries = data.artists
    if not entries:
        return RosterImportResult(
            label_id=label.id,
            label_name=label.name,
            parsed_count=0,
            created_count=0,
            skipped_count=0,
            parsed=[],
            created=[],
            skipped=[],
            warnings=["No roster entries provided"],
        )

    created, skipped, import_warnings = await _upsert_roster_entries(
        db, label.id, entries, data.default_platform
    )
    await db.commit()

    if data.run_pipeline:
        await _enqueue_pipeline(label.id)

    return RosterImportResult(
        label_id=label.id,
        label_name=label.name,
        parsed_count=len(entries),
        created_count=len(created),
        skipped_count=len(skipped),
        parsed=entries,
        created=created,
        skipped=skipped,
        warnings=import_warnings,
    )

@router.get("/labels/{label_id}/taste-map", response_model=TasteMapResponse)
async def get_taste_map(label_id: str, user: User | None = Depends(get_optional_user), db: AsyncSession = Depends(get_db)):
    label = await _get_user_label(db, label_id, user)

    result = await db.execute(
        select(LabelCluster).where(LabelCluster.label_id == label_id)
        .order_by(LabelCluster.cluster_index)
    )
    clusters = result.scalars().all()
    artist_name_map: dict[str, str] = {}
    if clusters:
        artist_ids = {
            aid for cluster in clusters for aid in (cluster.artist_ids or [])
        }
        if artist_ids:
            artist_result = await db.execute(
                select(Artist.id, Artist.name).where(Artist.id.in_(artist_ids))
            )
            artist_name_map = {row[0]: row[1] for row in artist_result.all()}

    return TasteMapResponse(
        label_id=label_id,
        label_name=label.name,
        label_dna=label.label_dna,
        clusters=[
            ClusterInfo(
                cluster_id=c.id,
                cluster_index=c.cluster_index,
                cluster_name=c.cluster_name,
                artist_ids=c.artist_ids or [],
                artist_names=[
                    artist_name_map[aid]
                    for aid in (c.artist_ids or [])
                    if aid in artist_name_map
                ],
            )
            for c in clusters
        ],
    )


@router.get("/labels/{label_id}/scout-feed", response_model=ScoutFeedResponse)
async def get_scout_feed(label_id: str, limit: int = 50, user: User | None = Depends(get_optional_user), db: AsyncSession = Depends(get_db)):
    label = await _get_user_label(db, label_id, user)

    cluster_result = await db.execute(
        select(LabelCluster).where(LabelCluster.label_id == label_id)
    )
    cluster_map = {c.id: c for c in cluster_result.scalars().all()}

    # Get latest batch
    result = await db.execute(
        select(Recommendation).where(Recommendation.label_id == label_id)
        .order_by(Recommendation.created_at.desc()).limit(1)
    )
    latest = result.scalar_one_or_none()
    if not latest:
        return ScoutFeedResponse(label_id=label_id, batch_id="", items=[], total=0)

    batch_id = latest.batch_id

    # clamp limit to protect UX and perf
    limit = max(1, min(limit, 200))
    result = await db.execute(
        select(Recommendation).where(
            Recommendation.label_id == label_id,
            Recommendation.batch_id == batch_id,
        ).order_by(Recommendation.final_score.desc()).limit(limit)
    )
    recs = result.scalars().all()
    rec_artist_ids = [r.artist_id for r in recs]

    stage_map: dict[str, str] = {}
    if rec_artist_ids:
        stage_result = await db.execute(
            select(LabelArtistState).where(
                LabelArtistState.label_id == label_id,
                LabelArtistState.artist_id.in_(rec_artist_ids),
            )
        )
        stage_map = {s.artist_id: s.stage for s in stage_result.scalars().all()}

    # Load cultural profiles for recommended artists
    cultural_map: dict[str, ArtistCulturalProfile] = {}
    if rec_artist_ids:
        cultural_result = await db.execute(
            select(ArtistCulturalProfile).where(
                ArtistCulturalProfile.artist_id.in_(rec_artist_ids)
            ).order_by(ArtistCulturalProfile.computed_at.desc())
        )
        for cp in cultural_result.scalars().all():
            if cp.artist_id not in cultural_map:
                cultural_map[cp.artist_id] = cp

    total_result = await db.execute(
        select(func.count()).select_from(Recommendation).where(
            Recommendation.label_id == label_id,
            Recommendation.batch_id == batch_id,
        )
    )
    total = total_result.scalar_one()

    items = []
    for rec in recs:
        artist = await db.get(Artist, rec.artist_id)
        if not artist:
            continue

        # Get latest features
        feat_result = await db.execute(
            select(ArtistFeature).where(ArtistFeature.artist_id == rec.artist_id)
            .order_by(ArtistFeature.computed_at.desc()).limit(1)
        )
        features = feat_result.scalar_one_or_none()

        # Get nearest roster artist name
        nearest_name = None
        if rec.nearest_roster_artist_id:
            nearest = await db.get(Artist, rec.nearest_roster_artist_id)
            if nearest:
                nearest_name = nearest.name
        cluster_name = None
        if rec.nearest_cluster_id:
            cluster = cluster_map.get(rec.nearest_cluster_id)
            if cluster:
                cluster_name = cluster.cluster_name or f"Cluster {cluster.cluster_index + 1}"

        reasons = []
        if cluster_name:
            reasons.append(f"Fit to {cluster_name}")
        if nearest_name:
            reasons.append(f"Similar to {nearest_name}")
        growth_7d = features.growth_7d if features else None
        growth_30d = features.growth_30d if features else None
        if growth_7d is not None and growth_7d >= 0.1:
            reasons.append(f"7d growth {_format_growth(growth_7d)}")
        elif growth_30d is not None and growth_30d >= 0.2:
            reasons.append(f"30d growth {_format_growth(growth_30d)}")
        if features and features.momentum_score is not None and features.momentum_score >= 0.6:
            reasons.append("Strong momentum")
        if rec.risk_score is not None and rec.risk_score <= 0.1:
            reasons.append("Low risk")

        # Cultural data
        cp = cultural_map.get(rec.artist_id)
        cultural_energy = cp.cultural_energy if cp else None
        breakout_candidate = cp.breakout_candidate if cp else None
        cultural_highlights = None
        if cp and cp.cultural_profile and cp.cultural_profile.get("cultural_identity", {}).get("themes"):
            cultural_highlights = [
                t["label"] for t in cp.cultural_profile["cultural_identity"]["themes"][:3]
            ]
        if cp and cp.breakout_candidate:
            reasons.append("Breakout signal")

        if len(reasons) > 3:
            reasons = reasons[:3]

        items.append(ScoutFeedItem(
            artist_id=rec.artist_id,
            artist_name=artist.name,
            image_url=artist.image_url,
            fit_score=rec.fit_score,
            momentum_score=rec.momentum_score,
            risk_score=rec.risk_score,
            final_score=rec.final_score,
            nearest_roster_artist=nearest_name,
            growth_7d=growth_7d,
            growth_30d=growth_30d,
            genre_tags=artist.genre_tags,
            score_breakdown=rec.score_breakdown or None,
            reasons=reasons or None,
            stage=stage_map.get(rec.artist_id),
            cultural_energy=cultural_energy,
            breakout_candidate=breakout_candidate,
            cultural_highlights=cultural_highlights,
        ))

    return ScoutFeedResponse(
        label_id=label_id, batch_id=batch_id, items=items, total=int(total or 0)
    )


@router.get("/artists/{artist_id}", response_model=ArtistDetailResponse)
async def get_artist_detail(
    artist_id: str,
    label_id: str | None = None,
    user: User | None = Depends(get_optional_user),
    db: AsyncSession = Depends(get_db),
):
    artist = await db.get(Artist, artist_id)
    if not artist:
        raise HTTPException(status_code=404, detail="Artist not found")

    # Verify user has access through one of their labels
    if label_id:
        label = await _get_user_label(db, label_id, user)
    elif user is not None:
        access_check = await db.execute(
            select(Label.id).join(RosterMembership, RosterMembership.label_id == Label.id)
            .where(Label.user_id == user.id, RosterMembership.artist_id == artist_id)
            .limit(1)
        )
        if not access_check.scalar_one_or_none():
            # Also check recommendations
            rec_check = await db.execute(
                select(Label.id).join(Recommendation, Recommendation.label_id == Label.id)
                .where(Label.user_id == user.id, Recommendation.artist_id == artist_id)
                .limit(1)
            )
            if not rec_check.scalar_one_or_none():
                raise HTTPException(status_code=403, detail="You do not have access to this artist")

    # Platform accounts
    result = await db.execute(
        select(PlatformAccount).where(PlatformAccount.artist_id == artist_id)
    )
    accounts = result.scalars().all()

    # Recent snapshots (last 30)
    result = await db.execute(
        select(Snapshot).where(Snapshot.artist_id == artist_id)
        .order_by(Snapshot.captured_at.desc()).limit(30)
    )
    snapshots = list(reversed(result.scalars().all()))

    # Latest features
    result = await db.execute(
        select(ArtistFeature).where(ArtistFeature.artist_id == artist_id)
        .order_by(ArtistFeature.computed_at.desc()).limit(1)
    )
    latest_feat = result.scalar_one_or_none()

    # Latest LLM brief
    result = await db.execute(
        select(ArtistLLMBrief).where(ArtistLLMBrief.artist_id == artist_id)
        .order_by(ArtistLLMBrief.created_at.desc()).limit(1)
    )
    llm_brief_row = result.scalar_one_or_none()

    # Feedback history
    result = await db.execute(
        select(Feedback).where(Feedback.artist_id == artist_id)
        .order_by(Feedback.created_at.desc())
    )
    feedback_rows = result.scalars().all()

    # Cultural profile
    result = await db.execute(
        select(ArtistCulturalProfile).where(
            ArtistCulturalProfile.artist_id == artist_id
        ).order_by(ArtistCulturalProfile.computed_at.desc()).limit(1)
    )
    cultural_row = result.scalars().first()
    cultural_profile = None
    if cultural_row and cultural_row.cultural_profile:
        cp = cultural_row.cultural_profile
        cultural_profile = CulturalProfileResponse(
            cultural_energy=cultural_row.cultural_energy,
            sentiment=cp.get("sentiment"),
            engagement=cp.get("engagement"),
            superfans=cp.get("superfans"),
            cross_platform=cp.get("cross_platform"),
            cultural_identity=cp.get("cultural_identity"),
            persona=cp.get("persona"),
            polarization=cp.get("polarization"),
            evidence_snippets=cp.get("evidence_snippets"),
            breakout_signals=cp.get("breakout_signals"),
            fan_community=cp.get("fan_community"),
            scores=cp.get("scores"),
        )

    label_stage = None
    if label_id:
        stage_result = await db.execute(
            select(LabelArtistState).where(
                LabelArtistState.label_id == label_id,
                LabelArtistState.artist_id == artist_id,
            )
        )
        state = stage_result.scalar_one_or_none()
        if state:
            label_stage = state.stage

    return ArtistDetailResponse(
        id=artist.id,
        name=artist.name,
        bio=artist.bio,
        genre_tags=artist.genre_tags,
        image_url=artist.image_url,
        is_candidate=artist.is_candidate,
        platform_accounts=[PlatformAccountResponse.model_validate(a) for a in accounts],
        created_at=artist.created_at,
        snapshots=[SnapshotResponse.model_validate(s) for s in snapshots],
        latest_features=ArtistFeatureResponse.model_validate(latest_feat) if latest_feat else None,
        llm_brief=llm_brief_row.brief if llm_brief_row else None,
        feedback_history=[
            {"action": f.action, "notes": f.notes, "created_at": str(f.created_at)}
            for f in feedback_rows
        ],
        label_stage=label_stage,
        cultural_profile=cultural_profile,
    )


@router.post("/labels/{label_id}/feedback", response_model=FeedbackResponse)
async def submit_feedback(label_id: str, data: FeedbackInput, user: User | None = Depends(get_optional_user), db: AsyncSession = Depends(get_db)):
    label = await _get_user_label(db, label_id, user)

    artist = await db.get(Artist, data.artist_id)
    if not artist:
        raise HTTPException(status_code=404, detail="Artist not found")

    feedback = Feedback(
        id=new_uuid(), label_id=label_id, artist_id=data.artist_id,
        recommendation_id=data.recommendation_id,
        action=data.action, notes=data.notes, context=data.context or {},
    )
    db.add(feedback)
    await db.flush()
    await db.refresh(feedback)
    if data.action in {"shortlist", "sign", "pass", "archive"}:
        await _upsert_stage(db, label_id, data.artist_id, data.action)
    return feedback


@router.post("/labels/{label_id}/artists/{artist_id}/stage")
async def update_artist_stage(
    label_id: str,
    artist_id: str,
    data: StageUpdateInput,
    user: User | None = Depends(get_optional_user),
    db: AsyncSession = Depends(get_db),
):
    label = await _get_user_label(db, label_id, user)
    artist = await db.get(Artist, artist_id)
    if not artist:
        raise HTTPException(status_code=404, detail="Artist not found")
    state = await _upsert_stage(db, label_id, artist_id, data.stage, data.notes)
    return {"status": "ok", "stage": state.stage}


@router.get("/labels/{label_id}/watchlists", response_model=list[WatchlistResponse])
async def list_watchlists(label_id: str, user: User | None = Depends(get_optional_user), db: AsyncSession = Depends(get_db)):
    label = await _get_user_label(db, label_id, user)
    await _ensure_default_watchlist(db, label_id)
    result = await db.execute(
        select(Watchlist, func.count(WatchlistItem.id))
        .outerjoin(WatchlistItem, WatchlistItem.watchlist_id == Watchlist.id)
        .where(Watchlist.label_id == label_id)
        .group_by(Watchlist.id)
        .order_by(Watchlist.created_at.asc())
    )
    rows = result.all()
    return [
        WatchlistResponse(
            id=w.id,
            label_id=w.label_id,
            name=w.name,
            description=w.description,
            is_active=w.is_active,
            item_count=int(count or 0),
            created_at=w.created_at,
            updated_at=w.updated_at,
        )
        for w, count in rows
    ]


@router.post("/labels/{label_id}/watchlists", response_model=WatchlistResponse)
async def create_watchlist(
    label_id: str,
    data: WatchlistCreate,
    user: User | None = Depends(get_optional_user),
    db: AsyncSession = Depends(get_db),
):
    label = await _get_user_label(db, label_id, user)
    watchlist = Watchlist(
        id=new_uuid(),
        label_id=label_id,
        name=data.name,
        description=data.description,
        is_active=True,
    )
    db.add(watchlist)
    await db.flush()
    return WatchlistResponse(
        id=watchlist.id,
        label_id=watchlist.label_id,
        name=watchlist.name,
        description=watchlist.description,
        is_active=watchlist.is_active,
        item_count=0,
        created_at=watchlist.created_at,
        updated_at=watchlist.updated_at,
    )


@router.get("/labels/{label_id}/watchlists/{watchlist_id}", response_model=WatchlistDetailResponse)
async def get_watchlist_detail(
    label_id: str,
    watchlist_id: str,
    user: User | None = Depends(get_optional_user),
    db: AsyncSession = Depends(get_db),
):
    await _get_user_label(db, label_id, user)
    watchlist = await db.get(Watchlist, watchlist_id)
    if not watchlist or watchlist.label_id != label_id:
        raise HTTPException(status_code=404, detail="Watchlist not found")

    result = await db.execute(
        select(WatchlistItem, Artist, LabelArtistState.stage)
        .join(Artist, Artist.id == WatchlistItem.artist_id)
        .outerjoin(
            LabelArtistState,
            and_(
                LabelArtistState.label_id == label_id,
                LabelArtistState.artist_id == Artist.id,
            ),
        )
        .where(WatchlistItem.watchlist_id == watchlist_id)
        .order_by(WatchlistItem.created_at.desc())
    )
    items = []
    for item, artist, stage in result.all():
        items.append(WatchlistItemResponse(
            artist_id=artist.id,
            artist_name=artist.name,
            image_url=artist.image_url,
            stage=stage,
            added_at=item.created_at,
            notes=item.notes,
        ))

    detail = WatchlistResponse(
        id=watchlist.id,
        label_id=watchlist.label_id,
        name=watchlist.name,
        description=watchlist.description,
        is_active=watchlist.is_active,
        item_count=len(items),
        created_at=watchlist.created_at,
        updated_at=watchlist.updated_at,
    )
    return WatchlistDetailResponse(watchlist=detail, items=items)


@router.post("/labels/{label_id}/watchlists/{watchlist_id}/items", response_model=WatchlistItemResponse)
async def add_watchlist_item(
    label_id: str,
    watchlist_id: str,
    data: WatchlistItemInput,
    user: User | None = Depends(get_optional_user),
    db: AsyncSession = Depends(get_db),
):
    await _get_user_label(db, label_id, user)
    watchlist = await db.get(Watchlist, watchlist_id)
    if not watchlist or watchlist.label_id != label_id:
        raise HTTPException(status_code=404, detail="Watchlist not found")
    artist = await db.get(Artist, data.artist_id)
    if not artist:
        raise HTTPException(status_code=404, detail="Artist not found")

    existing = await db.execute(
        select(WatchlistItem).where(
            WatchlistItem.watchlist_id == watchlist_id,
            WatchlistItem.artist_id == data.artist_id,
        )
    )
    item = existing.scalar_one_or_none()
    if not item:
        item = WatchlistItem(
            id=new_uuid(),
            watchlist_id=watchlist_id,
            artist_id=data.artist_id,
            source="manual",
            notes=data.notes,
        )
        db.add(item)
        await db.flush()

    stage = None
    stage_result = await db.execute(
        select(LabelArtistState).where(
            LabelArtistState.label_id == label_id,
            LabelArtistState.artist_id == data.artist_id,
        )
    )
    state = stage_result.scalar_one_or_none()
    if not state:
        state = await _upsert_stage(db, label_id, data.artist_id, "review")
    stage = state.stage

    return WatchlistItemResponse(
        artist_id=artist.id,
        artist_name=artist.name,
        image_url=artist.image_url,
        stage=stage,
        added_at=item.created_at,
        notes=item.notes,
    )


@router.delete("/labels/{label_id}/watchlists/{watchlist_id}/items/{artist_id}")
async def remove_watchlist_item(
    label_id: str,
    watchlist_id: str,
    artist_id: str,
    user: User | None = Depends(get_optional_user),
    db: AsyncSession = Depends(get_db),
):
    await _get_user_label(db, label_id, user)
    watchlist = await db.get(Watchlist, watchlist_id)
    if not watchlist or watchlist.label_id != label_id:
        raise HTTPException(status_code=404, detail="Watchlist not found")
    result = await db.execute(
        select(WatchlistItem).where(
            WatchlistItem.watchlist_id == watchlist_id,
            WatchlistItem.artist_id == artist_id,
        )
    )
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    await db.delete(item)
    await db.flush()
    return {"status": "ok"}


@router.get("/labels/{label_id}/alerts", response_model=list[AlertResponse])
async def list_alerts(
    label_id: str,
    status: str | None = None,
    limit: int = 50,
    user: User | None = Depends(get_optional_user),
    db: AsyncSession = Depends(get_db),
):
    label = await _get_user_label(db, label_id, user)
    limit = max(1, min(limit, 200))
    query = select(Alert, Artist.name).join(Artist).where(Alert.label_id == label_id)
    if status:
        query = query.where(Alert.status == status)
    query = query.order_by(Alert.created_at.desc()).limit(limit)
    result = await db.execute(query)
    alerts = []
    for alert, artist_name in result.all():
        alerts.append(AlertResponse(
            id=alert.id,
            label_id=alert.label_id,
            artist_id=alert.artist_id,
            artist_name=artist_name,
            rule_id=alert.rule_id,
            severity=alert.severity,
            status=alert.status,
            title=alert.title,
            description=alert.description,
            created_at=alert.created_at,
            context=alert.context,
        ))
    return alerts


@router.post("/labels/{label_id}/alerts/{alert_id}/status")
async def update_alert_status(
    label_id: str,
    alert_id: str,
    data: AlertStatusInput,
    user: User | None = Depends(get_optional_user),
    db: AsyncSession = Depends(get_db),
):
    await _get_user_label(db, label_id, user)
    alert = await db.get(Alert, alert_id)
    if not alert or alert.label_id != label_id:
        raise HTTPException(status_code=404, detail="Alert not found")
    alert.status = data.status
    await db.flush()
    return {"status": "ok", "alert_id": alert.id, "alert_status": alert.status}


@router.post("/labels/{label_id}/llm/refresh")
async def refresh_label_llm(label_id: str, user: User | None = Depends(get_optional_user), db: AsyncSession = Depends(get_db)):
    """Regenerate Label DNA via LLM."""
    from app.llm.label_dna import generate_label_dna
    label = await _get_user_label(db, label_id, user)
    result = await generate_label_dna(db, label_id)
    if result:
        return {"status": "ok", "label_dna": result.model_dump()}
    return {"status": "fallback", "message": "LLM unavailable, using cached or default"}


@router.post("/artists/{artist_id}/llm/refresh")
async def refresh_artist_llm(artist_id: str, label_id: str = None, user: User | None = Depends(get_optional_user), db: AsyncSession = Depends(get_db)):
    """Regenerate artist scouting brief via LLM."""
    from app.llm.artist_brief import generate_artist_brief
    artist = await db.get(Artist, artist_id)
    if not artist:
        raise HTTPException(status_code=404, detail="Artist not found")
    result = await generate_artist_brief(db, artist_id, label_id)
    if result:
        return {"status": "ok", "brief": result.model_dump()}
    return {"status": "fallback", "message": "LLM unavailable"}
