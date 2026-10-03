# Codebase Structure

**Analysis Date:** 2026-10-03

## Directory Layout

```
AA-match/
├── aamatch/            # The PyMOL plugin package (pure layer + cmd tier + Qt tier)
│   ├── data/           # Bundled demo molecules (committed; regenerated, never hand-edited)
│   │   ├── MANIFEST.json
│   │   └── ligands/    # *.sdf demo ligand records (acetate.sdf ... demo-veryhard-2-heme.sdf)
│   └── *.py            # 28 modules — see Directory Purposes below
├── tests/              # WSL unittest suite (stdlib only, python3.6) incl. mechanical gates
├── smoke/              # Headless Windows-PyMOL proof scripts + run_smoke.sh runner
├── scripts/            # Build tooling (Phase 8 demo-data pipeline)
│   └── demo_specs/     # Per-demo-set JSON specs consumed by build_demos.py
├── docs/               # Human-gated reference docs (detection thresholds, data sources)
├── .planning/          # GSD planning docs (PROJECT/ROADMAP/STATE/phases/research) — NOT code
├── spec.md             # Feature spec (the game + setup-window requirements)
├── AGENTS.md           # Environment + workflow rules (WSL/Windows split, purity gates)
├── README.md           # User-facing install/requirements
├── opencode.json       # OpenCode agent config (denies pip/apt/conda/rm)
├── LICENSE
├── Pymol-script-repo   # Symlink → ../bioCHEMeleon/Pymol-script-repo (gitignored prior-art reference; NOT code)
├── pymol-src           # Symlink → ../bioCHEMeleon/tmp/pymol-src (gitignored PyMOL source reference; NOT code)
└── tmp/                # Gitignored scratch (not code)
```

**NOT present / do not invent:** no `vmd/` (VMD/Tcl port is planned only), no `Pymol-script-repo/` or `vmd-ref/` content in-repo (symlinked/gitignored reference material), no `3rd_party_lib/` (vendored-libs dir, gitignored), no `biochemeleon.zip` (gitignored install artifact).

## Directory Purposes

**`aamatch/` (the package):**
- Purpose: The whole plugin, exactly one flat module per concern — layered as PURE / CMD TIER / QT TIER (see `.planning/codebase/ARCHITECTURE.md`).
- Contains:
  - **Plugin entry:** `__init__.py` (metadata comment block FIRST + `__version__` + `__init_plugin__` + `run_plugin_gui`; ZERO module-level imports).
  - **Pure foundation (Phase 1):** `setup_state.py`, `level_spec.py`, `persistence.py`, `backup.py`, `paths.py`.
  - **Pure game core (Phases 2–3):** `vec3.py`, `spatial.py`, `manifest.py`, `capability.py`, `thresholds.py`, `detector.py`, `generator.py`, `game_state.py`, `wizard_core.py`, `wizard_text.py`.
  - **Pure window/checkpoint glue (Phases 4–7):** `setup_form.py`, `game_file.py`, `status_text.py`, `checkpoint.py`.
  - **Cmd tier:** `engine.py`, `geometry.py`, `placement.py`, `wizard.py`, `gamestart.py`, `upload.py`.
  - **Qt tier:** `setup_window.py`, `game_window.py`.
- Key files: `aamatch/gamestart.py` (lifecycle seam), `aamatch/engine.py` (headless ops + module state), `aamatch/persistence.py` (`FORMAT_VERSION`, container law), `aamatch/level_spec.py` (`DETECTOR_VERSION`, `LEVEL_SPEC_VERSION`).

**`aamatch/data/`:**
- Purpose: Bundled demo molecule supply, resolved at runtime via `paths.package_data_path('data', ...)` (never `os.getcwd()`).
- Contains: `MANIFEST.json` (versioned container, kind `'manifest'`; sets of entries with file, sha256, atom/bond counts, protonation, provenance) and `ligands/*.sdf`.
- Rule: NEVER hand-edit SDF or MANIFEST.json — regenerate via `scripts/build_demos.py`.

**`tests/`:**
- Purpose: The entire WSL-side verification suite — plain `unittest`, stdlib only, `python3.6 -m unittest discover -s tests -v`.
- Contains: one `test_<module>.py` per pure module (mirrors the module name), plus `test_purity.py` (the mechanical purity gates + `PURE_MODULES` registry), `test_code_audit.py` (AST audits of detector/discipline), `test_demo_data.py` / `test_demo_supply.py` (bundled-data integrity batteries), `test_detector_invariance.py`, `test_generator_invariants.py`, `test_wizard_source.py` (source scans of Qt/cmd tiers), `test_package_skeleton.py`.
- Key files: `tests/test_purity.py` (THE enforced layering contract), `tests/__init__.py`.

**`smoke/`:**
- Purpose: Headless proof that the REAL Windows PyMOL build does what the WSL suite claims; numbered scripts 01–21 by phase/feature.
- Contains: `run_smoke.sh` (wraps `cmd.exe /c C:\src\run-conda-pymol.bat -cq` and greps `=== SMOKE-NN PASS ===`), and `smoke_NN_*.py`: bootstrap/manifest/generate/e2e/perf (01–05), movement spike + wizard loop + starter composition (06–08), Qt probes + window (09–11), upload flow (10, 12), status surface/tab/lifecycle (13–16), `.pse` round-trip + checkpoint save/import/e2e + demo cleanup (17–21).

**`scripts/`:**
- Purpose: Committed build tooling, not runtime code.
- Contains: `build_demos.py` (stdlib-only V2000 SDF parser: derives atom/bond counts + sha256 from ligand bytes IN THE SAME RUN, fetches/verifies, emits SDF bytes + MANIFEST.json set payloads) and `demo_specs/<set_id>.json` (10 curated demo sets: easy/hard/veryhard/challenge/dev tiers).

**`docs/`:**
- Purpose: Human-gated truth documents referenced by code docstrings.
- Contains: `DETECTION_THRESHOLDS.md` (the approved DETECT-03 gate table backing `aamatch/thresholds.py` and `aamatch/capability.py`), `DATA_SOURCES.md` (demo-data provenance).

## Key File Locations

**Entry Points:**
- `aamatch/__init__.py:16` — `__init_plugin__` (Plugins-menu registration; metadata comment block must stay the file's first lines).
- `aamatch/__init__.py:29` — `run_plugin_gui` (lazy-imports `setup_window.open_window`).
- `aamatch/gamestart.py:412` — `start_game` (THE game-start seam; menu + Qt window share it).
- `aamatch/gamestart.py:496` — `start_game_from_payload` (Import / Restart, embed-don't-regenerate).
- `aamatch/gamestart.py:646` — `load_checkpoint` (`.aamz` resume; gates-first ordering).
- `smoke/run_smoke.sh` — headless Windows-PyMOL smoke runner.

**Configuration:**
- `aamatch/__init__.py:13` — `__version__` (kept in sync with the top `# Version:` comment).
- `aamatch/setup_state.py:40-62` — `INTERACTION_TYPES`, clamp constants, `DEFAULTS` (the 7-field setup schema).
- `aamatch/persistence.py:37` — `FORMAT_VERSION`; `aamatch/level_spec.py:60-61` — `DETECTOR_VERSION` / `LEVEL_SPEC_VERSION`; `aamatch/checkpoint.py` — `CHECKPOINT_VERSION`; `aamatch/game_file.py` — `GAME_VERSION`.
- `aamatch/thresholds.py` — every numeric detection criterion (single import point; bumpy = `DETECTOR_VERSION` event).
- `aamatch/data/MANIFEST.json` — bundled demo supply contract.
- `opencode.json` — agent sandbox rules.

**Core Logic:**
- `aamatch/generator.py` — seeded level construction (solvability-by-construction).
- `aamatch/detector.py` — the 7-type detection pipeline (pure).
- `aamatch/engine.py` — the headless op set + module-level `_payload`/`_registry`/`_game` state.
- `aamatch/placement.py` — materializer (`_aam_*` objects, sentinel tags, registry).
- `aamatch/geometry.py` — PyMOL → plain-data bridge.
- `aamatch/wizard.py` — `GameWizard` (thin input adapter over engine ops).
- `aamatch/setup_window.py` / `aamatch/game_window.py` — the modeless window + Game status tab.

**Testing:**
- `tests/test_purity.py` — Gates A (AST import scan), A2 (zero-init-imports), B (clean-subprocess import), D (3.6 syntax floor) + negative control.
- `tests/test_code_audit.py` — AST audits: `cross_pairs` routing, oracle isolation, no banned helper-visual call sites.
- `smoke/smoke_04_e2e.py`, `smoke/smoke_20_checkpoint_e2e.py` — end-to-end game and checkpoint proofs.

## Naming Conventions

**Files:**
- One flat module per concern, `snake_case.py`, no subpackages: `aamatch/game_file.py`, `aamatch/setup_state.py`, `aamatch/wizard_core.py`.
- Pure test mirrors module: `tests/test_<module>.py` (`tests/test_game_state.py` ↔ `aamatch/game_state.py`).
- Smokes: `smoke/smoke_NN_<feature>.py` (two-digit NN embedded in the PASS marker `=== SMOKE-NN PASS ===`).

**Game-object identity (PyMOL scene):**
- Private/hidden objects use the leading-underscore prefix: game objects `_aam_*` (prefix-only cleanup; user objects untouched), temp loads `_aam_tmp`, reserved backup prefix `_aam_backup` (`aamatch/backup.py:50`).
- Game atoms are sentinel-tagged: `segi AAM` + `b < 0` (the molecule-scoping and reconcile selectors).

**Code-level:**
- Private helpers: leading underscore (`gamestart._move_ligand_in_front`, `engine._current_game`).
- Errors: `<Domain>Error` classes — `FormatError`, `EngineError`, `PlacementError`, `GenerationError`, `WizardError`, `BackupError` (ValueError family except BackupError).
- Constants: `UPPER_SNAKE` with single-home law (`INTERACTION_TYPES` lives ONLY in `setup_state`; thresholds ONLY in `thresholds`).
- House string style: `%`-formatting (python3.6 floor).

## Where to Add New Code

**New pure logic (schema/chemistry/math/text/file-shape):**
- Primary code: new flat module `aamatch/<name>.py`, stdlib + pure-relative imports ONLY (any scope — Gate A scans function bodies too).
- Register the module name in `PURE_MODULES` in `tests/test_purity.py:99` (unregistered pure modules are silently ungated — the registration-pin tests show the pattern).
- Tests: `tests/test_<name>.py` — plain unittest, stdlib only, zero `sys.modules` stubs.

**New PyMOL scene operation:**
- Primary code: `aamatch/engine.py` (count-asserted op; plain data in/out) or `aamatch/placement.py`/`aamatch/geometry.py` for materialization/extraction. `from pymol import cmd` at module level is legal there; NEVER add these modules to `PURE_MODULES`.
- Proof: a `smoke/smoke_NN_<feature>.py` driving `gamestart`/`engine` headless on Windows PyMOL.

**New wizard interaction / panel behavior:**
- Pure logic in `aamatch/wizard_core.py` / `aamatch/wizard_text.py`; cmd-side wiring in `aamatch/wizard.py` (thin adapter — the engine stays the brain). Unit tests in `tests/test_wizard_core.py` / `tests/test_wizard_text.py`; scene proof in a smoke.

**New setup/status UI:**
- Qt in `aamatch/setup_window.py` / `aamatch/game_window.py` (Qt ONLY via `from pymol.Qt import ...`; sibling aamatch imports lazy + relative INSIDE handler methods); pure form glue / text builders in `aamatch/setup_form.py` / `aamatch/status_text.py` so the logic unit-tests in WSL.
- Modal wrapper → non-modal `_X_impl` split so headless smokes drive impls directly.

**New file kind / artifact:**
- Extend `KINDS` in `aamatch/persistence.py:39` and give the kind its own pure parse/validate home (mirror `level_spec.py` / `game_file.py` / `checkpoint.py`): additive fields only (refuse-newer container gate), exact-match gate ONLY where changed semantics break replay (`DETECTOR_VERSION` precedent). Version constants live in the owning module.

**New bundled demo data:**
- Never hand-edit: add/adjust `scripts/demo_specs/<set_id>.json`, run `scripts/build_demos.py`, which regenerates `aamatch/data/ligands/*.sdf` + `aamatch/data/MANIFEST.json` with derived counts + sha256. Integrity is enforced by `tests/test_demo_data.py` / `tests/test_demo_supply.py`.

**Utilities:**
- Pure shared helpers → the matching pure module (vector math → `aamatch/vec3.py`, paths → `aamatch/paths.py`); no catch-all `utils.py` exists — keep single-home law.

## Special Directories

**`.planning/`:**
- Purpose: GSD ("get-shit-done") workflow docs — `PROJECT.md`, `ROADMAP.md`, `STATE.md`, `REQUIREMENTS.md`, `research/` (STACK/ARCHITECTURE/PITFALLS/FEATURES/SUMMARY investigations), `phases/<NN-name>/` (per-plan PLAN/SUMMARY/RESEARCH/VERIFICATION docs). Read `.planning/research/` before non-trivial viewer work.
- Generated: No (hand + orchestrated).
- Committed: Yes (`commit_docs: true`; Conventional Commits with phase-plan scope, e.g. `feat(02-03):`).

**`aamatch/data/`:**
- Purpose: Bundled demo molecules + manifest (see above).
- Generated: Yes — by `scripts/build_demos.py` from `scripts/demo_specs/*.json`.
- Committed: Yes (the regenerated output IS committed; hand edits forbidden).

**`Pymol-script-repo/`, `pymol-src/` (symlinks), `tmp/`, `__pycache__/`, `*.pyc`:**
- Purpose: Prior-art reference, PyMOL source reference, scratch, bytecode.
- Generated: n/a / Yes.
- Committed: No — gitignored; never treat as project code.

---

*Structure analysis: 2026-10-03*
