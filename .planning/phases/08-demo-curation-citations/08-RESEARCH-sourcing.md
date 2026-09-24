# Phase 8: Demo Curation & Citations — Sourcing Research

**Researched:** 2026-09-24 (all web fetches this date)
**Domain:** Demo-content sourcing — candidate molecules, download URLs, provenance databases, licenses, DOIs, multi-state policy, propose→approve→fetch/commit protocol
**Confidence:** HIGH for licenses/URL patterns/engine laws; MEDIUM for candidate chemistry classification (see §2 method note); LOW/UNVERIFIED items explicitly flagged inline

---

## Summary

This research answers three things: **(1) what fills the ~9 tier slots, (2) what sources/licenses/DOIs make DATA_SOURCES.md truthful, (3) what artifacts the propose → approve → fetch/commit protocol needs.**

**Sources are fully verified and benign.** PDB data is CC0 1.0 (wwPDB usage policy, fetched verbatim) and PubChem data carries no NCBI use/distribution restriction (NCBI policy page + PubChem FTP Fair Use Disclaimer, both fetched). ChEBI is CC BY 4.0 (fetched). Every needed download URL pattern was fetched live and works: RCSB ligand ideal SDF (`files.rcsb.org/ligands/view/<CCD>_ideal.sdf`), PubChem 3D conformer SDF (`.../cid/<CID>/SDF?record_type=3d`), the RCSB search API and Data API. PDB entry DOIs (`10.2210/pdbXXXX/pdb`) resolve via doi.org (proven with 1OXR).

**The large-bucket reality check is the main design surprise.** PubChem 3D conformers exist for essentially all classic small/medium teaching ligands (aspirin 13 heavy atoms … NAD 44 heavy), but the three tested large candidates (vancomycin ~101, cyclosporin A ~85, FAD 53 heavy) have **no PubChem 3D conformer** (404s). The generator's NEAREST-BUCKET supply fallback (verified in `aamatch/generator.py` `_select_pool`) is therefore not a corner case — it is the designed carrier for large-bucket games, and the curated set should lean on medium molecules (NAD, ATP, folic acid, heme) as the "big" supply. This is honest and works by construction; a true ≥60-heavy ligand remains a GATE-time stretch option.

**Provenance anchor: PLIP, not PDBsum.** PLIP is live and verified (PDB-ID input, atom-level protein–ligand interactions, parsable output; citation doi:10.1093/nar/gkaf361) — and its threshold names are exactly what the 02-01 detector gate doc already cites, giving internal precedent. **PDBsum is verified-unavailable** (its own EBI page says so and points to PDBe). The per-candidate provenance record should be: PDB complex ID (found via the verified RCSB search API) + PLIP/PDBe analysis of that entry + the structure paper DOI + the entry DOI.

**Primary recommendation:** Bundle ready-made single-record SDFs (PubChem 3D for free ligands; RCSB ideal SDF for the heme metal case) — no format conversion of any kind, satisfying the zero-extra-deps constraint. Run the GATE proposal plan early (after bundling machinery + 1–2 trial sets), with per-candidate fetched-URL evidence inline, and record human approval in STATE.md (DETECT-03 precedent) before any fetch/commit.

---

## RQ1 — Tier-slot content design

### Tier philosophy (derived from game mechanics; repo-verified mechanics, chemistry judgment marked ANALYSIS)

Difficulty in AA-match = grid N + size_class + count of required interaction types (`aamatch/generator.py`: `grid_n = 3+frac`, `n_required_types = 1+frac`; SIZE buckets `SIZE_S1=25`, `SIZE_S2=60` heavy atoms — VERIFIED in code). Tier fit therefore maps to:

| Tier slot (count) | size_class aim | required-type spread | chemistry character |
|---|---|---|---|
| Easy ×3 | small | 1–2 types | classic single-motif teaching molecules |
| Hard ×3 | small→medium | 3–4 types | two-motif + charged species (salt bridge, cation-π) |
| Challenge ×1 | small→medium | 4–5 types | **halogen debut** (rare type), mixed set |
| Very challenging ×2 | medium (+ documented large fallback) | 5–6 types | metal (Fe), multi-ring large ligands |

### The 7-type coverage target (ANALYSIS — from capability.py typing rules)

Across the ~9 sets, every one of the 7 interaction types must be showcased at least once (GEN-06 diversity), and ≥1 metal-present + ≥1 halogen-present entry is the mechanics researcher's supply target (STATE.md 02-08 note). Mapping (typing rules from `aamatch/capability.py`, VERIFIED in code; per-molecule classification is ANALYSIS to be re-verified against the actual SDFs at bundling):

- **h_bond** — any ligand with O/N/S (+ donor where H-bonded): nearly all candidates
- **salt_bridge** — needs a *charged* group: acetate(−), benzoate(−), citrate(multi−), glutamate(−), guanidinium(+), imidazolium(+), tetramethylammonium(+), acetylcholine(+)
- **pi_stacking** — aromatic ring: aspirin, caffeine, benzoate, benzamidine, quinine, thyroxine, ATP (adenine), folic acid, NAD, heme (porphyrin)
- **cation_pi** — ligand-side cation (acetylcholine/guanidinium/imidazolium/TMA) under an AA ring, or an AA cation over a ligand ring (aromatic ligands)
- **hydrophobic** — all candidates (C/H content)
- **halogen** — ligand C–X donors only, X ∈ {Cl, Br, I} (C–F EXCLUDED per DETECT-03): **chloramphenicol (2×C–Cl), thyroxine (4×C–I)**, vancomycin (2×C–Cl, unverified 3D)
- **metal** — metal **in the ligand**: **heme (Fe)** — the only verified metal-bearing candidate

**Honest typing notes (recorded repo laws that constrain candidates):**
- Ligand **phosphate/sulfonate are NOT typed** as charge groups (STATE.md 02-06: DETECT-04 parity) → neutral ATP's phosphates give h_bond acceptors but **no salt bridge** in the neutral form; citrate/carboxylates do.
- **C–F is never a halogen donor** (02-01) → avoid fluoro-drugs as the halogen showcase; chlorinated/iodinated candidates are correct.
- Ligand **guanidino center = centroid of 3 bonded Ns** (02-06) → guanidinium(+) is a real-world test of that recorded rule and of the 02-07 ammonium-veto boundary (the veto applies to ammonium N with exactly 3 non-H substituents; guanidinium's charge is on the C(N₃) group).

### Size-class reality check (HIGH confidence — verified against live sources)

`small < 25 ≤ medium < 60 ≤ large` heavy atoms (generator.py). PubChem 3D conformer availability caps out around ~44 heavy atoms among tested candidates:

- small: aspirin 13, caffeine 14, benzoate 7, benzamidine 9, citrate 6, glutamate 5, acetate 2, guanidinium 4, imidazolium 3, TMA 5, acetylcholine 9, **chloramphenicol 20**, **quinine 24**, **thyroxine 21**
- medium: **ATP 31, folic acid 38, NAD 44, heme (HEM) 43**
- large (≥60): **no verified 3D source** — vancomycin ~101 (2D SDF only, 200 OK), cyclosporin A ~85 and FAD 53 (3D 404)

**Consequence:** the curated set provides a healthy small+medium supply and deliberately documents the NEAREST-BUCKET fallback for large-bucket games (generator-verified behavior; ties → smaller). A true ≥60-heavy candidate is a GATE stretch option (vancomycin 2D, or an RCSB large-CCD search at GATE time) — flagged, not required.

---

## RQ2 — Candidate molecules (verification status explicit)

**Method note:** "3D SDF" column = live HTTP fetch of `https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/<CID>/SDF?record_type=3d` on 2026-09-24 (200 = fetched). RCSB CCDs = live fetch of `https://files.rcsb.org/ligands/view/<CCD>_ideal.sdf`. Names verified via PubChem property endpoint. Interaction-type columns are ANALYSIS (from capability.py rules) pending bundling-time re-check against the actual SDF bytes.

### PubChem candidates (all property-verified via `.../cid/<CID>/property/.../JSON`)

| CID | Name | Formula (heavy atoms) | 3D SDF | Types it can showcase | halogen | metal | Tier fit |
|---|---|---|---|---|---|---|---|
| 2244 | Aspirin | C9H8O4 (13) | **200 ✓** | h_bond, pi_stacking, hydrophobic | no | no | Easy-1 |
| 3979 | Benzoic acid | C7H6O2 (7) | **200 ✓** | salt_bridge (as benzoate −1), pi_stacking, hydrophobic | no | no | Easy-1 alt |
| 311 | Citric acid | C6H8O7 (6) | **200 ✓** | salt_bridge (multi−), h_bond | no | no | Easy-2 |
| 175 | Acetate anion | C2H3O2− (2) | **200 ✓** | salt_bridge, h_bond | no | no | Easy-2 alt |
| 2519 | Caffeine | C8H10N4O2 (14) | **200 ✓** | h_bond (acceptor-only), pi_stacking, hydrophobic | no | no | Easy-3 |
| 2332 | Benzamidine | C7H8N2 (9) | **200 ✓** | cation_pi (+1 amidinium), h_bond, pi_stacking | no | no | Hard-1 |
| 32838 | Guanidinium | CH6N3+ (4) | property only (3D not fetched) | cation_pi, salt_bridge (as ligand cation) | no | no | Hard-1 alt |
| 33032 | Glutamic acid | C5H9NO4 (5) | **200 ✓** | salt_bridge (−1), h_bond, hydrophobic | no | no | Hard-2 |
| 444234 | Imidazolium cation | C3H5N2+ (3) | property only | cation_pi, h_bond | no | no | Hard-2 alt |
| 6380 | Tetramethylammonium | C4H12N+ (5) | property only | cation_pi (pure), salt_bridge | no | no | Hard-2 alt |
| 5957 | ATP | C10H16N5O13P3 (31) | **200 ✓** | h_bond (rich), pi_stacking (adenine), hydrophobic — **phosphate NOT salt-bridge-typed** | no | no | Hard-3 |
| 5892 | NAD (nadide) | C21H27N7O14P2 (44) | **200 ✓** | h_bond, pi_stacking (adenine + nicotinamide), hydrophobic | no | no | Hard-3 alt |
| 5959 | Chloramphenicol | C11H12Cl2N2O5 (20) | **200 ✓** | **halogen (C–Cl ×2)**, h_bond, nitro-aromatic pi | **yes (Cl2)** | no | Challenge |
| 3034034 | Quinine | C20H24N2O2 (24) | **200 ✓** | pi_stacking (quinoline), h_bond, hydrophobic | no | no | Challenge alt |
| 5819 | Thyroxine | C15H11I4NO4 (21) | **200 ✓** | **halogen (C–I ×4)**, pi_stacking, h_bond | **yes (I4)** | no | Very challenging-1 |
| 135398658 | Folic acid | C19H19N7O6 (38) | **200 ✓** | h_bond, pi_stacking (pterin + p-aminobenzoate), salt_bridge (carboxylates) | no | no | Very challenging-1 |
| 187 | Acetylcholine | C7H16NO2+ (9) | **200 ✓** | cation_pi (quaternary N+ — classic), h_bond | no | no | Hard-2 alt |
| 14969 | Vancomycin | C66H75Cl2N9O24 (~101) | **3D 404** (2D SDF 200 ✓) | halogen, pi_stacking ×many, h_bond, salt_bridge | yes (Cl2) | no | **UNVERIFIED 3D — large stretch only** |
| 5284373 | Cyclosporin A | C62H111N11O12 (85) | **3D 404** | — | no | no | rejected (no 3D) |
| 643975 | FAD | C27H33N9O15P2 (53) | **3D 404** | — | no | no | rejected (no 3D) |

### RCSB CCD candidates (ideal SDF fetched live)

| CCD | Name | SDF fetch | Notes |
|---|---|---|---|
| ATP | ADENOSINE-5'-TRIPHOSPHATE | **200 ✓** (47 atoms / 49 bonds, formal charge 0, 10 aromatic bonds; page `rcsb.org/ligand/ATP` fetched) | explicit H present; 3,738 standalone-ligand PDB entries (page-verified count) |
| ASP | (aspirin; CCD page not name-fetched — file fetched, header "ASP") | **200 ✓** (16 atoms) | cross-checked with PubChem aspirin |
| HEM | heme (name cross-checked via PubChem heme formula C34H32FeN4O4; CCD *name field* not read this session — confirm at fetch) | **200 ✓** | **Fe in molecule → metal_present true**; porphyrin pi_stacking |
| FOL | folic acid (cross-checked with PubChem CID 135398658) | **200 ✓** | |
| DRG | **name UNVERIFIED** (file fetched 200, name not read) | 200 | do not use without confirming the CCD name |

### PDB complex provenance (VERIFIED via RCSB search API 2026-09-24)

Search API (`https://search.rcsb.org/rcsbsearch/v2/query?json=...`, full_text) — VERIFIED working. Top hits per ligand:

| Ligand | Top PDB entity hit(s) | total_count | Status |
|---|---|---|---|
| Aspirin | **1OXR** (1TGM, 6UX1) | 26 | **1OXR fully verified**: GraphQL Data API returned title "…complex formed between Phospholipase A2 and Aspirin…", nonpolymer entities = **CA (CALCIUM ION)** + **AIN (2-(ACETYLOXY)BENZOIC ACID)**; paper DOI 10.1080/10611860400024078 (primary); entry DOI 10.2210/pdb1oxr/pdb resolves 200 at doi.org |
| Caffeine | 3G6M (8FTG, 9XUA) | 1,465 | search-level only — confirm ligand present in entry via Data API at proposal time |
| Benzamidine | 1S0R (2EEK, 2OXS) | 966 | search-level only |
| Citrate | 1O7X (2R9E, 2R26) | 34,100 | search-level only |
| Chloramphenicol | 4CLA (3U9F, 3CLA) | 5,944 | search-level only |
| Quinine | 9NDX (9NDV, 4UIL) | 149 | search-level only |
| Folate | 4KMZ (4KN0, 4KN1) | 1,108 | search-level only |

**1OXR's CA calcium ion is the ligand+ions demo anchor** for ROADMAP criterion 4 (Cleanup leaves the original object set): CA is in the detector's approved metal list (02-01: {MG, ZN, FE, CA, MN, CU, NI, CO, CD}) and demonstrates that a scene carrying ions is untouched by prefix-scoped cleanup. Note CA/ions are *separate* CCD components — they are scene context (user-loaded or shipped PDB), never part of the ligand SDF.

---

## RQ3 — Download sources (all patterns fetched live 2026-09-24)

| Source | Exact URL pattern | Format | Verified? |
|---|---|---|---|
| PubChem 3D SDF | `https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/<CID>/SDF?record_type=3d` | SDF V2000, 1 record, **bond orders + explicit H + real 3D coords** | **YES** — ~15 fetches incl. 2244 (aspirin: 21 atoms/21 bonds, H present) |
| PubChem property | `.../rest/pug/compound/cid/<CID>/property/MolecularFormula,MolecularWeight,Title,Charge/JSON` | JSON | **YES** |
| PubChem name lookup | `.../rest/pug/compound/name/<name>/property/.../JSON` | JSON | **YES** (resolves names → CIDs) |
| PubChem 2D SDF | `.../SDF?record_type=2d` | SDF, flat coords | **YES** (vancomycin 200) — not gameplay-preferred |
| RCSB ligand ideal SDF | `https://files.rcsb.org/ligands/view/<CCD>_ideal.sdf` | SDF V2000, 1 record, bond orders + explicit H, 3D coords | **YES** — ATP/ASP/DRG/HEM/FOL all 200; plain `<CCD>.sdf` **404s** (only `_ideal` works) |
| RCSB ligand page | `https://www.rcsb.org/ligand/<CCD>` | HTML (atom/bond counts, charge, SMILES/InChI, DrugBank link) | **YES** (ATP) |
| RCSB search API | `https://search.rcsb.org/rcsbsearch/v2/query?json=<urlencoded>` | JSON | **YES** (7 ligand searches) |
| RCSB Data API (REST) | `https://data.rcsb.org/rest/v1/core/entry/<PDBID>` | JSON (title, citations incl. `pdbx_database_id_DOI`, `rcsb_is_primary`) | **YES** (1OXR) |
| RCSB Data API (GraphQL) | `https://data.rcsb.org/graphql?query=...` | JSON (entry ligand inventory) | **YES** (1OXR ligands) |
| ChEBI molfile | `https://www.ebi.ac.uk/chebi/backend/api/public/molfile/<numeric-id>` | **2D** molfile (Marvin) | **YES** (acetate CHEBI:30089) — 2D only; use only if an ionized form lacking a PubChem 3D conformer is chosen |

### SDF-first implications (decided)

- **Bundle ready-made SDFs. Never convert from PDB.** PDB-format complex bonds are order-1/CONECT-only — conversion cannot invent orders (mechanics researcher's verified claim; restated). Both recommended sources already carry MDL bond orders + explicit H + 3D coords, satisfying the SDF-first rule (bond orders + explicit H) with **zero conversion tooling** → zero extra deps (no Open Babel; PyMOL-as-converter unnecessary and UNVERIFIED — do not rely on it).
- Feed both formats through the existing string loaders (`read_sdfstr` path; count_states==1 asserted — engine.py:234, placement.py:337 VERIFIED in code).
- PubChem's CID page (pubchem.ncbi.nlm.nih.gov/compound/<CID>) is the human-checkable landing URL for DATA_SOURCES.md; the REST endpoint is the machine fetch URL.

---

## RQ4 — Provenance databases

| Database | Status | What it records | Use in DATA_SOURCES.md |
|---|---|---|---|
| **PLIP** (Protein-Ligand Interaction Profiler) | **VERIFIED live** 2026-09-24 — `https://plip-tool.biotec.tu-dresden.de/plip-web/plip/index` (fetched; JS page served fine to fetcher) | Accepts **PDB IDs** (or .pdb files); identifies protein–ligand interactions (h-bond, salt bridge, pi-stacking, cation-pi, hydrophobic, halogen, water bridges, metal complexes); atom-level binding characterization; parsable output; adjustable thresholds whose names match the 02-01 gate doc (PISTACK_DIST_MAX, PICATION_DIST_MAX, HALOGEN_DIST_MAX, SALTBRIDGE_DIST_MAX…) | **Primary interaction-provenance citation per entry**: "PLIP analysis of PDB <id>: <interaction types reported>"; cite Schake, Bolz et al., PLIP 2025, doi:10.1093/nar/gkaf361 (fetched from the tool page). GitHub: github.com/pharmai/plip |
| **PDBsum** | **VERIFIED UNAVAILABLE** 2026-09-24 — its own EBI page (fetched) states "PDBsum is currently unavailable due to issues with the web server, and likely to remain so for the foreseeable future. Please use other services such as PDBe." Standalone PDBsum-Generate exists via GitHub link on that page | Ligand interaction diagrams per PDB entry | **Do NOT anchor provenance on PDBsum** (would make DATA_SOURCES.md untruthful/unexecutable). Mention only as historical, if at all |
| **PDBe** (EBI) | RECOMMENDED-BY-PDBSUM (linked from the fetched page); per-entry URL `https://www.ebi.ac.uk/pdbe/entry/pdb/<id>` not fetched this session | Entry pages incl. ligand interactions | Secondary provenance link (MEDIUM confidence until fetched at proposal time) |
| **RCSB search + Data APIs** | VERIFIED | Programmatic ligand→complex discovery + per-entry metadata (title, citations, DOI, ligand inventory) | The mechanism the GATE proposal uses to pin each candidate's complex |
| BindingDB | **UNVERIFIED** (not fetched) | Binding affinities | URL to check at GATE: https://www.bindingdb.org — optional affinity note, not required |
| PDBbind | UNVERIFIED (not fetched; known registration-based) | Curated binding-affinity complexes | Skip (registration friction vs. zero-deps truthfulness) |

**Per-candidate provenance record =** PDB complex ID (from verified search) → PLIP interaction report for that ID → structure paper (primary citation + DOI from `pdbx_database_id_DOI`) → entry DOI. This is exactly the "protonation/interaction provenance from known binding databases" chain, and PLIP is a binding-interaction database of record.

---

## RQ5 — Licenses (fetched verbatim 2026-09-24)

| Source | License | Exact policy statement (fetched) | URL |
|---|---|---|---|
| **wwPDB archive data** (covers RCSB ligand ideal SDFs, CCD definitions, PDB entries) | **CC0 1.0** | "Data files contained in the PDB archive are available under the CC0 1.0 Universal (CC0 1.0) Public Domain Dedication. Users of PDB data are encouraged to attribute the original authors of the PDB structure data where possible." | https://www.wwpdb.org/about/usage-policies (fetched; mirrored on https://www.rcsb.org/pages/policies) |
| **NCBI / PubChem** | Public domain (US-gov) + no-restrictions molecular data | "Information that is created by or for the US government on this site is within the public domain… it is requested that in any subsequent use of this work, NLM be given appropriate acknowledgment." AND "NCBI itself places no restrictions on the use or distribution of the data contained therein" — with the caveat that "some submitters of the original data may claim patent, copyright, or other intellectual property rights…" | https://www.ncbi.nlm.nih.gov/home/about/policies/ (fetched); PubChem FTP Fair Use Disclaimer: https://ftp.ncbi.nlm.nih.gov/pubchem/README (fetched verbatim) |
| **ChEBI** | **CC BY 4.0** | "All data in the ChEBI database is non-proprietary or is derived from a non-proprietary source… The data on this website is available under the Creative Commons License (CC BY 4.0), and governed by EMBL-EBI's terms of use" | https://www.ebi.ac.uk/chebi/about (fetched) |

**Flags for the GATE/human:**
1. **PubChem web-docs disclaimer page is JS-walled to this environment** (`https://pubchem.ncbi.nlm.nih.gov/docs/disclaimer` returned "JavaScript is required"; Wayback capture also JS-only). The legal substance is covered by the two fetched pages above (NCBI policy + FTP Fair Use). The human approver should eyeball the disclaimer in a real browser once and record that the submitter-rights caveat doesn't apply to our chosen drug-like CIDs (each is a single well-known compound, not a submitter-restricted deposit).
2. CC0/CC BY both **permit redistribution/bundling** — the manifest's set-level `license` field can carry e.g. `"CC0 1.0 (wwPDB)"` or `"Public domain (NCBI PubChem)"` per set's dominant source; mixed-source sets should state both.
3. DrugBank data (surfaced on RCSB ligand pages) is **CC BY-NC 4.0 — do NOT bundle or cite as our license**; it is informational only (seen on the fetched ATP page).

---

## RQ6 — DOIs (what DATA_SOURCES.md should cite)

Verified scheme (RCSB policies page, fetched) + live resolution check:

1. **PDB entry DOI** — format `10.2210/pdbXXXX/pdb` (4-char IDs, entries deposited before 2027-07-21; 12-char `pdb_1000axyz` after). **Live-verified**: `https://doi.org/10.2210/pdb1oxr/pdb` → HTTP 200.
2. **Structure-paper DOI** — the primary citation's DOI from the RCSB Data API: field `citation[].pdbx_database_id_DOI` with `rcsb_is_primary: Y`. **Live-verified for 1OXR**: 10.1080/10611860400024078 ("Aspirin induces its anti-inflammatory effects through its specific binding to phospholipase A2…", 2005).
3. **PubChem** — the **CID is the identifier** (stable, URL-addressable `pubchem.ncbi.nlm.nih.gov/compound/<CID>`); there is **no per-compound DOI**. PubChem's canonical database citation (Kim et al., Nucleic Acids Research) is **UNVERIFIED this session** — the docs pages are JS-walled here; confirm at GATE via https://pubchemdocs.ncbi.nlm.nih.gov/publications in a browser.
4. **ChEBI** citation (VERIFIED, fetched About page): Malik, A., et al. (2025). ChEBI: re-engineered for a sustainable future. Nucleic Acids Res. doi:10.1093/nar/gkaf1271.
5. **PLIP** citation (VERIFIED, fetched tool page): doi:10.1093/nar/gkaf361.

**DATA_SOURCES.md citation per ligand entry should carry:** source + exact fetch URL; CID (or CCD); PDB complex ID + entry DOI (10.2210/pdbXXXX/pdb) + primary paper DOI (from Data API); PLIP report reference; fetch date. Per-set: database citations (RCSB/Berman 2000 doi:10.1093/nar/28.1.235 — fetched from the RCSB policies page; wwPDB 2018 doi:10.1093/nar/gky949).

---

## RQ7 — Multi-state ligand policy (decide WITH the curated data)

**Engine laws (VERIFIED in code):** `cmd.count_states == 1` is asserted at every ligand load — engine.py:234 and placement.py:337 — and the bundler must emit exactly ONE molecule record per SDF file (STATE.md 04-04). The manifest carries `states_expected: 1` per entry and `protonation` as a descriptive string.

**Observed source behavior (VERIFIED live):** PubChem 3D SDF queries return exactly **one record per CID** (every fetch this session); RCSB ideal SDFs are single-record (ATP fetched).

**Recommended policy (for the GATE to ratify):**
1. **One record per file, by construction.** Bundle only single-record SDFs. If a future source yields multiple records, the bundler must either FAIL naming the source or split records into separate files — never merge/collapse (collapsing states would silently change chemistry; splitting keeps every entry truthful and `states_expected: 1` honest).
2. **Protonation chosen at PROPOSAL time, per candidate.** Pick the ionization state deliberately and record why — e.g., acetate anion (CID 175, −1, verified) not acetic acid; guanidinium (CID 32838, +1) not guanidine; citrate as free acid (CID 311, 0 — its carboxylate charge groups: note capability's acid-OH guard treats COOH as neutral, so a *fully deprotonated* citrate would need a charged source record if salt-bridge typing is wanted; GATE decides). Manifest string stays `'as-recorded'` (dev precedent, 02-04/04-06); the WHY lives in DATA_SOURCES.md, not the schema.
3. **Altloc/occupancy filtering: out of scope for v1.** Ready-made SDFs carry no altlocs; PDB-extraction is explicitly not the sourcing route (RQ3). If ever added, it would be a bundler feature with its own versioned policy — flag only.
4. **Ions:** separate components (e.g., 1OXR's CA) are scene context for the cleanup demo, never merged into a ligand SDF. A lone metal ion as a "ligand" is rejected (tiny bounding sphere, degenerate grid) — metal coordination is showcased via **heme's in-molecule Fe**.

---

## RQ8 — Propose → approve → fetch/commit protocol shape

**Precedent (repo):** demo-dev-1 was script-built with rationale recorded in plan summaries (02-04); DETECT-03's GATE approval was recorded as a dated STATE.md decision line ("[GATE] APPROVED", 2026-09-06). The protocol should reuse both patterns.

**Ordering (mechanics researcher's suggestion, adopted):** build bundling machinery first on 1–2 trial sets → **GATE proposal plan EARLY** → per-set bundling tasks → consolidation (dropdown tier grouping + every-manifest-id smoke + cleanup smoke).

**Artifact 1 — the proposal document** (e.g. `.planning/phases/08-demo-curation-citations/08-PROPOSALS.md`): one section per set, one row per candidate, with columns that let a human verify truthfully *without re-doing research*:

```
| field | content |
|---|---|
| set_id / tier / entry_id | demo-easy-1 / easy / aspirin |
| molecule + formula | Aspirin, C9H8O4 |
| source | PubChem CID 2244; fetch URL (exact); 3D SDF fetched <date> |
| size_class + heavy atoms | small, 13 |
| interaction types + why | h_bond (COOH donor + ester O acceptors), pi_stacking (benzene ring), hydrophobic — per capability.py rules |
| halogen/metal flags | false/false |
| PDB complex provenance | 1OXR (PLA2–aspirin–Ca2+); entry DOI 10.2210/pdb1oxr/pdb; paper DOI 10.1080/10611860400024078; PLIP report for 1OXR |
| protonation record | 'as-recorded' (neutral); why |
| license | Public domain (NCBI PubChem) + CC0 (wwPDB, for the complex reference) — URLs + quote |
| selection rationale | educational coverage / tier fit / diversity slot in the 9-set plan |
| evidence | fetched URL(s) + date + sha256-at-fetch |
| alternates | benzoic acid (CID 3979) |
```

**Artifact 2 — the approval record:** a dated human verdict per set recorded in (a) the proposal doc header ("APPROVED <date>, human") and (b) STATE.md decisions (verbatim human note, DETECT-03 precedent). **No fetch/commit of any approved candidate before this line exists.**

**Artifact 3 — the fetch/commit mechanism:** a git-ignored `tmp/` build script (02-04 `tmp/build_fixtures.py` pattern) that: downloads from the approved exact URLs → verifies single-record → computes sha256 → derives all 14 manifest keys mechanically → regenerates MANIFEST.json (never hand-edit SDFs after manifest creation — 02-04 law) → emits the DATA_SOURCES.md rows. Commit includes SDFs + MANIFEST.json + DATA_SOURCES.md in one atomic set-per-commit cadence.

**Artifact 4 — smoke criteria mapping:** every-manifest-id loop (02-RESEARCH-materialization §3.3 shape, VERIFIED in that doc) + the cleanup test. For "ligand+ions+water", the smoke needs a scene object *besides* the game objects: either load a tiny script-built ions+water PDB fixture (dev-fixture pattern, license trivial, no network) or load the real 1OXR-derived PDB (network dependency in the conda env). Recommend the **local fixture** (headless determinism), citing 1OXR in DATA_SOURCES.md as the real-world analog.

---

## RQ9 — DATA_SOURCES.md structure (proposed, satisfies criterion 3)

Location: `docs/DATA_SOURCES.md` (Phase 9 audits it alongside README/help; docs/ exists with DETECTION_THRESHOLDS.md).

```markdown
# Demo Data Sources (AA-match)
Last verified: <date> · Verification protocol: every claim carries a fetched URL + date;
human approval recorded in .planning/.../08-PROPOSALS.md before any bundled file was committed.

## 1. Sources & licenses
| Source | License | Policy quote | URL | Verified |
|---|---|---|---|---|
| PubChem (NCBI) | Public domain / no-restrictions | "<quote>" | <url> | <date> |
| wwPDB / RCSB | CC0 1.0 | "<quote>" | <url> | <date> |
(plus database citations: Berman 2000; wwPDB 2018; Malik 2025 ChEBI; PLIP 2025)

## 2. Demo sets (one section per set, tier-grouped order = dropdown order)
### demo-easy-1 — "<title>" (tier: easy)
Rationale: <educational coverage / tier fit / diversity slot>
License: <per above>
| entry_id | file | molecule | source (URL) | ID (CID/CCD) | PDB complex (ID + entry DOI + paper DOI) | interaction provenance (PLIP on <PDB ID>: types) | protonation ('as-recorded' + why) | halogen/metal | sha256 | fetched |
(14 manifest keys cross-ref: "counts/sha256 pinned in aamatch/data/MANIFEST.json; regenerate via tmp/build script, never hand-edit")

## 3. Multi-state & ions policy (the ratified RQ7 text)
## 4. Not-bundled acknowledgements (DrugBank CC BY-NC shown on RCSB pages — informational only)
```

---

## Recommendations

**Top candidate per slot (all 3D-SDF-verified unless noted):**

| Set | Tier | Entries | Why |
|---|---|---|---|
| demo-easy-1 | easy | Aspirin (2244) + benzoic acid (3979) | classic; h_bond+pi_stacking; 1OXR provenance |
| demo-easy-2 | easy | Citric acid (311) + acetate (175) | salt-bridge intro; metabolites |
| demo-easy-3 | easy | Caffeine (2519) | acceptor-only h_bond + pi_stacking; 3G6M |
| demo-hard-1 | hard | Benzamidine (2332) + guanidinium (32838) | cation_pi + trypsin classic 1S0R |
| demo-hard-2 | hard | Glutamic acid (33032) + imidazolium (444234) or acetylcholine (187) | salt_bridge + cation_pi both directions |
| demo-hard-3 | hard | ATP (5957) + NAD (5892) | first medium molecules; cofactor classics |
| demo-challenge-1 | challenge | Chloramphenicol (5959) + quinine (3034034) | **halogen debut**; 4CLA/9NDX |
| demo-veryhard-1 | very_challenging | Folic acid (135398658) + thyroxine (5819) | large-ish + **iodine halogen**; 4KMZ |
| demo-veryhard-2 | very_challenging | HEM ideal SDF (RCSB) | **metal (Fe)** + porphyrin pi_stacking |

**Policy decisions to make at the GATE:** (1) ratify one-record-per-file + proposal-time protonation choice (RQ7); (2) accept NEAREST-BUCKET fallback as the large-bucket carrier vs. hunting a true ≥60-heavy ligand (vancomycin 2D / RCSB large CCD); (3) citrate ionization form (free acid vs deprotonated CID) given the COOH-never-anion guard; (4) cleanup-smoke scene fixture (local script-built ions+water vs network 1OXR PDB); (5) tier tokens stay exactly `easy|hard|challenge|very_challenging` (02-RESEARCH §3.2 comment) and set_ids sort-friendly for the future tier-grouped dropdown; (6) detector-coverage stress check: chloramphenicol/thyroxine exercise 02-07b halogen branch, HEM exercises the metal gate + `ligand_has_metal` — any detector surprise is a DETECTOR_VERSION bump event (02-01 caveat), never a silent edit.

---

## Handoff to planner

The planner must turn these into tasks:

1. **08-01 (machinery + trial):** extend `tmp/` build script to fetch-verify-single-record-sha256-derive-keys; regenerate manifest for 1–2 trial sets (e.g. easy-1); unit-test the 14-key derivation against dev-fixture invariants.
2. **08-02 (GATE proposal):** produce 08-PROPOSALS.md with the exact per-candidate table (RQ8 artifact 1) — every row's URLs re-fetched during the plan; human approval recorded in STATE.md BEFORE any commit of new data files.
3. **08-03..08-NN (per-set fetch/commit):** one plan per set (or batched 2–3): fetch → regenerate MANIFEST.json + SDFs → commit atomically; never hand-edit SDFs.
4. **DATA_SOURCES.md task:** write per RQ9 skeleton from the build script's emitted rows; mark [HUMAN] verification step.
5. **Dropdown tier grouping:** setup_form/setup_window change to group rows by tier (04-04 recorded gap) — tokens `easy|hard|challenge|very_challenging`, display order Easy→Hard→Challenge→Very challenging regardless of set_id sort.
6. **Smoke tasks:** every-manifest-id loop (all sets, counts vs manifest, sha256, flags vs element scan) + cleanup-restore test with an ions+water scene fixture (recommend local fixture; 1OXR cited as real-world analog).
7. **Detector-coverage check task:** run the detector over the new halogen/metal entries headlessly; any threshold surprise → DETECTOR_VERSION bump proposal (02-01 gate §4.7), not a silent edit.

---

## Sources

### Primary (HIGH confidence — fetched 2026-09-24)
- https://www.wwpdb.org/about/usage-policies — CC0 statement (verbatim captured)
- https://www.rcsb.org/pages/policies — citation formats, PDB DOI scheme, RCSB/wwPDB citations
- https://www.ncbi.nlm.nih.gov/home/about/policies/ — public-domain + molecular-data policy
- https://ftp.ncbi.nlm.nih.gov/pubchem/README — PubChem Fair Use Disclaimer (verbatim)
- https://www.ebi.ac.uk/chebi/about — CC BY 4.0 + ChEBI citation (Malik 2025, doi:10.1093/nar/gkaf1271)
- https://plip-tool.biotec.tu-dresden.de/plip-web/plip/index — PLIP live tool + citation (doi:10.1093/nar/gkaf361)
- https://www.ebi.ac.uk/thornton-srv/databases/pdbsum/ — PDBsum unavailable notice (verbatim)
- https://files.rcsb.org/ligands/view/{ATP,ASP,DRG,HEM,FOL}_ideal.sdf — ideal-SDF pattern (plain `.sdf` 404s)
- https://pubchem.ncbi.nlm.nih.gov/rest/pug/... — property + 3D-SDF endpoints (~25 live fetches; CIDs listed in RQ2)
- https://search.rcsb.org/rcsbsearch/v2/query — search API (7 ligand queries)
- https://data.rcsb.org/rest/v1/core/entry/1OXR + /graphql — entry metadata, ligands, DOIs
- https://doi.org/10.2210/pdb1oxr/pdb — resolves (200)
- https://www.rcsb.org/ligand/ATP — ligand page (counts, charge, DrugBank CC BY-NC note)
- Repo code: aamatch/generator.py (SIZE_S1/S2, _candidate_class, _select_pool fallback), aamatch/engine.py:234 / aamatch/placement.py:337 (count_states==1), aamatch/capability.py (typing rules), aamatch/setup_form.py (manifest_sets), aamatch/data/MANIFEST.json (frozen schema), .planning/phases/02-headless-game-engine/02-RESEARCH-materialization.md §3.2–3.3

### Secondary (MEDIUM)
- https://www.ebi.ac.uk/pdbe — PDBe as PDBsum replacement (recommended by the fetched PDBsum page; per-entry URL not fetched)
- RCSB search top-hits as *complex provenance* (ligand presence inside each entry still to be confirmed via Data API at proposal time — only 1OXR fully confirmed)

### Tertiary / UNVERIFIED (must check before GATE)
- https://pubchem.ncbi.nlm.nih.gov/docs/disclaimer — JS-walled here; human browser check recommended (substance covered by fetched NCBI/FTP pages)
- PubChem canonical database citation — confirm via https://pubchemdocs.ncbi.nlm.nih.gov/publications (JS-walled here)
- https://www.bindingdb.org — not fetched; optional affinity provenance
- HEM CCD *name field* and DRG CCD identity — file fetched but name not read; confirm at fetch
- PyMOL `cmd.save` SDF writing — unneeded by the recommended design; do not rely on
- Vancomycin 3D conformer (404 today) — recheck if a true large candidate is wanted

## Metadata

**Confidence breakdown:** Licenses/DOIs/URL patterns: HIGH (all fetched, some verbatim). Engine laws: HIGH (code). Candidate existence + SDF availability: HIGH (live fetches). Per-molecule interaction classification: MEDIUM (capability-rule ANALYSIS, to re-verify on actual SDF bytes at bundling). Large-bucket supply: MEDIUM (verified absence of 3D sources; fallback verified in code).

**Research date:** 2026-09-24 · **Valid until:** ~30 days (policy pages stable; PubChem conformer availability may change — re-verify at fetch time anyway per protocol)
