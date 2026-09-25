---
phase: 08-demo-curation-citations
plan: 01
subsystem: data-pipeline
tags: [sdf, v2000-parser, manifest, sha256, demo-curation, scripts, python3.6]

# Dependency graph
requires:
  - phase: 02-headless-game-engine
    provides: script-built fixture contract (02-04), frozen 14-key manifest
      schema (02-03), pure persistence/manifest/generator single homes,
      SMOKE-02 shape (authoritative cross-check)
provides:
  - Durable committed bundling pipeline (scripts/build_demos.py) replacing
    the deleted tmp/build_fixtures.py throwaway
  - Committed dev-set spec + dry-run parser oracle
    (scripts/demo_specs/demo-dev-1.json) -- derived == committed on every key
  - Data-integrity battery (tests/test_demo_data.py), data-relative so
    08-05..08-07 curated sets are auto-covered
affects: [08-05, 08-06, 08-07, 08-09 DATA_SOURCES.md, every content plan
  that must fetch -> bundle -> commit through this pipeline before its
  atomic commit]

# Tech tracking
tech-stack:
  added: [top-level scripts/ tree (new repo dir), spec-driven SDF bundler,
    stdlib-only V2000 record parser]
  patterns: [spec-file-per-set under scripts/demo_specs/, counts derived
    from bytes not hand-entered, sha256 over target bytes in the same run,
    replace-or-insert ONLY one manifest set, dry-run parser oracle,
    report-only provenance rows for DATA_SOURCES.md]

key-files:
  created: [scripts/build_demos.py, scripts/demo_specs/demo-dev-1.json,
    tests/test_demo_data.py]
  modified: []

key-decisions:
  - "Route A adopted over 08-RESEARCH Q1's route-B recommendation: pure
    python3.6 V2000 parser derives counts in WSL; SMOKE-02 (real PyMOL
    loads, per-entry asserts) is the authoritative cross-check every
    content plan runs BEFORE its atomic commit, so a parser/PyMOL
    disagreement can never land in git. A disagreement is a Rule-1 fix:
    repair the parser, regenerate, re-run -- never hand-edit."
  - "Multi-record SDF sources refused at the builder (record count > 1
    names the entry): split or pick one state at curation time, never
    collapse -- states_expected==1 by construction."
  - "size_class always via generator._candidate_class (single bucket
    home); protonation defaults 'as-recorded'; file defaults
    ligands/<set_id>-<entry_id>.sdf with explicit override for the dev
    set's legacy names."
  - "Manifest entries stay EXACTLY the 14 REQUIRED_ENTRY_KEYS (battery
    test both-directions set equality); entry-level citation DEPTH
    (source_url/pdb_id/DOIs/PLIP/notes) lives in the SPECS, not
    MANIFEST.json -- 08-RESEARCH Q5 verdict: runtime validator untouched,
    truthfulness is the GATE + DATA_SOURCES.md's job."

patterns-established:
  - "The pipeline IS the only write path: every content plan (08-05..08-07)
    fetches/commits data ONLY through scripts/build_demos.py; the
    'NEVER hand-edit an SDF or MANIFEST.json' law (02-04) is now
    mechanically easy to obey."
  - "Spec-driven per-set JSON under scripts/demo_specs/<set_id>.json;
    --fetch for downloads, local_path for local sources, existing target
    otherwise; --dry-run never writes; --report-only never touches
    network or disk writes."

# Metrics
duration: 19 min
completed: 2026-09-25
---

# Phase 8 Plan 01: Bundling Pipeline Summary

**Committed, reproducible multi-set demo bundling pipeline: a py3.6-stdlib
V2000 spec-driven builder whose dry-run reproduces the committed
demo-dev-1 manifest set payload exactly, plus a data-relative 10-test
integrity battery (900/900 WSL green).**

## Performance

- **Duration:** 19 min
- **Started:** 2026-09-25T17:47:03Z
- **Completed:** 2026-09-25T18:05:56Z
- **Tasks:** 2/2
- **Files created:** 3 (725 LOC builder, 250 LOC battery, 34-line spec)

## Accomplishments

- `scripts/build_demos.py` (725 LOC): full contract CLI
  `--spec … [--fetch] [--dry-run] [--report-only]`; spec schema validated
  with refusals naming the bad field; byte resolution via
  urllib fetch (User-Agent `AA-match-build/1.0`, timeout 60 s),
  `local_path` copy, or existing committed file; ALL 14
  `manifest.REQUIRED_ENTRY_KEYS` derived from the resolved bytes (counts
  line cols 0-3/3-6, heavy = non-H elements stripped+uppercased,
  bond-order digit-string tally, M CHG formal-charge sum,
  states_expected == record count asserted == 1, DETECT-03 metal/halogen
  element scans, size via `generator._candidate_class`, sha256 over the
  target bytes in the SAME run); assembly = read committed manifest via
  `persistence.read_json_file` + `parse_manifest_dict`, replace-or-insert
  ONLY the target set, `make_container('manifest', …)`, RE-PARSE proof,
  `write_json_atomic`; `--report-only` cross-checks every spec against
  the manifest (exit 1 naming every gap) and prints the exact
  DATA_SOURCES.md provenance columns.
- **Dry-run proof (the must-have truth):**
  `python3.6 scripts/build_demos.py --spec scripts/demo_specs/demo-dev-1.json --dry-run`
  prints `derived == committed for set 'demo-dev-1' (every key, 2 entries)`,
  exit 0, MANIFEST.json mtime unchanged (stat-verified before/after).
  Benzamide 16/16/`{"1":12,"2":4}`/heavy 9/charge 0; acetate
  7/6/`{"1":5,"2":1}`/heavy 4/charge −1 -- the 02-04 constructed counts
  reproduced exactly by the route-A parser.
- Fail-closed refusal teeth exercised by probe: multi-record source
  refusal (names the entry, "never collapse"), counts-line parse failure
  (V3000 tag refused), `expect_atom_count` corruption guard, missing
  provenance key, off-vocabulary tier, url/local_path exclusivity.
- `tests/test_demo_data.py` (250 LOC, 10 tests): manifest parses; every
  entry file exists + sha256-matches; exactly the 14 keys both
  directions; `states_expected == 1`; bond-order totals == bond_count;
  `_candidate_class` reproduces size_class; forward-slash package-relative
  file; curated-set semantics (license/provenance/title non-empty, tier
  vocabulary pinned, spec provenance depth source_url/notes/pdb_id);
  spec-coverage (spec exists + set_id/entries/files match); builder py3.6
  syntax floor via in-memory `compile()`. Fully data-relative
  (loop-driven; the dev set is exempted exactly once by id).
- No network fetch happened during this plan (dry-run + local files only).

## Task Commits

Each task was committed atomically:

1. **Task 1: bundler + dev-set dry-run proof** - `2090da6` (feat)
2. **Task 2: data-integrity battery** - `1273af7` (test)

**Plan metadata:** (recorded below; docs commit)

## Files Created/Modified
- `scripts/build_demos.py` - the bundling pipeline (CLI + spec schema +
  V2000 parser + manifest assembly + dry-run/report-only)
- `scripts/demo_specs/demo-dev-1.json` - committed dev-set spec; dry-run
  oracle; durable regeneration path replacing tmp/build_fixtures.py
- `tests/test_demo_data.py` - data-integrity battery over the real
  bundled manifest

## Test/Smoke Results

- `python3.6 -m py_compile aamatch/*.py scripts/build_demos.py` — OK
- `python3.6 -m unittest discover -s tests -v` — **900/900 OK**
  (890 pre-existing incl. purity gates + 10 new TestDemoData)
- Dry-run: derived == committed on every key, exit 0, no data-write
- Report-only: exit 0, "all specs match the committed manifest
  (1 spec(s), 2 entrie(s))"
- `git status --short` post-plan: ONLY the three new files;
  aamatch/data/ untouched
- No smokes required by this plan (pure-pipeline plan; SMOKE-02 remains
  the per-content-plan authoritative cross-check)

## Decisions Made

- Route A (pure WSL V2000 parser) adopted over the mechanics-research
  Q1 route-B recommendation, per the plan's recorded decision; SMOKE-02
  is the binding cross-check at content-plan commit time.
- The dev set's legacy file names (`ligands/benzamide.sdf`,
  `ligands/acetate.sdf`) preserved via explicit spec `file` overrides;
  committed dev SDFs never renamed or rewritten.
- Provenance/citation depth lives in specs (and flows to DATA_SOURCES.md
  via --report-only); manifest entries keep exactly the 14 frozen keys.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None. (Authoring-time note: an intermediate draft of the builder was
self-reviewed and rewritten once before first compile; the committed
file is the reviewed form. No production code was touched.)

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- 08-05..08-07 can fetch/bundle/commit strictly through this pipeline
  (spec file per set -> `--fetch` -> SMOKE-02 -> commit).
- 08-09 has --report-only as the mechanical producer of DATA_SOURCES.md
  provenance rows (columns: entry_id, file, molecule, source URL, ID,
  PDB complex + DOIs, PLIP ref, protonation, halogen, metal, sha256,
  fetched).
- The battery automatically goes red if any curated set lands with empty
  license/provenance/title, an off-vocabulary tier, shallow spec
  provenance, multi-record data, or a sha256/count drift.

---
*Phase: 08-demo-curation-citations*
*Completed: 2026-09-25*
