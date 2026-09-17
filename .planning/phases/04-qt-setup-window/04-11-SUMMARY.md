---
phase: 04-qt-setup-window
plan: 11
subsystem: qt-window handlers
tags: [pymol, qt, setup-window, cleanup, wizard-stack, prefix-deletion, headless-smoke]

# Dependency graph
requires:
  - phase: 02-13 placement
    provides: cleanup_game_objects prefix-only deletion returning {'deleted': n}
  - phase: 03-03 wizard
    provides: GameWizard + the canonical cmd.set_wizard() None-pop (C layer pops, own cleanup runs, prior wizard auto-resumes)
  - phase: 03-05 gamestart
    provides: start_game one-call seam returning the live GameWizard
  - phase: 04-qt-setup-window 04-09
    provides: _guard contract + the _X_impl modal-free factoring rule (smoke-99 probe receipt)
provides:
  - _cleanup_now() NON-MODAL impl: pop GameWizard iff top-of-stack, then prefix-only cleanup; returns the deleted count
  - _on_cleanup thin MODAL wrapper (SETUP-09 wired; btn_cleanup connected)
  - module-level `from pymol import cmd` in setup_window.py (Decision 17)
  - SMOKE-11 PART E: start -> cleanup -> exact-scene-restore proof headlessly (research P6 hazard closed)
affects: [04-15 checkpoint B, 04-12 export, 04-13 start]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Wizard pop-first pattern: isinstance(cmd.get_wizard(), GameWizard) gate before the canonical None-pop -- a USER wizard is never popped"
    - "Exact-scene-restore assertion: baseline get_names -> game start -> cleanup -> get_names == baseline (the prefix rule's mechanical proof)"

key-files:
  created: []
  modified:
    - aamatch/setup_window.py
    - smoke/smoke_11_window.py

key-decisions:
  - "Pop-first (Decision 6): GameWizard popped via canonical cmd.set_wizard() iff top-of-stack; the isinstance gate guarantees a user wizard is never popped"
  - "Module-level 'from pymol import cmd' added NOW (Decision 17) -- cleanup is the only handler needing raw cmd; legal in the Qt tier"
  - "Adopted-ligand bookkeeping (placement.py:61-63): ZERO v1 workload recorded -- v1 never adopts user objects, so prefix deletion IS the complete original-scene restore; docstring records the reading, no machinery built"

patterns-established:
  - "Cleanup handler shape: _cleanup_now returns the raw count; _on_cleanup owns the informational QMessageBox (impls never own boxes)"

# Metrics
duration: 16min
completed: 2026-09-17
---

# Phase 4 Plan 11: Cleanup Handler Summary

**SETUP-09 Cleanup button wired: GameWizard pop-first via canonical None-pop (isinstance gate), then prefix-only `_aam_*` deletion with the deleted count surfaced -- SMOKE-11 PART E proves the exact original-scene restore headlessly.**

## Performance

- **Duration:** ~16 min
- **Started:** 2026-09-17T03:34:39Z
- **Completed:** 2026-09-17T03:50:24Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments
- `aamatch/setup_window.py`: module-level `from pymol import cmd` (Decision 17; module docstring import note + 04-05 NOTE updated), `_cleanup_now()` NON-MODAL impl (isinstance GameWizard gate -> canonical `cmd.set_wizard()` None-pop -> `placement.cleanup_game_objects()` -> returns `result['deleted']`; docstring records the adopted-ligand ZERO-workload reading and the user-wizard-never-popped rule), `_on_cleanup` thin MODAL wrapper via `_guard` + `QMessageBox.information` surfacing the count, `btn_cleanup.clicked` connected.
- `smoke/smoke_11_window.py`: SMOKE-11 PART E (ALWAYS-tier; cmd-substance) -- baseline object list -> `gamestart.start_game()` defaults (scene grew by 20 `_aam_*` objects, GameWizard on top) -> `dlg._cleanup_now()` (direct-call equivalent prepared if PART B's dialog is absent) -> `deleted == 20 > 0` -> `cmd.get_names('objects') == baseline` EXACTLY (the prefix rule's proof of original-scene restore) -> `cmd.get_wizard() is None` (pop happened, nothing dangling -- research P6 hazard closed). Gate A2 echo renumbered PART E -> PART F.
- Verifications: `python3.6 -m py_compile aamatch/setup_window.py` green; full WSL suite 688/688 green (both after Task 1 and after Task 2); `bash smoke/run_smoke.sh smoke/smoke_11_window.py 120` prints `=== SMOKE-11 PASS ===` with PART E green (all prior parts still green).

## Task Commits

Each task was committed atomically:

1. **Task 1: module-level cmd import + _cleanup_now + _on_cleanup** - `8b6acd4` (feat)
2. **Task 2: SMOKE-11 PART E cleanup drive** - `155a0d6` (test)

**Plan metadata:** (below -- docs commit)

## Files Created/Modified
- `aamatch/setup_window.py` - module-level cmd import (Decision 17), `_cleanup_now` + `_on_cleanup` (SETUP-09), btn_cleanup connected
- `smoke/smoke_11_window.py` - PART E cleanup drive (exact scene restore + wizard pop), Gate A2 echo renumbered PART F

## Decisions Made
None beyond the plan's frozen decisions - pop-first isinstance gate (Decision 6), module-level cmd import now (Decision 17), adopted-ligand ZERO-workload recorded reading, all executed verbatim.

## Deviations from Plan

None - plan executed exactly as written (all snippets adopted verbatim).

## Issues Encountered
None. First smoke run passed end-to-end; `deleted=20` matches the start log's 2 molecules / 18 AA-slot materialization; baseline was an empty scene and the restore matched exactly.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- Cleanup (SETUP-09) is functionally complete mid-game AND idle: wizard popped iff top-of-stack, only `_aam_*` objects deleted, user objects/user wizards untouched, count surfaced.
- Ready for the remaining wave-5/6 handlers (04-12 export, 04-13 start) and the human checkpoints 04-14/04-15 (checkpoint B now has a wired Cleanup to verify with a real user object alongside a live game).
- `tests/test_code_audit.py` PROSE_PIN untouched: zero banned-token mentions added to prose.

---
*Phase: 04-qt-setup-window*
*Completed: 2026-09-17*
