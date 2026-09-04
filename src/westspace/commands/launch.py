"""``westspace launch`` - open a shell (or run a command) in the toolchain env.

Vanilla: a subshell with the workspace ``.venv`` and Zephyr environment active.
NCS: ``nrfutil toolchain-manager launch`` for the configured NCS version.
"""

import argparse

from ._args import add_passthrough_argument

NAME = "launch"
HELP = "Open a shell in the workspace toolchain environment"


def configure(parser: argparse.ArgumentParser) -> None:
    add_passthrough_argument(
        parser,
        metavar="-- COMMAND",
        help="command to run in the environment; if omitted, an interactive shell opens",
    )


def run(args: argparse.Namespace) -> int:
    raise NotImplementedError(NAME)
