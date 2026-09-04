# Vanilla and NCS workspaces

`westspace` supports two kinds of workspace. The kind is set by the `ncs` block
in `westspace.yml`: absent or `enabled: false` means vanilla, present means NCS.

## Vanilla (upstream Zephyr)

- A `.venv` is created at the workspace root. `west` and everything
  `west packages pip --install` pulls from the manifest live there.
- `west init -l --mf <manifest_file> <manifest_dir>`, then `west update`.
- `west sdk install` fetches the Zephyr SDK. The version comes from the checked
  out Zephyr (`SDK_VERSION`). The `toolchains` key limits which GNU toolchains
  are installed.
- `west` runs directly from `.venv/bin`.

## NCS (nRF Connect SDK)

- No `.venv`. The toolchain bundle installed by `nrfutil toolchain-manager`
  provides its own Python, west, Zephyr SDK, and host tools.
- If `nrfutil` is not on `PATH`, the latest build is downloaded once into a
  `platformdirs` data directory and reused from there. Toolchain bundles stay in
  `nrfutil`'s own location.
- The `device`, `sdk-manager`, and `toolchain-manager` plugins are installed if
  missing.
- `nrfutil toolchain-manager install --ncs-version <version>` installs the
  bundle for `ncs.version`.
- `west init` and `west update` run through
  `nrfutil toolchain-manager launch --ncs-version <version> -- ...`.
- `west packages pip --install` and `west sdk install` are not run. The bundle
  already provides them, and its Python is not a virtual environment, so
  `west packages pip` would fail.

## Which manifest is used

Vanilla uses the top level `manifest_file` (default `west.yml`). NCS uses
`ncs.manifest_file` (default `west-ncs.yml`). A template repo is expected to
carry both files so a workspace can switch flavors with `westspace init --force`.
