#!/usr/bin/env python3
import argparse
import csv
import hashlib
import json
import os
import sqlite3
from datetime import datetime, timezone

def utc_now_iso():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")

def safe_json_loads(s):
    if not s or not isinstance(s, str):
        return {}
    try:
        return json.loads(s)
    except Exception:
        return {}

def sha256_hex(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()

def short8(hexstr: str) -> str:
    return (hexstr or "")[:8]

def get_cols(cur, table: str):
    cur.execute(f"PRAGMA table_info({table})")
    return [r[1] for r in cur.fetchall()]

def compute_paths(item: dict) -> dict:
    """
    Compute deterministic paths based on artifact type, env, counts, and sequence.
    This is just the view. Registry stays the truth.
    """
    t = (item.get("artifact_type") or "UNKNOWN").upper()
    aid = item.get("artifact_id") or "UNKNOWN_ID"
    env = item.get("use_env_last") or "unknown"
    capability = item.get("capability") or "unknown"
    sid_count = item.get("sid_count")
    cid_count = item.get("cid_count")
    cid_sequence = item.get("cid_sequence") or ""

    source_path = f"Raw/{t}/{aid}.py"
    explainer_path = f"Raw/{t}/{aid}.explainer.md"

    if t == "PYN":
        sc = int(sid_count or 0)
        artifacts_path = f"Artifacts/PY/{env}/SID-count_{sc:03d}/{aid}/"
    elif t == "SID":
        cc = int(cid_count or 0)
        seq_sig = short8(sha256_hex(cid_sequence)) if cid_sequence else "NOSEQ"
        artifacts_path = f"Artifacts/SID/{env}/CID-count_{cc:03d}/SEQ_{seq_sig}/{aid}/"
    elif t == "CID":
        artifacts_path = f"Artifacts/CID/{aid}/CAP_{capability}/"
    else:
        artifacts_path = f"Artifacts/UNKNOWN/{env}/{aid}/"

    item["source_path"] = source_path
    item["explainer_path"] = explainer_path
    item["artifacts_path"] = artifacts_path
    return item

def build_human_txt(items: list) -> str:
    by_env = {}
    for it in items:
        env = it.get("use_env_last") or "unknown"
        by_env.setdefault(env, []).append(it)

    lines = []
    for env in sorted(by_env.keys()):
        lines.append(f"ENV: {env}")
        lines.append("")
        env_items = by_env[env]

        def sort_key(it):
            t = it.get("artifact_type") or ""
            aid = it.get("artifact_id") or ""
            return (t, aid)

        for it in sorted(env_items, key=sort_key):
            t = it.get("artifact_type") or ""
            aid = it.get("artifact_id") or ""
            h = it.get("code_hash_full") or ""
            cap = it.get("capability") or ""
            sc = it.get("sid_count")
            cc = it.get("cid_count")
            seq = it.get("cid_sequence") or ""
            ap = it.get("artifacts_path") or ""
            sp = it.get("source_path") or ""
            ep = it.get("explainer_path") or ""
            desc = (it.get("description") or "").strip()

            parts = [f"{t} | id={aid}"]
            if h:
                parts.append(f"hash={short8(h)}")
            if cap:
                parts.append(f"cap={cap}")
            if t == "PYN" and sc is not None:
                parts.append(f"sid_count={sc}")
            if t in ("PYN", "SID") and cc is not None:
                parts.append(f"cid_count={cc}")
            if t == "SID" and seq:
                parts.append(f"seq={seq}")
            if desc:
                parts.append(f"desc={desc}")

            lines.append(" | ".join(parts))
            lines.append(f"  artifacts_path: {ap}")
            lines.append(f"  source_path:    {sp}")
            lines.append(f"  explainer_path: {ep}")
            lines.append("")

        lines.append("")

    return "\n".join(lines).rstrip() + "\n"

def build_human_md(items: list) -> str:
    by_env = {}
    for it in items:
        env = it.get("use_env_last") or "unknown"
        by_env.setdefault(env, []).append(it)

    out = []
    out.append("# Artifacts Index")
    out.append("")
    out.append(f"Generated: {utc_now_iso()}")
    out.append("")

    for env in sorted(by_env.keys()):
        out.append(f"## ENV: {env}")
        out.append("")
        out.append("| Type | ID | Hash | Capability | SID Count | CID Count | Sequence | Description | Artifacts Path | Source Path | Explainer Path |")
        out.append("|---|---|---|---|---:|---:|---|---|---|---|---|")

        def sort_key(it):
            return (it.get("artifact_type") or "", it.get("artifact_id") or "")

        for it in sorted(by_env[env], key=sort_key):
            t = it.get("artifact_type") or ""
            aid = it.get("artifact_id") or ""
            h = short8(it.get("code_hash_full") or "")
            cap = it.get("capability") or ""
            sc = it.get("sid_count") if t == "PYN" else ""
            cc = it.get("cid_count") if t in ("PYN", "SID") else ""
            seq = it.get("cid_sequence") if t == "SID" else ""
            desc = (it.get("description") or "").replace("\n", " ").strip()
            ap = it.get("artifacts_path") or ""
            sp = it.get("source_path") or ""
            ep = it.get("explainer_path") or ""
            out.append(f"| {t} | {aid} | {h} | {cap} | {sc} | {cc} | {seq} | {desc} | {ap} | {sp} | {ep} |")

        out.append("")

    return "\n".join(out).rstrip() + "\n"

def structural_rows_from_items(items: list):
    rows = []
    for it in items:
        rows.append({
            "artifact_type": it.get("artifact_type"),
            "artifact_id": it.get("artifact_id"),
            "code_hash_full": it.get("code_hash_full"),
            "capability": it.get("capability"),
            "cid_sequence": it.get("cid_sequence"),
            "use_env_last": it.get("use_env_last"),
        })
    rows_sorted = sorted(
        rows,
        key=lambda r: (
            r.get("artifact_type") or "",
            r.get("artifact_id") or "",
            r.get("capability") or "",
            r.get("use_env_last") or "",
        ),
    )
    return rows_sorted

def structural_signature(items: list) -> str:
    rows_sorted = structural_rows_from_items(items)
    payload = json.dumps(rows_sorted, sort_keys=True, separators=(",", ":"))
    return sha256_hex(payload)

def main():
    ap = argparse.ArgumentParser(
        description="Indexer: reads registry, compares to current manifest, only rewrites repo index files on structural change."
    )
    ap.add_argument("--db", required=True, help="Path to registry sqlite file (outside repo is fine)")
    ap.add_argument("--table", default="scan_events", help="Registry table name")
    ap.add_argument("--json-out", default="Artifacts/index-manifest.json", help="Repo: machine index JSON")
    ap.add_argument("--txt-out", default="Artifacts/index.txt", help="Repo: human index TXT")
    ap.add_argument("--md-out", default="Artifacts/index.md", help="Repo: human index MD")
    ap.add_argument("--stats-out", default=None, help="Outside repo: noisy stats CSV (updates every run)")
    args = ap.parse_args()

    if not os.path.exists(args.db):
        raise SystemExit(f"DB not found: {args.db}")

    con = sqlite3.connect(args.db)
    cur = con.cursor()
    cols = get_cols(cur, args.table)
    if not cols:
        raise SystemExit(f"Table not found or empty: {args.table}")

    cur.execute(f"SELECT * FROM {args.table}")
    rows = cur.fetchall()
    col_idx = {name: i for i, name in enumerate(cols)}

    def get(row, name, meta=None):
        if name in col_idx:
            return row[col_idx[name]]
        if meta:
            return meta.get(name)
        return None

    items = []
    for r in rows:
        meta = safe_json_loads(get(r, "metadata_json") or get(r, "meta_json"))

        artifact_type = get(r, "artifact_type", meta) or get(r, "type", meta) or meta.get("artifact_type")
        artifact_id   = get(r, "artifact_id", meta) or get(r, "id", meta) or meta.get("artifact_id")

        item = {
            "artifact_type": artifact_type,
            "artifact_id": artifact_id,
            "use_env_last": get(r, "use_env_last", meta) or meta.get("use_env_last") or None,
            "capability": get(r, "capability", meta) or meta.get("capability") or None,
            "sid_count": get(r, "sid_count", meta),
            "cid_count": get(r, "cid_count", meta),
            "cid_sequence": get(r, "cid_sequence", meta) or meta.get("cid_sequence") or meta.get("cid_seq") or None,
            "code_hash_full": get(r, "code_hash_full", meta) or meta.get("code_hash_full") or None,
            "description": get(r, "description", meta) or meta.get("description") or None,
        }

        item = compute_paths(item)
        items.append(item)

    # Compute structural signature from current registry view
    new_sig = structural_signature(items)

    # Always update external stats if requested
    if args.stats_out:
        os.makedirs(os.path.dirname(args.stats_out) or ".", exist_ok=True)
        if "scan_id" in cols and "timestamp_utc" in cols:
            cur.execute(f"SELECT COUNT(DISTINCT scan_id) FROM {args.table}")
            total_scans = cur.fetchone()[0] or 0
            cur.execute(f"""
                SELECT artifact_type, artifact_id,
                       COUNT(DISTINCT scan_id) AS scans_present,
                       MAX(timestamp_utc) AS last_seen
                FROM {args.table}
                GROUP BY artifact_type, artifact_id
            """)
            stat_rows = cur.fetchall()
            with open(args.stats_out, "w", newline="", encoding="utf-8") as f:
                w = csv.writer(f)
                w.writerow(["artifact_type","artifact_id","scans_present","total_scans","presence_pct","last_seen_utc"])
                for t, aid, scans_present, last_seen in stat_rows:
                    pct = (float(scans_present) / float(total_scans) * 100.0) if total_scans else 0.0
                    w.writerow([t, aid, scans_present, total_scans, f"{pct:.4f}", last_seen])
        else:
            with open(args.stats_out, "w", newline="", encoding="utf-8") as f:
                w = csv.writer(f)
                w.writerow(["note"])
                w.writerow(["scan_id/timestamp_utc not available; stats limited."])

    con.close()

    # Load previous manifest, if it exists
    prev_sig = None
    if os.path.exists(args.json_out):
        try:
            with open(args.json_out, "r", encoding="utf-8") as f:
                old_manifest = json.load(f)
            prev_sig = old_manifest.get("structural_signature")
        except Exception:
            prev_sig = None

    # If structural signature is unchanged, don't rewrite repo files
    if prev_sig == new_sig:
        print("No structural change detected. Repo index files not rewritten.")
        return

    # Structural change: rewrite manifest, TXT, MD
    os.makedirs(os.path.dirname(args.json_out) or ".", exist_ok=True)

    manifest = {
        "generated_at_utc": utc_now_iso(),
        "schema_version": 1,
        "structural_signature": new_sig,
        "source_db": args.db,
        "table": args.table,
        "item_count": len(items),
        "items": items,
    }

    json_text = json.dumps(manifest, indent=2, sort_keys=False) + "\n"
    with open(args.json_out, "w", encoding="utf-8") as f:
        f.write(json_text)

    txt_text = build_human_txt(items)
    with open(args.txt_out, "w", encoding="utf-8") as f:
        f.write(txt_text)

    md_text = build_human_md(items)
    with open(args.md_out, "w", encoding="utf-8") as f:
        f.write(md_text)

    print("Structural change detected. Repo index files updated.")

if __name__ == "__main__":
    main()
