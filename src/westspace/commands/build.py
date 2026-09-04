"""``westspace build`` - build a target/config from ``westspace.yml``."""

import argparse

from ._args import add_passthrough_argument, add_target_argument

NAME = "build"
HELP = "Build a target"


def configure(parser: argparse.ArgumentParser) -> None:
    add_target_argument(parser, action="build")
    parser.add_argument(
        "--pristine",
        nargs="?",
        choices=("always", "auto", "never"),
        const="auto",
        default=None,
        metavar="{always,auto,never}",
        help="pass -p/--pristine to west build (value defaults to 'auto' when bare)",
    )
    parser.add_argument(
        "--board",
        metavar="BOARD",
        default=None,
        help="override the board resolved from westspace.yml",
    )
    parser.add_argument(
        "--no-auto-init",
        dest="auto_init",
        action="store_false",
        help="do not run init automatically when the workspace is uninitialized",
    )
    add_passthrough_argument(
        parser,
        metavar="-- CMAKE_ARGS",
        help="arguments after -- are forwarded to CMake",
    )


def run(args: argparse.Namespace) -> int:
    raise NotImplementedError(NAME)
