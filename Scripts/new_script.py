#!/usr/bin/env python3
"""
new_script.py

Generate a new script module with this layout:

scripts/<category_or_root>/<name>/
    config.py
    core.py
    cli.py
    helpers.py

Usage examples:

    # Create under scripts/ directly
    python3 scripts/new_script.py my_tool

    # Create under scripts/devtools/
    python3 scripts/new_script.py log_cleaner --category devtools
"""

import argparse
from pathlib import Path
from textwrap import dedent


def create_file(path: Path, content: str) -> None:
    """Create a file with the given content if it does not already exist."""
    if path.exists():
        raise FileExistsError(f"{path} already exists")
    path.write_text(content, encoding="utf-8")


def make_module_layout(base_scripts_dir: Path, name: str, category: str | None) -> Path:
    """
    Create the folder and 4-part layout:

    config.py, core.py, cli.py, helpers.py
    """
    if category:
        root = base_scripts_dir / category / name
    else:
        root = base_scripts_dir / name

    root.mkdir(parents=True, exist_ok=False)

    # Basic content templates
    config_content = dedent(
        f"""\
        \"\"\"Configuration for {name}.\"\"\"\n
        TOOL_NAME = "{name}"
        LOG_LEVEL = "INFO"  # or DEBUG, WARNING, etc.
        """
    )

    core_content = dedent(
        f"""\
        \"\"\"Core logic for {name}.\"\"\"\n
        from .config import TOOL_NAME\n
        \n
        def run(**kwargs) -> int:
            \"\"\"Main core function for {name}. Return an int exit code.\"\"\"\n
            # TODO: implement core behavior
            print(f"Running {{TOOL_NAME}} with args: {{kwargs}}")
            return 0
        """
    )

    cli_content = dedent(
        f"""\
        \"\"\"CLI entrypoint for {name}.\"\"\"\n
        import argparse
        from .config import TOOL_NAME
        from .core import run\n
        \n
        def parse_args(argv=None):
            parser = argparse.ArgumentParser(
                prog=TOOL_NAME,
                description="Command-line interface for {name}.",
            )
            # TODO: add specific CLI arguments here
            return parser.parse_args(argv)\n
        \n
        def main(argv=None) -> int:
            args = parse_args(argv)
            kwargs = vars(args)  # Namespace -> dict
            return run(**kwargs)\n
        \n
        if __name__ == "__main__":
            raise SystemExit(main())
        """
    )

    helpers_content = dedent(
        f"""\
        \"\"\"Helper functions for {name}.\"\"\"\n
        # TODO: add shared helpers here
        """
    )

    create_file(root / "config.py", config_content)
    create_file(root / "core.py", core_content)
    create_file(root / "cli.py", cli_content)
    create_file(root / "helpers.py", helpers_content)

    return root


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        prog="new_script",
        description="Generate a new script module (config/core/cli/helpers).",
    )
    parser.add_argument(
        "name",
        help="Name of the tool (will become the folder name).",
    )
    parser.add_argument(
        "-c",
        "--category",
        help="Optional category folder under scripts/ (e.g., sqlite, files, baws, devtools, experiments).",
    )

    args = parser.parse_args(argv)

    # Base scripts directory = this file's parent
    base_scripts_dir = Path(__file__).resolve().parent

    try:
        module_root = make_module_layout(base_scripts_dir, args.name, args.category)
    except FileExistsError as exc:
        print(f"ERROR: {exc}")
        return 1

    print(f"Created module at: {module_root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())