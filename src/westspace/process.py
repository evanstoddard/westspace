"""Thin wrapper around :mod:`subprocess` with logging and uniform errors."""

import logging
import subprocess
from pathlib import Path

from .errors import CommandError

log = logging.getLogger("westspace")


def run(
    argv: list,
    *,
    cwd: Path | str | None = None,
    env: dict | None = None,
    check: bool = True,
    capture: bool = False,
) -> subprocess.CompletedProcess:
    """Run *argv*.

    Output goes straight to the terminal unless ``capture`` is set. A non-zero
    exit raises :class:`CommandError` when ``check`` is true; a missing
    executable always does.
    """
    argv = [str(a) for a in argv]
    printable = " ".join(argv)
    log.info("$ %s", printable)

    try:
        proc = subprocess.run(
            argv,
            cwd=str(cwd) if cwd is not None else None,
            env=env,
            text=True,
            capture_output=capture,
        )
    except FileNotFoundError as exc:
        raise CommandError(f"{argv[0]}: command not found") from exc

    if check and proc.returncode != 0:
        detail = ""
        if capture and proc.stderr:
            detail = "\n" + proc.stderr.strip()
        raise CommandError(f"command failed (exit {proc.returncode}): {printable}{detail}")

    return proc
