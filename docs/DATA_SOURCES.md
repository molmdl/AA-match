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
not an omission to invent** (approved rows: 8FUY, 1S0R, 9NDX, 1MBN).

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
| aspirin | ligands/demo-easy-1-aspirin.sdf | aspirin (C9H8O4, 13 heavy) | https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/2244/SDF?record_type=3d | CID 2244 | 1OXR (phospholipase A2–aspirin·Ca²⁺; AIN confirmed in nonpolymer inventory 2026-09-26) · entry DOI https://doi.org/10.2210/pdb1oxr/pdb · paper DOI https://doi.org/10.1080/10611860400024078 (VERIFIED at RCSB record; human-verified via PDB website) | PLIP (doi:10.1093/nar/gkaf361) reference complex 1OXR | as-recorded — neutral free acid (Charge 0 as registered); capability's COOH-never-anion guard means the carboxyl is not salt-bridge-typed | no / no | 958bdc9d8071 | 2026-09-26 |
| benzoic_acid | ligands/demo-easy-1-benzoic_acid.sdf | benzoic acid (C7H6O2, 9 heavy) | https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/243/SDF?record_type=3d | CID 243 (approved correction C1: research's 3979 is a different compound; human accepted "1 ok") | 5E4D (hydroxynitrile lyase–benzoic acid; BEZ confirmed in inventory 2026-09-26) · entry DOI https://doi.org/10.2210/pdb5e4d/pdb · paper DOI https://doi.org/10.1038/srep46738 (resolves 200) | PLIP (doi:10.1093/nar/gkaf361) reference complex 5E4D | as-recorded — neutral free acid (Charge 0 per approved C3); the charged benzoate anion (−1, CID 242) is an approved alternate, NOT substituted | no / no | f188caa88593 | 2026-09-26 |

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
| citric_acid | ligands/demo-easy-2-citric_acid.sdf | citric acid (C6H8O7, 13 heavy) | https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/311/SDF?record_type=3d | CID 311 | 8FUY (Crithidia fasciculata G6PDH, citrate bound; CIT confirmed 2026-09-26 — research's top hit 1O7X rejected: no nonpolymer entities, correction C5) · entry DOI https://doi.org/10.2210/pdb8fuy/pdb · paper DOI **— (none recorded in the RCSB data — honest absence)** | PLIP (doi:10.1093/nar/gkaf361) reference complex 8FUY | as-recorded — free acid CHOSEN per approved Decision 5 (deprotonated-citrate sourcing REJECTED for v1 — only a 2D ChEBI route exists); COOH-never-anion guard ⇒ its carboxylates are not salt-bridge-typed; the set's salt-bridge slot is acetate | no / no | 121c21362fbc | 2026-09-26 |
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
| benzamidine | ligands/demo-hard-1-benzamidine.sdf | benzamidine (C7H8N2, 9 heavy) | https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/2332/SDF?record_type=3d | CID 2332 | 1S0R (bovine trypsin–benzamidine, atomic resolution; BEN confirmed 2026-09-26) · entry DOI https://doi.org/10.2210/pdb1s0r/pdb · paper DOI **— (none recorded in the RCSB data — honest absence; title VERIFIED "Bovine Pancreatic Trypsin inhibited with Benzamidine at Atomic resolution")** | PLIP (doi:10.1093/nar/gkaf361) reference complex 1S0R | as-recorded — neutral free base (Charge 0 as registered, approved C3); in the trypsin pocket benzamidine is protonated, but no charged form is invented — the charged benzamidinium chloride (CID 444655, +1) is an approved alternate, NOT substituted | no / no | 484b30982d94 | 2026-09-26 |
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
| glutamic_acid | ligands/demo-hard-2-glutamic_acid.sdf | L-glutamic acid (C5H9NO4, 10 heavy) | https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/33032/SDF?record_type=3d | CID 33032 | 2JFO (Enterococcus faecalis glutamate racemase with D- and L-glutamate; GLU confirmed 2026-09-26 — hits 2CT6/1J0F rejected, no nonpolymer GLU) · entry DOI https://doi.org/10.2210/pdb2jfo/pdb · paper DOI https://doi.org/10.1038/nature05689 (resolves 200) | PLIP (doi:10.1093/nar/gkaf361) reference complex 2JFO | as-recorded — neutral free acid (Charge 0 as registered, approved C3); physiological zwitterion deliberately NOT synthesized (parallel policy to citrate, Decision 5); this set's salt-bridge slot is acetylcholine | no / no | d30a909cad9f | 2026-09-26 |
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
| quinine | ligands/demo-challenge-1-quinine.sdf | quinine (C20H24N2O2, 24 heavy) | https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/3034034/SDF?record_type=3d | CID 3034034 | 9NDX (quinine-binding RNA aptamer "Tonic"; QI9 confirmed 2026-09-26, CCD name Quinine) · entry DOI https://doi.org/10.2210/pdb9ndx/pdb · paper DOI **— (none recorded in the RCSB data — honest absence)** | PLIP (doi:10.1093/nar/gkaf361) reference complex 9NDX | as-recorded — neutral free base (quinuclidine N unprotonated as registered) | no / no (the set's deliberate flag contrast) | 3e43700d0924 | 2026-09-26 |

### demo-veryhard-1 — "Big & iodinated" (tier: very challenging)

- **Rationale:** the vitamin (32 heavy, medium) atop two coplanar-ish ring systems beside
  the iodine halogen stress case — four C–I donors in one ligand (08-PROPOSALS.md Set 8).
- **License:** `Public domain (NCBI PubChem)` (matches MANIFEST.json verbatim); complex
  reference metadata `CC0 1.0 (wwPDB)` (quotes in §1).
- **Cross-ref:** counts/sha256 pinned in `aamatch/data/MANIFEST.json`; regenerate via
  `python3.6 scripts/build_demos.py --spec scripts/demo_specs/demo-veryhard-1.json --fetch`.

| entry_id | file | molecule | source (fetch URL) | ID | PDB complex (ID + entry DOI + paper DOI) | interaction provenance | protonation ('as-recorded' + why) | halogen/metal | sha256 | fetched |
|---|---|---|---|---|---|---|---|---|---|---|
| folic_acid | ligands/demo-veryhard-1-folic_acid.sdf | folic acid (C19H19N7O6, 32 heavy, medium) | https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/135398658/SDF?record_type=3d | CID 135398658 | 4KMZ (human folate receptor β (FOLR2)–folate; FOL confirmed 2026-09-26; K/Cl ions also present) · entry DOI https://doi.org/10.2210/pdb4kmz/pdb · paper DOI https://doi.org/10.1073/pnas.1308827110 (VERIFIED at RCSB record; human-verified via PDB website) | PLIP (doi:10.1093/nar/gkaf361) reference complex 4KMZ | as-recorded — neutral as registered; tail COOHs not salt-bridge-typed (same free-acid policy, Decision 5) | no / no | 95eb0e4060d8 | 2026-09-26 |
| thyroxine | ligands/demo-veryhard-1-thyroxine.sdf | thyroxine, LT4 (C15H11I4NO4, 24 heavy) | https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/5819/SDF?record_type=3d | CID 5819 | 2RIW (reactive-loop-cleaved human thyroxine-binding globulin + thyroxine; T44 confirmed 2026-09-26, CCD name 3,5,3′,5′-TETRAIODO-L-THYRONINE) · entry DOI https://doi.org/10.2210/pdb2riw/pdb · paper DOI https://doi.org/10.1074/jbc.M110.171082 (resolves 200) | PLIP (doi:10.1093/nar/gkaf361) reference complex 2RIW | as-recorded — neutral as registered (head NH₂ + COOH; zwitterion not synthesized — same free-acid policy) | **yes (I ×4)** / no | 3a7e110e519a | 2026-09-26 |

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
| heme | ligands/demo-veryhard-2-heme.sdf | heme, protoporphyrin IX–Fe (C34H32FeN4O4, 43 heavy, medium) | https://files.rcsb.org/ligands/view/HEM_ideal.sdf (plain `.sdf` 404s — `_ideal` required, research-verified; header name line 'HEM' per approved C7) | CCD HEM | 1MBN (Kendrew's sperm-whale myoglobin — the heme classic; HEM confirmed 2026-09-26) · entry DOI https://doi.org/10.2210/pdb1mbn/pdb · paper DOI **— (none recorded in the RCSB data — 1960 structure, honest absence)** | PLIP (doi:10.1093/nar/gkaf361) reference complex 1MBN | as-recorded — the RCSB ideal SDF as published. CHARGE DELTA RECORDED 2026-09-26 (08-07 narrative fix): the proposal's "(…charge field 0)" parenthetical does NOT match the file — the ideal SDF carries M CHG annotations summing to formal charge −4 (builder-derived and SMOKE-02/PyMOL-agreed); counts/atoms/flags/identity match the approved row exactly, and the file ships as-recorded | no / **yes (Fe ×1 — FE in the DETECT-03 approved metal list)** | 414ee8fbc00b | 2026-09-26 |

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
