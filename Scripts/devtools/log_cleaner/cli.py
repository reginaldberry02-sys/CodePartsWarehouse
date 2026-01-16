"""CLI entrypoint for log_cleaner."""

import argparse
from .config import TOOL_NAME
from .core import run



def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        prog=TOOL_NAME,
        description="Command-line interface for log_cleaner.",
    )
    # TODO: add specific CLI arguments here
    return parser.parse_args(argv)



def main(argv=None) -> int:
    args = parse_args(argv)
    kwargs = vars(args)  # Namespace -> dict
    return run(**kwargs)



if __name__ == "__main__":
    raise SystemExit(main())
