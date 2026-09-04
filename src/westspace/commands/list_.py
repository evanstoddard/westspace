"""``westspace list`` - show configured targets and configs."""

import argparse
import json
import sys

from .. import config, workspace

NAME = "list"
HELP = "List targets and configs defined in westspace.yml"


def configure(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--json",
        action="store_true",
        help="emit machine-readable JSON",
    )


def run(args: argparse.Namespace) -> int:
    ws = workspace.from_args(args)
    cfg = config.load(ws.config_path)

    if args.json:
        _emit_json(ws, cfg)
    else:
        _emit_text(cfg)
    return 0


def _emit_text(cfg: config.Config) -> None:
    flavor = f"NCS {cfg.ncs_version}" if cfg.is_ncs else "vanilla Zephyr"
    print(f"{cfg.path}  ({flavor})")

    targets = cfg.targets
    if not targets:
        print("  (no targets defined)")
        return

    default_target = cfg.resolve_default_target()
    width = max(len(name) for name in targets)

    for name, target in targets.items():
        marker = "*" if name == default_target else " "
        board = target.get("board", "?")
        suffix = "  [sysbuild]" if target.get("sysbuild") else ""
        print(f"{marker} {name.ljust(width)}  {board}{suffix}")

        default_cfg = config.default_config(target)
        for cfg_name in target.get("configs") or {}:
            tag = "  (default)" if cfg_name == default_cfg else ""
            print(f"    - {cfg_name}{tag}")


def _emit_json(ws: workspace.Workspace, cfg: config.Config) -> None:
    payload = {
        "workspace": str(ws.root),
        "config": str(cfg.path),
        "flavor": "ncs" if cfg.is_ncs else "vanilla",
        "ncs_version": cfg.ncs_version if cfg.is_ncs else None,
        "default_target": cfg.resolve_default_target(),
        "targets": {
            name: {
                "source": target.get("source"),
                "board": target.get("board"),
                "sysbuild": bool(target.get("sysbuild", False)),
                "default_config": config.default_config(target),
                "configs": list((target.get("configs") or {}).keys()),
            }
            for name, target in cfg.targets.items()
        },
    }
    json.dump(payload, sys.stdout, indent=2)
    sys.stdout.write("\n")
