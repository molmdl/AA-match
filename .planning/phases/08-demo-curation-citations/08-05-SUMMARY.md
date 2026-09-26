---
phase: 08-demo-curation-citations
plan: 05
subsystem: demo-data
tags: [demo-curation, sdf, pubchem, manifest, smoke-02, data-battery, python3.6]

# Dependency graph
requires:
  - phase: 08-demo-curation-citations
    provides: 08-01 bundling pipeline (scripts/build_demos.py + data
      battery), 08-04 [GATE] APPROVED 2026-09-26 proposal rows
      (08-PROPOSALS.md incl. corrections C1-C7 and the 16/16 atom-count
      re-verification)
provides:
  - Three curated easy-tier demo sets (demo-easy-1/2/3, 5 ligands)
    bundled via the 08-01 pipeline: pre-downloaded single-record 3D SDFs
    with in-run derived counts + sha256
  - specs scripts/demo_specs/demo-easy-{1,2,3}.json carrying the
    approved per-entry provenance (CID fetch URL, PDB complex + DOIs,
    PLIP ref, protonation why, notes) - the DATA_SOURCES.md source rows
  - MANIFEST.json grown to 4 sets / 7 entries; demo-dev-1 payload
    byte-identical; GEN-06 Easy x3 slots filled
affects: [08-06 hard tier, 08-07 challenge/very-challenging tiers,
  08-09 DATA_SOURCES.md (--report-only now prints 7 real rows),
  08-10 supply re-measurement, 08-11 detector-coverage review]

# Tech tracking
tech-stack:
  added: [curated PubChem 3D SDF content, spec-carried citation depth]
  patterns: [propose -> approve -> fetch/commit protocol executed
    end-to-end on the simplest tier; one atomic commit per set, each
    gated by SMOKE-02 real-load BEFORE commit; approved-correction
    transcription (C1 CID 243) outranks stale plan text]

key-files:
  created: [scripts/demo_specs/demo-easy-1.json,
    scripts/demo_specs/demo-easy-2.json,
    scripts/demo_specs/demo-easy-3.json,
    aamatch/data/ligands/demo-easy-1-aspirin.sdf,
    aamatch/data/ligands/demo-easy-1-benzoic_acid.sdf,
    aamatch/data/ligands/demo-easy-2-citric_acid.sdf,
    aamatch/data/ligands/demo-easy-2-acetate.sdf,
    aamatch/data/ligands/demo-easy-3-caffeine.sdf]
  modified: [aamatch/data/MANIFEST.json]

key-decisions:
  - "Benzoic acid bundled as CID 243 per APPROVED correction C1
    (human verdict '1 ok'; the plan body's stale 'CID 3979' text is
    superseded - 3979 is a different compound). Transcription source is
    the APPROVED proposal row, never the stale plan sketch."
  - "Entry ids transcribed verbatim from the approved rows (aspirin,
    benzoic_acid, citric_acid, acetate, caffeine); file names derive
    single-rule as ligands/<set_id>-<entry_id>.sdf per Decision 6 with
    NO 'file' overrides in the curated specs."
  - "Citric acid bundled as the neutral free acid CID 311 per approved
    Decision 5 (COOH-never-anion guard; deprotonated-citrate sourcing
    REJECTED for v1); the set's salt-bridge slot is acetate CID 175,
    whose M CHG derived formal_charge_sum -1 exactly."
  - "Citric acid paper_doi recorded as '' (NONE recorded in the RCSB
    data - honest absence, never invented) per the approved row."

patterns-established:
  - "Content-plan execution loop proven: spec -> --fetch -> SMOKE-02 ->
    data battery -> atomic commit, three times with zero failures;
    --report-only exit 0 over 4 specs / 7 entries at plan end."
  - "Set-level spec provenance shape: source_url (REST template),
    license_url, pubchem_citation (U1 canonical wording), complex_license
    (CC0 1.0 wwPDB), fetched (date), notes (rationale + approvals)."

# Metrics
duration: ~20 min
completed: 2026-09-26
---

# Phase 8 Plan 05: Easy-Sets Bundling Summary

**First curated content through the approved GATE: the three Easy demo
sets (aspirin + benzoic acid, citric acid + acetate, caffeine) fetched,
manifest-derived, SMOKE-02-proven and committed atomically via the 08-01
pipeline - 4 sets / 7 entries total, 906/906 WSL green, zero deviations
requiring fixes.**

## Performance

- **Duration:** ~20 min
- **Started:** 2026-09-26T14:16:07Z
- **Completed:** 2026-09-26T14:36Z
- **Tasks:** 3/3
- **Files created:** 8 (3 specs + 5 SDFs); modified: 1 (MANIFEST.json)

## Accomplishments

- **demo-easy-1 "Everyday organics"** (commit d0cef87): aspirin CID 2244
  (21 atoms/21 bonds/heavy 13/charge 0) + benzoic_acid CID 243 (15/15/
  heavy 9/charge 0). Provenance: 1OXR (paper DOI human-verified via PDB
  website) and 5E4D (paper DOI resolves 200). Single-record fetches;
  expect_atom_count guards 21/15 passed.
- **demo-easy-2 "Metabolites & ions"** (commit 9b64323): citric_acid CID
  311 (21/20/heavy 13/charge 0 - neutral free acid per Decision 5;
  paper DOI honestly absent) + acetate CID 175 (7/6/heavy 4/**charge -1**
  - M CHG derived exactly; the set's salt-bridge carrier). 8FUY (C5
  re-pin) and 5YS8 provenance. Legacy dev `ligands/acetate.sdf` untouched.
- **demo-easy-3 "Caffeine"** (commit 0875c74): caffeine CID 2519 (24/25/
  heavy 14/charge 0) - the acceptor-only h_bond teaching case; 3G6M
  provenance (paper DOI human-verified via PDB website).
- MANIFEST.json: 4 sets (dev + 3 easy) / 7 entries; container shape
  frozen (kind 'manifest', version 1, magic AAMATCH, manifest_version 1);
  entries remain exactly the 14 REQUIRED_ENTRY_KEYS (battery test 03).
- Disk sha256 == manifest sha256 on all 5 new SDFs (report-only +
  SMOKE-02 + independent `sha256sum` all agree).

## Task Commits

Each set was committed atomically (SDFs + MANIFEST.json + spec in one
commit), SMOKE-02 run BEFORE each commit:

1. **Task 1: bundle demo-easy-1 (aspirin + benzoic acid)** - `d0cef87` (feat)
2. **Task 2: bundle demo-easy-2 (citric acid + acetate)** - `9b64323` (feat)
3. **Task 3: bundle demo-easy-3 (caffeine) + full-suite regression** -
   `0875c74` (feat)

**Plan metadata:** (recorded below; docs commit)

## Files Created/Modified

- `scripts/demo_specs/demo-easy-{1,2,3}.json` - approved curation inputs:
  set-level license/provenance (fetched 2026-09-26, U1 canonical PubChem
  citation, CC0 wwPDB complex metadata) + per-entry provenance
  (source_url, pdb_id, entry_doi, paper_doi, plip, notes) transcribed
  from APPROVED 08-PROPOSALS.md rows only
- `aamatch/data/ligands/demo-easy-1-aspirin.sdf`,
  `demo-easy-1-benzoic_acid.sdf`, `demo-easy-2-citric_acid.sdf`,
  `demo-easy-2-acetate.sdf`, `demo-easy-3-caffeine.sdf` - single-record
  PubChem 3D SDFs fetched through `scripts/build_demos.py --fetch` only
- `aamatch/data/MANIFEST.json` - regenerated by the builder three times
  (replace-or-insert one set per run; demo-dev-1 payload byte-identical,
  proven by --dry-run exit 0 after plan end)

## Test/Smoke Results

- `python3.6 -m py_compile aamatch/*.py scripts/build_demos.py` - OK
- `python3.6 -m unittest discover -s tests -v` - **906/906 OK**
  (full suite incl. purity gates + the 10-test data battery, which now
  covers the 3 curated sets: license/provenance/title non-empty, tier
  vocabulary, spec provenance depth, spec coverage)
- `bash smoke/run_smoke.sh smoke/smoke_02_manifest.py 180` - **===
  SMOKE-02 PASS ===** after ALL THREE sets (every entry of all 4 sets
  load-verified in real PyMOL: sha256/atoms/bond-multiset/charge/states/
  element-scan flags; no tmp leak)
- `python3.6 scripts/build_demos.py --report-only` - exit 0, "all specs
  match the committed manifest (4 spec(s), 7 entrie(s))"; the DATA_SOURCES.md
  provenance rows print for all curated entries
- `--dry-run` on demo-dev-1 - exit 0, derived == committed on every key
  (multi-set assembly never disturbs other sets)
- acetate manifest check: `formal_charge_sum` list for demo-easy-2 =
  `[0, -1]` (includes -1 as the plan's gate requires)

## Decisions Made

- Benzoic acid transcribed as **CID 243** (APPROVED correction C1), not
  the plan body's stale 3979 - the approval-time 16/16 re-verification
  row (15 atoms, 1 record, heavy 9) is the binding evidence; the
  expect_atom_count 15 guard passed on the live fetch.
- No `file` overrides in curated specs: file names derive from the
  single Decision-6 rule `ligands/<set_id>-<entry_id>.sdf` (realized as
  e.g. `demo-easy-1-benzoic_acid.sdf`); the plan frontmatter's
  hyphenated spellings were plan-text cosmetics.
- Citric `paper_doi: ""` is a recorded honest absence (RCS record
  carries no primary citation), never an invented value; the entry's
  notes carry the 8FUY re-pin history (C5).

## Deviations from Plan

**No Rule 1-3 fixes required - zero code/data repairs.** Two
plan-text-vs-approved-source notes (neither is a substitution):

1. **Approved-correction note (transcription fidelity, not a
   deviation):** the plan body says "benzoic-acid (CID 3979)", but the
   binding source (08-PROPOSALS.md correction C1, human-accepted "1 ok",
   re-verified 16/16 MATCH) pins **CID 243**. Executed as CID 243. Using
   the stale 3979 would have fetched the WRONG compound
   (N-(3-benzylpurin-6-yl)acetamide) and violated the gate.
2. **Plan-frontmatter cosmetic note:** the frontmatter's `files_modified`
   lists hyphenated file names (`demo-easy-1-benzoic-acid.sdf` etc.);
   the realized names keep the approved entry_ids verbatim per the
   Decision-6 single naming rule (`demo-easy-1-benzoic_acid.sdf` etc.).
   The battery's spec-coverage test computes the same rule, so specs and
   manifest agree exactly.

## Issues Encountered

None - every fetch returned 200 single-record records matching the
approval-time re-verification counts exactly (21/15/21/7/24), SMOKE-02
passed on first run after each set, and no substitution/ALTERNATE path
was needed.

## User Setup Required

None - network fetches used the builder's sanctioned urllib path
(User-Agent AA-match-build/1.0, timeout 60 s).

## Next Phase Readiness

- GEN-06 Easy x3 slots FILLED; 08-06 (hard x3 sets) and 08-07 (challenge
  + very_challenging) repeat this exact loop with their approved rows
  (hemme's RCSB `_ideal` fetch and the halogen/metal flag flips live
  there).
- 08-09 can run `--report-only` today to produce 5 real provenance rows
  (+2 dev rows) for DATA_SOURCES.md.
- 08-10 supply re-measurement: 7 ligands bundled today (dev 2 + curated
  easy 5); the approved bundle's 18 total (dev 2 + curated 16) lands
  once 08-06/08-07 complete.
- 08-11's detector-coverage check now has the easy tier's real ligands
  staged (metal/halogen carriers arrive with 08-06/08-07).

---
*Phase: 08-demo-curation-citations*
*Completed: 2026-09-26*
