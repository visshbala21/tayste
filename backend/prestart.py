"""Pre-start script: ensure alembic_version is consistent with actual DB state.

If tables exist but alembic_version is missing (e.g. DB was created outside
Alembic), detect which migrations have already been applied by inspecting
the schema, then stamp the correct version so 'alembic upgrade head' only
runs the remaining migrations.
"""
import os

from sqlalchemy import create_engine, inspect, text


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
    url = os.environ.get("DATABASE_URL_SYNC", "")
    if not url:
        print("prestart: DATABASE_URL_SYNC not set, skipping stamp check")
        return

    # Render uses postgres:// but SQLAlchemy needs postgresql://
    if url.startswith("postgres://"):
        url = "postgresql://" + url[len("postgres://"):]

    engine = create_engine(url)
    insp = inspect(engine)
    tables = set(insp.get_table_names())

    has_app_tables = "labels" in tables
    has_alembic = "alembic_version" in tables

    if has_app_tables and not has_alembic:
        level = detect_migration_level(insp)
        print(f"prestart: tables exist but alembic_version missing — detected level {level}")
        with engine.begin() as conn:
            conn.execute(text(
                "CREATE TABLE alembic_version (version_num VARCHAR(32) NOT NULL)"
            ))
            conn.execute(text(
                f"INSERT INTO alembic_version (version_num) VALUES ('{level}')"
            ))
        print(f"prestart: stamped migration {level}, 'alembic upgrade head' will apply remaining migrations")
    elif has_app_tables and has_alembic:
        print("prestart: alembic_version exists, nothing to do")
    else:
        print("prestart: fresh database, alembic upgrade will run from scratch")


if __name__ == "__main__":
    main()
