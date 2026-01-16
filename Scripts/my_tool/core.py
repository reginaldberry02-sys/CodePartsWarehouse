"""Core logic for my_tool."""

from .config import TOOL_NAME


def run(**kwargs) -> int:
    """Main core function for my_tool. Return an int exit code."""
    # TODO: implement core behavior for this tool
    print(f"Running {TOOL_NAME} with args: {kwargs}")
    return 0