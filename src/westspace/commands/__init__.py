"""Subcommand modules.

Each module exposes a small, uniform interface consumed by :mod:`westspace.cli`:

    NAME: str                  the subcommand name as typed on the CLI
    HELP: str                  one-line description
    configure(parser)          add arguments to the subcommand's parser
    run(args) -> int | None    execute; return an exit code (``None`` means 0)

``ALL`` is ordered for display in ``--help``.
"""

from . import build, clean, create, flash, init, launch, list_, update

ALL = [create, init, update, build, flash, clean, launch, list_]

__all__ = ["ALL"]
