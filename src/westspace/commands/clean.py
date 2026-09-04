"""``westspace clean`` - remove build output, or the whole initialized tree."""

import argparse
import logging
import shutil
from pathlib import Path

from .. import config, nrfutil, west, workspace
from ..errors import CommandError, WestspaceError

log = logging.getLogger("westspace")

NAME = "clean"
HELP = "Remove build directories (with --all, also the initialized workspace tree)"


def configure(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "target",
        nargs="?",
        metavar="TARGET[:CONFIG]",
        help="only clean this target/config's build directory (ignored with --all)",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="also remove .west/, fetched west projects (zephyr/, modules/, ...) "
        "and the workspace venv",
    )
    parser.add_argument(
        "--yes",
        action="store_true",
        help="do not prompt for confirmation (required with --all when non-interactive)",
    )


def run(args: argparse.Namespace) -> int:
    ws = workspace.from_args(args)
    cfg = config.load(ws.config_path)

    build_dirs = _build_dirs(ws, cfg, None if args.all else args.target)

    if not args.all:
        _remove_present(build_dirs)
        return 0

    paths = _strip_nested(_dedupe(build_dirs + _workspace_paths(ws, cfg)))
    present = [p for p in paths if p.exists() or p.is_symlink()]
    if not present:
        log.info("nothing to clean")
        return 0

    if not args.yes:
        _confirm(present)

    _remove_present(present)
    log.info("workspace reset; run 'westspace init' to rebuild it")
    return 0


def _build_dirs(
    ws: workspace.Workspace, cfg: config.Config, spec: str | None
) -> list[Path]:
    if spec:
        resolved = [config.resolve_target(cfg, spec)]
    else:
        resolved = [
            config.resolve_target(cfg, f"{name}:{cname}")
            for name, target in cfg.targets.items()
            for cname in (target.get("configs") or {})
        ]
    return _dedupe(ws.root / r.build_dir for r in resolved)


def _workspace_paths(ws: workspace.Workspace, cfg: config.Config) -> list[Path]:
    """`.west/`, the venv, and every west project outside the manifest repo."""
    paths = [ws.west_dir, ws.venv_dir, ws.zephyr_dir, ws.modules_dir]

    if ws.is_initialized:
        manifest_root = (ws.root / cfg.manifest_dir).resolve()
        try:
            runner = west.runner_for(
                cfg, ws, nrfutil_path=nrfutil.locate() if cfg.is_ncs else None
            )
            listing = runner.run("list", "-f", "{abspath}", capture=True)
        except CommandError:
            log.warning(
                "could not list west projects; some fetched directories may remain"
            )
        else:
            for line in listing.stdout.splitlines():
                project = Path(line.strip())
                if not line.strip():
                    continue
                if ws.root not in project.parents:
                    continue
                if project == manifest_root or manifest_root in project.parents:
                    continue
                paths.append(project)

    return _dedupe(paths)


def _dedupe(paths) -> list[Path]:
    seen: set[Path] = set()
    out: list[Path] = []
    for path in paths:
        resolved = path.resolve()
        if resolved not in seen:
            seen.add(resolved)
            out.append(path)
    return out


def _strip_nested(paths: list[Path]) -> list[Path]:
    """Drop paths that live inside another path already in the list."""
    resolved = [p.resolve() for p in paths]
    return [
        path
        for path, rp in zip(paths, resolved)
        if not any(other != rp and other in rp.parents for other in resolved)
    ]


def _confirm(paths: list[Path]) -> None:
    print("This will permanently remove:")
    for path in paths:
        print(f"  {path}")
    try:
        reply = input("Proceed? [y/N] ")
    except EOFError:
        raise WestspaceError("not an interactive terminal; pass --yes to confirm") from None
    if reply.strip().lower() not in ("y", "yes"):
        raise WestspaceError("aborted")


def _remove_present(paths: list[Path]) -> None:
    removed = 0
    for path in paths:
        if path.is_dir() and not path.is_symlink():
            log.info("removing %s", path)
            shutil.rmtree(path, ignore_errors=True)
            removed += 1
        elif path.exists() or path.is_symlink():
            log.info("removing %s", path)
            path.unlink(missing_ok=True)
            removed += 1
    if removed == 0:
        log.info("nothing to clean")
