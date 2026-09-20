---
phase: 06-scoring-lifecycle-endgame
plan: 05
subsystem: wizard
tags: [wizard, lifecycle, scoring, endgame, event-marker, rebind, cmd-tier, headless-smoke, python3.6]

# Dependency graph
requires:
  - phase: 06-scoring-lifecycle-endgame (06-03)
    provides: engine lifecycle ops (guarded record_scored, atomic anchor-preserving advance_level, complete_game/give_up, total_score/is_over)
  - phase: 06-scoring-lifecycle-endgame (06-04)
    provides: gamestart.compose_molecule_view(registry, molecule_index=0) — the ONE compose seam used for level-advance re-framing
  - phase: 05-status-surface
    provides: _state_dict additive-key precedent + status_text.status_events last_event consumption contract
provides:
  - "Wizard lifecycle event machinery: _event_seq/_last_event/_game_over/_end_state + _set_event/_sync_end_state (plain data, contract 2) + the 3 additive _state_dict keys (last_event/game_over/end_state)"
  - "molecule_scored marker payload shape (consumed by the 06-02 status_text builders): {kind, seq, score, total, molecule_pos (1-based, captured pre-advance), molecule_total, formed, required, extras}"
  - "Confirm return contract (plain dict through _guard): {score, total, advanced: 'molecule'|'level'|None, game_over, summary, level_pos, molecule_pos} — the 06-07 tab consumes game_over/summary"
  - "_advance_after_record: the ONE advancement decision site (molecule | level | complete) moving GameState + wizard books atomically"
  - "_rebind_maps/_rebind_molecule/_rebind_level/_compose_active_molecule seams (06-06 skip/give-up + 06-09 reuse)"
  - "SMOKE-15 PART B (22 checks): wizard-tier confirm/advance/rebind/marker/completion E2E incl. the D6 anchor-untouched assert"
affects: [06-06-wizard-lifecycle-b, 06-07-tab-lifecycle-wiring, 06-09-endgame-screen]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "One-op atomics: GameState + wizard index books move in ONE method (_advance_after_record); capture the COMPLETED molecule's position BEFORE the advance, stamp the marker LAST (poll sees marker + new position in one diff)"
    - "Same-instance level rebind: the polled wizard identity is stable across level advances, so the marker survives to the tab's sync refresh and the timer anchor is untouched by construction"
    - "Op-time mirroring: _game_over/_end_state refreshed by _sync_end_state after every advancing op (wizard ops are the only mutation paths — drift-free by construction); the tab reads plain wizard data, never the engine"

key-files:
  created: []
  modified:
    - aamatch/wizard.py
    - smoke/smoke_15_lifecycle.py
    - smoke/smoke_07_wizard_loop.py

key-decisions:
  - "D3: Confirm advances IMMEDIATELY (spec.md:47 'show ... then move'); _result is CLEARED on advance — the debrief rides the molecule_scored last_event marker into the info box; the panel shows the NEXT molecule (recorded shift from the 04-15 clarification)"
  - "Level advance = SAME-INSTANCE REBIND (deliberate deviation from 06-RESEARCH Q1's new-wizard push): (i) the marker set on the polled instance survives to the tab's sync refresh — a new instance would LOSE the scored event for the level's final molecule; (ii) no msm ORDER-LAW re-run mid-game; (iii) the dying level's color store is cleared WITH its objects; D6's timer-continuation intent holds by construction (activate_game never called mid-game — SMOKE-15 B3 asserts the anchor unchanged)"
  - "Marker mechanism (Q7): _event_seq int + _last_event dict-or-None, plain picklable data; seq makes identical consecutive events distinct under the tab's whole-dict-equality fingerprint"

patterns-established:
  - "advance-then-event ordering: every successful lifecycle op = record -> advance -> sync -> _set_event -> refresh -> plain-data return"
  - "rebind helper pattern: restore-FIRST for in-level advances (objects exist); clear-without-restore for level advances (objects deleted by the engine's scene rebuild)"

# Metrics
duration: 13 min
completed: 2026-09-20
---

# Phase 6 Plan 05: Wizard Lifecycle Core Summary

**Confirm is now the progression spine: guarded record → one-site atomic advance (molecule | level | complete) → molecule_scored event marker, with same-instance level rebinds (timer anchor untouched), the 06-04 camera compose on level advance, and SMOKE-15 PART B proving the whole flow headlessly (50/50 checks incl. 22 new PART B)**

## Performance

- **Duration:** 13 min
- **Started:** 2026-09-20T13:26:31Z
- **Completed:** 2026-09-20T13:39:30Z
- **Tasks:** 3
- **Files modified:** 3

## Accomplishments
- `_event_seq`/`_last_event`/`_game_over`/`_end_state` + `_set_event`/`_sync_end_state` + the three additive `_state_dict` keys give every later lifecycle op (06-06 skip/give-up) and the tab (06-07/06-09) the event channel they consume
- `_confirm_molecule_impl` reworked: `is_over` gate → molecule-scoped detect → guarded `record_scored` (the Phase-3 re-Confirm caveat is CLOSED at the engine's front door) → running total → `_advance_after_record` (the ONLY advancement decision site) → `_sync_end_state` → `molecule_scored` marker with the captured pre-advance position → plain-dict return through `_guard`
- SMOKE-15 PART B (22 checks) proves headlessly: molecule advance (result/selection cleared, required reflects molecule 2), level advance (SAME instance on the stack, timer anchor unchanged, fresh 74-object scene, marker seq 2 pos 2, camera re-framed), rebind pick resolution through the rebuilt maps, and the 6-molecule completion drive ending in `game_over`/`completed` + the exact 06-01 summary keys

## Task Commits

Each task was committed atomically:

1. **Task 1: marker mechanism + _state_dict extension + rebind helpers** — `cd57286` (feat)
2. **Task 2: confirm rework + shared _advance_after_record** — `cd0c3a8` (feat)
3. **Task 3: SMOKE-15 PART B + SMOKE-07 advance-semantics evolution** — `475a575` (test)

## Files Created/Modified
- `aamatch/wizard.py` — 4 new plain-data attrs; `_set_event`/`_sync_end_state`; `_state_dict` + 3 additive keys; `_rebind_maps`/`_rebind_molecule`/`_rebind_level`/`_compose_active_molecule`; reworked `confirm_molecule`/`_confirm_molecule_impl` + new `_advance_after_record`; docstrings updated (caveat closed, D3 recorded; banned-token prose counts untouched)
- `smoke/smoke_15_lifecycle.py` — PART B appended (22 checks, ALWAYS tier, public wizard methods only); verdict line now reports PART A 28 / PART B 22 / TOTAL 50, 0 failures
- `smoke/smoke_07_wizard_loop.py` — PART 0 game now `difficulty_levels: 1` (level-0 difficulty identical under the D>1 formula; Confirm COMPLETES the one-molecule game so PART D's scene survives untouched); PART C's two post-confirm result asserts re-targeted to the advance semantics (return dict + last_event marker; `_result` cleared; panel/prompt still build); the exactly-one-record assert tightened (`len(scores) == 1`)

## Decisions Made
- **D3 + same-instance rebind + marker mechanism** recorded in frontmatter key-decisions (all three were plan-binding, implemented verbatim).
- **SMOKE-07 evolution shape (rule-of-minimal-edit):** keep 1 molecule/level but cut the game to 1 level so the single Confirm takes the COMPLETE path instead of a level advance — level 0's payload/grid/pose is byte-identical under the generator's frac=0 row, PART D stays byte-identical, and only the two deliberately-evolving PART C checks change (per the plan's pre-authorized evolution).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] SMOKE-07's knock-on failure scope was larger than the plan's two-check prediction**
- **Found during:** Task 3 (advance-semantics analysis before the SMOKE-07 edit)
- **Issue:** The plan predicted exactly two expected-fail checks (part-C result asserts). In reality the PART C game has `molecules_per_level: 1` with 3 levels, so under the new advance semantics Confirm triggers a LEVEL advance whose scene rebuild DELETES the level-0 objects PART D asserts against (centroid reads on dead objects) — a third knock-on failure the plan's molecule-advance model missed.
- **Fix:** Evolved PART 0 to `difficulty_levels: 1` inside the same smoke edit (advance → completion, scene intact; level-0 difficulty identical under the guarded D==1 frac=0 branch), so only the two pre-authorized checks change shape; the molecule_scores check kept and tightened to exactly one record (the 06-03 guard owns score-once).
- **Files modified:** smoke/smoke_07_wizard_loop.py
- **Verification:** `bash smoke/run_smoke.sh smoke/smoke_07_wizard_loop.py` → `=== SMOKE-07 PASS ===` (56 check lines PASS, 0 FAIL)
- **Committed in:** `475a575` (Task 3 commit)

---

**Total deviations:** 1 auto-fixed (1 blocking, smoke-evolution shape only; zero production-code changes)
**Impact on plan:** None — production code matches the plan's action list verbatim (the tasks' diffs are exactly the listed members); the fix stayed inside the regression smoke the plan already authorized editing.

## Issues Encountered

None — SMOKE-15 PART B passed 50/50 on the FIRST run; SMOKE-07 re-green after the single evolution edit; WSL suite 826/826 green throughout; PROSE_PIN untouched (test_code_audit is part of the green suite).

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- **06-06 (skip/give-up wizard ops)** reuses `_advance_after_record`, `_sync_end_state`, `_set_event` and the plain-dict-through-_guard return contract; the `is_over` gate pattern is established (06-06 hardens the remaining ops).
- **06-07 (tab wiring)** consumes `confirm_molecule()`'s returned dict (`game_over`/`summary`) and the `_state_dict` `last_event`/`game_over`/`end_state` keys via `status_text.status_events`.
- **06-09 (endgame screen)** consumes the complete-game summary (exact 06-01 keys asserted in SMOKE-15 B5).
- Standing gates green at handoff: 826/826 WSL, SMOKE-15 50/50 (A+B), SMOKE-07 PASS, PROSE_PIN untouched.

---
*Phase: 06-scoring-lifecycle-endgame*
*Completed: 2026-09-20*
