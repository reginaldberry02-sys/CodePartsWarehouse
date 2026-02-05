#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import json
import pathlib
import sqlite3
import sys

DB_PATH_DEFAULT = pathlib.Path("registry/registry.sqlite")

def now_utc_iso_ms() -> str:
    # Example: 2026-02-01T16:05:12.123Z
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"

def scan_id_for_now(conn: sqlite3.Connection, now_utc: dt.datetime) -> str:
    # YYYYMMDD-NNNNN (counter resets per UTC day)
    day = now_utc.strftime("%Y%m%d")
    cur = conn.execute(
        "SELECT COUNT(*) FROM scan_events WHERE scan_id LIKE ?",
        (f"{day}-%",),
    )
    n = int(cur.fetchone()[0]) + 1
    return f"{day}-{n:05d}"

def ensure_db(conn: sqlite3.Connection) -> None:
    # Table should already exist; this is a guardrail.
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")

def main(argv: list[str]) -> int:
    p = argparse.ArgumentParser(description="Append one scan event to the CodePartsWarehouse registry.")
    p.add_argument("--db", default=str(DB_PATH_DEFAULT), help="Path to registry sqlite db.")
    p.add_argument("--artifact-type", required=True, choices=["PYN", "SID", "CID"])
    p.add_argument("--artifact-id", required=True)
    p.add_argument("--parent-id", default=None)
    p.add_argument("--supersedes-id", default=None)
    p.add_argument("--superseded-by-id", default=None)
    p.add_argument("--pyn-id", default=None)
    p.add_argument("--sid-count", type=int, default=0)
    p.add_argument("--cid-count", type=int, default=0)
    p.add_argument("--capability", default=None)
    p.add_argument("--standalone-status", default="none", choices=["none", "inventory", "runnable"])
    p.add_argument("--metadata-json", default=None, help="Raw JSON string; optional.")

    args = p.parse_args(argv)

    db_path = pathlib.Path(args.db)
    if not db_path.exists():
        print(f"ERROR: db not found: {db_path}", file=sys.stderr)
        return 2

    now = dt.datetime.now(dt.timezone.utc)

    meta = None
    if args.metadata_json:
        try:
            meta_obj = json.loads(args.metadata_json)
            meta = json.dumps(meta_obj, separators=(",", ":"), sort_keys=True)
        except Exception as e:
            print(f"ERROR: metadata-json is not valid JSON: {e}", file=sys.stderr)
            return 3

    with sqlite3.connect(str(db_path)) as conn:
        ensure_db(conn)
        sid = scan_id_for_now(conn, now)
        ts = now_utc_iso_ms()

        conn.execute(
            """
            INSERT INTO scan_events(
              timestamp_utc, scan_id, artifact_type, artifact_id,
              parent_id, supersedes_id, superseded_by_id, pyn_id,
              sid_count, cid_count, capability, standalone_status, metadata_json
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                ts, sid, args.artifact_type, args.artifact_id,
                args.parent_id, args.supersedes_id, args.superseded_by_id, args.pyn_id,
                args.sid_count, args.cid_count, args.capability, args.standalone_status, meta
            ),
        )
        conn.commit()

    print(sid)
    return 0

if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
