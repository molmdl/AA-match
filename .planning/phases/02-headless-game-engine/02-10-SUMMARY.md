---
phase: 02-headless-game-engine
plan: 10
subsystem: scoring-runtime-state
tags: [pure, score, SCORE-01, game-state, canonical-records, TDD, purity]

# Dependency graph
requires:
  - phase: 02-06
    provides: canonical detector record contract (records carry r['type']; sorted by (INTERACTION_TYPES position, ...))
  - phase: 02-07
    provides: pi_stacking + cation_pi records in the same canonical shape (score is type-agnostic over them)
  - phase: 02-08
    provides: resolved required shape {'mode': 'any'|'list', 'items': [{'type', 'count'}]} (derive_required)
  - phase: 01-05
    provides: setup_state.INTERACTION_TYPES — the ONE enum home (canonical formed-type order)
provides:
  - aamatch/game_state.py — score(required, results) SCORE-01 fraction semantics ('any' binary, 'list' formed/items, binary per item, counts never inflate) + GameState runtime container (position, scores, counters, timer anchor, formed types, lossless to_dict/from_dict)
  - PURE_MODULES = 13 (+ game_state; imports time + setup_state only)
affects: [02-11/02-12 (engine ops consuming score/GameState), 02-14 (E2E), SCORE-02 debrief (reads the SAME records), phase-7 sidecar persistence]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "scoring consumes ONLY r['type'] from canonical records — one source for score and debrief, no drift (SCORE-01/SCORE-02)"
    - "binary per interaction: item formed iff >= 1 record of its type; record counts never inflate (dedupe by type)"
    - "OQ-1 'any'-mode scoping lives in the detector's INPUT, never in score — documented in score's docstring"
    - "record_molecule_result stores score + formed types in ONE call — the two views can never drift apart"
    - "runtime state as plain data only: timer anchor is a stored float; QTimer/rendering is a later Qt phase's job"

key-files:
  created: ["aamatch/game_state.py", "tests/test_game_state.py"]
  modified: ["tests/test_purity.py (PURE_MODULES 12 -> 13 + registration pin test)"]

key-decisions:
  - "Record contract checks fail closed: non-dict record, missing 'type', or 'type' outside INTERACTION_TYPES -> ValueError; unknown mode -> ValueError; empty items in 'list' mode -> ValueError (empty items is the exclusive 'any' representation only)"
  - "Formed types stored per molecule in canonical INTERACTION_TYPES order, deduped — 'list' mode = formed item types; 'any' mode = types the detector produced (its input already scopes to allowed/cross-side interactions)"
  - "start_timer(now=None) defaults to time.time() but callers pass the anchor explicitly — deterministic in tests, wall-clock in the engine; rendering kept out of scope"
  - "to_dict/from_dict must be lossless already (engine/debug surface) even though the formal sidecar container is Phase 7's"
  - "Baseline observed at 438/438 (upstream 02-xx merges after the 423 snapshot), final 464/464"

patterns-established:
  - "score module test fixtures use minimal {'type': t} dicts — type-agnostic over the record shape; a docstring note pins that any canonical record satisfies the contract"
  - "purity-registration pin test per new pure module (generator pattern reused for game_state)"

# Metrics
duration: 15 min
completed: 2026-09-06
---

# Phase 2 Plan 10: Game State / Scoring Summary

**Pure scoring + runtime state (aamatch/game_state.py, 208 lines): score(required, results) implements SCORE-01 ('any' binary -> 1.0 on >=1 record of any type; 'list' = formed items / items; binary per item — record counts never inflate), consuming only r['type'] from the canonical 02-06/02-07 detector records so score and debrief share one source; GameState is a plain-data container (level/molecule position, molecule_scores + total_score, skip/give-up counters, timer anchor, per-molecule formed types in canonical order) with lossless to_dict/from_dict; registered in PURE_MODULES (now 13).**

## Performance

- **Duration:** ~15 min
- **Started:** 2026-09-06T16:45:04Z
- **Completed:** 2026-09-06T17:00:00Z
- **Tasks:** 2/2
- **Files modified:** 3 tracked (aamatch/game_state.py, tests/test_game_state.py, tests/test_purity.py)

## Accomplishments

- **Task 1 (TDD):** score fraction semantics — RED `f5818c2` (13 failing contract cases via import error) -> GREEN `a7bca4c` (score() implemented; all 13 green). Covers: 'any' binary incl. duplicate-records-never-inflate and every-enum-member check; 'list' 0/0.5/1.0 incl. non-item types forming nothing; empty-list-items/unknown-type/missing-type/non-dict/unknown-mode refusals.
- **Task 2 (TDD):** GameState container — RED `bcf4f7f` (10 container + 3 round-trip tests failing on ImportError; 1 purity pin failing) -> GREEN `f93fa38` (container + PURE_MODULES registration; full suite 464/464).
- Purity gates scan aamatch/game_state.py (AST + clean-subprocess); standing gates untouched; suite runs with zero sys.modules stubs as required.

## Test Evidence

- `python3.6 -m py_compile aamatch/*.py` — clean (3.6 floor).
- `python3.6 -m unittest tests.test_game_state -v` after Task 1 GREEN — 13/13 OK.
- `python3.6 -m unittest tests.test_game_state tests.test_purity` after Task 2 RED — FAILED (errors=1, failures=1) as expected; after GREEN — all pass.
- `python3.6 -m unittest discover -s tests` — baseline **438/438**, final **464/464 OK** (brief said 423; the worktree's upstream merges had added 15 generator/detector tests since that snapshot).

## Deviations from Plan

**None — plan executed exactly as written.** No Rule-1/2/3 deviations: the plan anticipated all contract checks (empty list-items refusal, record 'type' validation) and the 'any'/'list' shapes matched derive_required's output verbatim.

Notes (not deviations):

- **Baseline test count:** the orchestrator brief said 423; the worktree base (e475fd6) ran 438 before this plan's first change. Tracked actuals; no weakening of gates.
- **Unknown-mode refusal** is a test case the plan's task-1 action implied ("unknown modes" beyond the named contract checks); implemented fail-closed, consistent with derive_required's refusal style.

## Authentication Gates

None.

## Next Phase Readiness

- 02-12 engine ops can call `GameState.record_molecule_result(level, molecule, required, detect(...))` directly — detect results come back in the canonical record shape scorer consumes.
- Skip semantics note for the engine: SCORE-01 says "skip stores partial score" — a skip path should record the current partial fraction via the same `record_molecule_result` (score is append-only per molecule) and increment `skip_count`.
- Phase 7 sidecar: `to_dict` is already lossless/JSON-able; the formal container format can wrap it without reshaping.
