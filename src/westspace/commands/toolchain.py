"""``westspace toolchain`` - install the toolchain without west init or update.

NCS: installs ``nrfutil``, its plugins, and the toolchain bundle for
``ncs.version``. Nothing else is read or written, so the config can be given as
a bare file (e.g. in a Docker build that only has ``westspace.yml``).

Vanilla: runs ``west packages pip --install`` and ``west sdk install`` in an
existing workspace, since the SDK version comes from the checked-out
``zephyr/``. A directory made by ``westspace seed`` works, so an image can seed
first and then install the SDK from the seed.

Without a file, the workspace's ``westspace.yml`` is used.
"""

import argparse
import logging
from pathlib import Path

from .. import config, nrfutil, pyenv, toolsdir, west, workspace
from ..errors import ConfigError, UsageError

log = logging.getLogger("westspace")

NAME = "toolchain"
HELP = "Install the toolchain only (no west init or update)"


def configure(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "config",
        metavar="CONFIG",
        nargs="?",
        type=Path,
        default=None,
        help="westspace.yml to read (default: the workspace's; NCS only)",
    )


def run(args: argparse.Namespace) -> int:
    ws = None
    if args.config is not None:
        if args.workspace is not None:
            raise UsageError("give either CONFIG or -C/--workspace, not both")
        cfg = config.load(args.config)
    else:
        ws = workspace.from_args(args)
        cfg = config.load(ws.config_path)

    if cfg.is_ncs:
        install(cfg)
        log.info("toolchain ready: NCS %s", cfg.ncs_version)
        return 0

    if ws is None or not ws.zephyr_dir.is_dir():
        raise UsageError(
            f"{cfg.path}: vanilla reads the SDK version from zephyr/, so it needs "
            "a checked-out workspace; run 'westspace seed DIR' and then "
            "'westspace -C DIR toolchain'"
        )
    install_zephyr_sdk(ws, cfg)
    log.info("toolchain ready: Zephyr SDK for %s", ws.root)
    return 0


def install(cfg: config.Config) -> str:
    """Install the NCS toolchain for *cfg*; return the ``nrfutil`` path."""
    if not cfg.ncs_version:
        raise ConfigError(f"{cfg.path}: ncs.version is required for NCS workspaces")
    nrf = nrfutil.ensure()
    nrfutil.ensure_plugins(nrf)
    nrfutil.toolchain_install(nrf, cfg.ncs_version)
    return nrf


def install_zephyr_sdk(ws: workspace.Workspace, cfg: config.Config) -> None:
    """Install Zephyr's Python requirements and SDK for vanilla workspace *ws*."""
    if not pyenv.executable(ws.venv_dir, "west").exists():
        raise UsageError(f"{ws.root} has no .venv with west; run 'westspace init' first")
    runner = west.runner_for(cfg, ws)
    runner.packages_pip_install()
    runner.sdk_install(cfg.toolchains, install_base=toolsdir.zephyr_sdk_base())
