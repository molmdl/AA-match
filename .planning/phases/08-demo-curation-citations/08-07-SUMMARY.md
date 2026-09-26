---
phase: 08-demo-curation-citations
plan: 07
subsystem: demo-data
tags: [demo-curation, sdf, pubchem, rcsb, manifest, smoke-02, data-battery,
  halogen-debut, metal-debut, heme, python3.6]

# Dependency graph
requires:
  - phase: 08-demo-curation-citations
    provides: 08-01 bundling pipeline (scripts/build_demos.py + data
      battery), 08-04 [GATE] APPROVED 2026-09-26 proposal rows
      (08-PROPOSALS.md Sets 7-9 incl. corrections C2/C7 and the 16/16
      atom-count re-verification), 08-05/08-06 proven per-set landing
      loop
provides:
  - The final three curated demo sets (demo-challenge-1,
    demo-veryhard-1, demo-veryhard-2; 5 ligands) bundled via the 08-01
    pipeline: pre-downloaded single-record SDFs with in-run derived
    counts + sha256
  - The HALOGEN DEBUT: chloramphenicol (2x C-Cl) and thyroxine (4x C-I)
    - halogen_present True, element-scan verified by the builder AND
    load-verified by SMOKE-02 (first real-data exercise of the 02-07b
    halogen branch)
  - The METAL DEBUT: heme (RCSB HEM_ideal.sdf, Fe in-molecule) -
    metal_present True, same dual verification (first real-data exercise
    of the 02-07b metal branch + the 02-08 >=1-metal supply target)
  - The FULL curated manifest: 10 sets / 18 ligands (16 curated + 2 dev),
    tier census exactly 3 easy + 3 hard + 1 challenge + 2 very_challenging
    (+ dev set) - GEN-06 slot inventory COMPLETE; all 7 interaction
    types supply-real
  - specs scripts/demo_specs/demo-{challenge-1,veryhard-1,veryhard-2}.json
    carrying the approved per-entry provenance (PDB complex + DOIs,
    PLIP refs, protonation whys, honest absences, the heme charge delta)
affects: [08-08 phase smoke suite (10-set census + flag-branch coverage
  now satisfiable), 08-09 DATA_SOURCES.md (--report-only prints 18 real
  rows incl. halogen/metal columns), 08-10 supply re-measurement (final
  12 small / 4 medium / 0 large curated distribution), 08-11 headless
  detector-coverage check (chloramphenicol/thyroxine/heme scenes) +
  grouped-dropdown [HUMAN] check (4 real tiers now populated)]

# Tech tracking
tech-stack:
  added: [halogen-bearing curated SDF content (chloramphenicol Cl x2,
    thyroxine I x4), metal-bearing curated SDF content (heme Fe, RCSB
    `_ideal` fetch path), RCSB/CCD-licensed (CC0 wwPDB) bundled data]
  patterns: [approved-row transcription ONLY (alternate-free Sets 7-9;
    nothing substituted), derivation-vs-narrative delta flagged + the
    derived truth recorded honestly (heme formal_charge_sum -4 vs the
    proposal's 'charge field 0' parenthetical - the file ships
    as-recorded)]

key-files:
  created: [scripts/demo_specs/demo-challenge-1.json,
    scripts/demo_specs/demo-veryhard-1.json,
    scripts/demo_specs/demo-veryhard-2.json,
    aamatch/data/ligands/demo-challenge-1-chloramphenicol.sdf,
    aamatch/data/ligands/demo-challenge-1-quinine.sdf,
    aamatch/data/ligands/demo-veryhard-1-folic_acid.sdf,
    aamatch/data/ligands/demo-veryhard-1-thyroxine.sdf,
    aamatch/data/ligands/demo-veryhard-2-heme.sdf]
  modified: [aamatch/data/MANIFEST.json]

key-decisions:
  - "File naming per the 08-05 single-rule law: all 5 files are
    ligands/<set_id>-<entry_id>.sdf with approved entry_ids verbatim
    (demo-veryhard-1-folic_acid.sdf); the plan frontmatter's sketch
    'demo-veryhard-1-folic-acid.sdf' (hyphen) was NOT followed - the
    battery's spec-coverage test computes the same rule, so a hyphen
    there would have failed spec-vs-manifest agreement. Plan-text typo
    recorded, no substitution involved."
  - "Heme ships AS-RECORDED with derived formal_charge_sum -4 (the RCSB
    ideal SDF's M CHG annotations - carboxylates deprotonated;
    builder-derived AND SMOKE-02/PyMOL-agreed -4 == -4). The proposal
    narrative's '(propionate carboxyls protonated ... charge field 0)'
    parenthetical does not match the file; the delta is recorded in the
    spec notes + here, per the honesty law (derived truth of the
    approved file wins; no data substitution). Counts/atoms/flags/
    identity match the approved row exactly (75/82/43 heavy/Fe1/'HEM')."
  - "Set 9 uses the RCSB `_ideal` fetch path and the set-level license
    'CC0 1.0 (wwPDB)' with license_url https://www.wwpdb.org/about/
    usage-policies - the first non-PubChem set-level license; the
    builder/battery manifest shape carried it unchanged (license is a
    free non-empty string for curated sets)."

patterns-established:
  - "Flag-branch debuts are dual-verified: the builder's element scan
    (METAL_ELEMENTS incl. FE / HALOGEN_ELEMENTS Cl/Br/I derivation)
    commits the flag and SMOKE-02's real-PyMOL element-scan
    cross-check agrees load-side BEFORE the commit - exercised here for
    chlorine, iodine, and iron for the first time on real data."

# Metrics
duration: ~7 min (execution 14:48Z-14:55Z)
completed: 2026-09-26
---

# Phase 8 Plan 07: Challenge + Very-Challenging Sets Bundling Summary

**The final tier slots landed: demo-challenge-1 (chloramphenicol +
quinine), demo-veryhard-1 (folic acid + thyroxine), and demo-veryhard-2
(heme) fetched, manifest-derived, SMOKE-02-proven and committed
atomically via the 08-01 pipeline - the halogen flag debut (Cl x2 /
I x4) and the metal flag debut (Fe) are now real, dual-verified data;
MANIFEST.json complete at 10 sets / 18 entries with the GEN-06 census
exact (3+3+1+2 curated tiers + dev); 906/906 WSL green; one recorded
narrative-delta fix (heme charge), zero code/data repairs.**

## Performance

- **Duration:** ~7 min
- **Started:** 2026-09-26T14:48Z
- **Completed:** 2026-09-26T14:55Z
- **Tasks:** 3/3
- **Files created:** 8 (3 specs + 5 SDFs); modified: 1 (MANIFEST.json)

## Accomplishments

- **demo-challenge-1 "Halogen & alkaloids"** (commit `12e08a5`):
  chloramphenicol CID 5959 (32 atoms/32 bonds/heavy 20/charge 0 -
  **halogen_present True, the bundle's C-Cl halogen debut, 2 donors**)
  + quinine CID 3034034 (48/51/heavy 24/charge 0 - halogen/metal
  False, the set's flag-contrast row; hydrophobic-strong alkaloid).
  Provenance: 4CLA (paper DOI 10.1021/bi00229a025, U2 rcsb-verified)
  + 9NDX (honest-absence paper DOI). Guards 32/48 passed.
- **demo-veryhard-1 "Big & iodinated"** (commit `af51384`):
  folic_acid CID 135398658 (51/53/heavy 32 per C2 - derived 'medium',
  exactly the proposal prediction) + thyroxine CID 5819 (35/36/heavy 24
  per C2, 1 below the SIZE_S1=25 boundary - **halogen_present True via
  4x C-I, the iodine branch**; iodine count cross-checked vs proposal
  evidence C15H11I4NO4 and recorded in the spec notes). Provenance:
  4KMZ (U2 rcsb-verified paper DOI) + 2RIW (both DOIs resolve 200).
  Guards 51/35 passed.
- **demo-veryhard-2 "Metalloporphyrin"** (commit `c7b8784`): heme via
  RCSB `HEM_ideal.sdf` (75/82/heavy 43 - derived 'medium' as predicted;
  header 'HEM' per C7; element tally C34 H32 N4 O4 **Fe1**) -
  **metal_present True via FE in the DETECT-03 approved list; first
  real exercise of the 02-07b metal branch** (SMOKE-02 element scan
  ['C','FE','H','N','O'] -> flag True). Derived formal_charge_sum
  **-4**: the proposal narrative's 'charge field 0' parenthetical does
  not match the file - delta recorded in the spec notes; the approved
  file ships as-recorded. Provenance: 1MBN (Kendrew myoglobin;
  honest-absence paper DOI); license **CC0 1.0 (wwPDB)** - the bundle's
  first non-PubChem set-level license.
- MANIFEST.json: **10 sets / 18 entries** (dev 2 + easy 5 + hard 6 +
  challenge 2 + veryhard 3), container shape frozen (kind 'manifest',
  version 1, manifest_version 1), entries still exactly the 14
  REQUIRED_ENTRY_KEYS; dev + easy + hard payloads byte-identical.
- **GEN-06 slot inventory COMPLETE:** tier census 3 easy + 3 hard +
  1 challenge + 2 very_challenging curated (+ dev easy) +
  18 = 16 curated + 2 dev ligands.
- **7-type interaction diversity is supply-real** (mapped from the
  approved proposal rows): h_bond (aspirin/citric/ATP/folic/heme/...),
  salt_bridge (acetate -1, guanidinium +1, acetylcholine +1),
  pi_stacking (aspirin/benzamidine/quinine/folic/heme/... - 10
  ring-bearing ligands), cation_pi (benzamidine/guanidinium/
  acetylcholine/caffeine/folic), hydrophobic (quinine/thyroxine/heme/
  ...), **halogen (chloramphenicol, thyroxine)**, **metal (heme)**.

## Task Commits

Each set was committed atomically (SDF(s) + MANIFEST.json + spec in one
commit), SMOKE-02 + data battery run BEFORE each commit:

1. **Task 1: bundle demo-challenge-1 (chloramphenicol + quinine)** - `12e08a5` (feat)
2. **Task 2: bundle demo-veryhard-1 (folic acid + thyroxine)** - `af51384` (feat)
3. **Task 3: bundle demo-veryhard-2 (heme) + full-suite regression** - `c7b8784` (feat)

**Plan metadata:** (recorded below; docs commit)

## Test/Smoke Results

- `python3.6 -m py_compile aamatch/*.py scripts/build_demos.py` - OK
- `python3.6 -m unittest discover -s tests -v` - **906/906 OK** (full
  suite incl. purity gates + the 10-test data battery, which now covers
  all 9 curated sets: license/provenance/title non-empty, tier
  vocabulary, spec provenance depth, spec coverage)
- `bash smoke/run_smoke.sh smoke/smoke_02_manifest.py 180` - **===
  SMOKE-02 PASS ===** after ALL THREE sets (every entry of all 10 sets
  load-verified in real PyMOL: sha256/atoms/bond-multiset/charge/states/
  element-scan flags; chloramphenicol scan includes 'CL' flag True;
  thyroxine scan includes 'I' flag True; heme scan includes 'FE' flag
  True; no tmp leak)
- `python3.6 scripts/build_demos.py --report-only` - exit 0, "all specs
  match the committed manifest (10 spec(s), 18 entrie(s))"; the
  DATA_SOURCES.md provenance rows print for all 18 entries incl. the
  halogen yes/no and metal yes/no columns (heme row: metal 'yes')
- `--dry-run` on demo-dev-1 - exit 0, derived == committed on every key
  (multi-set assembly never disturbs other sets; dev payload
  byte-identical through all three landings)
- Manifest census + flag checks (plan verification):
  - `10 ['challenge','easy','easy','easy','easy','hard','hard','hard',
    'very_challenging','very_challenging']`, 18 entries
  - metal True x1 (heme), halogen True x2 (chloramphenicol, thyroxine)
  - per-set flags: demo-challenge-1
    `[('chloramphenicol', True, False), ('quinine', False, False)]`;
    demo-veryhard-1 `[('folic_acid', False, False, 'medium'),
    ('thyroxine', True, False, 'small')]`; demo-veryhard-2
    `[('heme', True, False, 'medium', 43)]`
- `git log --oneline` - one atomic commit per set across the phase
  (08-05 x3, 08-06 x3, 08-07 x3) + per-plan docs commits

## Decisions Made

- **File naming law wins over plan-frontmatter sketch:** the plan's
  `files_modified` frontmatter listed `demo-veryhard-1-folic-acid.sdf`
  (hyphen); the binding 08-05 naming law (`ligands/<set_id>-<entry_id>`
  with approved entry_ids verbatim) gives
  `demo-veryhard-1-folic_acid.sdf`, and the battery's spec-coverage
  test computes the identical rule - the shipped file follows the law.
  Plan-text typo recorded here; no compound/source substitution of any
  kind.
- **Heme derived charge -4 recorded honestly:** the approved row's
  parenthetical "(propionate carboxyls protonated in the ideal
  geometry; charge field 0)" is contradicted by the file's actual
  M CHG annotations (sum -4; builder-derived AND SMOKE-02/PyMOL-agreed).
  Per the honesty law the derived truth ships (manifest
  `formal_charge_sum: -4`, `protonation: 'as-recorded'` - both accurate),
  the spec entry note was corrected to record the delta BEFORE commit,
  and the delta is recorded here. This is derivation evidence, not a
  content substitution: the fetched bytes are exactly the approved URL.
  The -4 (lobed porphyrin + deprotonated propionates charge model) is
  an input for 08-11's detector-coverage review.
- **Alternates: none to apply.** Approved Sets 7-9 declare no
  alternates for any row; nothing was substituted anywhere in this plan.

## Deviations from Plan

**One documented narrative-accuracy fix; zero code/data repairs;
zero substitutions.**

**1. [Rule 1 - incorrect claim] Heme charge narrative corrected**
- **Found during:** Task 3 (SMOKE-02 charge check).
- **Issue:** the approved proposal row's parenthetical said the HEM
  ideal SDF has "charge field 0 / propionate carboxyls protonated", but
  the fetched (and approval-time re-verified) file carries M CHG
  annotations summing to -4. The transcribed spec note would have
  shipped a false claim into the provenance that flows to
  DATA_SOURCES.md.
- **Fix:** spec entry note corrected to record the derived truth (-4)
  with the delta named literally; manifest ships the derived -4 (the
  honest truth of the approved file; builder and PyMOL agree exactly).
  Counts/atoms/flags/identity were verified against the approved row
  (75/82/43 heavy/Fe1/'HEM') - no mismatch, so no STOP per the plan's
  guardrail; nothing substituted.
- **Files modified:** `scripts/demo_specs/demo-veryhard-2.json`
  (entry-level provenance note only - outside the 14 manifest keys;
  no rebuild needed/possible).
- **Commit:** `c7b8784` (note included in the atomic set commit).

**2. [Plan-text typo, documented - no rule invoked] folic_acid file
name** - plan frontmatter sketched a hyphen where the 08-05 naming law
(and the battery) pin an underscore; shipped per the law
(`demo-veryhard-1-folic_acid.sdf`). Recorded here per the
transcription-record convention (cf. 08-05's stale-CID record).

## Issues Encountered

None beyond the recorded narrative delta (item 1 above). Every fetch
returned 200 single-record records matching the approval-time
re-verification counts exactly (32/48/51/35/75 atoms), SMOKE-02 passed
on first run after each set, and the RCSB `_ideal` fetch path worked
through the builder's standard urllib fetch with zero special-casing.

## User Setup Required

None - network fetches (PubChem PUG-REST + files.rcsb.org) used the
builder's sanctioned urllib path (User-Agent AA-match-build/1.0,
timeout 60 s).

## Next Phase Readiness

- **GEN-06 COMPLETE:** all ~9 curated tier slots ship pre-downloaded;
  18-ligand supply (12 small / 4 medium / 0 large curated distribution
  per the C2-corrected counts - ATP, NAD, folic acid, heme medium).
- **08-08 (phase smokes):** its pinned set census {'demo-dev-1', ...,
  'demo-veryhard-2'} and flag-branch coverage floor (>=1 metal, >=1
  halogen) are now satisfiable exactly as planned.
- **08-09 (DATA_SOURCES.md):** `--report-only` prints all 18 real rows
  today, incl. the halogen/metal flag columns and both U2-rcsb-verified
  paper DOIs; 3 honest-absence paper DOIs (9NDX, 1MBN + 1S0R) recorded.
- **08-10 (supply re-measurement):** the full 16-curated-ligand tally
  lands: `EXPECTED_SUPPLY = {'small': 12, 'medium': 4, 'large': 0}`
  matches today's distribution exactly.
- **08-11 (detector coverage + [HUMAN]):** chloramphenicol C-Cl,
  thyroxine C-I, and heme Fe scenes are now bundled for the headless
  coverage probe; the grouped dropdown gets its first 4-real-tier
  visual check; the heme -4 charge model is a recorded review input.

---
*Phase: 08-demo-curation-citations*
*Completed: 2026-09-26*
