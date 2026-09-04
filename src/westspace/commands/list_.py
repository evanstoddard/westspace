"""``westspace list`` - show configured targets and configs."""

import argparse

NAME = "list"
HELP = "List targets and configs defined in westspace.yml"


def configure(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--json",
        action="store_true",
        help="emit machine-readable JSON",
    )


def run(args: argparse.Namespace) -> int:
    raise NotImplementedError(NAME)
