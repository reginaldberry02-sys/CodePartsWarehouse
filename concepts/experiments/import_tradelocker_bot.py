#!/usr/bin/env python3
"""
Importer for TradeLocker-style bots using a 3-level pyramid layout.

Per bot <bot_name> we create:

bots/<bot_name>/
  <bot_name>_full.py         # full bot file

  chunks/
    <chunk_name>/
      <chunk_name>_full.py   # full chunk file
      execution/             # visible actions for this chunk (entries/exits/brackets/etc.)
        __init__.py
      math/                  # risk, sizing, indicators, exposure, other math
        __init__.py
      logging/               # logging behavior for this chunk
        __init__.py
      utilities/             # orchestration / helpers / glue for this chunk
        __init__.py

source.py is just your authoring file. This importer does NOT touch it;
it only writes <bot_name>_full.py and the chunks tree.
"""

from pathlib import Path
import argparse

# Chunks we scaffold for every bot by default.
# You can change this list later if you want different chunk names.
CHUNKS = ["core", "entries", "exits", "logging", "risk", "execution", "helpers"]

PART_TYPES = ["execution", "math", "logging", "utilities"]


def import_bot(bot_name: str, src_path: Path, overwrite: bool = False) -> None:
    """
    Import a bot from a TradeLocker-style source file into the pyramid layout.
    """
    if not src_path.exists():
        raise SystemExit(f"Source not found: {src_path}")

    bot_dir = Path("bots") / bot_name
    chunks_dir = bot_dir / "chunks"

    bot_dir.mkdir(parents=True, exist_ok=True)
    chunks_dir.mkdir(parents=True, exist_ok=True)

    source_text = src_path.read_text(encoding="utf-8")

    # 1) Bot-level full file: bots/<bot_name>/<bot_name>_full.py
    bot_full_path = bot_dir / f"{bot_name}_full.py"
    if bot_full_path.exists() and not overwrite:
        print(f"Preserving existing bot_full: {bot_full_path}")
    else:
        bot_full_path.write_text(source_text, encoding="utf-8")
        print(f"✅ Wrote bot_full: {bot_full_path}")

    # 2) Chunk folders + chunk_full + part-type folders
    for chunk in CHUNKS:
        chunk_dir = chunks_dir / chunk
        chunk_dir.mkdir(parents=True, exist_ok=True)

        # Main chunk file: <chunk_name>_full.py
        chunk_full_path = chunk_dir / f"{chunk}_full.py"
        if chunk_full_path.exists() and not overwrite:
            print(f"Preserving existing chunk_full: {chunk_full_path}")
        else:
            stub = (
                f"# {bot_name} - {chunk}_full.py (scaffold)\n"
                f"# Move {chunk}-specific logic here when you split the bot.\n"
            )
            chunk_full_path.write_text(stub, encoding="utf-8")
            print(f"✅ Scaffolded chunk_full: {chunk_full_path}")

        # Part-category folders under the chunk: execution/math/logging/utilities
        for part_type in PART_TYPES:
            part_dir = chunk_dir / part_type
            part_dir.mkdir(parents=True, exist_ok=True)

            init_path = part_dir / "__init__.py"
            if init_path.exists() and not overwrite:
                print(f"Preserving existing {part_type} package: {init_path}")
            else:
                init_stub = (
                    f"# {bot_name} - {chunk} {part_type} package\n"
                    f"# Put {part_type} pieces for this chunk in this folder.\n"
                )
                init_path.write_text(init_stub, encoding="utf-8")
                print(f"✅ Scaffolded {part_type} package: {init_path}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--bot", required=True, help="bot name, e.g. baseframework")
    ap.add_argument("--src", required=True, help="source .py file path")
    ap.add_argument("--overwrite", action="store_true")
    args = ap.parse_args()

    bot = args.bot.strip().lower()
    src = Path(args.src)

    import_bot(bot, src, overwrite=args.overwrite)


if __name__ == "__main__":
    main()

