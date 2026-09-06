# Detection Thresholds & AA Capability — DETECT-03 [GATE] Document

**Status:** APPROVED — 2026-09-06 (human gate, phase-2 plan 02-01 checkpoint). Units and
atom typing verified at approval time; provisional pending Phase-8 dataset revisit —
see §6 Approval record.

**Purpose:** This is the DETECT-03 gate document — the single source of truth that every
downstream Phase-2 plan transcribes into code. The project's truthfulness rule forbids
inventing chemistry: every published value below was verified from the official
PLIP/ProLIF/BINANA repositories on **2026-09-06** (see
`.planning/phases/02-headless-game-engine/02-RESEARCH-detection.md` and
`02-RESEARCH-generation.md`, fetched from raw.githubusercontent.com and the PLIP help page
on that date). This gate approves our **adoption** of those values, records the in-house
resolutions where the sources disagree, and freezes the policy decisions (D1, OQ-1, …)
that bind the detector, generator, and scoring plans.

**Downstream consumers (bind by transcription):**

- `aamatch/thresholds.py` (plan 02-06) — the 10 threshold rows become named constants,
  transcribed row-by-row from §2 of this document, each with a source comment.
- `aamatch/capability.py` (plan 02-05) — the AA capability table (§3) and ligand support
  predicates become the ONLY atom/residue typing module (see Policy Decision 4.2).
- Generator required-set semantics (plan 02-08) and score `any` semantics (plan 02-10)
  consume Policy Decision 4.3 (OQ-1 mode semantics).

**Approval protocol:** each threshold row below carries an `Approval:` line. The human
approved (with a units + atom-typing verification condition) at the 02-01 checkpoint on
2026-09-06; the real date + approver are recorded per row and in the final Approval
record section (§6). **No detector code freezes before the approval record exists — it
does now (§6), so detector code (plans 02-05..02-08) freezes against this table.**

---

## 1. Verified sources (all fetched/verified 2026-09-06)

### 1.1 Repos, versions, and fetched files

| Source | Version | Files fetched (official repo, raw.githubusercontent.com) |
|---|---|---|
| PLIP | 3.0.1 (master, `pharmai/plip`) | `plip/basic/config.py` (thresholds + METAL_IONS), `plip/structure/detection.py` (all geometric tests) |
| ProLIF | 2.2.x (master, `chemosim-lab/ProLIF`) | `prolif/interactions/interactions.py` (all class defaults), `CITATION.cff` (DOI) |
| BINANA | 2.1 (main, `durrantlab/binana`) | `INTERACTIONS.md` (algorithm + full parameter table), `python/binana/interactions/default_params.py` (values cross-check), `python/binana/interactions/_hydrogen_halogen_bonds.py` (angle semantics), `README.md` (DOI) |

Additional generation-side typing sources (same date): PLIP official help page
(https://plip-tool.biotec.tu-dresden.de/plip-web/plip/help) — charged-group attribution,
halogen donor/acceptor rules, metal-complex protein-side group list, hydrophobic atom
rule; ProLIF docs (tutorial output showing a backbone HBAcceptor hit on VAL — evidence
for D1). Repo trees verified via the GitHub contents API.

### 1.2 DOIs (each verified from the project's own repository file)

| Tool | Citation | Verified in |
|---|---|---|
| PLIP | Schake, Bolz et al., "PLIP 2025 …", Nucl. Acids Res., doi:10.1093/nar/gkaf361 | PLIP's own `config.py` `__citation_information__` + repo description (2026-09-06) |
| ProLIF | Bouysset & Fiorucci, J Cheminform 13:72 (2021), doi:10.1186/s13321-021-00548-6 | ProLIF's own `CITATION.cff` (2026-09-06) |
| BINANA | Durrant JD, McCammon JA, J Mol Graph Model 29(6):888-893 (2011), doi:10.1016/j.jmgm.2011.01.004 | BINANA's own `README.md` (2026-09-06) |

One in-house classification citation (capability table §3, hydrophobic row):
Kyte & Doolittle 1982, "A simple method for displaying the hydropathic character of a
protein", *J Mol Biol* 157(1):105-132, doi:10.1016/0022-2836(82)90515-0, PMID 7108955
(canonical side-chain hydropathy scale; citation verified via the reference list of the
Wikipedia *Hydrophobicity scales* article, fetched 2026-09-06).

### 1.3 Angle convention (settled — was the ambiguous item)

All three tools measure the **same** H-bond angle — at the hydrogen, between the donor
and acceptor directions (∠D-H···A). Verified from code: PLIP `detection.py`
(`vecangle(vector(h→d), vector(h→acc)) > HBOND_DON_ANGLE_MIN` → > 100°); BINANA
`_hydrogen_halogen_bonds.py` (deviation-from-linear ≤ 40° ⇔ ≥ 140° — the
`INTERACTIONS.md` prose "no greater than 40 degrees" is loose wording for *deviation from
linear*; the source is unambiguous); ProLIF `interactions.py` (`DHA_angle = (130, 180)` — degrees — the
`[Acceptor]...[Hydrogen]-[Donor]` angle). The three H-bond criteria therefore differ
**only in numbers** (distance 4.1 / 4.0 / 3.5 Å; angle > 100° / ≥ 140° / ≥ 130°).

---

## 2. Approved threshold table (10 rows)

### 2.1 Selection principles (the human may veto these, not just the numbers)

- **P1 — One source per row where possible** (cleanest provenance); interpolate only with recorded rationale.
- **P2 — Game-tuned, not analysis-tuned:** PLIP's permissiveness exists because it analyzes low-resolution crystal structures; a hand-placement game needs *decisive* geometry (a student must be able to tell success from failure), but slightly generous distances (no guides on screen). Strict angles, moderate distances.
- **P3 — Majority rule when two of three agree.**
- **P4 — Fewest geometric tests per type** that preserve chemical meaning (implementation + test surface).

### 2.2 The rows

Values marked [V] were verified from the cited primary source on 2026-09-06 (file-level
citations in the research files). Each row carries an `Approval:` line recorded at the
2026-09-06 human checkpoint.

#### Row 1 — Hydrogen bond

- **Adopted criterion:** D···A ≤ **4.0 Å** AND ∠D-H···A ≥ **140°** (both measured
  heavy-donor to heavy-acceptor / at H; angle convention §1.3). **Needs explicit polar H
  on both sides** (see §5, fail-closed donor typing).
- **Source of the value:** BINANA pair (4.0 Å, ≥ 140°) [V].
- **Rationale / rejected alternatives:** One-source pair, internally consistent; generous
   distance (kind to hand placement), decisive direction. Rejected: PLIP 4.1 Å/100° (too
   permissive — sloppy placements would count; the 100° floor admits near-perpendicular
   donors), ProLIF 3.5 Å/130° (distance tight for unguided play).
- Approval: date: 2026-09-06 approver: human gate, phase-2 plan 02-01 checkpoint

#### Row 2 — Salt bridge (ionic folded in)

- **Adopted criterion:** opposite charge-**group centers** ≤ **5.5 Å**.
- **Source of the value:** PLIP = BINANA = 5.5 Å [V].
- **Rationale / rejected alternatives:** Unanimous distance; group-center form (both PLIP
  & BINANA) is more chemically faithful than ProLIF's atom-atom 4.5 Å and matches the
  charge-group table we need anyway. Charge-group definitions: BINANA's verified table
  (see §2.3) as the in-house standard.
- Approval: date: 2026-09-06 approver: human gate, phase-2 plan 02-01 checkpoint

#### Row 3 — π-stacking (parallel + T-shaped as ONE category)

- **Adopted criterion:** ring-center dist < **5.5 Å** AND (normals within **30°** of
  parallel OR within **30°** of perpendicular) AND projected-center offset < **2.0 Å** —
  single test covers both sub-geometries; reported type is always `pi_stacking`
  (sub-type P/T recorded as a metric only).
- **Source of the value:** PLIP set (5.5 Å / 30° / 2.0 Å) [V].
- **Rationale / rejected alternatives:** One uniform test for both orientations (fewest
   rules — P4); published as one table. Rejected: BINANA 7.5 Å (catches distant stacks —
  makes the type easy; also needs two different lateral tests), ProLIF FaceToFace +
  EdgeToFace (two parameter sets + intersect computation). Both T-shaped and parallel
  count as the same category per spec (EXT-02 defers the split).
- Approval: date: 2026-09-06 approver: human gate, phase-2 plan 02-01 checkpoint

#### Row 4 — Cation-π

- **Adopted criterion:** charge center ↔ ring center ≤ **6.0 Å** AND projected charge
  offset < **2.0 Å**; direction recorded (AA-cation→lig-ring vs lig-cation→AA-ring).
- **Source of the value:** distance: PLIP + BINANA 6.0 Å (majority — P3); offset: PLIP 2.0 Å
  (same helper as row 3) [V].
- **Rationale / rejected alternatives:** The 2.0 Å offset ≈ BINANA's padded benzene disk
  (1.4 Å + 0.75 Å) — near-equivalent, cheaper to implement. Rejected: ProLIF 4.5 Å (too strict
  for a game) and its axis-angle test (harder to reason about for students). PLIP's
  ligand-tertiary-amine anti-artifact rule (amine-plane normal vs ring normal ≤ 30° to
  count) **adopted only when the small molecule carries the cation** — mirrors PLIP's
  ligand-side-only rule; documented asymmetry, recorded as Policy Decision 4.4 (OQ-4).
- Approval: date: 2026-09-06 approver: human gate, phase-2 plan 02-01 checkpoint

#### Row 5 — Hydrophobic contact

- **Adopted criterion:** ≥ 1 pair of qualifying carbons with d ≤ **4.0 Å**; qualifying
  carbon = element C with all bonded neighbors ∈ {C, H}. **Binary presence semantics**
  ("≥ 1 qualifying contact between this AA and the ligand").
- **Source of the value:** distance: PLIP + BINANA 4.0 Å (majority — P3); typing: PLIP's
  graph rule [V].
- **Rationale / rejected alternatives:** Graph rule is computable from the SDF/MOL2 bond
  block without atom-type tables (ProLIF's SMARTS excludes C-N/O/F — same spirit,
  majority-verified). Binary presence deliberately sidesteps PLIP's documented count
  explosion and dedup machinery — counts are irrelevant to fraction scoring. Gameplay
  flag: hydrophobic is easy to satisfy → Policy Decision 4.5 (OQ-5).
- Approval: date: 2026-09-06 approver: human gate, phase-2 plan 02-01 checkpoint

#### Row 6 — Halogen bond (donors ligand-side only)

- **Adopted criterion:** acceptor atom ··· halogen ≤ **4.0 Å** AND ∠(A···X-D) ∈
  **135°–195°** (165° ± 30°) AND ∠(Y-A···X) ∈ **90°–150°** (120° ± 30°); donors
  **ligand-side only**, X ∈ **{Cl, Br, I}** — **C-F donors EXCLUDED**; acceptors AA-side
  O/N/S.
- **Source of the value:** PLIP full set (4.0 Å / 165° ± 30° / 120° ± 30°) [V]; C-F exclusion
  is an in-house resolution — ProLIF precedent (`[#6,#7,Si,F,Cl,Br,I]-[Cl,Br,I,At]`
  excludes C-F) [V].
- **Rationale / rejected alternatives:** One source (P1) for the geometry; two-angle form
  encodes σ-hole chemistry; 4.0 Å is the kindest verified distance (BINANA's 5.5 Å is
  loose enough to fire on casual proximity; ProLIF's 3.5 Å frustrates). Donor-side restriction is
  the spec's own rule (both PLIP and BINANA treat proteins as halogen-free in practice —
  the spec makes it explicit). **[RESOLVE] C-F donor disagreement:** PLIP includes
  C-X with X = F; ProLIF's verified donor pattern excludes C-F. **Adopted: EXCLUDE C-F**
  — halogen bonding to F is weak/disputed and ProLIF's Auffinger-based pattern is the
  stricter precedent. (Research draft row 6 listed X ∈ {F, Cl, Br, I}; this resolution
  supersedes it and is recorded here for the human's review.)
- Approval: date: 2026-09-06 approver: human gate, phase-2 plan 02-01 checkpoint

#### Row 7 — Metal coordination (only when the ligand carries a metal)

- **Adopted criterion:** metal ··· coordinating atom ≤ **3.0 Å**, **distance-only** (no
  geometry fitting); metals gated to ligand-side presence; donors AA-side N/O/S.
- **Source of the value:** distance: PLIP 3.0 Å (between ProLIF 2.8 Å and BINANA 3.5 Å);
  no-angles: BINANA's published rationale [V].
- **Rationale / rejected alternatives:** BINANA explicitly documents why angle/geometry
  checks are omitted (many geometries, wide real-world L-M-L deviation, vacant sites) —
  direct precedent; PLIP's fitting machinery is analysis output we don't need. Adopted
  metal element list (v1): **{MG, ZN, FE, CA, MN, CU, NI, CO, CD}** [OQ-7] — the
  biologically common intersection/union core of the three verified lists (all members
  verified in the research §2.7); full union available at the gate if the human wants
  broader coverage.
- Approval: date: 2026-09-06 approver: human gate, phase-2 plan 02-01 checkpoint

#### Row 8 — Aromatic ring identification (support rule for rows 3–4)

- **Adopted criterion:** primary: **bond-order-derived aromaticity** from the SDF/MOL2
  bond block; fallback for missing bond orders: 5/6-member ring with adjacent-dihedral
  deviation ≤ **15°**.
- **Source of the value:** fallback value: BINANA 15° [V]; SDF-first: project decision
  (PITFALLS 12; spec GEN-02).
- **Rationale / rejected alternatives:** Bond orders are the reason the spec pins
  SDF/MOL2 upload format — use them; the planarity fallback is for defensive handling
  only. Rejected: PLIP 5.0° fallback (strict; irrelevant if bond orders present). AA-side
  rings come from the residue table (Phe/Tyr: 1 six-ring; His: 1 five-ring; Trp: **two**
  rings — BINANA's verified assignment).
- Approval: date: 2026-09-06 approver: human gate, phase-2 plan 02-01 checkpoint

#### Row 9 — Ring geometry (support rule)

- **Adopted criterion:** ring center = mean of ring-atom coordinates; ring normal = plane
  normal (first/third/fifth-atom plane per BINANA); ring radius = max(center→atom).
- **Source of the value:** BINANA definitions [V].
- **Rationale / rejected alternatives:** Matches PLIP's center computation (mean) too —
  consistent across sources.
- Approval: date: 2026-09-06 approver: human gate, phase-2 plan 02-01 checkpoint

#### Row 10 — Minimum distance (global)

- **Adopted criterion:** all pair distances must be > **0.5 Å**.
- **Source of the value:** PLIP MIN_DIST = 0.5 Å [V].
- **Rationale / rejected alternatives:** Cheap guard against coincident/duplicate atoms
  (defensive; game data shouldn't produce these).
- Approval: date: 2026-09-06 approver: human gate, phase-2 plan 02-01 checkpoint

### 2.3 Charge-group definitions (in-house standard = BINANA's verified table)

Used by row 2 (salt bridge). Verified from BINANA `INTERACTIONS.md` (2026-09-06):

- **Protein side:** Lys — amine N; Arg — guanidino (midpoint of the two terminal N);
  His — midpoint of the two ring N (**BINANA treats His as always charged — superseded
  on the AA side by the neutral-His resolution [OQ-3 / D2], §3**); Asp/Glu — carboxylate
  (midpoint of the two O).
- **Ligand side:** sp³/quaternary ammonium N; guanidino (midpoint of 2 Ns); carboxylate
  (midpoint of 2 Os); phosphate (P); sulfonate (S).
- PLIP's help page (2026-09-06) attributes protein positive charges to Arg/His/Lys
  side-chain N and negative charges to Asp/Glu carboxyl groups — consistent with the
  adopted Asp−/Glu−/Lys+/Arg+ standard set.

### 2.4 Not adopted (documented deviations)

- PLIP's donor-uniqueness / salt-bridge-overlap / hydrophobic-dedup rules: they change
  *counts*, not *presence*; fraction scoring is presence-based — simpler, and the
  deviation is honest and recorded.
- PLIP/BINANA's "His always charged" typing — superseded by the neutral-His resolution
  [OQ-3 / D2] (§3); we control protonation via our own AA templates.
- All three tools' backbone-donor/acceptor counting — superseded by D1 (side-chain-only,
  Policy Decision 4.1).

---

## 3. AA capability table (20 AAs × 7 types, side-chain-only per D1)

### 3.1 Provenance legend (per-cell marks)

- **[V-SRC]** — the classification follows deductively from a verified atom/group-typing
  rule in a fetched source (BINANA/PLIP/ProLIF) applied to the standard side-chain
  structure (textbook chemistry). Strongest available footing short of human approval.
- **[RESOLVE]** — documented cross-tool disagreement; AA-match records an explicit
  in-house resolution (the DETECT-03 "in-house resolutions of disagreements" mechanism,
  applied to typing instead of thresholds).
- **[HUMAN]** — pedagogical/in-house choice with no single authoritative tool rule; must
  be human-approved.

### 3.2 Reading rules (adopted; the human confirms at the checkpoint)

- **D2 — Capped amino acids, standard protonation per AA:** "capped" = neutral termini
  (e.g., acetyl + N-methylamide) so grid AAs carry no terminal charges; each AA object
  bundles the AA's *standard* ionization at physiological pH: Asp−, Glu−, Lys+, Arg+,
  **His neutral** (HIE/HID tautomer — pick ONE tautomer for the bundled file; typically
  HIE, but the choice belongs to the data manifest, Phase-8 approval). Under D2, HIS is
  NOT salt-bridge-capable as a cation *unless* a HIP (protonated) file is later curated.
  Protonation variants of AAs are an additive schema extension (`slot.protonation`),
  reserved but unused in v1.
- **D3 — salt_bridge and cation_pi are polarity-aware:** salt-bridge capability depends
  on the *ligand's* charge sign (ligand cationic → AA must be anionic: Asp/Glu; ligand
  anionic → AA must be cationic: Lys/Arg), and cation-π has two directions. The
  capability API is therefore `aa_capable(aa, itype, ligand_profile)` — not a bare
  two-column table.
- **D4 — cation_pi direction:** **either direction** (AA-cation over ligand ring OR
  AA-ring under ligand cation). Precedent: ProLIF ships both directions (`CationPi`,
  `PiCation`); BINANA checks both symmetrically. The detector must report cation_pi
  regardless of which side holds the cation. Rationale: demo ligands with cations are as
  common as aromatic ones; maximizes teachable moments.

### 3.3 The table (rows = the 20 standard AAs; cells = what the AA side chain can contribute on the AA side; backbone EXCLUDED per D1)

| AA | h_bond (side chain) | salt_bridge | pi_stacking | cation_pi | hydrophobic | halogen (acceptor) | metal (chelator) |
|----|---------------------|-------------|-------------|-----------|-------------|--------------------|------------------|
| Ala | — | — | — | — | Y [V-SRC: atom rule; residue set HUMAN] | — | — |
| Arg | donor (guanidinium NH1/NH2) [V-SRC: BINANA amine-donor + PLIP charged-N] | **cation** [V-SRC: PLIP+BINANA guanidino] | — | cation (over ligand ring) [V-SRC] | — | — | — |
| Asn | donor (ND2 amine) + acceptor (OD1) [V-SRC] | — | — | — | — | Y (O, N) [V-SRC: PLIP XB acceptor rule] | Y (O) [V-SRC: PLIP metal list "asparagine… (all O)"] |
| Asp | acceptor (carboxylate O) [RESOLVE→ADOPTED: carboxylate O is an H-bond acceptor per BINANA's verified rule "O/N/S atoms can act as acceptors"; research draft cell marked "—" under a protonation-dependent reading — superseded, recorded for review] | **anion** (carboxylate) [V-SRC: PLIP+BINANA] | — | — | — | Y (O) [V-SRC] | **Y (O) [RESOLVE→ADOPTED INCLUDE: PLIP's metal list omits Asp; BINANA's N/O/S rule includes it — carboxylates are canonical metal ligands]** |
| Cys | donor (thiol SH) [V-SRC: BINANA "thiol groups" donors] | — | — | — | — [RESOLVE→ADOPTED EXCLUDE from pedagogical set: KD 1982 ranks Cys among the more hydrophobic side chains (hydropathy +2.5 > Ala); pedagogically usually taught as polar-reactive — tension recorded] | Y (S) [V-SRC] | **Y (S) [RESOLVE→ADOPTED INCLUDE per PLIP+BINANA: PLIP lists Cys(S) explicitly; ProLIF's default SMARTS excludes neutral S]** |
| Gln | donor (NE2 amine) + acceptor (OE1) [V-SRC] | — | — | — | — | Y (O, N) [V-SRC] | **Y (O) [RESOLVE→ADOPTED INCLUDE: PLIP's list omits Gln; BINANA N/O/S includes]** |
| Glu | acceptor (carboxylate O) [RESOLVE→ADOPTED: same resolution as Asp] | **anion** [V-SRC] | — | — | — | Y (O) [V-SRC] | **Y (O) [RESOLVE→ADOPTED INCLUDE: PLIP includes "glutamic acid (O)" — yes; consistent]** |
| Gly | — | — | — | — | — [V-SRC: no side chain; ProLIF atom rule excludes the α-C (attached to N)] | — | — |
| His | donor + acceptor (ring N–H / ring N; neutral HIE-like default) [V-SRC: BINANA ring-N midpoint; ProLIF `[n+]c[nH]` donor] | — [RESOLVE→ADOPTED (OQ-3 / D2): neutral His bundled → **NOT a salt-bridge cation in v1**; BINANA treats His as ALWAYS charged and PLIP attributes + to His side-chain N — deviation recorded; capable only if a HIP file is later curated (additive)] | Y (one ring) [V-SRC: BINANA protein aromatics] | ring role (under ligand cation) [V-SRC + D4]; cation role only if HIP — not in v1 [RESOLVE→ADOPTED (OQ-3 / D2)] | — | Y (ring N) [V-SRC] | **Y (N) [RESOLVE→ADOPTED INCLUDE: PLIP lists His(N); ProLIF default excludes aromatic-attached N — His is the canonical Zn ligand]** |
| Ile | — | — | — | — | Y [HUMAN, V-SRC-consistent] | — | — |
| Leu | — | — | — | — | Y [HUMAN, V-SRC-consistent] | — | — |
| Lys | donor (NZ amine, charged) [V-SRC] | **cation** (NH3+) [V-SRC] | — | cation [V-SRC] | — | — | — |
| Met | — [RESOLVE→ADOPTED **EXCLUDE in v1**: BINANA "S atoms can act as acceptors" → yes; ProLIF's acceptor SMARTS has no aliphatic S → no; research recommended INCLUDE-marked-weak. **DETECT-03 disagreement recorded.** Rationale for excluding: weak thioether acceptor; excluded in v1, revisit only as a versioned capability-table change (DETECTOR_VERSION bump)] | — | — | — | Y [HUMAN, V-SRC-consistent] | Y (S) [V-SRC: PLIP acceptor rule includes S] | — [RESOLVE→ADOPTED EXCLUDE: not in PLIP's metal list; BINANA's S-rule would allow — thioether coordination is niche] |
| Phe | — | — | Y (one ring) [V-SRC] | ring (under ligand cation) [V-SRC + D4] | Y [HUMAN, V-SRC-consistent] | — | — |
| Pro | — [V-SRC: no side-chain N–H (ring N is the backbone N)] | — | — | — | Y [HUMAN, V-SRC-consistent] | — | — |
| Ser | donor + acceptor (OG) [V-SRC] | — | — | — | — | Y (O) [V-SRC] | Y (O) [V-SRC: PLIP "serin… (all O)"] |
| Thr | donor + acceptor (OG1) [V-SRC] | — | — | — | — | Y (O) [V-SRC] | Y (O) [V-SRC] |
| Trp | donor (NE1 indole) [V-SRC] | — | Y (**two rings**) [V-SRC: BINANA] | ring [V-SRC + D4] | Y [HUMAN, V-SRC-consistent] | — | — |
| Tyr | donor + acceptor (OH) [V-SRC] | — | Y (one ring) [V-SRC] | ring [V-SRC + D4] | — [RESOLVE→ADOPTED EXCLUDE from pedagogical set: ring is apolar but OH dominates pedagogy; PLIP/BINANA atom rules would partially count it — keep the taught set clean] | Y (O) [V-SRC] | Y (O) [V-SRC: PLIP "tyrosin (O)"] |
| Val | — | — | — | — | Y [HUMAN, V-SRC-consistent] | — | — |

### 3.4 Pedagogical hydrophobic set (adopted resolution)

`ALA, VAL, LEU, ILE, PRO, PHE, MET, TRP` — Cys/Tyr/Gly excluded (Cys and Tyr per the
row resolutions above; Gly has no side chain). Citation for the classification: Kyte &
Doolittle 1982, "A simple method for displaying the hydropathic character of a protein",
*J Mol Biol* 157(1):105-132, doi:10.1016/0022-2836(82)90515-0, PMID 7108955 (canonical
side-chain hydropathy scale; citation verified via the Wikipedia *Hydrophobicity scales*
article and its reference list, 2026-09-06). **[HUMAN]** — the exact membership is the
single most pedagogy-visible row of the table and is explicitly approved here; the
Wimley–White whole-residue scale (verified table on the same Wikipedia page) notably
ranks Ala/Trp differently because it includes backbone — reinforcing that the *choice of
scale* is an in-house pedagogical decision to be recorded, not a fact to be asserted.

On the AA side, hydrophobic contacts are classified **by residue name** (this pedagogical
set), not by the atom-level carbon rule — exactly as BINANA already treats protein
aromatics by residue name. The atom-level qualifying-carbon rule (threshold row 5)
applies to the **ligand side**.

### 3.5 Resolved AA sets (derived from the table under the adopted resolutions)

- **h_bond donors (side chain):** ARG, ASN, CYS, GLN, HIS, LYS, SER, THR, TRP, TYR (10)
- **h_bond acceptors:** ASN, ASP, CYS, GLN, GLU, HIS, SER, THR, TYR (9) — Met thioether-S
  EXCLUDED in v1 (recorded DETECT-03 disagreement, §3.3 Met row)
- **salt_bridge:** cationic LYS, ARG; anionic ASP, GLU (4; His not a cation in v1 per
  OQ-3 / D2; polarity-aware pairing per D3)
- **pi_stacking:** PHE, TYR, HIS, TRP (4; Trp = two rings)
- **cation_pi:** ring role PHE, TYR, HIS, TRP; cation role LYS, ARG (6 AAs; either
  direction per D4; His cation role only if a HIP file is later curated)
- **hydrophobic (pedagogical, residue-name-based on the AA side):** ALA, VAL, LEU, ILE,
  PRO, PHE, MET, TRP (8)
- **halogen acceptor (AA-side O/N/S):** ASN, ASP, CYS, GLN, GLU, HIS, SER, THR, TYR (9)
- **metal chelator (AA-side N/O/S):** ASN, ASP, CYS, GLN, GLU, HIS, SER, THR, TYR (9;
  Met thioether EXCLUDED)
- **Metal element list (ligand side, v1) [OQ-7]:** MG, ZN, FE, CA, MN, CU, NI, CO, CD

Counts per type (capable AAs, side-chain-only policy): h_bond 12 (10 donors ∪ 9
acceptors; differs from the research draft's 11 solely through the two recorded
resolutions — Met acceptor excluded, Asp/Glu carboxylate acceptors included); salt_bridge
4; pi_stacking 4; cation_pi 6; hydrophobic 8; halogen 9; metal 9. Every type has ≥ 4
capable AAs → solvability sampling never starves at any grid size; the "≥ 2 capable AAs
per type" invariant is asserted as a permanent test.

Approval (capability table §3 as a whole, including all resolutions):
Approval: date: 2026-09-06 approver: human gate, phase-2 plan 02-01 checkpoint

---

## 4. Policy decisions

### 4.1 D1 — Side-chain-only capability

**Decision:** The capability table is side-chain-only; the detector MUST restrict H-bond
donor/acceptor (and hydrophobic, residue-name-based) matching to side-chain atoms of grid
AAs. The ligand side may use its full chemistry.

**Rationale:** Verified from the sources: ProLIF counts backbone donors/acceptors (its
tutorial shows VAL as HBAcceptor — a backbone hit; the v2.2.1 changelog explicitly
discusses backbone-N acceptor handling), PLIP metal complexes include "all main chain
oxygens", BINANA tallies backbone vs side-chain separately. If backbone H-bonds counted,
EVERY capped AA would be h_bond-capable → `h_bond` solvability is trivial, the hint
lights up the whole grid, and the "which side chains do what" pedagogy collapses. This
single decision changes the table more than any chemistry claim.

**Binds:** `aamatch/capability.py` (02-05), `aamatch/detector.py` (02-06/07), generator
tests (02-08/02-09).

### 4.2 Single typing home — `aamatch/capability.py`

**Decision:** `aamatch/capability.py` is the ONLY atom/residue typing module (the
detection research's proposed `chem_types.py` is merged into it).

**Rationale:** One shared module is what makes generator capability (GEN-04 solvability,
`can_form`), detector typing, and the Hint's live eligibility check (PLAY-05) agree by
construction rather than by convention — the DETECT-04 requirement. `aamatch/thresholds.py`
(02-06) remains the separate home of the numeric threshold constants (§2).

**Binds:** all consumers (generator, detector, Hint later). DETECT-04 holds by
construction.

### 4.3 OQ-1 — Interaction-mode semantics

**Decision:**

- `exclusive` = "any interaction formed", **scoped by `allowed_interactions`**.
- `exclusive` + empty allowed list → `GenerationError` at generate time.
- `unset` + empty allowed list → draw from all 7 types (unset means "the game picks").
- `block_exclusive` + checked type the ligand cannot support → refuse, naming the type
  (never silently degrade).

**Rationale:** `allowed_interactions` is the game's interaction vocabulary everywhere
(setup serialization keeps it canonical even in `unset` mode; SCORE-04 displays required
types from it); REQUIREMENTS.md SETUP-06's exact wording is authoritative.

**Binds:** generator `derive_required` (02-08), score `any` semantics (02-10).

### 4.4 OQ-4 — Cation-π anti-artifact rule (asymmetric v1)

**Decision:** Keep PLIP's ligand-side-only tertiary-amine anti-artifact rule for
cation-π: when the small molecule carries the cation, an amine-substituent-plane normal
vs ring normal > 30° rejects the hit ("pi-cation interaction 'through' the ligand"). The
rule is NOT applied to the AA side (LYS/ARG) in v1 — documented asymmetry.

**Rationale:** Verified PLIP behavior; LYS's charged N geometry is well-constrained by
its own chain anyway; revisit only if playtesting shows through-side false positives.

**Binds:** `aamatch/detector.py` (02-06/07).

### 4.5 OQ-5 — Hydrophobic in `unset`-mode required-type sampling

**Decision:** Hydrophobic is excluded from `unset`-mode required-type sampling
(generator policy; detection semantics unchanged).

**Rationale:** The 4.0 Å C-C criterion is permissive; in random-required-set levels,
hydrophobic makes success near-trivial. Detection still reports hydrophobic normally —
this is a sampling policy, not a threshold change.

**Binds:** generator `derive_required` (02-08); detector (02-06/07) unchanged.

### 4.6 Purity convention — no `itertools` in pure modules

**Decision:** `itertools` is NOT added to `ALLOWED_STDLIB` in `tests/test_purity.py` —
pure modules use comprehensions/nested loops instead. (Deliberate decision; binds every
Phase-2 pure-module plan. If it ever becomes genuinely necessary, extending the whitelist
is a conscious, reviewed gate change — never a silent import.)

**Binds:** every Phase-2 pure-module plan (`capability.py` 02-05, `thresholds.py` 02-06,
`detector.py` 02-06/07, `generator.py` 02-08, `scoring.py` 02-10).

### 4.7 Bump policy — DETECTOR_VERSION

**Decision:** Any change to threshold rows 1–10 (§2) or to capability typing (§3)
requires bumping `DETECTOR_VERSION` in `aamatch/level_spec.py` (exact-match gate: a spec
generated under a different detector_version is refused — "stale or newer … regenerate").
The two version gates must never be conflated: the format `version`
(`FORMAT_VERSION` in `aamatch/persistence.py`) refuses only NEWER and accepts older
(additive-only evolution); `detector_version` refuses ANY mismatch (changed detection
semantics make specs unsolvable). Typing/threshold constants in
`aamatch/thresholds.py` (02-06) and `aamatch/capability.py` (02-05) are transcribed
row-by-row from this document — a doc change without a code+version change is a bug.

**Binds:** 02-05, 02-06, 02-07, 02-08, 02-10, and every later phase touching detection.

---

## 5. Chemistry policy summary

Each item is stated in full in the detector module docstring (02-06/07) — summarized
here for the gate (from the detection research §7):

1. **Waters excluded entirely.** The cmd-tier extraction collects only game objects
   (grid AAs + ligand); demo structures are stripped of waters before bundling; no
   water-bridge type in v1 (EXT-01 deferred). PLIP precedent: all-water metal complexes
   are skipped even there.
2. **Alt-conf: keep `''`/`'A'` only.** Defensive pure-layer policy
   (`apply_altloc_policy(atoms)`) applied before typing, unit-tested; PLIP ships
   `ALTLOC = False`. Game objects have no altlocs anyway; never "best-scoring
   conformer" (nondeterministic).
3. **Fail-closed donor typing.** An O/N/S **without an attached H is not a donor**.
   Ligands: SDF/MOL2 with explicit H + bond orders (spec GEN-02); AAs materialized with
   polar hydrogens (mechanism = OQ-2, cmd-tier decision). Rationale: BINANA documents
   that guessing protonation degrades accuracy; a guessed-H detector that fires wrong
   H-bonds is worse for a teaching game than one that misses marginal ones. The shared
   typing tables keep generator capability and detector typing consistent, so
   fail-closed cannot create unsolvable levels.
4. **State 1 only.** World/object coordinates, PyMOL state 1 only; game objects are
   single-state by design; the detector documents "state the caller gave me". Camera
   frame never enters (matrix/camera composition is the caller's job — PITFALLS 12).
5. **Metal gating via `ligand_has_metal`.** Metal coordination runs only if ≥ 1
   ligand-side atom's element is in the adopted metal list (§3.5); `capability.py`
   exposes `ligand_has_metal(atoms)` so the generator's required-type selection mirrors
   the same gate (never require metal coordination on a metal-free ligand). Intra-ligand
   coordination is unrepresentable (cross-side enumeration only).
6. **Covalent exclusions.** Atoms bonded to each other (intra-side) never pair;
   cross-side pairs at MIN_DIST 0.5 Å guard against coordinate duplicates. Covalent
   ligand interactions are out of scope per REQUIREMENTS.md.
7. **MIN_DIST 0.5 Å global** (threshold row 10): all pair distances must be > 0.5 Å —
   cheap guard against coincident/duplicate atoms.

---

## 6. Approval record

- **Date:** 2026-09-06
- **Approver:** human gate, phase-2 plan 02-01 checkpoint (DETECT-03 [GATE],
  checkpoint:human-verify)
- **Scope approved:** the full document — the 10 threshold rows (§2, each row's
  `Approval:` line), the charge-group table (§2.3), the AA capability table §3 as a
  whole including all recorded resolutions (§3.3–§3.5), and the policy decisions
  (§4.1–§4.7).
- **Freeze statement:** Detector implementation (plans 02-05..02-08) freezes against
  this table; any later change requires a DETECTOR_VERSION bump.
- **Units + atom-typing verification (the human's approval condition, checked
  2026-09-06 before recording):** every distance criterion is explicitly in Ångström
  (Å) and every angle criterion explicitly in degrees; atom-typing element sets are
  unambiguous (H-bond donor/acceptor O/N/S rules, halogen donors = Cl/Br/I with C-F
  excluded, metal list {MG, ZN, FE, CA, MN, CU, NI, CO, CD}, hydrophobe carbon rule
  `element C with all bonded neighbors ∈ {C, H}`, ring-atom rules). No adopted value
  was changed during the check; only explicit units were added to values that lacked
  them, and all values were cross-checked against the verified research §3
  (02-RESEARCH-detection.md) with no contradiction found.
- **Provisional scope (human caveat, recorded in substance):** approved with the
  condition that units and atom typing were checked at approval time, and values may
  need to be adjusted depending on the final curated dataset to be used. Such a
  revisit is a DETECTOR_VERSION bump event (§4.7) — never a silent edit.

