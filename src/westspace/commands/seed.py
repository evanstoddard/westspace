"""``westspace seed`` - populate a directory to serve as a west project cache.

Copies only ``westspace.yml`` and the manifest file into DIR, then runs
``west init`` and ``west update`` there. The result is laid out like any
workspace, so it works as ``west update --path-cache DIR``: clones come from
DIR, and only revisions missing from it are fetched. In a Docker build, the
source workspace can be a directory holding just those two files.

Re-running refreshes DIR (``west init`` is skipped once ``.west/`` exists).
The toolchain must already be installed (``westspace toolchain`` for NCS).
Manifests that import other files from their own repository are not supported:
only the manifest file itself is copied.
"""

import argparse
import logging
import shutil
from pathlib import Path

from .. import config, nrfutil, pyenv, west, workspace
from ..errors import ConfigError, ToolNotFoundError, UsageError, WestspaceError

log = logging.getLogger("westspace")

NAME = "seed"
HELP = "Populate a directory with the manifest's projects, for use as a west cache"


def configure(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "dest",
        metavar="DIR",
        type=Path,
        help="directory to seed; created if missing, refreshed if seeded before",
    )


def run(args: argparse.Namespace) -> int:
    src = workspace.from_args(args)
    cfg = config.load(src.config_path)

    manifest = src.root / cfg.manifest_dir / cfg.manifest_file
    if not manifest.is_file():
        raise ConfigError(f"manifest not found: {manifest}")

    dest = args.dest.resolve()
    if dest == src.root:
        raise UsageError("DIR must not be the workspace itself")
    seeded = workspace.Workspace(root=dest, config_path=dest / src.config_path.name)
    if dest.exists() and any(dest.iterdir()) and not seeded.is_initialized:
        raise WestspaceError(f"{dest} is not empty and was not seeded before")

    (dest / cfg.manifest_dir).mkdir(parents=True, exist_ok=True)
    shutil.copy2(src.config_path, seeded.config_path)
    shutil.copy2(manifest, dest / cfg.manifest_dir / cfg.manifest_file)

    runner = _runner(seeded, cfg)
    if not seeded.is_initialized:
        runner.init(cfg.manifest_dir, cfg.manifest_file)
    runner.update()
    log.info("seeded: %s", dest)
    return 0


def _runner(seeded: workspace.Workspace, cfg: config.Config) -> west.WestRunner:
    if cfg.is_ncs:
        nrfutil_path = nrfutil.locate()
        if nrfutil_path is None:
            raise ToolNotFoundError("nrfutil not found; run 'westspace toolchain' first")
        return west.runner_for(cfg, seeded, nrfutil_path=nrfutil_path)

    pyenv.ensure(seeded.venv_dir)
    if not pyenv.executable(seeded.venv_dir, "west").exists():
        pyenv.pip_install(seeded.venv_dir, "west")
    return west.runner_for(cfg, seeded)
