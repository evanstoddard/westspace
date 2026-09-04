"""Load and validate ``westspace.yml``.

The parsed document is kept as a plain ``dict`` on :class:`Config`; typed
accessors cover the handful of fields the commands need today. Validation uses
the bundled ``westspace.schema.json`` via :mod:`jsonschema` when it is installed,
and falls back to a couple of structural checks otherwise (jsonschema is not yet
a hard dependency).
"""

import json
from dataclasses import dataclass
from importlib import resources
from pathlib import Path
from typing import Any

import yaml

from .errors import ConfigError

SCHEMA_FILENAME = "westspace.schema.json"

DEFAULT_MANIFEST_DIR = "project"
DEFAULT_MANIFEST_FILE = "west.yml"
DEFAULT_NCS_MANIFEST_FILE = "west-ncs.yml"


@dataclass
class Config:
    """A parsed ``westspace.yml``."""

    path: Path
    data: dict[str, Any]

    # -- flavor ---------------------------------------------------------------
    @property
    def ncs(self) -> dict[str, Any]:
        return self.data.get("ncs") or {}

    @property
    def is_ncs(self) -> bool:
        return bool(self.ncs) and self.ncs.get("enabled", True)

    @property
    def ncs_version(self) -> str | None:
        return self.ncs.get("version")

    # -- manifest -----------------------------------------------------------
    @property
    def manifest_dir(self) -> str:
        return self.data.get("manifest_dir", DEFAULT_MANIFEST_DIR)

    @property
    def manifest_file(self) -> str:
        if self.is_ncs:
            return self.ncs.get("manifest_file", DEFAULT_NCS_MANIFEST_FILE)
        return self.data.get("manifest_file", DEFAULT_MANIFEST_FILE)

    # -- targets ----------------------------------------------------------
    @property
    def targets(self) -> dict[str, Any]:
        return self.data.get("targets") or {}

    @property
    def default_target(self) -> str | None:
        return self.data.get("default_target")

    def resolve_default_target(self) -> str | None:
        """Target used when none is named: the explicit ``default_target``, or the
        sole target when exactly one is defined."""
        if self.default_target:
            return self.default_target
        if len(self.targets) == 1:
            return next(iter(self.targets))
        return None


def default_config(target: dict[str, Any]) -> str | None:
    """Config used when a target is named without ``:config``: the target's
    ``default_config``, otherwise a config literally keyed ``default``."""
    explicit = target.get("default_config")
    if explicit:
        return explicit
    if "default" in (target.get("configs") or {}):
        return "default"
    return None


def load(path: Path) -> Config:
    """Parse and validate the config file at *path*."""
    try:
        raw = yaml.safe_load(path.read_text())
    except OSError as exc:
        raise ConfigError(f"{path}: {exc.strerror or exc}") from exc
    except yaml.YAMLError as exc:
        raise ConfigError(f"{path}: invalid YAML: {exc}") from exc

    if raw is None:
        raise ConfigError(f"{path}: file is empty")
    if not isinstance(raw, dict):
        raise ConfigError(f"{path}: top level must be a mapping")

    validate(raw, source=path)
    return Config(path=path, data=raw)


def validate(data: dict[str, Any], *, source: Path) -> None:
    """Validate *data* against the schema, raising :class:`ConfigError` on failure."""
    try:
        import jsonschema
    except ModuleNotFoundError:
        if not data.get("targets"):
            raise ConfigError(f"{source}: no targets defined") from None
        return

    try:
        jsonschema.validate(data, load_schema())
    except jsonschema.ValidationError as exc:
        location = "/".join(str(part) for part in exc.absolute_path) or "<root>"
        raise ConfigError(f"{source}: {location}: {exc.message}") from None


def load_schema() -> dict[str, Any]:
    """Return the JSON Schema document as a dict.

    Prefers a copy packaged alongside this module; falls back to the repo-root
    file when running from a source checkout.
    """
    packaged = resources.files(__package__).joinpath(SCHEMA_FILENAME)
    if packaged.is_file():
        return json.loads(packaged.read_text())

    for parent in Path(__file__).resolve().parents:
        candidate = parent / SCHEMA_FILENAME
        if candidate.is_file():
            return json.loads(candidate.read_text())

    raise ConfigError(f"could not locate {SCHEMA_FILENAME}")
