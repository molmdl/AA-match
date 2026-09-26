# Phase 8 — Demo Curation [GATE] Proposals

- **Phase:** 08-demo-curation-citations · **Plan:** 08-04 · **Date:** 2026-09-26
- **Status:** **APPROVED 2026-09-26, human** — approval recorded here **and** as a dated `[GATE] APPROVED` line in `.planning/STATE.md`, **before** any candidate data is fetched into the repo or committed (DETECT-03 precedent; fetch boundary below remains binding until 08-05..08-07 run the 08-01 pipeline).
- **Approval line:** **APPROVED 2026-09-26, human** — the human conditioned approval on an independent executor re-verification of the atom counts against source ("for the atom count, do again yourself and re-verify against source"); that re-verification was performed 2026-09-26 and **PASSED: 16/16 MATCH** (see *Approval-time re-verification* section). C1 accepted ("1 ok"); aspirin CID 2244 independently spot-verified by the human (verdict 3); U1–U4 RESOLVED as recorded in the UNVERIFIED section; all 10 decision defaults ACCEPTED as-is with the human's re-check-later caveat ("4 accept first lets chk later"). Full verbatim verdicts in the *Approval record* section. 08-05..08-07 are UNBLOCKED.
- **Fetch boundary (binding, from 08-04-PLAN):** proposal-time URL evidence fetches (property JSON, SDF counts-line reads, RCSB search/Data API) are sanctioned — they ARE the proposal evidence. **FORBIDDEN before the approval line exists:** downloading any candidate SDF into the repo, writing any file under `aamatch/data/`, and any git commit of candidate data. This session honored the boundary: ~80 evidence fetches went to stdout/temp only; `git status` verifies no `aamatch/data/` change and no new SDF anywhere in the tree.
- **Protocol:** proposes ~9 curated demo sets → human approves → 08-05..08-07 mechanically transcribe the APPROVED rows into `scripts/demo_specs/*.json` and fetch/commit through the 08-01 pipeline only. Nothing below changes code or data.

## Session verification summary (all fetches dated 2026-09-26)

| Work item | Result |
|---|---|
| PubChem property endpoint (Title/Formula/Charge), 15 primary CIDs + 4 alternate CIDs | 19/19 HTTP 200, values read and tabulated below |
| PubChem 3D SDF endpoint (`?record_type=3d`), 15 primary CIDs + 4 alternate CIDs | 19/19 HTTP 200, **exactly ONE** `$$$$` record each, counts line read per CID |
| Guanidinium CID 32838 3D SDF (was property-only at research time) | **RESOLVED VERIFIED**: 200, 1 record, counts `10 9` |
| RCSB `HEM_ideal.sdf` | 200, 1 record, counts `75 82`; element tally from atom block: C34 H32 N4 O4 **Fe1** (43 heavy); header name line reads **`HEM`** (see correction C7) |
| PDB complex provenance, 16 entries | EVERY chosen entry confirmed via RCSB Data API: ligand comp present in `non_polymer_entity` inventory + title + primary-citation DOI read from `citation[].pdbx_database_id_DOI (rcsb_is_primary=Y)` |
| Entry DOI resolution (`https://doi.org/10.2210/pdbXXXX/pdb`), 16 entries | 16/16 HTTP 200 → wwpdb.org landing |
| wwPDB usage policy (CC0 1.0) | VERIFIED 2026-09-26 verbatim (see Licenses row of every set) |
| NCBI policies page + PubChem FTP Fair Use Disclaimer | VERIFIED 2026-09-26 verbatim |
| Paper DOI resolution via doi.org | 5/12 resolve 200 from this environment; 7/12 HTTP 403 (publisher bot-block of non-browser agents — **not** a dead DOI; each paper DOI is VERIFIED against the RCSB Data API record; browser spot-checks deferred, see UNVERIFIED U2) |
| UNVERIFIED-now items | 4 items (U1–U4 below), each with the exact human check |

**Corrections discovered vs 08-RESEARCH-sourcing.md (all re-verified this session):** see section *"Evidence corrections"* — including the benzoic-acid CID error (research's 3979 is a different compound; correct CID is 243) and heavy-atom recounts. All corrected values below are the session-verified ones.

## Approval-time re-verification (2026-09-26) — demanded by human verdict 1

The human's first verdict was: **"for the atom count, do again yourself and re-verify against source."** A fresh, independent fetch+parse pass was run after the checkpoint verdict (NOT trusting the earlier same-session pass): for every primary candidate, the PubChem property JSON (MolecularFormula, MolecularWeight, Title, Charge) and the 3D SDF were re-fetched via curl, the SDF counts line was parsed, and heavy atoms were recomputed from the atom block. Three-way cross-check per candidate: (a) SDF counts-line atom count == number of atom-block lines parsed; (b) heavy atoms (atom block, symbol ≠ H) == this proposal's C2-corrected heavy count; (c) heavy-atom total computed from the fetched formula == the same number; plus exactly ONE `$$$$` record per SDF. Script output reproduced verbatim:

| entry | CID | formula | MW | charge | SDF atoms/bonds | `$$$$` | sdf_atoms==blk | heavy(SDF) | heavy(formula) | proposal heavy | VERDICT |
|---|---|---|---|---|---|---|---|---|---|---|---|
| aspirin | 2244 | C9H8O4 | 180.16 | 0 | 21/21 | 1 | True | 13 | 13 | 13 | **MATCH** |
| benzoic_acid | 243 | C7H6O2 | 122.12 | 0 | 15/15 | 1 | True | 9 | 9 | 9 | **MATCH** |
| citric_acid | 311 | C6H8O7 | 192.12 | 0 | 21/20 | 1 | True | 13 | 13 | 13 | **MATCH** |
| acetate | 175 | C2H3O2− | 59.04 | −1 | 7/6 | 1 | True | 4 | 4 | 4 | **MATCH** |
| caffeine | 2519 | C8H10N4O2 | 194.19 | 0 | 24/25 | 1 | True | 14 | 14 | 14 | **MATCH** |
| benzamidine | 2332 | C7H8N2 | 120.15 | 0 | 17/17 | 1 | True | 9 | 9 | 9 | **MATCH** |
| guanidinium | 32838 | CH6N3+ | 60.08 | +1 | 10/9 | 1 | True | 4 | 4 | 4 | **MATCH** |
| glutamic_acid | 33032 | C5H9NO4 | 147.13 | 0 | 19/18 | 1 | True | 10 | 10 | 10 | **MATCH** |
| acetylcholine | 187 | C7H16NO2+ | 146.21 | +1 | 26/25 | 1 | True | 10 | 10 | 10 | **MATCH** |
| atp | 5957 | C10H16N5O13P3 | 507.18 | 0 | 47/49 | 1 | True | 31 | 31 | 31 | **MATCH** |
| nad | 5892 | C21H27N7O14P2 | 663.4 | 0 | 71/75 | 1 | True | 44 | 44 | 44 | **MATCH** |
| chloramphenicol | 5959 | C11H12Cl2N2O5 | 323.13 | 0 | 32/32 | 1 | True | 20 | 20 | 20 | **MATCH** |
| quinine | 3034034 | C20H24N2O2 | 324.4 | 0 | 48/51 | 1 | True | 24 | 24 | 24 | **MATCH** |
| folic_acid | 135398658 | C19H19N7O6 | 441.4 | 0 | 51/53 | 1 | True | 32 | 32 | 32 | **MATCH** |
| thyroxine | 5819 | C15H11I4NO4 | 776.87 | 0 | 35/36 | 1 | True | 24 | 24 | 24 | **MATCH** |
| heme | HEM (RCSB `HEM_ideal.sdf`) | C34H32FeN4O4 | n/a | 0 | 75/82 | 1 | True | 43 | 43 | 43 | **MATCH** |

**Verdict: ALL 16 CANDIDATES MATCH** (three-way cross-check + single-record check, fresh fetches 2026-09-26). No proposal number was changed; the C2-corrected heavy counts are source-confirmed. The `expect_atom_count` guards above (aspirin 21, benzoic 15, citric 21, acetate 7, caffeine 24, benzamidine 17, guanidinium 10, glutamate 19, acetylcholine 26, ATP 47, NAD 71, chloramphenicol 32, quinine 48, folate 51, thyroxine 35, heme 75) are likewise re-confirmed.

---

## Set 1 — demo-easy-1 · tier: easy · title (amendable): "Everyday organics"

| field | content |
|---|---|
| set_id / tier / entry_id | demo-easy-1 / easy / **aspirin** |
| molecule + formula + heavy atoms | Aspirin (acetylsalicylic acid), C9H8O4, **13 heavy** (small) |
| source + fetch URL | PubChem CID **2244**; property `https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/2244/property/MolecularFormula,MolecularWeight,Title,Charge/JSON`; 3D `.../cid/2244/SDF?record_type=3d` |
| evidence | webfetch 2026-09-26: property 200 (Title=Aspirin, C9H8O4, Charge 0) + SDF 200, ONE record, counts `21 21` (21 atoms incl H / 21 bonds; `expect_atom_count` guard = 21) |
| interaction types + why (capability.py rules) | h_bond (carboxyl O–H donor; ester + carboxyl O acceptors), pi_stacking (benzene ring, 6-ring 3 alternating doubles), hydrophobic; cation_pi in the AA-cation-over-lig-ring direction |
| halogen/metal flags | false / false |
| PDB complex provenance | **1OXR** (phospholipase A2–aspirin·Ca²⁺ complex; AIN confirmed in nonpolymer inventory via Data API, 2026-09-26); entry DOI `10.2210/pdb1oxr/pdb` (resolves 200 this session); primary paper DOI **10.1080/10611860400024078** (VERIFIED at rcsb.org entry record; doi.org direct fetch = 403 bot-block → browser spot-check U2); PLIP reference: PLIP web-tool analysis of **1OXR** (tool verified live 2026-09-24, doi:10.1093/nar/gkaf361; report row to be written in DATA_SOURCES.md) |
| protonation record | `'as-recorded'` — neutral free acid (Charge 0). Note: capability's COOH-never-anion guard means the carboxyl is NOT salt-bridge-typed in this form; aspirin carries h_bond/pi/hydrophobic for the set |
| license | Public domain (NCBI PubChem) — https://www.ncbi.nlm.nih.gov/home/about/policies/ + https://ftp.ncbi.nlm.nih.gov/pubchem/README (both VERIFIED verbatim 2026-09-26; submitter-rights caveat → U1 human check). Complex reference metadata: CC0 1.0 (wwPDB) — https://www.wwpdb.org/about/usage-policies (VERIFIED 2026-09-26) |
| selection rationale | The everyday drug; 1OXR is the fully pre-verified provenance anchor and its crystallographic Ca²⁺ ion is also the real-world analog cited for the cleanup-scene fixture (Decision 7); easy-tier intros (1–2 required types) |
| alternates | none needed at this slot |

| field | content |
|---|---|
| set_id / tier / entry_id | demo-easy-1 / easy / **benzoic_acid** |
| molecule + formula + heavy atoms | Benzoic acid, C7H6O2, **9 heavy** (small) |
| source + fetch URL | PubChem CID **243** (**CORRECTED — see C1**); property `.../cid/243/property/.../JSON`; 3D `.../cid/243/SDF?record_type=3d` |
| evidence | webfetch 2026-09-26: name lookup `compound/name/benzoic%20acid` → CID 243; property 200 (Title=Benzoic Acid, C7H6O2, Charge 0) + SDF 200, ONE record, counts `15 15` (`expect_atom_count` = 15) |
| interaction types + why | h_bond (COOH donor + O acceptors), pi_stacking (benzene), hydrophobic, cation_pi (AA-cation-over-ring) |
| halogen/metal flags | false / false |
| PDB complex provenance | **5E4D** (hydroxynitrile lyase–benzoic acid complex; BEZ confirmed in inventory — chemcomp name queried: `BEZ = BENZOIC ACID`, VERIFIED 2026-09-26); entry DOI `10.2210/pdb5e4d/pdb` (resolves 200); primary paper DOI **10.1038/srep46738** (resolves 200 this session); PLIP reference: 5E4D |
| protonation record | `'as-recorded'` — neutral free acid (Charge 0). Honest note: the research's "salt_bridge as benzoate(−1)" does **not** hold for this CID; if a salt-bridge carrier is wanted inside easy-1, the approved alternate below is that form |
| license | Public domain (NCBI PubChem) + CC0 1.0 (wwPDB, complex reference) — same URLs/verification as aspirin row |
| selection rationale | Second classic organic acid for the 2-molecule easy set; smallest aromatic (9 heavy) keeps easy grids dense; pairs with aspirin as the duo of household organics |
| alternates | **benzoate anion CID 242** (C7H5O2−, Charge −1) — VERIFIED 2026-09-26: property 200 + SDF 200, ONE record, counts `14 14`; substitute if easy-1 should carry its own charged species |

---

## Set 2 — demo-easy-2 · tier: easy · title (amendable): "Metabolites & ions"

| field | content |
|---|---|
| set_id / tier / entry_id | demo-easy-2 / easy / **citric_acid** |
| molecule + formula + heavy atoms | Citric acid, C6H8O7, **13 heavy** (small; **CORRECTED from 6 — see C2**) |
| source + fetch URL | PubChem CID **311**; property `.../cid/311/property/.../JSON`; 3D `.../cid/311/SDF?record_type=3d` |
| evidence | webfetch 2026-09-26: property 200 (Title=Citric Acid, C6H8O7, Charge 0) + SDF 200, ONE record, counts `21 20` (`expect_atom_count` = 21) |
| interaction types + why | h_bond rich (4 OH-type donors — 3 COOH + 1 alcohol; 7 O acceptors), hydrophobic (small carbon skeleton). No salt bridge as-recorded (Decision 5: COOH-never-anion guard) |
| halogen/metal flags | false / false |
| PDB complex provenance | **8FUY** (Crithidia fasciculata G6PDH, citrate bound; CIT + CL confirmed in inventory). **Research's top hit 1O7X was REJECTED at confirmation**: its Data API entry carries **no nonpolymer entities** (inventory empty, 2026-09-26) — see C5. Entry DOI `10.2210/pdb8fuy/pdb` (resolves 200); primary paper DOI: **NONE recorded** in the RCSB data (title VERIFIED: "Glucose-6-phosphate 1-dehydrogenase (G6PDH) from Crithidia fasciculata (citrate bound)") — honest absence, not an omission to invent; PLIP reference: 8FUY |
| protonation record | `'as-recorded'` — neutral free acid (Charge 0; Decision 5 below records why deprotonated-citrate sourcing is rejected for v1) |
| license | Public domain (NCBI PubChem) + CC0 1.0 (wwPDB) — URLs as above |
| selection rationale | The central metabolite; teach h_bond-rich polyol chemistry; metabolite identity beside the artifact-level acetate ion |
| alternates | none (deprotonated citrate rejected for v1 — Decision 5) |

| field | content |
|---|---|
| set_id / tier / entry_id | demo-easy-2 / easy / **acetate** |
| molecule + formula + heavy atoms | Acetate anion, C2H3O2−, **4 heavy** (small; CORRECTED from 2 — see C2) |
| source + fetch URL | PubChem CID **175**; property `.../cid/175/property/.../JSON`; 3D `.../cid/175/SDF?record_type=3d` |
| evidence | webfetch 2026-09-26: property 200 (Title=Acetate, C2H3O2-, **Charge −1**) + SDF 200, ONE record, counts `7 6` (`expect_atom_count` = 7) |
| interaction types + why | **salt_bridge** (carboxylate −1 charged group — the set's salt-bridge carrier), h_bond (carboxylate O acceptors), hydrophobic (methyl) |
| halogen/metal flags | false / false |
| PDB complex provenance | **5YS8** (succinate–acetate permease; **ACT confirmed** in inventory — research-style top hit 5ZUG lacked ACT; walked hits to first confirmed entry, 2026-09-26); entry DOI `10.2210/pdb5ys8/pdb` (resolves 200); primary paper DOI **10.1038/s41422-018-0032-8** (resolves 200 this session); PLIP reference: 5YS8 |
| protonation record | `'as-recorded'` — the **deprotonated anion (−1) CHOSEN over acetic acid** deliberately: it is the salt-bridge carrier (carboxylate charge group typing requires the recorded charge) |
| license | Public domain (NCBI PubChem) + CC0 1.0 (wwPDB) — URLs as above |
| selection rationale | Minimal charged ion — teaches "charged group = salt bridge" at the smallest possible size; paired with the metabolite it derives from |
| alternates | none |

---

## Set 3 — demo-easy-3 · tier: easy · title (amendable): "Caffeine"

| field | content |
|---|---|
| set_id / tier / entry_id | demo-easy-3 / easy / **caffeine** |
| molecule + formula + heavy atoms | Caffeine (1,3,7-trimethylxanthine), C8H10N4O2, **14 heavy** (small) |
| source + fetch URL | PubChem CID **2519**; property `.../cid/2519/property/.../JSON`; 3D `.../cid/2519/SDF?record_type=3d` |
| evidence | webfetch 2026-09-26: property 200 (Title=Caffeine, C8H10N4O2, Charge 0) + SDF 200, ONE record, counts `24 25` (`expect_atom_count` = 24) |
| interaction types + why | h_bond **acceptor-only** (2 carbonyl O + 4 ring N, every ring N methylated → no N–H donor; a clean direction-refined-typing teaching case), pi_stacking (fused purine rings), hydrophobic |
| halogen/metal flags | false / false |
| PDB complex provenance | **3G6M** (chitinase CrChi1–caffeine complex; **CFF confirmed** in inventory, 2026-09-26); entry DOI `10.2210/pdb3g6m/pdb` (resolves 200); primary paper DOI **10.1099/mic.0.043653-0** (VERIFIED at rcsb.org; doi.org = 403 bot-block → U2); PLIP reference: 3G6M |
| protonation record | `'as-recorded'` — neutral (Charge 0); no ionization choice needed |
| license | Public domain (NCBI PubChem) + CC0 1.0 (wwPDB) — URLs as above |
| selection rationale | The most-recognized everyday stimulant; a one-molecule easy set showcasing acceptor-only h_bond + pi_stacking (GEN-06 diversity: acceptor-only case has no other carrier in the easy tier) |
| alternates | none |

---

## Set 4 — demo-hard-1 · tier: hard · title (amendable): "Trypsin classics"

| field | content |
|---|---|
| set_id / tier / entry_id | demo-hard-1 / hard / **benzamidine** |
| molecule + formula + heavy atoms | Benzamidine, C7H8N2, **9 heavy** (small) |
| source + fetch URL | PubChem CID **2332**; property `.../cid/2332/property/.../JSON`; 3D `.../cid/2332/SDF?record_type=3d` |
| evidence | webfetch 2026-09-26: property 200 (Title=Benzamidine, C7H8N2, **Charge 0** — see C3) + SDF 200, ONE record, counts `17 17` (`expect_atom_count` = 17) |
| interaction types + why | h_bond (amidine N–H donors + ring-N acceptors), pi_stacking (benzene), hydrophobic, cation_pi in the **AA-cation-over-lig-ring** direction only (ligand is neutral — the research's "+1 amidinium → ligand-side cation_pi" claim is INCORRECT for this CID; C3) |
| halogen/metal flags | false / false |
| PDB complex provenance | **1S0R** (bovine trypsin–benzamidine, atomic resolution — THE classic; **BEN confirmed** in inventory; CA ion also present — second cleanup-analog datapoint, 2026-09-26); entry DOI `10.2210/pdb1s0r/pdb` (resolves 200); primary paper DOI: **NONE recorded** in the RCSB data (title VERIFIED: "Bovine Pancreatic Trypsin inhibited with Benzamidine at Atomic resolution") — honest absence; PLIP reference: 1S0R |
| protonation record | `'as-recorded'` — neutral free base (Charge 0 as registered). In the trypsin pocket benzamidine is protonated, but we do NOT invent a charged form; the approved alternate below is the real charged PubChem record |
| license | Public domain (NCBI PubChem) + CC0 1.0 (wwPDB) — URLs as above |
| selection rationale | The textbook serine-protease inhibitor; trypsin/benzamidine is the most recognizable protein–ligand teaching system; hard-tier fit via charged-species companion (below) |
| alternates | **benzamidinium chloride CID 444655** (C7H9N2+, Charge +1) — VERIFIED 2026-09-26: property 200 + SDF 200, ONE record, counts `18 18`; substitute if a ligand-side cation showcase is preferred in this slot |

| field | content |
|---|---|
| set_id / tier / entry_id | demo-hard-1 / hard / **guanidinium** |
| molecule + formula + heavy atoms | Guanidinium, CH6N3+, **4 heavy** (small) |
| source + fetch URL | PubChem CID **32838**; property `.../cid/32838/property/.../JSON`; 3D `.../cid/32838/SDF?record_type=3d` |
| evidence | webfetch 2026-09-26: property 200 (Title=Guanidinium, CH6N3+, **Charge +1**) + SDF 200, **ONE record**, counts `10 9` (`expect_atom_count` = 10). **Research's "property only, 3D UNVERIFIED" is now RESOLVED VERIFIED** (plan step 2 executed; C4) |
| interaction types + why | **salt_bridge** (+1 C(N)₃ group — one center = centroid of the 3 bonded Ns per the 02-06 recorded detector rule; this candidate exercises that real-world geometry), **cation_pi ligand-side**, h_bond donors (6 N–H); ammonium-veto boundary: the PLIP veto targets ammonium N with exactly 3 non-H substituents — guanidinium's C-centered cation sits on the boundary, a live boundary-case demo |
| halogen/metal flags | false / false |
| PDB complex provenance | **5NWQ** (Thermobifida fusca **guanidine III riboswitch + guanidine** — the classic guanidinium-moiety system; **GAI confirmed** in inventory, chemcomp name queried: `GAI = GUANIDINE`; note CCD `GUN = GUANINE` — recorded pitfall, 2026-09-26); entry DOI `10.2210/pdb5nwq/pdb` (resolves 200); primary paper DOI **10.1016/j.chembiol.2017.08.021** (resolves 200 this session); PLIP reference: 5NWQ |
| protonation record | `'as-recorded'` — the cation (+1) CHOSEN over neutral guanine/guanidine bases deliberately: it is the salt-bridge + ligand-cation carrier |
| license | Public domain (NCBI PubChem) + CC0 1.0 (wwPDB) — URLs as above |
| selection rationale | Smallest possible charged amino-group species; the ion pair to acetate; completes the hard-tier's charged-species pair with benzamidine's aromatic side |
| alternates | none (3D now verified) |

---

## Set 5 — demo-hard-2 · tier: hard · title (amendable): "Charged messengers"

| field | content |
|---|---|
| set_id / tier / entry_id | demo-hard-2 / hard / **glutamic_acid** |
| molecule + formula + heavy atoms | L-Glutamic acid, C5H9NO4, **10 heavy** (small; CORRECTED from 5 — see C2) |
| source + fetch URL | PubChem CID **33032**; property `.../cid/33032/property/.../JSON`; 3D `.../cid/33032/SDF?record_type=3d` |
| evidence | webfetch 2026-09-26: property 200 (Title=L-Glutamic Acid, C5H9NO4, **Charge 0** — see C3) + SDF 200, ONE record, counts `19 18` (`expect_atom_count` = 19) |
| interaction types + why | h_bond rich (NH₂ donor + 2 COOH donors; carboxyl + amino N/O acceptors), hydrophobic (C3 spacer). No salt bridge **as-recorded** (neutral free acid; the research's "−1" claim is INCORRECT for this CID; C3) |
| halogen/metal flags | false / false |
| PDB complex provenance | **2JFO** (Enterococcus faecalis **glutamate racemase with D- and L-glutamate**; **GLU confirmed as a bound nonpolymer ligand** — hits 2CT6/1J0F rejected at confirmation (no nonpolymer GLU), 2026-09-26); entry DOI `10.2210/pdb2jfo/pdb` (resolves 200); primary paper DOI **10.1038/nature05689** (resolves 200 this session); PLIP reference: 2JFO |
| protonation record | `'as-recorded'` — neutral free acid (Charge 0). Physiological zwitterion is deliberately NOT synthesized; parallel policy to citrate (Decision 5). Salt-bridge teens for this set are carried by acetylcholine |
| license | Public domain (NCBI PubChem) + CC0 1.0 (wwPDB) — URLs as above |
| selection rationale | The most-recognized neurotransmitter amino acid; pairs free glutamate with the charged quaternary messenger next to it (contrast: uncharged vs permanently charged nitrogen) |
| alternates | the acetylcholine row's alternates serve the whole set (set-level cation flexibility) |

| field | content |
|---|---|
| set_id / tier / entry_id | demo-hard-2 / hard / **acetylcholine** |
| molecule + formula + heavy atoms | Acetylcholine, C7H16NO2+, **10 heavy** (small; CORRECTED from 9 — see C2) |
| source + fetch URL | PubChem CID **187**; property `.../cid/187/property/.../JSON`; 3D `.../cid/187/SDF?record_type=3d` |
| evidence | webfetch 2026-09-26: property 200 (Title=Acetylcholine, C7H16NO2+, **Charge +1**) + SDF 200, ONE record, counts `26 25` (`expect_atom_count` = 26) |
| interaction types + why | **salt_bridge** (permanently +1 quaternary N vs AA carboxylates), **cation_pi ligand-side** (the **NMe₃⁺ quaternary case sits OUTSIDE the PLIP tertamine veto** — veto requires exactly 3 non-H substituents; this entry demos the boundary complement), h_bond (carbonyl + ester O acceptors), hydrophobic |
| halogen/metal flags | false / false |
| PDB complex provenance | **9E3E** (Torpedo nicotinic acetylcholine receptor, diliganded; **ACH confirmed** in inventory — eight higher-ranked hits lacked ACH, walk recorded, 2026-09-26); entry DOI `10.2210/pdb9e3e/pdb` (resolves 200); primary paper DOI **10.1126/science.adw1264** (VERIFIED at rcsb.org; doi.org = 403 bot-block → U2); PLIP reference: 9E3E |
| protonation record | `'as-recorded'` — permanently charged quaternary ammonium (+1); no pKa choice exists |
| license | Public domain (NCBI PubChem) + CC0 1.0 (wwPDB) — URLs as above |
| selection rationale | **DEFAULT pick over imidazolium CID 444234** (recording plan choice): 3D fetched and VERIFIED 200; the quaternary-cation archetype; completes cation_pi + salt_bridge both-direction coverage with the benzamidine set |
| alternates | **imidazolium cation CID 444234** (C3H5N2+, +1) — VERIFIED 2026-09-26: property 200 + SDF 200, ONE record, counts `10 10` (research's "property only" is OVERTAKEN — 3D exists today); **tetramethylammonium CID 6380** (C4H12N+, +1) — VERIFIED 2026-09-26: SDF 200, ONE record, counts `17 16` |

---

## Set 6 — demo-hard-3 · tier: hard · title (amendable): "Cofactors"

| field | content |
|---|---|
| set_id / tier / entry_id | demo-hard-3 / hard / **atp** |
| molecule + formula + heavy atoms | ATP (adenosine 5′-triphosphate), C10H16N5O13P3, **31 heavy** (**medium**) |
| source + fetch URL | PubChem CID **5957**; property `.../cid/5957/property/.../JSON`; 3D `.../cid/5957/SDF?record_type=3d` |
| evidence | webfetch 2026-09-26: property 200 (Title=5'-Atp, C10H16N5O13P3, Charge 0) + SDF 200, ONE record, counts `47 49` (`expect_atom_count` = 47) |
| interaction types + why | h_bond rich (adenine NH/NH₂ donors + acceptors, ribose OH donors, phosphate O acceptors), pi_stacking (adenine), hydrophobic (ribose), cation_pi (AA-cation-over-adenine). **NO salt bridge: ligand phosphate groups are NOT charge-typed** (capability.py / DETECT-04 parity — recorded repo law, honest limitation) |
| halogen/metal flags | false / false |
| PDB complex provenance | **5IT5** (Thermus thermophilus PilB ATPase core with ATP; **ATP confirmed** — inventory also carries AGS/MG/ZN scene ions, 2026-09-26); entry DOI `10.2210/pdb5it5/pdb` (resolves 200); primary paper DOI **10.1016/j.str.2016.08.010** (resolves 200 this session); PLIP reference: 5IT5 |
| protonation record | `'as-recorded'` — neutral as registered (real ATP at pH 7 is ~4−; explicitly NOT modeled — see interaction note; the protonation policy lives in Decision 1/5) |
| license | Public domain (NCBI PubChem) + CC0 1.0 (wwPDB) — URLs as above |
| selection rationale | The energy currency — first **medium** (≥25 heavy) ligand in the bundle; cofactor design icon; anchors the transition into multi-ring/multi-moiety recognition |
| alternates | none |

| field | content |
|---|---|
| set_id / tier / entry_id | demo-hard-3 / hard / **nad** |
| molecule + formula + heavy atoms | NAD (nicotinamide adenine dinucleotide), C21H27N7O14P2, **44 heavy** (**medium**) |
| source + fetch URL | PubChem CID **5892**; property `.../cid/5892/property/.../JSON`; 3D `.../cid/5892/SDF?record_type=3d` |
| evidence | webfetch 2026-09-26: property 200 (Title=Nadide, C21H27N7O14P2, Charge 0) + SDF 200, ONE record, counts `71 75` (`expect_atom_count` = 71) |
| interaction types + why | h_bond rich (2 nucleosides' donors/acceptors), pi_stacking **×2 ring systems** (adenine + nicotinamide amide ring), hydrophobic, cation_pi (AA-cation-over-ring directions). No salt bridge (pyrophosphate not charge-typed — same recorded law as ATP) |
| halogen/metal flags | false / false |
| PDB complex provenance | **8HBA** (NAD-II riboswitch with NAD; **NAD confirmed** — NMN also present, 2026-09-26); entry DOI `10.2210/pdb8hba/pdb` (resolves 200); primary paper DOI **10.1093/nar/gkad102** (VERIFIED at rcsb.org; doi.org = 403 bot-block → U2); PLIP reference: 8HBA |
| protonation record | `'as-recorded'` — neutral as registered (charge-0 record) |
| license | Public domain (NCBI PubChem) + CC0 1.0 (wwPDB) — URLs as above |
| selection rationale | The redox cofactor; largest conjugated system in the hard tier; with ATP it carries the "cofactor recognition" curriculum and supplies the bundle's medium-bucket mass |
| alternates | none |

---

## Set 7 — demo-challenge-1 · tier: challenge · title (amendable): "Halogen & alkaloids"

| field | content |
|---|---|
| set_id / tier / entry_id | demo-challenge-1 / challenge / **chloramphenicol** |
| molecule + formula + heavy atoms | Chloramphenicol, C11H12Cl2N2O5, **20 heavy** (small) |
| source + fetch URL | PubChem CID **5959**; property `.../cid/5959/property/.../JSON`; 3D `.../cid/5959/SDF?record_type=3d` |
| evidence | webfetch 2026-09-26: property 200 (Title=Chloramphenicol, C11H12Cl2N2O5, Charge 0) + SDF 200, ONE record, counts `32 32` (`expect_atom_count` = 32) |
| interaction types + why | **halogen (C–Cl ×2 — the bundle's halogen DEBUT; chlorine compound, correctly NOT fluoro — C–F is excluded per DETECT-03)**, h_bond (2 OH donors + amide N–H donor; nitro/amide/OH oxygen acceptors), pi_stacking (nitrophenyl), hydrophobic |
| halogen/metal flags | **true (Cl ×2)** / false |
| PDB complex provenance | **4CLA** (chloramphenicol acetyltransferase–chloramphenicol — the resistance enzyme complex, the canonical named entry; **CLM confirmed** — CO ion also present, 2026-09-26); entry DOI `10.2210/pdb4cla/pdb` (resolves 200); primary paper DOI **10.1021/bi00229a025** (VERIFIED at rcsb.org; doi.org = 403 bot-block → U2); PLIP reference: 4CLA |
| protonation record | `'as-recorded'` — neutral (Charge 0) |
| license | Public domain (NCBI PubChem) + CC0 1.0 (wwPDB) — URLs as above |
| selection rationale | Antibiotic with the dichloroacetyl motif — **first ligand the detector's halogen branch (02-07b row 6) sees from real data**; feeds Decision 8 (DETECT-03 revisit trigger) |
| alternates | none |

| field | content |
|---|---|
| set_id / tier / entry_id | demo-challenge-1 / challenge / **quinine** |
| molecule + formula + heavy atoms | Quinine, C20H24N2O2, **24 heavy** (small) |
| source + fetch URL | PubChem CID **3034034**; property `.../cid/3034034/property/.../JSON`; 3D `.../cid/3034034/SDF?record_type=3d` |
| evidence | webfetch 2026-09-26: property 200 (Title=Quinine, C20H24N2O2, Charge 0) + SDF 200, ONE record, counts `48 51` (`expect_atom_count` = 48) |
| interaction types + why | h_bond (OH donor; methoxy O + quinoline N acceptors), pi_stacking (quinoline fused rings), hydrophobic strong (quinuclidine cage) — the alkaloid/hydrophobic-heavy contrast to the h_bond-rich sets |
| halogen/metal flags | false / false |
| PDB complex provenance | **9NDX** (quinine-binding RNA aptamer "Tonic"; **QI9 confirmed** — chemcomp name queried: `QI9 = Quinine`, 2026-09-26); entry DOI `10.2210/pdb9ndx/pdb` (resolves 200); primary paper DOI: **NONE recorded** in the RCSB data — honest absence; PLIP reference: 9NDX |
| protonation record | `'as-recorded'` — neutral free base (quinuclidine N unprotonated as registered) |
| license | Public domain (NCBI PubChem) + CC0 1.0 (wwPDB) — URLs as above |
| selection rationale | The alkaloid archetype (malaria epoch); largest carbon framework in the small bucket; hydrophobic/alkaloid diversity slot |
| alternates | none |

---

## Set 8 — demo-veryhard-1 · tier: very_challenging · title (amendable): "Big & iodinated"

| field | content |
|---|---|
| set_id / tier / entry_id | demo-veryhard-1 / very_challenging / **folic_acid** |
| molecule + formula + heavy atoms | Folic acid, C19H19N7O6, **32 heavy** (**medium**; CORRECTED from 38 — see C2) |
| source + fetch URL | PubChem CID **135398658**; property `.../cid/135398658/property/.../JSON`; 3D `.../cid/135398658/SDF?record_type=3d` |
| evidence | webfetch 2026-09-26: property 200 (Title=Folic Acid, C19H19N7O6, Charge 0) + SDF 200, ONE record, counts `51 53` (`expect_atom_count` = 51) |
| interaction types + why | h_bond prolific (pterin N/NH donors + acceptors, glutamate COOH donors), pi_stacking **×2** (pterin + p-aminobenzoate), hydrophobic, cation_pi (AA-cation-over-rings). Tail COOHs not salt-bridge-typed as-recorded |
| halogen/metal flags | false / false |
| PDB complex provenance | **4KMZ** (human folate receptor β (FOLR2)–folate; **FOL confirmed** — K/Cl ions also present, 2026-09-26); entry DOI `10.2210/pdb4kmz/pdb` (resolves 200); primary paper DOI **10.1073/pnas.1308827110** (VERIFIED at rcsb.org; doi.org = 403 bot-block → U2); PLIP reference: 4KMZ |
| protonation record | `'as-recorded'` — neutral as registered |
| license | Public domain (NCBI PubChem) + CC0 1.0 (wwPDB) — URLs as above |
| selection rationale | The vitamin; medium-bucket mass atop two coplanar-ish ring systems; very-challenging anchor next to the iodine carrier |
| alternates | none |

| field | content |
|---|---|
| set_id / tier / entry_id | demo-veryhard-1 / very_challenging / **thyroxine** |
| molecule + formula + heavy atoms | Thyroxine (LT₄), C15H11I4NO4, **24 heavy** (small — 1 below the SIZE_S1=25 boundary; CORRECTED from 21 — see C2) |
| source + fetch URL | PubChem CID **5819**; property `.../cid/5819/property/.../JSON`; 3D `.../cid/5819/SDF?record_type=3d` |
| evidence | webfetch 2026-09-26: property 200 (Title=Thyroxine, C15H11I4NO4, Charge 0) + SDF 200, ONE record, counts `35 36` (`expect_atom_count` = 35) |
| interaction types + why | **halogen (C–I ×4 — iodine donors, the heaviest halogen case)**, h_bond (phenolic OH donor; ether + amino-acid head acceptors/donor), pi_stacking (2 aryl rings), hydrophobic |
| halogen/metal flags | **true (I ×4)** / false |
| PDB complex provenance | **2RIW** (reactive-loop-cleaved human thyroxine-binding globulin + thyroxine; **T44 confirmed** — chemcomp name queried: `T44 = 3,5,3',5'-TETRAIODO-L-THYRONINE`, 2026-09-26); entry DOI `10.2210/pdb2riw/pdb` (resolves 200); primary paper DOI **10.1074/jbc.M110.171082** (resolves 200 this session); PLIP reference: 2RIW |
| protonation record | `'as-recorded'` — neutral as registered (head NH₂ + COOH; zwitterion not synthesized, same policy) |
| license | Public domain (NCBI PubChem) + CC0 1.0 (wwPDB) — URLs as above |
| selection rationale | The hormone; **four C–I bonds in one ligand** — the halogen stress case beside chloramphenicol's debut; feeds Decision 8 (DETECT-03 revisit trigger) |
| alternates | none |

---

## Set 9 — demo-veryhard-2 · tier: very_challenging · title (amendable): "Metalloporphyrin"

| field | content |
|---|---|
| set_id / tier / entry_id | demo-veryhard-2 / very_challenging / **heme** |
| molecule + formula + heavy atoms | Heme (protoporphyrin IX–Fe), C34H32FeN4O4, **43 heavy** (medium) |
| source + fetch URL | RCSB CCD **HEM**, ideal coordinates `https://files.rcsb.org/ligands/view/HEM_ideal.sdf` (plain `.sdf` 404s — `_ideal` required, research-verified) |
| evidence | webfetch 2026-09-26: SDF 200, ONE record (`$$$$`×1), counts `75 82` (75 atoms incl H / 82 bonds; `expect_atom_count` = 75); atom-block element tally VERIFIED: **C34 H32 N4 O4 Fe1**; header name line reads **`HEM`** (see C7); CCD chemical name via chemcomp endpoint: `PROTOPORPHYRIN IX CONTAINING FE` (VERIFIED) |
| interaction types + why | **metal (Fe in-molecule — the detector's metal gate via `ligand_has_metal`; Fe ∈ approved metal list {…FE…} per DETECT-03 row; the ONLY verified metal-bearing candidate in the sourcing research)**, pi_stacking (porphyrin macrocycle aromatic bonds), h_bond (propionate OH donors as-recorded), hydrophobic |
| halogen/metal flags | false / **true (Fe ×1)** |
| PDB complex provenance | **1MBN** (Kendrew's sperm-whale myoglobin — the heme classic; **HEM confirmed** — OH also present, 2026-09-26); entry DOI `10.2210/pdb1mbn/pdb` (resolves 200); primary paper DOI: **NONE recorded** in the RCSB data (1960 structure) — honest absence; PLIP reference: 1MBN |
| protonation record | `'as-recorded'` — the RCSB ideal SDF as published (propionate carboxyls protonated in the ideal geometry; charge field 0) |
| license | **CC0 1.0 (wwPDB)** — CCD ideal files are PDB-archive data: https://www.wwpdb.org/about/usage-policies (VERIFIED 2026-09-26 verbatim: "Data files contained in the PDB archive are available under the CC0 1.0 Universal (CC0 1.0) Public Domain Dedication. Users of PDB data are encouraged to attribute the original authors of the PDB structure data where possible."). The 1MBN reference metadata carries the same CC0 |
| selection rationale | **The metal-coordination showcase** — first real-world exercise of the whole 02-07b metal branch + the 02-08 supply target (≥1 metal-present entry); porphyrin = the archetypal biological macrocycle |
| alternates | none (only verified metal-bearing candidate; a lone metal ion as ligand is DESIGN-REJECTED per sourcing RQ7 item 4 — degenerate bounding sphere) |

---

## Evidence corrections vs 08-RESEARCH-sourcing.md (all re-verified this session, 2026-09-26)

- **C1 — Benzoic acid CID error (research error, critical).** Research/plan-context proposed "Benzoic acid CID 3979 (C7H6O2)". Live property fetch of **CID 3979 returns `N-(3-benzylpurin-6-yl)acetamide`, C27H39N3O2** — the CID belongs to a different compound. Name lookup (`compound/name/benzoic%20acid`) resolves benzoic acid to **CID 243** (property + 3D SDF VERIFIED today). The proposal uses 243.
- **C2 — Heavy-atom recounts (research counted carbons in several rows).** Verified against property formulas: citric acid **6 → 13**, acetate **2 → 4**, glutamic acid **5 → 10**, acetylcholine **9 → 10**, folic acid **38 → 32**, thyroxine **21 → 24**. The corrected bundle size distribution still reads **12 small / 4 medium / 0 large** (thyroxine 24 stays just under SIZE_S1=25; folic acid 32 stays medium) — predicted supply from plan Task-2 item 4 is unchanged.
- **C3 — Recorded charges differ from research claims.** Benzamidine CID 2332 is **neutral** (claim "cation_pi (+1 amidinium)" incorrect for this CID); glutamic acid CID 33032 is **neutral** (claim "−1" incorrect); benzoic acid CID 243 is **neutral** (claim "salt_bridge as benzoate(−1)" incorrect). All three keep `'as-recorded'` with honest typing notes; the charged forms exist as VERIFIED alternates (benzamidinium 444655, benzoate 242) or are rejected by policy (deprotonated glutamate — same citrate rule).
- **C4 — Guanidinium 3D RESOLVED.** Research left CID 32838 "property only (3D not fetched)". This session: **3D SDF 200, ONE record, counts `10 9`** — VERIFIED primary; no substitution needed.
- **C5 — Citrate provenance re-pinned.** Research's top hit **1O7X carries NO nonpolymer entities** in the RCSB Data API (citrate not present as a ligand) → rejected at the plan's confirmation step; alternates 2R9E (SDX) and 2R26 (CMC/OAA) confirmed-missing CIT too. Citrate is re-pinned to **8FUY** (CIT confirmed).
- **C6 — Alternates' 3D availability corrected.** Imidazolium CID 444234 and tetramethylammonium CID 6380 were "property only" at research; both fetched **200, ONE record** today (VERIFIED). Benzamidinium 444655 and benzoate 242 identified + VERIFIED as the charged-form alternates. Vancomycin (CID 14969) remains 3D-404 per research (not re-fetched — it is a rejected stretch, not an approved row); cyclosporin A / FAD stay REJECTED (3D 404).
- **C7 — HEM name field.** Research expected the CCD name field to read "HEME". The `HEM_ideal.sdf` header name line reads **`HEM`**; the CCD chemical name is `PROTOPORPHYRIN IX CONTAINING FE` (VERIFIED via the chemcomp endpoint). Recorded truthfully — HEM is both the CCD code and the file's own name line.

## UNVERIFIED items deferred to the human (exact checks — none is ever silently assumed)

- **U1 — PubChem submitter-rights caveat (license nuance).** The NCBI policy page's Molecular Data section (VERIFIED verbatim) says NCBI "places no restrictions on the use or distribution" but that "some submitters of the original data may claim patent, copyright, or other intellectual property rights". The web docs disclaimer `https://pubchem.ncbi.nlm.nih.gov/docs/disclaimer` is **unfetchable from this environment** (HTTP 404 now; previously JS-walled). **Human check:** open that disclaimer in a browser and confirm the caveat does not apply to our 15 chosen drug-like/metabolite CIDs (each is a single well-known compound, not a submitter-restricted deposit). Verdict to be recorded VERIFIED or flagged in DATA_SOURCES.md.
- **U2 — 7 paper DOIs blocked by publisher bot-guards.** 10.1080/10611860400024078 (1OXR), 10.1099/mic.0.043653-0 (3G6M), 10.1021/bi00229a025 (4CLA), 10.1073/pnas.1308827110 (4KMZ), 10.1126/science.adw1264 (9E3E), 10.1093/nar/gkad102 (8HBA) — each is **VERIFIED in the RCSB Data API entry record** but direct `doi.org` resolution returns HTTP 403 from this environment (Taylor & Francis / Microbiology Society / ACS / PNAS / Science / OUP bot-blocking). **Human check (2–3 spot-checks suffice):** visit e.g. `https://doi.org/10.1080/10611860400024078` and `https://doi.org/10.1126/science.adw1264` in a browser; each should land on the correct article page.
- **U3 — PubChem canonical database citation.** `https://pubchemdocs.ncbi.nlm.nih.gov/publications` is **JS-walled to this environment** ("JavaScript is required"). **Human check:** open it and confirm the current PubChem canonical citation (NAR database paper, e.g. the latest Kim et al. entry) to quote in DATA_SOURCES.md. Until confirmed, DATA_SOURCES.md will cite PubChem by CID URLs + the two VERIFIED policy pages and mark the canonical citation "(confirm, U3)" rather than guess.
- **U4 — PDBe per-entry pages.** `https://www.ebi.ac.uk/pdbe/entry/pdb/1oxr` returns the JS app shell only from this environment ("PDBe Connect Pages"). **Optional human check:** confirm the entry page renders per-entry ligand/interaction info as the secondary provenance link proposed by the sourcing research (RQ4). Not required for approval — every provenance claim already stands on RCSB-verified records.

---

## Decisions (open items, each with its DEFAULT — the human may override any at approval)

1. **Multi-state policy (sourcing RQ7). DEFAULT: ONE molecule record per SDF file, `states_expected: 1`, conformer/protonation chosen at proposal time and recorded per row above; the bundler REFUSES any multi-record source naming the entry (split or choose at curation — never collapse silently).** The 08-01 builder already enforces this; all 16 candidates verified single-record today.
2. **Tier vocabulary. DEFAULT: manifest tokens exactly `easy | hard | challenge | very_challenging`; display labels Easy / Hard / Challenge / Very challenging; `TIER_ORDER` as shipped in 08-02 (setup_form.py), dropdown order Easy → Hard → Challenge → Very challenging.** Formal ratification of the vocabulary 08-02 pre-wired with its 'Other' escape group.
3. **Dev-set visibility. DEFAULT: `demo-dev-1` REMAINS in the manifest and the dropdown under Easy** (development set keeps its dev role and survives as a regression oracle for `test_demo_data.py` and the dry-run pipeline check). Removing it is an explicit human override.
4. **Large-bucket supply. DEFAULT: accept the generator's NEAREST-BUCKET fallback as the designed large-bucket carrier** (curated bundle = **12 small / 4 medium / 0 large**, re-measured after correction C2 — matches the plan-task prediction). A true ≥60-heavy ligand (vancomycin 2D / an RCSB large CCD) is an OPTIONAL stretch, **NOT required**; vancomycin 3D is 404 today (research-verified).
5. **Citrate ionization form. DEFAULT: free acid CID 311 `'as-recorded'`** — capability's COOH-never-anion guard means its carboxylates are NOT salt-bridge-typed, and demo-easy-2's salt-bridge slot is carried by acetate (−1, VERIFIED). Deprotonated-citrate sourcing is REJECTED for v1 (only ChemSpider-free ChEBI molfile route exists and it is 2D-only). The same rule was applied consistently to glutamic acid and the benzoic/thyroxine/folic acid-free COOHs (correction C3).
6. **File naming. DEFAULT: `ligands/<set_id>-<entry_id>.sdf` for every curated file** (e.g. `ligands/demo-easy-2-acetate.sdf`); collision-free with the dev set's legacy `ligands/acetate.sdf` / `ligands/benzamide.sdf`, which keep their names via spec `file` overrides (08-01 law).
7. **Payload provenance. DEFAULT: saved-game payload ligand blocks keep `provenance: ''` (generator.py:864 UNCHANGED);** citations live in the manifest set-level fields + `scripts/demo_specs/*.json` + `docs/DATA_SOURCES.md` (08-09) — never in the payload. `MANIFEST.json` entries stay EXACTLY the 14 REQUIRED_ENTRY_KEYS (08-01 law); deeper provenance flows through specs → `--report-only` → DATA_SOURCES.md.
8. **Context complexes. DEFAULT: NOT SHIPPED.** PDB complex files for the game scene are outside the frozen manifest format and have no runtime consumer; the messy scene for the cleanup field test is a **LOCAL script-built ions+water fixture** (smoke_21, dev-fixture pattern, headless-deterministic), with **1OXR cited in DATA_SOURCES.md as the real-world analog** (its crystallographic Ca²⁺, in the approved metal list, demonstrates that prefix-scoped cleanup never touches non-game objects; 1S0R's CA is a second analog).
9. **DETECT-03 revisit trigger. DEFAULT: RECORDED AS TRIGGERED-FOR-CHECK.** The curated data brings the detector its first real **metal** (heme Fe) and **halogen** (chloramphenicol C–Cl, thyroxine C–I) ligands. The headless detector-coverage check runs in 08-11; any threshold surprise becomes a **DETECTOR_VERSION bump PROPOSAL in a new plan (never a silent edit)** — the 02-01 GATE §4.7 policy, honoring the provisional-approval caveat (thresholds were dataset-provisional; the dataset is now defined).
10. **Entry counts + set titles. DEFAULT: 16 curated ligands across 9 sets** (2+2+1+2+2+2+2+2+1), size distribution **12 small / 4 medium / 0 large**; 18 ligands total including the dev set's 2; supply re-measured in 08-10 (nearest-bucket behavior under real grids). Dropdown titles (amendable): *Everyday organics*, *Metabolites & ions*, *Caffeine*, *Trypsin classics*, *Charged messengers*, *Cofactors*, *Halogen & alkaloids*, *Big & iodinated*, *Metalloporphyrin*.
