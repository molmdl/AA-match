---
status: diagnosed
trigger: "saltbridge-hbond-interplay"
created: 2026-11-15T21:47:06+08:00
updated: 2026-11-15T21:58:27+08:00
mode: "symptoms_prefilled: true; goal: find_root_cause (classify A/B/C; no semantic fixes)"
---

## Current Focus

hypothesis: CONFIRMED verdict A -- independent channels work as designed; no detection/materialization defect.
test: Completed E1-E5 and unchanged WSL gates.
expecting: Satisfied: E1/E4/E5 positives emit both; E2/E5 negatives emit salt only; 969/969 pass.
next_action: Commit only this diagnosis doc and return ROOT CAUSE FOUND with Phase-9 help-text recommendation.

## Symptoms

expected: A residue pair that forms a salt bridge (ionic, charge-group centroid <= 5.5 A per the approved thresholds) AND simultaneously satisfies the H-bond geometric criterion (donor-H...acceptor <= 4.0 A, donor angle >= 140 deg) should yield BOTH a salt_bridge record AND an h_bond record -- so a level requiring both interaction types can complete both with one well-posed contact. At minimum: the actual joint logic must be understood and classified.
actual (HUMAN VERBATIM, 2026-11-15, quoted from the checkpoint response -- never paraphrase in the record): "suppose salt bridge residue also forming hbond, but detecting salt bridge still have hbind missing. check logic"
errors: none -- no crash, no console error; the game continued clean.
reproduction: Observed live in a GUI game (curated-demo class session, seed 210373887, standard game start). For diagnosis, reproducible headlessly: WSL pure-tier scripted geometry (detector-test authoring pattern) and/or the cmd-tier materialization + engine detect pipeline via the headless smoke recipe.
started: First report 2026-11-15 at the Phase-8.3 fresh-session GUI checkpoint. The detector is Phase-2 vintage; the task states the detector has been byte-untouched through Phase 8.3 (verifier-confirmed 2026-11-15). No prior report of this interplay.

## Hypotheses

| ID | Verdict candidate | Specific falsifiable claim | Status |
| --- | --- | --- | --- |
| H-A | A -- works as designed | The channels are independent; E1 emits both, negative controls suppress only the violated type, and real fragments expose the typed atoms needed in-game. | CONFIRMED by E1-E5 |
| H-B | B -- detector logic bug | Joint charged-pair geometry suppresses an h_bond or salt_bridge record even though both frozen criteria pass; E1 versus E3/E4 isolates the mechanism. | ELIMINATED by E1-E4 and E5 joint live records |
| H-C | C -- real-fragment feature bug | Pure geometry works, but materialized chempy AA/ligand charged groups omit or misattach typed donor-H/acceptor features, making real games systematically unable to emit the h_bond half. | ELIMINATED by E5 real typed features and joint live records |

## Eliminated

- hypothesis: H-B -- charge-group feature enumeration masks or deduplicates H-bond detection on a joint contact (verdict B).
  evidence: E1 emits BOTH canonical records with independent valid metrics for the same LYS NZ-carboxylate pair; E2 emits salt-only when D...A is 4.463462781 A (>4.0) and again when angle is 70.00000000000001 deg (<140) despite D...A=3.579455266 A; E3 emits neutral H-bond-only; E4 emits BOTH records in the reverse ASP acceptor / ligand-ammonium donor direction. No suppression mechanism survives these controls.
  timestamp: 2026-11-15T21:50:33+08:00

- hypothesis: H-C -- real chempy fragment / curated ligand materialization systematically removes usable charged-pair donor-H or acceptor features (verdict C).
  evidence: E5 actual LYS yields three NZ donor-H attachments (chempy names 1HZ/2HZ/3HZ at 1.009999992--1.027223088 A) and acetate yields carboxylate O acceptors. Real LYS-acetate positive pose emits BOTH records with score 1.0; a 4.299999841 A center-distance pose retains salt but emits no H-bond and scores 0.5. Real ASP plus benzamidinium repeats BOTH records (H-bond role AA acceptor, ligand donor) and the salt-only negative follows. The naming variant does not block geometric pairing.
  timestamp: 2026-11-15T21:56:01+08:00

## Evidence

- timestamp: 2026-11-15T21:47:06+08:00
  checked: Repository layout against task references.
  found: Detector implementation is `aamatch/detector.py` (there is no `aamatch/detection.py`); detector tests are `tests/test_detector.py` and `tests/test_detector_invariance.py` (there are no `tests/test_detector_part1.py` / `part2.py` files).
  implication: Use the actual detector/test homes; this is a reference mismatch, not yet a behavioral symptom.

- timestamp: 2026-11-15T21:48:19+08:00
  checked: Complete `aamatch/detector.py`, `aamatch/capability.py`, `aamatch/thresholds.py`, `aamatch/engine.py`, `aamatch/game_state.py`, and detector test precedents.
  found: H-bonds and salt bridges have separate independent emitters composed by `_part1_records` and `detect`: `_h_bond_records` consumes AA-heavy/ligand atom candidates and geometric donor-H attachment, whereas `_salt_bridge_records` directly enumerates opposite-sign feature centers. No cross-type deletion/dedup or scoring suppression exists; `score_preview` derives formation from record types. LYS NZ is simultaneously a table-listed donor and cation center; ligand carboxylate O atoms remain acceptors when they comprise a charge group; ASP OD1/OD2 are acceptors and ligand ammonium N-H remains a donor when charged.
  implication: Static code supports H-A but does not prove the runtime geometry. Candidate membership, best-H selection, both directions, and real materialization still require controls.

- timestamp: 2026-11-15T21:48:19+08:00
  checked: Existing detector laws for charged groups and directions.
  found: `tests/test_detector.py` separately proves neutral SER H-bond boundaries, LYS donor-H feature construction, ASP/ligand-ammonium salt bridges, and reverse-direction SER H-bonds; no existing test places salt-bridge and H-bond criteria on the SAME residue pair.
  implication: E1-E4 fill an actual missing joint-geometry regression surface without adding committed tests in this diagnose-only session.

- timestamp: 2026-11-15T21:49:30+08:00
  checked: First pure-probe invocation, `python3.6 -m py_compile tmp/probe_saltbridge_hbond_pure.py && python3.6 tmp/probe_saltbridge_hbond_pure.py`.
  found: Syntax compilation passed; execution stopped at test-helper loading with `ModuleNotFoundError: No module named 'aamatch'`. Direct script execution puts `tmp/`, not the repo root, on `sys.path`. No detector function ran and no geometry assertion ran.
  implication: Probe harness import-path issue only; add the repo root to `sys.path`, with no detector or geometry change.

- timestamp: 2026-11-15T21:50:33+08:00
  checked: `tmp/probe_saltbridge_hbond_pure.py` E1-E4 through production `detector.detect` and `game_state.score_preview`.
  found: All five positive/negative scenes passed exactly (E1 one run, E2 two variants, E3, E4). The decisive positive run reported both records and score 1.0; exact negative controls removed only H-bond; the reverse direction repeated the joint success.
  implication: Verdict B is eliminated. E5 must now rule out fragment/ligand materialization as the remaining systematic cause (C).

- timestamp: 2026-11-15T21:53:28+08:00
  checked: E5 first headless run (`python3.6 -m py_compile tmp/probe_saltbridge_hbond_real.py`, then Windows PyMOL `-cq tmp\\probe_saltbridge_hbond_real.py`).
  found: Real chempy LYS donors WERE extracted: `('NZ','1HZ',1.027223087603096)`, `('NZ','2HZ',1.0252752174805628)`, `('NZ','3HZ',1.00999999244107)` -- all inside AA_H_ATTACH_MAX=1.5. Real acetate carboxylate ids [1,2] were typed as acceptors and one anionic group, and LYS unclassified count was zero. The script then failed its own spelling-specific expectation `HZ1/HZ2/HZ3` and raised IndexError selecting HZ1 before any joint pose.
  implication: A new materialized-name variant exists, but it does NOT remove donor features because AA donor-H pairing is geometric over all same-object hydrogens. Correct only the tmp probe to select actual attached records (by ids), then run the unchanged positive/negative pose logic. No production semantic change is warranted by this name observation.

- timestamp: 2026-11-15T21:54:21+08:00
  checked: E5 second headless run after spelling-independent real donor selection.
  found: REAL JOINT POSITIVE PASSED through production materialization/extraction/engine.detect: LYS `_aam_aa01` NZ id 8 + H id 19 donated to acetate O id 1, h_bond d_da=3.0000003345875945 angle=179.99999402358446, PLUS salt_bridge on NZ/acetate O group d_center=1.8559980545566355; score=1.0 and formed both. The subsequent probe move did NOT create the intended salt-only negative because another acetate O (id 2) became a valid acceptor at d_da=2.011995733351605 angle=179.99999260610335; the detector correctly kept both records. E5B then failed probe-side with `TypeError: tuple indices must be integers or slices, not str` before posing because ligand donor features are index/record pairs.
  implication: The actual real-materialization joint result rules out systematic charged-pair H-bond blindness on AA donors and ligand carboxylates. Redesign the attempted negative on an equidistant two-O axis; fix only the tmp probe's ligand tuple unpack. The misposed negative is not evidence against the detector.

- timestamp: 2026-11-15T21:55:15+08:00
  checked: E5 third headless run.
  found: Real LYS/acceptor typing checks passed again; setup raised `ValueError: zero vector` constructing the negative's axis because `O2-O1` and `O1-center` are collinear, so their cross product cannot define a normal. No new detect run occurred.
  implication: Pure probe-vector construction error, not detector behavior. Use an independent reference axis; the geometry goal remains to make both O distances grow from a 3.0 A charge-center baseline to >4.0 at 4.3 A center distance.

- timestamp: 2026-11-15T21:56:01+08:00
  checked: E5 fourth/final headless real-materialization run, with actual LYS+acetate and ASP+benzamidinium scenes through placement.materialize -> geometry.extract_game_atoms -> engine.remap_ligand_bonds -> engine.detect -> game_state.score_preview.
  found: `=== E5 REAL PASS ===`. E5A real joint h_bond d_da=3.210723056457649 angle=179.99994269531328 PLUS salt_bridge d_center=2.999999883161587, score 1.0. E5A real salt-only salt d_center=4.299999841412402, no h_bond, score 0.5. E5B real reverse joint h_bond d_da=2.999999692610857 angle=179.9999802706229 PLUS salt_bridge d_center=3.2719672737857346, score 1.0. E5B real salt-only d_center=4.518523832020857, no h_bond, score 0.5. All feature, role, best-H, score, cleanup checks passed.
  implication: H-C is eliminated. Actual game-class fragments and curated charged ligands are not H-bond blind. Verdict A is confirmed at both pure and real materialization tiers; no detector fix proposal is needed.

## Experiment Log

### E1 -- joint-detection positive control

Command (after the harness-only import-path correction): `python3.6 -m py_compile tmp/probe_saltbridge_hbond_pure.py && python3.6 tmp/probe_saltbridge_hbond_pure.py`.

Geometry and feature receipts (literal output):

```text
E1_JOINT_AA_DONOR GEOMETRY {"angle_deg": 160.00000000000003, "donor_acceptor": 3.5794552658190883, "donor_h_attach": 1.0, "salt_center_distances": [4.562071897723665]}
E1_JOINT_AA_DONOR FEATURES donor_pairs=[('NZ', 'HZ1'), ('NZ', 'HZ2'), ('NZ', 'HZ3')] acceptors=[] aa_charge={'sign': '+', 'center': (0.0, 0.0, 0.0), 'atom_ids': [710]} lig_charge=[('carboxylate', '-', (4.5, 0.75, 0.0))]
E1_JOINT_AA_DONOR SCORE score=1.0 formed=['h_bond', 'salt_bridge']
E1_JOINT_AA_DONOR PASS types=['h_bond', 'salt_bridge']
E1 DECISIVE both records use the same aa_lys/ligand contact; score=1.0
```

Canonical record metrics/roles from the same run:

```text
h_bond: aa LYS donor [NZ=710, HZ1=711] -> lig acceptor [O3=2]; d_da=3.5794552658190883; angle_deg=160.00000000000003
salt_bridge: aa cation [NZ=710] <-> lig anion [O2=1,O3=2]; d_center=4.562071897723665
```

Verdict: PASS. Both criteria are independently satisfied and both records are emitted through full 7-type `detector.detect`; list-mode scoring completes both required items with score 1.0. Note the scripted charge-center distance is sqrt(4.5^2+0.75^2)=4.56207 because `_carboxylate_ligand`'s O midpoint has y=0.75; the assertion uses the actual frozen center criterion rather than the approximate setup comment.

### E2 -- salt-only independence control

Literal output:

```text
E2_DISTANCE_CONTROL min_NZ_to_O=4.463462781 (> 4.0)
E2_DISTANCE_SALT_ONLY GEOMETRY {"angle_deg": 160.00000000000003, "donor_acceptor": 4.463462781294362, "donor_h_attach": 0.9999999999999999, "salt_center_distances": [5.451834553615875]}
E2_DISTANCE_SALT_ONLY SCORE score=0.5 formed=['salt_bridge']
E2_DISTANCE_SALT_ONLY PASS types=['salt_bridge']

E2_ANGLE_SALT_ONLY GEOMETRY {"angle_deg": 70.00000000000001, "donor_acceptor": 3.5794552658190883, "donor_h_attach": 1.0, "salt_center_distances": [4.562071897723665]}
E2_ANGLE_SALT_ONLY SCORE score=0.5 formed=['salt_bridge']
E2_ANGLE_SALT_ONLY PASS types=['salt_bridge']
```

Verdict: PASS (two independent negatives). A salt-valid contact does NOT imply H-bond: with all heavy acceptors beyond 4.0 A, or with distance inside but angle at H only 70 deg, only the salt record survives and the two-item score is correctly 0.5. This is the mechanism most directly explaining the human's missing-H-bond report.

### E3 -- neutral H-bond masking control

Literal output:

```text
E3_NEUTRAL_HBOND_ONLY GEOMETRY {"angle_deg": 160.0, "donor_acceptor": 3.5794552658190883, "donor_h_attach": 1.0, "salt_center_distances": []}
E3_NEUTRAL_HBOND_ONLY FEATURES donor_pairs=[('OG', 'HG')] acceptors=['OG'] aa_charge={'sign': None, 'center': None, 'atom_ids': []} lig_charge=[]
E3_NEUTRAL_HBOND_ONLY SCORE score=0.5 formed=['h_bond']
E3_NEUTRAL_HBOND_ONLY PASS types=['h_bond']
```

Verdict: PASS. Neutral SER-carbonyl H-bond geometry at the same distance/angle class as E1 emits the H-bond record with no charge group and no salt record. E1 charged geometry also emitted it, so charge typing is not masking the channel.

### E4 -- reverse-direction control

Literal output:

```text
E4_JOINT_LIGAND_DONOR GEOMETRY {"angle_deg": 160.0, "donor_acceptor": 2.1360009363293826, "donor_h_attach": 1.0, "salt_center_distances": [3.0]}
E4_JOINT_LIGAND_DONOR FEATURES donor_pairs=[] acceptors=['OD1', 'OD2'] aa_charge={'sign': '-', 'center': (1.5, 0.25, 0.0), 'atom_ids': [308, 309]} lig_charge=[('ammonium', '+', (4.5, 0.25, 0.0))]
E4_JOINT_LIGAND_DONOR SCORE score=1.0 formed=['h_bond', 'salt_bridge']
E4_JOINT_LIGAND_DONOR PASS types=['h_bond', 'salt_bridge']

=== PURE E1-E4 PASS: independent joint channels in both directions ===
```

Canonical record metrics/roles: h_bond has AA ASP role `acceptor` [OD1=308], ligand role `donor` [N1=0,H3=2], d_da=2.1360009363293826 and angle 160; salt_bridge has AA anion [OD1=308,OD2=309], ligand cation [N1=0], d_center=3.0. Verdict: PASS in both directions; `score_preview` completes both required items.

### E5 -- real-fragment materialization control

Command: `python3.6 -m py_compile tmp/probe_saltbridge_hbond_real.py && timeout 180 cmd.exe /c "C:\\src\\run-conda-pymol.bat -cq tmp\\probe_saltbridge_hbond_real.py"`. The final run used actual `placement.materialize` objects and the production `engine.detect()` path. Earlier harness-only failures are retained in Evidence above; they did not change production code or the final geometry criteria.

Feature receipts (literal final output):

```text
E5A REAL_LYS_DONORS [('NZ', '1HZ', 1.027223087603096), ('NZ', '2HZ', 1.0252752174805628), ('NZ', '3HZ', 1.00999999244107)]
E5 E5A real LYS has 3 geometrically attached NH hydrogens PASS
E5 E5A real LYS unclassified atoms zero         PASS
E5 E5A real acetate carboxylate typed           PASS
E5 E5A acetate charge O atoms are acceptors     PASS group_ids=[1, 2] acceptor_ids=[1, 2]
E5B REAL_BENZAMIDINIUM_DONORS [('N', 'H', 1.0148201627526767), ('N', 'H', 1.0110927173962203)]
E5 E5B cation-group N-H donors available        PASS
E5 E5B real ASP acceptors and charge available  PASS
E5 E5B real ASP unclassified atoms zero         PASS
```

E5A real AA-donor positive and negative receipts:

```text
E5A_REAL_JOINT SCORE 1.000000 formed=['h_bond', 'salt_bridge']
E5 E5A_REAL_JOINT selected AA-donor H-bond      PASS h_bonds=1
E5 E5A_REAL_JOINT selected H best-angle         PASS aa_ids=[8, 19]
E5 E5A real joint emits salt too                PASS
E5 E5A real joint completes both                PASS
E5A_REAL_SALT_ONLY SCORE 0.500000 formed=['salt_bridge']
E5 E5A 4.3 A negative removes H-bond            PASS
E5 E5A 4.3 A negative retains salt              PASS salt_metrics=[{'d_center': 4.299999841412402}]
E5 E5A salt-only score is half                  PASS
```

E5A positive canonical metrics: h_bond LYS NZ atom 8 + H atom 19 (donor) -> acetate O atom 1 (acceptor), d_da=3.210723056457649 A, angle_deg=179.99994269531328; salt_bridge NZ [8] <-> acetate O group [1,2], d_center=2.999999883161587 A.

E5B real ligand-donor positive and negative receipts:

```text
E5B_REAL_JOINT SCORE 1.000000 formed=['h_bond', 'salt_bridge']
E5 E5B_REAL_JOINT selected ligand-donor H-bond  PASS
E5 E5B real reverse joint emits salt too        PASS
E5 E5B real reverse joint completes both        PASS
E5B_REAL_SALT_ONLY SCORE 0.500000 formed=['salt_bridge']
E5 E5B 4.3 A negative removes H-bond            PASS
E5 E5B 4.3 A negative retains salt              PASS salt_metrics=[{'d_center': 4.518523832020857}]
E5 E5B salt-only score is half                  PASS
=== E5 REAL PASS ===
```

E5B positive canonical metrics: h_bond benzamidinium N/H atom ids [1,15] (donor) -> ASP OD1 atom 6 (acceptor), d_da=2.999999692610857 A, angle_deg=179.9999802706229; salt_bridge ASP OD1/OD2 [6,7] <-> cation N [1], d_center=3.2719672737857346 A.

Verdict: PASS. Real charged-pair H-bonding works in both directions with unmodified chempy/curated coordinates, and moving outside the independent H-bond distance criterion removes exactly that half while leaving the salt bridge and half score. Actual LYS uses digit-prefixed H names `1HZ`/`2HZ`/`3HZ`; this is not a bug because donor-H attachment is geometric and all three are usable.

- timestamp: 2026-11-15T21:58:27+08:00
  checked: Final WSL gates and tree audit after all diagnosis (no production semantic edits).
  found: `python3.6 -m py_compile aamatch/*.py` exited 0 with no output. `python3.6 -m unittest discover -s tests` printed `Ran 969 tests in 27.856s` and `OK`; detector perf guard 0.310 s under 2.0 s. `git diff -- aamatch` was empty and `git status --short` listed only this new requested debug doc.
  implication: Verdict A verified without regression or semantic drift. Ready to commit the diagnosis alone.

## Final Gate Receipt

```text
$ python3.6 -m py_compile aamatch/*.py
(no output; success)

$ python3.6 -m unittest discover -s tests
----------------------------------------------------------------------
Ran 969 tests in 27.856s

OK
[02-11 perf guard] worst-case detect(): 0.310 s (1253 atoms, 81 records, guard 2.0 s)

$ git diff -- aamatch && git status --short
?? .planning/debug/saltbridge-hbond-interplay.md
```

## Resolution

verdict: A -- WORKS AS DESIGNED. Joint H-bond and salt-bridge detection is independent and functional in both directions at pure tier and with real materialized fragments/curated charged ligands.
root_cause: The observed salt-only/MISSING-H-bond outcome is explained by independent criteria, not channel suppression. Salt bridge tests opposite charge-GROUP centers <=5.5 A. H-bond separately requires a typed explicit donor-H pair, donor-heavy...acceptor-heavy <=4.0 A, and the D-H...A angle AT H >=140 deg. Meeting salt geometry does not imply either H-bond condition. E2 and both E5 negative scenes reproduce exactly salt_bridge=formed + h_bond=MISSING + two-item score 0.5 under those independent conditions; E1/E4/E5 positives prove that when both sets of conditions hold, both records emit and both items complete. The precise original GUI pose's H metrics are unavailable (no coordinates/checkpoint atoms were captured), so this verdict classifies the actual detector behavior rather than claiming a reconstructed numeric measurement for that historical pose; there is no evidence that both H-bond criteria were satisfied there.
fix_proposal: None -- no B/C defect exists and no detector semantics changed. DETECTOR_VERSION impact: NO. No new test files are committed; E1-E5 receipts remain proposals in this doc plus git-ignored tmp probes. Existing 02-01 law and detector thresholds stay frozen.
phase_9_help_recommendation: Add explicit help/tutorial text: "Salt bridge and H-bond are scored independently. For both on one contact, put an actual polar donor-H and acceptor heavy atom within 4.0 A and align D-H...A at H to at least 140 deg; a 5.5 A charge-group-center salt contact alone is not enough. Rotate the AA to aim a specific polar H, and where relevant choose a pair with a donor/acceptor role in the required direction." Optionally surface near-miss reason metrics in a later non-semantic UI/help plan, but do not imply H-bond from salt-bridge proximity. Real chempy LYS H names 1HZ/2HZ/3HZ need no player action or detector change.
verification: E1-E4 pure controls PASS; E5 actual LYS-acetate and ASP-benzamidinium positive/negative controls PASS; WSL syntax gate PASS and existing unit suite 969/969 PASS (27.856 s); production diff empty.
files_changed:
  - .planning/debug/saltbridge-hbond-interplay.md (debug documentation only)
probe_files:
  - tmp/probe_saltbridge_hbond_pure.py (git-ignored; E1-E4 PASS)
  - tmp/probe_saltbridge_hbond_real.py (git-ignored; E5 PASS)
