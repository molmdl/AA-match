---
phase: 05-game-status-tab-start-sequence
plan: 09
subsystem: ui
tags: [pymol, pyqt5, qtabwidget, qtimer, countdown, deferred-activation, wizard-stack]

# Dependency graph
requires:
  - phase: 05-game-status-tab-start-sequence
    provides: 05-05 gamestart activate=False kwarg + activate_game + _last_start;
      05-06 GameTab skeleton (start_countdown/_begin_play/cancel_pending_start)
      + two-tab SetupWindow shell; 04-11 _cleanup_now pop-first pattern;
      04-13 _start_impl ordering law + Decision-4 seed policy
provides:
  - _pop_game_wizard() helper (isinstance pop, deletion excluded) shared by
    _cleanup_now and _start_impl
  - The window-driven deferred start sequence: pop -> prepare(activate=False)
    -> tab switch -> cancellable 3-2-1 countdown -> GO
  - _on_cleanup cancels any pending countdown FIRST (P-2 closed window-side)
  - SMOKE-11 PART G reworked for the deferred drive contract (03-05 precedent)
affects: [phase-05 remaining plans (status surface, import), phase-06 game
  lifecycle (restart replays start through this same sequence), phase-05
  GUI human checkpoint]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "The WINDOW is the sequencer: pop -> start_game(activate=False) ->
      tabs.setCurrentWidget -> start_countdown; the cmd tier stays Qt-free
      (research Q2 answer (c))"
    - "Shared isinstance-pop helper (_pop_game_wizard) reused by cleanup
      (deletion follows) and start (start_game's cleanup-first deletes)"
    - "Cancel-first teardown: _on_cleanup calls cancel_pending_start before
      the guarded cleanup (P-2); restore blocks in smokes do the same"

key-files:
  created: []
  modified:
    - aamatch/setup_window.py
    - smoke/smoke_11_window.py

key-decisions:
  - "_pop_game_wizard() extracted from _cleanup_now's first half as the one
    isinstance-pop home; returns whether a GameWizard was popped (deletion
    always excluded)"
  - "_start_impl now RETURNS the prepared GameWizard (smoke assertion
    handle; previously returned None)"
  - "SMOKE-11 PART G rework recorded as a deliberate evolution (03-05
    precedent): checks survive, the drive sequence moves -- pending-read
    before GO, GO driven via _begin_play"

patterns-established:
  - "Docstring-carried deferred-sequence contract: the four steps + the P-3
    rationale + the unchanged ordering law live in _start_impl's docstring"
  - "Smoke restore blocks cancel the countdown BEFORE popping/cleaning so a
    leaked pending GO can never fire over a restored scene"

# Metrics
duration: ~10min
completed: 2026-09-19
---

# Phase 5 Plan 09: Window-Driven Start Sequence Summary

**The Setup window's Start button now orchestrates the deferred sequence — pops the prior GameWizard, prepares unactivated, switches to the Game status tab, arms the cancellable 3-2-1 countdown — and Cleanup cancels any pending countdown first, with SMOKE-11 PART G reworked to prove the new drive contract.**

## Performance

- **Duration:** ~10 min
- **Started:** 2026-09-19T07:54:51Z
- **Completed:** 2026-09-19T08:04:20Z
- **Tasks:** 3
- **Files modified:** 2

## Accomplishments
- `_pop_game_wizard()` extracted from `_cleanup_now`'s first half (isinstance pop, deletion excluded, returns popped-bool); `_cleanup_now` delegates — SMOKE-11 PART E re-green proves behavior byte-identical.
- `_start_impl` tail reworked to the deferred sequence: `_pop_game_wizard()` (P-3: stale-wizard clicks can never hit objects start_game's cleanup deletes) → `start_game(activate=False)` → `tabs.setCurrentWidget(game_tab)` → `game_tab.start_countdown(wiz)` → `return wiz` (new smoke assertion handle). The collect → upload_ready → build_state → Decision-4 seed-policy prefix is byte-identical; the ORDERING LAW (build_state refusals caught by `_guard` with the scene untouched) is preserved.
- `_on_cleanup` cancels any pending countdown FIRST (`game_tab.cancel_pending_start()`) so Cleanup mid-countdown can never fire a stale GO over deleted objects (P-2).
- SMOKE-11 PART G reworked as a documented deliberate evolution (03-05 precedent): G1 asserts the pending wizard is stored and NOT on the stack, drives GO directly via `_begin_play`, then asserts push + float timer anchor + the GO-time msm ORDER-LAW snapshot; G2 reads seed 31337 from the PENDING wizard's payload BEFORE its GO; G3 unchanged; the restore block cancels pending countdown first. PART G-alt pure chain untouched.

## Task Commits

Each task was committed atomically:

1. **Task 1: _pop_game_wizard helper + deferred _start_impl + cleanup cancel** — `4e2a080` (feat)
2. **Task 2: SMOKE-11 PART G rework** — `f79c237` (test)
3. **Task 3: full gate sweep** — no commit (no fixups needed; all gates green as committed)

**Plan metadata:** `1f8b651` (docs: complete plan)

## Files Created/Modified
- `aamatch/setup_window.py` — `_pop_game_wizard()` new helper; `_cleanup_now` delegates; `_start_impl` deferred sequence + docstring; `_on_cleanup` cancel-first; stale "unconnected Hint" doc mentions corrected
- `smoke/smoke_11_window.py` — PART G header + body reworked for the deferred drive; header docstring part list updated

## Decisions Made
- `_pop_game_wizard()` returns whether a GameWizard was popped, making the single isinstance-pop home reusable by both the cleanup path (deletion follows) and the start path (start_game's cleanup-first step deletes).
- `_start_impl` now returns the prepared GameWizard (was None) — the plan-prescribed smoke assertion handle for the pending-state asserts.
- PART G's evolution is documented in place (header comment): the prior-art 03-05 precedent — existing parts are reworked only when their drive contract changes, the checks survive.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug (stale doc)] Corrected "unconnected Hint button" mentions**
- **Found during:** Task 1 (setup_window.py docstring updates)
- **Issue:** Three docstring/comment mentions in setup_window.py still called the Game tab's Hint button "unconnected" — 05-08 (Hint slice, a prior wave plan) connected it; the stale text contradicted the code.
- **Fix:** Updated the module docstring, the class docstring and the __init__ comment to say the Hint button is connected since 05-08.
- **Files modified:** aamatch/setup_window.py
- **Verification:** Text search confirms no remaining "unconnected" mentions; full suite green.
- **Committed in:** 4e2a080 (Task 1 commit)

---

**Total deviations:** 1 auto-fixed (1 stale-doc bug)
**Impact on plan:** Cosmetic documentation accuracy only. No scope creep.

## Issues Encountered
None — the prior wave's deliverables (05-05/05-06/05-08) fit the plan exactly; the PART G rework ran green on the first execution (one smoke run for Task 2's verify; no iteration needed).

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- SETUP-11's observable start sequence is wired end-to-end: window-Start → wizard-free countdown → GO activation + timer anchor; Cleanup-safe mid-countdown.
- All standing gates green: `python3.6 -m py_compile aamatch/*.py`; 753/753 WSL tests (incl. purity gates); SMOKE-08 PASS (default `activate=True` path untouched by the window work — the window's `activate=False` is its single call site); SMOKE-11 PASS with the reworked PART G; SMOKE-14 PASS.
- The countdown/timer cadence look-feel, the timer freeze under a REAL modal, and the deferred-activation game feel remain for the Phase-5 [HUMAN] GUI checkpoint (per research verification tiers; PITFALL P5 keeps modals out of headless proof).

---
*Phase: 05-game-status-tab-start-sequence*
*Completed: 2026-09-19*
