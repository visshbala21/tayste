#!/usr/bin/env python3
"""Soundcharts pilot harness.

Goal: Validate ID-based resolution quality before committing to a paid tier.

Input formats:
- CSV/TSV with columns: name, platform, platform_id, expected_name, expected_uuid
- JSON array of objects with the same fields
- JSON object with key "artists" containing the array

Example CSV row:
name,platform,platform_id,expected_name,expected_uuid
Artist A,spotify,0TnOYISbd1XYRBk9myaseg,Artist A,

Usage:
  python backend/tools/soundcharts_pilot.py --input roster.csv
  python backend/tools/soundcharts_pilot.py --input roster.json --output report.json

Required env vars:
  SOUNDCHARTS_APP_ID
  SOUNDCHARTS_API_KEY
Optional:
  SOUNDCHARTS_API_BASE (default: https://customer.api.soundcharts.com)
"""

from __future__ import annotations

import argparse
import asyncio
import csv
import json
import os
import re
import time
from dataclasses import asdict, dataclass
from typing import Any, Iterable

import httpx

DEFAULT_API_BASE = "https://customer.api.soundcharts.com"
DEFAULT_API_VERSION = "v2.9"
DEFAULT_TIMEOUT = 20


@dataclass
class InputEntry:
    name: str | None
    platform: str
    platform_id: str
    expected_name: str | None = None
    expected_uuid: str | None = None
    label: str | None = None


@dataclass
class ResultRow:
    index: int
    platform: str
    platform_id: str
    expected_name: str | None
    expected_uuid: str | None
    status: str
    http_status: int | None
    artist_name: str | None
    artist_uuid: str | None
    match: bool | None
    match_reason: str | None
    latency_ms: int | None
    error: str | None
    response_preview: str | None = None


def _normalize_name(value: str | None) -> str:
    if not value:
        return ""
    value = value.lower().strip()
    value = re.sub(r"[^a-z0-9\s]", "", value)
    value = re.sub(r"\s+", " ", value)
    return value


def _first_truthy(*values: Any) -> Any:
    for value in values:
        if value:
            return value
    return None


def _extract_artist(payload: Any) -> tuple[str | None, str | None]:
    if payload is None:
        return None, None
    if isinstance(payload, list) and payload:
        payload = payload[0]
    if isinstance(payload, dict):
        candidate = payload
        for key in ("artist", "data", "result", "item"):
            if key in candidate and isinstance(candidate[key], (dict, list)):
                candidate = candidate[key]
                if isinstance(candidate, list) and candidate:
                    candidate = candidate[0]
                break
        if isinstance(candidate, dict):
            name = _first_truthy(
                candidate.get("name"),
                candidate.get("artistName"),
                candidate.get("displayName"),
            )
            uuid = _first_truthy(
                candidate.get("uuid"),
                candidate.get("id"),
                candidate.get("artistUuid"),
            )
            return name, uuid
    return None, None


def _extract_identifiers(payload: Any) -> list[str]:
    if payload is None:
        return []
    if isinstance(payload, dict):
        for key in ("identifiers", "data", "results", "items"):
            if key in payload and isinstance(payload[key], list):
                payload = payload[key]
                break
    if isinstance(payload, list):
        values: list[str] = []
        for item in payload:
            if isinstance(item, dict):
                ident = _first_truthy(item.get("identifier"), item.get("id"), item.get("value"))
                if ident:
                    values.append(str(ident))
            elif isinstance(item, str):
                values.append(item)
        return values
    return []


def _match_artist(entry: InputEntry, artist_name: str | None, artist_uuid: str | None, mode: str) -> tuple[bool | None, str | None]:
    expected_uuid = entry.expected_uuid
    expected_name = entry.expected_name or entry.name

    if expected_uuid:
        if not artist_uuid:
            return False, "expected_uuid_missing_returned_uuid"
        return (expected_uuid == artist_uuid, "uuid_match" if expected_uuid == artist_uuid else "uuid_mismatch")

    if not expected_name:
        return None, "no_expected_name"

    if not artist_name:
        return False, "expected_name_missing_returned_name"

    if mode == "contains":
        left = _normalize_name(artist_name)
        right = _normalize_name(expected_name)
        return (right in left or left in right, "name_contains" if right in left or left in right else "name_mismatch")

    return (_normalize_name(expected_name) == _normalize_name(artist_name), "name_match" if _normalize_name(expected_name) == _normalize_name(artist_name) else "name_mismatch")


def _load_entries(path: str) -> list[InputEntry]:
    ext = os.path.splitext(path)[1].lower()
    if ext in {".csv", ".tsv"}:
        delimiter = "\t" if ext == ".tsv" else ","
        with open(path, "r", newline="", encoding="utf-8") as handle:
            reader = csv.DictReader(handle, delimiter=delimiter)
            entries = []
            for row in reader:
                platform = (row.get("platform") or row.get("service") or "").strip().lower()
                platform_id = (row.get("platform_id") or row.get("platformId") or row.get("id") or "").strip()
                if not platform or not platform_id:
                    continue
                entries.append(InputEntry(
                    name=(row.get("name") or row.get("artist") or row.get("artist_name")),
                    platform=platform,
                    platform_id=platform_id,
                    expected_name=(row.get("expected_name") or row.get("expectedName")),
                    expected_uuid=(row.get("expected_uuid") or row.get("expectedUuid")),
                    label=(row.get("label") or row.get("label_name")),
                ))
            return entries

    with open(path, "r", encoding="utf-8") as handle:
        data = json.load(handle)

    if isinstance(data, dict) and isinstance(data.get("artists"), list):
        data = data["artists"]

    if not isinstance(data, list):
        raise ValueError("Unsupported JSON format; expected list or {artists: []}")

    entries: list[InputEntry] = []
    for row in data:
        if not isinstance(row, dict):
            continue
        platform = str(row.get("platform") or row.get("service") or "").strip().lower()
        platform_id = str(row.get("platform_id") or row.get("platformId") or row.get("id") or "").strip()
        if not platform or not platform_id:
            continue
        entries.append(InputEntry(
            name=row.get("name") or row.get("artist") or row.get("artist_name"),
            platform=platform,
            platform_id=platform_id,
            expected_name=row.get("expected_name") or row.get("expectedName"),
            expected_uuid=row.get("expected_uuid") or row.get("expectedUuid"),
            label=row.get("label") or row.get("label_name"),
        ))
    return entries


def _build_headers(app_id: str, api_key: str) -> dict[str, str]:
    return {
        "x-app-id": app_id,
        "x-api-key": api_key,
        "accept": "application/json",
    }


def _get_env(name: str, default: str | None = None) -> str | None:
    value = os.getenv(name)
    if value is None or value == "":
        return default
    return value


def _score_summary(results: Iterable[ResultRow]) -> dict[str, Any]:
    totals = {
        "total": 0,
        "resolved": 0,
        "missing": 0,
        "unauthorized": 0,
        "forbidden": 0,
        "errors": 0,
        "matches_evaluated": 0,
        "matches_correct": 0,
    }

    for row in results:
        totals["total"] += 1
        if row.status == "resolved":
            totals["resolved"] += 1
        elif row.status == "missing":
            totals["missing"] += 1
        elif row.status == "unauthorized":
            totals["unauthorized"] += 1
        elif row.status == "forbidden":
            totals["forbidden"] += 1
        elif row.status == "error":
            totals["errors"] += 1

        if row.match is not None:
            totals["matches_evaluated"] += 1
            if row.match:
                totals["matches_correct"] += 1

    precision = None
    if totals["matches_evaluated"] > 0:
        precision = totals["matches_correct"] / totals["matches_evaluated"]

    return {**totals, "precision": precision}


async def _fetch_artist(
    client: httpx.AsyncClient,
    entry: InputEntry,
    api_base: str,
    api_version: str,
    headers: dict[str, str],
    match_mode: str,
    verify_identifiers: bool,
    include_response: bool,
    timeout: float,
    idx: int,
) -> ResultRow:
    url = f"{api_base}/api/{api_version}/artist/by-platform/{entry.platform}/{entry.platform_id}"
    start = time.monotonic()
    try:
        resp = await client.get(url, headers=headers, timeout=timeout)
        latency_ms = int((time.monotonic() - start) * 1000)
    except Exception as exc:
        return ResultRow(
            index=idx,
            platform=entry.platform,
            platform_id=entry.platform_id,
            expected_name=entry.expected_name or entry.name,
            expected_uuid=entry.expected_uuid,
            status="error",
            http_status=None,
            artist_name=None,
            artist_uuid=None,
            match=None,
            match_reason=None,
            latency_ms=None,
            error=str(exc),
        )

    if resp.status_code == 404:
        return ResultRow(
            index=idx,
            platform=entry.platform,
            platform_id=entry.platform_id,
            expected_name=entry.expected_name or entry.name,
            expected_uuid=entry.expected_uuid,
            status="missing",
            http_status=resp.status_code,
            artist_name=None,
            artist_uuid=None,
            match=False if (entry.expected_name or entry.expected_uuid or entry.name) else None,
            match_reason="not_found",
            latency_ms=latency_ms,
            error=None,
            response_preview=None,
        )

    if resp.status_code == 401:
        return ResultRow(
            index=idx,
            platform=entry.platform,
            platform_id=entry.platform_id,
            expected_name=entry.expected_name or entry.name,
            expected_uuid=entry.expected_uuid,
            status="unauthorized",
            http_status=resp.status_code,
            artist_name=None,
            artist_uuid=None,
            match=None,
            match_reason=None,
            latency_ms=latency_ms,
            error=resp.text,
            response_preview=None,
        )

    if resp.status_code == 403:
        return ResultRow(
            index=idx,
            platform=entry.platform,
            platform_id=entry.platform_id,
            expected_name=entry.expected_name or entry.name,
            expected_uuid=entry.expected_uuid,
            status="forbidden",
            http_status=resp.status_code,
            artist_name=None,
            artist_uuid=None,
            match=None,
            match_reason=None,
            latency_ms=latency_ms,
            error=resp.text,
            response_preview=None,
        )

    if resp.status_code >= 400:
        return ResultRow(
            index=idx,
            platform=entry.platform,
            platform_id=entry.platform_id,
            expected_name=entry.expected_name or entry.name,
            expected_uuid=entry.expected_uuid,
            status="error",
            http_status=resp.status_code,
            artist_name=None,
            artist_uuid=None,
            match=None,
            match_reason=None,
            latency_ms=latency_ms,
            error=resp.text,
            response_preview=None,
        )

    payload = None
    try:
        payload = resp.json()
    except Exception:
        payload = None

    response_preview = None
    if include_response:
        try:
            response_preview = resp.text
        except Exception:
            response_preview = None
        if response_preview and len(response_preview) > 4000:
            response_preview = response_preview[:4000] + "...(truncated)"

    artist_name, artist_uuid = _extract_artist(payload)

    match, match_reason = _match_artist(entry, artist_name, artist_uuid, match_mode)

    if verify_identifiers and artist_uuid:
        id_url = f"{api_base}/api/v2/artist/{artist_uuid}/identifiers"
        try:
            id_resp = await client.get(id_url, headers=headers, timeout=timeout)
            if id_resp.status_code < 400:
                identifiers = _extract_identifiers(id_resp.json())
                if entry.platform_id not in identifiers:
                    match = False if match is not None else None
                    match_reason = (match_reason or "") + "|identifier_mismatch"
        except Exception:
            pass

    return ResultRow(
        index=idx,
        platform=entry.platform,
        platform_id=entry.platform_id,
        expected_name=entry.expected_name or entry.name,
        expected_uuid=entry.expected_uuid,
        status="resolved",
        http_status=resp.status_code,
        artist_name=artist_name,
        artist_uuid=artist_uuid,
        match=match,
        match_reason=match_reason,
        latency_ms=latency_ms,
        error=None,
        response_preview=response_preview,
    )


async def _run_async(args: argparse.Namespace) -> dict[str, Any]:
    app_id = args.app_id or _get_env("SOUNDCHARTS_APP_ID")
    api_key = args.api_key or _get_env("SOUNDCHARTS_API_KEY")
    if not app_id or not api_key:
        raise RuntimeError("Missing SOUNDCHARTS_APP_ID or SOUNDCHARTS_API_KEY")

    entries = _load_entries(args.input)
    if args.sample and args.sample > 0:
        entries = entries[: args.sample]

    headers = _build_headers(app_id, api_key)
    api_base = args.api_base or _get_env("SOUNDCHARTS_API_BASE", DEFAULT_API_BASE)
    api_version = args.api_version or DEFAULT_API_VERSION

    results: list[ResultRow] = []
    semaphore = asyncio.Semaphore(args.concurrency)

    async with httpx.AsyncClient() as client:
        async def worker(idx: int, entry: InputEntry):
            async with semaphore:
                row = await _fetch_artist(
                    client=client,
                    entry=entry,
                    api_base=api_base,
                    api_version=api_version,
                    headers=headers,
                    match_mode=args.match_mode,
                    verify_identifiers=args.verify_identifiers,
                    include_response=args.include_response,
                    timeout=args.timeout,
                    idx=idx,
                )
                results.append(row)

        tasks = [worker(idx, entry) for idx, entry in enumerate(entries)]
        if tasks:
            await asyncio.gather(*tasks)

    results.sort(key=lambda r: r.index)
    summary = _score_summary(results)

    report = {
        "summary": summary,
        "results": [asdict(r) for r in results],
        "config": {
            "api_base": api_base,
            "api_version": api_version,
            "match_mode": args.match_mode,
            "verify_identifiers": args.verify_identifiers,
            "concurrency": args.concurrency,
            "timeout": args.timeout,
            "input": args.input,
        },
    }
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description="Soundcharts pilot harness")
    parser.add_argument("--input", required=True, help="Path to CSV/TSV/JSON roster file")
    parser.add_argument("--output", default="soundcharts_pilot_report.json", help="Path to write report JSON")
    parser.add_argument("--api-base", default=None, help="Override API base URL")
    parser.add_argument("--api-version", default=None, help="Override API version for by-platform endpoint")
    parser.add_argument("--app-id", default=None, help="Soundcharts app id (or SOUNDCHARTS_APP_ID env)")
    parser.add_argument("--api-key", default=None, help="Soundcharts api key (or SOUNDCHARTS_API_KEY env)")
    parser.add_argument("--match-mode", choices=["exact", "contains"], default="exact", help="Name match strategy")
    parser.add_argument("--verify-identifiers", action="store_true", help="Check identifiers endpoint for platform id")
    parser.add_argument("--include-response", action="store_true", help="Include response preview for resolved rows")
    parser.add_argument("--concurrency", type=int, default=6, help="Concurrent requests")
    parser.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT, help="Request timeout (seconds)")
    parser.add_argument("--sample", type=int, default=0, help="Limit to first N rows")

    args = parser.parse_args()

    report = asyncio.run(_run_async(args))

    with open(args.output, "w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2)

    summary = report["summary"]
    precision = summary.get("precision")
    precision_str = "n/a" if precision is None else f"{precision:.3f}"

    print("Soundcharts pilot report")
    print(f"  total: {summary['total']}")
    print(f"  resolved: {summary['resolved']}")
    print(f"  missing: {summary['missing']}")
    print(f"  unauthorized: {summary['unauthorized']}")
    print(f"  forbidden: {summary['forbidden']}")
    print(f"  errors: {summary['errors']}")
    print(f"  precision: {precision_str}")
    print(f"  output: {args.output}")


if __name__ == "__main__":
    main()
