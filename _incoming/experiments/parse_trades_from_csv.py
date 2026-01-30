import csv
import re
from datetime import datetime

# === Config ===
INPUT_CSV = "trades_raw.csv"      # your existing CSV
OUTPUT_CSV = "trades_parsed.csv"  # new enriched CSV

# Name of the "sequence" column in your CSV.
# If your header is different, change this to match.
SEQUENCE_COL_CANDIDATES = ["sequence_full", "sequence", "seq"]

# === Regex patterns to parse fills ===

STRAT_COMPLETED_RE = re.compile(
    r"^(?P<dt>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) .*?\[STRATEGY\] Order Completed by the broker \| type:\s+(?P<side>Buy|Sell), exec_type:\s+(?P<exec_type>Market|Stop|Limit), executed_size:\s+(?P<size>-?\d+(?:\.\d+)?), executed_price:\s+(?P<price>\d+(?:\.\d+)?), ref_id:\s+(?P<ref_id>\d+)",
    re.IGNORECASE,
)

ORDER_COMPLETED_RE = re.compile(
    r"^(?P<dt>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) - ORDER \| ref=(?P<ref_id>\d+) status=(?P<status>\w+) exectype=(?P<exectype>\d+) size=(?P<size>-?\d+(?:\.\d+)?) exec_price=(?P<price>\d+(?:\.\d+)?)",
    re.IGNORECASE,
)


def parse_events(sequence_text: str):
    """
    Given the big 'sequence' string for a row, extract all completed fills
    (both [STRATEGY] and bare ORDER lines).
    Returns a list of dicts sorted by datetime.
    """
    events = []
    if not sequence_text:
        return events

    parts = sequence_text.split("⏐")
    for raw in parts:
        line = raw.strip()
        if not line:
            continue

        # Try [STRATEGY] Completed lines first
        m = STRAT_COMPLETED_RE.search(line)
        if m:
            d = m.groupdict()
            events.append(
                {
                    "dt": datetime.strptime(d["dt"], "%Y-%m-%d %H:%M:%S"),
                    "side": d["side"].upper(),
                    "exec_type": d["exec_type"].upper(),  # MARKET / STOP / LIMIT
                    "size": float(d["size"]),
                    "price": float(d["price"]),
                    "ref_id": int(d["ref_id"]),
                    "source": "STRATEGY",
                    "raw": line,
                }
            )
            continue

        # Fall back to plain ORDER | ... Completed lines
        m2 = ORDER_COMPLETED_RE.search(line)
        if m2:
            d = m2.groupdict()
            if d["status"] != "Completed":
                continue
            code = d["exectype"]
            exec_type = {"0": "MARKET", "2": "LIMIT", "3": "STOP"}.get(code, code)

            events.append(
                {
                    "dt": datetime.strptime(d["dt"], "%Y-%m-%d %H:%M:%S"),
                    "side": None,  # we don't know Buy/Sell from this line alone
                    "exec_type": exec_type,
                    "size": float(d["size"]),
                    "price": float(d["price"]),
                    "ref_id": int(d["ref_id"]),
                    "source": "ORDER",
                    "raw": line,
                }
            )

    events.sort(key=lambda e: e["dt"])
    return events


def enrich_row(row, seq_col_name):
    """
    Take one CSV row (dict), parse its sequence column, and add:
      - entry_exec_dt / price / size
      - exit_exec_dt / price / size / type
      - realized_pnl_points
      - realized_rr  (based on SL from row)
      - fill_events  (count of completed fills in sequence)
    """
    sequence_text = row.get(seq_col_name, "")
    events = parse_events(sequence_text)

    # Default blank outputs
    out = dict(row)  # start with original columns
    out.update(
        {
            "entry_exec_dt": "",
            "entry_exec_price": "",
            "entry_exec_size": "",
            "exit_exec_dt": "",
            "exit_exec_price": "",
            "exit_exec_size": "",
            "exit_exec_type": "",
            "exit_source": "",
            "fill_events": len(events),
            "realized_pnl_points": "",
            "realized_rr": "",
        }
    )

    if not events:
        return out

    # Pick entry = first MARKET fill if present, otherwise the first fill
    market_events = [e for e in events if e["exec_type"] == "MARKET"]
    if market_events:
        entry = market_events[0]
    else:
        entry = events[0]

    # Exit = last fill in the sequence
    exit_event = events[-1]

    # Write basic fill info
    out["entry_exec_dt"] = entry["dt"].strftime("%Y-%m-%d %H:%M:%S")
    out["entry_exec_price"] = f"{entry['price']:.5f}"
    out["entry_exec_size"] = f"{entry['size']:.5f}"

    out["exit_exec_dt"] = exit_event["dt"].strftime("%Y-%m-%d %H:%M:%S")
    out["exit_exec_price"] = f"{exit_event['price']:.5f}"
    out["exit_exec_size"] = f"{exit_event['size']:.5f}"
    out["exit_exec_type"] = exit_event["exec_type"]
    out["exit_source"] = exit_event["source"]

    # Try to compute realized PnL in points and realized R:R from SL
    try:
        side = out.get("side", "") or out.get("direction", "")
        side = side.upper()
        dir_mult = 1 if side == "LONG" else -1

        entry_price = float(entry["price"])
        exit_price = float(exit_event["price"])
        sl_price = float(out.get("sl_price") or out.get("sl") or "")

        realized_points = (exit_price - entry_price) * dir_mult
        out["realized_pnl_points"] = f"{realized_points:.5f}"

        risk_per_unit = (entry_price - sl_price) * dir_mult
        if risk_per_unit != 0:
            realized_rr = realized_points / risk_per_unit
            out["realized_rr"] = f"{realized_rr:.5f}"
    except Exception:
        # If anything is missing / bad, just leave RR blank
        pass

    return out


def main():
    # Open input CSV and detect the sequence column
    with open(INPUT_CSV, "r", newline="") as f_in:
        reader = csv.DictReader(f_in)
        fieldnames = reader.fieldnames or []

        seq_col_name = None
        for cand in SEQUENCE_COL_CANDIDATES:
            if cand in fieldnames:
                seq_col_name = cand
                break
        if seq_col_name is None:
            # Fall back to last column if we can't find by name
            seq_col_name = fieldnames[-1]

        # Build new header: original + our derived columns
        extra_cols = [
            "entry_exec_dt",
            "entry_exec_price",
            "entry_exec_size",
            "exit_exec_dt",
            "exit_exec_price",
            "exit_exec_size",
            "exit_exec_type",
            "exit_source",
            "fill_events",
            "realized_pnl_points",
            "realized_rr",
        ]

        new_fieldnames = fieldnames + [c for c in extra_cols if c not in fieldnames]

        with open(OUTPUT_CSV, "w", newline="") as f_out:
            writer = csv.DictWriter(f_out, fieldnames=new_fieldnames)
            writer.writeheader()

            for row in reader:
                enriched = enrich_row(row, seq_col_name)
                writer.writerow(enriched)


if __name__ == "__main__":
    main()
