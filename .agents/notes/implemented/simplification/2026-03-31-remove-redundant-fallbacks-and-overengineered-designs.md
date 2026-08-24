# Agent Note: Remove Redundant Fallbacks and Overengineered Designs

Status: implemented

## Problem
The build framework contained several layers of historical compatibility fallbacks and over-engineered abstractions that added unnecessary complexity, caused caching inefficiencies, or risked data duplication:
1. **Redundant Target Fallbacks & Aliases**: `resolver.py` performed 4-tier fuzzy matching (casefold matching, declared name scanning across all TOMLs, duplicate warning deduplication) instead of treating `<name>.toml` as a strict contract. Legacy aliases such as `IMMORTALWRT_*` environment variables, `general.work_root`, `diy` table, and `*_scripts` keys cluttered configuration parsing.
2. **Over-Engineered Toolchain Cache**: `compute_toolchain_key` attempted regex scanning of 7 Kconfig macro types and bound strictly to `target.name` and Git commits, preventing different router targets on the same hardware architecture from sharing toolchain builds and causing cache invalidations on irrelevant upstream commits. Moreover, dual tar/tarfile decompression fallbacks carried unnecessary complexity.
3. **ccache Configuration Overload & Pre-Checks**: Triple-configured ccache (`.config`, environment variables, runtime `ccache.conf` generation), excessive 10G defaults, and redundant pre-build `.config` checks.
4. **Git Safe Directory Overhead**: Custom `add-git-safe` CLI command with recursive traversal and system/global config injection.
5. **Data Double-Writing**: Metadata written concurrently to both `infos/<target>/workspace.json` and flat text files (`lastCommit`, `lastUpstreamCommit`), and CI Summary written by both `output.py` and `write-ci-build-summary.py`.

## Decision
The following simplifications and architectural cleanups are implemented:
1. **Strict Target Resolution & Canonical Naming**:
   - `target_config_path` resolves exclusively via `<name>.toml` matching; missing files raise `FileNotFoundError`.
   - `resolve_work_root` and `resolve_target_name` standardize on `IWB_*` environment variables and `[workspace].work_root`.
   - `loader.py` exclusively recognizes the `[patch]` table with `pre_feeds_patches`, `post_feeds_patches`, and `post_config_patches`.
2. **Cross-Target Toolchain Cache Sharing**:
   - Toolchain cache keys are calculated using `extract_arch_signature` and upstream tree hash: `toolchain-{arch_signature}-{upstream_tree_hash}`.
   - Eliminates `target.name` binding, allowing all targets on the same platform (e.g. MediaTek Filogic, x86_64) to share compiled toolchains.
   - Patch scripts are excluded from toolchain cache hashing (custom compiler patches require manual cache invalidation or defconfig change).
   - Toolchain archive save and restore operations use native system `tar` exclusively.
3. **Cross-Target ccache Partitioning & 3.5G Cap**:
   - ccache directories are partitioned by `arch_signature` (`cache/ccache/<arch_sig>`) and shared across targets of the same architecture.
   - Default ccache storage cap is set to `3.5G`, delegating LRU eviction to ccache itself.
   - Removed redundant `ccache.conf` file generation and pre-compilation `.config` matching checks.
4. **Removal of `add-git-safe`**:
   - Removed `iwb tools add-git-safe` subcommand and related helper functions.
5. **Unified Metadata & CI Step Summary**:
   - Workspace metadata is stored exclusively in `infos/<target>/workspace.json`.
   - `output.py` generates `filedigest.md` without implicitly hooking `$GITHUB_STEP_SUMMARY`, leaving `write-ci-build-summary.py` as the single authoritative summary writer in CI.

## Alternatives considered
- **Retaining Target-Bound Toolchain Keys (`toolchain-{target.name}-...`)**: Evaluated but rejected because building multiple router models on the same chip platform (e.g. 360T7, AX3000M, WR30U on MT7981) forced redundant 20-minute GCC rebuilds for each model.
- **Hashing Patch Scripts into Toolchain Key**: Evaluated but rejected because typical Python patches only tweak user-space packages or network configurations; hashing them into the toolchain key caused spurious toolchain rebuilds on minor application patch changes.

## Consequences
- **Build Performance**: CI pipelines achieve cross-target toolchain cache hits, saving 15–25 minutes of compilation per target on shared architectures.
- **Maintainability**: Removed over 250 lines of redundant fallback, verification, and legacy-alias code.
- **Clarity**: Clear single source of truth for workspace metadata and CI Step Summary output.
