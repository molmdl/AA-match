# Codebase Structure

**Analysis Date:** 2026-09-12

## Directory Layout

```
AA-match/                       # repo root (Windows-visible via /mnt/c — PyMOL smokes run against this copy)
├── aamatch/                    # THE plugin package (installed via PyMOL Plugin Manager)
│   ├── __init__.py             # composition root; ZERO module-level imports; '# Version:' metadata block first
│   ├── data/                   # bundled game data (committed)
│   │   ├── MANIFEST.json       # versioned manifest container (sets -> entries; sha256-pinned ligands)
│   │   └── ligands/            # demo SDF ligand files (acetate.sdf, benzamide.sdf, ...)
│   ├── [pure layer]            # 15 modules — see Key File Locations
│   └── [cmd tier]              # 5 modules — see Key File Locations
├── tests/                      # WSL unit tests (python3.6 -m unittest discover -s tests -v)
├── smoke/                      # headless Windows-PyMOL smokes + run_smoke.sh harness
├── docs/                       # human reference docs (DETECTION_THRESHOLDS.md)
├── .planning/                  # GSD workflow state — source of truth for scope/progress (see Special Directories)
├── spec.md                     # product/design spec (code & UI standards, dependency constraints)
├── AGENTS.md                   # agent-facing repo rules (WSL/Windows split, purity gates, worktree protocol)
├── README.md                   # user-facing: install, requirements, license
├── opencode.json               # OpenCode tool permissions (denies pip/apt/conda/rm)
├── LICENSE                     # BSD 3-Clause
├── tmp/                        # GIT-IGNORED scratch (probe scripts, v1 reference checkout)
├── Pymol-script-repo ->        # GIT-IGNORED symlink to ../bioCHEMeleon/Pymol-script-repo (v1 reference plugins)
└── pymol-src ->                # GIT-IGNORED symlink to ../bioCHEMeleon/tmp/pymol-src (PyMOL 2.5.0 source, citation source)
```

Note: `vmd/` (planned Phase-2-of-product VMD Tcl port), `vmd-ref/`, `3rd_party_lib/`, `vmd/3rd_party_lib/` do NOT exist yet — they are reserved in `.gitignore`. Architecture is currently PyMOL-only.

## Directory Purposes

**`aamatch/` (pure layer — stdlib + pure siblings ONLY):**
- Purpose: All game logic, math, schemas, I/O discipline. Unit-tested in WSL with bare python3.6, zero stubs.
- Contains: one module per concern, flat layout (no subpackages except `data/`)
- Key files: `aamatch/setup_state.py`, `aamatch/level_spec.py`, `aamatch/persistence.py`, `aamatch/backup.py`, `aamatch/paths.py`, `aamatch/vec3.py`, `aamatch/spatial.py`, `aamatch/manifest.py`, `aamatch/capability.py`, `aamatch/thresholds.py`, `aamatch/detector.py`, `aamatch/generator.py`, `aamatch/game_state.py`, `aamatch/wizard_core.py`, `aamatch/wizard_text.py`
- Registration rule: a new pure module MUST be added to `PURE_MODULES` in `tests/test_purity.py:87-90` (unregistered modules are silently ungated; the registration-pin tests in that file are the pattern to copy).

**`aamatch/` (cmd tier — module-level `from pymol import cmd`):**
- Purpose: PyMOL bridges + orchestration. NEVER registered in `PURE_MODULES` (Gate D still compiles them at the 3.6 floor). NO Qt anywhere (Phase 4 will add Qt-facing modules with the same rule).
- Key files: `aamatch/geometry.py` (object → plain-data bridge), `aamatch/placement.py` (materializer + cleanup + reset), `aamatch/engine.py` (headless op set + module-level runtime state), `aamatch/wizard.py` (`GameWizard` viewer adapter), `aamatch/gamestart.py` (THE game-start seam)

**`aamatch/data/`:**
- Purpose: Bundled game data the plugin loads at runtime via `aamatch/paths.py:package_data_path`.
- Contains: `MANIFEST.json` (container kind `'manifest'`; each entry pins `file`, `sha256`, atom/bond counts, `size_class`, protonation), `ligands/*.sdf`.

**`tests/`:**
- Purpose: The complete WSL suite. `tests/test_purity.py` enforces the purity contract (Gates A/A2/B/D + negative control); `tests/test_code_audit.py` audits source text via AST (routing, banned cmd calls, no naive pair loops); `tests/test_wizard_source.py` pins wizard-file discipline; the rest are per-module unit/invariant suites.
- Contains: one `test_<module>.py` per pure module, plus `test_detector_invariance.py` / `test_generator_invariants.py` corpus suites; `tests/__init__.py` marks the package.

**`smoke/`:**
- Purpose: Headless proofs against REAL Windows PyMOL (the repo copy — no staging). Verdict carried by a printed marker, not exit code.
- Contains: `smoke/run_smoke.sh` (harness; greps `=== SMOKE-NN PASS ===`), `smoke/smoke_01_bootstrap.py` through `smoke/smoke_08_starter.py`.

**`docs/`:**
- Purpose: Human-facing reference (currently only `docs/DETECTION_THRESHOLDS.md` — the approved threshold table backing `aamatch/thresholds.py`).

## Key File Locations

**Entry Points:**
- `aamatch/__init__.py`: PyMOL plugin entry (`__init_plugin__`, `run_plugin_gui`); `# Version: 0.1.0` metadata block must stay the first lines
- `aamatch/gamestart.py:60`: `start_game()` — the one seam every game start routes through
- `smoke/run_smoke.sh`: smoke harness (`bash smoke/run_smoke.sh smoke/<script>.py` from repo root)

**Configuration:**
- `opencode.json`: OpenCode permissions
- `.gitignore`: reference-dir and artifact exclusions
- `.planning/config.json`: GSD config (`commit_docs: true`, parallelization)

**Core Logic:**
- `aamatch/generator.py`: seeded level construction (the producer side)
- `aamatch/detector.py`: 7-type interaction classification
- `aamatch/game_state.py`: SCORE-01 scoring + `GameState`
- `aamatch/engine.py`: the headless operation set (module-level `_payload`/`_registry`/`_game` at lines 93-95)
- `aamatch/placement.py`: scene materialization; `SENTINEL_SEGI`/`SENTINEL_B` at lines 96-97
- `aamatch/persistence.py`: container format; `FORMAT_VERSION` at line 35
- `aamatch/level_spec.py`: spec gates; `DETECTOR_VERSION`/`LEVEL_SPEC_VERSION` at lines 60-61

**Testing:**
- `tests/test_purity.py`: the enforced purity gates
- `tests/test_code_audit.py`: AST source audit
- `tests/test_<module>.py`: per-module suites

## Naming Conventions

**Files:**
- Python modules: lowercase `snake_case`, one concern per file: `setup_state.py`, `wizard_text.py`, `level_spec.py`
- Tests: `test_<module>.py` mirroring the module under test (`tests/test_detector.py` ↔ `aamatch/detector.py`); corpus/invariant suites suffix `_invariance`/`_invariants`
- Smokes: `smoke_NN_name.py` — NN is parsed by `run_smoke.sh` for the marker grep; renaming without the NN segment breaks verdict detection

**Directories:**
- Flat package layout inside `aamatch/`; data under `aamatch/data/`
- Planning: `.planning/phases/NN-name/` with `NN-MM-PLAN.md` / `NN-MM-SUMMARY.md` (+ optional `NN-RESEARCH-*.md`, `NN-VERIFICATION.md`)

**In-scene names (PyMOL):**
- Game objects: `cmd.get_unused_name('_aam_<role>')`, role in `{'lig', 'aa', 'tmp'}` — the reserved prefix is the ONLY cleanup rule
- Sentinels: every game atom carries `segi='AAM'`, `b=-999.0`

## Where to Add New Code

**New pure game rule / schema / math:**
- Primary code: new or existing module in `aamatch/` (stdlib + pure-sibling imports ONLY)
- Register it: append the module name to `PURE_MODULES` in `tests/test_purity.py` (copy the registration-pin test pattern)
- Tests: `tests/test_<module>.py` (must import with zero stubs — if it needs a pymol stub, it belongs in the cmd tier)

**New cmd-tier op (anything touching PyMOL objects):**
- Implementation: `aamatch/engine.py` (game ops) or `aamatch/placement.py`/`aamatch/geometry.py` (scene/bridge mechanics). Module-level `from pymol import cmd` is legal; Qt is not.
- Proof: extend or add `smoke/smoke_NN_*.py` + run via `bash smoke/run_smoke.sh`; no WSL unittest can import these modules.

**New wizard behavior (clicks/keys/panel):**
- Thin adapter code: `aamatch/wizard.py` (plain picklable attributes only; engine imported lazily inside methods)
- Any logic that can be pure goes in `aamatch/wizard_core.py` or `aamatch/wizard_text.py` instead (WSL-testable).

**New bundled ligand set:**
- Data: `aamatch/data/ligands/<name>.sdf` + entry in `aamatch/data/MANIFEST.json` (sha256-pinned; format per `tests/test_manifest.py` fixtures)

**New phase/planning artifacts:**
- `.planning/phases/NN-name/NN-MM-PLAN.md` etc.; project-level docs in `.planning/` (committed — `commit_docs: true`)

**Qt setup window (Phase 4):**
- New module(s) in `aamatch/` importing `pymol.Qt`; MUST route through the existing `gamestart.start_game` seam; never add to `PURE_MODULES`.

**Utilities:**
- Shared pure helpers: extend the existing homes (`vec3`, `spatial`, `paths`) — do NOT create grab-bag `util.py` modules; single-home discipline (typing in `capability`, thresholds in `thresholds`, enums in `setup_state`).

## Special Directories

**`.planning/`:**
- Purpose: GSD workflow state — `PROJECT.md` (what/why), `ROADMAP.md` (phase plan), `STATE.md` (current position), `REQUIREMENTS.md` (requirement IDs), `research/` (verified API/pitfalls docs — READ before non-trivial viewer work), `phases/NN-name/` (per-phase plans/summaries), `codebase/` (this mapping), `debug/` (checkpoint failure logs)
- Generated: No (hand/agent-authored)
- Committed: **Yes** (`commit_docs: true`; Conventional Commits with phase scope, e.g. `feat(02-03):`)

**`tmp/`:**
- Purpose: Scratch — crash-hunt/materialization probe scripts (`probe_*.py`), `tmp/fixtures`, and `tmp/bioCHEMeleon -> ../../bioCHEMeleon/pymol` (symlink to the shipped v1 plugin, the architectural prior art)
- Generated: Yes (ad-hoc)
- Committed: **No** (git-ignored)

**`Pymol-script-repo/`, `pymol-src/`:**
- Purpose: Reference material. `Pymol-script-repo ->` v1 reference plugins; `pymol-src ->` the local PyMOL 2.5.0 source tree — the citation authority for every PyMOL API claim (symlinks out of the repo into `../bioCHEMeleon/`)
- Generated: No
- Committed: **No** (git-ignored; rely on the symlink targets' presence on the dev machine only)

**`aamatch/__pycache__/`, `tests/__pycache__/`, `smoke/__pycache__/`:**
- Purpose: Byte-compiled caches from local py_compile/test runs
- Generated: Yes
- Committed: **No** (`*.pyc` ignored; safe to leave in place)

---

*Structure analysis: 2026-09-12*
