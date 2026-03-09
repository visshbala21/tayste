-- Tayste: Create all tables from scratch in Supabase
-- Run in: Supabase Dashboard > SQL Editor
-- Requires: pgvector extension

-- Enable pgvector
CREATE EXTENSION IF NOT EXISTS vector;

BEGIN;

-- ============================================================
-- 1. profiles (linked to Supabase Auth users)
-- ============================================================
DROP TABLE IF EXISTS profiles CASCADE;

CREATE TABLE profiles (
    id          UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    email       VARCHAR(255) UNIQUE NOT NULL,
    name        VARCHAR(255),
    picture     VARCHAR(512),
    is_active   BOOLEAN DEFAULT TRUE,
    created_at  TIMESTAMP DEFAULT NOW(),
    updated_at  TIMESTAMP DEFAULT NOW()
);

-- ============================================================
-- 2. labels
-- ============================================================
CREATE TABLE IF NOT EXISTS labels (
    id                      VARCHAR(36) PRIMARY KEY,
    name                    VARCHAR(255) NOT NULL,
    description             TEXT,
    genre_tags              JSONB DEFAULT '{}',
    label_dna               JSONB,
    pipeline_status         VARCHAR(20) DEFAULT 'idle',
    pipeline_started_at     TIMESTAMP,
    pipeline_completed_at   TIMESTAMP,
    user_id                 UUID REFERENCES profiles(id),
    created_at              TIMESTAMP DEFAULT NOW(),
    updated_at              TIMESTAMP DEFAULT NOW()
);

-- ============================================================
-- 3. artists
-- ============================================================
CREATE TABLE IF NOT EXISTS artists (
    id              VARCHAR(36) PRIMARY KEY,
    name            VARCHAR(255) NOT NULL,
    bio             TEXT,
    genre_tags      JSONB DEFAULT '[]',
    image_url       VARCHAR(512),
    is_candidate    BOOLEAN DEFAULT FALSE,
    created_at      TIMESTAMP DEFAULT NOW(),
    updated_at      TIMESTAMP DEFAULT NOW()
);

-- ============================================================
-- 4. platform_accounts
-- ============================================================
CREATE TABLE IF NOT EXISTS platform_accounts (
    id                  VARCHAR(36) PRIMARY KEY,
    artist_id           VARCHAR(36) NOT NULL REFERENCES artists(id),
    platform            VARCHAR(50) NOT NULL,
    platform_id         VARCHAR(255) NOT NULL,
    platform_url        VARCHAR(512),
    platform_metadata   JSONB DEFAULT '{}',
    created_at          TIMESTAMP DEFAULT NOW(),
    updated_at          TIMESTAMP DEFAULT NOW(),
    CONSTRAINT uq_platform_account UNIQUE (platform, platform_id)
);

-- ============================================================
-- 5. roster_memberships
-- ============================================================
CREATE TABLE IF NOT EXISTS roster_memberships (
    id          VARCHAR(36) PRIMARY KEY,
    label_id    VARCHAR(36) NOT NULL REFERENCES labels(id),
    artist_id   VARCHAR(36) NOT NULL REFERENCES artists(id),
    is_active   BOOLEAN DEFAULT TRUE,
    created_at  TIMESTAMP DEFAULT NOW(),
    updated_at  TIMESTAMP DEFAULT NOW(),
    CONSTRAINT uq_roster_membership UNIQUE (label_id, artist_id)
);

-- ============================================================
-- 6. snapshots (append-only time-series)
-- ============================================================
CREATE TABLE IF NOT EXISTS snapshots (
    id              VARCHAR(36) PRIMARY KEY,
    artist_id       VARCHAR(36) NOT NULL REFERENCES artists(id),
    platform        VARCHAR(50) NOT NULL,
    captured_at     TIMESTAMP NOT NULL,
    followers       INTEGER,
    views           INTEGER,
    likes           INTEGER,
    comments        INTEGER,
    shares          INTEGER,
    engagement_rate FLOAT,
    extra_metrics   JSONB DEFAULT '{}'
);

CREATE INDEX IF NOT EXISTS ix_snapshot_artist_platform_time
    ON snapshots (artist_id, platform, captured_at);

-- ============================================================
-- 7. embeddings (pgvector)
-- ============================================================
CREATE TABLE IF NOT EXISTS embeddings (
    id          VARCHAR(36) PRIMARY KEY,
    artist_id   VARCHAR(36) NOT NULL REFERENCES artists(id),
    provider    VARCHAR(50) NOT NULL DEFAULT 'metric',
    vector      vector(128),
    metadata    JSONB DEFAULT '{}',
    created_at  TIMESTAMP DEFAULT NOW(),
    updated_at  TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_embedding_artist_provider
    ON embeddings (artist_id, provider);

-- ============================================================
-- 8. label_clusters (pgvector centroid)
-- ============================================================
CREATE TABLE IF NOT EXISTS label_clusters (
    id              VARCHAR(36) PRIMARY KEY,
    label_id        VARCHAR(36) NOT NULL REFERENCES labels(id),
    cluster_index   INTEGER NOT NULL,
    centroid        vector(128),
    cluster_name    VARCHAR(255),
    artist_ids      JSONB DEFAULT '[]',
    metadata        JSONB DEFAULT '{}',
    created_at      TIMESTAMP DEFAULT NOW(),
    updated_at      TIMESTAMP DEFAULT NOW()
);

-- ============================================================
-- 9. artist_features
-- ============================================================
CREATE TABLE IF NOT EXISTS artist_features (
    id              VARCHAR(36) PRIMARY KEY,
    artist_id       VARCHAR(36) NOT NULL REFERENCES artists(id),
    computed_at     TIMESTAMP NOT NULL,
    growth_7d       FLOAT DEFAULT 0.0,
    growth_30d      FLOAT DEFAULT 0.0,
    acceleration    FLOAT DEFAULT 0.0,
    engagement_rate FLOAT DEFAULT 0.0,
    momentum_score  FLOAT DEFAULT 0.0,
    risk_score      FLOAT DEFAULT 0.0,
    risk_flags      JSONB DEFAULT '[]',
    extra           JSONB DEFAULT '{}',
    created_at      TIMESTAMP DEFAULT NOW(),
    updated_at      TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_artist_features_artist_time
    ON artist_features (artist_id, computed_at);

-- ============================================================
-- 10. recommendations
-- ============================================================
CREATE TABLE IF NOT EXISTS recommendations (
    id                      VARCHAR(36) PRIMARY KEY,
    label_id                VARCHAR(36) NOT NULL REFERENCES labels(id),
    artist_id               VARCHAR(36) NOT NULL REFERENCES artists(id),
    batch_id                VARCHAR(36) NOT NULL,
    fit_score               FLOAT NOT NULL,
    momentum_score          FLOAT NOT NULL,
    risk_score              FLOAT NOT NULL,
    final_score             FLOAT NOT NULL,
    nearest_cluster_id      VARCHAR(36),
    nearest_roster_artist_id VARCHAR(36),
    score_breakdown         JSONB DEFAULT '{}',
    created_at              TIMESTAMP DEFAULT NOW(),
    updated_at              TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_recommendation_label_batch
    ON recommendations (label_id, batch_id);

-- ============================================================
-- 11. feedback
-- ============================================================
CREATE TABLE IF NOT EXISTS feedback (
    id                  VARCHAR(36) PRIMARY KEY,
    label_id            VARCHAR(36) NOT NULL REFERENCES labels(id),
    artist_id           VARCHAR(36) NOT NULL REFERENCES artists(id),
    recommendation_id   VARCHAR(36),
    action              VARCHAR(50) NOT NULL,
    notes               TEXT,
    context             JSONB DEFAULT '{}',
    created_at          TIMESTAMP DEFAULT NOW(),
    updated_at          TIMESTAMP DEFAULT NOW()
);

-- ============================================================
-- 12. label_artist_states
-- ============================================================
CREATE TABLE IF NOT EXISTS label_artist_states (
    id          VARCHAR(36) PRIMARY KEY,
    label_id    VARCHAR(36) NOT NULL REFERENCES labels(id),
    artist_id   VARCHAR(36) NOT NULL REFERENCES artists(id),
    stage       VARCHAR(32) NOT NULL DEFAULT 'new',
    notes       TEXT,
    created_at  TIMESTAMP DEFAULT NOW(),
    updated_at  TIMESTAMP DEFAULT NOW(),
    CONSTRAINT uq_label_artist_state UNIQUE (label_id, artist_id)
);

CREATE INDEX IF NOT EXISTS ix_label_artist_state_label_stage
    ON label_artist_states (label_id, stage);

-- ============================================================
-- 13. watchlists
-- ============================================================
CREATE TABLE IF NOT EXISTS watchlists (
    id          VARCHAR(36) PRIMARY KEY,
    label_id    VARCHAR(36) NOT NULL REFERENCES labels(id),
    name        VARCHAR(255) NOT NULL,
    description TEXT,
    is_active   BOOLEAN DEFAULT TRUE,
    created_at  TIMESTAMP DEFAULT NOW(),
    updated_at  TIMESTAMP DEFAULT NOW(),
    CONSTRAINT uq_watchlist_label_name UNIQUE (label_id, name)
);

CREATE INDEX IF NOT EXISTS ix_watchlist_label ON watchlists (label_id);

-- ============================================================
-- 14. watchlist_items
-- ============================================================
CREATE TABLE IF NOT EXISTS watchlist_items (
    id              VARCHAR(36) PRIMARY KEY,
    watchlist_id    VARCHAR(36) NOT NULL REFERENCES watchlists(id),
    artist_id       VARCHAR(36) NOT NULL REFERENCES artists(id),
    source          VARCHAR(50) DEFAULT 'manual',
    notes           TEXT,
    created_at      TIMESTAMP DEFAULT NOW(),
    updated_at      TIMESTAMP DEFAULT NOW(),
    CONSTRAINT uq_watchlist_item UNIQUE (watchlist_id, artist_id)
);

CREATE INDEX IF NOT EXISTS ix_watchlist_item_watchlist ON watchlist_items (watchlist_id);

-- ============================================================
-- 15. alert_rules
-- ============================================================
CREATE TABLE IF NOT EXISTS alert_rules (
    id          VARCHAR(36) PRIMARY KEY,
    label_id    VARCHAR(36) NOT NULL REFERENCES labels(id),
    name        VARCHAR(255) NOT NULL,
    severity    VARCHAR(20) DEFAULT 'medium',
    is_active   BOOLEAN DEFAULT TRUE,
    criteria    JSONB DEFAULT '{}',
    created_at  TIMESTAMP DEFAULT NOW(),
    updated_at  TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_alert_rule_label ON alert_rules (label_id);

-- ============================================================
-- 16. alerts
-- ============================================================
CREATE TABLE IF NOT EXISTS alerts (
    id              VARCHAR(36) PRIMARY KEY,
    label_id        VARCHAR(36) NOT NULL REFERENCES labels(id),
    artist_id       VARCHAR(36) NOT NULL REFERENCES artists(id),
    watchlist_id    VARCHAR(36) REFERENCES watchlists(id),
    rule_id         VARCHAR(36) REFERENCES alert_rules(id),
    severity        VARCHAR(20) DEFAULT 'medium',
    status          VARCHAR(20) DEFAULT 'new',
    title           VARCHAR(255) NOT NULL,
    description     TEXT,
    context         JSONB DEFAULT '{}',
    created_at      TIMESTAMP DEFAULT NOW(),
    updated_at      TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_alert_label_status_created
    ON alerts (label_id, status, created_at);

-- ============================================================
-- 17. artist_llm_briefs
-- ============================================================
CREATE TABLE IF NOT EXISTS artist_llm_briefs (
    id          VARCHAR(36) PRIMARY KEY,
    artist_id   VARCHAR(36) NOT NULL REFERENCES artists(id),
    label_id    VARCHAR(36),
    input_hash  VARCHAR(64) NOT NULL,
    brief       JSONB NOT NULL,
    created_at  TIMESTAMP DEFAULT NOW(),
    updated_at  TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_llm_brief_artist_hash
    ON artist_llm_briefs (artist_id, input_hash);

-- ============================================================
-- 18. cultural_signals
-- ============================================================
CREATE TABLE IF NOT EXISTS cultural_signals (
    id                  VARCHAR(36) PRIMARY KEY,
    artist_id           VARCHAR(36) NOT NULL REFERENCES artists(id),
    platform            VARCHAR(50) NOT NULL,
    source_type         VARCHAR(50) NOT NULL,
    source_id           VARCHAR(255) NOT NULL,
    captured_at         TIMESTAMP NOT NULL,
    comment_count       INTEGER,
    view_count          INTEGER,
    like_count          INTEGER,
    reply_count         INTEGER,
    unique_commenters   INTEGER,
    repeat_commenters   INTEGER,
    sampled_comments    JSONB,
    rule_sentiment      JSONB,
    extra               JSONB DEFAULT '{}',
    CONSTRAINT uq_cultural_signal UNIQUE (artist_id, platform, source_id)
);

CREATE INDEX IF NOT EXISTS ix_cultural_signal_artist_time
    ON cultural_signals (artist_id, captured_at);

-- ============================================================
-- 19. artist_cultural_profiles
-- ============================================================
CREATE TABLE IF NOT EXISTS artist_cultural_profiles (
    id                      VARCHAR(36) PRIMARY KEY,
    artist_id               VARCHAR(36) NOT NULL REFERENCES artists(id),
    computed_at             TIMESTAMP NOT NULL,
    input_hash              VARCHAR(64) NOT NULL,
    sentiment_strength      FLOAT DEFAULT 0.0,
    engagement_density      FLOAT DEFAULT 0.0,
    superfan_density        FLOAT DEFAULT 0.0,
    cross_platform_presence FLOAT DEFAULT 0.0,
    thematic_clarity        FLOAT DEFAULT 0.0,
    polarization_index      FLOAT DEFAULT 0.0,
    cultural_energy         FLOAT DEFAULT 0.0,
    breakout_candidate      BOOLEAN DEFAULT FALSE,
    sentiment_distribution  JSONB,
    cultural_profile        JSONB,
    created_at              TIMESTAMP DEFAULT NOW(),
    updated_at              TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_cultural_profile_artist_time
    ON artist_cultural_profiles (artist_id, computed_at);

CREATE INDEX IF NOT EXISTS ix_cultural_profile_hash
    ON artist_cultural_profiles (artist_id, input_hash);

-- ============================================================
-- Alembic version tracking (so migrations know where we are)
-- ============================================================
CREATE TABLE IF NOT EXISTS alembic_version (
    version_num VARCHAR(32) NOT NULL,
    CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
);

-- Mark as fully migrated
INSERT INTO alembic_version (version_num) VALUES ('008')
    ON CONFLICT (version_num) DO NOTHING;

COMMIT;

SELECT 'All tables created successfully.' AS status;
