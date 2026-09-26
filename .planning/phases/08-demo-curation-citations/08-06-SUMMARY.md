---
phase: 08-demo-curation-citations
plan: 06
subsystem: demo-data
tags: [demo-curation, sdf, pubchem, manifest, smoke-02, data-battery, cation-pi, medium-size-class, python3.6]

# Dependency graph
requires:
  - phase: 08-demo-curation-citations
    provides: 08-01 bundling pipeline (scripts/build_demos.py + data
      battery), 08-04 [GATE] APPROVED 2026-09-26 proposal rows
      (08-PROPOSALS.md Sets 4-6 incl. corrections C3/C4 and the 16/16
      atom-count re-verification), 08-05 proven per-set landing loop
provides:
  - Three curated hard-tier demo sets (demo-hard-1/2/3, 6 ligands)
    bundled via the 08-01 pipeline: pre-downloaded single-record 3D SDFs
    with in-run derived counts + sha256
  - The bundle's FIRST medium size-class entries (ATP 31 heavy, NAD 44
    heavy, both derived 'medium') - the generator's medium bucket and the
    NEAREST-BUCKET fallback for large-tier games are now non-empty
  - Charge-verified cation-pi/salt-bridge carriers: guanidinium +1
    (02-06 guanidino-centroid law exercised), acetylcholine +1
    (quaternary NMe3+, outside the PLIP tertamine veto)
  - specs scripts/demo_specs/demo-hard-{1,2,3}.json carrying the
    approved per-entry provenance (CID fetch URL, PDB complex + DOIs,
    PLIP ref, protonation why, notes)
  - MANIFEST.json grown to 7 sets / 13 entries; demo-dev-1 and the easy
    sets byte-identical; GEN-06 Hard x3 slots filled
affects: [08-07 challenge/very-challenging tiers (same loop),
  08-09 DATA_SOURCES.md (--report-only now prints 13 real rows),
  08-10 supply re-measurement (real medium-bucket distribution),
  08-11 detector-coverage review]

# Tech tracking
tech-stack:
  added: [charged-species curated SDF content (guanidinium +1,
    acetylcholine +1), medium size-class curated content (ATP, NAD)]
  patterns: [approved-DEFAULT transcription: alternates (444655/444234/
    6380) recorded but NOT substituted because the plan did not call for
    them; derived size_class wins on live data and matched the proposal
    prediction exactly]

key-files:
  created: [scripts/demo_specs/demo-hard-1.json,
    scripts/demo_specs/demo-hard-2.json,
    scripts/demo_specs/demo-hard-3.json,
    aamatch/data/ligands/demo-hard-1-benzamidine.sdf,
    aamatch/data/ligands/demo-hard-1-guanidinium.sdf,
    aamatch/data/ligands/demo-hard-2-glutamic_acid.sdf,
    aamatch/data/ligands/demo-hard-2-acetylcholine.sdf,
    aamatch/data/ligands/demo-hard-3-atp.sdf,
    aamatch/data/ligands/demo-hard-3-nad.sdf]
  modified: [aamatch/data/MANIFEST.json]

key-decisions:
  - "Benzamidine bundled NEUTRAL as CID 2332 per approved C3 (Charge 0
    as registered; the approved charged alternate benzamidinium chloride
    CID 444655 was NOT substituted - the plan's default row is binding);
    cation_pi showcase on this entry is AA-cation-over-lig-ring only."
  - "Guanidinium bundled as CID 32838 (+1; the 08-04 3D-resolution per
    C4 held - single-record 200 fetch, counts 10/9). Its manifest entry
    derives formal_charge_sum +1; the spec notes cite the 02-06 recorded
    law (ligand guanidino center = centroid of the 3 bonded Ns) as the
    reason this ligand exercises that detector branch."
  - "Glutamic acid bundled NEUTRAL as CID 33032 per approved C3
    (physiological zwitterion deliberately NOT synthesized; parallel
    policy to citrate Decision 5); acetylcholine CID 187 is the DEFAULT
    approved +1 pick (imidazolium 444234 / tetramethylammonium 6380
    alternates NOT substituted - plan did not call for them)."
  - "ATP and NAD derive size_class 'medium' (31 / 44 heavy) exactly as
    the proposal predicted - no derivation-vs-prediction delta to flag;
    both neutral as registered (Decision 1) with phosphates NOT
    salt-bridge-typed per the DETECT-04 parity law (spec interaction
    columns say h_bond/pi_stacking/hydrophobic/cation_pi only)."

patterns-established:
  - "Charge-showcase transcription: an entry's recorded charge is taken
    from the APPROVED proposal row only (C3 neutral-as-registered rulings
    outrank stale research claims of charged forms); expect_atom_count
    guards (17/10/19/26/47/71) passed on every live fetch."

# Metrics
duration: ~15 min
completed: 2026-09-26
---

# Phase 8 Plan 06: Hard-Sets Bundling Summary

**Hard tier bundled: the three curated Hard demo sets (benzamidine +
guanidinium, glutamic acid + acetylcholine, ATP + NAD) fetched,
manifest-derived, SMOKE-02-proven and committed atomically via the 08-01
pipeline - MANIFEST.json now 7 sets / 13 entries with the FIRST medium
size-class supply (ATP 31 heavy, NAD 44 heavy) and charge-verified +1
cation carriers; 906/906 WSL green, zero deviations requiring fixes.**

## Performance

- **Duration:** ~15 min
- **Started:** 2026-09-26T14:30Z
- **Completed:** 2026-09-26T14:42Z
- **Tasks:** 3/3
- **Files created:** 9 (3 specs + 6 SDFs); modified: 1 (MANIFEST.json)

## Accomplishments

- **demo-hard-1 "Trypsin classics"** (commit `aca6b8f`): benzamidine CID
  2332 (17 atoms/17 bonds/heavy 9/**charge 0** - neutral free base as
  registered per approved C3; the charged 444655 alternate NOT
  substituted) + guanidinium CID 32838 (10/9/heavy 4/**charge +1** -
  the set's salt_bridge carrier and ligand-side cation_pi showcase;
  spec notes cite the 02-06 guanidino-centroid law). Provenance: 1S0R
  (paper DOI honestly absent) and 5NWQ. expect_atom_count guards 17/10
  passed.
- **demo-hard-2 "Charged messengers"** (commit `6aadd02`): glutamic_acid
  CID 33032 (19/18/heavy 10/**charge 0** - neutral free acid per C3;
  zwitterion NOT synthesized per Decision-5-parallel policy) +
  acetylcholine CID 187 (26/25/heavy 10/**charge +1** - the permanently
  charged quaternary NMe3+; sits OUTSIDE the PLIP tertamine veto, the
  boundary complement to guanidinium; DEFAULT approved pick).
  Provenance: 2JFO and 9E3E. Guards 19/26 passed.
- **demo-hard-3 "Cofactors"** (commit `a41cb01`): atp CID 5957
  (47/49/heavy 31/charge 0 -> **MEDIUM**) + nad CID 5892
  (71/75/heavy 44/charge 0 -> **MEDIUM**) - the bundle's first medium
  size-class entries; derived class matched the proposal prediction
  exactly, no delta. Both neutral as registered; phosphates NOT
  salt-bridge-typed per the DETECT-04 parity law (honest limitation
  recorded in the specs). Provenance: 5IT5 and 8HBA. Guards 47/71
  passed.
- MANIFEST.json: 7 sets (dev + 3 easy + 3 hard) / 13 entries; container
  shape frozen (kind 'manifest', version 1, magic AAMATCH,
  manifest_version 1); entries remain exactly the 14
  REQUIRED_ENTRY_KEYS (battery test 03).
- Disk sha256 == manifest sha256 on all 6 new SDFs (SMOKE-02 +
  --report-only agree).

## Task Commits

Each set was committed atomically (SDFs + MANIFEST.json + spec in one
commit), SMOKE-02 run BEFORE each commit:

1. **Task 1: bundle demo-hard-1 (benzamidine + guanidinium)** - `aca6b8f` (feat)
2. **Task 2: bundle demo-hard-2 (glutamic acid + acetylcholine)** - `6aadd02` (feat)
3. **Task 3: bundle demo-hard-3 (ATP + NAD) + full-suite regression** - `a41cb01` (feat)

**Plan metadata:** (recorded below; docs commit)

## Files Created/Modified

- `scripts/demo_specs/demo-hard-{1,2,3}.json` - approved curation
  inputs: set-level license/provenance (fetched 2026-09-26, U1 canonical
  PubChem citation, CC0 wwPDB complex metadata) + per-entry provenance
  (source_url, pdb_id, entry_doi, paper_doi, plip, notes) transcribed
  from APPROVED 08-PROPOSALS.md Sets 4-6 rows only
- `aamatch/data/ligands/demo-hard-1-benzamidine.sdf`,
  `demo-hard-1-guanidinium.sdf`, `demo-hard-2-glutamic_acid.sdf`,
  `demo-hard-2-acetylcholine.sdf`, `demo-hard-3-atp.sdf`,
  `demo-hard-3-nad.sdf` - single-record PubChem 3D SDFs fetched through
  `scripts/build_demos.py --fetch` only
- `aamatch/data/MANIFEST.json` - regenerated by the builder three times
  (replace-or-insert one set per run; demo-dev-1 and the easy sets
  byte-identical, proven by --dry-run / --report-only exit 0)

## Test/Smoke Results

- `python3.6 -m py_compile aamatch/*.py scripts/build_demos.py` - OK
- `python3.6 -m unittest discover -s tests -v` - **906/906 OK**
  (full suite incl. purity gates + the 10-test data battery, which now
  covers all 6 curated sets: license/provenance/title non-empty, tier
  vocabulary, spec provenance depth, spec coverage)
- `bash smoke/run_smoke.sh smoke/smoke_02_manifest.py 180` - **===
  SMOKE-02 PASS ===** after ALL THREE sets (every entry of all 7 sets
  load-verified in real PyMOL: sha256/atoms/bond-multiset/charge/states/
  element-scan flags; no tmp leak)
- `python3.6 scripts/build_demos.py --report-only` - exit 0, "all specs
  match the committed manifest (7 spec(s), 13 entrie(s))"; the
  DATA_SOURCES.md provenance rows print for all 11 curated entries
- `--dry-run` on demo-dev-1 - exit 0, derived == committed on every key
  (multi-set assembly never disturbs other sets)
- Manifest charge/`size_class` spot checks:
  - demo-hard-1: `[('benzamidine', 0, 'small'), ('guanidinium', 1, 'small')]`
  - demo-hard-2: `[('glutamic_acid', 0, 'small'), ('acetylcholine', 1, 'small')]`
  - demo-hard-3: `[('atp', 0, 'medium'), ('nad', 0, 'medium')]`

## Decisions Made

- **Approved-DEFAULT transcription rule applied:** every approved
  alternate (benzamidinium chloride 444655, imidazolium 444234,
  tetramethylammonium 6380) was recorded in the spec notes but NOT
  substituted, because the plan called for the default rows. Per the
  gate context, alternates are used only if the plan explicitly calls
  for them - silently swapping would re-open the gate.
- **Derivation-vs-prediction check (plan Task 3 contingency):** ATP 31
  heavy and NAD 44 heavy both derived `size_class: 'medium'`, matching
  the proposal's prediction exactly - the delta-flag path stayed unused.
- **1S0R paper_doi recorded as "" (honest absence)** per the approved
  row (RCS record carries no primary citation; title verified).

## Deviations from Plan

**No Rule 1-3 fixes required - zero code/data repairs.** Every fetch
returned 200 single-record records matching the approval-time
re-verification counts exactly (17/10/19/26/47/71), SMOKE-02 passed on
first run after each set, and no substitution/ALTERNATE path was needed.

## Issues Encountered

None.

## User Setup Required

None - network fetches used the builder's sanctioned urllib path
(User-Agent AA-match-build/1.0, timeout 60 s).

## Next Phase Readiness

- GEN-06 Hard x3 slots FILLED; 08-07 (demo-challenge-1 + demo-challenge-2
  + demo-veryhard-1/2) repeats this exact loop with its approved rows -
  the halogen flag debut (chloramphenicol Cl x2), the metal flag debut
  (heme), and heme's RCSB `_ideal` fetch path all live there.
- 08-09 can run `--report-only` today to produce 11 real provenance
  rows (+2 dev rows) for DATA_SOURCES.md.
- 08-10 supply re-measurement: 13 ligands bundled today (dev 2 +
  curated easy 5 + hard 6); the medium bucket is now non-empty
  (ATP/NAD), so the NEAREST-BUCKET fallback for large-tier games has
  real supply; the full 18 lands once 08-07 completes.
- 08-11's detector-coverage review now has real charged-species ligands
  staged (guanidinium/acetylcholine cation_pi + salt_bridge carriers);
  halogen/metal carriers arrive with 08-07.

---
*Phase: 08-demo-curation-citations*
*Completed: 2026-09-26*
