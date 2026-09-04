"""``westspace update`` - re-sync the workspace after a manifest change.

For now this is just ``west update`` (run directly for vanilla, through
``nrfutil toolchain-manager launch`` for NCS).
"""

import argparse

NAME = "update"
HELP = "Re-run west update for the current workspace"


def configure(parser: argparse.ArgumentParser) -> None:
    del parser  # no options yet


def run(args: argparse.Namespace) -> int:
    raise NotImplementedError(NAME)
