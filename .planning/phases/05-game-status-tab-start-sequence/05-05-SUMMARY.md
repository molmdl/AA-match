---
phase: 05-game-status-tab-start-sequence
plan: 05
subsystem: gameplay-seam
tags: [pymol, gamestart, deferred-activation, countdown, restart, timer]

# Dependency graph
requires:
  - phase: 03-wizard-interaction
    provides: gamestart.start_game one-call seam, GameWizard (msm ORDER LAW), engine runtime
  - phase: 04-qt-setup-window
    provides: ligand_content threading, _last_export (Decision 4), SMOKE-11 part conventions
provides:
  - start_game(setup, seed, candidates, ligand_content, activate=True) seam
  - gamestart.activate_game(wiz) = the SINGLE GO-time activation home (conditional
    replace re-evaluated at activation + timer anchored from zero)
  - gamestart._last_start module-level initial-state input-tuple store
    (deep-copied setup) for Phase-6 Restart replay
  - SMOKE-11 PART H headless proof of the deferred path (T1a tier)
affects: [05-06 countdown tab mechanics, 05-09 window start rework, 05-10 status surface,
          phase-06 restart/scoring lifecycle]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Deferred activation seam: prepare(activate=False) -> countdown -> activate_game(wiz) at GO (Pattern 2)"
    - "Conditional replace re-evaluated AT ACTIVATION, never cached (03-05 decision re-checked)"
    - "Module-level _last_start INPUT tuple (mirrors Decision-4 _last_export shape, lives in gamestart)"

key-files:
  created: []
  modified:
    - aamatch/gamestart.py
    - smoke/smoke_11_window.py

key-decisions:
  - "activate=True default preserves every existing caller byte-for-byte (SMOKE-08 26 checks green unchanged)"
  - "conditional replace is re-evaluated INSIDE activate_game at activation time -- the stack can change during the countdown"
  - "_last_start lives in gamestart, never in the window's _last_export -- a later export must never corrupt the restart source"
  - "setup is DEEP-COPIED into _last_start (allowed_interactions list aliasing, the 04-09 _reset_impl note)"

patterns-established:
  - "GO-time activation: start_timer(time.time()) wired inside activate_game -- start_timer called in production for the FIRST time"
  - "_last_start: {'setup' deep-copied, 'seed', 'candidates', 'ligand_content'} set after successful compose, before any wizard mutation"

# Metrics
duration: 7 min
completed: 2026-09-18
---

# Phase 5 Plan 05: Deferred-Activation Seam Summary

**gamestart start_game split into prepare(activate=False) + activate_game(wiz) GO step with replace re-evaluated at activation, timer anchored from zero, and a deep-copied _last_start input-tuple store for Phase-6 Restart -- default path proven byte-identical by SMOKE-08**

## Performance

- **Duration:** 7 min
- **Started:** 2026-09-18T18:28:53Z
- **Completed:** 2026-09-18T18:36:30Z
- **Tasks:** 3
- **Files modified:** 2

## Accomplishments
- `start_game(..., activate=True)` seam: `activate=False` prepares the FULL game (cleanup -> new_game -> materialize -> compose/framing) and returns the GameWizard WITHOUT pushing it -- the countdown window is wizard-free (spec.md: "countdown ... then start the game"; pitfall P-1 closed)
- `gamestart.activate_game(wiz)` = THE single GO-time activation home: re-evaluates the conditional replace AT ACTIVATION (03-05's decision re-checked, never cached; the stack can change during the 3-second countdown), pushes the wizard per the msm ORDER LAW, and anchors the per-molecule timer from zero via `engine._current_game().start_timer(time.time())` -- `start_timer` called in production for the first time (one anchor home, research Pattern 2/Q4)
- `gamestart._last_start` module-level store captures `{'setup' DEEP-COPIED, 'seed', 'candidates', 'ligand_content'}` after every successful start and before any wizard mutation (SETUP-11; Phase 6 Restart replays it verbatim, ROADMAP:159; NOT a v1-style backup object -- the inputs fully regenerate the scene)
- DEFAULT path byte-identical: SMOKE-08's 26 checks incl. the msm ORDER-LAW teeth green unchanged; SMOKE-08/SMOKE-10's direct start_game calls untouched
- SMOKE-11 gains ALWAYS-tier T1a PART H (deferred-activation direct drive, 9 checks, exact-scene restore); Gate-A2 echo re-lettered H -> I per the established renumber pattern

## Task Commits

Each task was committed atomically:

1. **Task 1: gamestart deferred-activation seam + _last_start store** - `2a41be2` (feat)
2. **Task 2: SMOKE-11 deferred-activation T1a PART** - `586445d` (test)
3. **Task 3: full gate sweep** - no commit (no fixups needed; all gates green on the two task commits)

**Plan metadata:** `07bba6e` (docs: complete plan)

## Files Created/Modified
- `aamatch/gamestart.py` - activate kwarg + activate_game(wiz) GO home + _last_start store + deferred-activation docstring notes (cmd tier, NO Qt usage, zero banned-token mentions kept)
- `smoke/smoke_11_window.py` - new PART H (9 checks) inserted before the echo; echo re-lettered H -> I; header docstring part list updated; every prior part byte-identical

## Decisions Made
- `import time` at module level beside `math` (consistent with the file's current shape; plan-permitted) and lazy `import copy` inside start_game (3.6-safe; cmd tier may use stdlib freely)
- The pre-compose `prior = cmd.get_wizard()` cache was REMOVED from start_game -- the stack-top read now lives ONLY inside activate_game (comments document the re-check, not the retiree)
- activate_game keeps the plan-prescribed lazy `from . import engine` inside its body even though engine is module-level imported elsewhere in gamestart (module-identity pattern visibility, wizard.py precedent)

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None. All verify commands green on first runs:
- `python3.6 -m py_compile aamatch/*.py` OK (3.6 floor)
- `python3.6 -m unittest discover -s tests -v` 688/688 OK (incl. test_purity + test_code_audit PROSE_PIN + test_wizard_source SCANNED_MODULES)
- SMOKE-08: `=== SMOKE-08 PASS ===` (26 checks, default path byte-identical)
- SMOKE-11: `=== SMOKE-11 PASS ===` (new PART H 9 checks + all prior parts + re-lettered PART I echo)
- gamestart.py: zero banned-token mentions (get_model/matrix_reset/get_object_ttt = 0); zero Qt imports (the 5 'Qt' greps are pre-existing-style prose mentions the plan text itself mandates; test_wizard_source's AST + source gates are the enforced mechanism and pass)
- Task 3 gate sweep required NO fixups, hence no `test(05-05): gate sweep green` commit (plan: commit "if any fixups")

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- ready for wave-mates merging: 05-06 (countdown QTimer mechanics consumes gamestart.activate_game), 05-09 (window start rework drives start_game(activate=False) + reworks SMOKE-11 PART G around _pending_wizard), 05-10 (status surface reads the GO-time anchor)
- downstream consumers: Phase 6 Restart replays `_last_start` verbatim (ROADMAP:159); 05-07's engine.game_status() tolerance for a float timer_anchor on the default path is now REAL (activate_game anchors on EVERY activated start)
- no blockers; the double-activation edge (window GO after a default-path start) resolves via the ORDER-LAW snapshot at push time, unchanged

---
*Phase: 05-game-status-tab-start-sequence*
*Completed: 2026-09-18*
