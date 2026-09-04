"""``westspace build`` - build a target/config from ``westspace.yml``."""

import argparse
import logging

from .. import config, nrfutil, west, workspace
from ..errors import ToolNotFoundError, WestspaceError
from . import init as init_cmd
from ._args import add_passthrough_argument, add_target_argument, clean_passthrough

log = logging.getLogger("westspace")

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
    ws = workspace.from_args(args)
    cfg = config.load(ws.config_path)
    resolved = config.resolve_target(cfg, args.target)

    if not ws.is_initialized:
        if not args.auto_init:
            raise WestspaceError("workspace not initialized; run 'westspace init'")
        log.info("workspace not initialized; running init first")
        init_cmd.initialize(ws, cfg)

    nrfutil_path = None
    if cfg.is_ncs:
        nrfutil_path = nrfutil.locate()
        if nrfutil_path is None:
            raise ToolNotFoundError("nrfutil not found; run 'westspace init' first")

    runner = west.runner_for(cfg, ws, nrfutil_path=nrfutil_path)

    source = ws.root / resolved.source
    overlays = [str(source / path) for path in resolved.overlays]
    conf = [str(source / path) for path in resolved.conf]

    log.info("building %s (board %s) -> %s", resolved.label, resolved.board, resolved.build_dir)
    runner.build(
        str(source),
        board=args.board or resolved.board,
        build_dir=resolved.build_dir,
        sysbuild=resolved.sysbuild,
        pristine=args.pristine,
        snippets=resolved.snippets,
        overlays=overlays,
        conf=conf,
        cmake_args=resolved.cmake_args,
        west_args=resolved.west_args,
        extra=clean_passthrough(args.passthrough),
    )
    return 0
