"""Exception types and exit-code conventions.

Anything deriving from :class:`WestspaceError` is an *expected* failure: the CLI
prints its message without a traceback and exits with ``exit_code``. Unexpected
exceptions propagate normally so they show a full traceback.

Exit codes:
    0   success
    1   general runtime error (:class:`WestspaceError` default)
    2   usage / not-yet-implemented
    130 interrupted (Ctrl-C)
"""


class WestspaceError(Exception):
    """Base class for expected, user-facing errors."""

    exit_code = 1


class UsageError(WestspaceError):
    """The command was invoked incorrectly."""

    exit_code = 2


class WorkspaceNotFoundError(WestspaceError):
    """No ``westspace.yml`` could be located from the current directory."""


class ConfigError(WestspaceError):
    """``westspace.yml`` is missing, malformed, or fails schema validation."""


class ToolNotFoundError(WestspaceError):
    """A required external tool (``west``, ``nrfutil``, …) is unavailable."""


class CommandError(WestspaceError):
    """An external command exited non-zero."""
