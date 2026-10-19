"""Optional fixed location for installed tools: ``$WESTSPACE_TOOLS_DIR``.

Unset, tools go where they always have (under ``$HOME``). Set, everything
westspace installs lives under it, so a prebuilt image keeps working when
``$HOME`` or the user differs at run time (e.g. GitHub Actions container jobs):

    <dir>/bin/nrfutil     downloaded nrfutil
    <dir>/nrfutil/        NRFUTIL_HOME (plugins, config)
    <dir>/ncs/            NCS toolchain bundles
    <dir>/zephyr-sdk/     Zephyr SDKs, one zephyr-sdk-<version>/ each
"""

import os
from pathlib import Path

from .workspace import Workspace

ENV = "WESTSPACE_TOOLS_DIR"


def root() -> Path | None:
    value = os.environ.get(ENV)
    return Path(value).absolute() if value else None


def apply_env() -> None:
    """Point nrfutil at the tools dir (unless NRFUTIL_HOME is already set)."""
    base = root()
    if base is not None:
        os.environ.setdefault("NRFUTIL_HOME", str(base / "nrfutil"))


def ncs_install_dir() -> Path | None:
    base = root()
    return base / "ncs" if base is not None else None


def zephyr_sdk_base() -> Path | None:
    base = root()
    return base / "zephyr-sdk" if base is not None else None


def zephyr_sdk_dir(ws: Workspace) -> Path | None:
    """The installed SDK matching *ws*'s ``zephyr/SDK_VERSION``, if any.

    Zephyr finds the SDK through a CMake package registry under ``$HOME``;
    exporting this as ``ZEPHYR_SDK_INSTALL_DIR`` works without it.
    """
    base = zephyr_sdk_base()
    version_file = ws.zephyr_dir / "SDK_VERSION"
    if base is None or not version_file.is_file():
        return None
    sdk = base / f"zephyr-sdk-{version_file.read_text().strip()}"
    return sdk if sdk.is_dir() else None


def zephyr_sdk_env(ws: Workspace) -> dict[str, str] | None:
    """``os.environ`` plus ``ZEPHYR_SDK_INSTALL_DIR``, or ``None`` if not needed."""
    sdk = zephyr_sdk_dir(ws)
    if sdk is None:
        return None
    return {**os.environ, "ZEPHYR_SDK_INSTALL_DIR": str(sdk)}
