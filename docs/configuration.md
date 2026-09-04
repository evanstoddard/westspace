# westspace.yml

`westspace.yml` lives at the workspace root. It is validated against
[`westspace.schema.json`](../westspace.schema.json); editors that understand the
`yaml-language-server` schema directive will complete and check it.

## Top level

| Key | Default | Purpose |
|-----|---------|---------|
| `version` | required | Schema version. Currently always `1`. |
| `ncs` | absent | Presence selects the nRF Connect SDK instead of vanilla Zephyr. |
| `manifest_dir` | `project` | Directory passed to `west init -l`. |
| `manifest_file` | `west.yml` | Manifest inside `manifest_dir`, used with `west init -l --mf`. |
| `toolchains` | absent | Zephyr SDK GNU toolchains to install. Vanilla only. |
| `default_target` | none | Target used when a command is given no `TARGET`. |
| `targets` | required | Named build targets. |

## `ncs`

Omit the whole block for vanilla Zephyr. When present:

| Key | Default | Purpose |
|-----|---------|---------|
| `enabled` | `true` | Set `false` to keep the block but build vanilla. |
| `version` | required | `sdk-nrf` release, e.g. `v2.7.0`. Drives `nrfutil toolchain-manager install`. |
| `manifest_file` | `west-ncs.yml` | Manifest used in place of the top level `manifest_file`. |

`version` must be a released NCS version string. Branches and commit SHAs are
not accepted by `nrfutil toolchain-manager`.

## `toolchains`

Controls `west sdk install`:

- omitted: install every toolchain
- a list such as `[arm-zephyr-eabi]`: install only those (`-t`)
- an empty list `[]`: install none (`-T`), SDK and host tools only

Ignored for NCS, which gets its toolchain from the nrfutil bundle.

## Targets and configs

    targets:
      app:
        source: project/app          # app directory passed to west build
        board: nrf52840dk/nrf52840
        sysbuild: false              # optional, adds --sysbuild
        default_config: default      # config for "westspace build app"
        configs:
          default: {}
          dev:
            overlays: [boards/dev.overlay]   # EXTRA_DTC_OVERLAY_FILE
            conf: [dev.conf]                 # EXTRA_CONF_FILE
            snippets: [rtt-console]          # west build -S
            cmake_args: [-DFOO=y]            # after the -- separator
            west_args: [--sysbuild]          # to west build itself
            build_dir: build/app-dev         # default: build/<target>-<config>

Every key under a `config` is optional. `overlays` and `conf` paths are relative
to the target's `source` directory.

Resolution when a command takes `TARGET[:CONFIG]`:

- target: the `TARGET` argument, else `default_target`, else the only target if
  there is exactly one
- config: the `:CONFIG` part, else the target's `default_config`, else a config
  named `default`

## Vanilla example

    # yaml-language-server: $schema=https://github.com/evanstoddard/westspace/westspace.schema.json
    version: 1

    manifest_dir: project
    default_target: app

    toolchains:
      - arm-zephyr-eabi

    targets:
      app:
        source: project/app
        board: nrf52840dk/nrf52840
        default_config: default
        configs:
          default: {}
          dev:
            conf: [dev.conf]
            snippets: [rtt-console]
            build_dir: build/app-dev
      sim:
        source: project/app
        board: native_sim/native/64
        default_config: default
        configs:
          default:
            build_dir: build_sim

## NCS example

    # yaml-language-server: $schema=https://github.com/evanstoddard/westspace/westspace.schema.json
    version: 1

    ncs:
      enabled: true
      version: v2.7.0

    manifest_dir: project
    default_target: app

    targets:
      app:
        source: project/app
        board: nrf52840dk/nrf52840
        sysbuild: true
        default_config: default
        configs:
          default: {}
          release:
            conf: [release.conf]
            build_dir: build/app-release
