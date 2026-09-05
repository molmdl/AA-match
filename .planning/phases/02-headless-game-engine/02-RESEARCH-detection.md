# Phase 2 — Detection Engine Research (DETECT-01 … DETECT-05)

**Researched:** 2026-09-06 (all web sources fetched 2026-09-06 unless dated otherwise)
**Domain:** In-house geometric interaction detection — seven types, threshold provenance, pure-layer architecture, chemistry policy, perf verification
**Scope note:** One of three parallel Phase-2 researchers. Covers DETECTION only. Grid generation and cmd-tier materialization/smoke plumbing are other researchers' scope; interface needs are noted, not designed.
**Confidence:** HIGH for all published threshold values (every number below was read today from the official PLIP/ProLIF/BINANA repositories, with file-level citations; BINANA values double-verified from two files in the same repo). The *in-house resolutions* and the *capability matrix* are proposals by definition — they are the human gate's (DETECT-03) content, clearly marked.

---

## Summary

This research answers "what do I need to know to plan the detection engine well?" in five parts. (1) **The published criteria are now fully verified**: PLIP's complete threshold table (`plip/basic/config.py`, v3.0.1) and its exact detection mechanics (`plip/structure/detection.py`), ProLIF's complete per-class defaults (`prolif/interactions/interactions.py`, master), and BINANA's full parameter table (`INTERACTIONS.md` + `default_params.py`) plus the one ambiguous prose item — the H-bond/halogen-bond angle — resolved from source (`_hydrogen_halogen_bonds.py`: deviation-from-linear ≤ 40°, i.e. D-H···A angle ≥ 140°). All three DOIs are verified from the projects' own files. (2) The three sources **agree on criterion *shapes*** (distance + one or two angles; charge-group centers for salt bridges; ring centers/normals for π types) but **disagree on values** for every type except cation-π distance — so the in-house table cannot be a straight copy; a per-row resolution with rationale is required, drafted below. (3) The detector architecture that fits the purity gates is **five new pure modules** (`vec3`, `spatial`, `chem_types`, `thresholds`, `detector`): feature precomputation (rings, charge groups) + cell-list spatial pruning for atom-level contacts + per-candidate constant-time vector math, with explicit partner sides on every result record and a canonical result order. (4) "Vectorized, not loop-bound" in stdlib Python 3.6 means exactly: no all-pairs enumeration; O(N) bucketing; two-level pruning (per-AA bounding-sphere prefilter, then cell-list candidate pairs); results as presence-per-(type, AA) for binary scoring. (5) The perf budget is verifiable headlessly with a scripted largest-ligand + max-grid smoke that asserts detect < 100 ms (the PITFALLS.md stated figure) and records extract+detect wall time.

**Primary recommendation:** Adopt the in-house threshold table drafted in §3 (each row citing the verified source it comes from, with recorded rationale where sources disagree), implement it behind the five-module pure architecture in §5, and put the threshold document + approval in front of the human as the phase's first plan — the gate is the critical path and everything downstream (capability matrix, generator, hint, scoring) consumes it.

---

## 1. Verified facts (citations + access dates)

### 1.1 Sources and what was fetched (access date 2026-09-06 for all)

| Source | Version | Files fetched (official repo, raw.githubusercontent.com) | Confidence |
|---|---|---|---|
| PLIP | 3.0.1 (master, `pharmai/plip`) | `plip/basic/config.py` (thresholds + METAL_IONS), `plip/structure/detection.py` (all geometric tests) | HIGH |
| ProLIF | 2.2.x (master, `chemosim-lab/ProLIF`) | `prolif/interactions/interactions.py` (all class defaults), `CITATION.cff` (DOI) | HIGH |
| BINANA | 2.1 (main, `durrantlab/binana`) | `INTERACTIONS.md` (algorithm + full parameter table), `python/binana/interactions/default_params.py` (values cross-check), `python/binana/interactions/_hydrogen_halogen_bonds.py` (angle semantics), `README.md` (DOI) | HIGH (double-verified) |

Repo trees also verified via the GitHub contents API (paths above exist on the default branches; PLIP `preparation.py` and BINANA `_metal_coordination.py` located but not fetched — see §2 unverified items).

### 1.2 DOIs (each from the project's own repository file)

| Tool | Citation | Verified in |
|---|---|---|
| PLIP | Schake, Bolz et al., "PLIP 2025 …", Nucl. Acids Res., doi:10.1093/nar/gkaf361 | PLIP's own `config.py` `__citation_information__` + repo description (2026-09-06) |
| ProLIF | Bouysset & Fiorucci, J Cheminform 13:72 (2021), doi:10.1186/s13321-021-00548-6 | ProLIF's own `CITATION.cff` (2026-09-06) |
| BINANA | Durrant JD, McCammon JA, J Mol Graph Model 29(6):888-893 (2011), doi:10.1016/j.jmgm.2011.01.004 | BINANA's own `README.md` (2026-09-06) |

*Human gate still applies:* DETECT-03 requires explicit human approval of the threshold document before the detector freezes; the citations above are verified as *what the sources publish*, and the gate approves *our adoption* of them.

### 1.3 The exact angle convention every source uses for H-bonds (settled — this was the ambiguous one)

All three tools measure the **same** angle — at the hydrogen, between the donor and acceptor directions (∠D-H···A). Verified from code:

- **PLIP** (`detection.py`, `hbonds()`): `vecangle(vector(h→d), vector(h→acc)) > HBOND_DON_ANGLE_MIN` → ∠D-H···A > 100°.
- **BINANA** (`_hydrogen_halogen_bonds.py`): `angle = fabs(180 − angle_between_three_points(donor, H, acceptor))`; bond kept iff `angle ≤ 40` → ∠D-H···A ≥ 140°. The `INTERACTIONS.md` prose ("angle … is no greater than 40 degrees") is loose wording for *deviation from linear*; the source is unambiguous.
- **ProLIF** (`interactions.py`, `HBAcceptor` docstring): `DHA_angle = (130, 180)` — "the `[Acceptor]...[Hydrogen]-[Donor]` angle", i.e. the same angle at H, ∈ [130°, 180°].

This means the three H-bond criteria differ **only in numbers** (distance 4.1 / 4.0 / 3.5 Å; angle >100° / ≥140° / ≥130°), which makes the in-house resolution clean.

---

## 2. Per-type published criteria: what each source says (Q1)

Legend: **[V]** = verified from primary source today (file cited). Every numeric value below is **[V]** unless marked.

### 2.1 Hydrogen bond

| Criterion | PLIP | BINANA | ProLIF |
|---|---|---|---|
| Distance (donor···acceptor, heavy atoms) | 0.5 < d < **4.1 Å** (Hubbard & Haider 2001 + 0.6, "extended for low-quality structures") [V config.py] | d ≤ **4.0 Å** [V default_params.py] | d ≤ **3.5 Å** [V interactions.py] |
| Angle | ∠D-H···A > **100°** [V detection.py] | \|180° − ∠D-H···A\| ≤ **40°** (⇔ ≥140°) [V _hydrogen_halogen_bonds.py] | ∠D-H···A ∈ **[130°, 180°]** [V interactions.py] |
| Donor typing | donors with attached H (preparation classifies donor-H pairs) [V detection.py signature: `donor_pairs` = (d, h)] | hydroxyl, amine, thiol groups (O/N/S + H); when H absent, sp2/sp3 geometry scoring fallback [V INTERACTIONS.md + code] | SMARTS donor: `[$([O,S,#7;+0]),$([Nv4+1]),$([n+]c[nH])]-[H]` [V] |
| Acceptor typing | O/N/S-based (preparation) [V shape] | O, N, S [V] | SMARTS acceptor (excludes amides-in-ring etc., long pattern) [V] |
| Dedup | donor in only one H-bond (keep closest to 180°); acceptors may be multi-partner; H-bonds inside salt bridges suppressed [V help page 2026-09-05 per FEATURES.md] | donor-count limits in the no-H fallback path only [V code] | none documented (yields all matches) [V] |

### 2.2 Salt bridge (ionic folded in)

| Criterion | PLIP | BINANA | ProLIF |
|---|---|---|---|
| Distance | charge-center ↔ charge-center < **5.5 Å** (Barlow & Thornton 1983 + 1.5) [V] | representative-charge-point ↔ representative-charge-point < **5.5 Å**, opposite signs [V] | charged **atom** ↔ charged **atom** ≤ **4.5 Å** [V] |
| Charged-group definitions (protein side) | Lys/Arg/His + , Asp/Glu − (help page, verified 2026-09-05 per FEATURES.md; atom-name lists live in `preparation.py` — path verified, contents not fetched) | Lys N; Arg midpoint of terminal Ns; **His midpoint of ring Ns — always treated charged**; Asp/Glu midpoint of the two Os [V INTERACTIONS.md] | SMARTS-based (protonation-dependent) [V] |
| Ligand-side charged groups | quaternary/sp³ ammonium, guanidino, carboxylate, phosphate, sulfonate (help page 2026-09-05) | sp³/quaternary ammonium N; guanidino (midpoint of 2 Ns); carboxylate (midpoint of 2 Os); phosphate (P); sulfonate (S); metal-cation names MG, MN, RH, ZN, FE, BI, AS, AG [V INTERACTIONS.md] | SMARTS: `+{1-}`/`- {1-}` with resonance forms (carboxylate `O=[C,S,P]-[O-]`, amidine/guanidine) [V] |

### 2.3 π-stacking (parallel + T-shaped as ONE category)

| Criterion | PLIP | BINANA | ProLIF |
|---|---|---|---|
| Ring-center distance | < **5.5 Å** (McGaughey 1998) [V] | ≤ **7.5 Å** [V] | FaceToFace ≤ **5.5 Å**; EdgeToFace ≤ **6.5 Å** [V] |
| Angle | deviation from parallel **or** perpendicular < **30°** (single test: `a = min(θ, 180−θ)`; P: a<30; T: 90±30) [V detection.py] | normals within **30°** of parallel (P) or **30°** of perpendicular (T) [V] | FaceToFace plane angle ∈ **[0°, 35°]**, normal-centroid ∈ [0°, 33°]; EdgeToFace plane angle ∈ **[50°, 90°]**, normal-centroid ∈ [0°, 30°] [V] |
| Lateral displacement | projected opposite-center offset < **2.0 Å** (benzene radius + 0.5) [V] | **any projected ring atom inside padded disk** (radius + **0.75 Å**) for P; for T additionally closest atom-atom dist ≤ **5.0 Å** and projected *center* in disk [V] | EdgeToFace: plane-intersection point within **1.5 Å** of opposite centroid [V] |
| Ring finding | ring perception + planarity fallback, `AROMATIC_PLANARITY = **5.0**`° deviation [V config.py] | 5/6-member rings; planarity = adjacent-dihedral deviation ≤ **15°**; **Phe/Tyr/His one ring, Trp two rings** [V] | SMARTS aromatic 5/6-rings [V] |

### 2.4 Cation-π

| Criterion | PLIP | BINANA | ProLIF |
|---|---|---|---|
| Distance (charge center ↔ ring center) | < **6.0 Å** (Gallivan & Dougherty 1999) [V] | < **6.0 Å** [V] | ≤ **4.5 Å** [V] |
| In-ring test | charge projected into ring plane; offset from center < **2.0 Å** (reuses PISTACK_OFFSET_MAX) [V] | projected charge point inside padded disk (radius + 0.75) [V] | angle between ring normal and centroid→cation vector ∈ **[0°, 30°]** (axis-perpendicularity) [V] |
| Directionality | both sides handled (`rings × pos_charged`, `protcharged` flag) [V] | charge points × ring centers, side-agnostic [V] | **explicit pair**: CationPi (lig cation → res ring) and PiCation (lig ring → res cation) [V] |
| Anti-artifact rule | **ligand-side tertiary amines only**: amine-substituent-plane normal vs ring normal must be ≤ **30°** or the hit is rejected ("pi-cation interaction 'through' the ligand") [V detection.py] | none documented [V] | none documented [V] |

### 2.5 Hydrophobic contact

| Criterion | PLIP | BINANA | ProLIF |
|---|---|---|---|
| Distance | 0.5 < d < **4.0 Å** [V] | C-C ≤ **4.0 Å** [V] | ≤ **4.5 Å** [V] |
| Hydrophobic atom definition | "qualified carbon atoms" = **carbon whose neighbors are only C/H** (help page 2026-09-05 per FEATURES.md; typing in `preparation.py`) | AutoDock carbon types (PDBQT typing) [V] | SMARTS: aromatic C/S + chain carbons, **excluding any C bonded to N/O/F**, not charged [V; 2.1.0 changelog confirms the exclusion] |
| Count explosion handling | mandatory reduction: per-residue closest-only, then per-atom closest-only [V help page] | plain tallies (two distance tiers) [V] | n/a (per-atom-pair yields) [V] |

### 2.6 Halogen bond (AA-match: ligand-side donors only)

| Criterion | PLIP | BINANA | ProLIF |
|---|---|---|---|
| Distance (acceptor atom ··· halogen) | 0.5 < d < **4.0 Å** (Auffinger + 0.5) [V] | ≤ **5.5 Å** [V] | ≤ **3.5 Å** [V] |
| Donor angle ∠(A···X-D) | **165° ± 30** [V] | deviation-from-linear ≤ **40°** (⇔ ≥140°; same shared angle code as H-bond) [V code] | ∈ **[130°, 180°]** [V] |
| Acceptor angle ∠(Y-A···X) | **120° ± 30** [V] | — (no acceptor angle) [V] | ∈ **[80°, 140°]** (Auffinger et al. PNAS 2004, per docstring) [V] |
| Donor typing | C-X (detection is "Y-O···X-C"); donors classified on both sides, but proteins are halogen-free in practice [V] | donors **O-X, N-X, S-X, C-X**, X ∈ {I, Br, Cl, F} [V] | `[#6,#7,Si,F,Cl,Br,I]-[Cl,Br,I,At]` [V] |
| Acceptor typing | O ("Y-O···X-C") [V] | O, N, S [V] | N, O, P, S, Se, Te + aromatic C, not positively charged [V] |

### 2.7 Metal coordination (AA-match: only when the ligand carries a metal)

| Criterion | PLIP | BINANA | ProLIF |
|---|---|---|---|
| Distance (metal ··· coordinating atom) | < **3.0 Å** (Harding 2001) [V] | ≤ **3.5 Å** [V] | ≤ **2.8 Å** [V] |
| Geometry beyond distance | coordination-geometry **fitting** (ideal angle signatures for CN 2–6: linear, trigonal planar/pyramidal, tetrahedral, square planar, trigonal bipyramidal, square pyramidal, octahedral), lowest-RMS choice, superfluous targets excluded, all-water complexes skipped [V detection.py] | **distance-only, explicitly no angle check**, with published rationale: many geometries possible, L-M-L angles deviate widely, sites may be vacant [V INTERACTIONS.md] | distance-only [V] |
| Metals | `METAL_IONS` whitelist: CA, CO, MG, MN, FE, CU, ZN, FE2/3/4/1, LI, NA, K, RB, SR, CS, BA, CR, NI, RU/RU1, RH/RH1, PD, AG, CD, LA, W/W1, OS, IR, PT/PT1, AU, HG, CE, PR, SM, EU, GD, TB, YB, LU, AL, GA, IN, SB, TL, PB [V config.py] | salt-bridge cation names MG, MN, RH, ZN, FE, BI, AS, AG [V; full coordination metal list lives in `_metal_coordination.py` — not fetched, §2-open] | SMARTS `[Ca,Cd,Co,Cu,Fe,Mg,Mn,Ni,Zn]` [V] |
| Coordinating atoms | metal-binding groups on both sides + water [V] | N, O, Cl, F, Br, I, S near the cation [V] | O, N (exclusions), anions [V] |

### 2.8 Where the sources disagree (summary) — this is why DETECT-03 exists

Every type has at least one numeric disagreement; the criterion *shapes* agree everywhere (distance + 1–2 angles; group centers for charges; ring center/normal for π). Notable disagreements: H-bond angle (100/130/140 lower bounds), π-stacking center distance (5.5/7.5/5.5-6.5) and lateral test (center-offset vs any-atom-disk), halogen-bond distance (4.0/5.5/3.5) and angle form (two-angled vs one-angled), metal distance (3.0/3.5/2.8) and geometry-fitting-or-not, hydrophobic distance (4.0/4.0/4.5) and atom typing (name/graph-based vs SMARTS). This confirms the project Key Decision recorded in FEATURES.md: **one internally consistent in-house table, cited per row, human-approved** — no value can be copied on authority.

---

## 3. Proposed in-house threshold table (DRAFT — the DETECT-03 human gate approves this)

Selection principles used (record so the human can veto the principles, not just the numbers):

- **P1 — One source per row where possible** (cleanest provenance); interpolate only with recorded rationale.
- **P2 — Game-tuned, not analysis-tuned:** PLIP's permissiveness exists because it analyzes low-resolution crystal structures; a hand-placement game needs *decisive* geometry (a student must be able to tell success from failure), but slightly generous distances (no guides on screen). Strict angles, moderate distances.
- **P3 — Majority rule when two of three agree.**
- **P4 — Fewest geometric tests per type** that preserve chemical meaning (implementation + test surface).

| # | Type | Adopted criterion | Source of the value | Rationale / rejected alternatives |
|---|------|-------------------|--------------------|-----------------------------------|
| 1 | H-bond | D···A ≤ **4.0 Å** AND ∠D-H···A ≥ **140°** (both measured heavy-donor to heavy-acceptor / at H) | BINANA pair (4.0, ≥140) [V] | One-source pair, internally consistent; generous distance (kind to hand placement), decisive direction. Rejected: PLIP 4.1/100° (too permissive — sloppy placements would count; the 100° floor admits near-perpendicular donors), ProLIF 3.5/130° (distance tight for unguided play). **Needs explicit polar H on both sides** (§7.3). |
| 2 | Salt bridge | opposite charge-**group centers** ≤ **5.5 Å** | PLIP = BINANA = 5.5 [V] | Unanimous distance; group-center form (both PLIP & BINANA) is more chemically faithful than ProLIF's atom-atom 4.5 and matches the charge-group table we need anyway. Charge-group definitions: BINANA's verified table (§2.2) as the in-house standard. |
| 3 | π-stacking (one category) | ring-center dist < **5.5 Å** AND (normals within **30°** of parallel OR within **30°** of perpendicular) AND projected-center offset < **2.0 Å** — single test covers both sub-geometries; reported type is always `pi_stacking` (sub-type P/T recorded as a metric only) | PLIP set (5.5 / 30 / 2.0) [V] | One uniform test for both orientations (fewest rules — P4); published as one table. Rejected: BINANA 7.5 (catches distant stacks — makes the type easy; also needs two different lateral tests), ProLIF FTF+ETF (two parameter sets + intersect computation). Both T-shaped and parallel count as the same category per spec (EXT-02 defers the split). |
| 4 | Cation-π | charge center ↔ ring center ≤ **6.0 Å** AND projected charge offset < **2.0 Å**; direction recorded (AA-cation→lig-ring vs lig-cation→AA-ring) | distance: PLIP+BINANA 6.0 (majority — P3); offset: PLIP 2.0 (same helper as row 3) [V] | The 2.0 Å offset ≈ BINANA's padded benzene disk (1.4+0.75) — near-equivalent, cheaper to implement. Rejected: ProLIF 4.5 (too strict for a game) and its axis-angle test (harder to reason about for students). PLIP's ligand-tertiary-amine anti-artifact rule (amine-plane normal vs ring normal ≤ 30° to count) **adopted only when the small molecule carries the cation** — mirrors PLIP's ligand-side-only rule; documented asymmetry, flagged in §9 OQ-4. |
| 5 | Hydrophobic | ≥1 pair of qualifying carbons with d ≤ **4.0 Å**; qualifying carbon = element C with all bonded neighbors ∈ {C, H} | distance: PLIP+BINANA 4.0 (majority — P3); typing: PLIP's graph rule [V] | Graph rule is computable from the SDF/MOL2 bond block without atom-type tables (ProLIF's SMARTS excludes C-N/O/F — same spirit, majority-verified). **Binary presence semantics** ("≥1 qualifying contact between this AA and the ligand") deliberately sidesteps PLIP's documented count explosion and dedup machinery — counts are irrelevant to fraction scoring (FEATURES.md finding). Gameplay flag: hydrophobic is easy to satisfy; §9 OQ-5. |
| 6 | Halogen bond | acceptor atom ··· halogen ≤ **4.0 Å** AND ∠(A···X-D) ∈ **135°–195°** (165±30) AND ∠(Y-A···X) ∈ **90°–150°** (120±30); donors **ligand-side only**, X ∈ {F, Cl, Br, I}; acceptors AA-side O/N/S | PLIP full set (4.0 / 165±30 / 120±30) [V] | One source (P1); two-angle form encodes σ-hole chemistry; 4.0 Å is the kindest verified distance (BINANA's 5.5 is loose enough to fire on casual proximity; ProLIF's 3.5 frustrates). Donor-side restriction is the spec's own rule (both PLIP and BINANA treat proteins as halogen-free in practice — the spec just makes it explicit). |
| 7 | Metal coordination | metal ··· coordinating atom ≤ **3.0 Å**, **distance-only** (no geometry fitting); metals gated to ligand-side presence; donors AA-side N/O/S | distance: PLIP 3.0 (between ProLIF 2.8 and BINANA 3.5); no-angles: BINANA's published rationale [V] | BINANA explicitly documents why angle/geometry checks are omitted (many geometries, wide real-world L-M-L deviation, vacant sites) — direct precedent; PLIP's fitting machinery is analysis output we don't need. Adopted metal element list (v1): **{MG, ZN, FE, CA, MN, CU, NI, CO, CD}** — the biologically common intersection/union core of the three verified lists (all three members verified in §2.7); full union available at the gate if the human wants broader coverage. |
| 8 | Aromatic ring identification (support rule for rows 3–4) | primary: **bond-order-derived aromaticity** from the SDF/MOL2 bond block; fallback for missing bond orders: 5/6-member ring with adjacent-dihedral deviation ≤ **15°** | fallback value: BINANA 15° [V]; SDF-first: project decision (PITFALLS 12; spec GEN-02) | Bond orders are the reason the spec pins SDF/MOL2 upload format — use them; the planarity fallback is for defensive handling only. Rejected: PLIP 5.0° fallback (strict; irrelevant if bond orders present). AA-side rings come from the residue table (Phe/Tyr: 1 six-ring; His: 1 five-ring; Trp: **two** rings — BINANA's verified assignment). |
| 9 | Ring geometry (support rule) | ring center = mean of ring-atom coordinates; ring normal = plane normal (first/third/fifth-atom plane per BINANA); ring radius = max(center→atom) | BINANA definitions [V] | Matches PLIP's center computation (mean) too — consistent across sources. |
| 10 | Minimum distance (global) | all pair distances must be > **0.5 Å** | PLIP MIN_DIST = 0.5 [V] | Cheap guard against coincident/duplicate atoms (defensive; game data shouldn't produce these). |

**Not adopted (documented deviations):** PLIP's donor-uniqueness / salt-bridge-overlap / hydrophobic-dedup rules (they change *counts*, not *presence*; fraction scoring is presence-based — simpler, and the deviation is honest and recorded). PLIP/BINANA's "His always charged" typing — see §7.4 (we control protonation; neutral-His default proposed). All three tools' backbone-donor/acceptor counting — see §6 capability-matrix recommendation.

**Bump policy:** any change to rows 1–10 or to the typing tables in `chem_types.py` requires bumping `DETECTOR_VERSION` in `aamatch/level_spec.py` (exact-match gate already implemented and tested in Phase 1 plan 06). The threshold document must record approval date + approver per row.

---

## 4. Partner sides & roles (Q2 — DETECT-04)

**Mapping the sources' roles onto AA-match's two-sided world.** The game has exactly two sides: `aa` (grid amino acid objects) and `lig` (the small molecule). Every detector result record names both sides explicitly plus per-type roles:

| Type | AA side role | Ligand side role | Direction-sensitive? |
|---|---|---|---|
| H-bond | donor OR acceptor (per contact; role field) | the complement | yes — matters for capability matrix (SER donates & accepts; ASP only accepts) |
| Salt bridge | cationic group (LYS/ARG) or anionic (ASP/GLU) | complement | yes |
| π-stacking | ring (PHE/TYR/HIS/TRP) | ring | no |
| Cation-π | cation (LYS/ARG) **or** ring | complement | **yes — two directions** (ProLIF's CationPi vs PiCation split is the precedent; a LYS can only do cation→ring; a TRP only ring→cation... a TRP could theoretically also H-bond but not cation-π as cation) |
| Hydrophobic | carbon set | carbon set | no |
| Halogen bond | **acceptor only** (O/N/S) | **donor only** (C-X) | fixed by spec — enforced by enumerating only (AA-acceptor × lig-donor) pairs; PLIP/BINANA are side-agnostic in code (proteins happen to be halogen-free) — we make it structural |
| Metal coordination | donor (N/O/S) | **metal carrier** (gating) | fixed by spec — metal must be ligand-side; AA-side atoms coordinate to it |

**Consequence for the pipeline (the DETECT-04 mechanism):** interactions are *always* cross-side. The detector enumerates only (aa-atom/feature × lig-atom/feature) candidate pairs — an AA↔AA or lig↔lig contact is unrepresentable. Result records carry `{"type", "aa": {object, atom ids, resn, resi, role}, "lig": {object, atom ids, role}, "metrics": {...}, "formed": true}`. Scoring collapses to "required type T counts as formed iff ≥1 record of type T exists" — hint/capability (PLAY-05) and generator solvability (GEN-04) consume the *same* role information from the *same* typing tables, which is what makes DETECT-04's "capability checks and scoring agree" hold by construction rather than by convention (§5.3).

**HIS asymmetry note:** BINANA and PLIP both treat His as always-charged *because they cannot know PDB protonation*. AA-match controls its own AA templates, so the game can be principled (§7.4). But cation-π/salt-bridge capability for His follows the adopted protonation policy, not the sources' guess.

---

## 5. Detector architecture in the pure layer (Q4)

### 5.1 Module split (5 new pure modules — all must be added to `PURE_MODULES` in `tests/test_purity.py`)

```
aamatch/
├── vec3.py          # PURE  ~100 lines: 3-vector math on tuples (add/sub/dot/cross/
│                    #        norm/dist/angle-at/point-plane-projection). math only.
├── spatial.py       # PURE  cell-list neighbor search: build_index(atoms, cell) ->
│                    #        dict[(i,j,k)] -> [atom idx]; cross_pairs(a_atoms, b_atoms,
│                    #        cutoff) -> candidate pairs. + brute_force_pairs() used by
│                    #        the equivalence test ONLY.
├── chem_types.py    # PURE  typing tables + functions: AA residue table (donors/
│                    #        acceptors/charge groups/ring atom names/hydrophobic
│                    #        atoms per residue); ligand-side typing from atom records
│                    #        + bond block (rings+aromaticity, donors/acceptors,
│                    #        charge groups, hydrophobes, halogens, metals). No geometry
│                    #        thresholds here — typing only.
├── thresholds.py    # PURE  the human-approved table of §3 as named constants, each
│                    #        with a source comment (value + citation + approval date
│                    #        placeholder). Single import point for the detector.
├── detector.py      # PURE  pipeline: typed features + cell-list candidates ->
│                    #        per-type geometric tests -> canonical result records.
│                    #        Module docstring carries the chemistry policy (§7).
```

Dependency direction (strictly downward, mirrors the Phase-1 contract): `thresholds` → standalone; `vec3` → standalone; `spatial` → `vec3`; `chem_types` → `vec3`; `detector` → all four. No module imports `level_spec`/`persistence` (detector consumes plain data; the caller passes typed atom records + bonds).

**Interface contract with the cmd tier (noted, not designed):** the detector consumes plain atom records — `{"side": "aa"|"lig", "object": str, "id": int, "name": str, "elem": str, "resn": str, "resi": int, "alt": str, "x": float, "y": float, "z": float}` — plus the ligand bond block `[(i, j, order)]` (from the SDF/MOL2 load, cmd-tier extraction) and returns plain dicts. Coordinates are **final composed world-frame coordinates** (the caller resolves object matrices — Pitfall 12 matrix-blindness). The same extraction helper must serve the Phase-2 smoke AND the Phase-3 wizard confirm so both paths feed the detector identically.

### 5.2 Pipeline ("vectorized, not loop-bound" in stdlib 3.6 — DETECT-05 reconciliation)

The roadmap reconciles "numpy vectorized" with the purity gate as: *vectorization + spatial pruning implemented stdlib-pure; numpy only in cmd-tier helpers; perf verified headless.* Concretely, that means:

1. **Feature precomputation (O(atoms), once per detect):** ligand rings (centers/normals/radii), AA-side rings, charge-group centers both sides, donor-H pairs, acceptor/hydrophobe/halogen/metal atom lists. No per-pair recomputation of centroids/normals.
2. **Coarse AA-level prefilter (O(#AAs)):** each placed AA gets a bounding sphere; only AAs whose sphere intersects the ligand's bounding sphere inflated by the max cutoff (7.5 Å) proceed. In a real placement, most grid AAs are far away — this prunes ~80–95% before any pair math.
3. **Cell-list candidate pairs (O(near atoms), not O(N²)):** `spatial.cross_pairs` buckets the ligand's typed atoms into a uniform grid (cell = max atom-level cutoff, 4.0 Å); each near-AA atom queries its 3×3×3 neighboring cells. Ring↔ring, charge↔charge, charge↔ring feature pairs are enumerated directly (counts are tiny — ≤ ~20 rings, ≤ ~20 groups per scene; no spatial index needed at that granularity).
4. **Per-candidate constant-time tests:** each candidate pair runs its type's row from §3 — a handful of `vec3` operations (`math.sqrt/acos` on 3-tuples). No numpy anywhere.
5. **Canonical results:** records sorted by `(type, aa_object, aa_id, lig_id)`; binary presence computed downstream. Deterministic regardless of dict/iteration order.

**What the "no naive per-atom-pair loops" code audit checks:** no nested `for a in atoms: for b in atoms:` over the full atom sets anywhere in `detector.py`/`spatial.py`; candidate generation goes through `spatial.cross_pairs`; the brute-force path exists only in tests as the equivalence oracle.

### 5.3 Single source of truth for capability (generator ↔ detector agreement)

`chem_types.py` is the **only** place that knows "LYS side chain = cationic ammonium; PHE = one six-ring; SER = donor+acceptor O". The generator's AA-capability matrix (GEN-04 solvability, `can_form` in the level spec) and the hint's eligibility check (PLAY-05) must be **derived from these same tables + the same thresholds**, not from a parallel hand-written matrix. Recommended helper in `chem_types.py`: `residue_capabilities(resn, ligand_profile)` → set of interaction types that residue *could* form given a ligand-chemistry profile — used by generator (with the ligand's static profile from the manifest), hint (with the real ligand), and tests. This kills the hint/score disagreement class by construction.

### 5.4 Draft AA-capability matrix (UNVERIFIED-in-the-citation-sense — human approval required; standard residue chemistry, cross-checked against the sources' typing rules §2)

| Type | Capable AA side chains (draft) | Notes |
|---|---|---|
| H-bond | donors: SER THR TYR CYS TRP ASN GLN LYS ARG (HIS if protonated policy) · acceptors: ASP GLU ASN GLN HIS SER THR TYR CYS | **Recommendation: side-chain-only** — see §6 policy; backbone would make all 20 AAs H-bonders |
| Salt bridge | +: LYS ARG (HIS per §7.4) · −: ASP GLU | group-center test |
| π-stacking | PHE TYR HIS TRP | Trp = two rings |
| Cation-π | cation role: LYS ARG (HIS per policy) · ring role: PHE TYR HIS TRP | direction recorded |
| Hydrophobic | ALA VAL LEU ILE MET PHE TRP PRO | per §3 row 5 carbon rule |
| Halogen bond | acceptor role: ASP GLU SER THR TYR ASN GLN HIS CYS | donor always ligand-side |
| Metal coordination | donor role: ASP GLU HIS CYS TYR | only when ligand carries a metal (element list §3 row 7) |

---

## 6. Rotation/translation invariance (Q5)

**Why it holds by construction:** every criterion in §3 is a function of *relative* geometry only — distances, angles between vectors derived from coordinate differences, ring normals, projections. There is no absolute origin, axis, or camera dependence; the detector never reads PyMOL state. Given identical relative poses, results are bit-identical (modulo float associativity, which is fixed by a fixed evaluation order — hence canonical result ordering and a fixed atom iteration order derived from sorted keys).

**The one real risk is upstream, not in the detector:** matrix-blindness (PITFALLS 12) — if the movement model moves AAs via object matrices, stored coordinates are stale. The interface contract (§5.1) puts matrix composition in the caller. If both the smoke and the wizard use the same extraction helper, Phase-3 movement and Phase-6 reset cannot produce scores that disagree with the screen.

**Tests that pin it (all WSL, pure, scripted geometries — no PyMOL):**

1. **Rigid-transform invariance (property test, ≥100 random transforms):** build a scripted scene with known interactions; apply random rotation (normalized axis-angle) + random translation to *all* atoms; assert the interaction result sets (and metrics, to float tolerance ~1e-9) are identical.
2. **Permutation invariance:** same scene with atoms listed in shuffled order → identical canonical results (guards ordering bugs).
3. **Determinism:** same input twice → identical output (guards set/dict nondeterminism).
4. **Sensitivity controls (per type):** a scripted geometry at the criterion boundary moved 0.2 Å beyond cutoff / rotated past the angle window → interaction disappears; moved inside → appears. These double as the criteria-table tests.
5. **Cell-list equivalence:** `spatial.cross_pairs` output set == brute-force filtered pairs on randomized atom clouds (≥100 seeds) — proves pruning never misses a candidate (the correctness half of DETECT-05; the perf half is §8).

---

## 7. Chemistry policy (Q6 — must be documented in the detector module docstring, human-approved with the table)

1. **Waters:** excluded entirely. The cmd-tier extraction collects only game objects (grid AAs + ligand); demo structures are stripped of waters before bundling (roadmap Phase 8 note); no water-bridge type in v1 (EXT-01 deferred). PLIP precedent: all-water metal complexes are skipped even there [V detection.py].
2. **Alt-conf:** ligands come from SDF/MOL2 (no altlocs); grid AAs from bundled/fragment templates (no altlocs). Defensive policy in the pure layer: `apply_altloc_policy(atoms)` keeps alt `""`/`"A"` atoms and drops other altlocs, applied before typing, unit-tested. Precedent: PLIP ships `ALTLOC = False` (does not consider alternate locations) [V config.py]. Never the "best-scoring conformer" — nondeterministic and gameplay-irrelevant since game objects have no altlocs anyway.
3. **Hydrogens / protonation (the big one):** the §3 row-1 criterion needs real H positions. Policy proposal:
   - Ligands: SDF/MOL2 with explicit H + bond orders (spec GEN-02 already requires this).
   - AAs: materialized **with polar hydrogens** (cmd-tier `h_add` on AA objects, or bundled AA templates that already carry H — decision belongs to the materialization researcher; the *detector-side contract* fixed here: **donor typing is fail-closed — an O/N/S without an attached H is not a donor**).
   - Rationale for fail-closed: BINANA documents that guessing protonation without hydrogens degrades accuracy [V INTERACTIONS.md §Comments on protonation]; a guessed-H detector that fires wrong H-bonds is worse for a teaching game than one that misses marginal ones. The shared `chem_types` tables keep generator capability and detector typing consistent, so fail-closed cannot create unsolvable levels. Flagged as human decision (OQ-2), including the alternative (ProLIF's implicit-donor hybridization geometry) if the human prefers tolerance over strictness.
4. **HIS protonation:** default **neutral** (HIE-like: donor AND acceptor; not a salt-bridge cation; cation-π ring role only). Recorded deviation from BINANA ("always considered charged") and PLIP (charged group) — justified because we control templates; both sources' behavior exists precisely because *they* can't control it. HIP variant may be added later as a distinct residue entry (additive). Human-approve (OQ-3). Asp/Glu fixed −, Lys/Arg fixed + (standard pH set; both consistent with the sources' charged-group tables).
5. **Frames/states:** world/object coordinates, PyMOL **state 1 only**; game objects are single-state by design; multi-state ligand policy is a Phase-8 decision (roadmap) — the detector just documents "state the caller gave me". Camera frame never enters (PITFALLS 12).
6. **Metal gating:** metal coordination runs only if ≥1 ligand-side atom's element is in the adopted metal list (§3 row 7). Exposes `ligand_has_metal(atoms)` from `chem_types.py` so the generator/required-interaction selection can mirror the same gate (never require metal coordination on a metal-free ligand). Intra-ligand coordination is unrepresentable (cross-side enumeration only).
7. **Covalent exclusions:** atoms bonded to each other (intra-side) never pair; cross-side pairs at MIN_DIST 0.5 Å guard against coordinate duplicates. (Covalent-ligand interactions are out of scope per REQUIREMENTS.md.)

---

## 8. Performance & DETECT-05 verification (Q7)

### 8.1 Complexity

- Scene scale (worst case, from PITFALLS 15): 9×9 grid = 81 AAs × ~10–20 atoms ≈ up to ~1600 atoms + ligand ≤ ~200 atoms. Naive all-pairs ≈ 1.4 M pair evals ≈ seconds in pure 3.6 — the forbidden shape.
- With §5.2's pipeline: coarse prefilter leaves typically <10 near AAs (grid gap + spacing); cell-list queries over the small ligand index: ~(#near-AA atoms) × 27 cells × ~1–2 atoms/cell ≈ 10³–10⁴ candidate evals; feature pairs ≤ ~10². Expected detect time: **single-digit to low-tens of ms in pure Python 3.6**, comfortably inside the stated budget.
- Geometry *extraction* (`iterate_state` over game objects) is expected to dominate the smoke's wall time — which is why the smoke times extract and detect separately.

### 8.2 Budget numbers (traceable)

- **Detect pass < 100 ms** — stated in PITFALLS.md ("Detection-on-Confirm … should be < 100 ms at this scale"); adopted as the DETECT-05 headless assert.
- **Extract + detect < 1.0 s** headless wall (generous: Windows-side `iterate_state` + process startup noise; recorded, not just asserted).
- Phase-9 budgets (Generate < 30 s, pick/drag < 200 ms) unchanged and untouched here; detection-on-confirm is not on the per-drag path (ARCHITECTURE.md: detection runs on Confirm only).

### 8.3 Perf-smoke design (headless, cmd-only, count-asserted)

1. Load the **largest bundled molecule** (the Phase-2 bundled set's biggest ligand; if Phase-8 curation lands later, ship one provisional largest ligand now) and materialize a **max grid (9×9 = 81 AAs)**.
2. Script a placement that forms at least one interaction of each exercisable type.
3. Extract typed atom records + bond block (cmd tier, `iterate_state` with explicit `space`), time it.
4. Call the pure detector, time it; assert `detect_ms < 100` and `extract+detect < 1000`; print both for the record.
5. Assert result counts (≥1 per scripted type) — count-asserted per the standing smoke discipline.
6. Record `DETECTOR_VERSION` in the generated spec (already enforced by the Phase-1 gate on read).

### 8.4 WSL-side perf guard (unit, loose)

A synthetic worst-case scene (81 AAs + 200-atom ligand, all crammed within cutoff) asserted < **2 s** wall under python3.6 — a regression guard against accidental O(N²), not the budget (the budget lives in the headless smoke; WSL 3.6 is slower than the Windows env's Python and CI-noisy on tight bounds). The correctness half of DETECT-05 is the cell-list equivalence test (§6.5), which is deterministic and fast.

---

## 9. Failure modes / pitfalls for the planner (Q8)

From PITFALLS.md (topics *detection-engine*, *detection chemistry/frames*, *performance*, *atom identity*) plus this research:

1. **Matrix blindness** (PITFALLS 12): detector consumes composed world coordinates; contract in §5.1; shared extraction helper across smoke/wizard; Phase-4 spike decides the movement model — detector design must not assume coordinates-are-stored-coordinates.
2. **Camera-frame leak** (PITFALLS 12): `cmd.translate` defaults to camera=1; extraction path must pass world-frame values; the detector itself is frame-free by construction.
3. **Missing-H fail-closed vs unsolvability**: if materialization ever ships heavy-atom-only AAs, donor typing silently empties → required H-bonds become unmakeable → generator/detector still *agree* (shared tables) but levels rely on non-H-bond interactions. Early warning: generator invariant tests must include at least one H-bond-requiring seed.
4. **His/protonation divergence** from the sources (§7.4): documented, human-approved, or the capability matrix and the sources' tables will appear to contradict.
5. **Hydrophobic over-firing**: 4.0 Å C-C is permissive; in "any"-mode levels hydrophobic makes success near-trivial. Flag for the generator researcher (OQ-5): e.g., exclude hydrophobic from `any`-mode requirement sampling (policy, not detection change).
6. **Ring-perception edge cases**: trust bond orders first (§3 row 8); Trp two rings; His five-ring; planarity fallback threshold (15°) only for defensive paths. MOL2 aromatic bond types vs SDF kekulé — normalize in the bond-block reader (cmd tier; interface noted).
7. **Order/dict nondeterminism**: canonical result ordering + fixed iteration order (§5.2.5); pinned by permutation/determinism tests.
8. **Detector change invalidates generated/exported specs** (PITFALLS 11): `DETECTOR_VERSION` bump policy (§3); the exact-match gate already refuses stale games — the *policy* (when to bump: thresholds OR typing semantics) must be written into the threshold doc.
9. **Purity-gate housekeeping — whitelist gap:** `tests/test_purity.py::ALLOWED_STDLIB` currently lacks **`itertools`** (and possibly `heapq`/`operator`). The detector legitimately wants `itertools.product`. Adding roots to the whitelist is a deliberate, reviewable gate change — plan it explicitly, don't discover it as a red suite. New modules must be added to `PURE_MODULES` (standing gate #2).
10. **Perf test flakiness**: keep WSL perf asserts loose (§8.4); real budget headless (§8.3). Never assert sub-100 ms under python3.6 in a unit test.
11. **`cmd.get_model` trap** (PITFALLS 15): extraction uses `iterate_state` with narrow selections, never `get_model` on whole objects.
12. **salt-bridge group-center vs atom-level mismatch** if implementation drifts: charge-center math must use the *group* representative points (BINANA table), not first-atom coordinates — test with a carboxylate whose first O is far from the midpoint.

---

## 10. Open questions for the planner (decision points, with recommendations)

1. **OQ-1 (GATE, critical path):** Threshold-table approval — the §3 draft goes to the human as the phase's first plan. Everything downstream consumes it.
2. **OQ-2:** Explicit-H-on-AAs materialization (h_add vs bundled H-bearing AA templates) — detector-side contract fixed (fail-closed typing, §7.3); the materialization mechanism is the cmd-tier researcher's decision but **must land in Phase 2/3 before H-bond unit tests can run against real data** (scripted geometries don't need it).
3. **OQ-3:** HIS neutral-default policy (§7.4) — human approval; affects capability matrix, cation-π/salt-bridge rows.
4. **OQ-4:** Keep PLIP's ligand-side-only tertiary-amine anti-artifact rule (asymmetric between sides) or symmetrize it (apply to LYS NH3+ too, using the same N-substituent-plane test)? Recommendation: keep PLIP's asymmetric form for v1 (verified behavior, LYS's charged N geometry is well-constrained by its own chain anyway); revisit only if playtesting shows through-side false positives.
5. **OQ-5:** Hydrophobic in "any"-mode requirement sampling (generator policy) — recommend excluding or down-weighting; detection semantics unchanged.
6. **OQ-6:** Side-chain-only capability semantics (§6 policy recommendation) — deviates from all three sources (which are analysis tools); pedagogy call for the human.
7. **OQ-7:** Metal element list breadth (v1 core set §3 row 7 vs full union of the three verified lists).
8. **OQ-8:** Whether the debrief (Phase 6) ever wants sub-type metrics (P vs T stacking, direction fields) — results already carry them as metrics; no extra work, just a UI decision later.

---

## 11. Sources

### Primary — fetched 2026-09-06 (HIGH confidence)

- PLIP repo `pharmai/plip` @ master (v3.0.1): `plip/basic/config.py` (threshold table, METAL_IONS, ALTLOC default), `plip/structure/detection.py` (hbonds/pistacking/pication/saltbridge/halogen/metal_complexation mechanics), repo tree via GitHub contents API (file paths verified). DOI in `config.py` + repo description: 10.1093/nar/gkaf361.
- ProLIF repo `chemosim-lab/ProLIF` @ master (2.2.x): `prolif/interactions/interactions.py` (all seven relevant class defaults + SMARTS), `CITATION.cff` (doi:10.1186/s13321-021-00548-6), repo tree.
- BINANA repo `durrantlab/binana` @ main (2.1): `INTERACTIONS.md` (algorithms + parameter table + charge-group definitions + protonation notes), `python/binana/interactions/default_params.py` (values cross-check), `python/binana/interactions/_hydrogen_halogen_bonds.py` (angle semantics), `README.md` (doi:10.1016/j.jmgm.2011.01.004, Apache-2.0).

### Secondary — previously verified in this repo's research (HIGH)

- PLIP official help page (interaction list, two-stage algorithm, dedup rules, hydrophobic definition, group definitions) — fetched 2026-09-05, recorded in `.planning/research/FEATURES.md`.
- Local repo constraints: `AGENTS.md` standing gates; `tests/test_purity.py` (Gate A/A2/B/D, `PURE_MODULES`, `ALLOWED_STDLIB`); `aamatch/level_spec.py` (DETECTOR_VERSION exact-match gate); `aamatch/persistence.py` (container discipline); `.planning/research/{PITFALLS,ARCHITECTURE,STACK}.md`.

### Tertiary / not fetched (explicitly UNVERIFIED — do not cite numbers from these)

- PLIP `plip/structure/preparation.py` (path verified in tree; contains protein charge-group atom-name lists & hydrophobic/acceptor classification) — **NEEDS HUMAN VERIFICATION at the gate if the adopted table cites PLIP's typing atom-lists directly** (the help page's conceptual definitions were verified 2026-09-05).
- BINANA `python/binana/interactions/_metal_coordination.py` (full metal list for coordination; the salt-bridge metal-cation name list IS verified in INTERACTIONS.md) — fetch at implementation time if a broader metal list is adopted.
- BINANA 2011 paper body (we cite the repo's docs/parameters, which is what BINANA itself publishes as current).

---

## Metadata

**Confidence breakdown:**
- Published threshold values: **HIGH** — every number read today from official repo files; BINANA cross-checked in two files; angle convention resolved from code, not prose.
- Architecture proposal: **HIGH** for fit with existing gates (pattern proven by Phase-1 modules); **MEDIUM** for the exact module granularity (planner may merge `spatial` into `detector` — the equivalence test must survive any merge).
- In-house resolutions & capability matrix: **proposals** — valid only after the DETECT-03 human gate.
- Perf estimates: **MEDIUM** — complexity math is sound; absolute ms figures need the headless smoke to confirm (that's what DETECT-05 is for).

**Research date:** 2026-09-06
**Valid until:** ~2026-10-06 for the threshold values (PLIP/ProLIF/BINANA are stable projects; PLIP master moved 2026-07; re-verify if the gate slips past a month). Interfaces/policies: valid until Phase 2 planning completes.

---
*Research for: AA-match Phase 2 (Headless Game Engine) — detection engine scope*
*Researched: 2026-09-06*
