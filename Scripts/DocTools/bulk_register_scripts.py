#!/usr/bin/env python3
"""
bulk_register_scripts.py

Scan a folder tree for *.py files and register them into RegScriptBox/Scripts
using register_script.py.

Usage examples:

  # Dry run: see what would be registered from a folder
  python3 bulk_register_scripts.py --root "/path/to/scan" --category experiments --dry-run

  # Actually register everything
  python3 bulk_register_scripts.py --root "/path/to/scan" --category experiments
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def resolve_paths() -> tuple[Path, Path, Path]:
    here = Path(__file__).resolve()
    scripts_root = here.parents[1]   # .../Scripts
    repo_root = here.parents[2]      # .../RegScriptBox
    return here, scripts_root, repo_root


def iter_external_py(root: Path, repo_root: Path):
    root = root.resolve()
    repo_root = repo_root.resolve()

    for path in root.rglob("*.py"):
        # Skip anything already under RegScriptBox
        try:
            path.relative_to(repo_root)
            # if this doesn't raise, it's inside repo_root -> skip
            continue
        except ValueError:
            pass

        yield path


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(
        prog="bulk_register_scripts",
        description="Scan for .py files and register them into RegScriptBox.",
    )
    ap.add_argument(
        "--root",
        required=True,
        help="Folder to scan for *.py files.",
    )
    ap.add_argument(
        "--category",
        help="Category under Scripts/ to register into (e.g. experiments, devtools).",
        default="experiments",
    )
    ap.add_argument(
        "--dry-run",
        action="store_true",
        help="List what would be registered without changing anything.",
    )

    args = ap.parse_args(argv)

    here, scripts_root, repo_root = resolve_paths()
    register_script = here.with_name("register_script.py")

    if not register_script.exists():
        print("ERROR: register_script.py not found next to this script.")
        return 1

    root = Path(args.root).expanduser().resolve()

    print(f"[scan] root={root}")
    print(f"[scan] repo_root={repo_root}")
    print(f"[scan] category={args.category}")
    print(f"[scan] dry_run={args.dry_run}")
    print()

    count = 0
    for src in iter_external_py(root, repo_root):
        count += 1
        tool_name = src.stem
        print(f"[found] {src} -> tool_name={tool_name}")

        if args.dry_run:
            continue

        cmd = [
            sys.executable,
            str(register_script),
            "--src",
            str(src),
            "--name",
            tool_name,
            "--category",
            args.category,
            "--description",
            f"Imported script {tool_name} from {root}",
        ]
        print(f"[register] {' '.join(cmd)}")
        subprocess.run(cmd, check=False)

    print(f"\nDone. Found {count} candidate scripts.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
