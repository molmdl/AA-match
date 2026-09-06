---
phase: 02-headless-game-engine
plan: 06
subsystem: detection
tags: [thresholds, detector, h-bond, salt-bridge, hydrophobic, spatial-pruning, tdd, pure-layer, detect-01, detect-03, detect-04]

# Dependency graph
requires:
  - phase: 02-headless-game-engine
    provides: "DETECT-03 gate doc (docs/DETECTION_THRESHOLDS.md, APPROVED 2026-09-06) — the frozen transcription source; capability.py single typing home (AA_RESIDUES side_chain/donors/acceptors/charge/rings, ligand typing predicates, METAL_ELEMENTS, RING_PLANARITY_FALLBACK_DEG); spatial.cross_pairs (cell==cutoff exhaustive candidate source); vec3 radians math; setup_state.INTERACTION_TYPES (canonical type order)"
provides:
  - "aamatch/thresholds.py — the approved 10-row table as named constants (18 public names), one source: comment per constant (row # + published source + 2026-09-06 approval date), MAX_CUTOFF computed, AA_PREFILTER_MARGIN=7.5, single-home re-exports of capability's METAL_ELEMENTS + 15-deg fallback; docstring carries the DETECTOR_VERSION bump policy + cell-cutoff note"
  - "aamatch/detector.py — pipeline core: extract_features (donor-H pairs, acceptors, charge-group centers, aromatic rings with row-9 center/normal/radius, hydrophobes, halogen donors, metals — computed ONCE), _aa_bounding_spheres + AA_PREFILTER_MARGIN prefilter, spatial.cross_pairs candidate enumeration, and h_bond/salt_bridge/hydrophobic with explicit partner sides + canonical deterministic records; detect_part1 shares the pipeline 02-07's 7-type version finishes"
  - "Tests pinning transcription truthfulness (provenance scan), boundary sensitivity (141/139 deg, 3.9/4.1 A, center-vs-atom trap), D1 side-chain-only, DETECT-04 agreement (charge-sign parity + aa_capable cross-check), determinism + AA-permutation invariance"
affects: [02-07 detector types 4-7, 02-08 generator solvability, 02-10 scoring, 02-13 SMOKE-03 unclassified-atom assert, 02-14 E2E smoke, 02-15 audit grep]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Two-level pruning: AA bounding sphere (margin 7.5) -> spatial.cross_pairs (cell == shared atom-level cutoff); no full atom-set double loop anywhere"
    - "All cutoffs/angles imported from thresholds — never inlined; _PAIR_CUTOFF computed as max of atom-level rows"
    - "One record per physical contact: best-angle H per (donor, acceptor); hydrophobic = binary-presence record per (AA, ligand) with carbon-set atom_ids"
    - "DETECT-04 by construction: detector charge-group signs == capability.ligand_profile charge_signs (parity pinned); records cross-checked against aa_capable"

key-files:
  created:
    - aamatch/thresholds.py
    - aamatch/detector.py
    - tests/test_thresholds.py
    - tests/test_detector.py
  modified:
    - tests/test_purity.py

key-decisions:
  - "thresholds re-exports capability.METAL_ELEMENTS and capability.RING_PLANARITY_FALLBACK_DEG under their row names (asserted with assertIs) — the recorded 02-05 'reference, do NOT duplicate' decision + gate §4.2 single typing home override the plan's literal 'define constants' wording and the research's 'thresholds standalone' sketch"
  - "Ligand guanidino center = centroid of the 3 bonded Ns (gate §2.3's 'midpoint of 2 Ns' is the protein-side Arg pattern; an isolated guanidinium has three equivalent Ns and no chain anchor) — documented in the module docstring; revisiting = DETECTOR_VERSION event"
  - "Ligand phosphate/sulfonate groups NOT typed in v1: capability._charge_signs does not type them, so the detector must not either (DETECT-04 parity); adding them is a versioned capability change"
  - "One record per (donor heavy, acceptor) with the best-angle attached H (ties -> lowest H id) — two Hs on LYS NZ are one physical contact; donor-uniqueness across donors still NOT deduped (recorded §2.4 deviation stands)"
  - "AA-side donor-H pairing is geometric (AA_H_ATTACH_MAX = 1.5 A, typing-internal epsilon, NOT a gate threshold) so naming variants like chempy's digit-prefixed '2HE' on HIS still pair; SMOKE-03 field-verifies names separately"
  - "unclassified_aa_atoms = non-H AA atoms outside side_chain ∪ {N, CA, C, O, OXT, CB}; hydrophobic enumeration uses side-chain carbons INCLUDING CB (the universal anchor capability deliberately omits from side_chain sets) — both pinned by tests for SMOKE-03"
  - "Halogen-X and metal atoms are precomputed as ligand features and included in the shared cross_pairs point set now, so 02-07 adds classification branches without touching enumeration"

patterns-established:
  - "Provenance scan test: every thresholds constant must have a source: comment with the approval date within its comment window (mechanical truthfulness gate)"
  - "Boundary-sensitivity tests as criteria-table tests (research §6.4): 0.1 A / 1-2 deg outside the boundary flips the verdict"
  - "Canonical record ordering = (INTERACTION_TYPES position, aa object, aa atom_ids, lig atom_ids); determinism + AA-permutation invariance pinned"

# Metrics
duration: 23 min
completed: 2026-09-06
---

# Phase 2 Plan 06: Thresholds + Detector Core Summary

**The approved DETECT-03 table frozen as aamatch/thresholds.py constants plus a pure detector core that precomputes typed features once, prunes far AAs by bounding sphere, enumerates candidates only via spatial.cross_pairs, and classifies h_bond/salt_bridge/hydrophobic with explicit partner sides on scripted boundary geometries.**

## Performance

- **Duration:** 23 min
- **Started:** 2026-09-06T11:15:44Z
- **Completed:** 2026-09-06T11:38:41Z
- **Tasks:** 3/3 (TDD: RED+GREEN for tasks 1-2, registration for task 3)
- **Files modified:** 5 (4 created, 1 modified)

## Accomplishments
- thresholds.py: all 10 approved rows as 18 named constants, each with a `source:` comment (row #, published source, 2026-09-06 approval); MAX_CUTOFF computed from the distance rows; AA_PREFILTER_MARGIN=7.5 headroom invariant pinned; bump policy + cell-cutoff note in the docstring; a provenance-scan test makes "every constant cites source + approval date" mechanical.
- detector.py (825 lines): feature precomputation (donor-H pairs, acceptors, hydrophobes, aromatic rings with row-9 center/normal/radius, charge-group centers, halogen donors, metals), AA bounding-sphere prefilter, cross_pairs-only candidate enumeration, and the three contact types with explicit roles — records `{type, aa{object,atom_ids,resn,resi,role}, lig{object,atom_ids,role}, metrics, formed}`, canonically sorted and deterministic.
- Chemistry policy (research §7) carried in full in the detector docstring: waters fail-closed by side, alt-conf ''/'A' filter (implemented + unit-tested), fail-closed donors, state-1 only, metal-gating preview features, covalent exclusions, MIN_DIST guard, D1 side-chain-only.
- Purity gates extended: PURE_MODULES = 11; full WSL suite 346 green under python3.6 (was 295).

## Task Commits

Each task was committed atomically (TDD discipline):

1. **Task 1: thresholds.py — approved table as constants** — `fdf2ab8` (test RED), `735941d` (feat GREEN)
2. **Task 2: detector core — features, prefilter, candidates, 3 types** — `3ff2b9b` (test RED), `b5fa47d` (feat GREEN incl. post-green helper-order tidy)
3. **Task 3: register thresholds + detector in PURE_MODULES** — `c968629` (test)

**Plan metadata:** (this commit) `docs(02-06): complete ...`

## Files Created/Modified
- `aamatch/thresholds.py` — approved table as constants (single import point for the detector)
- `aamatch/detector.py` — pipeline core + 3 of 7 type tests + canonical record shape
- `tests/test_thresholds.py` — value/completeness/provenance/single-home/docstring pins
- `tests/test_detector.py` — scripted-geometry suite: features, prefilter, boundaries, record contract, capability agreement
- `tests/test_purity.py` — PURE_MODULES 9 -> 11

## Decisions Made
- (see key-decisions in frontmatter) Single-home re-exports in thresholds; guanidino centroid center; phosphate/sulfonate untyped for capability parity; best-H one-record-per-contact; geometric AA donor-H pairing (AA_H_ATTACH_MAX=1.5); CB + known-backbone set defining `unclassified_aa_atoms`; halogen/metal features precomputed now for 02-07.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing Critical] Implemented `apply_altloc_policy` + unit tests**
- **Found during:** Task 2 (detector core)
- **Issue:** detection research §7.2 assigns the alt-conf policy to the pure layer ("keeps alt ''/'A', applied before typing, unit-tested") but neither 02-06 nor 02-07's task lists name the function; the plan only requires the docstring to carry the policy.
- **Fix:** Implemented `apply_altloc_policy(atoms)` (order-preserving, keep ''/'A'/missing) in detector.py, called at the top of `extract_features`, with `TestAltlocPolicy`.
- **Files modified:** aamatch/detector.py, tests/test_detector.py
- **Verification:** test_keeps_blank_and_A_drops_others passes; suite green
- **Committed in:** b5fa47d (Task 2 commit)

**2. [Rule 2 - Missing Critical] Fail-closed input validation for bonds and sides**
- **Found during:** Task 2
- **Issue:** A ligand bond index out of range would silently corrupt every downstream feature; a record with an unknown `side` (water/cofactor) would otherwise be silently dropped — both violate the fail-closed policy class.
- **Fix:** `_validate_ligand_bonds` raises ValueError on out-of-range indices; `_split_sides` raises on any side ∉ {'aa','lig'} (waters can never silently join detection — policy item 1 made structural).
- **Files modified:** aamatch/detector.py, tests/test_detector.py
- **Verification:** test_bond_indices_out_of_range_fail_closed, test_unknown_side_fails_closed
- **Committed in:** b5fa47d

---

**Total deviations:** 2 auto-fixed (both Rule 2, both policy-completing, zero scope creep)
**Impact on plan:** Both additions are required by the research-assigned chemistry policy the plan's docstring mandate references. No architectural changes.

## Issues Encountered
- First GREEN run of test_thresholds failed its own provenance scan (source comments sat outside the scan window; re-exports had no assignment lines) — restructured thresholds.py to one tight `source:` line per constant group and real assignment lines for the re-exports; the scan is now a durable gate.
- Benzamide test fixture initially used a rounded hexagon y (1.204 vs 1.39·sin 60°), making the row-9 radius 1.3901946 — fixture rebuilt with exact trig; detector code was correct.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- **02-07 is ready to extend without rework:** ring features (center/normal/radius), ligand charge groups, halogen donors (C-X pairs), and metal atoms are all precomputed in `extract_features` and included in the shared cross_pairs point set; 02-07 adds `_pi_stacking`/`_cation_pi`/`_halogen`/`_metal` classifiers + the 7-type `detect()` wrapper on the same `_prefilter_pass`/`_atom_candidate_pairs` pipeline.
- `detect_part1` + `_TYPE_ORDER` (INTERACTION_TYPES position) is the canonical-order home 02-07's "canonical completion" test asserts against.
- SMOKE-03 (02-13) contract ready: `features['unclassified_aa_atoms']` exists and scores zero on standard fragment geometry; the known-backbone set {N, CA, C, O, OXT, CB} may need cap-atom names added during 02-13's field verification (reconcile in capability.py, never thresholds).
- Recorded doc tension for the next versioned review: gate §2.3 ligand guanidino "midpoint of 2 Ns" vs the implemented 3-N centroid (documented in the detector docstring, never silent).

---
*Phase: 02-headless-game-engine*
*Completed: 2026-09-06*
