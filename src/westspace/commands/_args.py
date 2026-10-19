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
    """Accept trailing ``-- ...`` arguments as ``args.passthrough``.

    The CLI splits argv at the first ``--`` before parsing (see
    :func:`westspace.cli.run`), so options may appear anywhere before it. This
    only sets the default and documents the arguments in ``--help``.
    """
    parser.set_defaults(passthrough=[])
    parser.add_argument_group("passthrough", f"{metavar}: {help}")
