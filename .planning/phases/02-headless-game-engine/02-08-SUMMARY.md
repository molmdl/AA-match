---
phase: 02-headless-game-engine
plan: 08
subsystem: seeded-generator
tags: [generator, level-spec, rng-determinism, solvability, grid-geometry, difficulty, capability, oq-1, oq-5, purity]

# Dependency graph
requires:
  - phase: 02-01
    provides: docs/DETECTION_THRESHOLDS.md — the APPROVED gate doc (OQ-1 mode semantics §4.3, OQ-5 hydrophobic sampling exclusion §4.5, version-bump policy §4.7) that derive_required transcribes
  - phase: 02-05
    provides: aamatch/capability.py — aa_capable/ligand_support/AA_RESIDUES/AA_TOKENS (the single typing home; generator never re-derives typing, DETECT-04)
  - phase: 02-06
    provides: aamatch/detector.py detect_part1 (h_bond/salt_bridge/hydrophobic) — consumed by the generator<->detector agreement cross-check test
  - phase: 01-06
    provides: level_spec reserved schema + DETECTOR_VERSION/LEVEL_SPEC_VERSION + make_level_spec_container/parse_level_spec_dict round-trip gates
provides:
  - aamatch/generator.py — the pure seeded generator: difficulty_params (GEN-05 half-up interpolation), slot_position/placement_offset (GEN-03 grid), derive_required (OQ-1 semantics + OQ-5 exclusion), allocate_slots (GEN-04 solvability by construction), generate (GEN-01 payload assembly), GenerationError
  - the payload contract 02-13/02-14/02-10/02-12 consume: version stamps, per-level difficulty, per-molecule ligand/required/placement/grid with serialized poses (nothing re-derives from the seed at replay)
  - the ligand_data CONTRACT: (set_id, entry_id)-keyed (or one shared) {'centroid', 'radius', 'profile'} — profile is capability.ligand_profile-shaped and REQUIRED for non-degenerate mode handling (see deviations)
affects: [02-10 (engine: bounding_sphere + profile feed generate), 02-12 (>=100-seed sweep), 02-13 (SMOKE-03 must pass profiles), 02-14 (new_game E2E must pass profiles), 02-15, phase-3+ replay/reset]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "integer HALF-UP interpolation (x + d//2)//d — never round() (banker's trap); mechanically pinned by a source scan test"
    - "RNG only via randint/choice/sample/shuffle over SORTED/fixed-order lists — never sets/dicts; per-unit sub-RNGs drawn from the master stream in fixed order with a FIXED STRIDE (setup-independent consumption)"
    - "solvability by construction: one dedicated role='required' slot per required item with truthful can_form via aa_capable; distractors from all 20 AAs"
    - "fail-early guards: degenerate ligand bounds (NaN/inf/R<=0), bool seed, unknown modes/types, vocabulary drift — every GenerationError names the cause"

key-files:
  created: ["aamatch/generator.py", "tests/test_generator.py"]
  modified: ["tests/test_purity.py (PURE_MODULES += generator -> 12)"]

key-decisions:
  - "difficulty formula implemented as grid_n = 3 + frac, n_required_types = 1 + frac with frac = (L*6 + (D-1)//2)//(D-1) — the plan's inline '3 + frac*6' is impossible (violates its own 3..9/1..7 invariants and the D=3 spot rows); research §6 form satisfies every stated invariant (deviation recorded)"
  - "ligand_data entries carry the chemistry 'profile' (capability.ligand_profile shape) alongside geometry — generator required-set derivation is polarity/support-aware (D3/D4) and cannot run from geometry alone; missing profile degrades FAIL-CLOSED to an empty profile (binds 02-13/02-14 wiring)"
  - "sub-seed stride = D * MOLECULES_CAP drawn once from the master (setup-independent): adding a molecule consumes previously-drawn-but-unused seeds and never shifts an existing molecule's stream (byte-isolation tested; PITFALL 11.2)"
  - "molecule selection is per-unit rng.sample(available, 1) with sequential distinct-pick dedup — a single level-level sample would re-pick all molecules when molecules_per_level changes (breaks the isolation must-have)"
  - "size-class bucket fallback: when the target bucket has no candidates, the NEAREST non-empty bucket supplies molecules (ties -> easier); the difficulty dict keeps RECORDING the target class — the 2-small-entry dev manifest must drive D>=2 games until Phase-8 curation"
  - "molecule_id numbered WITHIN each level (mol-001..): makes the sub-seed-isolation byte-equality exact and matches the per-molecule scoping of slot_id; level_index + molecule_id identify globally"
  - "unset + empty allowed_interactions draws from the SUPPORT-FILTERED non-hydrophobic types (OQ-1 'all 7' harmonized with the research edge ruling 'an unset draw never includes an unsupported type' + OQ-5) — drawing an unsupported type would only crash allocation later"
  - "derived D=10 row L4 is grid 6/types 4 (hand table sketch says 5/4): the plan's 'the formula wins' rule applied; research pre-authorizes asserting monotonicity, not the hand literals; D=3 reference rows agree exactly"

patterns-established:
  - "pure-module registration as its own TDD step: a pinned test asserts membership in PURE_MODULES before the list is extended (gates silently skip unregistered modules, 01-08)"
  - "detector-agreement cross-check pattern (DETECT-04): synthetic AA + ligand scene proves capability.aa_capable and detector.detect_part1 agree BOTH directions through the same typing tables"

# Metrics
duration: 17 min
completed: 2026-09-06
---

# Phase 2 Plan 08: Seeded Generator Summary

**Pure seeded generator (aamatch/generator.py, 879 lines): half-up difficulty interpolation, deterministic gap-respecting grids, OQ-1/OQ-5 required-set semantics over the shared capability tables, solvability-by-construction slot allocation, and byte-deterministic version-stamped payloads — 77 new tests (423/423 green), purity gates now scan the 12th pure module.**

## Performance

- **Duration:** 17 min
- **Started:** 2026-09-06T15:19:45Z
- **Completed:** 2026-09-06T15:36:54Z
- **Tasks:** 3/3 (each RED -> GREEN, 6 atomic commits)
- **Files modified:** 2 created (generator, its tests) + 1 modified (purity registration)

## Accomplishments

- **GEN-05 difficulty:** `difficulty_params(D, L)` interpolates grid_n 3..9 / n_required_types 1..7 / size-class thirds via INTEGER HALF-UP arithmetic — monotone over ALL legal D 1..10 (tested), D=1 -> single easiest level, D=3 rows exactly 3/1/small, 6/4/medium, 9/7/large. `round(` is mechanically banned from the module by a source-scan test.
- **GEN-03 geometry:** `slot_position` implements the research §5.2 formula exactly (slot(0,0) == (-8.0, -8.0, 9.0) for the n=3/R=4 reference); pairwise spacing >= 8.0 and slot-to-centroid >= R + GAP_MARGIN asserted for n up to 9; `placement_offset` shifts molecule group m by m*(n*SPACING + INTER_GRID_MARGIN) along +X — cross-molecule slots never coincide (tested >= one spacing apart).
- **OQ-1/OQ-5 semantics:** `derive_required` implements exclusive ('any' scoped by allowed; empty -> refusal naming the setup field), block_exclusive (exact checked set, canonical order, count 1; unsupported type -> refusal NAMING it; hydrophobic reachable ONLY here), unset (support-filtered sampling, k = min(n_required_types, len(pool)), OQ-5 hydrophobic exclusion with the only-hydrophobic refusal naming the policy). Research §4.3 edge rulings table transcribed verbatim in the docstring.
- **GEN-04 solvability:** `allocate_slots` gives every required item a dedicated role='required' slot with truthful `can_form` (proven against `aa_capable` per slot), draws AAs via rng.choice over sorted capable pools, fills distractors from the sorted 20-AA list, and refuses grid-too-small / no-capable-AA / count!=1 / vocabulary drift — each naming the cause.
- **GEN-01 assembly:** `generate()` emits the reserved payload + additive `placement.offset`, stamps DETECTOR_VERSION/LEVEL_SPEC_VERSION from level_spec, refuses bool/non-int seeds explicitly, validates ligand bounds fail-early (NaN/inf/R<=0), selects molecules by size-class bucket (with recorded supply fallback) as distinct per-level picks, picks multi-state protonation via rng.choice(sorted(states)), and round-trips through `parse_level_spec_dict(make_level_spec_container(payload))` unchanged. Same seed -> byte-identical (`json.dumps(sort_keys=True)`); sub-seed isolation proven byte-exact.
- **DETECT-04 agreement:** synthetic SER/VAL h_bond scene proves `aa_capable` and `detector.detect_part1` agree BOTH directions (capable->detected, incapable->not-detected) through the same capability tables.
- **Purity:** generator imports only math/random + pure aamatch modules; PURE_MODULES = 12 — Gates A/A2/B/D + negative control all green.

## Task Commits

Each task committed RED (failing tests) then GREEN (implementation):

1. **Task 1: Difficulty mapping + grid geometry + RNG skeleton** — RED `d6d76e5` (test) -> GREEN `da9a04e` (feat)
2. **Task 2: derive_required + allocate_slots + detector cross-check** — RED `1964b21` (test) -> GREEN `7241e98` (feat)
3. **Task 3: generate() assembly + purity registration** — RED `25843fe` (test) -> GREEN `d402ae6` (feat)

**Plan metadata:** see final docs commit.

## Files Created/Modified

- `aamatch/generator.py` — the pure seeded generator (879 lines; constants GRID_SPACING/GAP_MARGIN/INTER_GRID_MARGIN/GRID_SPAN/SIZE_S1/SIZE_S2, GenerationError, difficulty_params, slot_position, placement_offset, _validate_ligand_data, _sub_seeds, derive_required, allocate_slots, generate + input-validation helpers)
- `tests/test_generator.py` — 76 tests: difficulty mapping, grid geometry, ligand-data guards, sub-seed derivation, OQ-1/OQ-5 mode semantics, allocation solvability, detector agreement, payload shape/stamps/determinism/isolation/round-trip
- `tests/test_purity.py` — PURE_MODULES += 'generator' (12) + registration pin test

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Plan-text bug] The plan's inline difficulty formula `grid_n: 3 + frac*6` is impossible**

- **Found during:** Task 1 RED authoring
- **Issue:** with frac = (L*6 + (D-1)//2)//(D-1) in 0..6, `3 + frac*6` yields grid 3..39 and types 1..43 — violating the plan's OWN invariants (grid_n 3..9, types 1..7) and its own D=3 spot rows (6/4, 9/7).
- **Fix:** implemented the generation-research §6 form: `grid_n = 3 + frac`, `n_required_types = 1 + frac` (frac interpolates over GRID_SPAN=6). This satisfies every stated invariant AND the D=3 reference rows exactly. The plan's own rule — "if the formula disagrees with the hand table, THE FORMULA WINS" — applied to the plan text itself.
- **Files:** aamatch/generator.py (difficulty_params), tests/test_generator.py
- **Commit:** da9a04e

**2. [Rule 1 - Bug, caught by tests] `_validate_ligand_data` dropped the geometry dict's `profile` key**

- **Found during:** Task 3 GREEN (15 generate() errors: profiles never reached derive_required)
- **Issue:** the validator returned a fresh `{'centroid', 'radius'}` dict, silently discarding the chemistry profile — every unset/block_exclusive game then refused as "supports none".
- **Fix:** validator returns a copy of the full geometry dict with normalized centroid/radius; profile survives.
- **Files:** aamatch/generator.py
- **Commit:** d402ae6

### Contract/Design Deviations (recorded, tested)

**3. [Rule 3 - Blocking contract gap] ligand_data must carry the chemistry `profile` — BINDS 02-13/02-14**

- **Issue:** `derive_required(setup, ligand_profile, ...)` and `allocate_slots(..., ligand_profile, ...)` are polarity/support-aware (gate D3/D4/D1); the plans for 02-13/02-14 sketch ligand_data as bounding_sphere output ONLY ({'centroid', 'radius'}), which cannot ground required-set derivation (an empty profile refuses every non-degenerate mode).
- **Fix:** the ligand_data contract is now explicit (docstring + tests): entries are `{'centroid': (x, y, z), 'radius': R, 'profile': <capability.ligand_profile shape>}`, keyed by (set_id, entry_id) tuples — or ONE shared such dict (single-ligand smokes). A MISSING profile degrades fail-closed to empty (clear "supports none / cannot support" refusals, never unsolvable levels). The cmd tier already loads each ligand for its bounding sphere; it must additionally compute `capability.ligand_profile(lig_records, lig_bonds)` from the same extraction and include it.
- **Action for orchestrator:** 02-13 (SMOKE-03) and 02-14 (new_game) plan steps need one extra line each: `profile = capability.ligand_profile(lig_atoms, lig_bonds)` merged into the geometry dict before generate().

**4. [Design] Sub-seed stride fixed at D * MOLECULES_CAP** — the plan's "levels x molecules" draw would shift EVERY existing molecule's stream when molecules_per_level changes, violating the plan's own sub-seed-isolation must-have. Fixed-stride draw + per-(level, slot) indexing satisfies isolation; `_sub_seeds(master_rng, n_units)` signature unchanged. (d402ae6)

**5. [Design] Per-unit sequential distinct molecule picks** — instead of one level-level `rng.sample(pool, mpl)` (which re-picks ALL molecules when mpl changes). Each unit draws `rng.sample(available, 1)` from the sorted bucket minus this level's earlier picks; unit 0 always sees the full pool. Still "rng.sample from the deterministically sorted candidate list", per unit. (d402ae6)

**6. [Design] Size-class supply fallback** — target bucket empty -> nearest non-empty bucket by rank distance (ties -> easier); difficulty dict keeps recording the TARGET class. Without it, the 2-small-entry dev manifest refuses every D >= 2 game, blocking the phase's own SMOKE-03/04/05 before Phase-8 curation. Zero candidates still refuses. (d402ae6)

**7. [Interpretation] unset + empty allowed draws from the support-filtered non-hydrophobic types** — OQ-1's "draw from all 7 types" harmonized with the research edge ruling ("an unset draw never includes an unsupported type") and OQ-5; drawing an unsupported type would only crash allocation with a less local message. Featureless ligand -> immediate clear refusal. (7241e98)

**8. [Trivial] Detector cross-check uses `detector.detect_part1`** (plan prose says `detector.detect`) — sibling plan 02-07 owns detect(); the base detector already covers h_bond, exactly as pre-authorized in this plan's execution instructions. (7241e98)

**9. [Note] Derived D=10 row L4 = grid 6 / types 4** (research hand-table sketch says 5/4) — the research itself pre-authorizes: "the test asserts monotonicity, not the literals"; the formula wins per the plan's instruction. The plan-mandated D=3 spot rows agree exactly. (da9a04e)

## Authentication Gates

None — fully WSL-pure plan (no CLI/API credentials involved).

## Verification

- `python3.6 -m py_compile aamatch/*.py` — clean (3.6 syntax floor)
- `python3.6 -m unittest discover -s tests -v` — **423/423 OK** (baseline 346 + 77 new: 76 generator + 1 purity registration pin)
- Purity gates on the new module: Gate A AST import scan (math/random + pure aamatch only, every scope), Gate A2 lazy init untouched, Gate B clean-subprocess import, Gate D py_compile, negative control intact
- No itertools/numpy/dataclasses/pymol/Qt tokens in generator.py outside docstring prose (AST gate is the enforced mechanism); no sys.modules stubs anywhere; no round( anywhere in the module (mechanically pinned)

## Next Phase Readiness

- 02-10 (engine) can wire `generate(...)` directly: `geometry.bounding_sphere()` output + `capability.ligand_profile(atoms, bonds)` -> ligand_data entries keyed by (set_id, entry_id).
- 02-12 (>=100-seed sweep) inherits byte-determinism + the invariant suite shape from tests/test_generator.py.
- 02-13/02-14 MUST pass the chemistry profile in ligand_data (deviation 3) — otherwise block_exclusive/unset modes refuse fail-closed.
- Reset/replay (Phase 3/6) can consume `grid_pose.position` + `placement.offset` verbatim — nothing re-derives from the seed.
