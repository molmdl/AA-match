---
phase: 07-checkpoint-game-file-persistence
plan: 06
subsystem: ui
tags: [pyqt5, pymol, checkpoint, aamz, save-button, t1b-smoke]

# Dependency graph
requires:
  - phase: 07-checkpoint-game-file-persistence
    provides: 07-02 pure checkpoint module (zip I/O + read gates), 07-03 status_text.game_saved_line, 07-04 gamestart capture_checkpoint_snapshot/save_checkpoint + GameWizard.snapshot_books seams (SMOKE-18)
provides:
  - btn_save_game ('Save') on the Game tab, inserted before the stretch (Hint/Confirm/Skip-GiveUp/Restart/Reset/Save)
  - _on_save_game: gate-first thin wrapper (silent no-op before any dialog; pre-dialog elapsed capture; 'game.aamz' default + .aamz auto-append filter; cancel-safe; NO success box -- the info-box line IS the feedback)
  - _save_game_to(path, elapsed): box-free non-modal impl = capture(elapsed) -> save(path, data); Qt tier never touches engine/wizard privates
  - SMOKE-16 PART D (10 checks): labels/tooltip/stretch-law, gate no-op, deterministic verbatim elapsed_at_save == 75.0 through the real read gates
affects: [07-07 import button wiring, 07-10 endgame/re-arm, 07-11 full regression battery, 07-12 human checkpoint]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Save/Import wrapper pattern: pre-dialog value capture -> modal pick in wrapper -> non-modal impl as a pure function of (path, captured-value)"

key-files:
  created: []
  modified:
    - aamatch/game_window.py
    - smoke/smoke_16_tab.py

key-decisions:
  - "(07-06, carried) Save gating on a game_over state = ALLOW -- the gate is ONLY the wizard-live isinstance check; no new refusal wording"
  - "(07-06, carried) Default Save filename 'game.aamz', filter 'AA-match Checkpoint (*.aamz);;All Files (*)', .aamz auto-append (04-09 Decision-2 law)"
  - "(07-06, carried) NO success box -- the status_text.game_saved_line info-box line IS the feedback (v1 game-tab Save precedent)"

patterns-established:
  - "Elapsed-capture doctrine in smoke: re-anchor via GameState.start_timer(time.time() - N) + drive the NON-MODAL impl directly -> sidecar value == N VERBATIM (deterministic pure-function-of-args proof)"

# Metrics
duration: ~10 min
completed: 2026-09-21
---

# Phase 7 Plan 06: Game-Tab Save Button (SCORE-08 UI) Summary

**Game-tab Save button wired through the 07-04 checkpoint seams: gate-first thin wrapper (`_on_save_game`) with pre-dialog elapsed capture driving the box-free `_save_game_to(path, elapsed)` impl, proven headlessly by SMOKE-16 PART D (77/77 incl. verbatim `elapsed_at_save == 75.0` through the real read gates)**

## Performance

- **Duration:** ~10 min
- **Started:** 2026-09-21T19:50:12Z
- **Completed:** 2026-09-21T20:00:36Z
- **Tasks:** 2/2
- **Files modified:** 2

## Accomplishments

- `btn_save_game` ('Save' + pinned tooltip) lives on the Game tab's button row, inserted BEFORE the stretch (row order Hint/Confirm/Skip-GiveUp/Restart/Reset/Save, stretch stays LAST -- the 05-06 OQ-1 no-reflow law; the class docstring's reserved Phase-7 slot).
- `_on_save_game` = the THIN wrapper per the 04-09 _X_impl law: isinstance-gated silent no-op BEFORE any dialog (pre-GO / no-game / post-endgame-popped ALL covered; NO game_over refusal per 07-04 Recorded Decision 3), elapsed captured BEFORE the QFileDialog via the tab's own `_compute_elapsed()` (the v1 capture-before-dialog doctrine), 'game.aamz' default with '.aamz' auto-append, cancel = safe no-op, and the success line `Game saved to <path>.` handler-logged AFTER the impl returns via the pure `status_text.game_saved_line` (07-03 handler-logged law) -- NO success box.
- `_save_game_to(path, elapsed)` = the NON-MODAL, box-free impl (smoke-99 law): a pure function of (path, elapsed) composing `gamestart.capture_checkpoint_snapshot(elapsed)` -> `gamestart.save_checkpoint(path, data)`. The Qt tier never touches engine/wizard privates (zero grep hits).
- SMOKE-16 PART D (10 checks incl. restore): fresh-tab construction pins, the wrapper's headless-safe gate no-op (returns BEFORE any dialog -- the drive is also the connected-slot behavioral evidence), the live-tab elapsed read ~= 75.0 after a public `start_timer` re-anchor, and the deterministic sidecar proof (`read_checkpoint_zip` verifies through the real gates; BOTH members; `elapsed_at_save == 75.0` VERBATIM). The wrapper's dialog path is documented [HUMAN]-only.

## Task Commits

Each task was committed atomically:

1. **Task 1: btn_save_game + _on_save_game wrapper + _save_game_to impl** - `88a93b6` (feat)
2. **Task 2: SMOKE-16 PART D -- save-button T1b drive** - `38a6837` (test)

## Files Created/Modified

- `aamatch/game_window.py` - Save button + thin modal wrapper + non-modal impl; class/module docstrings updated for the 07-06 addition
- `smoke/smoke_16_tab.py` - PART D (10 checks: D1 construction/stretch-law, D2 gate no-op, D3 elapsed-capture determinism through read gates, D4 [HUMAN]-only documentation pin, D5 restore) + docstring header + PART-D tally print

## Decisions Made

All three decisions were pre-recorded in the plan (yolo) and implemented verbatim; nothing new arose:

1. Save gating on game_over = ALLOW (gate = isinstance check ONLY; lossless game_over/end_state/final_time round-trip).
2. Default Save filename = 'game.aamz', filter 'AA-match Checkpoint (*.aamz);;All Files (*)', .aamz extension auto-append.
3. NO success box -- the info-box `Game saved to <path>.` line IS the feedback (v1 precedent); the wrapper captures elapsed BEFORE the dialog (capture-before-dialog doctrine) and logs AFTER the impl returns.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None. SMOKE-16 PART D passed 77/77 on the first run; SMOKE-14 regression PASS; py_compile + 881/881 WSL green.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Wired-pair precedent for 07-07/07-08 (Import button): same _X_impl factoring; the Import line logs AFTER `start_countdown` arms (07-03 Import-line placement law -- the countdown's box clear would wipe a pre-arm line).
- SCORE-08's save half is UI-complete; the wrapper's dialog path (default filename, filter, extension auto-append, success log line, and NO success box) needs a [HUMAN] verify in the Phase-7 GUI checkpoint (07-12) -- headlessly undriven per smoke-99.
- **Note for 07-10 (re-arm):** the Save wrapper/body changes nothing about countdown/endgame state (save never pops, never stops the timer); the re-arm plan inherits a save-capable live-wizard state by construction.
- Full six-smoke regression battery re-verify stays assigned to 07-11 per the wave contract (this plan re-ran SMOKE-16 fully + the plan-named SMOKE-14 only).

---
*Phase: 07-checkpoint-game-file-persistence*
*Completed: 2026-09-21*
