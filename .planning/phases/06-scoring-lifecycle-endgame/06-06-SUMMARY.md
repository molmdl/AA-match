---
phase: 06-scoring-lifecycle-endgame
plan: 06
subsystem: wizard
tags: [wizard, lifecycle, scoring, endgame, skip, give-up, gating, event-marker, cmd-tier, headless-smoke, python3.6]

# Dependency graph
requires:
  - phase: 06-scoring-lifecycle-endgame (06-05)
    provides: "_advance_after_record (the ONE advancement site) + _sync_end_state/_set_event marker machinery + _rebind helpers + the plain-dict-through-_guard return contract"
  - phase: 06-scoring-lifecycle-endgame (06-03)
    provides: "engine.skip_molecule (record_scored + skip_count, guard-at-front-door law), engine.give_up (freeze end-state summary), engine.is_over/total_score"
  - phase: 06-scoring-lifecycle-endgame (06-02)
    provides: "pinned event payload shapes (molecule_skipped {score,total,molecule_pos,molecule_total}, gave_up {total,molecule_pos,molecule_total,level_pos}, game_reset {}) and the status_text line builders"
provides:
  - "wizard.skip_molecule / wizard.give_up ops: partial-score record through the SAME shared advancement site as Confirm; skip on the last molecule of the last level completes the game; give_up ends the game at the current stage (current molecule NOT scored, summary returned plain through _guard, wizard does NOT pop itself)"
  - "The return contracts for 06-07: skip_molecule() and confirm_molecule() return the SAME dict shape ({score,total,advanced,game_over,summary,level_pos,molecule_pos}); give_up() returns {game_over True, summary, level_pos, molecule_pos} — the tab's endgame sequence consumes it"
  - "_require_playing: the ONE game-over gate home ('The game is over.', pinned wording); every gameplay impl refuses through _guard; do_pick fails SOFT (error line, selection unchanged — never raise into the C-layer pick dispatch)"
  - "game_reset marker on reset_grid — the ONLY channel the status poll sees a reset through (no pose keys in _state_dict, 'result' never fingerprinted)"
  - "SMOKE-15 PART C (24 checks): skip-advance, skip-completes-game, full post-game-over lockdown, give_up data, reset marker + zero GameState touch"
affects: [06-07-tab-lifecycle-wiring, 06-09-endgame-screen]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "One gate home for every gameplay handler: _require_playing() as the FIRST line of each gameplay impl (hard refusal via _guard); do_pick is the single SOFT exception (the C-layer pick dispatch must never see an exception)"
    - "Uniform lifecycle-op return shape: skip returns the EXACT confirm dict shape so 06-07's tab code path is uniform; give_up returns a slimmer endgame tuple (game_over, summary, end position)"
    - "Skip IS Confirm minus the intent: identical record path (engine.skip_molecule = record_scored + skip_count), identical advancement call, identical position-capture-before-advance — zero duplicated logic"

key-files:
  created: []
  modified:
    - aamatch/wizard.py
    - smoke/smoke_15_lifecycle.py
    - smoke/smoke_07_wizard_loop.py

key-decisions:
  - "do_pick's game-over gate is SOFT (pinned wording on the error line + no-op return) while every other handler's gate is HARD (WizardError through _guard): do_pick runs inside the C-layer mouse dispatch, where a raised exception propagates into C code"
  - "The reset proof in regression SMOKE-07 must run MID-GAME now: a completed game (which PART C's D=1 Confirm produces) refutes any post-completion reset/move by the plan's own lockdown law — the proof moved between the placed pose and the completion Confirm, with a re-pose step (rotations persist, 03-03)"

patterns-established:
  - "Every gameplay impl = _require_playing() first, then business logic; every successful lifecycle op ends record -> advance -> sync -> marker -> refresh -> plain-dict return (06-05 shape, inherited verbatim by skip/give_up)"

# Metrics
duration: 17 min
completed: 2026-09-20
---

# Phase 6 Plan 06: Wizard Skip/Give-Up Half Summary

**The wizard's lifecycle termination + protection half: skip_molecule and give_up ops riding the 06-05 shared advancement site (a skipped final molecule still completes the game), one `_require_playing('The game is over.')` gate across every gameplay handler with a SOFT do_pick variant, the game_reset marker on reset_grid, and SMOKE-15 PART C proving the whole surface headlessly (74/74 checks incl. 24 new PART C)**

## Performance

- **Duration:** 17 min
- **Started:** 2026-09-20T13:45Z
- **Completed:** 2026-09-20T14:02Z
- **Tasks:** 3
- **Files modified:** 3

## Accomplishments

- `skip_molecule()` (SCORE-05 wizard half): partial score recorded at skip time through the SAME record path as Confirm (`engine.skip_molecule` = `record_scored` + `skip_count`), then advanced through the ONE shared `_advance_after_record` site — a skip on the last molecule of the last level completes the game with `end_state 'completed'`; `molecule_skipped` marker stamped with the captured pre-advance position; returns the exact confirm dict shape so 06-07's tab path is uniform
- `give_up()` (SCORE-06 wizard half): ends the game at the current stage (the current molecule is NOT scored — spec.md:44-45), freezes the timer, stamps the `gave_up` marker `{total, molecule_pos, molecule_total, level_pos}`, returns `{game_over: True, summary, level_pos, molecule_pos}` plain through `_guard`; the wizard does NOT pop itself (the tab's endgame sequence owns the pop)
- `_require_playing()` = the single game-over gate home: hard refusal (WizardError, pinned `'The game is over.'` wording visible on the panel via `_guard`) at the top of nudge/rotate/step/move_to/hint/reset_grid/confirm (replacing 06-05's inline gate)/skip/give_up; do_pick gets the documented SOFT variant (selection unchanged, never raise into the C-layer pick dispatch)
- `reset_grid` now stamps the `game_reset` marker — the poll's ONLY reset channel since `_state_dict` carries no pose keys and `'result'` is never fingerprinted
- SMOKE-15 PART C (24 checks, ALWAYS tier, public wizard methods only) proves skip-advance, skip-completes-game, the full post-game-over lockdown (movement pose-unchanged at dev=0, hint/reset/skip/confirm None-through-guard, soft no-op scripted pick), give_up data + frozen final_time, and the reset marker with ZERO GameState touch (to_dict equality)

## Task Commits

Each task was committed atomically:

1. **Task 1: skip_molecule wizard op (shared advancement)** — `9d2e4a3` (feat)
2. **Task 2: give_up wizard op + game-over gating + game_reset marker** — `42b238d` (feat)
3. **Task 3: SMOKE-15 PART C + SMOKE-07 reset-proof migration** — `7d1ab17` (test)

## Files Created/Modified

- `aamatch/wizard.py` — `skip_molecule`/`_skip_molecule_impl`; `give_up`/`_give_up_impl`; `_require_playing` gate + 9 call sites (movement ×4, hint, reset_grid, confirm, skip, give_up); do_pick SOFT game-over gate; `game_reset` marker in `_reset_grid_impl`; docstrings (spec.md:44-45 semantics, warning-ownership notes, no-self-pop law, soft-gate rationale)
- `smoke/smoke_15_lifecycle.py` — PART C appended (24 checks: C1 skip-advance, C2 skip-completes-game, C3 lockdown, C4 give_up data, C5 reset marker + zero GameState touch, C6 restore); docstring + verdict line updated (A 28 / B 22 / C 24 / TOTAL 74)
- `smoke/smoke_07_wizard_loop.py` — reset proof moved MID-GAME into PART C (between the placed pose and the completion Confirm) with a new re-pose check; PART D reduced to the Done restore table; all original check names preserved; 57 PASS lines (+1 re-pose check)

## Decisions Made

- **do_pick fails SOFT, everything else fails HARD (Rule-from-plan):** a raised exception inside do_pick would propagate into the C-layer mouse pick dispatch — its game-over gate sets the error line and returns with the selection unchanged; every other handler's gate is a WizardError through `_guard`.
- **Skip returns the confirm dict shape:** `{score, total, advanced, game_over, summary, level_pos, molecule_pos}` — 06-07's tab code consumes one uniform contract; give_up's slimmer `{game_over, summary, level_pos, molecule_pos}` is its own contract (no score exists — the current molecule is not scored).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug / knock-on] SMOKE-07's reset proof collided with the plan's own game-over lockdown law**

- **Found during:** Task 3 verification (SMOKE-07 regression re-run, required by the plan's `<verification>` section)
- **Issue:** 06-05's evolution made SMOKE-07's PART C Confirm COMPLETE its one-molecule D=1 game; PART D then called `reset_grid`, which Task 2's `_require_playing` correctly refuses (`'The game is over.'`). The reset never replayed → `reset_grid replays grid positions` (worst dev 9 Å) and `reset clears the interaction` (pi records persist) both FAILED. The 06-06 locks are working exactly as designed — the regression smoke's order had become impossible.
- **Fix:** Moved the reset proof INTO PART C, mid-game — between the placed pose and the completion Confirm (reset replay, interaction-cleared, identity matrices, selection/recolor-persist checks preserved under their original names), then a new `re-pose after reset lands the ring again` check (rotations persist per the 03-03 decision, so the same placement vector re-lands the ring), then the completion Confirm. PART D now holds only the Done restore table. Zero production-code changes.
- **Files modified:** smoke/smoke_07_wizard_loop.py
- **Verification:** `bash smoke/run_smoke.sh smoke/smoke_07_wizard_loop.py` → `=== SMOKE-07 PASS ===` (57 PASS lines, 0 FAIL); SMOKE-15 re-run → `=== SMOKE-15 PASS ===` (74 checks)
- **Committed in:** `7d1ab17` (Task 3 commit)

---

**Total deviations:** 1 auto-fixed (1 knock-on smoke evolution; nothing in `aamatch/` changed)
**Impact on plan:** None — production code matches the plan's action list verbatim; the fix stayed inside the regression smoke the plan instructs to re-run, following the 06-05 minimal-evolution precedent.

## Issues Encountered

None beyond the single SMOKE-07 knock-on above (which passed clean once reordered). Note: PART C of SMOKE-15 passed 24/24 on the FIRST run; WSL suite 826/826 green throughout; PROSE_PIN untouched (test_code_audit is part of the green suite).

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- **06-07 (tab lifecycle wiring)** consumes: `confirm_molecule()`/`skip_molecule()`'s uniform return dict (game_over/summary), `give_up()`'s endgame tuple for its endgame sequence (which owns the wizard pop), the `last_event`/marker kinds (molecule_skipped/gave_up/game_reset) via `status_text`'s pinned 06-02 builders, and the pinned gate wording `'The game is over.'`. The confirmation warnings belong to the tab wrapper (wizard ops are the Yes-branches — documented in each op's docstring).
- **06-09 (endgame screen)** consumes the same give_up/completion summary (exact 06-01 keys asserted in SMOKE-15 C4/B5).
- Standing gates green at handoff: 826/826 WSL, `python3.6 -m py_compile aamatch/*.py` clean, SMOKE-15 74/74 (A+B+C) PASS, SMOKE-07 57-check PASS, PROSE_PIN untouched.

---
*Phase: 06-scoring-lifecycle-endgame*
*Completed: 2026-09-20*
