---
phase: 06-scoring-lifecycle-endgame
plan: 08
subsystem: ui
tags: [qt, game-tab, restart, reset, spec-replay, last-start, deferred-start, game-reset-marker, headless-smoke, python3.6]

# Dependency graph
requires:
  - phase: 05-game-status-tab-start-sequence (05-05/05-09)
    provides: "gamestart._last_start (the deep-copied 4-key input tuple captured after every successful start) + the deferred start sequence (_pop_game_wizard -> start_game(activate=False) -> start_countdown -> GO)"
  - phase: 06-scoring-lifecycle-endgame (06-02)
    provides: "status_text.game_restarted_line() (tab-handler-logged channel, excluded from the poll builder table) + the pinned game_reset line 'Amino acids reset to grid positions (orientations kept).'"
  - phase: 06-scoring-lifecycle-endgame (06-06)
    provides: "the game_reset marker stamped by the wizard's reset_grid (the poll's ONLY reset channel) + the reset-lockdown gate semantics"
  - phase: 06-scoring-lifecycle-endgame (06-07)
    provides: "GameTab._pop_game_wizard helper, the wrapper/impl law (_on_X -> _guard(_X_now)), the sync-refresh pattern, insert-before-stretch row slots"
provides:
  - "Restart button + _on_restart/_restart_now: verbatim _last_start replay through the 05-09 deferred sequence (fail-closed None refusal -> cancel -> pop -> start_game(activate=False) -> countdown -> 'Game restarted.' logged AFTER the arm) -- SCORE-09"
  - "Reset button + _on_reset_grid/_reset_grid_now: isinstance-gated dispatch to the wizard's PUBLIC reset_grid() (PITFALL 6 at the widget layer; NEVER the engine's replay direct) + synchronous poll rendering the game_reset marker line -- SCORE-10"
  - "SMOKE-16 PART B (23 checks): the restart replay E2E (fresh GameState, fresh generation, D7 line placement), the exact None refusal, the reset drive (mechanism + invariants + marker), the H-8 no-wizard silent gate"
affects: [06-09-endgame-screen-modal, 06-10-human-endgame-checkpoint, phase-7-persistence]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Restart = spec replay of the input tuple (PITFALL 9): start_game(activate=False) over the stored 4-key _last_start tuple, never a saved-object/backup restore -- the PITFALL-9 reconciliation lives in handler docstrings (the backup module keeps no Phase-6 role) and is NEVER wired as code"
    - "D7 line placement: handler-logged event lines that must survive a countdown arm log AFTER start_countdown (the arm's box clear is the ordering hazard); the box then reads ['Get ready...', 'Game restarted.']"
    - "Reset ownership: the tab dispatches to the wizard's PUBLIC op behind the isinstance gate (silent None no-op pre-GO, D8/H-8) and renders the marker-driven line via a SYNCHRONOUS _refresh_status() -- house refusals stay on the wizard PANEL"

key-files:
  created: []
  modified:
    - aamatch/game_window.py
    - smoke/smoke_16_tab.py

key-decisions:
  - "Restart is NOT gated behind an active wizard (restart-reset D1): the fail-closed '_last_start is None' refusal fires FIRST, before any pop/cancel/start, so a refusal leaves scene/log/stack untouched; the op works from the post-endgame popped state"
  - "No rebuild pre-checks on the replay (04-13 clean-then-refuse law): the tuple was validated at first start; OSError/ValueError residue (e.g. a deleted fixture) still surfaces through _guard"
  - "The pre-existing dormant-user-wizard stack-hole (restart-reset D6) stays documented-only -- NOT a Phase-6 fix (recorded in the _restart_now docstring)"

patterns-established:
  - "Restart E2E proof shape: stamp the SMOKE-08 marker band on the live generation BEFORE the restart; post-replay, marker-band survivors == 0 with exactly one fresh generation (derived count -- NAME sets can never prove death across same-seed rebuilds)"
  - "Reset invariants battery: target pose (float32 ulp slack) + detect() on-grid -> 0 records (rotation-persist evidence) + marker + pinned line + GameState to_dict / timer-anchor / selection-key equality (Q3b/Q7)"

# Metrics
duration: 12 min
completed: 2026-09-20
---

# Phase 6 Plan 08: Game Tab Lifecycle Controls (Part 2) Summary

**The Game tab's restart/reset half lands: Restart replays the stored `_last_start` input tuple verbatim through the 05-09 deferred sequence (fail-closed None refusal, pop -> prepare -> countdown -> the D7-placed 'Game restarted.' line -> a provably fresh game at GO), Reset routes through the wizard's PUBLIC grid-replay op behind the isinstance gate with the game_reset marker driving the pinned line through the synchronous poll, and SMOKE-16 PART B proves both headlessly (53/53 A+B)**

## Performance

- **Duration:** 12 min
- **Started:** 2026-09-20T14:33:16Z
- **Completed:** 2026-09-20T14:45:36Z
- **Tasks:** 3
- **Files modified:** 2 (1 code + 1 smoke)

## Accomplishments

- **Restart (SCORE-09):** `btn_restart` landed after `btn_skip_menu` (insert-before-stretch law); `_on_restart` -> `_guard(_restart_now)` with NO confirmation warning (spec.md:43-45 requires warnings for Skip/Give Up only, D9). The impl runs the refusal FIRST (exact `ValueError('Restart: no game has been started yet.')`, house-fail-closed before ANY scene touch), then the P-2 pending-start cancel, the P-3 `_pop_game_wizard`, the verbatim `start_game(setup/seed/candidates/ligand_content, activate=False)` replay, the self-healing countdown arm, and ONLY THEN the `'Game restarted.'` line (D7 -- the arm's box clear cannot wipe it; the box reads `['Get ready...', 'Game restarted.']`). At GO `_begin_play` re-anchors the timer from zero and re-seeds `_last_status` over a fresh GameState by construction. The handler docstring carries the PITFALL-9 reconciliation verbatim-class (spec replay IS the mechanism; the backup module keeps no Phase-6 role -- prose only, never wired) and records the D6 dormant-user-wizard stack-hole as documented-only.
- **Reset (SCORE-10):** `btn_reset_grid` (attribute named DISTINCT from the Setup tab's `btn_reset` per the D7 naming law) + `_on_reset_grid` -> `_guard(_reset_grid_now)`. The impl is the reset OWNER LAW at the widget layer: isinstance-gated silent None no-op pre-GO/no-game (D8/H-8), then the wizard's PUBLIC `reset_grid()` -- NEVER the engine's replay direct, never engine/wizard privates (the never-do list pinned in the docstring incl. "no pose data to the poll"). The synchronous `_refresh_status()` afterwards renders the 06-06 game_reset marker through the 06-02 pinned line; the timer keeps running and NO GameState is touched (positions only; rotations persist -- the 03-03 replay law).
- **SMOKE-16 PART B (23 checks, first-run PASS):** B1 construction inventory (texts, tooltips, row order, stretch LAST); B2-B4 the restart E2E (live game + a recorded score + the SMOKE-08 marker-band stamp on all 20 generation objects; `_restart_now` returns True with the replay wizard armed off-stack; the D7 box-order assert; GO brings fresh zeros, marker survivors 0 with exactly one fresh generation, and the previously-moved slot re-baked at 3.19e-07 <= 2.04e-06 tolerance); B5 the exact None refusal with scene/log/stack untouched; B6 the reset drive (move + 90 deg SMOKE-06-recipe rotation -> centroid back at 1.67e-07 <= 2.04e-06, `detect()` 0 records as rotation-persist evidence, the `game_reset` marker + pinned line, GameState to_dict / timer-anchor / selection-key all UNCHANGED); B7 the H-8 silent None gate + EXACT baseline restore.
- **Regressions green:** SMOKE-16 PART A re-ran inside the same verdict (30/30), SMOKE-08 PASS (the replay path re-exercises `start_game`), 826/826 WSL, `py_compile` clean, grep laws hold (zero `engine` private hits in game_window.py; the tab never names the engine's grid replay).

## Task Commits

Each task was committed atomically:

1. **Task 1: Restart button + handler** — `075a3bf` (feat)
2. **Task 2: Reset button + handler** — `80d0d9e` (feat)
3. **Task 3: SMOKE-16 PART B (restart/reset drive)** — `658167e` (test)

## Files Created/Modified

- `aamatch/game_window.py` — `btn_restart` + `_on_restart`/`_restart_now`; `btn_reset_grid` + `_on_reset_grid`/`_reset_grid_now`; module + class docstrings updated (ROLE paragraph with the 06-08 half, button inventory with the D7 naming law)
- `smoke/smoke_16_tab.py` — PART B appended (23 checks, same T1b ZERO-modals drive); docstring updated (06-08 scope, B1-B7 descriptions); verdict line now reports the A/B breakdown

## Decisions Made

- Recorded in frontmatter: refusal-FIRST ordering (untouched scene on the `None` refusal); no rebuild pre-checks on the replay (04-13 clean-then-refuse residue law); the D6 stack-hole stays documented-only.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug / plan-internal contradiction] The restart-line info-box order in the Task 3 sketch was self-inconsistent**

- **Found during:** Task 3 (authoring the B3 assert)
- **Issue:** Task 3 step 2 sketched the assert as `info box == ['Game restarted.', 'Get ready...'] (the line logged after the clear)`. But the plan's OWN Task 1 handler order (countdown arm FIRST, then the log -- restart-reset D7: "log AFTER start_countdown arms (the countdown's box clear would wipe a pre-chain line)") and the plan's must_haves truth ("pop -> start_game -> countdown -> 'Game restarted.' line -> fresh game at GO") both make the box read `['Get ready...', 'Game restarted.']` -- the restart line is the LAST pre-tick entry. The sketched order is only achievable by logging BEFORE the arm, which D7 explicitly forbids (the clear would wipe the line).
- **Fix:** Asserted the D7-decisive order `['Get ready...', 'Game restarted.']` with the rationale pinned in the check name + smoke docstring; the handler followed Task 1 verbatim (arm-then-log).
- **Files modified:** smoke/smoke_16_tab.py
- **Verification:** SMOKE-16 B3 PASS (`lines=['Get ready...', 'Game restarted.']`); full SMOKE-16 A+B 53/53 PASS
- **Committed in:** `658167e` (Task 3 commit)

---

**Total deviations:** 1 auto-fixed (plan-internal contradiction resolved toward the plan's own D7 decision; zero production-code divergence from the plan)
**Impact on plan:** None -- the implemented handler matches the plan's action list verbatim; only the smoke's assert reconciled the two conflicting specs inside the plan.

## Issues Encountered

None -- SMOKE-16 PART B passed 23/23 on the FIRST run embedded in the full 53/53 verdict; SMOKE-08 regression PASS unchanged; 826/826 WSL green throughout; PROSE_PIN and the wizard-source gates untouched (game_window.py was already scanned).

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- **06-09 (endgame screen modal)** consumes: the unchanged wrapper/impl structure on every lifecycle control (its modal-scheduling tail lands on the WRAPPERS only), `_endgame_sequence` + the endgame summary shape, and the restart button's behavior across an ended game (restart works from the post-endgame popped state -- D1).
- **06-10 ([HUMAN] endgame checkpoint)** owns the never-headless tails; B5's exact refusal message is the string the GUI _guard box will show for the no-start Restart press.
- Standing gates green at handoff: 826/826 WSL, SMOKE-16 A+B 53/53 PASS, SMOKE-08 PASS, `py_compile` clean, grep law zero-hit.

---
*Phase: 06-scoring-lifecycle-endgame*
*Completed: 2026-09-20*
