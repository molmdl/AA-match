# Architecture

**Analysis Date:** 2026-10-03

## Pattern Overview

**Overall:** Layered architecture with a mechanically enforced **pure-core / host-coupled-shells** split. A stdlib-only "pure" layer owns all schemas, chemistry typing, detection, generation, scoring, text building, and file formats; two thin host tiers adapt it to PyMOL (`cmd` tier) and Qt (`pymol.Qt` tier).

**Key Characteristics:**
- **Enforced three-layer purity.** 19 pure modules are registered in `tests/test_purity.py:99` (`PURE_MODULES`) and gate-checked (AST import scan in any scope + clean bare-interpreter subprocess import): no `pymol`, `numpy`, `dataclasses`, `PyQt5`/`PySide2`, `pmg_tk` — stdlib whitelist only (`ALLOWED_STDLIB`, `tests/test_purity.py:113`).
- **Single source of truth per artifact.** All file kinds share ONE versioned container format (`aamatch/persistence.py`); the level-spec payload is the shareable game truth ("embed-don't-regenerate" — regenerate only at fresh generation time).
- **Data-in / decisions-out.** Cmd tier reads PyMOL atoms into plain dicts/tuples and hands them down; pure modules never see the scene (`aamatch/geometry.py` is THE boundary).
- **Thin input adapter.** `aamatch/wizard.py`'s `GameWizard` routes clicks/keys onto engine ops; the engine (`aamatch/engine.py`) is the brain.

## Layers

**Pure layer (19 modules — `PURE_MODULES` in `tests/test_purity.py:99`):**
- Purpose: All deterministic logic — schemas, chemistry, math, text, file formats. Unit-testable in WSL under bare `python3.6` with ZERO `sys.modules` stubs.
- Location: `aamatch/setup_state.py`, `aamatch/level_spec.py`, `aamatch/persistence.py`, `aamatch/backup.py`, `aamatch/paths.py`, `aamatch/vec3.py`, `aamatch/spatial.py`, `aamatch/manifest.py`, `aamatch/capability.py`, `aamatch/thresholds.py`, `aamatch/detector.py`, `aamatch/generator.py`, `aamatch/game_state.py`, `aamatch/wizard_core.py`, `aamatch/wizard_text.py`, `aamatch/setup_form.py`, `aamatch/game_file.py`, `aamatch/status_text.py`, `aamatch/checkpoint.py`
- Contains: constants/tables (`capability`, `thresholds`), tuple math (`vec3`), cell-list pruning (`spatial`), 7-type detection (`detector`), seeded level generation (`generator`), scoring/state (`game_state`), container/`FormatError` (`persistence`), level-spec gates (`level_spec`), manifest parse (`manifest`), setup schema (`setup_state`), game container (`game_file`), checkpoint sidecar + `.aamz` I/O (`checkpoint`), backup lifecycle over an INJECTED store (`backup`), path guards (`paths`), pure wizard/tab logic + text (`wizard_core`, `wizard_text`, `status_text`, `setup_form`).
- Depends on: stdlib whitelist + pure siblings only.
- Used by: both host tiers and the WSL `tests/` suite.

**Cmd tier (host-coupled, `from pymol import cmd` LEGAL at module level):**
- Purpose: Adapt the pure layer to PyMOL session state; own all scene mutation and module-level runtime state.
- Location: `aamatch/engine.py` (the headless op set + runtime state `_payload`/`_registry`/`_game`), `aamatch/geometry.py` (PyMOL objects → plain atom records; the pure/cmd boundary), `aamatch/placement.py` (materializer; builds `_aam_*` objects, grid slots, sentinel tagging `segi AAM` + `b<0`), `aamatch/wizard.py` (`GameWizard`, subclass of `pymol.wizard.Wizard`; thin input adapter), `aamatch/gamestart.py` (THE game lifecycle seam — see Entry Points), `aamatch/upload.py` (uploaded-molecule extraction bridge).
- Contains: module-level engine state, scene composition (camera roll/front-offset laws in `gamestart`), count-asserted ops (`new_game`, `materialize`, `place_aa`, `reset_to_grid`, `detect`/`detect_molecule`, `score_current`, `record_scored`, `confirm`, `skip_molecule`, `advance_molecule`, `advance_level`, `give_up`, `complete_game`, `endgame_summary` — enumerated in `aamatch/engine.py:31-112`).
- Depends on: pure layer + `pymol.cmd`. NO Qt anywhere.
- Used by: Qt tier (via `gamestart` seam only) and headless smokes; NEVER by pure modules.

**Qt tier (`from pymol.Qt import ...` REQUIRED at module level — class definitions need it):**
- Purpose: Modeless windows (setup form + game status tab); dumb renderers that delegate every game action into the cmd-tier seam.
- Location: `aamatch/setup_window.py` (setup singleton `SetupWindow`, 7 buttons + tab host), `aamatch/game_window.py` (`GameTab`: info box, 1 Hz timer tick, Hint/Confirm/Skip/Give-up/Save/Restart/Reset/Import controls).
- Contains: Qt widget construction, `_guard` wrappers catching the ValueError-family refusals, modal-wrapper/non-modal-impl split ("impls never own boxes" so headless smokes drive impls directly).
- Depends on: `pymol.Qt` shim ONLY (vendor binding never imported directly — the shim-only law), cmd tier via lazy relative imports inside handler methods (module-identity law).
- Used by: `aamatch/__init__.py:run_plugin_gui`. Never imported by WSL tests.

## Data Flow

**Fresh game (Plugins menu → playable wizard):**

1. `aamatch/__init__.py:run_plugin_gui` → lazy `from . import setup_window` → `setup_window.open_window()` (singleton, reuse-and-raise).
2. User fills the setup form; Qt handlers validate through pure `setup_state.validate_state` (`aamatch/setup_state.py:90`).
3. Start button `_start_impl` (`aamatch/setup_window.py:995`) → `gamestart.start_game(setup, seed, ...)` (`aamatch/gamestart.py:412`) — THE seam, shared by the menu item and the window.
4. `placement.cleanup_game_objects()` — prefix-only deletion of prior `_aam_*` objects.
5. `engine.new_game(setup, seed)` (`aamatch/engine.py`): parse bundled `aamatch/data/MANIFEST.json` (`manifest.parse_manifest_dict`), enumerate candidates, build per-candidate ligand profiles via a temp `_aam_tmp` load + `geometry.extract_game_atoms` + `capability` typing, then `generator.generate` → **level-spec payload** (seed + per-level grids + resolved required sets + `detector_version` stamp).
6. `engine.materialize(payload, 0)` → `placement.materialize` builds PyMOL objects (ligand + AA grid slots, sentinel-tagged) and returns the **registry** (object name → sorted atom ids).
7. `gamestart.compose_molecule_view` — geometry-first composition: world-space front-offset (`_move_ligand_in_front`), camera roll (`_frame_ligand_above_grid`), final framing `cmd.zoom` LAST.
8. `gamestart._last_start` captures the deep-copied materialization INPUT tuple (`{'setup','seed','candidates','ligand_content','payload'}`) — Restart's replay source.
9. `gamestart.activate_game(wiz)` — one conditional wizard push (`replace=1` iff top-of-stack is a GameWizard) + `GameState.start_timer`.

**Gameplay loop (per molecule):**

1. `GameWizard` click/key handlers (`aamatch/wizard.py`) → engine ops: `place_aa` (translate slot object), detect/score via `detect_molecule` (molecule-scoped).
2. Detection: `geometry.extract_game_atoms()` + `geometry.ligand_bonds` → plain records → `detector.detect` (pure, 7 interaction types, `spatial.cross_pairs` cell-list candidates, `thresholds` constants, `capability` typing) → canonical records.
3. Scoring: `game_state.score` via `engine.record_scored` (single lifecycle record site guarded by `GameState.has_record`) — `score_current`, `confirm`, `skip_molecule` compose on top.
4. Progression: `advance_molecule` → recompose view (`compose_molecule_view` with advanced index); `advance_level` = cleanup → materialize(L+1) → `GameState.advance_level` LAST (fail-closed ordering).
5. `game_window.GameTab` 1 Hz poll reads the live wizard's public `get_status()` diffed through pure `status_text.status_events` — the tab stays a dumb renderer.
6. End: `give_up` / `complete_game` freeze the timer (`stop_timer`) and emit the SCORE-07 endgame summary.

**Persistence / sharing (three versioned artifacts, one container law):**

1. Setup file: `persistence.save_setup_file` / `load_setup_file` (validate-on-save AND validate-on-load; kind `'setup'`).
2. Game file (Generate-and-export, kind `'game'`): `game_file.make_game_data` embeds the level-spec payload + base64 `ligand_files` for uploads — Import replays payload-direct through `gamestart.start_game_from_payload` (`aamatch/gamestart.py:496`), NEVER regenerates.
3. Checkpoint (kind `'checkpoint'`, `.aamz` zip = `game.pse` full session + `state.json` sidecar): `gamestart.capture_checkpoint_snapshot` → `checkpoint.build_checkpoint_data` → `gamestart.save_checkpoint` (`cmd.save` full session → `checkpoint.write_checkpoint_zip` atomic). Resume: `gamestart.load_checkpoint` (`aamatch/gamestart.py:646`) — gates FIRST (`checkpoint.read_checkpoint_zip` refusal chain before ANY scene mutation), pop live GameWizard (any module identity), `cmd.load` the `.pse`, sentinel sweep, `checkpoint.reconcile_registry` (never-ghost + completeness gates), `engine.adopt_game` with timer REBASE from `elapsed_at_save`, wizard ADOPT-OR-REBUILD via canonical-registry compare, `_last_start` rebuild.

**State Management:**
- **Engine module state** (`aamatch/engine.py`): `_payload`, `_registry`, `_game` (one `game_state.GameState`). The three are the whole runtime truth; reset/recover REPLAY the spec, never derive from scene.
- **PyMOL scene** holds atoms + sentinels only (`segi AAM`, `b < 0`, `_aam_*` object prefix).
- **Wizard-side**: `GameWizard` carries its own books (`snapshot_books`/`resume_from`: colors, saved `mouse_selection_mode`, player poses) — checkpoint round-trips them.
- **Restart store**: `gamestart._last_start` (module-level dict; payload stored BY IDENTITY for payload-direct replay).

## Key Abstractions

**The level-spec payload:**
- Purpose: Single source of truth for a generated game — seed, per-level difficulty, molecules, resolved `required` sets, grids with slot poses. Fully determines the level; nothing is re-derived from the seed at replay.
- Schema home: `aamatch/level_spec.py:14-35` (reserved shape, additive-only extension; unknown keys PRESERVED, input never mutated).
- Producer: `aamatch/generator.py` (pure, seeded); consumers: `placement.materialize`, `engine` ops, `game_file`/`checkpoint` embedding.

**The versioned container:**
- Purpose: ONE format discipline for every AA-match file: `{"magic": "AAMATCH", "version": 1, "kind": <KINDS entry>, "data": {...}}` where `KINDS = ('setup', 'level_spec', 'game', 'checkpoint', 'manifest')` (`aamatch/persistence.py:39`).
- Examples: `aamatch/persistence.py:46` (`make_container`), `aamatch/persistence.py:63` (`check_container` refusal chain: foreign/newer/misfiled), `aamatch/persistence.py:133` (`peek_kind` — JSON or `.aamz`, header-exact routing for the one-button Import).

**The TWO version gates (never conflated):**
- `FORMAT_VERSION = 1` in `aamatch/persistence.py:37` — container gate: **refuse-newer / accept-older** (additive-only evolution; readers use `.get()` defaults). Parallel payload gates: `LEVEL_SPEC_VERSION` in `aamatch/level_spec.py:61`, `CHECKPOINT_VERSION` in `aamatch/checkpoint.py`, `GAME_VERSION` in `aamatch/game_file.py`, `manifest_version` in `aamatch/manifest.py`.
- `DETECTOR_VERSION = "det-1"` in `aamatch/level_spec.py:60` — **EXACT match both directions**: stale AND newer stamps refused, because changed detection semantics (`aamatch/thresholds.py` constants) make old specs unsolvable, not merely incomplete. Any threshold change is a `DETECTOR_VERSION` bump event (`aamatch/thresholds.py` bump policy).

**Capability typing tables (single homes):**
- `aamatch/capability.py` — THE atom/residue typing home (`AA_RESIDUES`, `AA_TOKENS`, `aa_capable`, `ligand_support`, `METAL_ELEMENTS`, `ligand_profile`); shared by generator (solvability), detector (typing agreement), and the Hint.
- `aamatch/thresholds.py` — THE numeric detection criteria home, each constant carrying a `source:` provenance comment against `docs/DETECTION_THRESHOLDS.md`.
- `aamatch/setup_state.py` — THE setup schema home (`INTERACTION_TYPES` 7-type enum, `DEFAULTS`, clamp constants).

**Backup policy over an injected store:**
- `aamatch/backup.py` — PyMOL Open Source has NO undo; every destructive mutation is snapshot → (discard | restore), with sha256-framed stored bytes and `verify_intact` as the corruption gate. Duck-typed store protocol (`save_bytes`/`load_bytes`/`delete`/`exists`); ships `MemoryStore` and atomic `FileStore`. `BACKUP_OBJECT_PREFIX = '_aam_backup'` reserved for a future cmd-tier adapter.

**Sentinel tagging + registry identity:**
- Game objects are named with the private `_aam_` prefix and tagged `segi AAM` + `b < 0` (`aamatch/placement.py`). The materialize registry maps molecule → `{'ligand': (name, ids), 'slots': {slot_id: (name, ids)}}` — object names + sorted atom ids ARE the identity contract for checkpoint reconcile (`gamestart._canonical_registry` normalizes list/tuple container drift before comparison).

## Entry Points

**PyMOL plugin startup:**
- Location: `aamatch/__init__.py:16` (`__init_plugin__(app=None)`)
- Triggers: PyMOL plugin loader (installed via Plugin Manager; also smokes/direct imports).
- Responsibilities: Registers ONE Plugins-menu item via `from pymol.plugins import addmenuitemqt` → `addmenuitemqt('AA-match', run_plugin_gui)`. The import is INSIDE the function and FIRST (headless `HAVE_QT=False` raises cleanly; avoids the `cmd.extend` restore quirk). `run_plugin_gui` (`aamatch/__init__.py:29`) lazily imports + opens the modeless `SetupWindow`. The leading `# Version: 0.1.0` comment metadata block is LOAD-BEARING (pymol.plugins parses `# Key: value` comment lines at file top, stopping at the first non-# line).

**Game start (THE seam):**
- Location: `aamatch/gamestart.py:412` (`start_game`), `:496` (`start_game_from_payload`), `:393` (`activate_game` — the single activation home for the countdown path), `:646` (`load_checkpoint` resume).
- Triggers: Plugins-menu item, setup-window Start, tab Restart, tab Import, checkpoint Load.
- Contract: one call takes the scene from any state to a playable game; `activate=False` prepares without pushing the wizard (countdown path).

**Headless smokes (Windows PyMOL proof):**
- Location: `smoke/run_smoke.sh` + `smoke/smoke_NN_*.py` (01–21)
- Triggers: manual / per-phase verification — `bash smoke/run_smoke.sh smoke/<script>.py` from repo root.
- Mechanism: `cmd.exe /c "C:\src\run-conda-pymol.bat -cq smoke\<script>.py"`; verdict = grep for `=== SMOKE-NN PASS ===` (exit codes cannot carry verdicts through cmd.exe).

**WSL unit tests:**
- Location: `tests/` — `python3.6 -m unittest discover -s tests -v` from repo root; includes the purity gates (`tests/test_purity.py`) and mechanical code audits (`tests/test_code_audit.py`).
- Also: `python3.6 -m py_compile aamatch/*.py` (3.6 syntax floor; "Gate D" also enforced inside the suite).

## Error Handling

**Strategy:** Fail-closed everywhere. Refusals ride the ValueError family with messages that NAME the cause; unexpected exceptions propagate as bug surfacing.

**Patterns:**
- **Typed refusal hierarchy:** `persistence.FormatError(ValueError)` (foreign/newer/misfiled/unparseable files); `engine.EngineError(ValueError)`; `placement.PlacementError` / `generator.GenerationError` / wizard `WizardError`; `backup.BackupError(Exception)` (missing/corrupt backup). Qt `_guard` wrappers catch the ValueError family per button.
- **Gates before mutation:** checkpoint load runs the full refusal chain BEFORE touching the session (`aamatch/checkpoint.py`); engine ops are count-asserted (object list unchanged across generation); validate-on-save AND validate-on-load (`persistence.save_setup_file`).
- **Atomic file I/O:** `persistence.write_json_atomic` (temp + fsync + `os.replace`, `allow_nan=False`, sort_keys, binary write); `checkpoint.write_checkpoint_zip` same discipline; failed writes leave the original untouched.
- **Never re-derive a missing backup:** `backup.restore`/`verify_intact` raise on missing key — assert, don't re-call (callers route restore failure to regenerate-from-spec; the seeded level spec is the source of truth).
- **Fail-soft only where documented:** degenerate scene composition in `gamestart` keeps materialized geometry (roll + zoom still run); tab handlers are isinstance-gated SILENT no-ops before GO.

## Cross-Cutting Concerns

**Module identity (two import mechanisms, never mix):**
- Installed plugin imports as `pmg_tk.startup.aamatch`; smokes/direct imports as `aamatch`. Two module objects → duplicate singletons. Mitigations: `aamatch/__init__.py` holds ZERO module-level imports (Gate A2, `tests/test_purity.py:229`); Qt modules use lazy relative sibling imports INSIDE handlers (`aamatch/setup_window.py:39`); wizard identity checks go through the module-attribute predicate `wizard.is_game_wizard_any_identity` (used in `gamestart.load_checkpoint` and the tab) rather than bare `isinstance` against one module object.

**WSL→Windows path guard:**
- Every path crossing into Windows PyMOL routes through `paths.to_windows_path` (`aamatch/paths.py:20` — guard, not unconditional transform; `/mnt/c/...` → `C:\...`, idempotent). Bundled data anchors to `paths.package_data_path` (`__file__`-relative, never `os.getcwd()`). Smoke scripts run from the repo-root cwd which cmd.exe maps to a Windows path.

**Logging:** None. No logging framework anywhere (house rule); feedback is the wizard panel, the tab info box, and `print(...)` status lines from `gamestart.start_game` (visible in the PyMOL console / smoke output, e.g. `aamatch/gamestart.py:489`).

**Validation:** Centralized in pure schema modules — `setup_state.validate_state` (fill/clamp/normalize), `level_spec.parse_level_spec_dict` (three-gate chain), `game_file.parse_game_data`, checkpoint's four-gate parse replay — and re-run on EVERY load.

**Timer doctrine:** Per-molecule timer anchored from zero at `activate_game`; `advance_level` deliberately leaves the anchor untouched; checkpoint resume REBASES from `elapsed_at_save` iff the game is not over; game-over freezes `final_time` authoritative.

**Provenance/truthfulness:** Detection constants carry `source:` citations (`aamatch/thresholds.py`); the human-approved gate document is `docs/DETECTION_THRESHOLDS.md`; data sources are vetted in `docs/DATA_SOURCES.md`. Demo data is NEVER hand-edited — `scripts/build_demos.py` regenerates SDF bytes + `aamatch/data/MANIFEST.json` from `scripts/demo_specs/<set_id>.json`.

---

*Architecture analysis: 2026-10-03*
