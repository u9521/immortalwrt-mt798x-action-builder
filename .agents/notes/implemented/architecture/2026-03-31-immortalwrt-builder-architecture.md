# Agent Note: ImmortalWrt Action Builder Core Architecture

Status: implemented

## Problem
Building OpenWrt / ImmortalWrt firmware across diverse targets (such as MT7981 Filogic and x86_64) often relies on brittle monolithic shell scripts, unmaintainable sed invocations, lack of modularity across targets, and fragile state synchronization in CI runners. A deterministic, maintainable orchestration architecture was required to manage source synchronization, feed updates, configuration fragment composition, dynamic patch execution, caching (ccache and toolchain), and artifact digest generation.

## Decision
We implement a zero-dependency Python 3.14+ build orchestration architecture with CLI entry point `iwb`:

1. **Zero External Runtime Dependencies**:
   - Built exclusively on Python standard library modules (`tomllib`, `pathlib`, `subprocess`, `hashlib`, `shutil`, `json`, `urllib`).
   - Fast execution and instant CI bootstrapping without complex virtual environment setups or wheel compilations.

2. **Layered Directory Layout & Isolated Workspaces**:
   - Checked-in target inputs live under `immortalwrt_builder/configs/targets/`.
   - Checked-in defconfigs and fragments live under `immortalwrt_builder/configs/defconfigs/`.
   - Python patch scripts live under `immortalwrt_builder/configs/patchs/`.
   - Workspaces isolate state per target under `source-code/<target>/`, `cache/<target>/` (ccache and toolchain cache archives), `out/<target>/` for compiled firmware, and `infos/<target>/` for logs and metadata.

3. **Target Configuration & Inheritance**:
   - TOML target definitions support inheritance via the `extends` directive (e.g. extending `immortalwrt-base`).
   - Configurations specify source Git repositories, branches, defconfigs, fragments, custom feeds, patches, and output artifact paths.

4. **Modular Lifecycle Pipeline**:
   - `sync-source`: Initializes git repo and fetches target commit/branch/tag.
   - `feeds-update`: Executes pre-feeds Python patches and runs `./scripts/feeds update -a`.
   - `feeds-install`: Runs `./scripts/feeds install -a` and executes post-feeds Python patches.
   - `configure`: Merges defconfig and executes post-config Python patches.
   - `download`: Pre-downloads package archives via `make download`.
   - `build`: Compiles toolchain and firmware with configurable job concurrency.
   - `digest`: Computes cryptographic checksums and produces summary digests.
   - `tools`: Maintenance commands (`check-update`, `usage`, `clean`, `ccache-*`).

5. **Python Dynamic Patch System**:
   - Target-specific customizations are pure Python scripts executed dynamically with `PatchContext`.
   - `PatchContext` provides structured helpers (`path`, `exists`, `read_text`, `write_text`, `replace_text`, `append_text`, `remove`, `run_command`).

## Alternatives considered
1. **Monolithic Shell Scripts (`diy-part1.sh` / `diy-part2.sh`)**:
   - *Rejected*: Shell scripts lack type safety, structured unit testing, error handling, and cross-platform consistency.
2. **Heavyweight Third-Party Frameworks (Click, Rich, Pydantic)**:
   - *Rejected*: Adding external runtime dependencies introduces potential installation failures and slows down CI initialization. Standard library `argparse` and `tomllib` satisfy all CLI and configuration needs.
3. **Makefiles / Ansible Playbooks**:
   - *Rejected*: Harder to unit-test and lacks native dynamic patch scripting in Python.

## Consequences
- Fast, deterministic firmware builds with strong isolation between targets.
- High testability: complete pipeline and patch executor are covered by unit tests using `unittest`.
- Easy extensibility for new hardware targets by adding TOML target configs and Python patch scripts.
- Developers and agents must maintain pure Python standard library invariants across runtime modules.
