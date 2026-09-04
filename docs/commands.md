# Commands

Global options, given before the command:

| Option | Purpose |
|--------|---------|
| `-C, --workspace PATH` | Workspace directory. Default: search upward from the current directory for `westspace.yml`. |
| `-v, --verbose` | More output. Repeatable. |
| `--version` | Print version and exit. |

For how `TARGET[:CONFIG]` resolves, see "Targets and configs" in
[configuration.md](configuration.md).

## create

    westspace create NAME [--here] [--template-repo URL] [--template-ref REF]

Clones the template into `./NAME`, removes the cloned `.git`, and runs
`git init`. It makes no commit and does not run west.

- `--here`: scaffold into the current directory, which must be empty.
- `--template-repo`: default `https://github.com/evanrstoddard/zephyr_template`.
- `--template-ref`: tag or branch. Default: the latest GitHub release, or the
  default branch if there are no releases.

## init

    westspace init [--force]

Brings an existing workspace to a buildable state.

Vanilla: create `.venv`, `pip install west`, `west init`, `west update`,
`west packages pip --install`, `west sdk install`.

NCS: ensure `nrfutil` and its `device`, `sdk-manager`, and `toolchain-manager`
plugins, run `nrfutil toolchain-manager install`, then `west init` and
`west update` through `nrfutil toolchain-manager launch`.

`west init` is skipped when `.west/` already exists. `--force` removes `.west/`
first. The other steps always run, so `init` is safe to repeat.

## update

    westspace update

Runs `west update` only. It refuses if `.west/config` records a different
manifest than `westspace.yml` now selects (for example after toggling `ncs`);
run `westspace init --force` in that case.

## build

    westspace build [TARGET[:CONFIG]] [--pristine[={always,auto,never}]]
                    [--board BOARD] [--no-auto-init] [-- CMAKE_ARGS]

Runs `west build` for the resolved target and config, assembling the board,
`--sysbuild`, `-d <build_dir>`, `-S` snippets, `EXTRA_DTC_OVERLAY_FILE`,
`EXTRA_CONF_FILE`, `cmake_args`, and `west_args` from `westspace.yml`.

- `--pristine` with no value means `auto`.
- `--board` overrides the target's board.
- Anything after `--` goes to CMake.
- If `.west/` is missing, `init` runs first unless `--no-auto-init` is given.

## flash

    westspace flash [TARGET[:CONFIG]] [-- FLASH_ARGS]

Runs `west flash -d <build_dir>` for the resolved target and config. Anything
after `--` goes to `west flash`, for example `-- --runner jlink --dev-id 1`. It
errors when the build directory has no `CMakeCache.txt`.

## clean

    westspace clean [TARGET[:CONFIG]] [--all] [--yes]

Without `--all`: removes the build directory for the named target and config, or
for every target and config if none is named.

With `--all`: also removes `.west/`, the `.venv`, and every fetched west project
(`zephyr/`, `modules/`, and so on). Source files and `westspace.yml` are kept.
It prompts unless `--yes`, and requires `--yes` when stdin is not a terminal.

## launch

    westspace launch [-- COMMAND]

Opens a shell, or runs `COMMAND`, with the toolchain environment active.

Vanilla: the `.venv` is first on `PATH`, with `VIRTUAL_ENV` and `ZEPHYR_BASE`
set.

NCS: runs through `nrfutil toolchain-manager launch --shell`, or
`nrfutil toolchain-manager launch -- COMMAND`.

## list

    westspace list [--json]

Prints the targets and configs from `westspace.yml`, marking the default target
and each default config. `--json` emits the same information for scripts.
