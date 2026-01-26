#!/usr/bin/env python3
"""
register_script.py

Usage examples:

  # Minimal: infer name from src filename, drop it under Scripts/root
  python3 register_script.py --src /tmp/foo.py

  # With category (e.g. DocTools) + nicer name + description
  python3 register_script.py \
      --src /tmp/foo.py \
      --name WebDocMaker \
      --category DocTools \
      --description "Fetch + convert web docs (PDF/markdown) for archival"

What it does:

  1) Copies the source script into RegScriptBox/Scripts/[category]/[name].py
  2) Calls generate_script_spec.py to create a SPEC if one doesn't exist yet.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path


def resolve_paths() -> tuple[Path, Path, Path]:
    """
    Returns:
        here: this file path
        scripts_root: .../RegScriptBox/Scripts
        repo_root: .../RegScriptBox
    """
    here = Path(__file__).resolve()
    scripts_root = here.parents[1]   # .../Scripts
    repo_root = here.parents[2]      # .../RegScriptBox
    return here, scripts_root, repo_root


def register_script(
    src: Path,
    scripts_root: Path,
    name: str | None,
    category: str | None,
    description: str | None,
) -> Path:
    if not src.exists():
        raise FileNotFoundError(f"Source script not found: {src}")

    if name is None:
        name = src.stem

    # Category folder (optional)
    if category:
        dest_dir = scripts_root / category
    else:
        dest_dir = scripts_root

    dest_dir.mkdir(parents=True, exist_ok=True)
    dest_path = dest_dir / f"{name}.py"

    if dest_path.exists():
        print(f"[register] Dest already exists, not overwriting: {dest_path}")
    else:
        shutil.copy2(src, dest_path)
        print(f"[register] Copied -> {dest_path}")

    return dest_path


def maybe_generate_spec(
    here: Path,
    tool_name: str,
    description: str | None,
) -> None:
    """
    Call generate_script_spec.py if it exists.
    """
    spec_script = here.with_name("generate_script_spec.py")
    if not spec_script.exists():
        print("[register] No generate_script_spec.py found; skipping SPEC generation.")
        return

    desc = description or f"Script tool {tool_name}"
    cmd = [
        sys.executable,
        str(spec_script),
        tool_name,
        desc,
    ]
    print(f"[register] Running SPEC generator: {' '.join(cmd)}")
    try:
        subprocess.run(cmd, check=False)
    except Exception as exc:
        print(f"[register] SPEC generation failed: {exc}")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(
        prog="register_script",
        description="Copy an existing script into RegScriptBox and generate a SPEC.",
    )
    ap.add_argument(
        "--src",
        required=True,
        help="Path to the source .py script you just wrote / ran.",
    )
    ap.add_argument(
        "--name",
        help="Tool name (defaults to src filename without .py).",
    )
    ap.add_argument(
        "--category",
        help="Optional category under Scripts/ (e.g. DocTools, sqlite, devtools).",
    )
    ap.add_argument(
        "--description",
        help="One-line description for the SPEC.",
    )

    args = ap.parse_args(argv)

    here, scripts_root, _ = resolve_paths()

    src_path = Path(args.src).expanduser().resolve()
    tool_name = args.name or src_path.stem

    try:
        dest_path = register_script(
            src=src_path,
            scripts_root=scripts_root,
            name=tool_name,
            category=args.category,
            description=args.description,
        )
    except FileNotFoundError as exc:
        print(f"ERROR: {exc}")
        return 1

    maybe_generate_spec(here, tool_name, args.description)

    print(f"[register] Done. Tool='{tool_name}' at {dest_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
