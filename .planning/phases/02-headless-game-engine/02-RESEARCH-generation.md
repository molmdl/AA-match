# Phase 2 Research — GENERATION (seeded levels, solvability, grid layout)

**Researched:** 2026-09-06
**Scope:** GEN-01 … GEN-05 generator side only — capability table, solvability-by-construction, grid geometry, difficulty expression, RNG/serialization, required-set derivation (interaction modes), generator-side protonation selection, ≥100-seed invariant strategy, emit shape for the materializer/detector.
**Out of scope (other researchers):** detection criteria math; cmd-tier materialization/plumbing. This file notes what data the generator emits so those phases can consume it.
**Confidence:** HIGH for everything grounded in the local Phase-1 code (`level_spec.py`, `setup_state.py`, `test_purity.py`) and the verified reference-tool sources fetched 2026-09-06. The **amino-acid capability table is a DRAFT flagged NEEDS HUMAN VERIFICATION** (project truthfulness rule) — every row cites its source; three documented cross-tool disagreements are surfaced as explicit in-house resolutions.

---

## 0. Executive summary

The generator is a **pure, seeded, always-solvable level constructor**: it consumes a validated setup state + demo-manifest/upload references + ligand bounds (fed IN by the cmd tier — the proven prior-art data-in/decisions-out pattern), and emits a complete level-spec payload that *fully determines* the level (slot assignments AND grid positions serialized — nothing is recomputed from the seed at replay time). Solvability is by construction: per required interaction unit, one dedicated capable AA slot is allocated from the capability table (which must be a **shared module** with the detector, per DETECT-04); remaining slots are distractors. Grid positions are deterministic pure math (flat N×N plane beyond a gap from the ligand's bounding sphere), so the materializer only translates objects — no geometry decisions at materialize time.

Three decisions dominate the planning risk, and all three are **coordination gates with the detector researcher, not open-ended research**:
1. **Backbone participation in H-bonds.** At atom level (ProLIF/PLIP/BINANA), every capped AA has a backbone NH donor and C=O acceptor → "every AA can H-bond" — which trivializes solvability, hint, and difficulty for `h_bond`. Recommendation: capability table is **side-chain-only**, and the detector's H-bond rules must be restricted to side-chain atoms for the table to be true. Needs human + detector sign-off.
2. **Hydrophobic typing must be residue-name-based on the AA side.** ProLIF/BINANA/PLIP all define hydrophobic at atom level (carbon-only neighborhoods), which makes almost every AA partially "hydrophobic" — useless pedagogically. The capability table uses the classic residue set; the detector must classify AA-side hydrophobic contacts by residue name (exactly as BINANA already treats protein aromatics by residue name).
3. **Salt-bridge and cation-π polarity.** Capability is not a fixed AA↔type matrix for these: salt-bridge capability depends on the *ligand's* charge sign (Asp/Glu match cationic ligands; Lys/Arg/His match anionic ligands), and cation-π has two directions (ProLIF: `CationPi` vs `PiCation`). The required-set feasibility check and the detector must agree on direction semantics.

**Primary recommendation:** build one new pure module `aamatch/capability.py` (AA capability table + ligand support predicates, stdlib-only) *before or together with* the detector, consumed by both the generator (solvability) and the detector (typing agreement) and later by Hint (PLAY-05); the generator itself is `aamatch/generator.py` (pure), fed by a thin cmd-tier data adapter. Sequence the capability-table human review as an explicit [GATE] task alongside the threshold-table gate.

---

## 1. Verified facts (foundation this research builds on)

### 1.1 Local code contracts (HIGH — read directly from the repo, 2026-09-06)

| Fact | Source |
|------|--------|
| 7 interaction types, canonical order: `h_bond, salt_bridge, pi_stacking, cation_pi, hydrophobic, halogen, metal` | `aamatch/setup_state.py:40-41` (`INTERACTION_TYPES`) |
| 3 modes: `exclusive, block_exclusive, unset`; default `unset` | `aamatch/setup_state.py:44`, `:60` |
| Setup clamps: molecules 2/1/10; difficulty **3/1/10** (cap 10 human-amended at 01-09, frozen; changing = version-bump event) | `aamatch/setup_state.py:46-50` |
| `allowed_interactions` always serialized (canonical order), even in `unset` mode; "mode governs USE (decided Phase 2/4)" | `aamatch/setup_state.py:24-26`, `:134-135` |
| Level-spec payload shape is RESERVED (detector_version/format_version/seed/levels/difficulty/molecules/ligand/required/grid/slots incl. `slot_id, row, col, aa, role, can_form, grid_pose{position}`) | `aamatch/level_spec.py:9-35` (docstring) |
| `DETECTOR_VERSION = 'det-1'`; exact-match gate both directions ("stale or newer … regenerate"); `LEVEL_SPEC_VERSION = 1` refuse-newer/accept-older | `aamatch/level_spec.py:60-61`, `:111-121` |
| `seed` must be present AND a real int; bools refused | `aamatch/level_spec.py:64-66`, `:128-135` |
| `can_form` members are NOT validated against setup_state's enum — independent schemas; **Phase-2 generator guarantees consistency** | `aamatch/level_spec.py:52-55` |
| `slot_id` uniqueness enforced PER MOLECULE (the generator's global-allocation invariant); unhashable slot_id refused | `aamatch/level_spec.py:173-214` |
| Parse is passthrough (unknown keys preserved at every nesting level) → generator may add additive fields without schema breakage | `aamatch/level_spec.py:46-48` + 01-06-SUMMARY |
| Container: `{"magic": "AAMATCH", "version": 1, "kind": "level_spec", "data": …}`; `make_container(kind)` refuses unknown kinds | `aamatch/persistence.py:34-57` |
| JSON written with `sort_keys=True, allow_nan=False` (NaN/Infinity refused — grid float math must never produce NaN) | `aamatch/persistence.py:90-97` |
| Purity gate: `PURE_MODULES = ['setup_state', 'level_spec', 'persistence', 'backup', 'paths']`; new pure modules MUST be appended there. `ALLOWED_STDLIB` whitelist contains `math`, `random`, `copy`, `collections`, `re`… but **NOT `itertools`, NOT `struct`, NOT `string`** | `tests/test_purity.py:64-75` |
| Prior-art generator pattern: "cmd-coupled caller feeds data (bounding box, neighbor pool) IN and gets pure geometry/selection decisions OUT" — no pymol import in the generator | `.planning/research/ARCHITECTURE.md:64` (v1 `generators.py` docstring) |

### 1.2 Interaction-typing facts from reference tools (HIGH — official sources fetched 2026-09-06)

These establish *atom/group typing rules* (not thresholds). The AA-match in-house table adopts *concepts*, not values; every numeric threshold remains a separate human gate (DETECT-03, owned by the detector researcher). The generator needs **no thresholds at all** — only boolean capability.

**BINANA 2.1 `INTERACTIONS.md`** (fetched https://raw.githubusercontent.com/durrantlab/binana/main/INTERACTIONS.md, 2026-09-06):
- Hydrogen bonds: "hydroxyl, amine, and thiol groups" act as donors; "Oxygen, nitrogen, and sulfur atoms can act as hydrogen-bond acceptors."
- Salt bridges (protein side, by standardized atom names): Lys — amine N; Arg — guanidino (midpoint of the two terminal N); **"Histidine is always considered charged"** (midpoint of the two ring N); Asp/Glu — carboxylate (midpoint of the two O).
- Aromatic rings (protein): "Phenylalanine, tyrosine, and histidine all have aromatic rings. Tryptophan is assigned two aromatic rings." (Protein aromatics are identified **by residue name** — a precedent for residue-name-based protein-side typing.)
- Cation-π: each charged-group representative point is compared to each aromatic-ring center; charge projected onto ring disk (either partner may hold the cation — the check is symmetric over "each of the representative coordinates" vs "each of the center points").
- Halogen bonds: donors O-X/N-X/S-X/C–X (X ∈ I, Br, Cl, **F**); acceptors O/N/S. (No protein/ligand side restriction in BINANA.)
- Metal coordination: "whenever a N, O, Cl, F, Br, I, or S is located near a metal cation" — distance-only, with documented rationale (many geometries; L–M–L angles deviate; vacancies).
- Protonation: recommends input with polar hydrogens + charges (PDBQT); warns results degrade when protonation must be guessed from geometry. (Independent support for GEN-02's explicit-protonation requirement.)

**PLIP help page** (fetched https://plip-tool.biotec.tu-dresden.de/plip-web/plip/help, 2026-09-06):
- Charged groups (proteins): "positive charges are attributed to the side chain nitrogens of **Arginine, Histidine and Lysine**. Negative charges are assigned to the carboxyl groups in **Aspartic Acid and Glutamic Acid**." (Ligands: quaternary/tertiary ammonium, sulfonium, guanidine; phosphate, sulfonate, sulfonic acid, carboxylate.)
- Halogen bonds: "halogen bond **donors are searched for only in ligands**. All fluorine, chlorine, bromide or iodine atoms connected to a carbon atom qualify as donors. Halogen bond **acceptors in proteins** are all carbon, phosphor or sulphur atoms connected to oxygen, phosphor, nitrogen or sulfur."
- Metal complexes — protein-side interacting groups, explicitly listed: "sidechains of **cystein (S), histidine (N), asparagine, glutamic acid, serin, threonin, and tyrosin (all O), as well as all main chain oxygens**." Note: **aspartate and glutamine are absent from PLIP's list** (documented discrepancy vs BINANA's generic N/O/S rule — see §2 flags).
- Hydrophobic atoms: "a carbon … with only carbon or hydrogen atoms as neighbours" (atom-level).
- PLIP's own published threshold table exists on this page (HBOND_DIST_MAX etc.) — values verified accessible, **not adopted here** (human gate).

**ProLIF 2.2.x `interactions/interactions.py`** (fetched https://raw.githubusercontent.com/chemosim-lab/ProLIF/master/prolif/interactions/interactions.py, 2026-09-06):
- `Hydrophobic`: atom-level SMARTS (aromatic C, aliphatic C not attached to N/O/F, Br/I, divalent S) — **not residue-based**; distance default 4.5 Å.
- `HBAcceptor`/`HBDonor`: donor = `[O,S,N;+0]-[H]`, ammonium N+ `[Nv4+1]`, protonated His `[n+]c[nH]`; acceptor = neutral/aromatic N, O, aromatic O, C-F. **v2.2.1 note: "Fixed to explicitly exclude backbone nitrogens from being considered as acceptors"** — i.e., ProLIF *does* count backbone atoms in H-bonding generally.
- ProLIF's own tutorial output (same docs page) shows `VAL201.A … HBAcceptor` — valine has no side-chain donor/acceptor, so **that hit is the backbone carbonyl**: direct evidence that atom-level typing makes backbone H-bonding universal for capped AAs (see Decision D1).
- `XBAcceptor/XBDonor`: donor `[#6,#7,Si,F,Cl,Br,I]-[Cl,Br,I,At]` — **excludes C–F as a halogen-bond donor** (contradicts PLIP, which includes F); acceptor `[#7,#8,P,S,Se,Te,a;!+{1-}]!#[*]`.
- `Cationic/Anionic`: cation = net positive charge or amidine/guanidine resonance; anion = net negative or `O=[C,S,P]-[O-]`; **directional pairs** — `Anionic` (ligand anion vs residue cation) and `Cationic` (ligand cation vs residue anion) are inverse roles of each other.
- `CationPi` vs `PiCation`: separate classes per direction (ligand-cation→residue-ring vs ligand-ring→residue-cation).
- `MetalDonor`: metal list `[Ca,Cd,Co,Cu,Fe,Mg,Mn,Ni,Zn]`; chelating atoms = O, qualified N (excludes amide N, **N attached to aromatic atoms** — which excludes His ring N — and quaternary N), or anionic atoms. Note: **ProLIF's default excludes His and neutral Cys S from metal chelation**, contradicting PLIP's explicit Cys(S)/His(N) list and BINANA's N/O/S rule (see §2 flags).
- `PiStacking` = FaceToFace (distance 5.5 Å, plane angle 0–35°) + EdgeToFace (6.5 Å, 50–90°, intersect radius 1.5 Å) — v1 AA-match folds both into one `pi_stacking` category (per REQUIREMENTS DETECT-01).

**Cross-tool disagreement summary (generator-relevant):** C–F halogen donor (PLIP yes / ProLIF no); His + Cys as metal chelators (PLIP+BINANA yes / ProLIF default no); Asp+Gln as metal chelators (BINANA yes / PLIP's list omits them); Met thioether S as H-bond acceptor (BINANA yes / ProLIF no); His charged-ness (BINANA "always charged" / PLIP attributes + to His side-chain N / physiologically only partially protonated at pH 7.4). These are exactly the "in-house resolutions of disagreements" DETECT-03 mandates recording — the capability table must be frozen **with** the threshold doc, not before.

### 1.3 RNG reproducibility facts (HIGH — Python 3.6.15 official docs, fetched 2026-09-06)

From https://docs.python.org/3.6/library/random.html ("Notes on Reproducibility"):
> "Most of the random module's algorithms and seeding functions are subject to change across Python versions, but two aspects are guaranteed not to change: If a new seeding method is added, then a backward compatible seeder will be offered. **The generator's random() method will continue to produce the same sequence when the compatible seeder is given the same seed.**"

Consequences (design-binding):
- **Same interpreter + same seed → identical sequences** for `random.Random(seed).randint/choice/sample/shuffle` (they consume the same Mersenne Twister stream). Guaranteed across runs and machines *on the same Python version*.
- **Cross-Python-version drift is formally possible** for everything except `random()`. This is acceptable because **the spec never re-derives the level from the seed** (see §6): all slot assignments and positions are serialized. The seed's role is provenance + same-version regeneration.
- `random.sample` accepts a set in 3.6, but set iteration order is NOT stable across processes for strings (PYTHONHASHSEED randomization) — **never sample from a set; sample from a `sorted(list)`**.
- Never use `hash()` or set/frozenset iteration order for anything order-dependent (CPython 3.6 dict preserves insertion order, so dict iteration over a *constructed-in-fixed-order* dict is stable; sets are not).

---

## 2. The amino-acid capability table (DRAFT — NEEDS HUMAN VERIFICATION)

### 2.1 How to read this

The table is the **game's own in-house table** (like the threshold table, gated by the human-approval protocol). Per-cell status marks:
- **[V-SRC]** — the classification follows deductively from a verified atom/group-typing rule in a fetched source (BINANA/PLIP/ProLIF) applied to the standard side-chain structure (textbook chemistry). Strongest available footing short of human approval.
- **[RESOLVE]** — documented cross-tool disagreement; AA-match must record an explicit in-house resolution (this is the DETECT-03 "in-house resolutions of disagreements" mechanism, applied to typing instead of thresholds).
- **[HUMAN]** — pedagogical/in-house choice with no single authoritative tool rule; must be human-approved.

Rows = the 20 standard AAs. Columns = the 7 `INTERACTION_TYPES`. Cell = what the AA side chain can contribute **on the AA side** (the ligand side has its own support predicates, §2.3). Backbone is EXCLUDED by policy D1 below (recommendation; must be confirmed).

### 2.2 Policy decisions the table depends on (coordination gates)

**D1 — Backbone excluded from capability (RECOMMENDED; HUMAN + detector sign-off).**
Verified: ProLIF counts backbone donors/acceptors (its tutorial shows VAL as HBAcceptor — a backbone hit; the v2.2.1 changelog explicitly discusses backbone-N acceptor handling), PLIP metal complexes include "all main chain oxygens", BINANA tallies backbone vs side-chain separately. If backbone H-bonds count, EVERY capped AA is h_bond-capable → `h_bond` solvability is trivial, the hint lights up the whole grid, and the "which side chains do what" pedagogy collapses. **Recommendation: the v1 capability table is side-chain-only, and the detector must restrict H-bond donor/acceptor matching to side-chain atoms of grid AAs** (it may still use the ligand's full chemistry). Cite both sides in the gate doc; record the human's call. *This single decision changes the table more than any chemistry claim.*

**D2 — Capped amino acids, standard protonation per AA (RECOMMENDED; HUMAN).**
"capped amino acids" (GEN-03) = neutral termini (e.g., acetyl + N-methylamide) so grid AAs carry no terminal charges; each AA object bundles the AA's *standard* ionization at physiological pH: Asp−, Glu−, Lys+, Arg+, His neutral (HIE/HID tautomer — pick ONE tautomer for the bundled file; typically HIE, but the choice belongs to the data manifest, Phase 8 approval). Under D2, HIS is NOT salt-bridge-capable as a cation *unless* the bundled file is HIP (protonated) — see HIS row flags. Protonation variants of AAs are an additive schema extension (`slot.protonation`), reserved but unused in v1.

**D3 — salt_bridge and cation_pi are polarity-aware (design, follows from sources).**
A "capable AA" for salt_bridge depends on the ligand's charge sign: ligand cationic → AA must be anionic (Asp/Glu); ligand anionic → AA must be cationic (Lys/Arg/[His if HIP]). The capability API is therefore `aa_capable(aa, itype, ligand_profile)` — not a bare two-column table. Same for cation_pi direction (see D4).

**D4 — cation_pi direction (RESOLVE; HUMAN).** ProLIF ships both directions (`CationPi`, `PiCation`); BINANA checks both symmetrically; PLIP's rule is written from the positive-charge side but pairs "each positive charge with each aromatic ring" (both sides possible). Options for AA-match v1: (a) count either direction (AA-cation over ligand ring **or** AA-ring under ligand cation); (b) ligand-ring-only (AA cation required). Recommendation: **(a) either direction**, since demo ligands with cations are as common as aromatic ones and it maximizes teachable moments; the detector must then report cation_pi regardless of which side holds the cation. Record the decision in the typing doc.

### 2.3 The table

| AA | h_bond (side chain) | salt_bridge | pi_stacking | cation_pi | hydrophobic | halogen (acceptor) | metal (chelator) |
|----|---------------------|-------------|-------------|-----------|-------------|--------------------|------------------|
| Ala | — | — | — | — | Y [V-SRC: atom rule; residue set HUMAN] | — | — |
| Arg | donor (guanidinium NH1/NH2) [V-SRC: BINANA amine-donor + PLIP charged-N] | **cation** [V-SRC: PLIP+BINANA guanidino] | — | cation (over ligand ring) [V-SRC] | — | — | — |
| Asn | donor (ND2 amine) + acceptor (OD1) [V-SRC] | — | — | — | — | Y (O, N) [V-SRC: PLIP XB acceptor rule] | Y (O) [V-SRC: PLIP metal list "asparagine… (all O)"] |
| Asp | — (acceptor only when protonated COOH — not under D2) | **anion** (carboxylate) [V-SRC: PLIP+BINANA] | — | — | — | Y (O) [V-SRC] | **Y (O) [RESOLVE: PLIP's metal list omits Asp; BINANA's N/O/S rule includes it — recommend INCLUDE, carboxylates are canonical metal ligands]** |
| Cys | donor (thiol SH) [V-SRC: BINANA "thiol groups" donors] | — | — | — | borderline [HUMAN: KD 1982 ranks Cys among the more hydrophobic side chains (hydropathy +2.5 > Ala); pedagogically usually taught as polar-reactive — recommend EXCLUDE from the pedagogical set, note the tension] | Y (S) [V-SRC] | **Y (S) [RESOLVE: PLIP lists Cys(S) explicitly; ProLIF's default SMARTS excludes neutral S — recommend INCLUDE per PLIP+BINANA]** |
| Gln | donor (NE2 amine) + acceptor (OE1) [V-SRC] | — | — | — | — | Y (O, N) [V-SRC] | **Y (O) [RESOLVE: PLIP's list omits Gln; BINANA N/O/S includes — recommend INCLUDE]** |
| Glu | — (under D2) | **anion** [V-SRC] | — | — | — | Y (O) [V-SRC] | **Y (O) [RESOLVE: PLIP includes "glutamic acid (O)" — yes; consistent]** |
| Gly | — | — | — | — | — [V-SRC: no side chain; ProLIF atom rule excludes the α-C (attached to N)] | — | — |
| His | donor + acceptor (ring N–H / ring N; tautomer-dependent) [V-SRC: BINANA ring-N midpoint; ProLIF `[n+]c[nH]` donor] | **cation when protonated (HIP) [RESOLVE: BINANA treats His as ALWAYS charged; PLIP attributes + to His side-chain N; physiologically ~10% protonated at pH 7.4 — under D2 (neutral His bundled), recommend: His is NOT a salt-bridge cation in v1, marked capable only if a HIP file is later curated]** | Y (one ring) [V-SRC: BINANA protein aromatics] | both directions: ring AND (if HIP) cation [V-SRC + D4] | — | Y (ring N) [V-SRC] | Y (N) [RESOLVE: PLIP lists His(N); ProLIF default excludes aromatic-attached N — recommend INCLUDE, His is the canonical Zn ligand] |
| Ile | — | — | — | — | Y [HUMAN, V-SRC-consistent] | — | — |
| Leu | — | — | — | — | Y [HUMAN, V-SRC-consistent] | — | — |
| Lys | donor (NZ amine, charged) [V-SRC] | **cation** (NH3+) [V-SRC] | — | cation [V-SRC] | — | — | — |
| Met | acceptor (thioether S) [RESOLVE: BINANA "S atoms can act as acceptors" → yes; ProLIF's acceptor SMARTS has no aliphatic S → no — recommend INCLUDE, mark weak] | — | — | — | Y [HUMAN, V-SRC-consistent] | Y (S) [V-SRC: PLIP acceptor rule includes S] | — (not in PLIP's metal list; BINANA's S-rule would allow — recommend EXCLUDE, thioether coordination is niche) |
| Phe | — | — | Y (one ring) [V-SRC] | ring (under ligand cation) [V-SRC + D4] | Y [HUMAN, V-SRC-consistent] | — | — |
| Pro | — [V-SRC: no side-chain N–H (ring N is the backbone N)] | — | — | — | Y [HUMAN, V-SRC-consistent] | — | — |
| Ser | donor + acceptor (OG) [V-SRC] | — | — | — | — | Y (O) [V-SRC] | Y (O) [V-SRC: PLIP "serin… (all O)"] |
| Thr | donor + acceptor (OG1) [V-SRC] | — | — | — | — | Y (O) [V-SRC] | Y (O) [V-SRC] |
| Trp | donor (NE1 indole) [V-SRC] | — | Y (**two rings**) [V-SRC: BINANA] | ring [V-SRC + D4] | Y [HUMAN, V-SRC-consistent] | — | — |
| Tyr | donor + acceptor (OH) [V-SRC] | — | Y (one ring) [V-SRC] | ring [V-SRC + D4] | — [HUMAN: ring is apolar but OH dominates pedagogy; PLIP/BINANA atom rules would partially count it — recommend EXCLUDE to keep the taught set clean] | Y (O) [V-SRC] | Y (O) [V-SRC: PLIP "tyrosin (O)"] |
| Val | — | — | — | — | Y [HUMAN, V-SRC-consistent] | — | — |

**Pedagogical hydrophobic set (proposed):** `ALA, VAL, LEU, ILE, PRO, PHE, MET, TRP` — Cys/Tyr/Gly/charged/polar AAs excluded. Citation for the classification: Kyte & Doolittle 1982, "A simple method for displaying the hydropathic character of a protein", *J Mol Biol* 157(1):105–132, doi:10.1016/0022-2836(82)90515-0, PMID 7108955 (canonical side-chain hydropathy scale; citation verified via the Wikipedia *Hydrophobicity scales* article and its reference list, 2026-09-06). **[HUMAN]** — the exact membership is the single most pedagogy-visible row of the table and must be explicitly approved; the Wimley–White whole-residue scale (verified table on the same Wikipedia page) notably ranks Ala/Trp differently because it includes backbone — reinforcing that the *choice of scale* is an in-house pedagogical decision to be recorded, not a fact to be asserted.

**Counts per type (side-chain-only policy, under the recommendations above):** h_bond 10 AAs (Arg, Asn, Cys, Gln, His, Lys, Ser, Thr, Trp, Tyr + Met-acceptor = 11); salt_bridge 4 (cationic Lys/Arg [+His-conditional], anionic Asp/Glu); pi_stacking 4 (Phe, Tyr, His, Trp); cation_pi 4 rings + 2–3 cations = 6–7; hydrophobic 8; halogen-acceptor 9 (Arg? no — Asn, Asp, Cys, Gln, Glu, His, Ser, Thr, Tyr); metal 7–8 (Cys, His, Asn, Gln, Asp, Glu, Ser, Thr, Tyr = 9 under recommendations). Every type has ≥ 4 capable AAs → solvability sampling never starves at any grid size. Assert this "≥2 capable AAs per type" as a permanent invariant test.

### 2.4 Ligand-side support predicates (the other half of feasibility)

| Type | Ligand must have | Source basis |
|------|------------------|--------------|
| h_bond | ≥1 H-bond donor **or** ≥1 acceptor atom (AA side provides the complement) | BINANA donor/acceptor group rules [V-SRC] |
| salt_bridge | ≥1 charged group; polarity selects the AA subset (D3) | PLIP/BINANA charged-group lists [V-SRC] |
| pi_stacking | ≥1 aromatic ring (5/6-membered; planarity fallback per PLIP) | BINANA ring perception; PLIP SSSR+planarity [V-SRC] |
| cation_pi | ≥1 aromatic ring **or** ≥1 cationic group (per D4 direction policy) | ProLIF directional classes; BINANA symmetric check [V-SRC] |
| hydrophobic | ≥1 hydrophobic atom per the detector's AA-side-consistent typing (organic ligands: always true) | BINANA/PLIP hydrophobic atom rules [V-SRC] |
| halogen | ≥1 C–X donor (X = Cl, Br, I; **C–F per in-house resolution [RESOLVE: PLIP includes F, ProLIF excludes — recommend EXCLUDE C–F, halogen bonding to F is weak/disputed and ProLIF's Auffinger-based pattern is the stricter precedent]**) | PLIP "donors only in ligands" [V-SRC] |
| metal | ≥1 metal atom from the in-house metal list [RESOLVE: PLIP ">50 species" vs ProLIF 10-metal list vs BINANA 8-name list — recommend adopting a short explicit list (e.g., the union of ProLIF's `[Ca,Cd,Co,Cu,Fe,Mg,Mn,Ni,Zn]` + BINANA's MG/MN/RH/ZN/FE/BI/AS/AG), recorded in the typing doc] | all three [V-SRC + RESOLVE] |

These predicates live in the **shared capability module** (§5) and are the exact functions the generator calls for required-set feasibility (§7) — the detector consumes the same atom-typing tables so "capable" and "detected" cannot drift (DETECT-04).

---

## 3. Proposed architecture for generation

### 3.1 Modules

```
aamatch/
├── capability.py      # NEW PURE: AA_CAPABILITIES table, aa_capable(), ligand_support(),
│                      #   atom/group typing tables shared with the detector + Hint
├── generator.py       # NEW PURE: generate() — required-set derivation, slot allocation,
│                      #   grid geometry, level-spec payload assembly. stdlib only.
└── level_spec.py      # EXISTS: constants + parse gates (generator imports DETECTOR_VERSION/
                       #   LEVEL_SPEC_VERSION from here — pure<-pure, add to test_purity targets)
tests/
└── test_purity.py     # MODIFY: append 'capability', 'generator' to PURE_MODULES
```

Purity notes (enforced by `tests/test_purity.py` as it stands):
- `random`, `math`, `copy`, `collections` are whitelisted; **`itertools` is NOT** — do not import it in pure modules (or, if genuinely needed, extend `ALLOWED_STDLIB` as an explicit reviewed change — stdlib-only so it cannot break Gate B, but it is a whitelist edit and should be a conscious plan step).
- No file I/O in the generator: manifest parsing happens in the cmd tier (or a pure manifest module later); the generator receives already-resolved Python data.
- Generator must not import `setup_state` enums? It MAY — `random`/`copy`-style pure<-pure imports are allowed (persistence already imports setup_state). Import `INTERACTION_TYPES`/`INTERACTION_MODES` from `setup_state` and version constants from `level_spec` so the enums have ONE home.

### 3.2 Generator API (data in, decisions out — prior-art pattern)

```python
def generate(seed, setup, candidates, ligand_data, difficulty_levels):
    """Pure. Returns the level-spec payload dict (the container 'data').
    seed          : int (real int; caller passes the master seed)
    setup         : validated setup_state dict (mode, allowed_interactions, molecules_per_level)
    candidates    : list of molecule references, ALREADY sorted deterministically:
                    [{'set_id', 'entry_id', 'file', 'sha256', 'protonation',
                      'provenance', 'heavy_atoms': int, 'size_class': str}, ...]
                    (the cmd tier/manifest layer resolves the demo set or upload;
                     protonation = chosen from the manifest's recorded options)
    ligand_data   : per selected molecule, geometry summary fed IN by the cmd tier:
                    {'centroid': (x, y, z), 'radius': r}  # bounding sphere, ligand-file frame
    difficulty_levels : int (clamped D from setup)
    Raises GenerationError with a message naming the unmet precondition
    (mode-infeasible type, empty allowed set, grid too small, no capable AA).
    """
```

`GenerationError` = a new pure exception class in `generator.py` (subclass `ValueError`; it is NOT a `persistence.FormatError` — a failed *generation* is not a malformed *file*). The caller (Phase 4 GUI / headless smoke) renders it as a user-visible message.

### 3.3 Two-phase flow around the generator (who does what)

```
cmd tier (headless/GUI)                    PURE generator
────────────────────────                   ──────────────
resolve setup + manifest/upload  ──▶       candidates (sorted, size-classed)
load ligand file(s) via path helper,       (no pymol, no files)
cmd-tier extract bounding sphere  ──▶      ligand_data per molecule
                                           generate(seed, …) ──▶ payload dict
make_level_spec_container(payload)  ◀──    (pure)
save via persistence (level_spec kind)
[materializer — other researcher: consumes payload verbatim]
```

The **cmd-tier ligand-bounds step is the only PyMOL-dependent input**. Alternative if a headless pure-only path is wanted for tests: allow `ligand_data` to come from a tiny fixture (hand-written bounds dicts) — the generator never knows the difference. This keeps the ≥100-seed suite 100 % WSL-pure (criterion 3 is tagged [WSL]).

---

## 4. Solvability-by-construction algorithm (GEN-04)

### 4.1 Required-set derivation (consumes the interaction mode — SETUP-06)

Semantics per REQUIREMENTS.md SETUP-06 exact text ("exclusive (required target is `any` interaction formed), block-exclusive (required set is the specific checked interactions), or unset (random required set)") — note this RESOLVES the ambiguity FEATURES.md flagged; the requirements doc is authoritative:

```python
def derive_required(setup, ligand_profile, rng, n_required_types):
    allowed = setup['allowed_interactions']            # canonical order, may be []
    mode = setup['interaction_mode']
    if mode == 'exclusive':
        # required target = ANY (allowed) interaction formed
        if not allowed:
            raise GenerationError("exclusive mode with no allowed interactions checked")
        return {'mode': 'any', 'items': []}
    supported = [t for t in allowed if ligand_support(t, ligand_profile)]
    if mode == 'block_exclusive':
        # required set = ALL checked interactions (exact, human-checked set)
        missing = [t for t in allowed if t not in supported]
        if missing:
            raise GenerationError(
                "molecule cannot support required interaction(s): %s"
                % ', '.join(missing))   # refuse, never silently degrade (§4.3)
        return {'mode': 'list',
                'items': [{'type': t, 'count': 1} for t in allowed]}
    # unset → random required set from the ligand-supported ∩ allowed
    if not supported:
        raise GenerationError(
            "molecule supports none of the allowed interactions")
    k = min(n_required_types, len(supported))
    picked = rng.sample(supported, k)                # supported is a sorted list
    return {'mode': 'list',
            'items': [{'type': t, 'count': 1}
                      for t in allowed if t in picked]}   # canonical order
```

Open point to confirm with the human (flagged OQ-1): whether `exclusive`'s "any" is scoped by `allowed_interactions` (recommended: yes — `allowed_interactions` is the game's interaction vocabulary everywhere; SCORE-04 displays "required interaction types + counts (`any` or from the allowed list)"). Also: `unset` + empty `allowed_interactions` → draw from all 7 types (recommended) or refuse (alternative).

`count` semantics: **v1 always count = 1** (recommended). Score = fraction of required interactions formed, binary per interaction (SCORE-01) → denominator = `len(items)` in list mode; in `any` mode the score is binary (≥1 formed → 1.0). The `count` field exists in the reserved schema for future multi-instance requirements; the generator may emit counts > 1 later without format change (additive semantic already accommodated).

### 4.2 Slot allocation (global allocation pass — Pitfall 11.1)

```python
def allocate_slots(required_items, n, rng):
    """One global pass per molecule. Returns the slot list."""
    total = n * n
    needed = len(required_items)                      # v1: count==1 per item
    if needed + 1 > total:                            # +1: keep ≥1 distractor slot
        raise GenerationError("grid %dx%d too small for %d required interactions"
                              % (n, n, needed))
    capable = {}
    for item in required_items:
        pool = [aa for aa in ALL_AA if aa_capable(aa, item['type'], ligand_profile)]
        if len(pool) < item['count']:
            raise GenerationError("no amino acid can form %r with this molecule"
                                  % item['type'])
        capable[item['type']] = pool                  # pool never empty (table §2.3)

    slot_ids  = all (row, col) pairs in fixed order   # deterministic, not rng
    required_slots = rng.sample(slot_ids, needed)     # WHERE the required AAs sit
    assignments = {}
    for slot, item in zip(sorted(required_slots, key=slot_order), shuffled_items):
        aa = rng.choice(capable[item['type']])
        assignments[slot] = {'aa': aa, 'role': 'required',
                             'can_form': [item['type']]}
    for slot in remaining_slots:                      # distractors, any of the 20
        assignments[slot] = {'aa': rng.choice(ALL_AA_LIST),
                             'role': 'distractor', 'can_form': []}
```

Design points:
- **One required unit = one dedicated slot** with `role='required'` and `can_form=[type]`. A single AA instance is never assigned two required types (simpler accounting; a required slot's guarantee is atomic).
- **Distractors are drawn from all 20 AAs** — including AAs that could coincidentally form required interactions. That is fine: solvability is guaranteed by the dedicated required slots *in addition to* whatever distractors happen to support; distractors make the game non-obvious (the player can't just click everything dark-colored… Hint operates on capability, but distractor *incapable* AAs are the challenge).
- `can_form` semantics (recommended, record in the module docstring): "the interaction types this slot was CHOSEN to guarantee" — a generation-time provenance record. It is NOT the hint's data source: Hint (Phase 5) recomputes capability live via the shared capability module (so distractors that could form a required interaction still hint correctly).
- **Invariant chain (tested, §8):** every required item has ≥1 dedicated capable slot; slots globally unique per molecule; `n*n == len(slots)`.

### 4.3 Edge cases and their rulings

| Edge case | Ruling |
|-----------|--------|
| `block_exclusive` checked set includes a type the ligand cannot support (e.g., `halogen` checked but ligand has no C–X) | **Refuse with a message naming the type(s)**. The human explicitly checked them; silent degradation would corrupt the game's contract. Surfaced at Generate-time in the GUI. |
| `unset` random draw includes an unsupported type | Cannot happen — the draw is from the supported∩allowed list (§4.1). |
| `exclusive` ("any") + ligand supports zero of the allowed types | Refuse ("molecule supports none of the allowed interactions"). |
| Ligand with a metal: `metal` becomes supportable only then; a ligand without metal never samples `metal` | Handled by `ligand_support()` predicate — exactly DETECT-02's "conditional on metal present". |
| Ligand without halogens: `halogen` never supportable (donors are ligand-side only — PLIP verified) | Same predicate. |
| Required AA pool smaller than count | Guarded; impossible in practice (§2.3 counts ≥4 per type). |
| `n² < needed + 1` | Refuse ("grid too small"). With n ≥ 3 and ≤ 7 required types this cannot trigger in v1; the guard protects future count>1 modes. |
| Empty `allowed_interactions` in block/unset modes | block: refuse ("no interactions checked"); unset: policy choice (OQ-1). |
| Same AA chosen for many distractor slots | Allowed (grids of repeated AAs are fine and even aid pattern-reading); the ≥100-seed distribution test (§8) guards against degenerate all-identical grids. |
| Distractor drawn identical to a required AA | Allowed — role fields keep bookkeeping unambiguous. |

---

## 5. Grid geometry (GEN-03) — concrete, deterministic, materializer-ready

### 5.1 Model

A **flat N×N plane** facing the ligand along a fixed world axis. Exact 3D aesthetics stay simple (per the objective); what must hold: non-overlap, beyond-gap placement, per-slot determinism, clickability (Phase 3 picks whole-AA objects).

Inputs (fed IN, ligand-file frame): ligand centroid `C = (cx, cy, cz)`, bounding radius `R` (max distance of any ligand atom from C — the same "maximum extent" concept PLIP uses for binding-site determination [V-SRC]).

Constants (ENGINEERING choices, not chemistry claims — tune freely, assert via invariants):

| Constant | Proposed | Rationale |
|----------|----------|-----------|
| `GRID_SPACING` | **8.0 Å** | Exceeds the largest capped-AA extent (Trp + caps ≈ 10–12 Å total length, ~3.5–4 Å half-width) with margin → adjacent grid AAs cannot interpenetrate. Verified consequence: non-overlap invariant testable purely (§8). |
| `GAP_MARGIN` | **5.0 Å** beyond `R` | "Beyond a gap": nearest grid plane sits `R + GAP_MARGIN` from the ligand centroid → no grid AA can intersect the ligand at spawn (AA half-extent < GAP_MARGIN + slot clearance). |
| Plane normal | **+Z (world)** | Deterministic without camera knowledge. The materializer may `cmd.zoom/orient` after placement for framing. |
| Grid axes | +X (columns), +Y (rows) | Right-handed, fixed. |
| Inter-molecule offset | molecule index `m` shifts the whole group (ligand + grid) by `m * (grid_width + INTER_GRID_MARGIN)` along +X | Guarantees **globally disjoint slots across molecules in a level** (ROADMAP criterion 3) whether the materializer shows one molecule at a time or all at once. `INTER_GRID_MARGIN` ≈ 6 Å. |

### 5.2 Position formula (pure)

```
half       = (n - 1) / 2.0
origin     = (cx - half*SPACING, cy - half*SPACING, cz + R + GAP_MARGIN)   # top-left corner
slot(r, c) = (cx + (c - half)*SPACING, cy + (r - half)*SPACING, cz + R + GAP_MARGIN)
```

- Centered on the ligand centroid's (x, y); plane offset along +Z by `R + GAP_MARGIN`. All positions in the **ligand-file frame**; the per-molecule world offset (§5.1) is a separate additive spec field (§9).
- Floats serialize exactly through JSON (Python json repr round-trips doubles); `allow_nan=False` (persistence) means the generator must guard against degenerate ligand data (`R = 0` or NaN bounds → `GenerationError`).
- Rows/cols map to slots: `slot_id = "r{row}c{col}"` (unique per molecule — the level_spec gate enforces this; generator guarantees it by construction), `row`/`col` ints 0..n-1.
- `grid_pose: {"position": [x, y, z]}` matches the reserved shape exactly. Orientation is NOT stored (AAs spawn in canonical orientation; rotation is gameplay state, not spec state). If later needed: additive `grid_pose.orientation` key — passthrough parse already tolerates it.

### 5.3 Materializer contract (what the other researcher consumes — no decisions needed at materialize time)

- For each slot: load/copy the bundled AA structure for `slot['aa']` (see OQ-4 re: `cmd.fragment` inventory — bundled files are the safe source), translate its object to `grid_pose.position` with **`camera=0`** (world frame — PITFALL 12's camera-frame leak is a materialize-time hazard, the spec's coordinates are world/ligand-file frame), apply the per-molecule group offset, name objects with the reserved `_aam_` prefix + sentinel conventions (`segi`, `b`) per PITFALLS 8/13.
- Count-assert everything (PITFALL 7): `len(slots)` objects created, atom counts per AA file match, sentinel counts match.
- No geometry math at materialize time; Reset (Phase 6) replays `grid_pose.position` verbatim — the same numbers the generator serialized.

---

## 6. Difficulty expression (GEN-05) — concrete mapping for D = 1..10

`D = setup['difficulty_levels'] ∈ [1, 10]` (cap 10 frozen). Levels `L = 0..D-1` (`level_index == L == tier`; level advance = strictly increasing tier, satisfying SCORE-03). All three GEN-05 axes must escalate monotonically (ROADMAP criterion 3). Integer half-up interpolation (NO `round()` — banker's rounding would make the middle tier asymmetric):

```
denom = D - 1                       # D == 1 → tier 0 = easiest (single level, predictable)
frac  = (L * SPAN + denom // 2) // denom   if D > 1  else  0
```

| Axis | Formula | Range | Rationale |
|------|---------|-------|-----------|
| `grid_n` | `3 + frac(GRID_SPAN=6)` | **3..9** | 9×9 = 81 AAs = the researched perf ceiling (PITFALLS 15 "~81 AAs"); 3×3 = 9 AAs minimum for a meaningful choice. Cap 10 grid would be 100 AAs/molecule × up to 10 molecules — rejected for perf headroom; can be revisited with data. |
| `n_required_types` | `1 + frac(SPAN=6)` | **1..7** | Matches the 7-type enum; **clamped down to `len(supported ∩ allowed)`** per molecule (a 2-feature ligand at tier 9 still gets 2). |
| `molecule_size_class` | bucket by heavy-atom count: `small < S1 ≤ medium < S2 ≤ large`; level L picks from the matching bucket: L in lower third → small, middle → medium, top third → large (D < 3: use the single best-fit bucket) | small/medium/large | Reserved-schema field. Bucket thresholds S1/S2 (propose **S1 = 25, S2 = 60 heavy atoms** — engineering buckets, tuned when the Phase-8 manifest exists; recorded as constants, not chemistry). Selection inside a bucket = seeded `rng.sample` from the deterministically sorted candidate list. |

Reference table (proposed, D=10 and the default D=3):

| L | D=10: grid_n / types / size | D=3: grid_n / types / size |
|---|------------------------------|----------------------------|
| 0 | 3 / 1 / small | 3 / 1 / small |
| 1 | 4 / 2 / small | 6 / 4 / medium |
| 2 | 4 / 2 / small | 9 / 7 / large |
| 3 | 5 / 3 / small | — |
| 4 | 5 / 4 / medium | — |
| 5 | 6 / 4 / medium | — |
| 6 | 7 / 5 / medium | — |
| 7 | 8 / 6 / large | — |
| 8 | 8 / 6 / large | — |
| 9 | 9 / 7 / large | — |

(Exact row values depend on the half-up interpolation; the planner should generate the table from the formula in a unit test rather than hand-transcribe — the test asserts monotonicity, not the literals.)

Notes:
- `molecules_per_level` is **independent** of difficulty (it is a setup knob, not a difficulty axis — GEN-05 names grid N, molecule size, type count only). Every level contains the same molecule count.
- Difficulty also implicitly scales *which* types appear (more types → more diverse grid); counts-per-type stay 1 in v1 (§4.1).
- `difficulty` dict emitted per level: `{"tier": L, "grid_n": …, "n_required_types": …, "molecule_size_class": …}` — matches the reserved shape verbatim.

---

## 7. Seeded determinism & serialization (replay contract)

### 7.1 RNG strategy

- **One master `random.Random(seed)`** (seed = the spec's top-level int). Per-**game-unit** sub-RNGs derived **from the master stream in a fixed order** (not from `hash()`):
  ```python
  master = random.Random(seed)
  sub_seeds = [master.randint(0, 2**31 - 1) for _ in range(n_units)]   # levels × molecules
  # then rng = random.Random(sub_seeds.pop(0)) inside each unit, consumed in
  # a FIXED call order (derive_required → slot sample → distractor fill)
  ```
  Why: consumption order must be code-order-stable; sub-seeding isolates units so adding a molecule to a level cannot shift another molecule's stream (protects golden tests from unrelated churn — the data-quirk-coupling lesson, PITFALL 11.2).
- **Deterministic iteration everywhere:** every collection the RNG touches is a `sorted(list)` or a list built in fixed code order. NEVER sample/choose from a set or dict; never iterate a set (PYTHONHASHSEED). For dicts, iterate in insertion order built from canonical lists.
- `rng.sample(supported, k)` where `supported` is canonical-ordered — deterministic.
- All randomness consumes the stream only via `randint/choice/sample/shuffle` (fine within one interpreter; §1.3 explains why cross-version drift is moot).

### 7.2 What must be serialized (the replay contract — spec replay is Phase 6's Reset, Phase 7's restart)

**Principle: the payload fully determines the level without re-running the RNG.** Seed enables regeneration; serialization enables exact replay. Concretely, everything the materializer/game needs:

| Payload element | Filled by | Why serialized |
|-----------------|-----------|----------------|
| `seed` (int) | generator (passed in) | provenance + regeneration; level_spec gate requires it |
| `detector_version` | generator (import constant) | stale-game refusal (DETECT-05) |
| `format_version` | generator (import constant) | additive evolution gate |
| per level: `level_index`, `difficulty{tier, grid_n, n_required_types, molecule_size_class}` | generator | difficulty axis record; monotonicity tests |
| per molecule: `ligand{source, set_id, entry_id, file, sha256, protonation, provenance}` | generator from candidates | materializer loads the exact file; sha256 pins provenance; `protonation` records the selected state (GEN-02); `file` is package-relative (to_windows_path applied only at load time — never store absolute paths, PITFALL 2) |
| per molecule: `required{mode, items[{type, count}]}` | generator (§4.1) | scoring + status-tab display; RESOLVED set (mode 'any' or 'list') |
| per molecule: `grid{n, slots[{slot_id, row, col, aa, role, can_form, grid_pose{position}}]}` | generator (§4.2, §5.2) | **exact replay**: Reset/restart re-materialize from these numbers, no RNG |
| NEW additive per molecule: `placement{offset: [x,y,z]}` | generator (§5.1) | per-molecule group offset so multi-molecule levels are disjoint; additive key — passthrough parse accepts it; document in the module docstring as an extension of the reserved shape |

Not serialized (derivable or gameplay state): sub-seeds (regeneration detail), AA orientation (canonical at spawn), anything the player does (that's checkpoint/sidecar territory, Phase 7).

**Round-trip gate:** every generation path must pass `make_level_spec_container(payload)` → `write_json_atomic` → `read_json_file` → `parse_level_spec_dict` == payload (already-proven container discipline; make it a standing test).

### 7.3 Generator-side protonation selection (GEN-02 data side)

- The generator does NOT modify chemistry — it **selects and records**: for each molecule, `ligand.protonation` is set from the candidate's manifest-recorded protonation option (demo sets curated in Phase 8 carry a default state + provenance; uploads record `"as-uploaded"` + sha256). Deterministic: if a manifest offers multiple states, the per-molecule RNG picks one (`rng.choice(sorted(states))`) — and the picked value lands in the spec, so replay never re-picks.
- Materializer (other researcher) consumes `protonation` to load the right file/state and to preserve bond orders/valence (SDF/MOL2); detector consumes it to know the expected donor/acceptor chemistry. BINANA's protonation warning (§1.2) is the citation backing "explicit state beats guessed state".
- The manifest schema for protonation options is a Phase-2/8 shared contract → version it and smoke-test every id (PITFALL 11.3). Until Phase 8, Phase 2 bundles a minimal demo manifest with `protonation: "standard"`-style recorded strings.

---

## 8. ≥100-seed invariant test suite (ROADMAP criterion 3) — proposed list

All `[WSL]` unless noted: the generator + capability modules are pure; ligand bounds come from fixtures. Parametrize over `seeds = range(100)` (or a fixed list of 100 ints) and over setup variations (D ∈ {1, 3, 10}, mode ∈ {3}, molecules ∈ {1, 2, 5}).

### A. Determinism & format
1. **Determinism:** `generate(seed, …)` called twice → payloads compare equal (deep equality), byte-identical after `json.dumps(sort_keys=True)`.
2. **Round-trip:** every payload passes `parse_level_spec_dict(make_level_spec_container(payload))` unchanged; file round-trip byte-stable.
3. **Version stamps:** payload `detector_version == DETECTOR_VERSION`, `format_version == LEVEL_SPEC_VERSION`, `seed` real int (bool can never appear — generator writes ints; test asserts type).
4. **Cross-seed distinctness:** ≥ 95 of 100 seeds produce distinct payloads (catches accidental constant-generation; threshold loose to avoid flaky statistics).

### B. Solvability (GEN-04)
5. **Required coverage:** for every level/molecule, for every `required.items` entry, the number of slots with `item['type'] ∈ slot['can_form']` ≥ `item['count']` **counting only `role='required'` slots** (dedicated guarantee, distractors excluded from the proof).
6. **can_form truthfulness:** for every slot, `aa_capable(slot['aa'], t, ligand_profile)` is True for every `t ∈ slot['can_form']` (the table never lies); and `can_form ⊆ INTERACTION_TYPES` (generator-side enum consistency — the guarantee level_spec deliberately does not check).
7. **Mode semantics:** exclusive → `required.mode == 'any'`; block_exclusive → `mode == 'list'` and `items` == the checked set exactly (canonical order); unset → `items ⊆ allowed_interactions` and `len(items) == min(n_required_types, len(supported))`.
8. **Feasibility refusal:** crafted infeasible inputs (block_exclusive with `halogen` on a halogen-free ligand; empty allowed in exclusive) raise `GenerationError` with the offending type named.

### C. Grid structure (GEN-03 + ROADMAP "globally disjoint")
9. **Shape:** `grid.n == difficulty.grid_n`; `len(slots) == n*n`; `(row, col)` cover the full range exactly once; `slot_id` unique per molecule (redundant with the parse gate — assert at the source too).
10. **Non-overlap:** all pairwise slot distances ≥ `GRID_SPACING` (allow tiny epsilon; plane geometry makes this trivially true — the test pins the constant's honesty).
11. **Beyond-gap:** every slot position satisfies `distance(slot, ligand_centroid) ≥ R + GAP_MARGIN` (with epsilon); plus a minimum-distance bound (gap not absurdly large — e.g. ≤ `R + GAP_MARGIN + n*SPACING` sanity ceiling).
12. **Global disjointness:** across molecules in one level, no two slots from different molecules share a position (inter-molecule offset works).
13. **Float hygiene:** every serialized position is finite (`json allow_nan=False` would refuse — assert explicitly with `math.isfinite` for a better message).

### D. Difficulty expression (GEN-05)
14. **Monotonic escalation:** across a game's levels, `grid_n` non-decreasing, `n_required_types` non-decreasing (pre-clamp values), `molecule_size_class` rank non-decreasing; `level_index == tier` and tiers are `0..D-1` strictly ascending.
15. **Clamping honesty:** `n_required_types` (emitted intent) ≤ 7; emitted `required.items` count ≤ supported∩allowed for that molecule.
16. **Cap compliance:** for every D in 1..10 the mapping produces exactly D levels with tiers 0..D-1 (parametrized over all 10 legal D values).

### E. Randomization quality (soft, seed-corpus statistics)
17. **Distractor diversity:** across the 100-seed corpus, every one of the 20 AAs appears in at least one distractor slot (catches a broken pool); no seed produces an all-identical grid (for n ≥ 2).
18. **Capability-class coverage:** across the corpus, each interaction type is required at least once (for a multi-type demo ligand fixture) — guards against a sampling bug that starves a type.
19. **Slot-position coverage:** across the corpus, required slots are not concentrated on fixed positions (e.g., a fixed slot is required in < 50 % of seeds for n ≥ 3).

### F. Headless-only verification (NOT WSL — coordinate with the materializer researcher)
20. **Materialized counts:** objects/atoms/sentinels created == spec slot/atom counts (Pitfall 7 count-assertion discipline).
21. **Real-coordinate gap check:** `cmd.get_coordset`-derived distances match the spec's invariant 10/11 in the live session (catches camera=0 mistakes, frame leaks).
22. **Clickability smoke:** each grid AA object is individually pickable (Phase 3 human check inherits this).

---

## 9. What the generator EMITS — concrete payload example

(Fits the reserved shape; additive `placement` key documented as an extension.)

```json
{
  "detector_version": "det-1",
  "format_version": 1,
  "seed": 8675309,
  "levels": [
    {
      "level_index": 0,
      "difficulty": {"tier": 0, "grid_n": 3, "n_required_types": 1,
                     "molecule_size_class": "small"},
      "molecules": [
        {
          "molecule_id": "mol-001",
          "ligand": {"source": "demo", "set_id": "demo-set-01",
                     "entry_id": "ATP", "file": "data/ligands/ATP_Mg_standard.sdf",
                     "sha256": "…", "protonation": "standard",
                     "provenance": "PDB 1XDN ligand; protonation per Phase-8 record"},
          "required": {"mode": "list",
                       "items": [{"type": "h_bond", "count": 1},
                                 {"type": "pi_stacking", "count": 1}]},
          "placement": {"offset": [0.0, 0.0, 0.0]},
          "grid": {"n": 3, "slots": [
            {"slot_id": "r0c0", "row": 0, "col": 0, "aa": "LYS",
             "role": "required", "can_form": ["h_bond"],
             "grid_pose": {"position": [-8.0, -8.0, 14.7]}},
            {"slot_id": "r0c1", "row": 0, "col": 1, "aa": "PHE",
             "role": "required", "can_form": ["pi_stacking"],
             "grid_pose": {"position": [0.0, -8.0, 14.7]}},
            {"slot_id": "r0c2", "row": 0, "col": 2, "aa": "GLY",
             "role": "distractor", "can_form": [],
             "grid_pose": {"position": [8.0, -8.0, 14.7]}}
            /* … 6 more slots for n=3 … */
          ]}
        }
        /* … molecules_per_level - 1 more, each with its own placement.offset … */
      ]
    }
    /* … difficulty_levels - 1 more levels, escalating … */
  ]
}
```

Consumers:
- **Materializer (Phase 2 cmd tier):** loads `ligand.file` (sha256-verified, package-relative + path helper), applies `placement.offset` to the molecule group, creates one object per slot at `grid_pose.position` (world frame, `camera=0`), names/sentinels per PITFALLS 8/13. No decisions, count-asserts only.
- **Detector:** reads `required` for the scored set; consumes `capability.py` typing for AA-side classification (agreement = DETECT-04).
- **Game status tab (Phase 5):** renders `required` ("any" or the item list) — SCORE-04.
- **Hint (Phase 5):** recomputes per-slot capability live from `slot.aa` + `required` via `capability.py` (NOT from `can_form`, which is a generation-time record).
- **Reset/Restart (Phases 3/6):** re-apply `grid_pose.position` (+ `placement.offset`) — spec replay, no RNG, no inverse transforms.
- **Export/Import (Phase 7):** the payload IS the shareable game spec (level_spec container kind already reserved).

---

## 10. Common pitfalls (generation-specific)

| Pitfall | Why it bites | Prevention |
|---------|--------------|------------|
| Set/dict-iteration randomness | PYTHONHASHSEED randomizes str-hash → set order differs per process → same seed, different levels | Only RNG over `sorted(list)` / fixed-order lists; never `rng.choice(set)`; test 1 catches it (run suite twice in one process + subprocess determinism check) |
| Consuming one shared RNG stream in mutating code order | Inserting a molecule into level 2 shifts level 3's stream → golden tests churn (data-quirk coupling, PITFALL 11.2) | Per-unit sub-seeds drawn once from the master in fixed order (§7.1) |
| `round()` for difficulty interpolation | Python banker's rounding makes mid-tier asymmetric (round(2.5)==2) | Integer half-up `(x + d//2) // d`; parametrized monotonicity test over D=1..10 |
| D==1 division by zero in interpolation | `L/(D-1)` crashes for single-level games | Guard: D==1 → tier-0 values |
| Capability table drift vs detector typing | Generator promises "LYS is cation-capable"; detector's atom rules disagree → unsolvable-in-practice levels, hint/score disagreement (DETECT-04 violation) | ONE shared `capability.py`; an invariant test cross-checks table claims against the detector's typing functions on synthetic atoms |
| Backbone universality silently adopted | If detector counts backbone H-bonds but table is side-chain-only, EVERY AA trivially forms h_bond and "required h_bond" levels are auto-solved | Decision D1 recorded in BOTH modules' docstrings; detector restricted to side-chain atoms for grid AAs; verified by test 6 + a scripted-pose detector test (detector researcher) |
| Emitting NaN/Infinity positions from degenerate ligand bounds | `allow_nan=False` refusal at save time, far from the bug | Guard `ligand_data` at generate(): finite centroid, R ≥ min radius, else GenerationError |
| Serializing absolute or Windows paths in `ligand.file` | Breaks on repo move / WSL↔Windows (PITFALL 2) | Package-relative paths only; `to_windows_path()` applied exclusively at load time in the cmd tier |
| Storing `hash()`-derived seeds or `time`-based fallbacks | Non-reproducible across processes | Master seed is the caller's int only; no defaults to time; bool seeds refused upstream by level_spec gate (and generator should reject them too for a clearer message) |
| Grid N=10 ambition | 100 AAs × 10 molecules × 10 levels = 10 000 AA objects — perf budget death (PITFALL 15) | Cap grid at 9 (§6); revisit only with headless perf evidence |
| `itertools` import in the new pure modules | Whitelist failure in Gate A (not in ALLOWED_STDLIB) | Use `math`, `random`, `copy`, `collections`, comprehensions; if itertools becomes necessary, extend the whitelist as a reviewed change |
| Forgetting to add new modules to PURE_MODULES | Gates silently don't scan the new modules | First task of the generator plan: append `capability`, `generator` to `tests/test_purity.py` PURE_MODULES (the suite then enforces everything) |

---

## 11. Open questions (need human/planner decisions)

1. **`exclusive` scoping (OQ-1):** is "any interaction formed" scoped by `allowed_interactions` (recommended: yes) and what happens with an empty allowed list in exclusive mode (recommended: refuse at Generate with a setup-fixing message)? Also `unset` + empty allowed list (recommended: draw from all 7 types, since `unset` means "the game picks"). Needs a recorded human call before the generator plan freezes.
2. **Capability-table approval [GATE]:** the §2 table (esp. hydrophobic set membership, Cys/Tyr handling, His salt-bridge stance under neutral-His bundling, the four RESOLVE rows) must be human-approved together with the typing doc. Sequence it as a plan step adjacent to the threshold-table gate (same protocol: source rows + approval recorded in-repo).
3. **Detector coordination (D1/D3/D4):** side-chain-only H-bond for grid AAs; salt-bridge polarity pairing; cation-π direction. These change the DETECTOR's rules, not just the table — the two Phase-2 generator/detector plans must reference the same decision records. Recommendation: one short shared decision doc (e.g., `aamatch/docstring` + a section in the threshold/typing gate doc) written once, cited twice.
4. **AA structure source (OQ-4):** `cmd.fragment` amino-acid inventory is LOW-confidence (STACK.md: chempy fragments dir ships only `__init__.py` — do not plan around it). The generator only emits `aa` names; the materializer needs a bundled AA file per name (v1 `data/` pattern). Confirm in the materializer spike; the generator is agnostic.
5. **Grid facing the player (cosmetic):** fixed +Z plane is deterministic but may face away from the default camera on some ligands. If Phase 3 human checks find it awkward, the fix is a materializer-side `cmd.zoom/orient` (view state, not spec state) — no generator change. Noted so nobody "fixes" it in the spec.
6. **`n_required_types` vs ligand richness at high D:** high tiers on poor ligands clamp to few types — acceptable (difficulty then comes from grid N + size). If human wants strict escalation, Phase 8 curation must ensure every set has ≥7-feature ligands at the top tiers — a curation note, not a generator change.
7. **Counts>1:** reserved schema supports it; v1 keeps 1. If difficulty later needs "2× hydrophobic", the only changes are in `derive_required` + scoring denominator — no format change. Recorded to prevent premature schema speculation.

---

## 12. Sources

### Primary (HIGH — fetched/verified 2026-09-06 unless noted)
- Local repo (read directly): `aamatch/level_spec.py`, `aamatch/setup_state.py`, `aamatch/persistence.py`, `tests/test_purity.py`, `.planning/phases/01-bootstrap-pure-foundation/01-05-SUMMARY.md`, `01-06-SUMMARY.md`, `.planning/ROADMAP.md` (Phase 2), `.planning/REQUIREMENTS.md` (GEN-01..06, SETUP-06, DETECT-01..05, SCORE-01), `.planning/research/{PITFALLS,ARCHITECTURE,FEATURES,STACK,SUMMARY}.md`
- BINANA 2.1 INTERACTIONS.md — https://raw.githubusercontent.com/durrantlab/binana/main/INTERACTIONS.md (protein charged groups, aromatics by residue name, donor/acceptor group rules, halogen donor/acceptor sets, distance-only metal rationale, protonation recommendation)
- PLIP help page — https://plip-tool.biotec.tu-dresden.de/plip-web/plip/help (charged-group attribution; halogen donors ligand-side only + protein acceptor rule; explicit metal-complex protein-side group list; hydrophobic atom rule; binding-site "maximum extent" concept)
- ProLIF master `interactions/interactions.py` — https://raw.githubusercontent.com/chemosim-lab/ProLIF/master/prolif/interactions/interactions.py (Hydrophobic atom SMARTS; HBAcceptor/HBDonor patterns + backbone notes; XBDonor excluding C–F; Cationic/Anionic + CationPi/PiCation directionality; MetalDonor SMARTS incl. metal list; FaceToFace/EdgeToFace structure) + ProLIF docs page https://prolif.readthedocs.io/en/latest/source/modules/interaction-fingerprint.html (tutorial output showing backbone HBAcceptor on VAL)
- Python 3.6.15 random docs — https://docs.python.org/3.6/library/random.html ("Notes on Reproducibility" guarantees; set-sampling caveat)
- Kyte & Doolittle 1982 citation — doi:10.1016/0022-2836(82)90515-0, PMID 7108955 (verified via the reference list of the Wikipedia *Hydrophobicity scales* article, fetched 2026-09-06; the article's Wimley–White table also verified — used to show scale-choice sensitivity, not adopted)

### Secondary (MEDIUM)
- Wikipedia *Hydrophobicity scales* (tertiary aggregation; used only to locate/verify the primary citation and the whole-residue-scale contrast)

### Prior verified planning docs (not re-fetched)
- `.planning/research/FEATURES.md` (PLIP/ProLIF/BINANA doc existence + shapes, fetched 2026-09-05; exclusive/block-exclusive ambiguity note — now superseded by REQUIREMENTS.md SETUP-06 wording)
- `.planning/research/PITFALLS.md` (Pitfall 11 generation contract; Pitfall 12 frames/protonation; Pitfall 15 perf ceiling)

### Deliberately NOT asserted
- Any numeric interaction threshold (detector researcher's gate; published tables exist at the PLIP help page and BINANA INTERACTIONS.md — verified accessible, not adopted).
- Exact Windows conda env versions; `cmd.fragment` inventory; `.pse` matrix round-trip — all pre-existing Phase flags, irrelevant to the pure generator.

---

## 13. Metadata

**Confidence breakdown:**
- Code contracts (schema, gates, purity): HIGH — read from source this session.
- Typing/capability sources: HIGH for what the tools' docs say; the in-house TABLE is a flagged draft awaiting the human gate.
- Algorithms (solvability, grid, difficulty, RNG): HIGH as engineering proposals — constants are tunable, invariants are testable; no chemistry claims embedded.
- Test-invariant list: HIGH for WSL-purity of items 1–19 (fixtures-based); headless items 20–22 belong to the materializer researcher.

**Research date:** 2026-09-06
**Valid until:** ~2026-10-06 (stable — depends only on frozen Phase-1 contracts and published reference docs); re-verify the three RESOLVE rows if ProLIF/PLIP publish major typing changes before Phase 2 freezes.

---
*Generation-domain research for Phase 2: AA-match headless game engine (generator + solvability).*
