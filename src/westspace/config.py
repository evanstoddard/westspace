"""Load and validate ``westspace.yml``.

The parsed document is kept as a plain ``dict`` on :class:`Config`; typed
accessors cover the handful of fields the commands need today. Validation is
done against the bundled ``westspace.schema.json`` with :mod:`jsonschema`.
"""

import json
from dataclasses import dataclass
from importlib import resources
from pathlib import Path
from typing import Any

import jsonschema
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

    @property
    def toolchains(self) -> list[str] | None:
        """Zephyr SDK GNU toolchains for ``west sdk install`` (vanilla only).

        ``None`` (key absent) means install everything; ``[]`` means install none.
        """
        return self.data.get("toolchains")

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


@dataclass
class ResolvedTarget:
    """A concrete ``target:config`` pair with its build settings merged in."""

    name: str
    config_name: str
    board: str
    source: str
    sysbuild: bool
    build_dir: str
    overlays: list[str]
    conf: list[str]
    snippets: list[str]
    cmake_args: list[str]
    west_args: list[str]

    @property
    def label(self) -> str:
        return f"{self.name}:{self.config_name}"


def resolve_target(cfg: "Config", spec: str | None) -> ResolvedTarget:
    """Resolve a ``TARGET[:CONFIG]`` string (or ``None``) against *cfg*."""
    targets = cfg.targets
    if not targets:
        raise ConfigError(f"{cfg.path}: no targets defined")

    target_name, _, config_name = (spec or "").partition(":")
    target_name = target_name or cfg.resolve_default_target()
    if not target_name:
        raise ConfigError(
            f"{cfg.path}: no default_target set; name a target explicitly "
            f"(one of: {', '.join(targets)})"
        )
    if target_name not in targets:
        raise ConfigError(
            f"{cfg.path}: unknown target '{target_name}' (known: {', '.join(targets)})"
        )
    target = targets[target_name]
    configs = target.get("configs") or {}

    config_name = config_name or default_config(target)
    if not config_name:
        raise ConfigError(
            f"{cfg.path}: target '{target_name}' has no default_config; "
            f"use TARGET:CONFIG (one of: {', '.join(configs)})"
        )
    if config_name not in configs:
        raise ConfigError(
            f"{cfg.path}: target '{target_name}' has no config '{config_name}' "
            f"(known: {', '.join(configs)})"
        )
    conf_data = configs[config_name] or {}

    return ResolvedTarget(
        name=target_name,
        config_name=config_name,
        board=target["board"],
        source=target["source"],
        sysbuild=bool(target.get("sysbuild", False)),
        build_dir=conf_data.get("build_dir") or f"build/{target_name}-{config_name}",
        overlays=list(conf_data.get("overlays") or []),
        conf=list(conf_data.get("conf") or []),
        snippets=list(conf_data.get("snippets") or []),
        cmake_args=list(conf_data.get("cmake_args") or []),
        west_args=list(conf_data.get("west_args") or []),
    )


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
