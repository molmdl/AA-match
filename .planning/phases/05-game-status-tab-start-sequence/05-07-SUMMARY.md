---
phase: 05-game-status-tab-start-sequence
plan: 07
subsystem: ui
tags: [pymol, wizard, engine, status-tab, plain-data-snapshot, headless-smoke]

# Dependency graph
requires:
  - phase: 03-gameplay-wizard
    provides: GameWizard._state_dict() plain-data shape + contract 2 (pickle-safe)
  - phase: 02-headless-engine
    provides: engine ops + GameState.to_dict() 7-key snapshot + _current_game guard
  - phase: 05-game-status-tab-start-sequence
    provides: 05-RESEARCH-status-surface.md (researcher B Q6 access path)
provides:
  - GameWizard.get_status() — public plain-data status snapshot for the tab's 1 Hz poll
  - _state_dict() extended additively with level_pos / level_total
  - engine.game_status() — read-only 7-key GameState.to_dict() snapshot, EngineError before new_game
  - smoke/smoke_14_status_surface.py — SMOKE-14 T1a accessor proof (T1b extension slot for plan 05-10)
affects: [05-09, 05-10, phase-06-scoring-lifecycle]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "READ-path accessor pattern: tabs poll public plain-data snapshots (get_status / game_status), never wizard/engine privates, never callbacks onto the wizard (session-save pickle contract)"

key-files:
  created:
    - smoke/smoke_14_status_surface.py
  modified:
    - aamatch/wizard.py
    - aamatch/engine.py

key-decisions:
  - "get_status() returns _state_dict() verbatim (one dict, two consumers): the panel/prompt pure builders read only their own keys and tolerate the additive level_pos/level_total extras (wizard_text.py:209-265)"
  - "timer_anchor None-or-float tolerance in SMOKE-14 is UNCONDITIONAL: same-wave plan 05-05 anchors the timer in the DEFAULT start_game path after merge"

patterns-established:
  - "SMOKE-14 as the status-surface smoke: T1a accessor parts always run (no dialog); T1b surface parts are appended additively by the wiring plan 05-10 under the same verdict marker"

# Metrics
duration: 5 min
completed: 2026-09-18
---

# Phase 5 Plan 7: Status Read Accessors Summary

**Public plain-data status READ path: `GameWizard.get_status()` returning the additively level-extended `_state_dict()`, `engine.game_status()` returning the guarded 7-key GameState snapshot, both proven headlessly by the new SMOKE-14.**

## Performance

- **Duration:** 5 min
- **Started:** 2026-09-18T18:29:15Z
- **Completed:** 2026-09-18T18:33:48Z
- **Tasks:** 2/2
- **Files modified:** 3 (2 modified, 1 created)

## Accomplishments

- `_state_dict()` extended ADDITIVELY with `level_pos` (`_level_index + 1`) and `level_total` (`len(_payload['levels'])`) — plain data, pickle-safe (contract 2); existing pure text builders unaffected (they read only their own keys).
- NEW public `GameWizard.get_status()` — the Game status tab's 1 Hz poll target; the tab never reaches `_state_dict` across modules and never touches wizard/engine privates (05-RESEARCH-status-surface.md anti-patterns closed).
- NEW `engine.game_status()` — read-only `GameState.to_dict()` snapshot (exactly the 7 keys). EngineError before `new_game` inherited from the `_current_game` guard (engine.py:98-103). READ path only: no advance/skip/give-up writes (Phase 6 owns the scoring lifecycle).
- NEW `smoke/smoke_14_status_surface.py` (SMOKE-14 T1a): EngineError-before-game, full shape + level keys, json plain-data proof, mutation-free repeated reads, exact 7-key shape, unconditional timer_anchor tolerance, pre-start-exact teardown — `=== SMOKE-14 PASS ===`.

## Task Commits

Each task was committed atomically on `exec/05-07`:

1. **Task 1: the two additive accessors** — `7a98954` (feat)
2. **Task 2: SMOKE-14 — T1a accessor proof** — `0022969` (test)

**Plan metadata:** see final docs commit (below).

## Files Created/Modified

- `aamatch/wizard.py` — `_state_dict()` gains level_pos/level_total (additive); NEW `get_status()` public accessor (docstring cites the 1 Hz poll + contract 2).
- `aamatch/engine.py` — NEW `game_status()` beside the other public ops (+ an op-8 entry in the module OPS docstring, additive).
- `smoke/smoke_14_status_surface.py` — NEW headless smoke; T1b extension slot documented in its header.

## Decisions Made

- `get_status()` returns `_state_dict()` verbatim rather than a second dict shape: ONE dict serves both the pure text builders and the tab; the level keys are additive so no existing consumer changes (the plan's transcribed fact, confirmed by the green suite).
- SMOKE-14's `timer_anchor` assert is `None or float` with NO condition: plan 05-05 (same wave) anchors the timer at activation in the DEFAULT start_game path, so a merged-tree regression run must pass either reading. Documented in the smoke header.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None. All gates green on first pass:

- `python3.6 -m py_compile aamatch/*.py` — OK.
- `python3.6 -m unittest discover -s tests -v` — 688 tests OK (including `tests/test_purity.py` and `test_code_audit`'s PROSE_PIN exact-mention pins — zero banned-token mentions added).
- `bash smoke/run_smoke.sh smoke/smoke_14_status_surface.py 120` — `=== SMOKE-14 PASS ===` (11/11 checks; level_total=3, molecule_total=2 on the seed-42 defaults).
- `bash smoke/run_smoke.sh smoke/smoke_08_starter.py 120` — `=== SMOKE-08 PASS ===` regression (wizard/engine seam behavior untouched).

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- The READ path the Game status tab polls is public, plain-data, and smoke-proven. Plans 05-09/05-10 (wiring) consume a green read surface; 05-10 appends the T1b status-surface PARTs to SMOKE-14 additively under the same verdict marker.
- Phase 6 inherits `engine.game_status()` as the read path for running scores/counters; no writes landed here by design.

---
*Phase: 05-game-status-tab-start-sequence*
*Completed: 2026-09-18*
