---
phase: 09-help-docs-release-audit
plan: 02
subsystem: testing
tags: [smoke, perf-budget, pymol, headless, gamestart, wizard, drag, generate]

# Dependency graph
requires:
  - phase: 02-materialization-and-detection
    provides: gamestart.start_game path, manifest.largest_entry selector, placement/engine materialize, smoke_05 harness law
  - phase: 08.3-drag-movement-pivot
    provides: GameWizard.drag_move programmatic twin + 82-object level-9 scene precedents

provides:
  - smoke/smoke_25_perf_budgets.py — headless Phase-9 perf-budget battery (roadmap criterion 4 machine half)
  - Dated receipt: Generate < 30 s on NAD and on the max-legal manifest workload; pick/drag < 200 ms min/avg/max on the 82-object scene

affects: [09-11 (human feel half), 09-13 (final-build battery re-run)]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "smoke_05 harness law re-used verbatim: sys.argv repo-root anchor, one-line flushed prints, check(), local budget literals, SMOKE-ENV raw-number lines, single PASS marker"
    - "Non-vacuity guards on every measured row: object-count asserts (G/W/S), switch-path assert (P), centroid-displacement assert (D)"

key-files:
  created:
    - smoke/smoke_25_perf_budgets.py
  modified: []

key-decisions:
  - "Generate = one full gamestart.start_game (superset of the export path), timed cold; warm echoed only"
  - "Max legal manifest workload = demo_set_id '' + mPL 4 + D 10 (re-derived from the 14/4/0 size census; a GenerationError fails the row)"
  - "Pick/drag timed with stdlib time.time() per the research harness law; the Windows ~15.6 ms clock tick means sub-tick ops read 0.000 ms"
  - "Drag row carries a non-vacuity displacement assert so a silent no-op cannot record 0 ms"

patterns-established:
  - "SMOKE-25 is additive (roster now 01-25); smoke_05 stays byte-untouched as the self-adapting control"
  - "Tier law: WSL asserts nothing for these budgets; the headless smoke asserts the raw budgets"

# Metrics
duration: ~27 min
completed: 2026-11-18
---

# Phase 9 Plan 02: SMOKE-25 Perf-Budget Battery Summary

**Headless SMOKE-25 proves criterion 4's machine half: Generate 31 ms cold on NAD and 160 ms at the max-legal 18-candidate / mPL-4 / D-10 workload (both < 30 s); 20-rep scripted pick and drag on the 82-object level-9 scene report max 16 ms and 0 ms (both < 200 ms), every raw number echoed.**

## Performance

- **Duration:** ~27 min
- **Started:** 2026-11-18T04:20+08:00 (approx.)
- **Completed:** 2026-11-18T04:47+08:00
- **Tasks:** 3
- **Files modified:** 1 created (`smoke/smoke_25_perf_budgets.py`); zero existing files touched

## Task Commits

1. **Task 1: legality pre-flight probe** — no commit (file is `tmp/probe_25_legality.py`, git-ignored by repo convention; receipt below)
2. **Task 2: author SMOKE-25** — `df99bb0` (test)
3. **Task 3: run + non-vacuity strengthening** — `3b86ea9` (test; Rule-2 fix)

**Plan metadata:** (this docs commit) — SUMMARY + STATE

## Receipt — SMOKE-25 run (2026-11-18, headless Windows PyMOL 2.5.0 / Python 3.9.13)

Command: `bash smoke/run_smoke.sh smoke/smoke_25_perf_budgets.py 240`

```
=== SMOKE-25 PASS ===
SMOKE-ENV perf25 generate_cold_ms=31 generate_warm_ms=31
SMOKE-ENV perf25 workload_ms=160
SMOKE-ENV perf25 heavy_objects=82
SMOKE-ENV perf25 pick_min_ms=0 pick_avg_ms=4 pick_max_ms=16
SMOKE-ENV perf25 drag_min_ms=0 drag_avg_ms=0 drag_max_ms=0
```

Failed checks: none. Full check roster (all PASS): clean pre-game scene;
G largest_entry selects demo-hard-3/nad (heavy 44 of 18 entries); G
level-0 growth == 10 objects; G cold generate < 30 s; G warm generate
echoed; W level-0 growth == 40 objects; W max-legal generate < 30 s; S
heavy scene == 82 objects; S GameWizard live on level 9; P two
switchable slots exist (81); P picks exercised the switch path; P pick
avg < 200 ms; P pick max < 200 ms; P pick left no wizard error; D drag
moved the selected AA (first-rep centroid delta 0.5574 A); D drag avg <
200 ms; D drag max < 200 ms; D drag left no wizard error; teardown
leaves scene pre-game (deleted=82).

**Run history:** run 1 (pre-strengthening) PASSED with
`generate_cold_ms=94 generate_warm_ms=31 workload_ms=281 pick_avg_ms=5
pick_max_ms=16 drag_*=0`. Run 2 (final, quoted above) adds the drag
non-vacuity assert. Both far under budget.

**Timer-resolution note:** stdlib `time.time()` on Windows has a ~15.6 ms
wall-clock tick; sub-tick operations (the drag bake) read exactly
0.000 ms and the pick row's max shows one tick (15.65 ms). That
quantization is ~8% of the 200 ms budget; a real regression approaching
200 ms would still be visible. The 30 s generate rows are unaffected.
This is the environment fact the research flagged as UNVERIFIED (§8).

**2× re-run rule:** NOT TRIGGERED — no budget landed within 2× of its
limit (generate 31/160 ms vs ≥15 s; feedback max 16/0 ms vs ≥100 ms).

## Legality pre-flight receipt (Task 1)

`python3.6 tmp/probe_25_legality.py` → `PROBE-25 ALL PASS`:

```
container magic == AAMATCH                         PASS 'AAMATCH'
container kind == manifest                         PASS 'manifest'
10 sets                                            PASS 10 sets
18 entries                                         PASS 18 entries
largest_entry == demo-hard-3/nad                   PASS set=demo-hard-3 entry=nad
NAD heavy_atom_count == 44                         PASS heavy=44
size census 14/4/0                                 PASS census={'small': 14, 'medium': 4}
```

This re-derived the max-legal workload (mPL 4 ceiling from the medium
pool of 4) on the live tree rather than guessing; the smoke re-derives
`largest_entry` at runtime and treats a generator `GenerationError` as a
row FAIL with its own message.

## Files Created/Modified

- `smoke/smoke_25_perf_budgets.py` — additive headless battery: rows G
  (cold+warm generate on NAD), W (max-legal 18-candidate workload), S
  (82-object level-9 scene + live GameWizard), P (20-rep pick),
  D (20-rep drag), teardown; budget literals `GENERATE_BUDGET_MS =
  30000.0`, `FEEDBACK_BUDGET_MS = 200.0`.

## Decisions Made

- **"Generate" = one full `gamestart.start_game`** (cleanup → new_game →
  materialize level 0 → compose → activate), the superset of the
  export-only path; cold asserted, warm echoed only.
- **Max legal workload** = `demo_set_id: ''`, `molecules_per_level: 4`,
  `difficulty_levels: 10`; mPL ≥ 5 is refused by the generator, so the
  smoke never measures past a legality drift.
- **Harness fidelity:** room-temperature `time.time()` timing per
  research §5/§6, local budget literals, raw-budget asserts (no invented
  margin), SMOKE-ENV raw-number echo, single marker verdict.
- **smoke_05 untouched** (self-adapting NAD control); SMOKE-25 is a new
  additive file and the roster is now smokes 01-25.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing Critical] Added a drag-row non-vacuity assert**
- **Found during:** Task 3 (first smoke run — drag reported all-zero ms)
- **Issue:** The drag row asserted only timing + `_error is None`; a
  silent `drag_move` no-op would record 0.000 ms and satisfy the budget
  for the wrong reason.
- **Fix:** Capture the selected AA centroid before the row and assert
  the first rep already displaced (observed 0.5574 Å). Also documented
  the Windows `time.time()` tick in the header.
- **Files modified:** `smoke/smoke_25_perf_budgets.py`
- **Verification:** Re-ran SMOKE-25 → `D drag moved the selected AA PASS
  first-rep centroid delta=0.5574 A`; overall `=== SMOKE-25 PASS ===`.
- **Committed in:** `3b86ea9` (Task 3)

---

**Total deviations:** 1 auto-fixed (1 missing critical)
**Impact on plan:** Strengthens the drag receipt; no scope creep, no
budget change.

## Issues Encountered

- None blocking. The Windows wall-clock tick limits drag min/avg/max
  resolution (documented above); it does not threaten the 200 ms
  verdict given the observed sub-tick cost.

## User Setup Required

None — no external service configuration required.

## Next Phase Readiness

- **09-11 (human feel half):** run the §7 feel checklist on a fresh
  Windows PyMOL session with the demo-hard-3 (NAD) game; this plan
  supplies the machine half only.
- **09-13 (final-build battery sweep):** re-run
  `bash smoke/run_smoke.sh smoke/smoke_25_perf_budgets.py 240` on the
  final build and confirm `=== SMOKE-25 PASS ===` plus the SMOKE-ENV
  numbers.
- Standing gates on this tree: `python3.6 -m py_compile aamatch/*.py`
  clean; full WSL suite 973/973 green; `smoke_05_perf.py` byte-untouched
  (0-line diff).

---
*Phase: 09-help-docs-release-audit*
*Completed: 2026-11-18*
