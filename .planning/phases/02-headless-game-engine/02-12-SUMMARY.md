---
phase: 02-headless-game-engine
plan: 12
subsystem: seeded-generator
tags: [generator, invariant-suite, determinism, solvability, grid-geometry, difficulty, corpus-statistics, gen-01, gen-03, gen-04, gen-05, oq-1, oq-5]

# Dependency graph
requires:
  - phase: 02-08
    provides: aamatch/generator.py — the pure seeded generator under test + the recorded IMPLEMENTED semantics (9 deviations: half-up difficulty formula, ligand_data {'centroid','radius','profile'} contract, OQ-1/OQ-5 mode semantics, nearest-bucket supply fallback)
  - phase: 02-05
    provides: aamatch/capability.py — aa_capable/ligand_support/AA_RESIDUES (can_form truthfulness is proven through the single typing home, DETECT-04)
  - phase: 01-06
    provides: level_spec.make_level_spec_container/parse_level_spec_dict + DETECTOR_VERSION/LEVEL_SPEC_VERSION (every payload round-trips these gates)
provides:
  - tests/test_generator_invariants.py — the permanent >= 100-seed invariant suite (ROADMAP Phase 2 success criterion 3; generation research §8 items 1-19): GEN-01 determinism/format, GEN-03 grid honesty, GEN-04 solvability by construction, GEN-05 difficulty escalation, plus corpus statistics — 18 new tests sweeping 1800 payloads
affects: [02-10/02-14 (engine payload consumers inherit the proven contract), 02-13 (headless items 20-22 remain), 02-15 (the audit references this suite as the PITFALL-11 closure), phases 3+ (replay/reset consume proven-stable payloads)]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "corpus invariant suite: module-level lazy 1800-payload corpus shared by invariant groups; invariants assert IMPLEMENTED (02-08-recorded) semantics, never plan sketches"
    - "cross-seed distinctness measured with the 'seed' echo stripped — the payload carries its own seed, so raw-byte distinctness would trivially pass and catch nothing"
    - "exhaustive pairwise-spacing proof in O(k log k + k*w): sorted-x sliding window (a violating pair must have |dx| < limit) — full O(k^2) over 1800 payloads would dominate runtime for no added rigor"

key-files:
  created: ["tests/test_generator_invariants.py"]
  modified: []

key-decisions:
  - "block_exclusive sweeps with allowed = ALL 7 types: the only OQ-5-legit route to a required hydrophobic; corpus type-coverage (research item 18) therefore aggregates the whole corpus, with hydrophobic-required pinned to the block mode (recording this beats sweeping block without hydrophobic and silently failing the coverage stat)"
  - "unset sweeps with EMPTY allowed (OQ-1 'the game picks' harmonized with the support-filter edge ruling): exercises the full 6-type support-filtered sample pool"
  - "exclusive-mode solvability invariant is vacuous by construction (items == [] means no dedicated slots; 'any' scoring is 02-10) — the suite asserts the no-items/no-required-slots accounting instead of an empirical not-guaranteed 'some capable AA exists' claim"

patterns-established:
  - "profile_vocabulary/sample_pool helpers: the invariant oracle re-derives the mode vocabulary from INTERACTION_TYPES + the 02-08 rulings, keeping tests independent of generator internals while pinning exact k = min(n_required_types, len(pool))"

# Metrics
duration: ~45 min
completed: 2026-09-06
---

# Phase 2 Plan 12: 100-Seed Generator Invariant Suite Summary

**The permanent ROADMAP Phase-2 criterion-3 gate (tests/test_generator_invariants.py, 750 lines, 18 tests): 100 seeds × D ∈ {1,3,10} × all 3 modes × molecules ∈ {1,2} (18 configs, 1800 payloads) proving GEN-01/03/04/05 by invariant assertion — byte determinism, per-payload level_spec round-trip, solvability by construction with truthful can_form, honest NxN beyond-gap disjoint grids, monotonic difficulty with clamping honesty, and healthy corpus statistics (100/100 distinct per config, all 20 AAs as distractors, 7/7 types required, r0c0 required in 9.8% of units). 456/456 green including all pre-existing tests.**

## Performance

- **Duration:** ~45 min
- **Started / Completed:** 2026-09-06 (WSL)
- **Tasks:** 2/2 (both produce the single artifact; one `test(02-12):` commit)
- **Files modified:** 1 created (750 lines), zero aamatch/ changes
- **Test counts:** baseline 438/438 (this branch base e475fd6; earlier wave notes say 423 — the merged base carries the current count) → **456/456** (18 new). Invariant file alone: 18 tests in ~51 s; full suite ~67 s.

## Accomplishments

- **Group A — determinism & format (§8 items 1–4):** every payload generated twice is `json.dumps(sort_keys=True)` byte-equal; every payload round-trips `parse_level_spec_dict(make_level_spec_container(payload))` unchanged; detector_version/format_version stamps + real-int (never bool) seed pinned across the corpus; cross-seed distinctness ≥ 95/100 per config measured with the seed echo stripped — **observed 100/100 in all 18 configs** (most conservative reading of research item 4).
- **Group B — solvability (items 5–8):** every required item of every list-mode molecule has ≥ count dedicated `role='required'` slots carrying that type in `can_form`; every `can_form` entry verifies against `capability.aa_capable(slot_aa, type, profile)` (the table never lies — DETECT-04 property); can_form ⊆ INTERACTION_TYPES; required slots carry exactly one can_form entry, distractors none; required-slot count == list-item count. OQ-1/OQ-5 mode semantics pinned across the corpus: exclusive → `{'mode':'any','items':[]}`; block_exclusive → items == the checked set in canonical order, counts 1; unset → hydrophobic never sampled, k == min(n_required_types, len(supported pool)), canonical order. Feasibility refusals name the cause (halogen on halogen-free ligand names 'halogen'; exclusive + empty allowed names the field; unset pools emptied by OQ-5 name the policy).
- **Group C — grid structure (items 9–13):** `grid.n == difficulty.grid_n`, n² slots, (row,col) full coverage exactly once, unique `r{row}c{col}` ids; pairwise spacing ≥ GRID_SPACING proven exhaustively via an O(k log k) sorted-x sliding window (any violating pair must share |dx| < limit); every slot beyond R + GAP_MARGIN of the ligand centroid with a sanity ceiling (R + GAP_MARGIN + n·SPACING); every position finite; m=2 levels globally disjoint in world frame (grid_pose + placement.offset), with the combined sweep pinned ≥ spacing (structural cross-molecule gap = 14 Å > 8).
- **Group D — difficulty (items 14–16):** parametrized over ALL 10 legal D values: exactly D levels, tiers 0..D−1 strictly ascending, level_index == tier; grid_n / n_required_types / size-class rank non-decreasing across every payload's levels; clamping honesty — pre-clamp intent ≤ 7 and emitted items ≤ len(supported pool) per molecule.
- **Group E — corpus statistics (items 17–19):** over the 100-seed D=3 unset m=2 sweep all 20 AAs appear as distractors, no all-identical grid, every grid keeps ≥ 1 distractor, and slot r0c0 is required in **9.8 % of 600 units** (≠ 0, « 50 %); full-corpus type coverage: **7/7 interaction types required somewhere**, hydrophobic only via block_explicit (OQ-5 pinned both directions — zero in unset, nonzero in block).

## Deviations from Plan

**1. [Rule 1 - Test-side expectation error, caught at RED] The OQ-5 policy-naming refusal requires hydrophobic in `allowed`.**

- **Found during:** B8 feasibility-refusal test authoring.
- **Issue:** with `unset` + EMPTY allowed, the vocabulary itself excludes hydrophobic (02-08 implementation), so a hydrophobic-only ligand gets the generic 'supports none of the sampleable interactions' refusal — my first draft expected the OQ-5 policy message there.
- **Fix:** the test now passes `allowed=('hydrophobic',)` (unset mode) to reach the policy-naming branch, with a comment documenting both fail-closed paths. This tests the IMPLEMENTED semantics; no generator change.
- **Files:** tests/test_generator_invariants.py
- **Commit:** 3090e01

**2. [Interpretation] Type coverage (research item 18) aggregates the whole corpus, not just the unset sweep** — hydrophobic can ONLY be required via block_exclusive explicit check (OQ-5), so an unset-only coverage assert could never pass with the recorded semantics; the suite also pins hydrophobic at exactly zero in the unset corpus (the exclusion itself) — coverage AND the OQ-5 wall are both proven. Documented in the test docstring. (3090e01)

**3. [Interpretation] Exclusive-mode 'solvable by construction' invariant is recorded as vacuous** — `items == []` allocates zero dedicated slots; 'any' scoring-side solvability belongs to 02-10. The suite asserts the accounting identity (no items ⇒ no required slots) rather than a probabilistic 'some distractor happens to be capable' claim the generator does not guarantee. (3090e01)

**4. [Performance, within plan guidance] Exhaustive pairwise-spacing proof made O(k log k)** — the plan pins 'pairwise distances ≥ GRID_SPACING ε 1e-9' across the corpus; a literal O(k²) over 1800 payloads would dominate the ~51 s runtime. The sorted-x sliding window proves the identical statement exhaustively (any pair closer than the limit has |dx| below it). Runtime recorded: file ~51 s, full suite ~67 s — well inside 'reasonably fast' for the documented sweep. (3090e01)

**5. [Note] Distinctness strips the seed echo** — research item 4 guards against accidental constant-level generation; the payload serializes its own seed, so raw-byte distinctness would trivially pass. Seedless bytes observe **100/100 distinct in all 18 configs** (floor 95). (3090e01)

## Authentication Gates

None — fully WSL-pure plan (no CLI/API credentials involved).

## Verification

- `python3.6 -m py_compile aamatch/*.py` — clean (3.6 syntax floor)
- `python3.6 -m unittest tests.test_generator_invariants -v` — 18/18 OK (~51 s)
- `python3.6 -m unittest discover -s tests` — **456/456 OK** (438 baseline + 18 new), ~67 s — purity gates untouched (no aamatch/ edits, no PURE_MODULES change, no sys.modules stubs)

## Next Phase Readiness

- ROADMAP Phase-2 success criterion 3 ([WSL] generator invariant tests over ≥ 100 seeds) is satisfied and permanently enforced; the suite belongs to every later phase's inherit-and-don't-weaken gate set.
- 02-13/02-14 inherit items 20–22 (headless materialization/real-coordinate/clickability checks) — the WSL invariants stop at the payload boundary exactly as researched.
- The corpus fixtures (RICH profile, 6-candidate manifest rows, ligand_data contract) are reusable shapes for 02-13/02-14 smoke scripting.
