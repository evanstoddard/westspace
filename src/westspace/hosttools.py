"""Best-effort check for host build tools.

Missing tools are warned about, never fatal: they are installed through the
system package manager, which is out of westspace's scope.
"""

import logging
import shutil
from collections.abc import Iterable

log = logging.getLogger("westspace")

# Tools a typical Zephyr build shells out to.
HOST_TOOLS = ("cmake", "ninja", "dtc", "gperf", "git")


def check(extra: Iterable[str] = ()) -> list[str]:
    """Return the list of tools from :data:`HOST_TOOLS` (plus *extra*) not on PATH."""
    wanted = [*HOST_TOOLS, *extra]
    missing = [tool for tool in wanted if shutil.which(tool) is None]
    if missing:
        log.warning(
            "warning: host tools not found on PATH: %s\n"
            "  install them with your system package manager before building.",
            ", ".join(missing),
        )
    return missing
