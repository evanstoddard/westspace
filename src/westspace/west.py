"""Invoke ``west`` for a workspace.

Two flavors share one interface:

* vanilla - run the ``west`` from the workspace ``.venv`` directly;
* NCS - run ``west`` inside ``nrfutil toolchain-manager launch``.

:func:`runner_for` only *constructs* the runner; making sure the venv or the
nrfutil toolchain actually exists is the caller's job (see ``commands/init``).
"""

import logging
from dataclasses import dataclass, field
from pathlib import Path

from . import nrfutil, process, pyenv
from .config import Config
from .errors import ConfigError
from .workspace import Workspace

log = logging.getLogger("westspace")

# Mirrors the template's historical `west update -f smart -n -o=--depth=1`.
UPDATE_ARGS: tuple[str, ...] = ("-f", "smart", "-n", "-o=--depth=1")


@dataclass
class WestRunner:
    root: Path
    argv_prefix: list[str] = field(default_factory=list)

    def run(self, *args, **kwargs) -> object:
        return process.run([*self.argv_prefix, *args], cwd=self.root, **kwargs)

    def init(self, manifest_dir: str, manifest_file: str) -> None:
        self.run("init", "-l", "--mf", manifest_file, manifest_dir)

    def update(self, *extra: str) -> None:
        self.run("update", *(extra or UPDATE_ARGS))

    def packages_pip_install(self) -> None:
        self.run("packages", "pip", "--install")

    def sdk_install(self, toolchains: list[str] | None = None) -> None:
        """Install the Zephyr SDK.

        ``toolchains`` None -> all GNU toolchains; a non-empty list -> just those
        (``-t``); an empty list -> none (``-T``).
        """
        if toolchains is None:
            self.run("sdk", "install")
        elif toolchains:
            self.run("sdk", "install", "-t", *toolchains)
        else:
            self.run("sdk", "install", "-T")


def runner_for(cfg: Config, ws: Workspace, *, nrfutil_path: str | None = None) -> WestRunner:
    if cfg.is_ncs:
        if not cfg.ncs_version:
            raise ConfigError(f"{cfg.path}: ncs.version is required for NCS workspaces")
        prefix = [
            *nrfutil.launch_prefix(nrfutil_path or "nrfutil", cfg.ncs_version),
            "west",
        ]
        return WestRunner(root=ws.root, argv_prefix=prefix)

    return WestRunner(
        root=ws.root,
        argv_prefix=[str(pyenv.executable(ws.venv_dir, "west"))],
    )
