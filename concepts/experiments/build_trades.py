import csv
import re

# Input and output filenames (both in the current folder)
INPUT_FILE = "logs.txt"
OUTPUT_FILE = "trades_enriched.csv"

# --- Regexes ---------------------------------------------------------

# ENTRY line:
# 2025-12-24 15:46:00 - ENTER_SHORT | TREND_DIR=CHOP box_low=25577.910000 box_high=25595.160000 sl=25600.832556 tp=25589.371278 rr=1.747 size=23.451826
ENTRY_RE = re.compile(
    r"^(?P<dt>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})"
    r" - ENTER_(?P<side>LONG|SHORT) \| TREND_DIR=(?P<trend>\w+)\s+"
    r"box_low=(?P<box_low>-?\d+(?:\.\d+)?)\s+"
    r"box_high=(?P<box_high>-?\d+(?:\.\d+)?)\s+"
    r"sl=(?P<sl>-?\d+(?:\.\d+)?)\s+"
    r"tp=(?P<tp>-?\d+(?:\.\d+)?)\s+"
    r"rr=(?P<rr>-?\d+(?:\.\d+)?)\s+"
    r"size=(?P<size>-?\d+(?:\.\d+)?)"
)

# [STRATEGY] completed fills:
# 2025-12-23 09:56:00 -0500 [STRATEGY] Order Completed by the broker | type: Buy, exec_type: Market, executed_size: 8.29, executed_price: 25464.86, ref_id: 157
COMPLETED_RE = re.compile(
    r"(?P<dt>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})"
    r".*?\|\s*type:\s*(?P<side_word>Buy|Sell)"
    r",\s*exec_type:\s*(?P<exec_type>Market|Limit|Stop)"
    r".*?executed_size:\s*(?P<size>-?\d+(?:\.\d+)?)"
    r",\s*executed_price:\s*(?P<price>\d+(?:\.\d+)?)",
    re.DOTALL,
)


# --- Helpers ---------------------------------------------------------


def parse_sequence(lines):
    """
    Given all log lines for ONE trade (from ENTER_* up to just before the next ENTER_*),
    extract entry/exit fills from [STRATEGY] 'Order Completed ... executed_*' lines.
    """
    result = {
        "entry_status": "",
        "entry_exec_dt": "",
        "entry_exec_price": "",
        "exit_dt": "",
        "exit_status": "",
        "exit_exec_type": "",
        "exit_exec_price": "",
        "exit_size": "",
        "realized_rr": "",
        "pnl_cash": "",
    }

    if not lines:
        result["entry_status"] = "REJECTED"
        return result

    completed_events = []

    for line in lines:
        m = COMPLETED_RE.search(line)
        if m:
            completed_events.append(m.groupdict())

    # No completed events at all → planned but never actually traded
    if not completed_events:
        result["entry_status"] = "REJECTED"
        return result

    # First Market completion = actual entry
    entry_event = None
    for ev in completed_events:
        if ev["exec_type"] == "Market":
            entry_event = ev
            break

    if entry_event:
        result["entry_status"] = "FILLED"
        result["entry_exec_dt"] = entry_event["dt"]
        result["entry_exec_price"] = entry_event["price"]
    else:
        result["entry_status"] = "REJECTED"

    # Last completed event in the sequence = exit
    exit_event = completed_events[-1]
    result["exit_dt"] = exit_event["dt"]
    result["exit_exec_type"] = exit_event["exec_type"]
    result["exit_exec_price"] = exit_event["price"]
    result["exit_size"] = exit_event["size"]

    if exit_event["exec_type"] == "Limit":
        result["exit_status"] = "TP_HIT"
    elif exit_event["exec_type"] == "Stop":
        result["exit_status"] = "SL_HIT"
    elif exit_event["exec_type"] == "Market":
        result["exit_status"] = "MANUAL_CLOSE"
    else:
        result["exit_status"] = "UNKNOWN"

    return result


def finalize_trade(trade_dict):
    """
    Turn the in-memory trade_dict (entry fields + sequence_lines)
    into a flat row for CSV.
    """
    seq_lines = trade_dict.get("sequence_lines", [])
    seq_info = parse_sequence(seq_lines)

    row = {
        # Core planned entry info
        "entry_dt": trade_dict.get("entry_dt", ""),
        "side": trade_dict.get("side", ""),
        "trend_dir_entry": trade_dict.get("trend_dir_entry", ""),
        "box_low": trade_dict.get("box_low", ""),
        "box_high": trade_dict.get("box_high", ""),
        "sl_price": trade_dict.get("sl_price", ""),
        "tp_price": trade_dict.get("tp_price", ""),
        "planned_rr": trade_dict.get("planned_rr", ""),
        "entry_size": trade_dict.get("entry_size", ""),
        # Execution info from parse_sequence()
        "entry_status": seq_info.get("entry_status", ""),
        "entry_exec_dt": seq_info.get("entry_exec_dt", ""),
        "entry_exec_price": seq_info.get("entry_exec_price", ""),
        "exit_dt": seq_info.get("exit_dt", ""),
        "exit_status": seq_info.get("exit_status", ""),
        "exit_exec_type": seq_info.get("exit_exec_type", ""),
        "exit_exec_price": seq_info.get("exit_exec_price", ""),
        "exit_size": seq_info.get("exit_size", ""),
        "realized_rr": seq_info.get("realized_rr", ""),
        "pnl_cash": seq_info.get("pnl_cash", ""),
        # Full raw sequence for debugging
        "sequence_full": " ⏐ ".join(l.strip() for l in seq_lines),
    }

    return row


def main():
    trades = []
    current_trade = None

    # 1) Read the big log file line-by-line
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        for raw in f:
            line = raw.rstrip("\n")

            # Does this line start a new ENTER_* trade?
            m = ENTRY_RE.match(line)
            if m:
                # If we were already inside a trade, close it out
                if current_trade is not None:
                    trades.append(finalize_trade(current_trade))

                g = m.groupdict()
                current_trade = {
                    "entry_dt": g["dt"],
                    "side": g["side"],
                    "trend_dir_entry": g["trend"],
                    "box_low": g["box_low"],
                    "box_high": g["box_high"],
                    "sl_price": g["sl"],
                    "tp_price": g["tp"],
                    "planned_rr": g["rr"],
                    "entry_size": g["size"],
                    "sequence_lines": [line],
                }
            else:
                # If we're inside a trade, accumulate this line to its sequence
                if current_trade is not None:
                    current_trade["sequence_lines"].append(line)

    # End of file → flush last trade, if any
    if current_trade is not None:
        trades.append(finalize_trade(current_trade))

    # 2) Write CSV
    fieldnames = [
        "entry_dt",
        "side",
        "trend_dir_entry",
        "box_low",
        "box_high",
        "sl_price",
        "tp_price",
        "planned_rr",
        "entry_size",
        "entry_status",
        "entry_exec_dt",
        "entry_exec_price",
        "exit_dt",
        "exit_status",
        "exit_exec_type",
        "exit_exec_price",
        "exit_size",
        "realized_rr",
        "pnl_cash",
        "sequence_full",
    ]

    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as out_f:
        writer = csv.DictWriter(out_f, fieldnames=fieldnames)
        writer.writeheader()
        for tr in trades:
            writer.writerow(tr)

    print(f"Parsed {len(trades)} trades into {OUTPUT_FILE}")


if __name__ == "__main__":
    main()

