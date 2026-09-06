---
phase: 02-headless-game-engine
plan: 05
subsystem: typing
tags: [capability, typing, chemistry, tdd, pure-layer, detect-03, detect-04, gen-04]

# Dependency graph
requires:
  - phase: 02-headless-game-engine
    provides: "DETECT-03 gate doc (docs/DETECTION_THRESHOLDS.md, APPROVED 2026-09-06) — the transcription source; setup_state.INTERACTION_TYPES (one enum home); vec3 (radians angle math for the planarity fallback)"
provides:
  - "aamatch/capability.py — the SINGLE atom/residue typing home: AA_RESIDUES (20 AAs), resolved-set accessors, aa_capable (D3/D4 polarity-aware), residue_capabilities, AA_TOKENS (20-token vocabulary), ligand_profile, ligand_support (§2.4), ligand_has_metal"
  - "Table truthfulness pinned by tests: every capability set agrees row-for-row with the approved gate doc; permanent '>= 2 capable AAs per type' solvability invariant + approved per-type counts (12/4/4/6/8/9/9)"
  - "Ligand typing from §5.1 atom records + bond block: bond-order aromaticity with 15-deg planarity fallback, fail-closed donors, O/N/S acceptors, charge groups (formal_charge-aware), halogen donors (C-F excluded), metal list [OQ-7]"
affects: [02-06 thresholds, 02-07 detector, 02-08 generator solvability, 02-09 extraction, 02-13 SMOKE-03 atom-name field verification, PLAY-05 hint]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Single typing home: generator/detector/hint all consume capability.py tables — DETECT-04 agreement by construction (gate §4.2)"
    - "Polarity-aware capability API: aa_capable(resn, itype, ligand_profile) encodes D3/D4 instead of a bare two-column table"
    - "Transcription discipline: source: comments per row group; any table change = DETECTOR_VERSION bump event (gate §4.7)"

key-files:
  created:
    - aamatch/capability.py
    - tests/test_capability.py
  modified:
    - tests/test_purity.py

key-decisions:
  - "h_bond capability made direction-refined like D3 (Rule 2, correctness): an AA donor needs a ligand acceptor and an AA acceptor needs a ligand donor — the coarse 'has either' rule could allocate a slot the detector can never solve (donor-only AA vs donor-only ligand)"
  - "Carboxylate typing guard (Rule 2, correctness): a carboxyl OH (neutral acid) is never an anion — fail-closed, consistent with donor typing; ester-without-charges false '-' remains the recorded cost of the plan's structure-only decision"
  - "side_chain naming convention pinned by the plan's examples: heavy side-chain atoms beyond CB + polar (heteroatom-attached) Hs; carbon-bonded Hs omitted (they participate in no typed role) — ALA/GLY carry empty side_chain sets"
  - "Met halogen-acceptor EXCLUDED: gate §3.5 resolved set + the plan's transcription rule ('halogen-acceptor role = the h_bond-acceptor set') override the §3.3 Met-row Y(S) cell — internal doc tension recorded in code + tests, not silently dropped"
  - "RING_PLANARITY_FALLBACK_DEG = 15.0 lives in capability.py (typing-support constant, row 8); 02-06's thresholds.py should import/reference it rather than duplicate"
  - "ring_count counts AROMATIC rings only (pi_stacking/cation_pi support is about aromatic rings, row 8)"
  - "ARG donors transcribed as NH1/NH2 exactly per the approved cell (the fragment's NE/HE exists but is not a table-listed donor; widening = versioned change)"

patterns-established:
  - "Ligand typing contract: plain atom records (§5.1 shape + optional formal_charge) + bond block [(i, j, order)] with 0-based indices"
  - "Explicit-stack DFS ring perception (5/6-member simple cycles, canonical min-atom form) — no itertools, per the recorded 02-01 convention"

# Metrics
duration: 29 min
completed: 2026-09-06
---

# Phase 2 Plan 05: Single Typing Home Summary

**capability.py: the one atom/residue typing table (20 AAs × 7 types + ligand typing) transcribed row-for-row from the approved DETECT-03 gate doc, polarity-aware per D3/D4, shared by generator/detector/hint so DETECT-04 holds by construction**

## Performance

- **Duration:** 29 min
- **Started:** 2026-09-06T10:04:06Z
- **Completed:** 2026-09-06T10:33:38Z
- **Tasks:** 3/3
- **Files modified:** 3 (2 created, 1 modified)

## Accomplishments
- AA capability table transcribed exactly from the approved gate document: per-type capable sets pinned EXACTLY by tests (donors 10, acceptors 9 w/ Met excluded, salt +/− sets, pi 4, cation-pi roles, hydrophobic 8, halogen = acceptor set, metal chelators 9 w/ Asp/Gln included), incl. the recorded exclusions (Met thioether acceptor, neutral-His-not-a-cation, Cys/Tyr out of the hydrophobic pedagogical set)
- aa_capable(resn, itype, ligand_profile): salt-bridge polarity (D3), cation-pi either direction (D4), metal gated on ligand has_metal (§5 item 5), h_bond direction-refined
- Ligand-side typing from synthetic §5.1 records + bond block, each rule unit-tested: aromaticity (bond orders primary — 6-ring perfect alternation, 5-ring 2 non-adjacent doubles, all-4 markers, unmarked=single; 15° dihedral fallback ONLY when cycle orders absent, radians→degrees converted), fail-closed donors, O/N/S acceptors, charge groups (formal_charge governs when present; structure-only when absent per the recorded decision), halogen donors Cl/Br/I (C-F excluded), metal list [OQ-7]
- residue_capabilities + ligand_support (§2.4) + ligand_has_metal; AA_TOKENS = the ONE generator-token → fragment/resn/charge_class vocabulary (20 tokens, no protonation variants in v1)
- PURE_MODULES = 9; purity gates (AST any-scope, clean-subprocess, py_compile) now cover capability; full suite 295/295 green under python3.6

## Task Commits

Each task was committed atomically (TDD RED → GREEN per task):

1. **Task 1: AA residue table + capability matrix + AA_TOKENS** — RED `1badcb5` (test) → GREEN `13d3876` (feat)
2. **Task 2: Ligand-side typing + support predicates** — RED `f3d8f43` (test) → GREEN `cbce5ab` (feat, incl. the aa_capable→ligand_support delegation refactor)
3. **Task 3: Register capability in PURE_MODULES + full suite** — `625793a` (test)

## Files Created/Modified
- `aamatch/capability.py` — the single typing home: AA_RESIDUES (20 AAs, source: comments per row group), resolved-set accessors, aa_capable (D3/D4), residue_capabilities, AA_TOKENS, ligand typing (712 lines)
- `tests/test_capability.py` — table truthfulness + polarity + typing + support tests (84 tests, 947 lines)
- `tests/test_purity.py` — PURE_MODULES += 'capability' (now 9)

## Decisions Made
- **h_bond direction-refined (Rule 2):** an AA donor needs a ligand acceptor (and vice versa). The plan specified polarity tests only for salt_bridge/cation_pi/metal; the coarse "AA has donor/acceptor AND ligand has donor/acceptor" rule would mark LYS (donor-only) capable against a donor-only ligand — a pairing the detector can never realize, i.e. a potential GEN-04 unsolvable level. Pinned by a test.
- **Acid-OH guard on carboxylate (Rule 2):** a C(=O)–OH (neutral acid) never types '-'; with formal_charge present the Os' charges govern, when absent the kekulé C=O/O-C structure alone charges per the plan's recorded decision. Residual accepted cost: an ester written without charge flags types '-' (structure-only rule; documented in `_charge_signs`).
- **Met halogen-acceptor excluded:** the §3.3 Met-row cell says Y(S) but the resolved §3.5 set (9 AAs) and this plan's explicit transcription rule both exclude Met; recorded in code comment + test so the doc tension is visible.
- **side_chain convention:** heavy side-chain atoms beyond CB + polar Hs (plan's SER/LYS/ARG examples pin it); carbon Hs and CB omitted — they anchor no typed role; ALA/GLY side_chain sets are empty; hydrophobic stays residue-name-based (§3.4).
- **Ring lists stored as valid cyclic walks** (row-9 geometry may take first/third/fifth-atom planes); HIS corrected from the RED draft to the true imidazole walk CG-ND1-CE1-NE2-CD2-CG.
- **15° planarity constant lives here** (row 8 typing-support value); flagged for 02-06 to reference rather than duplicate.
- **ARG donors = NH1/NH2 only** (approved cell transcribed literally; NE/HE noted as a non-table-listed side-chain atom).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] HIS ring walk order corrected in the RED test**
- **Found during:** Task 1 GREEN
- **Issue:** the RED draft asserted the HIS ring as ['CG','ND1','CD2','CE1','NE2'], which is not a valid cyclic walk of the imidazole connectivity (ND1–CD2 and CD2–CE1 bonds do not exist)
- **Fix:** corrected to the true walk ['CG','ND1','CE1','NE2','CD2'] (CG-ND1-CE1-NE2-CD2-CG); ring lists must be walkable for row-9 ring geometry
- **Files modified:** tests/test_capability.py
- **Verification:** tests green; walk validated against standard imidazole connectivity
- **Committed in:** 13d3876 (Task 1 GREEN)

**2. [Rule 2 - Missing Critical] h_bond capability direction-refinement**
- **Found during:** Task 1 GREEN (while implementing aa_capable)
- **Issue:** coarse h_bond capability ("AA has a donor or acceptor AND ligand has either") can mark a donor-only AA (LYS/ARG) capable against a donor-only ligand — no H-bond is realizable, so the generator could allocate a slot the detector never scores (solvability hole)
- **Fix:** refined per D3's polarity principle: AA donor requires ligand has_acceptor; AA acceptor requires ligand has_donor; pinned by test_hbond_donor_only_aa_vs_donor_only_ligand_fails_closed
- **Files modified:** aamatch/capability.py, tests/test_capability.py
- **Verification:** all rich-profile counts unchanged (12/4/4/6/8/9/9 — RICH carries both donor and acceptor); invariant test green
- **Committed in:** 13d3876 (Task 1 GREEN)

**3. [Rule 2 - Missing Critical] Carboxylic-acid (COOH) guard in charge typing**
- **Found during:** Task 2 GREEN (while implementing _charge_signs)
- **Issue:** the structure-only carboxylate rule (plan decision for formal_charge-absent files) also matches a neutral carboxylic ACID — typing acetic acid as an anion would fabricate a salt-bridge capability
- **Fix:** carboxylate requires no O bearing an H (fail-closed, consistent with donor typing); formal_charge keys still govern when present (explicit zeros correctly de-charge); acetate with/without charges and the acid case all unit-tested
- **Files modified:** aamatch/capability.py, tests/test_capability.py
- **Verification:** test_carboxylic_acid_oh_is_not_an_anion green
- **Committed in:** cbce5ab (Task 2 GREEN)

---

**Total deviations:** 3 auto-fixed (1 test bug, 2 missing-critical correctness guards)
**Impact on plan:** all three protect detection/solvability correctness; no scope creep — the approved table transcription is untouched.

## Issues Encountered
- Gate-doc internal tension found and recorded (not silently resolved): §3.3 Met row marks halogen-acceptor Y(S) while §3.5's resolved halogen set omits Met. The plan's explicit transcription rule + §3.5 were followed; flagged here so the DETECT-03 owner can reconcile the doc row at the next versioned review (§4.7 bump policy).

## Authentication Gates

None — pure WSL work only (no Windows/PyMOL probes needed, per the plan).

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- 02-06 (thresholds.py): transcribe the 10 threshold rows; import/reference `capability.RING_PLANARITY_FALLBACK_DEG` for row 8 rather than redefining it
- 02-07 (detector): consume AA_RESIDUES typed sets + ligand typing from THIS module only (DETECT-04 by construction); the h_bond refinement means donor-side pairs enumerate against ligand acceptors and vice versa
- 02-08 (generator): solvability consumes residue_capabilities + ligand_support + ligand_has_metal; the >= 2-capable-AAs invariant is already test-pinned
- 02-09 (extraction): atom records may carry `formal_charge` (SDF M CHG round-trip verified by the materialization probe) — capability uses it when present
- 02-13 (SMOKE-03): field-verifies AA atom names against the materialized chempy fragments — known reconciliation point: chempy digit-prefixes HIS ring H ('2HE' on hie per the materialization probe) vs the standard-PDB names transcribed here; reconcile in capability.py atom names (never thresholds), and note CB/carbon-Hs are deliberately absent from side_chain sets

---
*Phase: 02-headless-game-engine*
*Completed: 2026-09-06*
