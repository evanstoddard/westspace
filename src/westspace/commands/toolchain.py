"""``westspace toolchain`` - install the toolchain without touching a workspace.

Installs ``nrfutil``, its plugins, and the NCS toolchain bundle for
``ncs.version``. Nothing else is read or written, so the config can be given as
a bare file (e.g. in a Docker build that only has ``westspace.yml``). Without a
file, the workspace's ``westspace.yml`` is used.

NCS only: the vanilla Zephyr SDK is installed by ``west sdk install``, which
needs a checked-out workspace, so vanilla installs it in ``westspace init``.
"""

import argparse
import logging
from pathlib import Path

from .. import config, nrfutil, workspace
from ..errors import ConfigError, UsageError

log = logging.getLogger("westspace")

NAME = "toolchain"
HELP = "Install the NCS toolchain only (no west init or update)"


def configure(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "config",
        metavar="CONFIG",
        nargs="?",
        type=Path,
        default=None,
        help="westspace.yml to read (default: the workspace's)",
    )


def run(args: argparse.Namespace) -> int:
    if args.config is not None:
        if args.workspace is not None:
            raise UsageError("give either CONFIG or -C/--workspace, not both")
        cfg = config.load(args.config)
    else:
        cfg = config.load(workspace.from_args(args).config_path)

    if not cfg.is_ncs:
        raise UsageError(
            f"{cfg.path}: 'toolchain' supports NCS configs only; "
            "vanilla installs the Zephyr SDK during 'westspace init'"
        )
    install(cfg)
    log.info("toolchain ready: NCS %s", cfg.ncs_version)
    return 0


def install(cfg: config.Config) -> str:
    """Install the NCS toolchain for *cfg*; return the ``nrfutil`` path."""
    if not cfg.ncs_version:
        raise ConfigError(f"{cfg.path}: ncs.version is required for NCS workspaces")
    nrf = nrfutil.ensure()
    nrfutil.ensure_plugins(nrf)
    nrfutil.toolchain_install(nrf, cfg.ncs_version)
    return nrf
