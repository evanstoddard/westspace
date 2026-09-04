"""``westspace init`` - initialize an existing workspace.

Vanilla: create ``.venv``, install west, ``west init`` -> ``west update`` ->
``west packages pip --install`` -> ``west sdk install``.
NCS: ensure ``nrfutil`` + plugins, ``toolchain-manager install``, then run
``west init`` / ``west update`` through ``nrfutil toolchain-manager launch``.
"""

import argparse

NAME = "init"
HELP = "Initialize an existing workspace (dependencies, west init, west update)"


def configure(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--force",
        action="store_true",
        help="re-run initialization even if the workspace is already initialized",
    )


def run(args: argparse.Namespace) -> int:
    raise NotImplementedError(NAME)
