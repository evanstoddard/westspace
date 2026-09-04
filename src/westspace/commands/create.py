"""``westspace create`` - scaffold a new workspace from the Zephyr template."""

import argparse

NAME = "create"
HELP = "Scaffold a new workspace from the Zephyr project template"

DEFAULT_TEMPLATE_REPO = "https://github.com/evanrstoddard/zephyr_template"


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
        help="template tag or branch (default: latest release)",
    )


def run(args: argparse.Namespace) -> int:
    raise NotImplementedError(NAME)
