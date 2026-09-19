---
phase: 06-scoring-lifecycle-endgame
plan: 04
subsystem: gamestart
tags: [gamestart, compose-seam, molecule_index, camera-framing, smoke-08, pymol]

# Dependency graph
requires:
  - phase: 03-wizard-gameplay-loop
    provides: gamestart one-call start seam + 03-07 framing laws (zoom-LAST, active-molecule-only, geometry-side front-offset)
  - phase: 05-status-tab-start-sequence
    provides: deferred-activation seam (activate=False / activate_game) + SMOKE-11 PART H deferred-prepare shape
provides:
  - "public compose_molecule_view(registry, molecule_index=0) — the ONE compose home for starts AND Phase-6 molecule/level advances"
  - "molecule_index=0 parameter on the three compose helpers (_active_molecule_selection, _frame_ligand_above_grid, _move_ligand_in_front)"
  - "SMOKE-08 PART 5: index-1 compose proof + default-index byte-identity"
affects: [06-05 wizard lifecycle (re-frame on every molecule/level advance via one call), 06-06 human checkpoint]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Additive molecule_index=0 generalization — default replaces the hardcoded 0 byte-identically; Phase-6 advances pass the advanced index"
    - "ONE compose home — start_game delegates; no composition logic may be duplicated in the wizard"

key-files:
  created: []
  modified:
    - aamatch/gamestart.py
    - smoke/smoke_08_starter.py

key-decisions:
  - "D6 recorded deviation: NO anchor_timer param on activate_game — the adopted Phase-6 design rebinds the SAME wizard at level advance and never calls activate_game mid-game, so the re-anchor hazard is structurally avoided; D6's timer-continuation intent honored, only the mechanism differs"
  - "compose_molecule_view placed immediately after _move_ligand_in_front; start_game:405-407 extracted verbatim (same three calls, same order, default index 0)"

patterns-established:
  - "Compose-parameterization pattern: registry['molecules'][molecule_index] with molecule_index=0 trailing; zero remaining hardcoded molecule-0 reads in compose code"
  - "Smoke deferred-compose proof: activate=False prepare (PART H shape) + explicit compose call + derived-count growth assert (name-based growth reads 0 after same-name regeneration)"

# Metrics
duration: 11 min
completed: 2026-09-19
---

# Phase 6 Plan 04: Gamestart Compose-Seam Generalization Summary

**Public `compose_molecule_view(registry, molecule_index=0)` is now the single compose home — the three molecule-0-hardcoded compose helpers are index-parameterized and SMOKE-08 PART 5 proves an index-1 compose frames molecule 1 only, idempotently, with the default path byte-identical (drift 0.00e+00).**

## Performance

- **Duration:** 11 min
- **Started:** 2026-09-19T18:47:01Z
- **Completed:** 2026-09-19T18:58:31Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments
- The start composition can now frame ANY molecule index of a materialized level, not only molecule 0 (three hardcoded `registry['molecules'][0]` reads gone; `grep "molecules][0]"` returns zero hits).
- One public `compose_molecule_view(registry, molecule_index=0)` owns the compose sequence; `start_game` delegates with the default index (byte-identical default path — SMOKE-08 re-green UNCHANGED before PART 5 was appended).
- The Phase-6 wizard lifecycle (06-05) can re-frame the camera onto a newly advanced molecule through ONE call — no composition logic will be duplicated in the wizard.

## Task Commits

Each task was committed atomically:

1. **Task 1: molecule_index params + compose_molecule_view extraction** - `ab9b2b1` (feat)
2. **Task 2: SMOKE-08 regression + PART 5 (index-1 compose proof)** - `ec83b68` (test)

**Plan metadata:** see final `docs(06-04)` commit below.

## Files Created/Modified
- `aamatch/gamestart.py` — `molecule_index=0` trailing param on the three compose helpers (docstrings updated with the start-path/Phase-6 note); NEW public `compose_molecule_view(registry, molecule_index=0)` carrying the verbatim start sequence parameterized; `start_game` delegates; module docstring PHASE 5/6 NOTE updated (re-framing now available for any molecule index; history kept). `_last_start` capture and `activate_game` untouched (byte-identical).
- `smoke/smoke_08_starter.py` — NEW PART 5 (index-1 compose proof, PART H deferred-prepare shape); determinism/teardown renumbered PART 6/7 (docstring + headers synced); `setup_state` added to the import line.

## Decisions Made
- **D6 anchor_timer deviation RECORDED (deliberate, per plan):** 06-RESEARCH D6 proposed `activate_game(wiz, anchor_timer=True)`. Not implemented: the adopted 06-05 design REBINDS THE SAME WIZARD at level advance and never calls `activate_game` mid-game, so the re-anchor hazard is structurally avoided and the param would be dead code. `activate_game` stays byte-identical; the no-reanchor property is asserted in SMOKE-15 PART B (plan 06-05). D6's timer-continuation intent honored; only the mechanism differs.
- PART 5 inserted as the new PART 5 with determinism→PART 6 and teardown→PART 7 renumbered (the plan names it "new PART 5"; existing check names/code unchanged, comments/docstring/one failure-fallback name synced).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] PART 5 growth/restore asserts used a name-based baseline that the same-name regeneration defeats**
- **Found during:** Task 2 (first PART 5 smoke run: 2 check FAILs)
- **Issue:** The plan's PART H shape compares object-name growth vs a part-local baseline, but at PART 5 entry the scene still holds PART 4's game objects (Done never deletes them), and `start_game`'s cleanup-first regeneration reuses the identical deterministic `_aam_*` names — so name-based growth read 0 and a name-based baseline restore could never match (after cleanup the scene is EMPTY vs the 20-name baseline).
- **Fix:** Growth proven by the DERIVED count (`len(_game_objects()) == _expected_count(wiz5)` — the established instance-vs-name lesson from 03-05); restore compares against the PART-0 pre-start snapshot (`pre_names`) — a mechanically stronger 'baseline EXACTLY'.
- **Files modified:** smoke/smoke_08_starter.py
- **Verification:** SMOKE-08 re-run: 40 checks PASS / 0 FAIL, `=== SMOKE-08 PASS ===`.
- **Committed in:** `ec83b68` (Task 2 commit)
- **Note:** smoke-assert shape only; no production code touched for this.

---

**Total deviations:** 1 auto-fixed (1 bug, smoke-check shape)
**Impact on plan:** The fix preserves the plan's intent exactly (growth + baseline-exact restore proven) using the repo's established instance/count assertion patterns. No production-code scope change.

## Issues Encountered
None beyond the deviation above. The gamestart refactor required zero debugging — py_compile + 753/753 WSL + SMOKE-08-unchanged re-green on the first run after Task 1.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- 06-05 (wizard lifecycle) consumes `compose_molecule_view(registry, molecule_index)` directly for molecule/level advance re-framing — the SCORE-03 groundwork is in place; SMOKE-15 PART B asserts the no-reanchor property there.
- All standing gates green from the worktree: `python3.6 -m py_compile aamatch/*.py` OK; `python3.6 -m unittest discover -s tests -v` 753/753 OK (purity gates, AST gates, EXACT-7-key game_status pin all untouched); SMOKE-08 40/40 PASS with zero FAIL lines.
- PROSE_PIN safe: gamestart.py still carries zero banned-token prose mentions; tests/test_code_audit.py untouched.
- No blockers.

---
*Phase: 06-scoring-lifecycle-endgame*
*Completed: 2026-09-19*
