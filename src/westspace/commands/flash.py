"""``westspace flash`` - flash a previously built target/config."""

import argparse

from ._args import add_passthrough_argument, add_target_argument

NAME = "flash"
HELP = "Flash a built target"


def configure(parser: argparse.ArgumentParser) -> None:
    add_target_argument(parser, action="flash")
    add_passthrough_argument(
        parser,
        metavar="-- RUNNER_ARGS",
        help="arguments after -- are forwarded to west flash",
    )


def run(args: argparse.Namespace) -> int:
    raise NotImplementedError(NAME)
