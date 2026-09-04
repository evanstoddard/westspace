"""Locate and describe a westspace workspace on disk.

A *workspace* is the directory tree rooted at the one containing ``westspace.yml``
(the same directory that will hold ``.west/`` after ``westspace init``).
"""

from dataclasses import dataclass
from pathlib import Path

from .errors import WorkspaceNotFoundError

CONFIG_NAMES = ("westspace.yml", "westspace.yaml")


@dataclass(frozen=True)
class Workspace:
    """Resolved paths for a single workspace."""

    root: Path
    config_path: Path

    @property
    def west_dir(self) -> Path:
        return self.root / ".west"

    @property
    def venv_dir(self) -> Path:
        return self.root / ".venv"

    @property
    def zephyr_dir(self) -> Path:
        return self.root / "zephyr"

    @property
    def modules_dir(self) -> Path:
        return self.root / "modules"

    @property
    def is_initialized(self) -> bool:
        return self.west_dir.is_dir()


def find(start: Path | None = None, *, search_parents: bool = True) -> Workspace:
    """Return the :class:`Workspace` for *start* (default: the current directory).

    With ``search_parents`` (the default) the search walks upward until a config
    file is found; otherwise only *start* itself is checked.
    """
    base = (start or Path.cwd()).resolve()
    candidates = (base, *base.parents) if search_parents else (base,)
    for directory in candidates:
        for name in CONFIG_NAMES:
            config_path = directory / name
            if config_path.is_file():
                return Workspace(root=directory, config_path=config_path)

    where = f"{base} or any parent directory" if search_parents else str(base)
    raise WorkspaceNotFoundError(f"no {CONFIG_NAMES[0]} found in {where}")


def from_args(args) -> Workspace:
    """Resolve the workspace honoring a global ``--workspace/-C`` override."""
    override = getattr(args, "workspace", None)
    if override is not None:
        return find(Path(override), search_parents=False)
    return find()
