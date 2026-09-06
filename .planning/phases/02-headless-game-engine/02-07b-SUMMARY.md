---
phase: 02-headless-game-engine
plan: 07b
subsystem: detection
tags: [detector, halogen-bond, metal-coordination, canonical-detect, two-angle-windows, metal-gating, tdd, pure-layer, detect-01, detect-02, detect-04]

# Dependency graph
requires:
  - phase: 02-headless-game-engine
    provides: "02-06 pipeline (features/prefilter/candidates incl. halogen-X + metal typed atoms already riding cross_pairs) + 02-07 ring types and canonical sort; thresholds.py HALOGEN_*/METAL_* constants (rows 6-7, approved 2026-09-06); capability.py ligand_has_metal gate + §3.5 sets (Met excluded from both halogen-acceptor and metal-chelator sets); 02-08 generator contract (detect_part1 consumers)"
provides:
  - "aamatch/detector.py (1188 lines) — COMPLETE 7-type surface: detect() emits canonical records for every INTERACTION_TYPES member through the unchanged 02-06 pipeline; _halogen_records (row 6: A...X <= 4.0 inclusive AND donor angle ∠(A...X-C) at X in (135,195) AND acceptor angle ∠(Y-A...X) at A in (90,150), windows INCLUSIVE from thresholds; structurally (AA acceptor x ligand C-X) only; C-F excluded at typing) and _metal_records (row 7: distance-only <= 3.0, chelator=capability acceptor, gated on capability.ligand_has_metal BEFORE enumeration)"
  - "acceptor-side Y anchor for row 6: geometric pairing HALOGEN_Y_ATTACH_MAX=2.0 (typing-internal epsilon like AA_H_ATTACH_MAX, fail-closed, docstring-carried) — the angle is never guessed"
  - "25 new scripted-geometry tests (438 -> 463): both-window boundary/break negatives, C-F no-candidates-at-all, AA-side C..CL structural impossibility, MET thioether exclusion per §3.5, metal gating spy (no metal -> _metal_records never called), NA-element non-typing, capability parity rows 6/7, canonical 7-type order/closed-set/count/determinism contract"
affects: [02-10 scoring partner-side records, 02-11 engine detect() wiring, 02-13 SMOKE-03, 02-14 E2E placement/scoring]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "One-directional interaction types enforced STRUCTURALLY by enumeration (AA acceptor atoms by capability name) x (ligand typed donors) — side rules are not checked, they are unrepresentable"
    - "Feature-gated enumeration: detect() consults capability.ligand_has_metal and skips the whole row-7 branch on a metal-free ligand (generator/detector gate symmetry, §7.6) — spy-pinned by mock.patch.object"
    - "Met exclusion falls OUT of the acceptor-name context (no special-case code): MET carries acceptors=() in capability, so its thioether SD never joins an acceptor candidate — the §3.5 ruling lives in exactly one table"

key-files:
  created: []
  modified:
    - aamatch/detector.py
    - tests/test_detector.py

key-decisions:
  - "Row-6 angle windows are INCLUSIVE (thresholds transcription tuples (135,195)/(90,150); donor upper bound 195 is inert on acos∈[0,180] per the row-6 implementer note, applied uniformly) — distance <= per thresholds comment like row 1"
  - "Row-6 Y anchor = acceptor's heavy-atom bond partner, paired GEOMETRICALLY (nearest non-H same-object atom within HALOGEN_Y_ATTACH_MAX=2.0; typing-internal, 02-07b-recorded like AA_H_ATTACH_MAX=1.5; no partner -> no angle -> no candidate, fail-closed) — AA fragments carry no bond block, so Y cannot come from connectivity"
  - "detect() = the complete 7-type entry; detect_part1 keeps its 5-of-7 contract byte-identical (02-08 generator tests consume it). Shared _pipeline preamble + _part1_records emitters; Task-2 wiring landed inside Task 1's GREEN (c582405) because Task-1 RED tests call detector.detect — the a5caf41 test commit pins the canonical contract"
  - "Record contract frozen: halogen roles acceptor/donor, aa atom_ids=[acceptor id], lig atom_ids=[C id, X id] sorted, metrics {d_ax, donor_angle_deg, acc_angle_deg}; metal roles chelator/metal, metrics {d_metal}; both one record per (AA atom, ligand atom) contact"

patterns-established:
  - "Spy-proof of a gating rule: mock.patch.object(detector, '_metal_records', wraps=original) + call_count==0 proves the metal-free ligand never enumerates the branch (no behavioral contrivance needed)"
  - "Closed-set proof by construction: len(INTERACTION_TYPES)==7 + every record type In enum + enum-order filter equals reported order"

# Metrics
duration: ~35 min
completed: 2026-09-06
---

# Phase 2 Plan 07b: Detector Part 2b — halogen + metal + canonical 7-type detect() Summary

**The pure detector is COMPLETE: rows 6/7 join the pipeline with structurally-enforced side rules (halogen = AA acceptor × ligand C-X only, C-F never typed; metal = distance-only, gated on ligand metal presence), and detect() now emits the closed 7-type canonical record surface that scoring (02-10) and the E2E smoke (02-14) bind against — WSL suite 463/463 green, purity gates untouched.**

## Performance

- **Duration:** ~35 min (17:10Z -> 17:45Z; baseline 438/463 runs included)
- **Tasks:** 2/2 (Task 1 TDD RED -> GREEN; Task 2 canonical contract + full-suite gate)
- **Tests:** 438 -> **463/463 green** (+25; `python3.6 -m unittest discover -s tests` OK 3.0 s; `python3.6 -m py_compile aamatch/*.py` clean; purity gates inside the suite)

## Completed Tasks

| Task | Name | Commit | Files |
| --- | --- | --- | --- |
| 1 (RED) | Failing scripted-geometry tests (halogen + metal) | 7752fb1 | tests/test_detector.py |
| 1 (GREEN) | halogen + metal implementation + detect() wiring | c582405 | aamatch/detector.py, tests/test_detector.py |
| 2 (contract) | Canonical 7-type surface tests (order/closed-set/count/determinism) | a5caf41 | tests/test_detector.py |

## What Was Built

- `_halogen_records(features, near_objs, lig_ctx, atom_pairs)` — row 6: `MIN_DIST < d(A···X) <= HALOGEN_D_MAX` AND donor angle ∠(A···X-C) vertex-at-X in `HALOGEN_DONOR_ANGLE_DEG=(135,195)` AND acceptor angle ∠(Y-A···X) vertex-at-A in `HALOGEN_ACC_ANGLE_DEG=(90,150)` (both windows INCLUSIVE, imported from thresholds; the 195 upper bound is inert on acos∈[0,180] per the row-6 implementer note). Enumeration is **one-directional by construction**: AA-side atoms must be capability-named acceptors (O/N/S set incl. Met-EXCLUDED) and ligand-side atoms must be the X of a typed C-X pair — C-F never enters `features['lig']['halogen_donors']`, so no candidate exists at all; an AA-side halogen is unrepresentable.
- `_halogen_y_partner(acceptor_rec, atoms)` — the row-6 acceptor-side "Y" (the acceptor's heavy-atom bond partner) paired geometrically: nearest non-H same-object atom within `HALOGEN_Y_ATTACH_MAX = 2.0` (typing-internal epsilon, same status as `AA_H_ATTACH_MAX = 1.5`; docstring-carried). No partner in range -> no angle -> no candidate (fail-closed, never guessed).
- `_metal_records(features, near_objs, lig_ctx, atom_pairs)` — row 7: `MIN_DIST < d <= METAL_D_MAX`, **distance-only** (BINANA's adopted rationale). Chelation atoms = the capability acceptors (side-chain N/O/S, D1); a non-chelator AA like ALA produces nothing even in contact.
- `detect(atom_records, ligand_bonds)` — the complete 7-type surface on the unchanged 02-06 pipeline (`_pipeline` shared preamble + `_part1_records` five-type emitters, kept byte-identical as `detect_part1` for the 02-06/02-07/02-08 consumers). Metal enumeration is **gated**: `if ligand_has_metal(features['lig']['atoms'])` — a metal-free ligand never runs the row-7 branch (spy-pinned). Output = the records of all five part-1 emitters + halogen (+ metal when gated in), `_canonical_sort`-ordered: `(INTERACTION_TYPES position, aa object, aa atom_ids, lig atom_ids)`. Closed set: every record type is an enum member by construction.
- Module/policy docstrings updated: metal-gating §5 item promoted from "PREVIEW" to the implemented gate; halogen Y-anchor + chelator policies recorded next to the other typing policies; `min_lines: 1000` artifact requirement comfortably exceeded (1188).

## Tests (new: 25; total: 463/463)

- `TestHalogen` (9): formed at 3.5 Å/165°/120° with exact metric values and id pins; donor 100° and acceptor 60° window negatives (other window passing); C-F at perfect geometry -> no candidates AT ALL (feature list asserted empty); AA-side C..CL at textbook flipped geometry -> nothing (feature-level structural proof: no ligand donors, no AA acceptors, CL counted unclassified); MET SD at perfect geometry -> nothing (§3.5 ruling — falls out of acceptors=(), not a special case); 4.0-yes/4.1-no distance boundary; donor-window 134° and MIN_DIST guards.
- `TestMetal` (7): ZN + HIS ND1 at 2.5 Å formed (roles chelator/metal, `d_metal` metric, id pins); 3.0 Å inclusive boundary formed; 3.2 Å not; **metal-free ligand gate** — same geometry with a carbonyl ligand: no record and `_metal_records` call_count == 0 (wraps-spy); `'NA'` not in `METAL_ELEMENTS` -> feature list empty and no record; ALA (non-chelator) in contact -> nothing; MIN_DIST guard.
- `TestHalogenMetalCapabilityParity` (2): DETECT-04 for rows 6/7 — formed records' (resn, type) agree with `capability.aa_capable` on the SAME profile; scripted exclusions (MET/metal-free) stay incapable; `profile['metal_elements'] == ['ZN']` pin.
- `TestCanonicalDetect` (7): combined scene (SER h_bond + PHE pi_stacking + ALA hydrophobic via `detect()`) gives exactly 3 records in enum-positions order; full sort-key ordering; closed-set proof (`len(INTERACTION_TYPES) == 7`, type ∈ enum, enum-filter order == reported order); partner role pins; halogen/metal riding positions 5/6 after the part-1 pages in a dual-feature scene; `detect_part1` byte-identical on the no-extra-features scene; determinism + AA-record-order permutation invariance.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing Critical] Row-6 acceptor-side "Y" anchor cannot come from connectivity (AA fragments carry no bond block)**

- **Found during:** Task 1 design (scripting the acceptor-angle geometry)
- **Issue:** Row 6's ∠(Y-A···X) reads the acceptor's bond partner "Y". The detector's AA side has no bond block (cross-side enumeration is the covalent exclusion), and capability tables name acceptor atoms but not their partners — the 02-06-style bond-graph lookup used on the ligand side does not exist here. Without a Y source the acceptor-angle leg of the row-6 criterion is unimplementable.
- **Fix:** Geometric pairing with a typing-internal epsilon, mirroring the established `AA_H_ATTACH_MAX = 1.5` donor-H precedent: `_halogen_y_partner` = nearest non-H same-object atom within `HALOGEN_Y_ATTACH_MAX = 2.0` (all typed AA acceptor single bonds C-O/C-N/C-S are ≤ ~1.8 Å, and a second heavy atom cannot sit within 2.0 Å in a sane fragment). No partner in range -> no candidate (fail-closed). Policy recorded in the module docstring; tests script fragments where the only heavy atom within 2.0 Å is the scripted Y.
- **Files modified:** aamatch/detector.py (implementation + docstring policy), tests/test_detector.py (_serine_og_cb/_methionine_sd/_histidine scripted-fragment helpers)
- **Commit:** c582405

**2. [Process note, not a rule deviation] Task-2 GREEN wiring landed inside Task-1 GREEN (c582405)**

- **Found during:** Task 2 execution
- **Issue:** The plan scripts Task 2 as RED-then-GREEN "wire all 7 types into detect()". But Task 1's RED tests already call `detector.detect(...)` (the natural public surface), so the canonical entry had to be wired by Task 1's GREEN commit to make Task 1 green. The Task-2 RED commit (a5caf41) therefore passes on arrival.
- **Fix:** Kept the wiring in c582405 (one atomic implementation commit covering rows 6/7 + the canonical surface) and made a5caf41 a contract-pinning test commit documenting this, rather than artificially splitting the implementation. Both plan-named commit subjects exist in history (`feat(02-07b): halogen + metal (TDD)` carries the wiring; the canonical-surface contract is pinned by `test(02-07b): canonical 7-type surface contract`).
- **Files modified:** none extra
- **Commit:** — (documented in c582405 / a5caf41 messages)

No Rule 1 bugs found; no Rule 3 blockers; no Rule 4 architectural changes (pipeline extended, not restructured; allowed file set respected); no authentication gates.

## Next Phase Readiness

- **02-10 (scoring)**: bind to `detector.detect(atoms, bonds)` — presence-based fraction scoring consumes record types only; the record contract is FINAL for all 7 types (halogen {d_ax, donor_angle_deg, acc_angle_deg}, metal {d_metal}, roles as pinned above). `detect_part1` remains available but is the 5-of-7 legacy entry — new consumers use `detect()`.
- **02-11 (engine)**: wire `detect()` = `extract_game_atoms()` + the probe-pinned bond remap; note metals/π features already ride features precomputation (no extra cmd work).
- **02-13 (SMOKE-03)**: material-real AA fragments subject AA-side acceptors to the new Y-anchor pairing — a fragment whose acceptor sits > 2.0 Å from every non-H atom is malformed, so `HALOGEN_Y_ATTACH_MAX` doubles as a fragment sanity bound; the unclassified-atoms assertion stays the cap-name reconciliation home.
- **Record determinism** (canonical sort incl. the two new types) is pinned under AA-record-order permutation; placement replay (02-14) can rely on byte-stable record lists.
