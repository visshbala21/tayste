"""Seed demo data for Tayste platform."""
import asyncio
import logging
import random
import numpy as np
from datetime import datetime, timedelta
from app.db.session import async_session_factory
from app.models.tables import (
    Label, Artist, PlatformAccount, RosterMembership, Snapshot, Embedding,
)
from app.models.base import new_uuid
from app.services.embeddings import build_metric_vector, store_embedding

logger = logging.getLogger(__name__)

ROSTER_ARTISTS = [
    {"name": "Velvet Collapse", "genres": ["indie-rock", "shoegaze"], "followers": 45000, "views": 2800000},
    {"name": "Pale Meridian", "genres": ["dream-pop", "ambient"], "followers": 32000, "views": 1900000},
    {"name": "Ghost Antenna", "genres": ["post-punk", "darkwave"], "followers": 28000, "views": 1500000},
    {"name": "Sable Hymn", "genres": ["folk-noir", "chamber-pop"], "followers": 18000, "views": 980000},
    {"name": "Noctilux", "genres": ["synth-pop", "indie-electronic"], "followers": 62000, "views": 4200000},
    {"name": "Wire Garden", "genres": ["art-rock", "experimental"], "followers": 15000, "views": 720000},
    {"name": "Hollow Shrine", "genres": ["post-rock", "ambient"], "followers": 22000, "views": 1100000},
    {"name": "Luna Dispatch", "genres": ["indie-pop", "bedroom-pop"], "followers": 55000, "views": 3600000},
]

CANDIDATE_ARTISTS = [
    {"name": "Dawnlit", "genres": ["dream-pop", "shoegaze"], "followers": 3200, "views": 180000, "growth": 0.15},
    {"name": "Spectral Youth", "genres": ["post-punk", "indie-rock"], "followers": 5800, "views": 320000, "growth": 0.12},
    {"name": "Moth Priest", "genres": ["darkwave", "gothic"], "followers": 2100, "views": 95000, "growth": 0.22},
    {"name": "Tidepool", "genres": ["ambient", "electronic"], "followers": 4500, "views": 210000, "growth": 0.08},
    {"name": "Bitter Frequency", "genres": ["noise-pop", "shoegaze"], "followers": 1800, "views": 67000, "growth": 0.28},
    {"name": "Glass Meridian", "genres": ["art-pop", "chamber-pop"], "followers": 7200, "views": 410000, "growth": 0.10},
    {"name": "Aether Station", "genres": ["synth-pop", "new-wave"], "followers": 9100, "views": 580000, "growth": 0.18},
    {"name": "Foxblood", "genres": ["indie-folk", "folk-noir"], "followers": 3800, "views": 190000, "growth": 0.14},
    {"name": "Void Parade", "genres": ["post-rock", "math-rock"], "followers": 2600, "views": 130000, "growth": 0.20},
    {"name": "Crystal Debt", "genres": ["indie-electronic", "glitch"], "followers": 6400, "views": 350000, "growth": 0.09},
    {"name": "SoftCrash", "genres": ["bedroom-pop", "lo-fi"], "followers": 11000, "views": 720000, "growth": 0.25},
    {"name": "Pale Wire", "genres": ["post-punk", "coldwave"], "followers": 1500, "views": 52000, "growth": 0.35},
    {"name": "Ember Circuit", "genres": ["electronic", "idm"], "followers": 4200, "views": 230000, "growth": 0.11},
    {"name": "Wildheart Sun", "genres": ["indie-pop", "twee"], "followers": 8500, "views": 490000, "growth": 0.16},
    {"name": "Rust Hymn", "genres": ["folk-noir", "americana"], "followers": 2900, "views": 140000, "growth": 0.13},
]


def generate_snapshots(artist_id: str, base_followers: int, base_views: int, growth_rate: float, days: int = 30) -> list:
    """Generate realistic daily snapshots over a period."""
    snapshots = []
    now = datetime.utcnow()
    daily_growth = growth_rate / days

    for day in range(days, -1, -1):
        t = now - timedelta(days=day)
        day_factor = 1 + daily_growth * (days - day)
        noise = random.uniform(0.97, 1.03)

        followers = int(base_followers * day_factor * noise)
        views = int(base_views * day_factor * random.uniform(0.95, 1.05))
        likes = int(views * random.uniform(0.02, 0.06))
        comments = int(views * random.uniform(0.003, 0.01))
        engagement = (likes + comments) / max(views, 1)

        snapshots.append(Snapshot(
            id=new_uuid(), artist_id=artist_id, platform="youtube",
            captured_at=t, followers=followers, views=views,
            likes=likes, comments=comments, engagement_rate=round(engagement, 6),
        ))
    return snapshots


async def run():
    logger.info("Seeding demo data...")
    async with async_session_factory() as db:
        # Create label
        label = Label(
            id=new_uuid(), name="Neon Dusk Records",
            description="Independent label focused on atmospheric, guitar-driven, and electronic-adjacent indie music. Known for signing artists at the intersection of dream-pop, post-punk, and ambient electronic.",
            genre_tags={"primary": ["indie-rock", "dream-pop", "post-punk"], "secondary": ["ambient", "synth-pop", "folk-noir"]},
        )
        db.add(label)
        await db.flush()
        logger.info(f"Created label: {label.name} ({label.id})")

        # Create roster artists
        for ra in ROSTER_ARTISTS:
            artist = Artist(
                id=new_uuid(), name=ra["name"], genre_tags=ra["genres"],
                is_candidate=False,
                image_url=f"https://picsum.photos/seed/{ra['name'].replace(' ', '')}/200",
            )
            db.add(artist)
            await db.flush()

            yt_account = PlatformAccount(
                id=new_uuid(), artist_id=artist.id, platform="youtube",
                platform_id=f"UC{new_uuid()[:20]}",
                platform_url=f"https://youtube.com/@{ra['name'].replace(' ', '')}",
            )
            db.add(yt_account)

            sp_account = PlatformAccount(
                id=new_uuid(), artist_id=artist.id, platform="spotify",
                platform_id=new_uuid()[:22],
                platform_url=f"https://open.spotify.com/artist/{new_uuid()[:22]}",
            )
            db.add(sp_account)

            sc_uuid = new_uuid()
            sc_account = PlatformAccount(
                id=new_uuid(), artist_id=artist.id, platform="soundcharts",
                platform_id=sc_uuid,
                platform_url=f"https://app.soundcharts.com/app/artist/{sc_uuid}",
            )
            db.add(sc_account)

            membership = RosterMembership(
                id=new_uuid(), label_id=label.id, artist_id=artist.id,
            )
            db.add(membership)

            # Generate snapshots
            growth = random.uniform(0.02, 0.08)
            snaps = generate_snapshots(artist.id, ra["followers"], ra["views"], growth)
            for s in snaps:
                db.add(s)

            # Build and store embedding
            snap_dicts = [
                {"followers": s.followers, "views": s.views, "likes": s.likes,
                 "comments": s.comments, "engagement_rate": s.engagement_rate}
                for s in snaps
            ]
            vec = build_metric_vector(snap_dicts)
            if vec is not None:
                await store_embedding(db, artist.id, vec)

            logger.info(f"  Roster: {ra['name']}")

        # Create candidate artists
        for ca in CANDIDATE_ARTISTS:
            artist = Artist(
                id=new_uuid(), name=ca["name"], genre_tags=ca["genres"],
                is_candidate=True,
                image_url=f"https://picsum.photos/seed/{ca['name'].replace(' ', '')}/200",
            )
            db.add(artist)
            await db.flush()

            yt_account = PlatformAccount(
                id=new_uuid(), artist_id=artist.id, platform="youtube",
                platform_id=f"UC{new_uuid()[:20]}",
                platform_url=f"https://youtube.com/@{ca['name'].replace(' ', '')}",
            )
            db.add(yt_account)

            sp_account = PlatformAccount(
                id=new_uuid(), artist_id=artist.id, platform="spotify",
                platform_id=new_uuid()[:22],
                platform_url=f"https://open.spotify.com/artist/{new_uuid()[:22]}",
            )
            db.add(sp_account)

            sc_uuid = new_uuid()
            sc_account = PlatformAccount(
                id=new_uuid(), artist_id=artist.id, platform="soundcharts",
                platform_id=sc_uuid,
                platform_url=f"https://app.soundcharts.com/app/artist/{sc_uuid}",
            )
            db.add(sc_account)

            # Generate snapshots with specified growth
            snaps = generate_snapshots(artist.id, ca["followers"], ca["views"], ca["growth"])
            for s in snaps:
                db.add(s)

            # Build and store embedding
            snap_dicts = [
                {"followers": s.followers, "views": s.views, "likes": s.likes,
                 "comments": s.comments, "engagement_rate": s.engagement_rate}
                for s in snaps
            ]
            vec = build_metric_vector(snap_dicts)
            if vec is not None:
                await store_embedding(db, artist.id, vec)

            logger.info(f"  Candidate: {ca['name']}")

        await db.commit()
    logger.info("Demo data seeded successfully!")
    logger.info(f"Label ID: {label.id}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(run())
