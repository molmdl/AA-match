---
phase: 08-demo-curation-citations
plan: 08
subsystem: testing
tags: [smoke-suite, smoke-02, smoke-21, curated-coverage, cleanup,
  pitfall-13, messy-scene, aspirin, to-windows-path, headless, python3.6]

# Dependency graph
requires:
  - phase: 08-demo-curation-citations
    provides: 08-07's FULL curated manifest (10 sets / 18 entries incl.
      the halogen/metal flag debuts), the dev-set anchor from 02-04,
      08-PROPOSALS D8 (messy scene = local script-built fixture; 1OXR
      aspirin+Ca2+ the approved real-world analog), smoke skeleton
      laws (01-07 anchor, 02-04 SMOKE-NN discipline), placement
      cleanup contract from 02-13, pre-registered snapshot pattern
      from 03-05
provides:
  - SMOKE-02 as the complete criterion-4 clause-1 machine: every
    manifest id load-verified PLUS the curated-coverage census
    (canonical 10 set_ids; every set >= 1 entry; tier census exactly
    {easy: 4, hard: 3, challenge: 1, very_challenging: 2} counting the
    dev set in easy; >= 1 metal_present and >= 1 halogen_present row
    so both element-scan branches exercise every run; every non-dev
    set license non-empty mirroring tests/test_demo_data.py)
  - smoke_21_demo_cleanup.py: ROADMAP criterion-4 clause-2 field test
    - a curated-set game on a messy user scene (protein fragment +
    3 waters + 1 Na+ ion, local script-built fixture) followed by
    placement.cleanup_game_objects() restores the EXACT original
    object set (names AND per-object atom counts); zero '_aam_'
    leakage; zero 'AAM' segi outside game objects (PITFALL 13 proven
    in the field)
  - The ratified deviation record: inline-PDB tmp-file cmd.load via
    to_windows_path replaces the research's UNVERIFIED read_pdbstr
    sketch (cmd.load = probe-proven universal path)
affects: [08-09 DATA_SOURCES.md (coverage asserts now bind the final
  10-set census; DATA_SOURCES must not shrink the bundle without
  updating them), 08-11 headless detector-coverage probe (smoke_21's
  fixture pattern is reusable), any future tier/set restructure
  (EXPECTED_SET_IDS + EXPECTED_TIER_CENSUS in SMOKE-02 are the pin)]

# Tech tracking
tech-stack:
  added: []
  patterns: [coverage census computed from the parsed payload with only
    stable curation contracts as literals (data-relative discipline),
    messy-scene fixture = script-built fixed-column PDB inline ->
    git-ignored tmp/ file -> to_windows_path cmd.load,
    pre-registered snapshot + per-object atom-count equality as the
    cleanup-isolation proof (PITFALL 13's own suggested check)]

key-files:
  created: [smoke/smoke_21_demo_cleanup.py]
  modified: [smoke/smoke_02_manifest.py]

key-decisions:
  - "SMOKE-02 coverage literals are the curation contracts ONLY
    (EXPECTED_SET_IDS 10 ids incl. demo-dev-1; EXPECTED_TIER_CENSUS
    counting dev in easy); every other number is computed from the
    parsed payload/entries - same discipline as tests/test_demo_data.py
    so a manifest edit failing truth surfaces identically in both tiers."
  - "smoke_21's messy fixture is local script-built atoms (no new
    fetch of complex data), written to git-ignored tmp/messy_scene.pdb
    and loaded via to_windows_path+cmd.load - the ratified replacement
    for the research's UNVERIFIED cmd.read_pdbstr sketch; 1OXR stays
    the cited approved real-world analog (08-PROPOSALS D8)."
  - "Candidate selection in smoke_21 is data-relative: demo-easy-1's
    first row from enumerate_entries' sorted order (the aspirin row,
    the 1OXR analog), molecules_per_level=1 per the 04-04
    single-candidate law, fixed seed 20260808."

patterns-established:
  - "Flag-branch coverage assert: cross-check loops must exercise BOTH
    sides of every boolean branch; the census asserts >= 1 present row
    per flag, computed from the entries, with row ids printed."
  - "Cleanup field proof = deleted-count match + name-set equality +
    per-object count map equality + zero leftover prefix objects + zero
    leftover sentinel segi atoms - all computed into variables BEFORE
    any check-detail string (03-04 authoring law)."

# Metrics
duration: ~6 min (execution 15:05Z-15:12Z)
completed: 2026-09-26
---

# Phase 8 Plan 08: Smoke Coverage + Cleanup Field Test Summary

**ROADMAP Phase-8 criterion 4 is now fully machine-proven headless:
SMOKE-02 became the complete curated-coverage machine (canonical
10-set census, exact tier census, metal/halogen flag-branch coverage,
non-dev license echo on top of the every-id load verification - 153
PASS lines, zero failures) and the NEW smoke_21 proves PITFALL 13 in
the field: a curated game on a messy protein+water+ion scene cleans
up to the EXACT pre-game object set (names and per-object atom
counts) with zero game-object leakage; smoke_04, 02, 21 all PASS and
906/906 WSL tests stay green - zero code fixes needed.**

## Performance

- **Duration:** ~6 min
- **Started:** 2026-09-26T15:05Z
- **Completed:** 2026-09-26T15:12Z
- **Tasks:** 3/3
- **Files created:** 1 (smoke/smoke_21_demo_cleanup.py); modified: 1
  (smoke/smoke_02_manifest.py)

## Accomplishments

- **SMOKE-02 curated-coverage extension** (commit `3d2549b`): six new
  coverage checks appended after the manifest parse, all computed from
  the parsed payload/entries - `coverage set census` (canonical 10
  set_ids present), `coverage every set non-empty`, `coverage tier
  census` ({easy: 4, hard: 3, challenge: 1, very_challenging: 2},
  dev set counting in easy), `coverage metal branch`
  (1 row: demo-veryhard-2/heme), `coverage halogen branch` (2 rows:
  demo-challenge-1/chloramphenicol, demo-veryhard-1/thyroxine),
  `coverage curated license` (every non-dev set licensed). The
  per-entry load loop is unchanged - the generic loop stays the
  criterion-4 clause-1 machine (research Q6).
- **smoke_21 messy-scene cleanup field test** (commit `c26bbaf`):
  PART A script-builds a 28-atom messy scene (5-residue ALA/GLY/LYS/
  PHE/SER fragment + 3 HOH + 1 Na+ ion) inline as fixed-column PDB to
  git-ignored `tmp/messy_scene.pdb` and cmd.loads it via
  `to_windows_path` as `user_complex`; the pre-registered snapshot
  (names + per-object count map) asserts the scene is non-game.
  PART B starts a curated game on demo-easy-1's data-relative first
  row (aspirin, the 1OXR analog) via engine.new_game(seed, candidates,
  molecules 1/levels 1/unset) and placement.materialize: 10 new
  objects (1 lig + 9 AAs) ALL '_aam_'-prefixed, 178 sentinel segi
  'AAM' atoms. PART C `placement.cleanup_game_objects()`: deleted 10
  of 10, post names EXACTLY equal the snapshot, per-object atom counts
  byte-equal, zero '_aam_' leftovers, zero 'AAM' segi atoms anywhere.
  Sole verdict marker `=== SMOKE-21 PASS ===` printed first run.
- **Regression pass** (no code change): SMOKE-02 PASS (153 PASS
  lines), SMOKE-21 PASS (15/15), SMOKE-04 PASS (26/26 - the
  pre-existing cleanup-assert precedent unaffected), full WSL suite
  906/906 green incl. the purity gates and the 02-11 perf guard
  (worst-case detect 0.378 s vs the 2.0 s loose guard);
  `git check-ignore tmp/messy_scene.pdb` confirms the fixture is
  git-ignored and `git status` is clean of it.

## Task Commits

| Task | Commit | Type | files |
| ---- | ------ | ---- | ----- |
| 1. SMOKE-02 curated-coverage extension | `3d2549b` | feat | smoke/smoke_02_manifest.py |
| 2. smoke_21 messy-scene cleanup field test | `c26bbaf` | feat | smoke/smoke_21_demo_cleanup.py |
| 3. Regression pass (verify-only) | - | - | no code change |

## Verification Results

- `bash smoke/run_smoke.sh smoke/smoke_02_manifest.py 180` ->
  `=== SMOKE-02 PASS ===` incl. all 6 new coverage checks PASS.
- `bash smoke/run_smoke.sh smoke/smoke_21_demo_cleanup.py 180` ->
  `=== SMOKE-21 PASS ===` (15/15 checks; messy 28 atoms; deleted 10/10;
  restoration exact).
- `bash smoke/run_smoke.sh smoke/smoke_04_e2e.py 240` ->
  `=== SMOKE-04 PASS ===` (26/26; no cross-effect).
- `python3.6 -m unittest discover -s tests` -> Ran 906 tests, OK.
- `python3.6 -m py_compile aamatch/*.py scripts/build_demos.py
  smoke/smoke_02_manifest.py smoke/smoke_21_demo_cleanup.py` -> clean.
- `tmp/messy_scene.pdb` git-ignored, NOT committed.

## Deviations from Plan

### Ratified design deviations (pre-authorized by the plan, recorded)

1. **[research-sketch replacement, plan-ratified]** smoke_21 loads the
   messy scene via inline-PDB -> tmp file -> `to_windows_path` +
   `cmd.load` instead of the research memo's `cmd.read_pdbstr` sketch -
   cmd.load is the repo's probe-proven universal path and read_pdbstr
   is an UNVERIFIED surface in this build. Documented in the smoke_21
   header exactly as the plan context prescribes.

### Auto-fixed issues

None - both smokes passed on the first authored run; no Rule 1-3 fixes
were needed in any aamatch code; zero changes outside the two
files_modified declared in the plan frontmatter.

## Authentication Gates

None.

## Lessons Learned

- The coverage-census discipline pays off immediately: computing
  everything from the parsed payload meant the SAME SMOKE-02 source
  verified a 2-set dev manifest (02-04) and the final 10-set curated
  bundle (08-08) with only the contract literals changing.
- smoke_21 first-run green validates the 02-13 prefix-only cleanup
  convention against the exact PITFALL 13 hazard class (waters + ion)
  with no accommodation: names and per-object counts restored exactly.

## Next Phase Readiness

- 08-09 (DATA_SOURCES.md) documents the same 10-set bundle SMOKE-02
  now pins; keep the license/provenance prose consistent with the
  battery + census asserts.
- 08-10 (supply re-measurement) and 08-11 (detector-coverage probe +
  [HUMAN] terminal check) inherit smokes 02 and 21 as green gates.
- Parallel-wave note: 08-08 ran in worktree exec/08-08 alongside the
  08-09/08-10 siblings; disjoint files_modified, orchestrator blends
  STATE.md on merge.
