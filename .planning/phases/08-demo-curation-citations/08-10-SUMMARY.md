---
phase: 08-demo-curation-citations
plan: 10
subsystem: demo-data / generator-supply
tags: [supply-measurement, generator, size-class-buckets, SIZE_S1,
  SIZE_S2, curated-manifest, default-config, nearest-bucket-fallback,
  fail-closed, thin-pool, python3.6]

# Dependency graph
requires:
  - phase: 08-demo-curation-citations
    provides: 08-07's FINAL curated manifest (10 sets / 18 entries,
      16 curated + 2 dev) and the 02-08 generator laws (bucket rule
      single-homed in aamatch/generator.py via _candidate_class;
      NEAREST-BUCKET fallback; non-empty-but-thin fail-closed refusal;
      binding constraint len(pool) >= molecules_per_level)
provides:
  - tests/test_demo_supply.py -- the PERMANENT supply instrument:
    curated bucket tally from the real manifest's heavy-atom counts
    pinned against EXPECTED_SUPPLY {'small': 12, 'medium': 4,
    'large': 0}; default-config generation (m=2, D=3, unset, allowed
    []) proven over ALL sets, curated-only rows, AND each single
    curated set at seeds 1/42/999; thin-set fail-closed refusals
    pinned verbatim; skips cleanly on a pre-Phase-8 tree
  - The recorded SIZE_S1/S2 verdict: NO RE-TUNE. generator.py:118-120's
    Phase-8-deferred re-tune question is answered NO with measured
    numbers (12/4/0; medium bucket 4 >= the Q8 floor 3; all-sets
    default-config generation provably succeeds) -- constants stand
    unchanged, generator.py untouched
affects: [08-11 detector-coverage probe + [HUMAN] grouped-dropdown
  checkpoint (the thin-set defaults table below is the input for
  documenting per-set feasibility in Phase 9 help/UI text), 08-08/08-09
  sibling plans (parallel wave 7 worktrees)]

# Tech tracking
tech-stack:
  added: []
  patterns: [supply measurement via the pure parse chain + hand-built
    SUPPORT-CAPABLE profiles (has_acceptor base + manifest halogen/
    metal flags) that isolate bucket supply from capability -- refusal
    in this instrument is bucket-supply by construction, capability
    can never fire; refusals-are-correct pinned VERBATIM per set]

key-files:
  created: [tests/test_demo_supply.py]
  modified: []

key-decisions:
  - "SIZE_S1=25 / SIZE_S2=60 STAND UNCHANGED (no-op verdict recorded
    with numbers): curated tally 12 small / 4 medium / 0 large; the
    NEAREST-BUCKET fallback (large target -> medium pool) is the
    designed carrier for the 0-large tier and all-sets + curated-only
    default games generate; medium 4 >= Q8 floor 3. Neither task-2
    trigger (all-sets refusal OR medium < 3) fired."
  - "THIN-SET discovery (evidence over plan sketch): the plan predicted
    two pinned refusal sets (demo-easy-3, demo-veryhard-2 -- the
    1-entry sets) by reasoning per-set ENTRY count. The measured
    per-BUCKET pool adds demo-veryhard-1: folic_acid (32 heavy) is
    medium, so demo-veryhard-1's LEVEL-0 small pool holds only
    thyroxine (24 heavy) -- 1 distinct < m=2 == the research-Q8
    non-empty-but-thin refusal (fallback fires ONLY on an EMPTY target
    pool). Refusal pinned verbatim, NOT a re-tune trigger; recorded as
    a plan-text correction."

patterns-established:
  - "Supply-instrument test pattern: skip-guard on curated set ids ->
    tally pinned against a module constant (EXPECTED_SUPPLY; updated
    ONLY in the same commit as bundled-data changes) -> Q8 floor
    pinned as a LOUD failing assertion (medium >= 3) instead of
    being absorbed by the tally -> default-config generation proven
    pool-structurally at three architecturally different seeds -> a
    data-relative per-set loop pins success OR verbatim fail-closed
    refusals (refusals-are-correct is itself the assertion)."

# Metrics
duration: ~15 min (execution 15:07Z-15:23Z)
completed: 2026-09-26
---

# Phase 8 Plan 10: Curated-Manifest Supply Measurement Summary

**Measured the real curated size-class supply on the final manifest
(12 small / 4 medium / 0 large, exactly the predicted distribution;
medium = atp 31, nad 44, folic_acid 32, heme 43 heavy), proved the
default config (m=2, D=3, unset) generates over ALL sets and
curated-only rows, pinned the three genuinely-thin per-set fail-closed
refusals verbatim (demo-easy-3, demo-veryhard-2, plus the measured
third: demo-veryhard-1's thin level-0 small pool), and recorded the
verdict: SIZE_S1=25/SIZE_S2=60 require NO re-tune --
generator.py:118-120's Phase-8-deferred question is answered with
data, not assumption; 912/912 WSL green.**

## Performance

- **Duration:** ~15 min
- **Started:** 2026-09-26T15:07Z
- **Completed:** 2026-09-26T15:23Z
- **Tasks:** 3/3
- **Files created:** 1 (tests/test_demo_supply.py); modified: 0

## Measured Tally + Verdict

**CURATED BUCKET TALLY (measured, 08-10): small 12 / medium 4 / large 0**

(all-sets incl. demo-dev-1's 2 small entries: 14/4/0 -- EXPECTED
difference, pinned data-relative by the test, never a failure.)

**VERDICT: NO RE-TUNE.** Generator.py:118-120's deferred decision is
answered NO with numbers:

| Bucket | Count | Q8 floor (>=3) | Notes |
| ------ | ----- | -------------- | ----- |
| small  | 12    | MEETS          | incl. thyroxine at 24 (1 below SIZE_S1=25) |
| medium | 4     | MEETS          | atp 31, nad 44, folic_acid 32, heme 43 |
| large  | 0     | n/a            | NEAREST-BUCKET fallback -> medium is the designed carrier |

Re-tune triggers (plan task 2, explicit): (a) all-sets default-config
generation refuses -- DID NOT FIRE (seeds 1/42/999 all generate);
(b) medium bucket < 3 -- DID NOT FIRE (4). SIZE_S1/S2 stay 25/60;
generator.py + test_generator.py + test_generator_invariants.py
UNTOUCHED (the bucket rule stays single-homed in
aamatch/generator.py::_candidate_class; game_file.py's import is
untouched).

Per-set default-config table (m=2, D=3; pool-structure, seed-independent):

| Set | Entries | Verdict |
| --- | ------- | ------- |
| demo-easy-1/2, demo-hard-1/2/3, demo-challenge-1 | 2 each | GENERATES |
| demo-easy-3 | 1 (caffeine) | REFUSES, pinned verbatim (thin small pool) |
| demo-veryhard-1 | 2 (folic medium, thyroxine small) | REFUSES, pinned verbatim (level-0 small pool = thyroxine alone -- non-empty-but-thin) |
| demo-veryhard-2 | 1 (heme) | REFUSES, pinned verbatim (thin small pool w/ medium fallback pool of 1) |

All three refusals are the SAME generator.py message:
"size class 'small' (fallback target 'small') has 1 distinct
candidate(s); level 0 needs 2 distinct molecules -- add candidates or
lower molecules_per_level" -- fail-closed with the user's remedy named.

## Task Commits

1. **Tasks 1+2: tests/test_demo_supply.py (measure + prove; no re-tune
   verdict)** -- `644ba02` (test) -- the plan's no-re-tune branch
   explicitly commits ONLY the new test; no code was added anywhere.
2. **Task 3: full WSL suite regression** -- no additional commits
   (zero remaining adjustments; suite green on the committed test).

**Plan metadata:** (recorded below; docs commit)

## Test Results

- `python3.6 -m unittest tests.test_demo_supply -v` -- **6/6 OK**
  (tally == EXPECTED_SUPPLY; all-sets tally = curated + dev pinned
  data-relative; medium/small >= Q8 floor 3; all-sets + curated-only
  default-config generation at seeds 1/42/999; per-set loop: 6 sets
  generate, 3 refuse with the exact pinned message)
- `python3.6 -m unittest tests.test_demo_supply tests.test_generator
  tests.test_generator_invariants -v` -- **102/102 OK**
- `grep -n "SIZE_S1\\|SIZE_S2" aamatch/generator.py` -- constants
  present at lines 121/122 (25/60) with the Phase-8-deferral comment
  intact; UNCHANGED
- `python3.6 -m py_compile aamatch/*.py scripts/build_demos.py` -- OK
- `python3.6 -m unittest discover -s tests` -- **912/912 OK** (full
  suite incl. purity gates, the 100-seed invariant battery, and the
  10-test data battery; 906 + 6 new)

## Files Created

- `tests/test_demo_supply.py` -- the permanent supply instrument (323
  lines): skip-guarded curated tally vs EXPECTED_SUPPLY, Q8 floor
  pinned loudly, default-config generation proofs (all-sets,
  curated-only, per-set) with hand-built support-capable profiles,
  verbatim thin-refusal pins. Reads the REAL MANIFEST.json via the
  pure parse chain (read_json_file -> parse_manifest_dict ->
  enumerate_entries); zero stubs; WSL-pure (no PyMOL).

## Decisions Made

1. **NO-OP verdict for SIZE_S1/S2, recorded loud.** The generator's
   Phase-8 deferral comment said "tuned when the Phase-8 manifest
   exists". The manifest now exists; the measurement says the buckets
   are right: default games over the real supply generate across all
   three target classes (large via the nearest-bucket fallback to
   medium), and the medium bucket (4) sits above the Q8 floor (3).
   Nothing was silent-edited; this SUMMARY + the pinned test constants
   ARE the record.
2. **Hand-built support-capable profiles (per plan) kept the trigger
   attribution honest.** With capability never in play, any default-
   config refusal in this instrument is bucket-supply by construction.
   No capability-shaped refusal occurred (profiles were correct by
   construction: has_acceptor base + manifest halogen/metal flags).
3. **Multi-seed proof (1, 42, 999).** Thin-pool refusals are
   seed-independent (pool structure, not draw luck) -- verified
   identical across all three seeds before pinning.

## Deviations from Plan

### Plan-text corrections (evidence over sketch)

**1. [Rule 1 - plan sketch correction] Thin-set list is THREE sets, not
the predicted two**

- **Found during:** Task 1 per-set generation probing
- **Issue:** The plan pinned expected refusals for "demo-easy-3 AND
  demo-veryhard-2 -- each is a 1-entry set". It reasoned per-set entry
  count, but the binding constraint is per-BUCKET pool depth:
  demo-veryhard-1 has 2 entries, yet its level-0 small pool holds only
  thyroxine (24 heavy) because folic_acid (32 heavy) lands in medium.
  Generation refuses exactly per the research-Q8 non-empty-but-thin
  ruling (the fallback fires ONLY on an EMPTY target pool).
- **Fix:** Pinned demo-veryhard-1's refusal verbatim as
  EXPECTED_THIN_REFUSALS entry with an explanatory comment; recorded
  the correction in the module docstring. No production code touched --
  the refusal IS the generator working as designed, and neither
  task-2 re-tune trigger is affected (they scope all-sets /
  medium-bucket count).
- **Files modified:** tests/test_demo_supply.py
- **Commit:** 644ba02

No bug fixes, no missing-critical additions, no blocking issues
(Rules 1-3 otherwise unused); no architectural decisions (Rule 4
untouched).

## Authentication Gates

None.

## Next Phase Readiness

- **08-11** has the honest per-set feasibility table above: three
  curated sets refuse the DEFAULT config (m=2) at D=3 -- the UI/help
  text (Phase 9) should point thin-set users at molecules_per_level=1
  rather than leave them reading a refusal. The heme -4 charge model
  input (08-07) plus this table are the 08-11 detector-coverage
  review's recorded inputs.
- **Parallel-wave note:** this plan ran in a wave-7 worktree
  (exec/08-10) alongside 08-08 and 08-09; its only shared-surface file
  is tests/ (new file, no overlap) -- merge should be trivial.
