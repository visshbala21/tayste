"""Pre-start script: ensure alembic_version is consistent with actual DB state.

If tables exist but alembic_version is missing (e.g. DB was created outside
Alembic), detect which migrations have already been applied by inspecting
the schema, then stamp the correct version so 'alembic upgrade head' only
runs the remaining migrations.
"""
import os
import sys

from sqlalchemy import create_engine, inspect, text


def get_db_url() -> str | None:
    """Get a sync database URL from environment, trying multiple vars."""
    for var in ("DATABASE_URL_SYNC", "DATABASE_URL"):
        url = os.environ.get(var, "")
        if url:
            # Render uses postgres:// but SQLAlchemy needs postgresql://
            if url.startswith("postgres://"):
                url = "postgresql://" + url[len("postgres://"):]
            # Ensure we have a sync (not async) URL
            url = url.replace("postgresql+asyncpg://", "postgresql://")
            print(f"prestart: using {var}", flush=True)
            return url
    return None


def detect_migration_level(insp) -> str | None:
    """Return the highest migration revision already reflected in the DB schema."""
    tables = set(insp.get_table_names())

    # 001: base tables (labels, artists, snapshots, etc.)
    if "labels" not in tables:
        return None

    level = "001"

    # 002: added pipeline_status column to labels
    label_cols = {c["name"] for c in insp.get_columns("labels")}
    if "pipeline_status" not in label_cols:
        return level
    level = "002"

    # 003: added index ix_platform_accounts_platform_platformid
    if "platform_accounts" in tables:
        pa_indexes = {idx["name"] for idx in insp.get_indexes("platform_accounts")}
        if "ix_platform_accounts_platform_platformid" not in pa_indexes:
            return level
    level = "003"

    # 004: added watchlists, alert_rules, alerts, label_artist_states tables
    if "watchlists" not in tables or "alerts" not in tables:
        return level
    level = "004"

    return level


def main() -> None:
    print("prestart: starting migration stamp check", flush=True)

    url = get_db_url()
    if not url:
        print("prestart: no DATABASE_URL_SYNC or DATABASE_URL found, skipping", flush=True)
        return

    try:
        engine = create_engine(url)
        insp = inspect(engine)
        tables = set(insp.get_table_names())
        print(f"prestart: found {len(tables)} tables in database", flush=True)

        has_app_tables = "labels" in tables
        has_alembic = "alembic_version" in tables

        if has_app_tables and not has_alembic:
            level = detect_migration_level(insp)
            print(f"prestart: tables exist but alembic_version missing — detected level {level}", flush=True)
            with engine.begin() as conn:
                conn.execute(text(
                    "CREATE TABLE alembic_version (version_num VARCHAR(32) NOT NULL)"
                ))
                conn.execute(text(
                    f"INSERT INTO alembic_version (version_num) VALUES ('{level}')"
                ))
            print(f"prestart: stamped migration {level}", flush=True)
        elif has_app_tables and has_alembic:
            # Check if alembic_version is empty or has a stale value
            with engine.begin() as conn:
                row = conn.execute(text("SELECT version_num FROM alembic_version")).fetchone()
                current = row[0] if row else None
            print(f"prestart: alembic_version exists, current stamp = {current!r}", flush=True)

            if not current:
                # Table exists but is empty (failed migration left it behind)
                level = detect_migration_level(insp)
                print(f"prestart: alembic_version is empty — stamping {level}", flush=True)
                with engine.begin() as conn:
                    conn.execute(text(
                        f"INSERT INTO alembic_version (version_num) VALUES ('{level}')"
                    ))
                print(f"prestart: stamped migration {level}", flush=True)
        else:
            print("prestart: fresh database, alembic upgrade will run from scratch", flush=True)
    except Exception as e:
        print(f"prestart: ERROR — {e}", flush=True)
        print("prestart: continuing anyway, alembic upgrade will attempt to run", flush=True)


if __name__ == "__main__":
    main()
