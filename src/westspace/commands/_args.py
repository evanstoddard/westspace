"""Argument helpers shared between subcommands."""

import argparse
import os
from pathlib import Path

from ..errors import UsageError

CACHE_ENV = "WESTSPACE_CACHE"


def add_cache_argument(parser: argparse.ArgumentParser) -> None:
    """Add ``--cache DIR`` (default ``$WESTSPACE_CACHE``) for ``west update``."""
    parser.add_argument(
        "--cache",
        metavar="DIR",
        type=Path,
        default=os.environ.get(CACHE_ENV) or None,
        help=(
            "clone west projects from DIR (e.g. made by 'westspace seed') via "
            f"'west update --path-cache'; default: ${CACHE_ENV}"
        ),
    )


def cache_dir(args: argparse.Namespace) -> Path | None:
    """The ``--cache`` directory, checked to exist; ``None`` when unset."""
    if args.cache is None:
        return None
    cache = Path(args.cache).resolve()
    if not cache.is_dir():
        raise UsageError(f"cache directory not found: {cache}")
    return cache


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
