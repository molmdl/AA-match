---
phase: 02-headless-game-engine
plan: 11
subsystem: testing
tags: [detector, property-tests, invariance, sensitivity-controls, perf-guard, pure-layer, detect-05]

# Dependency graph
requires:
  - phase: 02-headless-game-engine
    provides: "02-07b's COMPLETE 7-type detector.detect() canonical record surface; thresholds.py rows 1-7 + MAX_CUTOFF/AA_PREFILTER_MARGIN constants; capability.AA_RESIDUES ring walk (PHE) for scripted fragments; 02-13 STATE note that HALOGEN_Y_ATTACH_MAX doubles as a fragment sanity bound"
provides:
  - "tests/test_detector_invariance.py (1148 lines) — property battery over the complete 7-type detect(): 100-seed rigid-transform invariance (two retained-ligand scripted scenes covering 6 of 7 types), 25-seed permutation invariance with ligand bond-block remap, bit-identical determinism, per-type sensitivity controls (7/7, thresholds-driven, +0.2 A/deg kills / −0.2 restores, metal includes the ligand_has_metal gate toggle ZN→C→ZN), and the WSL loose perf guard (81 PHE + 200-atom ligand crammed within MAX_CUTOFF, ~0.4–0.9 s wall vs the 2.0 s guard)"
  - "the two-tier metric-comparsion rule for rigid-transform tests: distances/offsets are dot-product-conditioned (1e-9, per plan); acos-derived *_angle_deg metrics near degenerate configurations get 1e-6 (documented sqrt(eps) conditioning argument — the plan's 1e-9 is mathematically unattainable there)"
affects: [02-14 engine detect() wiring (record determinism under placement replay is now property-proven, not just unit-pinned), 02-15 perf smoke (budget assertion follows the loose WSL guard), DETECT-05]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Rigid-transform property testing in WSL with plain-list Rodrigues rotation (gaussian axis + uniform angle, random.Random(seed)) — zero numpy; record STRUCTURE compared exactly, metrics via the two-tier tolerance comparator (METRIC_ABS_TOL=1e-9, ANGLE_ABS_TOL=1e-6)"
    - "Multi-ligand scripted scenes carried as TWO groups but detected with exactly ONE retained ('keep a' / 'keep b' variants) so a single builder proves six gate-less types without cross-ligand contamination"
    - "Sensitivity control = executable threshold documentation: each type scripts formed → 0.2 A/deg outside → 0.2 A/deg inside, deltas applied to thresholds.py constants (NEVER inlined)"

key-files:
  created:
    - tests/test_detector_invariance.py
  modified: []

key-decisions:
  - "Transform-invariance metric comparison is two-tier (Rule 1 deviation): dot-product-conditioned metrics (d_*, offset) hold the plan's 1e-9 (observed drift ≤ 1e-13 with ~50 A gaussian translations); acos-derived angle metrics at scripted DEGENERATE geometries (parallel ring normals = exactly 0.0 deg) are conditioned as sqrt(eps_of_cosine) and drifted ~8.5e-7 in the worst of 100 seeds — 1e-9 is provably unattainable there, so *_angle_deg keys use 1e-6 with the conditioning argument documented in-file. Record type/objects/roles/atom_ids/metric keys and non-float metrics stay EXACT."
  - "The metal sensitivity control is cutoff + GATE TOGGLE: identical geometry with the ligand atom swapped ZN → C (not in METAL_ELEMENTS) kills the record via ligand_has_metal, swapping back restores it — per the plan's 'metal toggles the ligand's metal presence per the gating rule' (there is no metal-free geometry variant of the cutoff itself)."
  - "The WSL perf guard scripts 81 PHE + a 200-atom carbon-chain ligand crammed inside one MAX_CUTOFF ball: every 10th ligand atom is H so ~180 atoms are qualifying hydrophobes, forcing all 81 AAs through candidate generation AND hydrophobic classification (81 real records) — an early draft with alternating C/N/O produced ZERO records (carbons bonded to N/O never qualify), which would have made the guard toothless."

patterns-established:
  - "Worst-case perf scripting must assert a NON-ZERO record count via printed runtime+count evidence — a 0-record 'worst case' measures nothing"
  - "Donor-angle scripting rule: X→C at donor_deg from X→A means X→C = L·(cos(donor)·u + sin(donor)·v) with u = unit(X→A) — getting the sign of cos wrong yields 180°−donor (caught here twice; both fixed before commit)"

# Metrics
duration: ~27 min
completed: 2026-09-06
---

# Phase 2 Plan 11: Detector Invariance / Sensitivity Property Suite Summary

**The detector's 7-type surface is now property-proven in WSL: 100-seed rigid-transform invariance (record structure exact, metrics two-tier tolerant), seeded permutation invariance with bond-block remap, bit-identical determinism, thresholds-driven kill/restore sensitivity controls for all 7 types (including the metal gate toggle), and a worst-case crammed-scene perf guard at 0.4–0.9 s vs the 2.0 s bound — suite 507 → 521 green, DETECT-05's WSL correctness half closed.**

## Performance

- **Duration:** ~27 min (17:57Z → 18:24Z; includes baseline run + full-suite gate)
- **Tasks:** 2/2 (one commit — both plan tasks write only tests/test_detector_invariance.py; 02-07b precedent)
- **Tests:** 507 → **521/521 green** (+14; full suite 39.8 s under python3.6; `py_compile aamatch/*.py` clean; purity gates untouched — the new file imports only math/random/time/unittest + aamatch pure modules)

## Completed Tasks

| Task | Name | Commit | Files |
| --- | --- | --- | --- |
| 1 | Invariance properties (transform ×100 seeds ×2 scenes / permutation ×25 / determinism) | 135036c | tests/test_detector_invariance.py |
| 2 | 7-type sensitivity controls + WSL loose perf guard | 135036c | tests/test_detector_invariance.py |

## What Was Built

- **TestTransformInvariance** — two scripted scenes, each producing exactly 3 records: `keep_b=False` (ligand A: benzene + amide + ammonium J + C16-Cl17) fires h_bond/salt_bridge/halogen; `keep_b=True` (ligand B at (20,20,0): ring K + carboxylate + hydrophobe chain) fires pi_stacking/cation_pi/hydrophobic. 100 random Rodrigues rotations + gaussian translations each (seeded `random.Random`, plain list math — no numpy): record structure compared EXACTLY, metrics two-tier (`_assert_records_equivalent`).
- **TestPermutationInvariance** — 25 seeded FULL shuffles of the atom list with the ligand bond block remapped into the ligand sub-sequence's new positions (the detector contract), plus reversed AA blocks; identical canonical lists.
- **TestDeterminism** — `detect()` twice on each scene: identical lists, distinct objects.
- **TestSensitivity** — 7/7 types: formed baseline → +0.2 A (or angle outside the window) kills → −0.2 A/deg inside restores, every cutoff read from `thresholds` (never inlined: HBOND_D_MAX/ANGLE_MIN, SALT_CENTER_D_MAX, PISTACK_CENTER_D_MAX/ANGLE_TOL/OFFSET…, CATIONPI_D_MAX/OFFSET_MAX, HYDRO_D_MAX, HALOGEN_D_MAX + both angle windows, METAL_D_MAX). Metal additionally gets the **gate toggle**: same geometry with a 'C' stand-in replaces ZN → `ligand_has_metal` false → zero records; swapping back restores. A closed-surface drift guard pins the 7-type enum.
- **TestWSLPerfGuard** — 81 PHE AAs (13 atoms each) + 200-atom ligand ALL crammed in one 2 A-radius ball: 81 hydrophobic records materialize (maximal contact load) in **0.43–0.86 s wall** across runs vs the 2.0 s guard. Docstring carries the "regression guard, NOT the DETECT-05 budget (02-15 headless)" ruling verbatim.
- **Combined-scene geometry notes**: the salt bridge uses a formal-charge ammonium with NO hydrogens (zero donor typing → no shadow h_bond); the halogen Y partner (CB at 1.43 A, exactly 120°) is the ONLY heavy atom within the detector's 2.0 A pairing epsilon of SER OG, honoring the 02-13 STATE note that `HALOGEN_Y_ATTACH_MAX` doubles as a fragment sanity bound; tilted pi_stacking variants carry extra +z so ring carbons never dip below HYDRO_D_MAX (no stray hydrophobic can fake a kill or a restore).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Plan's 1e-9 metric tolerance is unattainable for acos-derived angle metrics at degenerate scripted geometries**

- **Found during:** Task 1 (first transform-invariance run — seed 0 drifted pi_stacking's `angle_deg` from exactly 0.0 to 8.54e-07)
- **Issue:** Angle metrics come from `math.acos` of ratios of unit vectors; near 0°/180° the output error grows like sqrt(eps of the cosine). With ~50 A gaussian translations (plan-suggested scale), the cosine drifts ~1e-13, so a scripted EXACTLY-parallel pi-stack angle drifts ~1e-6–1e-7 — an order above the plan's 1e-9. No implementation change can fix this; it is float conditioning, and rejecting all degenerate scripted geometries would gut the sensitivity scenes.
- **Fix:** Two-tier comparator `_assert_records_equivalent`: record structure (type/aa/lig dicts/formed/metric keys/non-float metrics) EXACT; dot-product-conditioned metrics (distances, offsets — observed drift ≤ 1e-13) keep the plan's `METRIC_ABS_TOL = 1e-9`; `*_angle_deg` metrics use `ANGLE_ABS_TOL = 1e-6` with the conditioning argument documented in-file (any real geometric change shifts an angle by orders of magnitude more than 1e-6, so the invariant stays meaningful).
- **Files modified:** tests/test_detector_invariance.py
- **Commit:** 135036c

**2. [Rule 1 - Bug] Scripted-ligand bond-block typo broke ammonium + halogen typing in the combined scene**

- **Found during:** Task 1 debugging (scene produced only h_bond)
- **Issue:** My ligand A bond list carried a stray `(11, 15)` N12–C16 bond and omitted the `(15, 16)` C–Cl bond; N12 ended up with 5 neighbors (so the ammonium group never typed → no salt bridge target) and Cl had no carbon partner (no halogen donor at all). Also an early N9–N12 bond made the amide N a spurious second ammonium.
- **Fix:** Rebound: N12 ammonium attached to ring C1 (`(0, 11)`) with its 3 Hs; C16–CL17 bonded (`(15, 16)`); ligand A charge groups verified programmatically = exactly one '+' ammonium at N12.
- **Files modified:** tests/test_detector_invariance.py
- **Commit:** 135036c (pre-commit fix; never reached the suite)

**3. [Rule 1 - Bug] Donor-angle sign flip (twice) in halogen scripting**

- **Found during:** Task 1/2 verification
- **Issue:** `X→C` at `donor_deg` from `X→A` is `L·(cos(donor)·u + sin(donor)·v)`; a `-cos` coefficient produces `180° − donor` (165° scripted → 15° measured). Caught once in `_halogen_scene` and once in `_halogen_against` (both mine).
- **Fix:** Sign corrected in both helpers; geometry re-verified by direct angle probes (donor 165.0, acceptor 120.0, d_ax exact).
- **Files modified:** tests/test_detector_invariance.py
- **Commit:** 135036c (pre-commit fix)

**4. [Rule 2 - Missing Critical] First worst-case perf scene produced ZERO records (toothless guard)**

- **Found during:** Task 2 (guard printed `0 records`)
- **Issue:** Alternating C/N/O chain atoms meant every carbon was bonded to an N or O — zero qualifying hydrophobes — and the chain graph had no rings, so the "worst case" skipped all contact classification (the very work it exists to measure).
- **Fix:** Ligand rebuilt as a 200-atom carbon chain with every 10th a terminal H (~180 qualifying hydrophobes) → all 81 PHE AAs generate candidates AND emit their binary hydrophobic record (81 records printed per run with wall time).
- **Files modified:** tests/test_detector_invariance.py
- **Commit:** 135036c (pre-commit fix)

**5. [Rule 2 - Missing Critical] 45°-tilt pi_stacking kill was contaminated by a stray hydrophobic record**

- **Found during:** Task 2 (tilted ring's lowest carbon dropped to 3.54 A from a ligand ring carbon → PHE hydrophobic fired, breaking the "exactly that type disappears" assertion)
- **Fix:** Tilted variants re-centered higher (+0.7 A z on the kill, 4.8 A on the 15° restore) so every ring carbon stays beyond HYDRO_D_MAX while distance/offset still pass — the angle clause alone decides.
- **Files modified:** tests/test_detector_invariance.py
- **Commit:** 135036c (pre-commit fix)

**Process note (not a rule deviation):** both plan tasks write ONLY `tests/test_detector_invariance.py`; like 02-07b, Tasks 1+2 landed in one atomic test commit (135036c) rather than an artificial file-split.

No Rule 3 blockers; no Rule 4 architectural changes; allowed file set respected (aamatch/ and other test files untouched); no authentication gates.

## Next Phase Readiness

- **02-14 (engine)**: detect() record lists are now property-proven invariant under whole-scene rigid transforms and atom-order permutation — placement replay (spec re-bake) can rely on byte-stable formed sets; the engine can assert determinism cheaply by reusing `_assert_records_equivalent`-style two-tier comparison if it ever composes matrices itself.
- **02-15 (perf smoke / audit)**: the WSL loose guard records actual runtime (0.43–0.86 s for the 1253-atom crammed scene) as the regression baseline; the REAL < 100 ms DETECT-05 budget remains a headless-only assertion per research §8.4 — do NOT import this 2.0 s constant into the smoke.
- **Detector correctness WSL-side is closed**: unit (507 prior) + property (14 new) cover the 7-type surface; remaining detector risk is cmd-tier (02-14/02-15's domain).

---
*Phase: 02-headless-game-engine*
*Completed: 2026-09-06*
