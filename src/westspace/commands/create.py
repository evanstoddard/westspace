"""``westspace create`` - scaffold a new workspace from the Zephyr template.

Pure scaffold: clone the template, drop its history, and start a fresh repo.
It does not run ``west`` or build anything - follow with ``westspace init``.
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

DEFAULT_TEMPLATE_REPO = "https://github.com/evanrstoddard/zephyr_template"

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
    _fresh_repo(dest, args.template_repo, ref)

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


def _fresh_repo(dest: Path, repo_url: str, ref: str | None) -> None:
    process.run(["git", "init", "-q", str(dest)])
    process.run(["git", "-C", str(dest), "add", "-A"])
    if _has_git_identity(dest):
        origin = f"{repo_url}@{ref}" if ref else repo_url
        process.run(
            ["git", "-C", str(dest), "commit", "-q", "-m", f"Initial commit from {origin}"]
        )
    else:
        log.warning(
            "git identity not configured; files are staged but not committed "
            "(run 'git commit' in %s)",
            dest,
        )


def _has_git_identity(dest: Path) -> bool:
    for key in ("user.name", "user.email"):
        result = process.run(
            ["git", "-C", str(dest), "config", "--get", key],
            check=False,
            capture=True,
        )
        if result.returncode != 0 or not result.stdout.strip():
            return False
    return True
