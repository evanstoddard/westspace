"""``westspace update`` - re-sync the workspace after a manifest change.

Runs ``west update`` only (directly for vanilla, through ``nrfutil
toolchain-manager launch`` for NCS). It does not re-run ``west init``,
``west packages pip --install``, or any toolchain install - use ``westspace
init`` for those.

If ``westspace.yml`` now selects a different manifest than the one recorded in
``.west/config`` (e.g. NCS was toggled on or off), update refuses and points at
``westspace init --force``.
"""

import argparse
import logging

from .. import config, nrfutil, west, workspace
from ..errors import ToolNotFoundError, WestspaceError

log = logging.getLogger("westspace")

NAME = "update"
HELP = "Re-run west update for the current workspace"


def configure(parser: argparse.ArgumentParser) -> None:
    del parser  # no options yet


def run(args: argparse.Namespace) -> int:
    ws = workspace.from_args(args)
    cfg = config.load(ws.config_path)

    if not ws.is_initialized:
        raise WestspaceError("workspace not initialized; run 'westspace init' first")

    on_disk = ws.initialized_manifest()
    if on_disk is not None and on_disk[1] != cfg.manifest_file:
        raise WestspaceError(
            f"workspace was initialized with manifest '{on_disk[1]}', but "
            f"westspace.yml now expects '{cfg.manifest_file}'; "
            f"run 'westspace init --force'"
        )

    nrfutil_path = None
    if cfg.is_ncs:
        nrfutil_path = nrfutil.locate()
        if nrfutil_path is None:
            raise ToolNotFoundError("nrfutil not found; run 'westspace init' first")

    runner = west.runner_for(cfg, ws, nrfutil_path=nrfutil_path)
    runner.update()
    log.info("workspace updated: %s", ws.root)
    return 0
