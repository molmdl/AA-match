# Architecture

**Analysis Date:** 2026-09-12

## Pattern Overview

**Overall:** Strict one-directional dependency layering — a pure, WSL-unit-testable game-logic core, a thin `pymol.cmd` bridge tier, a wizard-based viewer-interaction adapter, and a zero-import `__init__.py` composition root. PyMOL 2.5.0 plugin; single package `aamatch/` installed via PyMOL's Plugin Manager.

**Key Characteristics:**
- **Purity contract, mechanically enforced.** The pure layer (`tests/test_purity.py:87-90` `PURE_MODULES`) imports stdlib + other pure modules ONLY — no `pymol`, no Qt, no numpy, no dataclasses — at module level OR inside any function body. Gate A = AST import scan; Gate B = clean-subprocess import proof per module; Gate D = every `aamatch/*.py` compiles under python3.6. Zero `sys.modules` stubs anywhere in the test suite.
- **The level-spec payload is the single source of truth.** Seed + per-level grids + required interactions + `detector_version` stamp. Nothing re-derives from the seed at replay; reset/recovery REPLAY the spec (`placement.reset_to_grid`), never `cmd.matrix_reset`.
- **Fail-closed everywhere.** All domain errors subclass `ValueError` (`FormatError`, `GenerationError`, `PlacementError`, `EngineError`, `WizardError`); every engine op is count-asserted; a failed start never leaves a silent half-built game.
- **PyMOL holds atoms + sentinels only.** All game knowledge lives in plain Python data (payload, registry, `GameState`); the scene is a materialization of that data, not a store of it.
- **VMD port not present.** The repo contains ONLY the PyMOL side; the VMD Tcl port (`vmd/`) planned in `AGENTS.md` has no directory yet.

## Layers

**Layer 1 — PURE game logic (no pymol, no Qt, no numpy):**
- Purpose: All game rules, math, schemas, I/O discipline — unit-testable in WSL with bare `python3.6` and zero stubs.
- Location: `aamatch/` (15 modules registered in `tests/test_purity.py:87-90`)
- Contains:
  - Schemas/state: `aamatch/setup_state.py` (7-field setup model + `INTERACTION_TYPES` — the ONE enum home), `aamatch/level_spec.py` (level-spec schema + two version gates), `aamatch/game_state.py` (SCORE-01 scoring + `GameState` runtime container), `aamatch/wizard_core.py` (pure wizard logic: slot map, view math, color bookkeeping), `aamatch/wizard_text.py` (pure panel/prompt/result text builders)
  - Game brain: `aamatch/generator.py` (seeded, always-solvable level construction), `aamatch/detector.py` (7-type interaction classification over plain atom records), `aamatch/capability.py` (SINGLE atom/residue typing home), `aamatch/thresholds.py` (SINGLE import point for the approved DETECT-03 threshold table)
  - Foundations: `aamatch/vec3.py` (tuple vector math), `aamatch/spatial.py` (cell-list pruning + brute-force oracle), `aamatch/manifest.py` (bundled-data manifest parse/validate/enumerate), `aamatch/persistence.py` (versioned-container core + atomic JSON I/O), `aamatch/backup.py` (snapshot/restore over an injected store), `aamatch/paths.py` (WSL→Windows path guard + bundled-data resolution)
- Depends on: stdlib whitelist only (`json, os, sys, tempfile, time, hashlib, random, copy, math, io, re, collections, errno, ast, zipfile, shutil, unittest, datetime` — `tests/test_purity.py:98-101`) + sibling pure modules
- Used by: Layer 2 (cmd tier) and the Layer 3 wizard

**Layer 2 — CMD tier (module-level `from pymol import cmd` is LEGAL here, Qt is NEVER):**
- Purpose: The pure/cmd boundary. Reads PyMOL objects into plain data down, materializes plain specs into PyMOL objects up.
- Location: `aamatch/geometry.py`, `aamatch/placement.py`, `aamatch/engine.py`, `aamatch/wizard.py`, `aamatch/gamestart.py`
- Contains:
  - `aamatch/geometry.py` — THE geometry bridge: `extract_game_atoms` + `ligand_bonds` produce the detector-contract records; `bounding_sphere` feeds the generator's `ligand_data`. World-frame only, state-1 only, explicit `space=` dicts, identity = `(object, id)`. NEVER `cmd.get_model` (OOM pitfall).
  - `aamatch/placement.py` — the materializer: `materialize(payload, level_index) -> registry`, `reset_to_grid`, `cleanup_game_objects`. Establishes the name/sentinel conventions and the banned-call list (`matrix_reset`, `get_object_ttt`, `cmd.create`/`cmd.load` onto existing names).
  - `aamatch/engine.py` — the headless operation set (the brain): `new_game`, `materialize`, `place_aa`, `reset_to_grid`, `detect`, `detect_molecule`, `score_current`, `confirm`. Holds module-level runtime state `_payload`, `_registry`, `_game` (`engine.py:93-95`).
  - `aamatch/gamestart.py` — THE single game entry point (`start_game`), the seam both the menu item and the future Qt setup window call.
- Depends on: Layer 1 + `pymol.cmd`. NEVER added to `PURE_MODULES`.
- Used by: Layer 3 wizard and `__init__.py`

**Layer 3 — Viewer interaction adapter (still CMD tier for purity purposes):**
- Purpose: Thin input adapter over the engine. Routes clicks/keys/panel buttons onto engine ops and renders plain-data results as panel/prompt text. NO detection math, NO scoring, NO spec knowledge.
- Location: `aamatch/wizard.py` (`GameWizard(Wizard)`)
- Contains: `do_pick`/`do_key`/`do_select`/panel buttons → `engine.confirm`/`place_aa`/`reset_to_grid`; plain picklable attributes only (session save pickles the wizard stack — base class `__getstate__` strips `self.cmd`); stack-native lifecycle (`cmd.set_wizard(self)` push, panel Done → `cmd.set_wizard()` None pop)
- Depends on: `aamatch.engine` (imported lazily INSIDE methods — keeps `aamatch` vs `pmg_tk.startup.aamatch` identity behavior identical), `geometry`, `setup_state`, `wizard_core`, `wizard_text`
- Used by: `aamatch/gamestart.py` (instantiates, activates)

**Layer 4 — Qt GUI: not yet implemented.** Phase-4 work; will reuse the same `gamestart.start_game` seam (`aamatch/__init__.py:29-39`). Only `pymol.Qt`/PyQt5/numpy ships with PyMOL are permitted deps.

**Layer 0 — PyMOL host:** `pymol.cmd` API, wizard stack, plugin loader (`pymol.plugins` parses the `# Version:` metadata block at the top of `aamatch/__init__.py:1-11`).

**Composition root:**
- Purpose: Plugin entry and menu wiring only; ZERO module-level imports (Gate A2, `tests/test_purity.py:214-230`) so every pure-module test runs with zero stubs
- Location: `aamatch/__init__.py`
- `__init_plugin__(app=None)` lazily imports `pymol.plugins.addmenuitemqt` first (headless `ImportError` path is the design); `run_plugin_gui()` lazily imports `gamestart`

## Data Flow

**Game start (Plugins → AA-match):**
1. `aamatch/__init__.py:run_plugin_gui` → lazy `from . import gamestart` → `gamestart.start_game(setup=None, seed=42, candidates=None)` (`aamatch/gamestart.py:60`)
2. `placement.cleanup_game_objects()` — prefix-only (`_aam_`) deletion; user objects untouched
3. `engine.new_game(spec, seed, candidates)` → `(payload, manifest_entries)` — manifest parsed (`manifest.parse_manifest_dict`), per-candidate `ligand_data` built via temp `_aam_tmp` load → `geometry.bounding_sphere` + `capability.ligand_profile` → temp deleted; generator builds the level-spec payload (fail-closed validation inside)
4. `engine.materialize(payload, 0)` → `placement.materialize` → per-ligand `cmd.load` into `cmd.get_unused_name('_aam_lig')`, per-slot `cmd.fragment` amino-acid objects, world-frame baked poses (`cmd.translate/rotate(..., camera=0)`), sentinels stamped (`segi='AAM'`, `b=-999.0` via `cmd.alter` + `cmd.sort`) → registry {slot_id → (object, sorted atom ids)}
5. `GameWizard(payload, registry, 0, 0).activate(replace=...)` — `replace=1` only when the prior top-of-stack wizard is itself a `GameWizard` (restart hygiene); user wizards are never popped
6. `cmd.zoom('segi AAM', buffer=5.0)` to frame the whole game; returns the live wizard (smokes assert on it)

**Confirm (player clicks Confirm):**
1. `GameWizard` panel button → engine op
2. `engine.detect_molecule(level_index, molecule_index)` — `geometry.extract_game_atoms` restricted to the molecule's ligand + slot objects, bond block remapped (walk position i → `index_to_id[i+1]` → atom id → record position) → pure `detector.detect` → pure `game_state.records_for_molecule` post-filter (cross-molecule scoring guard)
3. `engine.score_current` — pure `game_state.score(required, records)` (fraction of required interaction types formed; binary per type) → stored in `GameState` via `record_molecule_result`
4. Wizard renders score + formed/missing type names via `wizard_text` (text only; selection feedback is RECOLOR ONLY — no lines/dots/CGO)

**Reset to grid:**
1. `engine.reset_to_grid()` → `placement.reset_to_grid(payload, registry, level_index)` — spec REPLAY re-bakes grid poses from the payload. NEVER `cmd.matrix_reset` (it reverts baked coordinates — probe-proven).

**State Management:**
- Truth: the level-spec payload (plain dict, `level_spec.py` schema).
- Runtime: `aamatch/engine.py:93-95` module-level `_payload`, `_registry`, `_game` (`game_state.GameState` — plain data: per-molecule formed types, running score, skip/give-up counters, timer anchor float).
- View: `GameWizard` holds ONLY plain picklable attributes (payload, registry, index ints, slot maps, color store, msm snapshot).
- Scene: PyMOL objects are a projection — identity = `(object_name, atom_id)`; registry reconciles.

## Key Abstractions

**Level-spec payload:**
- Purpose: Shareable source of truth for a generated game (seed + per-level grids + required interactions). Reset/replay/persist all consume it.
- Examples: `aamatch/level_spec.py` (schema + gates), produced by `aamatch/generator.py`, stamped with `DETECTOR_VERSION = 'det-1'` (`aamatch/level_spec.py:60`)
- Pattern: reserved schema, additive-only extension; unknown keys PRESERVED, input never mutated

**Versioned container:**
- Purpose: ONE file format for all AA-match files: `{"magic": "AAMATCH", "version": 1, "kind": <KINDS entry>, "data": {...}}`
- Examples: `aamatch/persistence.py:34-37` (`AAM_MAGIC`, `FORMAT_VERSION`, `KINDS`), `write_json_atomic` (temp+fsync+os.replace), `load_container`
- Pattern: two gates — container/payload `version` refuses only NEWER (accept-older via `.get` defaults); payload `detector_version` requires EXACT match (changed detection semantics make old specs unsolvable)

**Canonical detector record:**
- Purpose: The single result shape flowing from detection through scoring to the debrief UI — scoring reads the SAME records the player will see (no drift). Scoring consumes only `r['type']`, fail-closed on anything outside `setup_state.INTERACTION_TYPES`
- Examples: `aamatch/detector.py` (produces), `aamatch/game_state.py:45-59` (`_validate_records`), `aamatch/game_state.py:88-100` (`records_for_molecule`)

**Placement registry:**
- Purpose: Materialize-time map slot_id → (object, sorted atom ids) — the scene↔spec reconciliation table
- Examples: `aamatch/placement.py:232` (`materialize`), consumed by `engine` ops and the wizard's pick map

**Sentinel + name conventions (the hygiene contract):**
- Every game object is born `cmd.get_unused_name('_aam_<role>')`, role in `{'lig', 'aa', 'tmp'}` — the prefix is the ONLY cleanup selection rule
- Every game atom carries `segi='AAM'` and `b=-999.0` — selectors use `segi AAM` / `b < 0` (never `b -999`, malformed)
- Examples: `aamatch/placement.py:96-97` (`SENTINEL_SEGI`, `SENTINEL_B`), `aamatch/gamestart.py:85`

## Entry Points

**PyMOL plugin entry:**
- Location: `aamatch/__init__.py:16-39` (`__init_plugin__`, `run_plugin_gui`)
- Triggers: PyMOL Plugin Manager install → `Plugins → AA-match`
- Responsibilities: menu registration; delegates to `gamestart.start_game()`. As installed: `pmg_tk.startup.aamatch`; in smokes/direct imports: `aamatch` — NEVER both in one PyMOL session (two module objects → duplicate singletons)

**The game-start seam:**
- Location: `aamatch/gamestart.py:60` (`start_game(setup=None, seed=42, candidates=None)`)
- Triggers: the menu item today, the Phase-4 Qt setup window tomorrow (passes its validated setup through the SAME seam)
- Responsibilities: any state → playable game in one call (cleanup → new_game → materialize → wizard activate → zoom)

**WSL unit tests:**
- Location: `tests/` (discover via `python3.6 -m unittest discover -s tests -v` from repo root)
- Triggers: developer; includes the purity gates `tests/test_purity.py` and the source audit `tests/test_code_audit.py`

**Headless PyMOL smokes (Windows PyMOL proof):**
- Location: `smoke/run_smoke.sh` + `smoke/smoke_NN_*.py`
- Triggers: `bash smoke/run_smoke.sh smoke/smoke_NN_name.py [timeout]` from repo root; runs `cmd.exe /c C:\src\run-conda-pymol.bat -cq` against the REPO copy (repo is Windows-visible via `/mnt/c` — no staging)
- Verdict: grep for `=== SMOKE-NN PASS ===` (exit codes cannot carry verdicts through cmd.exe)

## Error Handling

**Strategy:** Fail-closed, message names the cause. A failed op raises; nothing degrades silently and no half-built game state survives quietly.

**Patterns:**
- One error class per tier, ALL subclasses of `ValueError`: `persistence.FormatError` (`aamatch/persistence.py:40`), `generator.GenerationError` (`aamatch/generator.py:130`), `placement.PlacementError` (`aamatch/placement.py:100`), `engine.EngineError` (`aamatch/engine.py:85`), `wizard.WizardError` (`aamatch/wizard.py:94`). Thrown errors propagate to PyMOL's menu handler, which surfaces the traceback.
- Validation BEFORE write and AGAIN on load (`persistence.save_setup_file`/`load_setup_file`); missing keys forward-filled from `DEFAULTS` (idempotent).
- Count/hygiene asserts in every engine op (e.g. object list unchanged across `new_game`; identity-matrix invariant after every wizard move with `_MATRIX_TOL = 1e-6`, `aamatch/wizard.py:84`).
- Refusal classes for file headers: foreign magic / newer version / misfiled kind / unparseable JSON — each with a distinct, user-facing message (`aamatch/persistence.py:8-12`).

## Cross-Cutting Concerns

**Logging:** No logging framework. Player-facing status goes through `print(...)` to the PyMOL console (e.g. `aamatch/gamestart.py:87-90`) and wizard panel/prompt text via `aamatch/wizard_text.py`.

**Validation:** Schema validation lives at the pure-layer homes — `setup_state.validate_state` (the 7-field setup), `level_spec.parse_level_spec_dict` (gate chain: container → format_version → detector_version → structural minimums), `manifest.parse_manifest_dict`. Inputs are never mutated; unknown keys are preserved.

**Authentication:** Not applicable (offline single-user desktop plugin; no network, no secrets; `*.env`/`secrets.toml` git-ignored defensively).

**Path discipline:** Every file path routes through `aamatch/paths.py` (`to_windows_path`, `package_data_path`) — Windows PyMOL cannot resolve `/mnt/c/...`; the repo is `C:\...`-visible to PyMOL smokes.

**Syntax floor:** All of `aamatch/*.py` written Python-3.6-safe (PyMOL's Windows runtime is 3.9; Gate D compiles under `python3.6`).

---

*Architecture analysis: 2026-09-12*
