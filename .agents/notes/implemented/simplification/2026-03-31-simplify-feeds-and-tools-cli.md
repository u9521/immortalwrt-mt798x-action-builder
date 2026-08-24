# Agent Note: Simplify Feeds Configuration, Split Feeds CLI, and Consolidate Tools Subcommands

Status: implemented

## Problem
Several areas of configuration and CLI design exhibited unnecessary coupling, redundant abstractions, or naming inconsistencies:
1. **Redundant `[feeds]` Target Configuration**: Feeds customization (adding third-party repos, modifying feeds config) is natively handled by Python patch scripts (e.g. `patch1.py`). The configuration table `[feeds]` with fields `custom_feeds`, `conf_file`, `update`, and `install` added extra schema complexity and duplicate pathways.
2. **Coupled `setup-feeds` CLI**: The composite `setup-feeds` command bundled pre-feeds patches, `feeds update`, `feeds install`, and post-feeds patches together. This prevented granular execution and debugging of feeds update vs feeds installation in CI pipelines.
3. **Missing Structured Patch Configuration**: Python patch scripts had no dedicated mechanism to consume target-specific configuration variables declared in target TOML files without hardcoding or abusing other fields.
4. **Unused `[general]` Global Config**: The `[general]` table in `global.toml` contained `default_depth` and `default_download`, which were never wired into target loading or runtime behavior.
5. **Monolithic `run` Command & Unconsolidated Tools**: The top-level `iwb run` command was a monolithic wrapper, while utility commands `check-update` and `usage` cluttered the top-level CLI namespace instead of residing under `iwb tools`.

## Decision
1. **Remove `[feeds]` Section from Target Configs**:
   - Removed `FeedsConfig` data model and all `[feeds]` table parsing from `schema.py`, `loader.py`, and target TOML templates (`immortalwrt-base.toml`, `mt798x-base.toml`).
   - Feeds customizations are declared exclusively via Python patches in `patchs/`.
2. **Split Feeds CLI into `feeds-update` and `feeds-install`**:
   - Replaced `setup-feeds` with two orthogonal CLI commands:
     - `iwb feeds-update --target <name>`: Applies pre-feeds Python patches (e.g. adding repos to `feeds.conf.default`), then executes `./scripts/feeds update -a`.
     - `iwb feeds-install --target <name>`: Executes `./scripts/feeds install -a`, then applies post-feeds Python patches (e.g. modifying installed package makefiles/configs).
   - Removed `setup_feeds` from `core/feeds/feeds.py`, keeping concise `update_feeds` and `install_feeds` functions.
3. **Introduce `[patchConfig]` for Python Patch Plugins**:
   - Added support for the `[patchConfig]` table in target TOML files.
   - Exposed as `target.patch_config` and accessible inside patch scripts via `context.patch_config` (and `context.target.patch_config`).
   - Supports recursive dictionary merging across target inheritance chains (`extends`).
4. **Clean Global Configuration**:
   - Removed `[general]` table, `default_depth`, and `default_download` from `global.toml` and `GlobalConfig`.
   - `global.toml` exclusively manages `[workspace]` configuration (`work_root`).
5. **Remove `iwb run` and Consolidate `iwb tools`**:
   - Removed `iwb run` in favor of explicit step-by-step pipeline execution in CI and scripts (`sync-source` -> `feeds-update` -> `feeds-install` -> `configure` -> `download` -> `build` -> `digest`).
   - Moved `check-update` to `iwb tools check-update`.
   - Moved `usage` to `iwb tools usage`.

## Alternatives considered
- **Keeping `setup-feeds` as a composite alias**: Rejected to avoid maintaining multiple overlapping commands for the same lifecycle phases and to ensure CI steps remain explicit.
- **Passing patch configuration via environment variables**: Rejected because declaring custom values directly within the target's TOML under `[patchConfig]` provides unified version-controlled target definitions.

## Consequences
- **Modularity & Transparency**: Each step of the build pipeline (`feeds-update`, `feeds-install`, `configure`, `download`, `build`, `digest`) has a distinct, single-purpose CLI entry point.
- **Config Cleanliness**: Target TOML files and `global.toml` contain only actionable configuration fields without dead or duplicated settings.
- **Extensibility**: Python patch scripts can be parameterized via `[patchConfig]` without modifying patch code.
