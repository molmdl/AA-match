---
phase: 06-scoring-lifecycle-endgame
plan: 01
subsystem: scoring
tags: [game-state, scoring, lifecycle, endgame, pure-layer, tdd, python3.6]

# Dependency graph
requires:
  - phase: 02-scoring-core
    provides: game_state.py (GameState container, score(), record_molecule_result, flat molecule_scores)
  - phase: 05-status-surface
    provides: engine.game_status() read path + SMOKE-14 exact-key pin
provides:
  - GameState end-state fields (game_over, end_state, final_time, score_per_molecule) round-tripping lossless through to_dict/from_dict with accept-older .get defaults
  - GameState.stop_timer(now=None): capture-once + freeze op (Q8), anchor untouched
  - GameState.has_record(level, molecule): Q10 one-record-per-molecule guard primitive
  - GameState.endgame_summary(molecule_counts): fail-closed SCORE-07 payload contract (exact 11 keys)
  - SMOKE-14 exact-11-key engine.game_status() pin (evolved from 7)
affects: [06-03-engine-lifecycle-ops, 06-09-endgame-screen, phase-07-persistence]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "capture-once + freeze stop semantics: stop_timer snapshots final_time once game_over; the anchor stays the pause mechanism's home"
    - "keyed score store written in the SAME call as the flat append: score/molecule views can never drift"
    - "fail-closed endgame payload: record-count laws per end_state (completed = every molecule recorded; gave_up = Q5 current molecule intentionally unrecorded)"

key-files:
  created: []
  modified:
    - aamatch/game_state.py
    - tests/test_game_state.py
    - smoke/smoke_14_status_surface.py

key-decisions:
  - "D8 home: end-state fields + stop_timer + has_record + endgame_summary live in game_state.py (established scoring home; PURE_MODULES registry unchanged)"
  - "D11: keyed score_per_molecule store written by record_molecule_result in the same call as the flat molecule_scores append — per-level aggregation never needs flat slicing"
  - "D9: final_time lives on GameState so Phase 7 can reconstruct a finished game's clock"
  - "Q8: stop = capture final elapsed ONCE + freeze; timer_anchor (pause home) is never touched; end_state reason is caller-owned, not set by stop_timer"
  - "endgame_summary takes molecule_counts as an argument (payload-order) because the level structure lives engine-side, not in the pure container"

patterns-established:
  - "Fail-closed record-count laws: end_state implies an exact expected record count; anything else refuses with ValueError naming the cause"
  - "Accept-older from_dict law applied to 4 new keys via .get defaults: pre-06-01 7-key dicts load without KeyError"

# Metrics
duration: 47min
completed: 2026-09-19
---

# Phase 6 Plan 01: GameState Lifecycle Data Layer Summary

**Fail-closed endgame data layer: GameState end-state fields, stop_timer (capture-once + freeze), has_record guard, keyed score_per_molecule store, and the exact-11-key SCORE-07 endgame_summary payload — all pure-layer and WSL-TDD'd, with SMOKE-14's game_status pin evolved to 11 keys**

## Performance

- **Duration:** 47 min
- **Started:** 2026-09-19T18:45:27Z
- **Completed:** 2026-09-19T19:32:51Z
- **Tasks:** 4 (RED, GREEN, smoke pin evolution, verification)
- **Files modified:** 3

## Accomplishments

- GameState now carries the complete game-over story: `game_over` + `end_state` + frozen `final_time` + keyed `score_per_molecule`, all round-tripping losslessly through `to_dict`/`from_dict` with accept-older `.get` defaults (a pre-06-01 7-key dict loads without KeyError)
- `endgame_summary(molecule_counts)` produces the exact SCORE-07 payload (11 keys: end_state, per-level score sums, total, final_time, levels/molecules sizes, molecules_completed, skip/give-up counters, 1-based end position) with fail-closed record-count laws per end_state — consumed verbatim by 06-03's engine read op and 06-09's endgame screen
- The Q10 one-record guard is now derivable (`has_record`), and the Q8 stop semantics are pinned WSL-side (anchor untouched, 0.0-tolerant, clamped, float-coerced)
- WSL suite grew 753 → 785 tests (36 → 71 in test_game_state.py); SMOKE-14 re-passed headlessly with the evolved exact-11-key pin

## Task Commits

Each task was committed atomically (TDD cycle per plan type=tdd):

1. **RED: failing lifecycle battery** — `089eaee` (test) — 35 new-case errors spanning the 7 behavior areas from the plan
2. **GREEN: implement lifecycle data layer** — `b4e3d1d` (feat) — 4 end-state fields, stop_timer, has_record, keyed same-call write, endgame_summary, to_dict/from_dict growth
3. **SMOKE-14 pin evolution** — `21ca64e` (test) — exact 7-key → exact 11-key game_status pin, re-run headlessly: `=== SMOKE-14 PASS ===`

No REFACTOR commit was needed — the GREEN implementation matched the tests and existing house style directly.

## Files Created/Modified

- `aamatch/game_state.py` — +4 end-state fields in `__init__`; `stop_timer` beside `rebase_timer`; `has_record`; same-call keyed write in `record_molecule_result`; `endgame_summary` method; 11-key `to_dict`/accept-older `from_dict`
- `tests/test_game_state.py` — +35 tests: TestEndStateFields, TestStopTimer, TestHasRecord, TestKeyedScoreStore, TestEndgameSummary + evolved round-trip fixture/assertions
- `smoke/smoke_14_status_surface.py` — `_GAME_KEYS` pin grown to the sorted 11-key list; PART-1 prose updated

## Decisions Made

- Followed all plan-binding research resolutions verbatim (D8/D9/D11/Q8 — see context); no new decisions were needed at execution time. `endgame_summary` reads `molecule_counts` as an argument rather than importing payload structure, preserving game_state.py's `time` + `.setup_state`-only import surface (verified by the grep receipt).

## Deviations from Plan

None — plan executed exactly as written. All four must-have truths from the frontmatter hold; files touched are exactly the three listed in `files_modified`.

## Issues Encountered

None. RED failed exactly as expected (35 AttributeError on the new battery), GREEN passed on first implementation, and SMOKE-14 passed on first re-run after the pin evolution.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- **06-03 (engine lifecycle ops)** can wrap these shapes directly: `has_record` for the one-record refusal, `stop_timer` at end, `endgame_summary` behind a thin read-only engine op, and the additive `game_over` key already floats through `engine.game_status()` (the 11-key pin).
- **06-09 (endgame screen)** consumes exactly the `endgame_summary` dict contract.
- **Phase 7 (persistence)** inherits a lossless 11-key GameState dict with accept-older toleration for any pre-06-01 snapshots.
- No blockers or concerns.

---
*Phase: 06-scoring-lifecycle-endgame*
*Completed: 2026-09-19*
