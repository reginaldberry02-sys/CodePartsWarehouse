#!/usr/bin/env python3
"""
ensure_specs_for_scripts.py

Walk RegScriptBox/Scripts and ensure each top-level tool script has a SPEC:

- Skips:
    - anything under a "chunks" directory
    - __init__.py

- For each *.py:
    - tool_name = filename without .py
    - SPEC path = Docs/<tool_name>_SPEC.md
    - if missing, call generate_script_spec.py
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def resolve_paths() -> tuple[Path, Path, Path]:
    here = Path(__file__).resolve()
    scripts_root = here.parents[1]   # .../Scripts
    repo_root = here.parents[2]      # .../RegScriptBox
    return here, scripts_root, repo_root


def iter_tool_scripts(scripts_root: Path):
    """
    Yield *.py files that should have SPECs:
    - under Scripts/
    - NOT under any 'chunks' directory
    - NOT named __init__.py
    """
    for path in scripts_root.rglob("*.py"):
        # skip DocTools helpers themselves
        if "/DocTools/" in str(path):
            continue
        # skip chunks
        if "chunks" in [p.name for p in path.parents]:
            continue
        # skip package inits
        if path.name == "__init__.py":
            continue
        yield path


def main(argv=None) -> int:
    here, scripts_root, _ = resolve_paths()

    spec_script = here.with_name("generate_script_spec.py")
    if not spec_script.exists():
        print("ERROR: generate_script_spec.py not found next to this script.")
        return 1

    docs_dir = here.with_name("Docs")
    docs_dir.mkdir(parents=True, exist_ok=True)

    created = 0
    skipped = 0

    for script in iter_tool_scripts(scripts_root):
        tool_name = script.stem
        spec_path = docs_dir / f"{tool_name}_SPEC.md"

        if spec_path.exists():
            print(f"[spec] EXISTS  -> {spec_path.name} (for {script.name})")
            skipped += 1
            continue

        desc = f"Script tool {tool_name}"
        cmd = [
            sys.executable,
            str(spec_script),
            tool_name,
            desc,
        ]
        print(f"[spec] CREATE -> {spec_path.name} (for {script.name})")
        subprocess.run(cmd, check=False)
        created += 1

    print(f"\nDone. Created={created}, Existing={skipped}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
