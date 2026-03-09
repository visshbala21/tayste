-- Clear all application data (respects FK constraints via deletion order)
-- Run with: psql $DATABASE_URL -f scripts/clear_all_data.sql
-- Or:       docker compose exec db psql -U tayste -d tayste -f /scripts/clear_all_data.sql

BEGIN;

-- 1. Leaf tables (no dependents)
TRUNCATE alerts CASCADE;
TRUNCATE alert_rules CASCADE;
TRUNCATE watchlist_items CASCADE;
TRUNCATE watchlists CASCADE;
TRUNCATE feedback CASCADE;
TRUNCATE label_artist_states CASCADE;
TRUNCATE recommendations CASCADE;
TRUNCATE label_clusters CASCADE;
TRUNCATE artist_llm_briefs CASCADE;
TRUNCATE artist_cultural_profiles CASCADE;
TRUNCATE cultural_signals CASCADE;
TRUNCATE embeddings CASCADE;
TRUNCATE artist_features CASCADE;
TRUNCATE snapshots CASCADE;
TRUNCATE roster_memberships CASCADE;
TRUNCATE platform_accounts CASCADE;

-- 2. Core tables
TRUNCATE labels CASCADE;
TRUNCATE artists CASCADE;

-- 3. User accounts
TRUNCATE profiles CASCADE;

COMMIT;

-- Summary
SELECT 'All data cleared.' AS status;
