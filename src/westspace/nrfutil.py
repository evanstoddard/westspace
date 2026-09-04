"""Locate, download, and drive ``nrfutil`` for NCS workspaces.

If ``nrfutil`` is already on PATH it is used as-is. Otherwise the latest binary
for the host platform is downloaded once into a westspace-owned directory (via
:mod:`platformdirs`) and reused from there. The toolchain *bundles* installed by
``nrfutil toolchain-manager`` stay in nrfutil's own default location.
"""

import logging
import platform
import shutil
import stat
import urllib.request
from pathlib import Path

import platformdirs

from . import process
from .errors import ToolNotFoundError

log = logging.getLogger("westspace")

REQUIRED_PLUGINS = ("device", "sdk-manager", "toolchain-manager")

_DOWNLOAD_BASE = (
    "https://files.nordicsemi.com/artifactory/swtools/external/nrfutil/executables"
)

# (system, machine) -> Nordic platform slug
_PLATFORMS = {
    ("linux", "x86_64"): "x86_64-unknown-linux-gnu",
    ("linux", "aarch64"): "aarch64-unknown-linux-gnu",
    ("darwin", "x86_64"): "x86_64-apple-darwin",
    ("darwin", "arm64"): "aarch64-apple-darwin",
    ("windows", "amd64"): "x86_64-pc-windows-msvc",
}


def _binary_name() -> str:
    return "nrfutil.exe" if platform.system().lower() == "windows" else "nrfutil"


def _store_dir() -> Path:
    return Path(platformdirs.user_data_dir("westspace")) / "bin"


def _downloaded_binary() -> Path:
    return _store_dir() / _binary_name()


def locate() -> str | None:
    """Return a usable ``nrfutil`` path (PATH first, then a prior download)."""
    found = shutil.which("nrfutil")
    if found:
        return found
    cached = _downloaded_binary()
    return str(cached) if cached.exists() else None


def ensure() -> str:
    """Return a usable ``nrfutil`` path, downloading it if necessary."""
    existing = locate()
    if existing:
        log.debug("using nrfutil: %s", existing)
        return existing
    return _download()


def _download() -> str:
    key = (platform.system().lower(), platform.machine().lower())
    slug = _PLATFORMS.get(key)
    if slug is None:
        raise ToolNotFoundError(
            f"nrfutil not on PATH and no prebuilt binary known for {key}; "
            "install it manually from https://www.nordicsemi.com/Products/Development-tools/nRF-Util"
        )

    url = f"{_DOWNLOAD_BASE}/{slug}/nrfutil"
    dest = _downloaded_binary()
    dest.parent.mkdir(parents=True, exist_ok=True)
    log.info("downloading nrfutil: %s", url)
    try:
        with urllib.request.urlopen(url) as response, open(dest, "wb") as out:
            shutil.copyfileobj(response, out)
    except OSError as exc:
        raise ToolNotFoundError(f"failed to download nrfutil from {url}: {exc}") from exc

    dest.chmod(dest.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    log.info("installed nrfutil: %s", dest)
    return str(dest)


def ensure_plugins(nrfutil: str) -> None:
    """Install any missing nrfutil plugins westspace relies on.

    ``nrfutil install`` is a no-op for an already-installed plugin, so this just
    runs it for each rather than probing first.
    """
    for plugin in REQUIRED_PLUGINS:
        log.info("ensuring nrfutil plugin: %s", plugin)
        process.run([nrfutil, "install", plugin])


def toolchain_install(nrfutil: str, ncs_version: str) -> None:
    process.run(
        [nrfutil, "toolchain-manager", "install", "--ncs-version", ncs_version]
    )


def launch_prefix(nrfutil: str, ncs_version: str) -> list[str]:
    """The argv prefix that runs a command inside the NCS toolchain env."""
    return [
        nrfutil,
        "toolchain-manager",
        "launch",
        "--ncs-version",
        ncs_version,
        "--",
    ]
