"""CLI entrypoint for my_tool."""

import argparse
from .config import TOOL_NAME
from .core import run


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        prog=TOOL_NAME,
        description="Command-line interface for my_tool.",
    )
    # TODO: add CLI arguments here as needed
    return parser.parse_args(argv)


def main(argv=None) -> int:
    args = parse_args(argv)
    kwargs = vars(args)  # Namespace -> dict
    return run(**kwargs)


if __name__ == "__main__":
    raise SystemExit(main())