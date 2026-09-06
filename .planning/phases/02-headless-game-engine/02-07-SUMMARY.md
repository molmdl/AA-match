---
phase: 02-headless-game-engine
plan: 07
subsystem: detection
tags: [detector, pi-stacking, cation-pi, ring-geometry, oq-4-anti-artifact, tdd, pure-layer, detect-01, detect-02, detect-04]

# Dependency graph
requires:
  - phase: 02-headless-game-engine
    provides: "02-06 detector pipeline (extract_features with ring features row-9 geometry, AA charge groups, ligand charge groups, _aa_bounding_spheres prefilter, cross_pairs candidates, detect_part1, _canonical_sort); thresholds.py PISTACK_*/CATIONPI_* constants (rows 3-4, approved 2026-09-06); capability.py ring walks + charge typing (single typing home); vec3 plane_project/angle_at"
provides:
  - "aamatch/detector.py (991 lines) — 5 of 7 types detecting (h_bond, salt_bridge, pi_stacking, cation_pi, hydrophobic) on the unchanged 02-06 pipeline: _pi_stacking_records (row 3 uniform test: center dist < 5.5 strict AND normals within 30 deg of parallel OR perpendicular AND min cross-projection offset < 2.0 strict; subtype P/T recorded as a METRIC only) and _cation_pi_records (row 4: charge center <= 6.0 AND projected charge offset < 2.0; BOTH D4 directions with explicit roles + metrics.direction)"
  - "OQ-4 anti-artifact veto (gate §4.4): ligand ammonium groups carry 'substituents' (non-H neighbor points); exactly-three-substituent (tertamine) ligand cations are vetoed when the substituent-plane normal is > 30 deg from the ring normal; the AA side has NO veto (documented asymmetry, proven by a perverse-chain LYS test); degenerate planes and non-tertamines never veto"
  - "15 new scripted-geometry tests (346 -> 361): parallel/T formation with exact metric values, strict-boundary negatives (5.6 A, offset 2.5, normals 45 deg), 6.5 A cation negative, veto-fires + pole-on control pair, D1 backbone-never-typed test, DETECT-04 aa_capable agreement both directions"
affects: [02-07b halogen/metal + canonical detect(), 02-10 scoring partner-side records, 02-13 SMOKE-03 materialized rings, 02-14 E2E placement]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Ring-geometry types as FEATURE-pair classification: aa rings x lig rings and charge groups x rings enumerated directly (tiny counts) — never through the atom-level cell list; the bounding-sphere prefilter covers them (feature centers lie inside side spheres)"
    - "min cross-projection offset (each ring center into the opposite ring's plane) — PLIP pistacking's form, makes the single uniform test order-independent and admits the T-shaped case the plan scripts"
    - "Unsigned line angle for normals folded to [0,90] via min(theta, 180-theta); T-branch condition a >= 90 - PISTACK_ANGLE_TOL_DEG"

key-files:
  created: []
  modified:
    - aamatch/detector.py
    - tests/test_detector.py

key-decisions:
  - "pi_stacking offset = min over BOTH cross-projections (verified from PLIP detection.py pistacking on 2026-09-06, the gate's own source file) — a one-sided projection would make the plan's T-shaped case (center 5.0 A away with offset 1.0) impossible to form, since projecting the ligand center onto a perpendicular plane leaves the full 4.9 A separation"
  - "OQ-4 veto semantics are KEPT-when-<=30/rejected-when->30 (PLIP detection.py pication + gate row 4/§4.4: 'amine-plane normal vs ring normal <= 30 to count'); the veto applies only to ligand ammonium groups with EXACTLY three non-H substituents (PLIP tertamine — quaternary ammonium, primary/secondary amines and guanidino never veto), and a collinear substituent plane carries no normal and cannot veto"
  - "The veto angle reuses thresholds.PISTACK_ANGLE_TOL_DEG (30.0): the gate's 30-deg veto value equals the approved row-3 tolerance and PLIP itself hardcodes 30.0 == PISTACK_ANG_DEV in detection.py; thresholds.py is OUTSIDE this plan's allowed file set, so no new constant could be added — the reuse is docstring-documented"
  - "pi_stacking/cation_pi metrics are fixed record-contract keys: pi_stacking {d_center, angle_deg, offset, subtype}; cation_pi {d_center, offset, direction} — partner-side roles 'ring'/'cation' as appropriate"

patterns-established:
  - "Ring-type tests always scope asserts with _of_type (a scripted aromatic ligand's ring carbons qualify as hydrophobes — a stray hydrophobic record must never fake a miss or a false pass)"
  - "Veto proof by control pair: identical geometry with the veto condition flipped (substituent-plane normal parallel vs perpendicular) must form, proving the miss is the VETO and not a distance/offset accident"

# Metrics
duration: 11 min
completed: 2026-09-06
---

# Phase 2 Plan 07: Detector Part 2a — pi_stacking + cation_pi Summary

**The two ring-geometry interaction types now detect on the shared 02-06 pipeline with scripted-boundary geometry: pi_stacking via the single uniform row-3 test (parallel AND T-shaped, subtype as a metric only) and cation_pi in both D4 directions with the OQ-4 ligand-side tertiary-amine anti-artifact veto — detector.py carries 5 of 7 types, WSL suite 361/361 green, purity gates untouched.**

## Performance

- **Duration:** ~11 min (16:22Z -> 16:33Z; baseline 346/361 runs included)
- **Tasks:** 2/2 (Task 1 TDD RED -> GREEN; Task 2 full-suite gate)
- **Tests:** 346 -> **361/361 green** (+15; `python3.6 -m unittest discover -s tests` OK 2.8 s; `python3.6 -m py_compile aamatch/*.py` clean; purity gates inside the suite)

## Completed Tasks

| Task | Name | Commit | Files |
| --- | --- | --- | --- |
| 1 (RED) | Failing scripted-geometry tests (pi + cation-pi) | cf0529d | tests/test_detector.py |
| 1 (GREEN) | pi_stacking + cation_pi implementation | f0fc52f | aamatch/detector.py |
| 2 | Full-suite gate (no code, evidence below) | — | — |

## What Was Built

- `_pi_stacking_records(features, near_objs)` — row 3: center distance < `PISTACK_CENTER_D_MAX` (strict), normals within `PISTACK_ANGLE_TOL_DEG` of parallel **or** perpendicular (single test; sub-type 'P'/'T' recorded as a metric), offset < `PISTACK_OFFSET_MAX` (strict) with the offset = **min of both cross-projections** (each ring center projected into the opposite ring's plane via `vec3.plane_project` — the PLIP pistacking form). Ring pairs enumerated directly off the existing 02-06 ring features; the AA bounding-sphere prefilter covers them (every feature center lies inside its side's sphere).
- `_cation_pi_records(features, near_objs)` — row 4: charge center ↔ ring center ≤ `CATIONPI_D_MAX` and projected charge offset < `CATIONPI_OFFSET_MAX`, both directions per D4 (`aa_cation_over_lig_ring` with roles cation/ring; `aa_ring_under_lig_cation` with roles ring/cation; `metrics.direction` disambiguates).
- **OQ-4 veto (`_substituent_plane_veto`)** — ligand-side only: an ammonium ligand cation with exactly three non-H substituents (PLIP tertamine) is rejected when its substituent-plane normal is more than 30° from the ring normal ('pi-cation interaction through the ligand'); the AA side has no veto (asymmetry proven by forming a LYS whose chain is scripted in the exact through-plane shape the ligand veto rejects). `_ligand_charge_groups` now annotates ammonium groups with their non-H `substituents` — a feature extension, not a typing change.
- Records keep the canonical shape `{type, aa{...}, lig{...}, metrics, formed}`; `detect_part1` emits 5 types in canonical `INTERACTION_TYPES` order — the 02-06 record-contract tests (shape/order/determinism/AA-permutation invariance) pass unchanged on the combined scene.

## Tests (new: 15; total: 361/361)

- `TestPiStacking` (7): parallel formation (d=√21.25, angle≈0, offset=1.0, subtype 'P', exact atom-id pins); 5.6 Å strict-distance miss; T-shaped formation (center 5.0 Å, normals perpendicular, offset 1.0 via the min cross-projection, subtype 'T'); offset-2.5 miss with distance+angle passing; 45°-normals miss with distance+offset passing; D1 backbone-never-typed proof (PHE fragment without ring atoms); capability agreement.
- `TestCationPi` (8): LYS NZ 5.5 Å over benzene (offset 1.0, direction aa_cation_over_lig_ring); ammonium ligand under PHE ring (direction aa_ring_under_lig_cation); 6.5 Å miss; offset-2.5 miss; OQ-4 veto fires (perpendicular amine plane) **plus the pole-on control that forms** (proves the miss is the veto); AA-side no-veto asymmetry proof; capability agreement both directions.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Plan case (e) prose inverts the OQ-4 veto geometry**

- **Found during:** Task 1 test scripting (cross-checked against PLIP detection.py `pication`, the gate document's own verified source file, before implementing)
- **Issue:** The plan scripts "substituent-plane normal is ~parallel to the ring normal … -> NOT formed". PLIP's verified code keeps the hit when the angle (folded to [0,90]) is **not > 30°** and rejects when > 30° — i.e., ~parallel normals (≈0°) are KEPT; the rejection case is a large angle (the edge-on/'through' arrangement). The frozen gate row 4/§4.4 says the same ('amine-plane normal vs ring normal ≤ 30° to count'). The plan's parenthetical 'amine stacked "through" the ring' describes the rejection case, so intent is clear, but the angle direction is inverted.
- **Fix:** Implemented the gate/PLIP semantics; scripted the veto test with a ~perpendicular substituent plane normal (veto fires → NOT formed) and added a control with a ~parallel normal in otherwise identical geometry (veto passes → FORMED). The control-pair construction also proves the verdict comes from the veto, not from distance/offset.
- **Files modified:** tests/test_detector.py (veto + control tests)
- **Commit:** cf0529d (tests), f0fc52f (implementation)

**2. [Rule 2 - Missing Critical] pi_stacking requires the min of BOTH cross-projections (plan's single 'projected-center offset' is under-specified)**

- **Found during:** Task 1 design (T-shaped case (c) analysis)
- **Issue:** A one-sided projection cannot satisfy the plan's T-shaped case (AA center 5.0 Å from the ligand center with the AA plane perpendicular): projecting the ligand center onto the perpendicular AA plane leaves the full ~4.9 Å in-plane separation (≥ 2.0 → would falsely reject a FORMED case).
- **Fix:** Adopted PLIP pistacking's verified form — offset = min over both cross-projections (each ring center into the opposite ring's plane), verified from PLIP detection.py on 2026-09-06. This is order-independent, matches the plan's parallel case (both projections equal) and admits the T-shaped case exactly as the plan scripts it.
- **Files modified:** aamatch/detector.py
- **Commit:** f0fc52f

No authentication gates; no Rule 3 blockers; no Rule 4 architectural changes (pipeline extended, not restructured; allowed file set respected).

## Next Phase Readiness

- **02-07b (wave 7)** adds halogen + metal classification on the same features/candidates and wraps the full 7-type `detect()`; the halogen-X/metal candidate atoms already ride the shared `cross_pairs` point set (02-06), so 02-07b is classification-only plus the `detect_part1` → `detect()` rename/wrap (rename ripples into the test file's entry points).
- **Record contract now final for ring types** (success criterion): roles 'ring'/'cation', metrics keys {d_center, angle_deg, offset, subtype} and {d_center, offset, direction} — scoring (02-10) and placement (02-14) should bind to these exactly.
- The OQ-4 veto's 30° constant reuse (`PISTACK_ANGLE_TOL_DEG`) is documented in the detector docstrings; if a future versioned review wants an independent row-4 veto constant, that is a `DETECTOR_VERSION` bump event in thresholds.py (§4.7), never a silent edit.
