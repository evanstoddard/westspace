"""``westspace clean`` - remove build output, or the whole initialized tree."""

import argparse

from ._args import add_target_argument

NAME = "clean"
HELP = "Remove build directories (with --all, also the initialized workspace tree)"


def configure(parser: argparse.ArgumentParser) -> None:
    add_target_argument(parser, action="clean")
    parser.add_argument(
        "--all",
        action="store_true",
        help="also remove .west/, modules/, zephyr/ and the workspace venv",
    )
    parser.add_argument(
        "--yes",
        action="store_true",
        help="do not prompt for confirmation",
    )


def run(args: argparse.Namespace) -> int:
    raise NotImplementedError(NAME)
