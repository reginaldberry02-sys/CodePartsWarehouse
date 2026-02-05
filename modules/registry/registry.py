#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import json
import pathlib
import sqlite3
import sys

DEFAULT_DB = pathlib.Path("registry/registry.sqlite")

SCHEMA_SQL = """
PRAGMA journal_mode=WAL;
PRAGMA synchronous=NORMAL;

CREATE TABLE IF NOT EXISTS scan_events (
  timestamp_utc     TEXT    NOT NULL, -- ISO 8601 with ms, UTC (e.g. 2026-02-01T16:05:12.123Z)
  scan_id           TEXT    NOT NULL, -- YYYYMMDD-NNNNN
  artifact_type     TEXT    NOT NULL, -- PYN|SID|CID
  artifact_id       TEXT    NOT NULL, -- the ID string for that artifact
  parent_id         TEXT,             -- lineage: extracted-from / source parent
  supersedes_id     TEXT,             -- this artifact supersedes another
  superseded_by_id  TEXT,             -- this artifact is superseded by another
  pyn_id            TEXT,             -- owning PYN (or self if artifact_type=PYN)
  sid_count         INTEGER NOT NULL DEFAULT 0,
  cid_count         INTEGER NOT NULL DEFAULT 0,
  capability        TEXT,             -- only meaningful for CID rows
  standalone_status TEXT    NOT NULL DEFAULT 'none', -- none|inventory|runnable
  metadata_json     TEXT              -- JSON string; optional spillover
);

CREATE UNIQUE INDEX IF NOT EXISTS ux_scan_events_scan_artifact
ON scan_events(scan_id, artifact_type, artifact_id);

CREATE INDEX IF NOT EXISTS ix_scan_events_artifact
ON scan_events(artifact_type, artifact_id);

CREATE INDEX IF NOT EXISTS ix_scan_events_time
ON scan_events(timestamp_utc);
"""

def now_utc() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)

def iso_utc_ms(t: dt.datetime) -> str:
    return t.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"

def connect(db: pathlib.Path) -> sqlite3.Connection:
    db.parent.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(str(db))

def init_db(conn: sqlite3.Connection) -> None:
    conn.executescript(SCHEMA_SQL)
    conn.commit()

def next_scan_id(conn: sqlite3.Connection, t: dt.datetime) -> str:
    day = t.strftime("%Y%m%d")
    n = conn.execute(
        "SELECT COUNT(*) FROM scan_events WHERE scan_id LIKE ?",
        (f"{day}-%",),
    ).fetchone()[0] + 1
    return f"{day}-{n:05d}"

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="registry.py")
    p.add_argument("--db", default=str(DEFAULT_DB))
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("init")
    sub.add_parser("schema")

    a = sub.add_parser("append")
    a.add_argument("--scan-id")  # optional override
    a.add_argument("--artifact-type", required=True, choices=["PYN", "SID", "CID"])
    a.add_argument("--artifact-id", required=True)
    a.add_argument("--parent-id")
    a.add_argument("--supersedes-id")
    a.add_argument("--superseded-by-id")
    a.add_argument("--pyn-id")
    a.add_argument("--sid-count", type=int, default=0)
    a.add_argument("--cid-count", type=int, default=0)
    a.add_argument("--capability")
    a.add_argument("--standalone-status", default="none", choices=["none", "inventory", "runnable"])
    a.add_argument("--metadata-json")  # optional JSON string

    return p

def cmd_init(args: argparse.Namespace) -> int:
    db = pathlib.Path(args.db)
    with connect(db) as conn:
        init_db(conn)
    return 0

def cmd_schema(args: argparse.Namespace) -> int:
    print(SCHEMA_SQL.strip())
    return 0

def cmd_append(args: argparse.Namespace) -> int:
    db = pathlib.Path(args.db)
    t = now_utc()
    ts = iso_utc_ms(t)

    meta = None
    if args.metadata_json:
        json.loads(args.metadata_json)  # validate
        meta = args.metadata_json

    with connect(db) as conn:
        init_db(conn)
        sid = args.scan_id or next_scan_id(conn, t)

        # Guardrails
        if args.artifact_type != "PYN" and not args.pyn_id:
            raise SystemExit("ERROR: --pyn-id is required for SID and CID rows")
        if args.artifact_type != "CID" and args.capability:
            raise SystemExit("ERROR: --capability is only allowed for CID rows")
        if args.artifact_type == "CID" and not args.capability:
            raise SystemExit("ERROR: --capability is required for CID rows")

        conn.execute(
            """
            INSERT INTO scan_events (
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

def main(argv: list[str]) -> int:
    p = build_parser()
    args = p.parse_args(argv)

    if args.cmd == "init":
        return cmd_init(args)
    if args.cmd == "schema":
        return cmd_schema(args)
    if args.cmd == "append":
        return cmd_append(args)

    return 2

if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
