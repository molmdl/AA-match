# Demo Data Sources (AA-match)

**Last verified:** 2026-09-26 (all policy quotes and per-entry provenance re-verified at the
08-04 GATE). Paper-DOI resolution spot-checks from this environment on **2026-09-26** (3 samples
across 3 sets, all HTTP 200 at doi.org): entry DOI `10.2210/pdb1oxr/pdb` (demo-easy-1) and paper
DOIs `10.1016/j.chembiol.2017.08.021` (demo-hard-1, 5NWQ) and `10.1016/j.str.2016.08.010`
(demo-hard-3, 5IT5).

**Verification protocol:** every factual claim in this document carries a fetched URL plus
a verification date. Human approval for every bundled ligand is recorded in
`.planning/phases/08-demo-curation-citations/08-PROPOSALS.md` (**APPROVED 2026-09-26, human**)
*BEFORE* any bundled file was committed (DETECT-03 precedent). The per-entry table rows below
are produced from the committed specs — reproduce them with
`python3.6 scripts/build_demos.py --report-only` (machine-reproducible, regenerable); the
human-approved depth behind each row lives in `scripts/demo_specs/<set_id>.json`
(per-entry `provenance.notes`) and in 08-PROPOSALS.md.

**Status:** awaiting [HUMAN] sign-off at the 08-11 checkpoint (ROADMAP phase-8 criterion 3).
No free-text claim below is editorialized: honest absences are marked as such, and every
"VERIFIED" note names where the verification happened.

---

## 1. Sources & licenses (verbatim policy quotes)

| Source | License | Policy quote (verbatim) | URL | Verified |
|---|---|---|---|---|
| PubChem (NCBI) | Public domain (US-gov) / no-restrictions on use or distribution | "Information that is created by or for the US government on this site is within the public domain… it is requested that in any subsequent use of this work, NLM be given appropriate acknowledgment." | https://www.ncbi.nlm.nih.gov/home/about/policies/ | fetched 2026-09-24; re-verified verbatim 2026-09-26 (08-04 GATE) |
| PubChem (NCBI) — Fair Use Disclaimer | NCBI places no restrictions on the data, with a recorded submitter-rights caveat | "NCBI itself places no restrictions on the use or distribution of the data contained therein" — with the caveat that "some submitters of the original data may claim patent, copyright, or other intellectual property rights…" (caveat does not apply to our 15 well-known drug-like/metabolite CIDs; see U1 resolution in 08-PROPOSALS.md) | https://ftp.ncbi.nlm.nih.gov/pubchem/README | fetched verbatim 2026-09-24; re-verified verbatim 2026-09-26 (08-04 GATE) |
| wwPDB / RCSB PDB archive (PDB entries, CCD definitions, CCD ideal SDFs) | CC0 1.0 (permitting bundling/redistribution; attribution requested, not required) | "Data files contained in the PDB archive are available under the CC0 1.0 Universal (CC0 1.0) Public Domain Dedication. Users of PDB data are encouraged to attribute the original authors of the PDB structure data where possible." | https://www.wwpdb.org/about/usage-policies (mirrored on https://www.rcsb.org/pages/policies) | fetched 2026-09-24; re-verified verbatim 2026-09-26 (08-04 GATE) |

**Database citations (each verified from its own or its database's official page):**

| Database | Citation | Verified |
|---|---|---|
| RCSB PDB | Berman HM, Westbrook J, Feng Z, et al. "The Protein Data Bank." *Nucleic Acids Res.* 2000;28:235-242. doi:10.1093/nar/28.1.235 | fetched from the RCSB policies page, 2026-09-24 |
| wwPDB | wwPDB consortium. "Protein Data Bank: the single global archive for 3D macromolecular structure data." *Nucleic Acids Res.* 2019;47(D1):D520-D528. doi:10.1093/nar/gky949 | fetched from the RCSB policies page, 2026-09-24 |
| PubChem (canonical) | Kim S, Chen J, Cheng T, et al. "PubChem 2025 update." *Nucleic Acids Res.* 2025;53(D1):D1516-D1525. doi:10.1093/nar/gkae1059 | VERIFIED 2026-09-26 verbatim from https://pubchem.ncbi.nlm.nih.gov/docs/citation-guidelines (the human-verified canonical page, 08-04 U1/U3 resolution; fetched via its Markdown representation https://pubchem.ncbi.nlm.nih.gov/pcfe/docs/markdown/citation-guidelines.md) |
| PUG-REST (fetch service) | Kim S, Thiessen PA, Cheng T, Yu B, Bolton EE. "An update on PUG-REST: RESTful interface for programmatic access to PubChem." *Nucleic Acids Res.* 2018;46(W1):W563-W570. doi:10.1093/nar/gky294 | VERIFIED 2026-09-26 from the same citation-guidelines page (08-04 U1) |
| PLIP (interaction provenance) | Schake H, Bolz C, et al. "PLIP 2025." *Nucleic Acids Res.*, doi:10.1093/nar/gkaf361 | fetched from the PLIP tool page https://plip-tool.biotec.tu-dresden.de/plip-web/plip/index, 2026-09-24 (tool live-verified) |
| ChEBI (consulted, NOT a bundled source) | Malik A, et al. "ChEBI: re-engineered for a sustainable future." *Nucleic Acids Res.*, doi:10.1093/nar/gkaf1271 | fetched from https://www.ebi.ac.uk/chebi/about, 2026-09-24 (CC BY 4.0 — recorded for completeness; deprotonated-citrate sourcing via ChEBI was REJECTED for v1 per approved Decision 5) |

**Per-record PubChem citation format (from the citation-guidelines page, 08-04 U1
resolution):** "PubChem Identifier: CID \<CID\>; URL: https://pubchem.ncbi.nlm.nih.gov/compound/\<CID\>".
Every bundled PubChem ligand below carries its CID; substitute it into that format for a
per-record citation.

**Secondary provenance:** PDBe per-entry pages (`https://www.ebi.ac.uk/pdbe/entry/pdb/<id>`)
render ligand/interaction info per entry — human-browser-tested on 1OXR, 2026-09-26
(08-04 U4 resolution: "tested 1xor pass"). Primary provenance remains the RCSB records.
DrugBank (CC BY-NC 4.0) never carries our license — see §4.

---

## 2. Demo sets (dropdown tier order: easy → hard → challenge → very challenging; development set last)

Set-level license/provenance fields below match `aamatch/data/MANIFEST.json` **verbatim**;
entry counts and full 64-hex sha256 values are pinned in `aamatch/data/MANIFEST.json`
(regenerate via `scripts/build_demos.py ... --fetch`; never hand-edit an SDF or the
manifest — 02-04 law). Rows are the exact `--report-only` columns plus the plan-required
ID (CID/CCD) and protonation-why depth (transcribed from the approved specs' per-entry
notes). `—` in a paper-DOI cell means **none recorded in the RCSB data — honest absence,
not an omission to invent** (approved row: 1MBN — the 8FUY/1S0R/9NDX rows were
AMENDED 2026-10-04 by human directive at the 08.1-08 checkpoint, and the 1MBN
row itself was AMENDED to 4WNV 2026-10-04 by human directive at the 08.1-08
checkpoint fix-batch 2 — that swap SUPERCEDES the 1982-era honest-absence row,
leaving NO honest-absence paper-DOI cell among the current curated rows; every
amended row carries its dated amendment note inline).

### demo-easy-1 — "Everyday organics" (tier: easy)

- **Rationale:** the household-organics duo for the 2-molecule easy tier; aspirin is the
  fully pre-verified provenance anchor (1OXR) and benzoic acid the smallest aromatic (9 heavy),
  keeping easy grids dense (08-PROPOSALS.md Set 1).
- **License:** `Public domain (NCBI PubChem)` (matches MANIFEST.json verbatim) —
  https://www.ncbi.nlm.nih.gov/home/about/policies/ ; complex reference metadata:
  `CC0 1.0 (wwPDB)` — https://www.wwpdb.org/about/usage-policies (quotes in §1).
- **Cross-ref:** counts/sha256 pinned in `aamatch/data/MANIFEST.json`; regenerate via
  `python3.6 scripts/build_demos.py --spec scripts/demo_specs/demo-easy-1.json --fetch` —
  never hand-edit an SDF or the manifest (02-04 law).

| entry_id | file | molecule | source (fetch URL) | ID | PDB complex (ID + entry DOI + paper DOI) | interaction provenance | protonation ('as-recorded' + why) | halogen/metal | sha256 | fetched |
|---|---|---|---|---|---|---|---|---|---|---|
| aspirin | ligands/demo-easy-1-aspirin.sdf | acetylsalicylate anion (C9H7O4−, 13 heavy, −1) | https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/3434975/SDF?record_type=3d | CID 3434975 | 1OXR (phospholipase A2–aspirin·Ca²⁺; AIN confirmed in nonpolymer inventory 2026-09-26) · entry DOI https://doi.org/10.2210/pdb1oxr/pdb · paper DOI https://doi.org/10.1080/10611860400024078 (VERIFIED at RCSB record; human-verified via PDB website) | PLIP (doi:10.1093/nar/gkaf361) reference complex 1OXR | as-recorded — **PHYSIOLOGICAL: acetylsalicylate −1** (99.99% at pH 7.4; pKa 3.47/3.5 PubChem AID 781325/781326, 3.49 Merck, 3.38 Serjeant via IUPAC dataset). **Amended 2026-10-05, human physiological-protonation decision "2 go R1-R8"** (08.1-08 protonation audit row 1/R3; directive "per our spec we want to assume physiological pH normally"): was CID 2244 neutral free acid (Charge 0). The prior recorded ester-based accidental `−` typing (capability ester false-positive) is SUPERSEDED by this bona-fide carboxylate; the neutral CID 2244 record stays in git history | no / no | 57c2f6ed874a | 2026-09-26 (ligand re-fetched 2026-10-05) |
| benzoic_acid | ligands/demo-easy-1-benzoic_acid.sdf | benzoate anion (C7H5O2−, 9 heavy, −1) | https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/242/SDF?record_type=3d | CID 242 | 5E4D (hydroxynitrile lyase–benzoic acid; BEZ confirmed in inventory 2026-09-26) · entry DOI https://doi.org/10.2210/pdb5e4d/pdb · paper DOI https://doi.org/10.1038/srep46738 (resolves 200) | PLIP (doi:10.1093/nar/gkaf361) reference complex 5E4D | as-recorded — **PHYSIOLOGICAL: benzoate −1** (99.94% at pH 7.4; pKa 4.207–3.96 AID 781325–781330, 4.19 LIDE, 4.204 CRC). **Amended 2026-10-05, human decision "2 go R1-R8"** (audit row 2/R2): was CID 243 neutral free acid (Charge 0 per approved C3); the charged benzoate alternate (CID 242, approved at 08-04) is now the SUBSTITUTED form — easy-1 gains its first salt-bridge-capable ligand. Neutral CID 243 record stays in git history | no / no | 1775c091b14a | 2026-09-26 (ligand re-fetched 2026-10-05) |

### demo-easy-2 — "Metabolites & ions" (tier: easy)

- **Rationale:** the central metabolite (citric acid) beside its minimal artifact-level
  ion (acetate) — teaches "charged group = salt bridge" at the smallest possible size
  (08-PROPOSALS.md Set 2).
- **License:** `Public domain (NCBI PubChem)` (matches MANIFEST.json verbatim); complex
  reference metadata `CC0 1.0 (wwPDB)` (quotes in §1).
- **Cross-ref:** counts/sha256 pinned in `aamatch/data/MANIFEST.json`; regenerate via
  `python3.6 scripts/build_demos.py --spec scripts/demo_specs/demo-easy-2.json --fetch`.

| entry_id | file | molecule | source (fetch URL) | ID | PDB complex (ID + entry DOI + paper DOI) | interaction provenance | protonation ('as-recorded' + why) | halogen/metal | sha256 | fetched |
|---|---|---|---|---|---|---|---|---|---|---|
| citric_acid | ligands/demo-easy-2-citric_acid.sdf | citrate, C6H5O7³⁻ (13 heavy, −3) | https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/31348/SDF?record_type=3d | CID 31348 | 1CTS (citrate synthase with citric acid — the more classic reference; CIT 'CITRIC ACID' confirmed in the RCSB nonpolymer inventory via the data API, 2026-10-04) · entry DOI https://doi.org/10.2210/pdb1cts/pdb (resolves) · paper DOI https://doi.org/10.1016/0022-2836(82)90452-1 (resolves; CrossRef title "Crystallographic refinement and atomic models of two different forms of citrate synthase at 2.7 and 1.7 Å resolution" — Remington, Wiegand, Huber, JMB 1982 — matches the RCSB primary citation exactly) · **Amended 2026-10-04 by human directive (08.1-08 checkpoint finding 4): reference complex 8FUY → 1CTS**; prior 8FUY record (C. fasciculata G6PDH citrate-bound; CIT confirmed 2026-09-26 — research's top hit 1O7X rejected: no nonpolymer entities, correction C5; paper DOI none recorded, honest absence) stays in git history | PLIP (doi:10.1093/nar/gkaf361) reference complex 1CTS | as-recorded — **PHYSIOLOGICAL: citrate ³−** (90.9% at pH 7.4 / H-citrate²⁻ 9.1%; pKa1 3.13, pKa2 4.76, pKa3 6.39–6.40 — Wikipedia chembox citing Sigma/Silva et al., Dalton Trans 2009; zero-ionic-strength 3.128/4.761/6.396). **Amended 2026-10-05, human physiological-protonation decision "2 go R1-R8"** (08.1-08 audit row 3/R1 — the human's own audit trigger: "citrate supposed to be deprotonated under physiological pH, but currently fully protonated"; directive "per our spec we want to assume physiological pH normally"): was CID 311 free acid per approved Decision 5 ("deprotonated-citrate sourcing REJECTED for v1 — only a 2D ChEBI route exists") — that verdict is SUPERSEDED by the audit's verified clean PubChem 3D route, and the decision is the human's own. The H-citrate(2−) minority record CID 24802 was recorded but NOT chosen. Neutral CID 311 record stays in git history. Typing: three deprotonated carboxylates — citrate is now the set's SECOND salt-bridge carrier beside acetate (was "the set's salt-bridge slot is acetate") | no / no | 780b88eb1b73 | 2026-09-26 (ligand re-fetched 2026-10-05) |
| acetate | ligands/demo-easy-2-acetate.sdf | acetate anion (C2H3O2−, 4 heavy, −1) | https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/175/SDF?record_type=3d | CID 175 | 5YS8 (succinate–acetate permease; ACT confirmed 2026-09-26 — research-style top hit 5ZUG lacked ACT) · entry DOI https://doi.org/10.2210/pdb5ys8/pdb · paper DOI https://doi.org/10.1038/s41422-018-0032-8 (resolves 200) | PLIP (doi:10.1093/nar/gkaf361) reference complex 5YS8 | as-recorded — the deprotonated anion (−1) CHOSEN over acetic acid deliberately: it is the salt-bridge carrier (carboxylate charge-group typing requires the recorded charge) | no / no | fb910587fea8 | 2026-09-26 |

### demo-easy-3 — "Caffeine" (tier: easy)

- **Rationale:** the most-recognized everyday stimulant; a one-molecule easy set showcasing
  acceptor-only h_bond (every ring N methylated ⇒ no N–H donor — a direction-refined-typing
  teaching case with no other easy-tier carrier) + pi_stacking (08-PROPOSALS.md Set 3).
- **License:** `Public domain (NCBI PubChem)` (matches MANIFEST.json verbatim); complex
  reference metadata `CC0 1.0 (wwPDB)` (quotes in §1).
- **Cross-ref:** counts/sha256 pinned in `aamatch/data/MANIFEST.json`; regenerate via
  `python3.6 scripts/build_demos.py --spec scripts/demo_specs/demo-easy-3.json --fetch`.

| entry_id | file | molecule | source (fetch URL) | ID | PDB complex (ID + entry DOI + paper DOI) | interaction provenance | protonation ('as-recorded' + why) | halogen/metal | sha256 | fetched |
|---|---|---|---|---|---|---|---|---|---|---|
| caffeine | ligands/demo-easy-3-caffeine.sdf | caffeine, 1,3,7-trimethylxanthine (C8H10N4O2, 14 heavy) | https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/2519/SDF?record_type=3d | CID 2519 | 3G6M (chitinase CrChi1–caffeine; CFF confirmed 2026-09-26) · entry DOI https://doi.org/10.2210/pdb3g6m/pdb · paper DOI https://doi.org/10.1099/mic.0.043653-0 (VERIFIED at RCSB record; human-verified via PDB website) | PLIP (doi:10.1093/nar/gkaf361) reference complex 3G6M | as-recorded — neutral (Charge 0); no ionization choice needed | no / no | f6824b927067 | 2026-09-26 |

### demo-hard-1 — "Trypsin classics" (tier: hard)

- **Rationale:** the textbook serine-protease system (trypsin–benzamidine, atomic
  resolution) paired with the smallest possible charged amino-group species — the ion
  pair to easy-2's acetate (08-PROPOSALS.md Set 4).
- **License:** `Public domain (NCBI PubChem)` (matches MANIFEST.json verbatim); complex
  reference metadata `CC0 1.0 (wwPDB)` (quotes in §1).
- **Cross-ref:** counts/sha256 pinned in `aamatch/data/MANIFEST.json`; regenerate via
  `python3.6 scripts/build_demos.py --spec scripts/demo_specs/demo-hard-1.json --fetch`.

| entry_id | file | molecule | source (fetch URL) | ID | PDB complex (ID + entry DOI + paper DOI) | interaction provenance | protonation ('as-recorded' + why) | halogen/metal | sha256 | fetched |
|---|---|---|---|---|---|---|---|---|---|---|
| benzamidine | ligands/demo-hard-1-benzamidine.sdf | benzamidinium (C7H9N2⁺, 9 heavy, +1) | https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/444655/SDF?record_type=3d | CID 444655 | 1V2L (benzamidine in complex with bovine trypsin variant; BEN 'BENZAMIDINE' confirmed in the RCSB nonpolymer inventory via the data API, 2026-10-04 — SO4 + CA ions also present) · entry DOI https://doi.org/10.2210/pdb1v2l/pdb (resolves) · paper DOI https://doi.org/10.1016/j.jmb.2003.11.041 (resolves; CrossRef title "Understanding Protein–Ligand Interactions: The Price of Protein Flexibility" — Rauh, Klebe, Stubbs, JMB 2004 — matches the RCSB primary citation exactly) · **Amended 2026-10-04 by human directive (08.1-08 checkpoint finding 4): reference complex 1S0R → 1V2L**; prior 1S0R record (bovine trypsin–benzamidine, atomic resolution; BEN confirmed 2026-09-26; paper DOI none recorded — honest absence; title VERIFIED "Bovine Pancreatic Trypsin inhibited with Benzamidine at Atomic resolution") stays in git history | PLIP (doi:10.1093/nar/gkaf361) reference complex 1V2L | as-recorded — **PHYSIOLOGICAL: benzamidinium +1** (99.993% protonated at pH 7.4; pKaH1 **11.6** @ 20 °C from the IUPAC Digitized pKa Dataset, record `perrin671` — the exact dataset PubChem annotates for benzamidine). **Amended 2026-10-05, human decision "2 go R1-R8"** (08.1-08 audit row 5/R4; directive "per our spec we want to assume physiological pH normally"): was CID 2332 neutral free base (Charge 0 per approved C3); the charged alternate CID 444655 is now the SUBSTITUTED form. **MISLABEL FIX (same amendment): this document previously called CID 444655 "benzamidinium chloride" — it is the BARE benzamidinium cation C7H9N2⁺** (PubChem IUPAC name `[amino(phenyl)methylidene]azanium`, single component, no counterion — audit §6 finding); the CID was right, the prose was wrong. Typing: amidinium +1 types `+` via the formal-charge branch — hard-1's SECOND `+` carrier beside guanidinium (additive). Neutral CID 2332 record stays in git history | no / no | d468c24a1b37 | 2026-09-26 (ligand re-fetched 2026-10-05) |
| guanidinium | ligands/demo-hard-1-guanidinium.sdf | guanidinium (CH6N3+, 4 heavy, +1) | https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/32838/SDF?record_type=3d | CID 32838 | 5NWQ (Thermobifida fusca guanidine III riboswitch + guanidine; GAI confirmed 2026-09-26 — note CCD GUN = GUANINE, recorded pitfall) · entry DOI https://doi.org/10.2210/pdb5nwq/pdb · paper DOI https://doi.org/10.1016/j.chembiol.2017.08.021 (resolves 200) | PLIP (doi:10.1093/nar/gkaf361) reference complex 5NWQ | as-recorded — the cation (+1) CHOSEN over neutral guanine/guanidine bases deliberately: the salt-bridge + ligand-cation carrier (its C(N)₃ group exercises the 02-06 guanidino-centroid law) | no / no | 709a650d6a80 | 2026-09-26 |

### demo-hard-2 — "Charged messengers" (tier: hard)

- **Rationale:** the most-recognized neurotransmitter amino acid beside the permanently
  charged quaternary messenger — a deliberate uncharged-vs-charged nitrogen contrast
  (08-PROPOSALS.md Set 5).
- **License:** `Public domain (NCBI PubChem)` (matches MANIFEST.json verbatim); complex
  reference metadata `CC0 1.0 (wwPDB)` (quotes in §1).
- **Cross-ref:** counts/sha256 pinned in `aamatch/data/MANIFEST.json`; regenerate via
  `python3.6 scripts/build_demos.py --spec scripts/demo_specs/demo-hard-2.json --fetch`.

| entry_id | file | molecule | source (fetch URL) | ID | PDB complex (ID + entry DOI + paper DOI) | interaction provenance | protonation ('as-recorded' + why) | halogen/metal | sha256 | fetched |
|---|---|---|---|---|---|---|---|---|---|---|
| glutamic_acid | ligands/demo-hard-2-glutamic_acid.sdf | L-glutamate zwitterion, (2S)-2-azaniumylpentanedioate (C5H8NO4⁻, 10 heavy, net −1: COO⁻ ×2 + NH₃⁺) | https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/5460299/SDF?record_type=3d | CID 5460299 | 2JFO (Enterococcus faecalis glutamate racemase with D- and L-glutamate; GLU confirmed 2026-09-26 — hits 2CT6/1J0F rejected, no nonpolymer GLU) · entry DOI https://doi.org/10.2210/pdb2jfo/pdb · paper DOI https://doi.org/10.1038/nature05689 (resolves 200) | PLIP (doi:10.1093/nar/gkaf361) reference complex 2JFO | as-recorded — **PHYSIOLOGICAL: L-glutamate zwitterion, net −1** (both carboxylates ~100% deprotonated: pK1 2.19 / pK2 4.25; α-NH₃⁺ 99.5%: pK3 9.67 — Merck 2013 via the CID 33032 record). **Amended 2026-10-05, human decision "2 go R1-R8"** (08.1-08 audit row 7/R5; directive "per our spec we want to assume physiological pH normally"): was CID 33032 neutral free acid (Charge 0 per approved C3; the Decision-5-parallel "zwitterion not synthesized" policy is superseded by the verified stereo-explicit 3D route — (2S) preserved). **Rejected candidates: 5128032 (wrong bare dianion, neutral N) and 4525487 (stereo-unspecified twin) — do NOT use.** Typing: the zwitterion types BOTH salt-bridge signs (`−` via the two carboxylates; `+` via the α-NH₃⁺ — formal-charge AND structural ammonium branches) — was "this set's salt-bridge slot is acetylcholine". Neutral CID 33032 record stays in git history | no / no | c846665122e7 | 2026-09-26 (ligand re-fetched 2026-10-05) |
| acetylcholine | ligands/demo-hard-2-acetylcholine.sdf | acetylcholine (C7H16NO2+, 10 heavy, +1) | https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/187/SDF?record_type=3d | CID 187 | 9E3E (Torpedo nicotinic acetylcholine receptor, diliganded; ACH confirmed 2026-09-26 — eight higher-ranked hits lacked ACH) · entry DOI https://doi.org/10.2210/pdb9e3e/pdb · paper DOI https://doi.org/10.1126/science.adw1264 (VERIFIED at RCSB record; human-verified via PDB website) | PLIP (doi:10.1093/nar/gkaf361) reference complex 9E3E | as-recorded — permanently charged quaternary ammonium (+1); no pKa choice exists. The DEFAULT approved pick over the imidazolium (CID 444234) / tetramethylammonium (CID 6380) alternates, NOT substituted | no / no | 4d0e29a7fff0 | 2026-09-26 |

### demo-hard-3 — "Cofactors" (tier: hard)

- **Rationale:** energy currency + redox cofactor — the bundle's first medium
  (≥ 25 heavy atoms) ligands, anchoring the cofactor-recognition curriculum
  (08-PROPOSALS.md Set 6).
- **License:** `Public domain (NCBI PubChem)` (matches MANIFEST.json verbatim); complex
  reference metadata `CC0 1.0 (wwPDB)` (quotes in §1).
- **Cross-ref:** counts/sha256 pinned in `aamatch/data/MANIFEST.json`; regenerate via
  `python3.6 scripts/build_demos.py --spec scripts/demo_specs/demo-hard-3.json --fetch`.

| entry_id | file | molecule | source (fetch URL) | ID | PDB complex (ID + entry DOI + paper DOI) | interaction provenance | protonation ('as-recorded' + why) | halogen/metal | sha256 | fetched |
|---|---|---|---|---|---|---|---|---|---|---|
| atp | ligands/demo-hard-3-atp.sdf | ATP, adenosine 5′-triphosphate (C10H16N5O13P3, 31 heavy, medium) | https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/5957/SDF?record_type=3d | CID 5957 | 5IT5 (Thermus thermophilus PilB ATPase core with ATP; ATP confirmed 2026-09-26 — AGS/MG/ZN scene ions also present) · entry DOI https://doi.org/10.2210/pdb5it5/pdb · paper DOI https://doi.org/10.1016/j.str.2016.08.010 (resolves 200) | PLIP (doi:10.1093/nar/gkaf361) reference complex 5IT5 | as-recorded — neutral as registered; real ATP at pH 7 is ~4− and is explicitly NOT modeled (approved Decision 1). Honest limitation: ligand phosphates are NOT charge-typed (capability.py / DETECT-04 parity), so no salt bridge for this entry | no / no | f1ed29266c93 | 2026-09-26 |
| nad | ligands/demo-hard-3-nad.sdf | NAD, nicotinamide adenine dinucleotide (C21H27N7O14P2, 44 heavy, medium) | https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/5892/SDF?record_type=3d | CID 5892 | 8HBA (NAD-II riboswitch with NAD; NAD confirmed 2026-09-26 — NMN also present) · entry DOI https://doi.org/10.2210/pdb8hba/pdb · paper DOI https://doi.org/10.1093/nar/gkad102 (VERIFIED at RCSB record; human-verified via PDB website) | PLIP (doi:10.1093/nar/gkaf361) reference complex 8HBA | as-recorded — neutral (charge-0 record); pyrophosphate not charge-typed (same DETECT-04 parity law as ATP) | no / no | 78128bef6f69 | 2026-09-26 |

### demo-challenge-1 — "Halogen & alkaloids" (tier: challenge)

- **Rationale:** antibiotic with the dichloroacetyl motif (the bundle's halogen debut —
  first real-data exercise of the 02-07b halogen branch) beside the alkaloid archetype
  (quinuclidine-cage hydrophobe) (08-PROPOSALS.md Set 7).
- **License:** `Public domain (NCBI PubChem)` (matches MANIFEST.json verbatim); complex
  reference metadata `CC0 1.0 (wwPDB)` (quotes in §1).
- **Cross-ref:** counts/sha256 pinned in `aamatch/data/MANIFEST.json`; regenerate via
  `python3.6 scripts/build_demos.py --spec scripts/demo_specs/demo-challenge-1.json --fetch`.

| entry_id | file | molecule | source (fetch URL) | ID | PDB complex (ID + entry DOI + paper DOI) | interaction provenance | protonation ('as-recorded' + why) | halogen/metal | sha256 | fetched |
|---|---|---|---|---|---|---|---|---|---|---|
| chloramphenicol | ligands/demo-challenge-1-chloramphenicol.sdf | chloramphenicol (C11H12Cl2N2O5, 20 heavy) | https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/5959/SDF?record_type=3d | CID 5959 | 4CLA (chloramphenicol acetyltransferase–chloramphenicol, the resistance-enzyme complex; CLM confirmed 2026-09-26) · entry DOI https://doi.org/10.2210/pdb4cla/pdb · paper DOI https://doi.org/10.1021/bi00229a025 (VERIFIED at RCSB record; human-verified via PDB website) | PLIP (doi:10.1093/nar/gkaf361) reference complex 4CLA | as-recorded — neutral (Charge 0). Halogen debut: 2× C–Cl donors (Cl in the approved donor list; C–F excluded per DETECT-03) | **yes (Cl ×2)** / no | 9145d94a48e2 | 2026-09-26 |
| quinine | ligands/demo-challenge-1-quinine.sdf | quinuclidinium quinine (C20H25N2O2⁺, 24 heavy, +1) | https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/6999115/SDF?record_type=3d | CID 6999115 | 4WNV (Human Cytochrome P450 2D6 Quinine Complex — a PROTEIN target; human ruled 9NDX's RNA aptamer the wrong reference class for an amino-acid game; QI9 'Quinine' confirmed in the RCSB nonpolymer inventory via the data API, 2026-10-04 — HEM also present as entity 2, plus GOL/ZN/NA) · entry DOI https://doi.org/10.2210/pdb4wnv/pdb (resolves) · paper DOI https://doi.org/10.1074/jbc.M114.627661 (resolves; CrossRef title "Contributions of Ionic Interactions and Protein Dynamics to Cytochrome P450 2D6 (CYP2D6) Substrate and Inhibitor Binding" — Wang, Stout, Zhang, JBC 2015 — matches the RCSB primary citation exactly) · **Amended 2026-10-04 by human directive (08.1-08 checkpoint finding 4): reference complex 9NDX → 4WNV**; prior 9NDX record (quinine-binding RNA aptamer "Tonic"; QI9 confirmed 2026-09-26) stays in git history. NOTE: 4WNV's HEM inventory also makes it the reference complex for the heme row below — **APPLIED 2026-10-04 by human directive** (08.1-08 checkpoint fix-batch 2; was HELD AS PROPOSAL in the prior fix-batch record) | PLIP (doi:10.1093/nar/gkaf361) reference complex 4WNV | as-recorded — **PHYSIOLOGICAL: quinuclidinium +1** (93.5% at pH 7.4 via pKa 8.56, PubChem AID 781325/781326 SID 103401549; 89.7% via pKaH 8.34 IUPAC `perrin2958` @ 20 °C; Merck pK1 5.07 quinoline N / pK2 9.7). **Amended 2026-10-05, human decision "2 go R1-R8, 3 +1" — the "3 +1" clause is the EXPLICIT +1-cation choice for this marginal row** (the audit had listed quinine as HUMAN-TO-DECIDE: cation 93.5% vs neutral; audit row 12/R8): was CID 3034034 neutral free base (quinuclidine N unprotonated as registered, counts 48/51). The substituted CID 6999115 is the **bare cation, stereo pattern identical to the shipped natural quinine** (IUPAC-name comparison receipt, audit §5); quinine salts (e.g. CID 91558 quinine hydrochloride) REJECTED per the one-bare-species-per-file law. Typing: the quinuclidinium NH⁺ types `+` (formal-charge AND structural ammonium branches) — challenge-1 gains a `+` salt-bridge carrier; the halogen flag-contrast vs chloramphenicol is UNCHANGED (that is the teaching pair). Neutral CID 3034034 record stays in git history | no / no (the set's deliberate flag contrast) | a7ab6e92ec99 | 2026-09-26 (ligand re-fetched 2026-10-05) |

### demo-veryhard-1 — "Big & iodinated" (tier: very challenging)

- **Rationale:** the vitamin (32 heavy, medium) atop two coplanar-ish ring systems beside
  the iodine halogen stress case — four C–I donors in one ligand (08-PROPOSALS.md Set 8).
- **License:** `Public domain (NCBI PubChem)` (matches MANIFEST.json verbatim); complex
  reference metadata `CC0 1.0 (wwPDB)` (quotes in §1).
- **Cross-ref:** counts/sha256 pinned in `aamatch/data/MANIFEST.json`; regenerate via
  `python3.6 scripts/build_demos.py --spec scripts/demo_specs/demo-veryhard-1.json --fetch`.

| entry_id | file | molecule | source (fetch URL) | ID | PDB complex (ID + entry DOI + paper DOI) | interaction provenance | protonation ('as-recorded' + why) | halogen/metal | sha256 | fetched |
|---|---|---|---|---|---|---|---|---|---|---|
| folic_acid | ligands/demo-veryhard-1-folic_acid.sdf | folate, C19H17N7O6²⁻ (32 heavy, medium, −2) | https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/135761165/SDF?record_type=3d | CID 135761165 | 4KMZ (human folate receptor β (FOLR2)–folate; FOL confirmed 2026-09-26; K/Cl ions also present) · entry DOI https://doi.org/10.2210/pdb4kmz/pdb · paper DOI https://doi.org/10.1073/pnas.1308827110 (VERIFIED at RCSB record; human-verified via PDB website) | PLIP (doi:10.1093/nar/gkaf361) reference complex 4KMZ | as-recorded — **PHYSIOLOGICAL: folate ²−** (glutamyl-tail carboxylates deprotonated; pKa 3.5/4.3 — */Estimated/ SPARC*, Hilal et al. 1994, via the CID record; estimated values honestly labeled, but the dianion conclusion is robust since both pKas sit far below pH 7.4). **Amended 2026-10-05, human decision "2 go R1-R8"** (08.1-08 audit row 13/R6; directive "per our spec we want to assume physiological pH normally"): was CID 135398658 neutral as registered (tail COOHs not salt-bridge-typed, the Decision-5-parallel policy — superseded by the verified 3D route); (2S) stereo preserved. Typing: gains `−` via the two carboxylates; a pre-existing structural `+` (pterin C bonded to 3 N — capability's guanidino pattern) is unchanged by the swap. Neutral CID 135398658 record stays in git history | no / no | 5a654975379b | 2026-09-26 (ligand re-fetched 2026-10-05) |
| thyroxine | ligands/demo-veryhard-1-thyroxine.sdf | thyroxine zwitterion, LT4 (C15H11I4NO4, 24 heavy, net 0: COO⁻ + NH₃⁺) | https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/25201348/SDF?record_type=3d | CID 25201348 | 2RIW (reactive-loop-cleaved human thyroxine-binding globulin + thyroxine; T44 confirmed 2026-09-26, CCD name 3,5,3′,5′-TETRAIODO-L-THYRONINE) · entry DOI https://doi.org/10.2210/pdb2riw/pdb · paper DOI https://doi.org/10.1074/jbc.M110.171082 (resolves 200) | PLIP (doi:10.1093/nar/gkaf361) reference complex 2RIW | as-recorded — **PHYSIOLOGICAL: L-thyroxine zwitterion** (COO⁻/NH₃⁺, net 0 via M CHG [−1,+1]; evidence: HSDB sections in the CID 5819 record — */Estimated/ pKa 7.43 and 9.43*, "levothyroxine will exist in the zwitterion form … at pH values of 5 to 9", ×3 annotations; the shipped free-acid/amine form was no physiological microstate). **Amended 2026-10-05, human decision "2 go R1-R8"** (08.1-08 audit row 14/R7; directive "per our spec we want to assume physiological pH normally"): was CID 5819 neutral as registered (head NH₂ + COOH). The phenolic pKa ~7.43 sits at the pH-7.4 edge — the chosen state is phenol (OH RETAINED), with the ~50% phenolate (net −1) microstate honestly recorded as coexisting (audit §6 caveat). Typing: gains BOTH signs (`−` carboxylate + `+` α-NH₃⁺); 24 heavy — one below the SIZE_S1=25 boundary, small bucket unchanged; the 4× C–I halogen case is UNCHANGED. Free-acid CID 5819 record stays in git history | **yes (I ×4)** / no | ada5a8420cff | 2026-09-26 (ligand re-fetched 2026-10-05) |

### demo-veryhard-2 — "Metalloporphyrin" (tier: very challenging)

- **Rationale:** the metal-coordination showcase — first real-data exercise of the whole
  02-07b metal branch (in-molecule Fe; a lone metal ion as ligand is DESIGN-REJECTED per
  sourcing RQ7 item 4 — degenerate bounding sphere); porphyrin = the archetypal biological
  macrocycle (08-PROPOSALS.md Set 9).
- **License:** `CC0 1.0 (wwPDB)` (matches MANIFEST.json verbatim — the bundle's only
  non-PubChem set-level license; CCD ideal files are PDB-archive data) —
  https://www.wwpdb.org/about/usage-policies (quote in §1).
- **Cross-ref:** counts/sha256 pinned in `aamatch/data/MANIFEST.json`; regenerate via
  `python3.6 scripts/build_demos.py --spec scripts/demo_specs/demo-veryhard-2.json --fetch`.

| entry_id | file | molecule | source (fetch URL) | ID | PDB complex (ID + entry DOI + paper DOI) | interaction provenance | protonation ('as-recorded' + why) | halogen/metal | sha256 | fetched |
|---|---|---|---|---|---|---|---|---|---|---|
| heme | ligands/demo-veryhard-2-heme.sdf | heme, protoporphyrin IX–Fe (C34H32FeN4O4, 43 heavy, medium) | https://files.rcsb.org/ligands/view/HEM_ideal.sdf (plain `.sdf` 404s — `_ideal` required, research-verified; header name line 'HEM' per approved C7) | CCD HEM | 4WNV (Human Cytochrome P450 2D6 Quinine Complex — HEM carried as nonpolymer entity 2, "PROTOPORPHYRIN IX CONTAINING FE"; RCSB data API 2026-10-04) · entry DOI https://doi.org/10.2210/pdb4wnv/pdb (resolves) · paper DOI https://doi.org/10.1074/jbc.M114.627661 (resolves; matches the RCSB primary citation). **Amended 2026-10-04 by human directive (08.1-08 checkpoint fix-batch 2): reference complex 1MBN → 4WNV** — verbatim reasoning: "1mbn has a old ref w/o doi, but the xtal quality is low so better use 4wnv to be simple"; all three receipts re-verified live 2026-10-04 for this change. Prior 1MBN record (Kendrew's sperm-whale myoglobin; HEM confirmed 2026-09-26; paper DOI honestly absent, 1960 structure) stays in git history, never deleted | PLIP (doi:10.1093/nar/gkaf361) reference complex 4WNV | as-recorded — **MODIFIED from the RCSB HEM_ideal.sdf: 2 artifact hydrogens + their O–H bonds removed** (the source's own M CHG block marks those carboxylate oxygens deprotonated at −1 each; the artifact bonds measured 12.43 Å / 4.70 Å against the file's own charge model) — recorded 2026-10-04 per human approval (08.1-08 checkpoint fix-batch 2; verbatim: "yes drop the 2 H since its supposed to be deprotonated"); the removal is a recorded, reproducible post-fetch transform (`drop_artifact_OH_bonds`) in `scripts/build_demos.py`. Counts are now 73 atoms / 80 bonds {"1": 65, "2": 15} (was 75/82); heavy 43 unchanged; M CHG untouched so formal charge −4 preserved; Fe/metal flag unaffected — no DETECTOR_VERSION event. CHARGE DELTA RECORDED 2026-09-26 (08-07 narrative fix): the proposal's "(…charge field 0)" parenthetical does NOT match the file — M CHG sums to −4 (builder-derived and SMOKE-02/PyMOL-agreed) | no / **yes (Fe ×1 — FE in the DETECT-03 approved metal list)** | 89210c9bb6d5 | 2026-09-26 |

### demo-dev-1 — "Phase-2 development set" (tier: easy) — DEVELOPMENT FIXTURE, NOT curated demo data

- **Rationale:** script-built regression oracle (02-04 fixtures; `test_demo_data.py` battery
  and the `--report-only` dry-run). It remains in the manifest and the dropdown under Easy
  per approved Decision 3; it is **not** part of the curated supply.
- **License:** `''` (empty string, matches MANIFEST.json verbatim) — **placeholder by
  design**: the set-level `license`/`provenance {}` fields are Phase-2 placeholders (02-04
  law). No external content is redistributed by this set; both fixtures are generated in-repo
  by script, so no external license applies.
- **Cross-ref:** counts/sha256 pinned in `aamatch/data/MANIFEST.json`; regenerate via
  `python3.6 scripts/build_demos.py --spec scripts/demo_specs/demo-dev-1.json --fetch` (local
  files, no network) — never hand-edit an SDF or the manifest (02-04 law).

| entry_id | file | molecule | source (fetch URL) | ID | PDB complex (ID + entry DOI + paper DOI) | interaction provenance | protonation ('as-recorded' + why) | halogen/metal | sha256 | fetched |
|---|---|---|---|---|---|---|---|---|---|---|
| benzamide | ligands/benzamide.sdf | benzamide (9 heavy) | — (script-built by 02-04's `tmp/build_fixtures.py`, git-ignored; no download source) | — | — (development fixture — no curated complex provenance) | — (not a PLIP-anchored entry) | as-recorded (script-built; manifest-derived counts, charge 0) | no / no | 319b964abadc | — (script-built 2026-09-06, Phase 2) |
| acetate | ligands/acetate.sdf | acetate (4 heavy, −1) | — (same script-built provenance as above; legacy name kept by spec `file` override to avoid colliding with curated demo-easy-2-acetate.sdf) | — | — (development fixture) | — | as-recorded (script-built; charge −1) | no / no | 9ea6ba6390c0 | — (script-built 2026-09-06, Phase 2) |

---

## 3. Multi-state & ions policy (ratified RQ7 — approved Decision 1, 2026-09-26)

- **One molecule record per SDF file, by construction.** Every bundled file carries exactly
  ONE record (`states_expected: 1` in the manifest; the bundler REFUSES any multi-record
  source naming the entry — split or choose at curation, never collapse silently;
  `cmd.count_states == 1` is asserted at every ligand load, engine.py / placement.py).
  All 16 curated candidates were verified single-record at approval time (one `$$$$` each).
- **Protonation chosen at PROPOSAL time, per candidate.** The ionization state was picked
  deliberately and the *why* recorded per row in §2 (e.g., acetate anion CID 175 chosen
  over acetic acid; guanidinium +1 chosen over neutral bases; citrate as free acid per
  Decision 5). The manifest string stays `'as-recorded'` (dev precedent); the why lives in
  this document, not the schema.
- **Ions are scene context, never ligand content.** Separate components (e.g., 1OXR's
  crystallographic Ca²⁺, 5IT5's AGS/MG/ZN) are never merged into a ligand SDF; they may
  appear in a cleanup-demo scene as non-game objects only.
- **Lone-ion ligands are rejected.** A single metal ion as a "ligand" has a degenerate
  bounding sphere and grid; metal coordination is showcased via heme's in-molecule Fe.
- **Altloc/occupancy filtering is out of scope for v1** (ready-made SDFs carry no altlocs;
  PDB extraction is not the sourcing route).

---

## 4. Not-bundled acknowledgements (recorded, not shipped)

- **DrugBank (CC BY-NC 4.0).** DrugBank data surfaces on RCSB ligand pages (seen on the
  fetched ATP ligand page). It is **informational only — NOT our license, and nothing from
  DrugBank is bundled or cited as provenance** in this repository. (Recorded per 08-04
  research RQ5 flag.)
- **PDBsum (currently unavailable).** PDBsum's own EBI page (fetched 2026-09-24) states:
  "PDBsum is currently unavailable due to issues with the web server, and likely to remain
  so for the foreseeable future. Please use other services such as PDBe."
  (https://www.ebi.ac.uk/thornton-srv/databases/pdbsum/). Provenance is therefore anchored
  on RCSB records + PLIP (and PDBe as the secondary link), never on PDBsum — an
  unexecutable anchor would make this document untruthful.
- **Context complexes are NOT shipped** (approved Decision 8): PDB complex files for the
  game scene are outside the frozen manifest format and have no runtime consumer; they are
  cited here as provenance only. The messy-scene cleanup field test uses a LOCAL
  script-built ions+water fixture (headless-deterministic), with **1OXR** cited as the
  real-world analog (its crystallographic Ca²⁺ demonstrates that prefix-scoped cleanup
  never touches non-game objects; 1S0R's CA ion is a second analog).
