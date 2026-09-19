---
phase: 06-scoring-lifecycle-endgame
plan: 03
subsystem: engine
tags: [engine, lifecycle, scoring, endgame, cmd-tier, headless-smoke, python3.6]

# Dependency graph
requires:
  - phase: 06-scoring-lifecycle-endgame (06-01)
    provides: GameState end-state fields, stop_timer, has_record guard, keyed score_per_molecule, fail-closed endgame_summary
  - phase: 05-status-surface
    provides: gamestart deferred start seam (_last_start, activate/anchor), game_status read path
provides:
  - engine.record_scored(level, molecule, required, records=None) — the ONE guarded lifecycle record site; refusal text "This molecule already has a recorded result (scored or skipped) -- use Restart to replay the game." (pinned, covers Confirm AND Skip; score_current/confirm byte-identical for probe paths)
  - engine.skip_molecule(level, molecule, required) — detection-at-skip-time partial score via the same record path + skip_count increment
  - engine.advance_molecule() / engine.advance_level() — data-only molecule transition, atomic level rebuild (cleanup -> materialize L+1 via retained _ligand_content -> GameState.advance_level LAST), timer anchor untouched
  - engine.give_up(now=None) / engine.complete_game(now=None) — end-state ops returning the 06-01 summary dict; refuse when already over
  - engine.total_score() / engine.is_over() / engine.endgame_summary() READ accessors (module _ligand_content store retained for uploaded-game re-materialization)
  - SMOKE-15 PART A: cmd-tier lifecycle E2E (28/28) — PART letters left open for 06-05/06-06 wizard/tab halves
affects: [06-05-wizard-lifecycle-ops, 06-06-wizard-lifecycle-b, 06-07..06-09-tab-and-endgame, phase-07-persistence]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Guard-at-the-front-door: lifecycle refusal lives in the NEW op (record_scored), never inside score_current/confirm, so smoke detection probes legitimately re-score"
    - "Fail-closed level-advance ordering: cleanup -> materialize(L+1) -> GameState.advance_level LAST (pure data cannot fail; a materialize failure leaves the book consistent)"
    - "Mutate-then-delegate-to-read: give_up/complete_game set the end state and return the READ-only endgame_summary op, so a read can never change the game"

key-files:
  created:
    - smoke/smoke_15_lifecycle.py
  modified:
    - aamatch/engine.py

key-decisions:
  - "The one-record guard lives in record_scored (engine.py) — not score_current/confirm — because smoke_04/06/07 legitimately re-score molecule (0,0) as detection probes"
  - "advance_molecule is deliberately range-check-free (data-only); the wizard owns last-molecule-ends-level routing"
  - "give_up does NOT score the current molecule (spec.md:44-45 — the partial store is Skip's only)"
  - "Timer anchor untouched by advance_level (the game clock runs across levels; only give_up/complete_game freeze via stop_timer)"

patterns-established:
  - "One guard site covers Confirm+Skip re-record refusals via GameState.has_record"
  - "Cleanup-order hazard (cleaned scene + live stale wizard) is documented residue; Restart is the recovery — advance_level docstring carries it"

# Metrics
duration: 12min
completed: 2026-09-19
---

# Phase 6 Plan 03: Engine Lifecycle Ops Summary

**Engine lifecycle brain: the one-record-guarded record_scored op closing the Phase-3 re-Confirm caveat, skip with partial-score store, atomic anchor-preserving level advance, give-up/complete end states returning the fail-closed 06-01 endgame summary — proven headlessly by SMOKE-15 PART A (28/28) in real PyMOL**

## Performance

- **Duration:** 12 min
- **Started:** 2026-09-19T19:41:46Z
- **Completed:** 2026-09-19T19:53:24Z
- **Tasks:** 3
- **Files modified:** 2

## Accomplishments

- `record_scored` is the ONE lifecycle record site: the D4/Q10 `has_record` guard refuses a second Confirm/Skip with the exact pinned wording, in one check covering BOTH paths; `score_current`/`confirm` stay byte-identical (smoke_04 re-passes unchanged — the probe paths are unaffected)
- `skip_molecule` records the detection-at-skip-time partial score via the same record path (02-10 sanctioned semantics) and increments `skip_count`; `advance_molecule`/`total_score`/`is_over` give the wizard cheap plain-data transitions and gates
- `advance_level` atomically rebuilds L+1 (cleanup → materialize via the retained module `_ligand_content` store → `GameState.advance_level` LAST) with the timer anchor provably untouched; `give_up`/`complete_game` freeze the game and return the exact 11-key 06-01 SCORE-07 summary through the read-only `endgame_summary` op
- SMOKE-15 PART A (28/28 PASS) drives the full lifecycle headlessly: guard refusal with exact text + unchanged state, skip counting, level-advance object counts (74 fresh `_aam_*` objects at L1), zero-anchor-drift, give-up summary contract, restart wipe, and the natural-completion drive with the no-next-level refusal — baseline-EXACT restore afterwards

## Task Commits

Each task was committed atomically:

1. **Task 1: guarded record op + skip + data reads** — `a0eea28` (feat)
2. **Task 2: advance_level + give_up/complete_game + endgame_summary** — `b679e51` (feat)
3. **Task 3: SMOKE-15 creation + PART A** — `6ed7425` (feat)

## Files Created/Modified

- `aamatch/engine.py` — module `_ligand_content` store (retained in new_game for advance_level's uploaded-game re-materialization); ops 9-17: record_scored, skip_molecule, advance_molecule, total_score, is_over, advance_level, give_up, complete_game, endgame_summary + private `_molecule_counts`; module docstring op list grown
- `smoke/smoke_15_lifecycle.py` — NEW: SMOKE-15 PART A (28 count-asserted checks, house style, `=== SMOKE-15 PASS ===` marker)

## Decisions Made

None beyond the plan — every semantic was pinned by the plan/research (D4/Q10 guard wording, 02-10 skip semantics, cleanup-before-materialize ordering, no-anchor-touch rule) and implemented verbatim. The smoke's zero-score record mechanics (grid state → (0.0, [])) held at seed 42 as the plan predicted, keeping score correctness in smoke_04's proven domain.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Smoke drive under-called advance_molecule in PART A5**

- **Found during:** Task 3 (first SMOKE-15 run)
- **Issue:** A5 called `engine.advance_molecule()` once but asserted `current_molecule_index == 2`; with one record (A2) and one skip (A4) the index legitimately reads 2 only after ONE advance per recorded molecule — the check read `level=0 molecule=1` FAIL.
- **Fix:** A5 now advances twice (one per recorded molecule) with the rationale documented in a comment; no engine change — the op behaved exactly as designed (data-only transition).
- **Files modified:** smoke/smoke_15_lifecycle.py
- **Verification:** re-run → `=== SMOKE-15 PASS ===` (28/28)
- **Committed in:** `6ed7425` (Task 3 commit)

---

**Total deviations:** 1 auto-fixed (Rule 1 - bug, smoke-script only; zero engine changes)
**Impact on plan:** None — engine semantics matched the plan on first run; the fix was in the smoke's own drive discipline.

## Issues Encountered

None beyond the single smoke-script fix above. All three tasks passed their gates on the first attempt otherwise.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- **06-05/06-06 (wizard lifecycle halves)** wrap these ops with the state-dict/event machinery and drive SMOKE-15 PART B/C (the PART-letter structure is deliberately left open).
- **06-07..06-09 (tab + endgame screen)** consume the READ ops (`total_score`/`is_over`/`endgame_summary`) and the pinned refusal wording — the tab's Skip/Give-Up handlers can route straight to `skip_molecule`/`give_up` behind the confirmation modals.
- Standing gates green at handoff: 826/826 WSL tests, SMOKE-04 regression PASS (confirm/score_current byte-identical), PROSE_PIN untouched (test_code_audit green without edits).
- No blockers or concerns.

---
*Phase: 06-scoring-lifecycle-endgame*
*Completed: 2026-09-19*
