"""Manage the per-workspace Python virtualenv used for vanilla Zephyr.

The workspace ``.venv`` holds ``west`` and everything ``west packages pip``
installs from the manifest. NCS workspaces do not use this - their Python comes
from the nrfutil toolchain bundle.
"""

import logging
import venv
from pathlib import Path

from . import process

log = logging.getLogger("westspace")


def bin_dir(venv_path: Path) -> Path:
    # POSIX layout; Windows support (``Scripts``) is a later concern.
    return venv_path / "bin"


def python(venv_path: Path) -> Path:
    return bin_dir(venv_path) / "python"


def executable(venv_path: Path, name: str) -> Path:
    return bin_dir(venv_path) / name


def ensure(venv_path: Path) -> None:
    """Create *venv_path* with pip if it does not already exist."""
    if python(venv_path).exists():
        log.debug("virtualenv already present: %s", venv_path)
        return
    log.info("creating virtualenv: %s", venv_path)
    venv.EnvBuilder(with_pip=True).create(venv_path)


def pip_install(venv_path: Path, *packages: str) -> None:
    if not packages:
        return
    process.run([python(venv_path), "-m", "pip", "install", "--upgrade", *packages])
