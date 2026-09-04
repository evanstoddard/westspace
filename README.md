# westspace

A command line tool for managing Zephyr [west](https://docs.zephyrproject.org/latest/develop/west/index.html) workspaces.

`westspace` reads a `westspace.yml` at the workspace root and uses it to
bootstrap the workspace, build named targets, flash, and open a toolchain shell.
It replaces the per-project shell scripts a Zephyr template repo usually carries.

Both vanilla upstream Zephyr and the nRF Connect SDK (NCS) are supported. Vanilla
workspaces use a local `.venv` plus `west sdk install`. NCS workspaces run west
through `nrfutil toolchain-manager`.

## Install

Requires Python 3.14+ and `git`.

    uv tool install git+https://github.com/evanstoddard/westspace

From a local checkout:

    uv tool install .

For development: `uv sync`, then `uv run westspace ...`.

## tl;dr

    westspace create my-project      # scaffold from the Zephyr template
    cd my-project
    westspace init                   # west init + update + toolchain install
    westspace build                  # build the default target
    westspace build app:dev          # build target "app", config "dev"
    westspace flash app:dev          # flash that build
    westspace launch                 # shell with the toolchain env active
    westspace list                   # show targets and configs

Use `-C PATH` to point at a workspace other than the current directory, and `-v`
for more output.

## Documentation

- [docs/configuration.md](docs/configuration.md): the `westspace.yml` format
- [docs/commands.md](docs/commands.md): every command and its options
- [docs/flavors.md](docs/flavors.md): how vanilla and NCS workspaces differ
