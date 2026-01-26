#!/usr/bin/env python3
"""
generate_script_spec.py

Tiny helper to generate a SPEC markdown file for a script in RegScriptBox.

Usage examples:

    # Basic: just name + one-liner
    python3 generate_script_spec.py WebDocMaker "Fetch PDFs + markdown from URLs"

    # With category path (relative to Scripts/)
    python3 generate_script_spec.py AliasMaker "Create file aliases" --category DocTools

This is *dumb-on-purpose* for now:
- It does NOT introspect code yet.
- It just stamps a structured SPEC template so future you (or an agent) can fill it in.
"""

import argparse
from pathlib import Path
from textwrap import dedent
from datetime import datetime


def make_spec_content(name: str, description: str | None) -> str:
    today = datetime.utcnow().strftime("%Y-%m-%d")
    desc = description or "(fill in: what this script actually does)"

    return dedent(
        f"""\
        # {name} SPEC

        1.0 Identity
        1.1 Name: {name}
        1.2 Location: Scripts/DocTools/{name}.py
        1.3 Created: {today}
        1.4 Status: DRAFT

        2.0 Purpose
        2.1 High-level description
            - {desc}

        3.0 Inputs
        3.1 CLI parameters
            - (fill in)
        3.2 Environment / config
            - (fill in)
        3.3 Files / directories touched
            - (fill in)

        4.0 Outputs
        4.1 Artifacts produced
            - (fill in)
        4.2 Side-effects
            - (fill in)

        5.0 Core Behavior
        5.1 Main steps
            5.1.1 (step 1)
            5.1.2 (step 2)
            5.1.3 (step 3)

        6.0 Failure Modes
        6.1 Common errors
            - (fill in)
        6.2 Safeguards
            - (fill in)

        7.0 Integration Notes
        7.1 How other tools/bots should call this
            - (fill in)
        7.2 Related scripts / bots
            - (fill in)
        """
    )


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        prog="generate_script_spec",
        description="Generate a SPEC markdown file for a RegScriptBox script.",
    )
    parser.add_argument(
        "name",
        help="Base script name (without .py), e.g. WebDocMaker, AliasMaker.",
    )
    parser.add_argument(
        "description",
        nargs="?",
        help="Optional one-line description to prime the SPEC.",
    )

    args = parser.parse_args(argv)

    scripts_root = Path(__file__).resolve().parent
    docs_dir = scripts_root / "Docs"
    docs_dir.mkdir(parents=True, exist_ok=True)

    spec_path = docs_dir / f"{args.name}_SPEC.md"

    if spec_path.exists():
        print(f"Refusing to overwrite existing SPEC: {spec_path}")
        return 1

    content = make_spec_content(args.name, args.description)
    spec_path.write_text(content, encoding="utf-8")
    print(f"✅ Created SPEC: {spec_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
