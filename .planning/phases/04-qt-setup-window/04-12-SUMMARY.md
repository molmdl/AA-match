---
phase: 04-qt-setup-window
plan: 12
subsystem: qt-window handlers
tags: [pymol, qt, qfiledialog, export, game-file, seed-policy, shareable-game, smoke]

# Dependency graph
requires:
  - phase: 04-qt-setup-window (04-03)
    provides: game_file container core (make_game_data, parse_game_data 5-gate chain, encode_ligand_files, GAME_VERSION)
  - phase: 04-qt-setup-window (04-10)
    provides: session _uploaded slot (rows/content/path/FILE-sha256/fmt) + upload_ready_for pre-check
  - phase: 04-qt-setup-window (04-02)
    provides: setup_form.build_state with known_set_ids + upload_ready pop
  - phase: 04-qt-setup-window (04-09)
    provides: _guard contract + _X_impl non-modal factoring rule (smoke-99 receipt)
provides:
  - module-level construct-free export_game(state, seed, candidates, ligand_content, path) -> summary line
  - _on_generate_export (QFileDialog 'game.aamatch.json' -> _guard -> success box in wrapper)
  - _export_game_to(path) -> summary (NON-MODAL; fresh random seed, _last_export tuple stored)
  - SMOKE-11 PART F (T1a export -> parse_game_data round-trip) + PART F2 (T1b dialog drive)
affects: [04-13 start, 04-15 checkpoint B]

# Tech tracking
tech-stack:
  added: [stdlib random (module-level import in the Qt tier)]
  patterns:
    - "Export chain: collect -> upload_ready_for -> build_state(known_set_ids from combo) -> fresh random seed -> export_game (engine.new_game -> make_game_data -> save_container kind 'game')"
    - "Summary-return contract: impl returns the success line, the wrapper owns the information box (same save/load shape, smoke-99 law)"

key-files:
  created: []
  modified: [aamatch/setup_window.py, smoke/smoke_11_window.py]

key-decisions:
  - "Decision 4 binding: seed = random.randint(0, 2**31 - 1) per export (generator._SUB_SEED_MAX domain), echoed in the summary line and inside the embedded payload"
  - "_last_export = {'setup', 'seed', 'candidates', 'ligand_content'} stored on the dialog after a successful export for 04-13's Start-after-Generate"
  - "Success box lives in _on_generate_export (the WRAPPER); _export_game_to returns the summary and owns no boxes (smoke-99 law) -- the plan text placed the box inside the impl; graded under the binding _X_impl rule"
  - "Engine side effect documented + benign: engine.new_game replaces engine-module runtime state (_payload/_game/_registry) on export"

patterns-established:
  - "Dialog export impl pattern: NON-MODAL _export_game_to(path) -> summary, driven headlessly by SMOKE-11 PART F2; wrapper adds the user-facing confirmation"

# Metrics
duration: 10min
completed: 2026-09-17
---

# Phase 4 Plan 12: Generate-and-export Handler + SMOKE-11 PART F Summary

**SETUP-08 wired end-to-end: a module-level construct-free `export_game` (engine.new_game -> game_file.make_game_data -> persistence.save_container kind 'game', atomic + to_windows_path-routed, '.aamatch.json' auto-append) with fresh random seed per export shown in the summary, the `_last_export` tuple stored for Start-after-Generate, the session-upload pair reused for the upload flow, and the SMOKE-11 PART F/F2 parse_game_data round-trip proof — SMOKE-11 PASS with the full WSL suite at 688/688.**

## Performance

- **Duration:** ~10 min
- **Started:** 2026-09-17T03:54:31Z
- **Completed:** 2026-09-17T04:04:27Z
- **Tasks:** 2
- **Files modified:** 2 (aamatch/setup_window.py, smoke/smoke_11_window.py)

## Accomplishments

- Module-level, construct-free `export_game(state, seed, candidates, ligand_content, path)` (setup_window.py): lazy `from . import engine, game_file, paths, persistence`; `engine.new_game` generates the full payload (documented benign side effect on engine module state); `make_game_data(state, payload, ligand_files=encode_ligand_files(ligand_content) if ligand_content else None, created_at=strftime)`; `.aamatch.json` auto-append; `save_container(to_windows_path(path), 'game', data)`; returns the summary line with path/seed/levels/molecule placements/source mode. The viewer scene is never touched (no cleanup/materialize/wizard in the export path).
- Dialog side: `self._last_export = None` slot in `__init__`; `_on_generate_export` = `getSaveFileName('Export AA-match Game', 'game.aamatch.json', 'AA-match Game (*.aamatch.json);;All Files (*)')` -> `if path: _guard(lambda: _export_game_to(path))` -> information box in the WRAPPER; `_export_game_to(path)` = collect -> `upload_ready_for` -> `setup_form.build_state(form, known_set_ids=tuple(...itemData(i)...))` -> `random.randint(0, 2**31 - 1)` -> upload branch reuses `self._uploaded['rows']`/`['content']` (else None/None) -> `export_game(...)` -> stores `_last_export` -> returns summary (NON-MODAL). `btn_generate_export` connected.
- SMOKE-11 PART F (T1a, module-level drive, no dialog needed): tmp game file -> `parse_game_data` round-trips the validated setup, on-disk container kind 'game', embedded payload seed echoes 4242, `ligand_texts == {}` for the demo flow, summary names 'seed 4242'. PART F2 (T1b): `dlg._export_game_to(tmp2)` at form defaults stores `_last_export` (fresh int seed 895540957, candidates/ligand_content None). Prior Gate A2 echo renumbered PART F -> PART G (behavior unchanged).

## Task Commits

Each task was committed atomically:

1. **Task 1: module-level export_game + dialog wrapper + _last_export** - `a7749b1` (feat)
2. **Task 2: SMOKE-11 PART F export round-trip (+ PART F2 dialog drive)** - `16211bd` (test)

**Plan metadata:** `<see final docs commit>` (docs: complete plan)

## Files Created/Modified

- `aamatch/setup_window.py` - module-level `import random`; module-level construct-free `export_game`; `_last_export` slot; `_on_generate_export` + NON-MODAL `_export_game_to`; button connection. QT tier (never PURE_MODULES, never WSL-imported; AST source gates only; zero PyQt5/prose-pin violations).
- `smoke/smoke_11_window.py` - PART F (7 checks, T1a) + PART F2 (3 checks, T1b); old Gate A2 part renumbered F -> G; docstring updated.

## Decisions Made

- **(04-DECISIONS #3/#4 binding)** Export filename/ext: default `game.aamatch.json`, filter `AA-match Game (*.aamatch.json);;All Files (*)`, auto-append `.aamatch.json`. Seed: `random.randint(0, 2**31 - 1)` fresh per export, displayed in the success message (Decision 4).
- **Box placement resolved under the binding 04-09 `_X_impl` rule:** the plan text ended `_export_game_to` with `QMessageBox.information(...)`; the smoke-99 law (static/modal QMessageBox BLOCKS under platform=offscreen) forbids a box in any impl a smoke drives, so `_export_game_to` RETURNS the summary and `_on_generate_export` shows the box on a non-None `_guard` result — the same save/load wrapper shape. The dialog wrapper behaves identically to the plan's intent; only the impl stays box-free.
- **Deviation fix (Rule 3):** the plan's smoke recipe state proved generation-infeasible; pinned in the smoke (see Deviations).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Smoke PART F state draw was generation-infeasible**
- **Found during:** Task 2 (SMOKE-11 PART F)
- **Issue:** `setup_form.usable_randomized_state(7, demo_set_id='demo-dev-1')` (the plan's prescriptive recipe) draws `molecules_per_level 9` (needs 9 distinct candidates from a 2-molecule demo set — the generator correctly refuses) and `block_exclusive` with `['h_bond','salt_bridge','cation_pi']` (the demo ligands cannot ALL support cation_pi — generator.py:403-410 correctly refuses). `usable_randomized_state` guarantees a *usable demo_set_id*, not a generation-feasible draw — PART F2's defaults flow (unset + []) IS feasible, which is why the dialog drive passed while the raw randomized drive raised.
- **Fix:** pinned the three fields in the smoke after the randomize call — `molecules_per_level 2` (frozen default; demo-set max), `interaction_mode 'exclusive'`, `allowed_interactions ['h_bond','pi_stacking']` (every demo ligand forms at least one) — with a rationale comment ("the exact fields a user correcting the infeasible draw would do before clicking Export"). Seed-7's randomized `difficulty_levels` (2) is kept. This is test-materialization only; no production-code change.
- **Files modified:** smoke/smoke_11_window.py
- **Verification:** SMOKE-11 PASS; PART F asserts setup/payload-seed/ligand_texts/summary round-trip green.
- **Committed in:** `16211bd` (part of task commit)

---

**Total deviations:** 1 auto-fixed (1 blocking)
**Impact on plan:** Smoke-only materialization fix; the production export_game handler is verbatim per the plan's snippet. No scope creep.

## Issues Encountered

None beyond the deviation above (the two GenerationError refusals were the generator behaving correctly, and were resolved in the smoke).

## Verification Evidence

- T0: `python3.6 -m py_compile aamatch/*.py smoke/smoke_11_window.py` green; full WSL suite 688/688 green.
- T1a/T1b (probe-PASS, platform=offscreen): `bash smoke/run_smoke.sh smoke/smoke_11_window.py 120` prints `=== SMOKE-11 PASS ===` (41 checks, 0 failures; PARTS A-G green incl. PART F 7/7 + PART F2 3/3).
- Static: `export_game` is module-level + construct-free (lazy sibling import; T1a-driven in PART F); `save_container(to_windows_path(path), 'game', data)` single call site; `ligand_files` only from `ligand_content`; NO placement/wizard/materialize references in the export path (cleanup-section references only); extension auto-append present; atomic writer reused (no new writer); `from pymol.Qt`, no `from PyQt5`; zero prose-pin tokens.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- **04-13 (Start, SETUP-10):** consumes `_last_export` — Start replays the exported `(setup, seed, candidates, ligand_content)` when the current built state equals `_last_export['setup']` (Start-after-Generate, Decision 4's EXCEPT clause), else fresh-seeds from the form. The export seed is proven fresh-random int per export; `setup` inside `_last_export` is already build_state-normalized.
- **04-15 checkpoint B:** the human-verify story now covers Browse -> ingest -> form reflection -> Generate-and-export -> the `game.aamatch.json` save dialog + success box in the GUI.
- **Upload-export path:** `_export_game_to`'s upload branch reuses `self._uploaded['rows']`/`['content']`; `build_state`'s upload_ready pre-check (04-10 wiring) refuses un-ingested upload configs BEFORE generation — no scene side effects on refusal.
- **Phase 7 (PERSIST-02 import):** the exported file is exactly the 04-03 container — `load_container(path, 'game')` -> `parse_game_data` gate chain is already the import-consumer contract (proven round-trip here).
- **Engine-side note for future plans:** exporting REPLACES engine module runtime state (a stale in-progress game's `_payload/_game/_registry` is overwritten); documented benign for v1 but 04-13's Start must always re-enter via `start_game`.

---
*Phase: 04-qt-setup-window*
*Completed: 2026-09-17*
