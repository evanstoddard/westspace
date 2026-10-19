"""Command-line entry point: argument parsing and dispatch."""

import argparse
import logging
import sys
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

from . import commands, toolsdir
from .errors import WestspaceError

PROG = "westspace"
log = logging.getLogger(PROG)


def _package_version() -> str:
    try:
        return version("westspace")
    except PackageNotFoundError:
        return "0+unknown"


def _configure_logging(verbosity: int) -> None:
    if verbosity >= 2:
        level = logging.DEBUG
    elif verbosity == 1:
        level = logging.INFO
    else:
        level = logging.WARNING
    logging.basicConfig(level=level, format="%(message)s")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog=PROG,
        description="Manage Zephyr west workspaces (vanilla or nRF Connect SDK).",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {_package_version()}",
    )
    parser.add_argument(
        "-C",
        "--workspace",
        metavar="PATH",
        type=Path,
        default=None,
        help="workspace directory (default: search upward from CWD for westspace.yml)",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="count",
        default=0,
        help="increase verbosity (repeatable)",
    )

    sub = parser.add_subparsers(dest="command", metavar="<command>", required=True)
    for module in commands.ALL:
        cmd = sub.add_parser(module.NAME, help=module.HELP, description=module.HELP)
        module.configure(cmd)
        cmd.set_defaults(_run=module.run)
    return parser


def _split_passthrough(argv: list[str]) -> tuple[list[str], list[str] | None]:
    """Split *argv* at the first ``--``; the tail is ``None`` when there is none."""
    if "--" not in argv:
        return argv, None
    index = argv.index("--")
    return argv[:index], argv[index + 1 :]


def run(argv: list[str] | None = None) -> int:
    """Parse *argv* (default ``sys.argv``) and dispatch. Returns a process exit code."""
    parser = build_parser()
    argv, passthrough = _split_passthrough(sys.argv[1:] if argv is None else list(argv))
    args = parser.parse_args(argv)
    if passthrough is not None:
        if not hasattr(args, "passthrough"):
            parser.error(f"'{args.command}' does not take arguments after '--'")
        args.passthrough = passthrough
    _configure_logging(args.verbose)
    toolsdir.apply_env()

    try:
        return args._run(args) or 0
    except NotImplementedError as exc:
        print(f"{PROG}: '{exc}' is not implemented yet", file=sys.stderr)
        return 2
    except WestspaceError as exc:
        print(f"{PROG}: error: {exc}", file=sys.stderr)
        return exc.exit_code
    except KeyboardInterrupt:
        print(f"{PROG}: interrupted", file=sys.stderr)
        return 130
