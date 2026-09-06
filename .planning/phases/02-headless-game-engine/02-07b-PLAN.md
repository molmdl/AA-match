---
phase: 02-headless-game-engine
plan: 07b
type: tdd
wave: 7
depends_on: ["02-07"]
files_modified:
  - aamatch/detector.py
  - tests/test_detector.py
autonomous: true

must_haves:
  truths:
    - "halogen detects only (AA O/N/S acceptor) x (ligand C-X donor, X in Cl/Br/I) within both angle windows; C-F excluded at typing; AA-side halogen donors structurally impossible"
    - "metal detects only when the ligand carries an approved metal (gated via capability.ligand_has_metal), distance-only, chelator = side-chain N/O/S"
    - "detect() exposes the complete 7-type canonical result list ordered by INTERACTION_TYPES position; unknown/extra types impossible (closed set)"
  artifacts:
    - path: "aamatch/detector.py"
      provides: "Full 7-type detection pipeline with canonical results"
      min_lines: 1000
  key_links:
    - from: "aamatch/detector.py"
      to: "aamatch/thresholds.py"
      via: "HALOGEN_* / METAL_* constants imported, never inlined"
      pattern: "from .thresholds import"
    - from: "tests/test_detector.py"
      to: "setup_state.INTERACTION_TYPES"
      via: "all 7 types produce records; canonical order matches the enum"
      pattern: "INTERACTION_TYPES"
---

<objective>
Detector part 2b: halogen bond + metal coordination + the canonical 7-type detect() completion. (Plan split 2026-09-06 from the original 02-07 after repeated silent spawn failures — this half depends on 02-07's ring types being merged first.)

Purpose: DETECT-01 + DETECT-02 complete; the record contract consumed by scoring (02-10) and the E2E smoke (02-14) becomes final.
Output: detector.py covering all 7 types, boundary-tested.
</objective>

<execution_context>
@~/.config/opencode/get-shit-done/workflows/execute-plan.md
@~/.config/opencode/get-shit-done/templates/summary.md
@~/.config/opencode/get-shit-done/references/tdd.md
</execution_context>

<context>
@docs/DETECTION_THRESHOLDS.md                                        # rows 6, 7 — the frozen criteria
@.planning/phases/02-headless-game-engine/02-RESEARCH-detection.md   # §2.6/2.7 mechanics, §4 partner sides, §7.6 metal gating
@aamatch/detector.py                                                 # 02-06 pipeline + 02-07 ring types (extend, do not restructure)
@aamatch/capability.py, @aamatch/thresholds.py, @aamatch/vec3.py
</context>

<tasks>

<task type="auto" tdd="true">
  <name>Task 1: halogen + metal (RED -> GREEN)</name>
  <files>aamatch/detector.py, tests/test_detector.py</files>
  <action>
RED:
- halogen: ligand C-Cl donor; AA SER OG acceptor. (a) A···Cl 3.5 A, donor angle ∠(A···Cl-C) = 165 deg, acceptor angle ∠(Y-A···X) at the acceptor A = 120 deg -> FORMED; (b) donor angle 100 deg (outside 135-195) -> NOT; (c) acceptor angle 60 deg (outside 90-150) -> NOT; (d) ligand C-F donor -> NO candidates AT ALL (C-F excluded at typing; assert no record even at perfect geometry); (e) AA-side "donor" attempt (ligand O accepting from an AA C-Cl) -> impossible: enumeration is (AA-acceptor x ligand-donor) only — assert an AA halogen produces nothing (spec's side rule, detection research §4).
- metal: ligand carries ZN (element in approved list) + AA HIS ring N at 2.5 A -> FORMED (distance-only; aa role 'chelator'); same geometry with NO metal in ligand -> NO record and _metal not even enumerated (gating via capability.ligand_has_metal — detection research §7.6); 3.2 A -> NOT; metal element not in METAL_ELEMENTS (e.g. 'NA') -> no record.

GREEN: implement _halogen (two angle windows from thresholds; enumerate ONLY (AA acceptor O/N/S) x (ligand donor C-X, X in {CL,BR,I})) and _metal (distance-only; gated by ligand_has_metal; AA donors = side-chain N/O/S of chelator residues). Keep MIN_DIST 0.5 guard + covalent exclusion (ligand bond block; AA side relies on cross-side enumeration).

Commit: `feat(02-07b): halogen + metal (TDD)`.
  </action>
  <verify>python3.6 -m unittest tests.test_detector -v</verify>
  <done>Halogen windows + metal gating boundary-exact; side rules structurally enforced</done>
</task>

<task type="auto" tdd="true">
  <name>Task 2: canonical 7-type completion + full suite</name>
  <files>aamatch/detector.py, tests/test_detector.py</files>
  <action>
RED: a scene triggering h_bond + pi_stacking + hydrophobic returns records ordered by (type-position in INTERACTION_TYPES, aa object, aa atom_ids, lig atom_ids); unknown/extra types impossible (closed set); total record count asserted.

GREEN: wire all 7 type tests into detect(atom_records, ligand_bonds) -> canonical list.

Commit: `feat(02-07b): canonical 7-type surface (TDD)`.

Then run the full suite — confirm no regression in tests/test_capability, tests/test_spatial, tests/test_thresholds, and the 02-06/02-07 detector tests.
  </action>
  <verify>python3.6 -m unittest discover -s tests -v</verify>
  <done>All 7 types boundary-tested; canonical deterministic output; full WSL suite green</done>
</task>

</tasks>

<verification>
python3.6 -m py_compile aamatch/*.py && python3.6 -m unittest discover -s tests -v
</verification>

<success_criteria>
DETECT-01 + DETECT-02 complete in the pure layer: 7 types, explicit partner sides, D1 restriction, canonical records — all WSL-green.
</success_criteria>

<output>
After completion, create `.planning/phases/02-headless-game-engine/02-07b-SUMMARY.md`
</output>
