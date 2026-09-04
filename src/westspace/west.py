"""Invoke ``west`` for a workspace.

Two flavors share one interface:

* vanilla - run the ``west`` from the workspace ``.venv`` directly;
* NCS - run ``west`` inside ``nrfutil toolchain-manager launch``.

:func:`runner_for` only *constructs* the runner; making sure the venv or the
nrfutil toolchain actually exists is the caller's job (see ``commands/init``).
"""

import logging
from collections.abc import Sequence
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

    def build(
        self,
        source: str,
        *,
        board: str,
        build_dir: str,
        sysbuild: bool = False,
        pristine: str | None = None,
        snippets: Sequence[str] = (),
        overlays: Sequence[str] = (),
        conf: Sequence[str] = (),
        cmake_args: Sequence[str] = (),
        west_args: Sequence[str] = (),
        extra: Sequence[str] = (),
    ) -> None:
        argv = ["build", "-b", board, "-d", build_dir]
        if sysbuild:
            argv.append("--sysbuild")
        if pristine:
            argv += ["-p", pristine]
        for snippet in snippets:
            argv += ["-S", snippet]
        argv += list(west_args)
        argv.append(source)

        cmake: list[str] = []
        if overlays:
            cmake.append("-DEXTRA_DTC_OVERLAY_FILE=" + ";".join(overlays))
        if conf:
            cmake.append("-DEXTRA_CONF_FILE=" + ";".join(conf))
        cmake += list(cmake_args)
        cmake += list(extra)
        if cmake:
            argv += ["--", *cmake]

        self.run(*argv)

    def flash(self, build_dir: str, *, args: Sequence[str] = ()) -> None:
        self.run("flash", "-d", build_dir, *args)


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
