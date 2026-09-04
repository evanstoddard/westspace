"""westspace - a utility for managing Zephyr project workspaces."""

from .cli import run

__all__ = ["main", "run"]


def main() -> None:
    """Console-script entry point (see ``[project.scripts]`` in pyproject.toml)."""
    raise SystemExit(run())
