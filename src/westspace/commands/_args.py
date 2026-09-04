"""Argument helpers shared between subcommands."""

import argparse


def add_target_argument(parser: argparse.ArgumentParser, *, action: str) -> None:
    """Add the optional ``TARGET[:CONFIG]`` positional used by build/flash/clean."""
    parser.add_argument(
        "target",
        nargs="?",
        metavar="TARGET[:CONFIG]",
        help=(
            f"target (and optional config) to {action}; "
            "defaults to default_target and the target's default_config"
        ),
    )


def add_passthrough_argument(
    parser: argparse.ArgumentParser, *, metavar: str, help: str
) -> None:
    """Add a trailing ``-- ...`` passthrough positional (everything after ``--``)."""
    parser.add_argument(
        "passthrough",
        nargs=argparse.REMAINDER,
        metavar=metavar,
        help=help,
    )


def clean_passthrough(values: list[str] | None) -> list[str]:
    """Drop a leading ``--`` left in place by ``argparse.REMAINDER``."""
    values = list(values or [])
    if values and values[0] == "--":
        values = values[1:]
    return values
