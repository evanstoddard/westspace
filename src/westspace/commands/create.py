"""``westspace create`` - scaffold a new workspace from the Zephyr template.

Pure scaffold: clone the template, drop its history, and start a fresh (empty)
git repo. It makes no commit - the first commit is the user's to make - and it
does not run ``west`` or build anything. Follow with ``westspace init``.
"""

import argparse
import json
import logging
import re
import shutil
import urllib.request
from pathlib import Path

from .. import process
from ..errors import UsageError

log = logging.getLogger("westspace")

NAME = "create"
HELP = "Scaffold a new workspace from the Zephyr project template"

DEFAULT_TEMPLATE_REPO = "https://github.com/evanstoddard/zephyr_template"

_GITHUB_RE = re.compile(r"github\.com[/:]([^/]+)/(.+?)(?:\.git)?/?$")


def configure(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "name",
        help="workspace name; a directory ./NAME is created",
    )
    parser.add_argument(
        "--here",
        action="store_true",
        help="scaffold into the current directory instead of ./NAME (must be empty)",
    )
    parser.add_argument(
        "--template-repo",
        metavar="URL",
        default=DEFAULT_TEMPLATE_REPO,
        help="template repository (default: %(default)s)",
    )
    parser.add_argument(
        "--template-ref",
        metavar="REF",
        default=None,
        help="template tag or branch (default: latest GitHub release, else default branch)",
    )


def run(args: argparse.Namespace) -> int:
    dest = _dest_dir(args)
    ref = args.template_ref or _latest_release(args.template_repo)

    _clone(args.template_repo, ref, dest)
    shutil.rmtree(dest / ".git", ignore_errors=True)
    process.run(["git", "init", "-q", str(dest)])

    log.info("created workspace: %s", dest)
    hint = "westspace init" if args.here else f"cd {dest.name} && westspace init"
    log.info("next: %s", hint)
    return 0


def _dest_dir(args: argparse.Namespace) -> Path:
    if args.here:
        dest = Path.cwd()
        if any(dest.iterdir()):
            raise UsageError(f"{dest} is not empty")
        return dest

    dest = Path.cwd() / args.name
    if dest.exists() and any(dest.iterdir()):
        raise UsageError(f"{dest} already exists and is not empty")
    return dest


def _latest_release(repo_url: str) -> str | None:
    match = _GITHUB_RE.search(repo_url)
    if not match:
        return None
    owner, name = match.group(1), match.group(2)
    api = f"https://api.github.com/repos/{owner}/{name}/releases/latest"
    try:
        with urllib.request.urlopen(api, timeout=10) as response:
            tag = json.load(response).get("tag_name")
    except (OSError, ValueError) as exc:
        log.info("no latest release for %s/%s (%s); using default branch", owner, name, exc)
        return None
    if tag:
        log.info("latest release: %s", tag)
    return tag


def _clone(repo_url: str, ref: str | None, dest: Path) -> None:
    argv = ["git", "clone", "--depth", "1"]
    if ref:
        argv += ["--branch", ref]
    argv += [repo_url, str(dest)]
    process.run(argv)
