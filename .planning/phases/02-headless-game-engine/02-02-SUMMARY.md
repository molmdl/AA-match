---
phase: 02-headless-game-engine
plan: 02
subsystem: geometry-pure-layer
tags: [vec3, spatial-index, cell-list, tdd, purity-gate, python3.6, no-numpy]

# Dependency graph
requires:
  - phase: 01-bootstrap-pure-foundation
    provides: enforced purity gates (tests/test_purity.py: Gate A AST scan, Gate B clean-subprocess, Gate D 3.6 syntax floor) + PURE_MODULES registration pattern
provides:
  - aamatch/vec3.py — pure 3-vector math on float tuples (add/sub/scale/dot/cross/norm/dist/norm_squared/unit/angle_at/plane_project), stdlib math only
  - aamatch/spatial.py — build_index (floor-division cell keys) + cross_pairs (cell=cutoff, 3x3x3 neighbourhood scan, sorted output) + brute_force_pairs test oracle
  - 100-seed cell-list equivalence proof (cross_pairs == brute_force_pairs, DETECT-05 correctness half)
  - PURE_MODULES grown 5 -> 7; both new modules gated by Gates A/B/D
affects: [02-06 detector typed-atom pipeline, 02-07 detector criteria, 02-15 code audit, chem_types, any Phase-2 pure geometry consumer]

# Tech tracking
tech-stack:
  added: [] # no new libraries — stdlib math + intra-package import only (purity constraint)
  patterns:
    - "Pure geometry on plain float 3-tuples, no numpy (purity gate forbids it in the pure layer)"
    - "Floats-in/floats-out: components coerced with float() so int inputs never leak"
    - "Fail-closed degeneracy: unit()/angle_at() raise ValueError on zero-length vectors"
    - "Cell size == cutoff makes the 3x3x3 neighbourhood scan provably exhaustive"
    - "itertools stays OUT of the pure layer (02-01 recorded convention) — nested dx/dy/dz loops"
    - "Test-only oracle marked in docstring for the 02-15 audit grep (brute_force_pairs)"

key-files:
  created:
    - aamatch/vec3.py
    - aamatch/spatial.py
    - tests/test_vec3.py
    - tests/test_spatial.py
  modified:
    - tests/test_purity.py

key-decisions:
  - "float() coercion in every tuple-returning vec3 function — the 'floats in, floats out' contract holds even for int inputs (geometry parsed from JSON stays uniform)"
  - "angle_at clamps cos to [-1, 1] before acos — cheap guard against math-domain crashes from float rounding near 0/pi in detector criteria"
  - "plane_project documents unit-normal requirement (caller uses unit()) rather than re-normalizing — keeps per-candidate cost constant-time"
  - "brute_force_pairs lives in spatial.py (per plan) with the audit-grep docstring 'Test oracle only -- the detector must never call this outside tests'; a unit test pins the phrase"
  - "No REFACTOR commits: each vec3 function is 1-3 lines; the 27-cell nested loop is the canonical form — no duplication worth extracting"

patterns-established:
  - "Pattern: Phase-2 pure-module TDD plan = RED test commit -> GREEN implementation commit -> register in PURE_MODULES as a test-type commit (repeated by later pure-module plans)"
  - "Pattern: property tests seed via random.Random(seed) over list comprehensions (fixed draw order), never sets (PYTHONHASHSEED)"
  - "Pattern: equivalence property tests carry a vacuous-guard assertion (non-empty result) so a doubly-broken pair generator cannot pass silently"

# Metrics
duration: 8 min
completed: 2026-09-06
---

# Phase 2 Plan 02: Pure Geometry Primitives Summary

**Pure tuple-based vec3 + cell-list spatial pruning with 100-seed brute-force equivalence proof — the numpy-free geometry foundation of DETECT-05, gated in PURE_MODULES (now 7).**

## Performance

- **Duration:** 8 min
- **Started:** 2026-09-06T07:53:28Z
- **Completed:** 2026-09-06T08:01:21Z
- **Tasks:** 3/3
- **Files modified:** 5 (4 created, 1 modified)

## Accomplishments
- `aamatch/vec3.py` (101 lines): 11 pure functions on float 3-tuples — add/sub/scale/dot/cross/norm/dist/norm_squared/unit/angle_at/plane_project; `import math` solely; fail-closed on zero-length vectors; angle_at 90°/180°/45° hand-verified.
- `aamatch/spatial.py` (80 lines): `build_index` with floor-division cell keys (negatives correct), `cross_pairs` scanning the 3×3×3 neighbourhood at cell=cutoff with sorted `(i, j)` output, and `brute_force_pairs` as the clearly-marked test-only oracle.
- DETECT-05 correctness half proven: `sorted(cross_pairs) == sorted(brute_force_pairs)` over 100 seeded random clouds (40+40 points, 20 Å box, cutoff 4.0), with boundary semantics (`<=` at exactly cutoff, axis + diagonal), empty-input, and determinism cases.
- Purity gates extended: PURE_MODULES now `['setup_state', 'level_spec', 'persistence', 'backup', 'paths', 'vec3', 'spatial']`; Gates A/B/D green over the new modules; full suite 163/163 (114 Phase-1 + 49 new).

## Task Commits

Each task was committed atomically (TDD RED → GREEN per task):

1. **Task 1: vec3.py — pure 3-vector math** — RED `d26d219` (test: add failing vec3 tests), GREEN `f31e474` (feat: implement pure vec3 module)
2. **Task 2: spatial.py — cell-list pruning + brute-force oracle** — RED `221f99e` (test: add failing spatial tests), GREEN `9f9ec65` (feat: implement spatial cell-list pruning + oracle)
3. **Task 3: register both modules in the purity gate** — `4b85861` (test: PURE_MODULES=7)

**Plan metadata:** pending (docs commit)

_Note: TDD tasks produced RED+GREEN commit pairs; no REFACTOR commits — nothing worth extracting (see key-decisions)._

## Files Created/Modified
- `aamatch/vec3.py` — pure 3-vector math on tuples (stdlib math only)
- `aamatch/spatial.py` — build_index + cross_pairs (cell-list) + brute_force_pairs (test oracle)
- `tests/test_vec3.py` — 35 hand-computed unit tests incl. floats-in/floats-out contract
- `tests/test_spatial.py` — 14 tests incl. 100-seed equivalence property + oracle-docstring pin
- `tests/test_purity.py` — PURE_MODULES 5 → 7 (+ prose "five" → "declared")

## Decisions Made
- **float() coercion everywhere in vec3** — guarantees the "floats in, floats out" contract even for int tuples; trivial constant cost per candidate.
- **angle_at cos-clamp to [-1, 1]** — prevents `math.acos` domain errors from float rounding at exactly-0°/180° geometries the detector will construct.
- **plane_project requires a unit normal (documented), no re-normalization** — caller already has `unit()`; keeps the hot path minimal.
- **Oracle docstring is test-pinned** — `test_brute_force_docstring_declares_test_only` guards the phrase the 02-15 code audit greps for.
- **No itertools, no refactor commits** — per recorded 02-01 convention and plan REFACTOR guidance.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None — RED phases failed exactly as expected (ImportError before implementation), GREEN on first attempt for both modules.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- vec3 + spatial are ready for the detector plans (02-06/07 consume `cross_pairs` + per-candidate vec3 math) and for 02-15's audit (oracle marked, no double loops in `cross_pairs`).
- PURE_MODULES registration pattern is now demonstrated for Phase 2 — later pure-module plans repeat it for their own module.
- No blockers or concerns; level_spec/persistence version gates untouched as required.

---
*Phase: 02-headless-game-engine*
*Completed: 2026-09-06*
