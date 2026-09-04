"""``westspace launch`` - open a shell (or run a command) in the toolchain env.

Vanilla: a subprocess with the workspace ``.venv`` on ``PATH``, ``VIRTUAL_ENV``
and ``ZEPHYR_BASE`` set. NCS: ``nrfutil toolchain-manager launch`` for the
configured NCS version (``--shell`` when no command is given).
"""

import argparse
import logging
import os
import shutil
import subprocess

from .. import config, nrfutil, workspace
from ..errors import ToolNotFoundError, WestspaceError
from ._args import add_passthrough_argument, clean_passthrough

log = logging.getLogger("westspace")

NAME = "launch"
HELP = "Open a shell in the workspace toolchain environment"


def configure(parser: argparse.ArgumentParser) -> None:
    add_passthrough_argument(
        parser,
        metavar="-- COMMAND",
        help="command to run in the environment; if omitted, an interactive shell opens",
    )


def run(args: argparse.Namespace) -> int:
    ws = workspace.from_args(args)
    cfg = config.load(ws.config_path)
    command = clean_passthrough(args.passthrough)

    if cfg.is_ncs:
        argv = _ncs_argv(cfg, ws, command)
        env = None
    else:
        _require_venv(ws)
        argv = command or [_shell()]
        env = _vanilla_env(ws)

    log.info("launch: %s", " ".join(argv))
    return subprocess.run(argv, cwd=ws.root, env=env).returncode


def _shell() -> str:
    return os.environ.get("SHELL") or shutil.which("bash") or "/bin/sh"


def _require_venv(ws: workspace.Workspace) -> None:
    if not (ws.venv_dir / "bin").is_dir():
        raise WestspaceError("workspace has no .venv; run 'westspace init' first")


def _vanilla_env(ws: workspace.Workspace) -> dict:
    env = dict(os.environ)
    env["PATH"] = f"{ws.venv_dir / 'bin'}{os.pathsep}{env.get('PATH', '')}"
    env["VIRTUAL_ENV"] = str(ws.venv_dir)
    env.pop("PYTHONHOME", None)
    if ws.zephyr_dir.is_dir():
        env["ZEPHYR_BASE"] = str(ws.zephyr_dir)
    env["WESTSPACE_LAUNCH"] = "1"
    return env


def _ncs_argv(
    cfg: config.Config, ws: workspace.Workspace, command: list[str]
) -> list[str]:
    if not cfg.ncs_version:
        raise WestspaceError(f"{cfg.path}: ncs.version is required for NCS workspaces")
    nrf = nrfutil.locate()
    if nrf is None:
        raise ToolNotFoundError("nrfutil not found; run 'westspace init' first")

    argv = [
        nrf, "toolchain-manager", "launch",
        "--ncs-version", cfg.ncs_version,
        "--chdir", str(ws.root),
    ]
    if command:
        argv += ["--", *command]
    else:
        argv.append("--shell")
    return argv
