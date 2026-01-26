#!/usr/bin/env python3
import re
import csv
import io
import sys
from datetime import datetime

# ============================================
# usage:
#   python3 chopbot_from_files.py ENTER_FILE ORDER_FILE > trades.csv
# example:
#   python3 chopbot_from_files.py enter_log.txt order_log.txt > trades.csv
# ============================================

if len(sys.argv) != 3:
    print("Usage: python3 chopbot_from_files.py ENTER_FILE ORDER_FILE > trades.csv", file=sys.stderr)
    sys.exit(1)

ENTER_FILE = sys.argv[1]
ORDER_FILE = sys.argv[2]

def read_file_lines(path):
    # Read non-empty lines from a file
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        return [line.rstrip("\n") for line in f if line.strip()]

def parse_dt(line):
    # Find 'YYYY-MM-DD HH:MM:SS' anywhere in line
    m = re.search(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}", line)
    if not m:
        return None
    ts = m.group(0)
    try:
        return datetime.strptime(ts, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        return None

# Pull metadata from ENTER lines
entry_re = re.compile(
    r'(?P<dt>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}).*ENTER_(?P<side>LONG|SHORT)'
    r'.*TREND_DIR=(?P<trend>[A-Z_]+)?'
    r'.*box_low=(?P<box_low>-?[0-9.]+)?'
    r'.*box_high=(?P<box_high>-?[0-9.]+)?'
    r'.*sl=(?P<sl>-?[0-9.]+)?'
    r'.*tp=(?P<tp>-?[0-9.]+)?'
    r'.*rr=(?P<rr>-?[0-9.]+)?'
    r'.*size=(?P<size>-?[0-9.]+)?'
)

# Read files
enter_lines = read_file_lines(ENTER_FILE)
order_lines = read_file_lines(ORDER_FILE)

print(f"[DEBUG] enter_lines={len(enter_lines)} order_lines={len(order_lines)}", file=sys.stderr)

# Merge and sort by time
all_lines = enter_lines + order_lines
all_with_dt = []
for ln in all_lines:
    dt = parse_dt(ln)
    all_with_dt.append((dt, ln))

# Sort: lines with dt first, then lines with no dt at the end
all_with_dt.sort(key=lambda x: (x[0] is None, x[0] or datetime.max))
sorted_lines = [ln for _, ln in all_with_dt]

# Build trades
trades = []
current_trade = None

for line in sorted_lines:
    if "ENTER_LONG" in line or "ENTER_SHORT" in line:
        # close previous trade if any
        if current_trade is not None:
            trades.append(current_trade)

        meta = {
            "entry_dt": "",
            "side": "",
            "trend_dir": "",
            "box_low": "",
            "box_high": "",
            "sl": "",
            "tp": "",
            "planned_rr": "",
            "size": "",
            "sequence": []
        }

        m = entry_re.search(line)
        if m:
            meta["entry_dt"]   = m.group("dt") or ""
            meta["side"]       = m.group("side") or ""
            meta["trend_dir"]  = m.group("trend") or ""
            meta["box_low"]    = m.group("box_low") or ""
            meta["box_high"]   = m.group("box_high") or ""
            meta["sl"]         = m.group("sl") or ""
            meta["tp"]         = m.group("tp") or ""
            meta["planned_rr"] = m.group("rr") or ""
            meta["size"]       = m.group("size") or ""

        meta["sequence"].append(line)
        current_trade = meta
    else:
        # Order / strategy lines get attached to the current trade
        if current_trade is not None:
            current_trade["sequence"].append(line)

# Flush last trade
if current_trade is not None:
    trades.append(current_trade)

print(f"[DEBUG] trades_found={len(trades)}", file=sys.stderr)

# Write CSV to stdout
fieldnames = [
    "entry_dt",
    "side",
    "trend_dir",
    "box_low",
    "box_high",
    "sl",
    "tp",
    "planned_rr",
    "size",
    "sequence",
]

output = io.StringIO()
writer = csv.DictWriter(output, fieldnames=fieldnames)
writer.writeheader()

for t in trades:
    row = t.copy()
    row["sequence"] = " ⏐ ".join(t["sequence"])
    writer.writerow(row)

csv_text = output.getvalue()
print(csv_text, end="")
