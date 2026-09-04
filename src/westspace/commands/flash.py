"""``westspace flash`` - flash a previously built target/config."""

import argparse
import logging

from .. import config, nrfutil, west, workspace
from ..errors import ToolNotFoundError, WestspaceError
from ._args import add_passthrough_argument, add_target_argument, clean_passthrough

log = logging.getLogger("westspace")

NAME = "flash"
HELP = "Flash a built target"


def configure(parser: argparse.ArgumentParser) -> None:
    add_target_argument(parser, action="flash")
    add_passthrough_argument(
        parser,
        metavar="-- FLASH_ARGS",
        help="arguments after -- are forwarded to west flash",
    )


def run(args: argparse.Namespace) -> int:
    ws = workspace.from_args(args)
    cfg = config.load(ws.config_path)
    resolved = config.resolve_target(cfg, args.target)

    if not ws.is_initialized:
        raise WestspaceError("workspace not initialized; run 'westspace init'")

    build_dir = ws.root / resolved.build_dir
    if not (build_dir / "CMakeCache.txt").is_file():
        raise WestspaceError(
            f"no build found at {resolved.build_dir}; "
            f"run 'westspace build {resolved.label}' first"
        )

    nrfutil_path = None
    if cfg.is_ncs:
        nrfutil_path = nrfutil.locate()
        if nrfutil_path is None:
            raise ToolNotFoundError("nrfutil not found; run 'westspace init' first")

    runner = west.runner_for(cfg, ws, nrfutil_path=nrfutil_path)
    log.info("flashing %s from %s", resolved.label, resolved.build_dir)
    runner.flash(resolved.build_dir, args=clean_passthrough(args.passthrough))
    return 0
