"""``westspace init`` - bring an existing workspace to a buildable state.

Vanilla:
    create ``.venv`` -> ``pip install west`` -> ``west init`` -> ``west update``
    -> ``west packages pip --install`` -> ``west sdk install``
NCS:
    ensure ``nrfutil`` + plugins -> ``toolchain-manager install`` -> then
    ``west init`` / ``west update`` run through ``nrfutil toolchain-manager
    launch``. ``west packages pip --install`` and ``west sdk install`` are
    skipped: the NCS toolchain bundle already provides both.

``west init`` is skipped when ``.west/`` already exists unless ``--force`` is
given (which removes it first); the remaining steps always run, so ``init`` is
safe to re-run.
"""

import argparse
import logging
import shutil
from pathlib import Path

from .. import config, hosttools, pyenv, west, workspace
from ..errors import ConfigError
from . import toolchain
from ._args import add_cache_argument, cache_dir

log = logging.getLogger("westspace")

NAME = "init"
HELP = "Initialize an existing workspace (dependencies, west init, west update)"


def configure(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--force",
        action="store_true",
        help="remove any existing .west/ and re-run 'west init'",
    )
    add_cache_argument(parser)


def run(args: argparse.Namespace) -> int:
    ws = workspace.from_args(args)
    cfg = config.load(ws.config_path)
    initialize(ws, cfg, force=args.force, cache=cache_dir(args))
    return 0


def initialize(
    ws: workspace.Workspace,
    cfg: config.Config,
    *,
    force: bool = False,
    cache: Path | None = None,
) -> None:
    """Run the full init sequence for *ws*. Also used by ``build`` for auto-init.

    *cache* is passed to ``west update`` as ``--path-cache``.
    """
    _check_manifest(ws, cfg)

    if cfg.is_ncs:
        runner = _provision_ncs(ws, cfg)
    else:
        runner = _provision_vanilla(ws, cfg)

    _west_init(runner, ws, cfg, force=force)
    runner.update(cache=cache)
    if not cfg.is_ncs:
        # NCS's toolchain bundle already ships every Zephyr/NCS Python
        # requirement, and its Python is not a venv, so `west packages pip
        # --install` both is unnecessary and fails ("outside of a virtual
        # environment") under `toolchain-manager launch`.
        toolchain.install_zephyr_sdk(ws, cfg)

    hosttools.check()
    log.info("workspace ready: %s", ws.root)


def _check_manifest(ws: workspace.Workspace, cfg: config.Config) -> None:
    manifest = ws.root / cfg.manifest_dir / cfg.manifest_file
    if not manifest.is_file():
        raise ConfigError(f"manifest not found: {manifest}")


def _provision_vanilla(ws: workspace.Workspace, cfg: config.Config) -> west.WestRunner:
    pyenv.ensure(ws.venv_dir)
    if not pyenv.executable(ws.venv_dir, "west").exists():
        pyenv.pip_install(ws.venv_dir, "west")
    return west.runner_for(cfg, ws)


def _provision_ncs(ws: workspace.Workspace, cfg: config.Config) -> west.WestRunner:
    nrf = toolchain.install(cfg)
    return west.runner_for(cfg, ws, nrfutil_path=nrf)


def _west_init(
    runner: west.WestRunner,
    ws: workspace.Workspace,
    cfg: config.Config,
    *,
    force: bool,
) -> None:
    if ws.west_dir.exists():
        if not force:
            log.info("%s already exists; skipping 'west init'", ws.west_dir)
            return
        log.warning("removing existing %s (--force)", ws.west_dir)
        shutil.rmtree(ws.west_dir)
    runner.init(cfg.manifest_dir, cfg.manifest_file)
