---
phase: 04-qt-setup-window
plan: 06
subsystem: pure-layer
tags: [upload, sdf, mol2, splitting, manifest-schema, sha256, tdd, python36]

# Dependency graph
requires:
  - phase: 04-qt-setup-window (04-03)
    provides: game_file PURE module (GAME_VERSION gate, UPLOAD_SET_ID, base64 codec)
  - phase: 02-headless-game-engine (02-03, 02-05, 02-08)
    provides: manifest 14-key schema + _check_entry family, capability._bond_order_int,
      generator._candidate_class (single homes reused)
provides:
  - UPLOAD_MAX_RECORDS = 50 (Decision 8; refusal carries the per-generate temp-load rationale)
  - split_sdf_records / split_mol2_segments (CRLF-byte-stable record splitters)
  - check_upload_supply (zero/empty-index/over-cap refusals naming file + record index)
  - read_upload_source (text, FILE sha256, format) with pinned PDB/decode refusals
  - build_uploaded_row (manifest-shaped upload rows, synthetic uploads/mol-00N keys)
  - validate_uploaded_rows (fail-closed guards + delegation to manifest._check_entry)
affects: [04-08 upload pipeline, 04-10 upload handler]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Synthetic-key upload identity: uploads/mol-00N.<fmt> keys (never real paths) make the os.path.join absolute-path hazard structurally impossible"
    - "Two-sha256 rule: FILE hash (read_upload_source) vs RECORD-TEXT hash (rows / ligand_files) — Decision 19, never conflated"
    - "Single-home delegation: validate_uploaded_rows calls manifest._check_entry; row size_class calls generator._candidate_class; bond_order_counts tallies capability._bond_order_int — no rule re-implementation"

key-files:
  created: []
  modified:
    - aamatch/game_file.py (upload-side pure surface appended; new imports stdlib os + pure siblings)
    - tests/test_game_file.py (31 RED tests + 3 adapter-pin tests)

key-decisions:
  - "build_uploaded_row carries 'set_id' == UPLOAD_SET_ID in the row itself (16 keys: 14 manifest + 'set_id' + 'title') — its rows feed engine.new_game directly as candidates and the generator requires non-empty set_id (generator.py candidate guard); the plan's '14 keys + title' wording is read as the manifest-key core plus the candidate-row set_id"
  - "CRLF detection of SDF terminators uses line.rstrip('\\r\\n') == '$$$$' after splitlines(True) — byte-stable rejoin, no '\\r' loss"
  - "Unrecognizable bond orders yield a 'None' tally key, refused by the manifest digit-string rule at validate time (fail-closed, never guessed)"
  - "read_upload_source uses bare stdlib open (rb) — the same pure I/O persistence performs; documented in the module docstring"

patterns-established:
  - "Adapter pin test pattern: broken-row test asserts the DELEGATED module's own message text (proves delegation, not re-implementation)"
  - "Refusal messages name file + record index + rationale verbatim and are pinned by exact-message equality"

# Metrics
duration: 15min
completed: 2026-09-16
---

# Phase 4 Plan 06: game_file upload helpers Summary

**Complete upload-side PURE surface in aamatch/game_file.py: CRLF-safe SDF/MOL2 splitters, a 50-record supply cap with the per-generate rationale in the refusal, file reads returning (text, FILE sha256, format), manifest-shaped uploaded rows with synthetic uploads/mol-00N keys and record-text hashes, and validation that delegates to manifest.\_check_entry — zero whitelist changes, 688 WSL tests green.**

## Performance

- **Duration:** ~15 min
- **Started:** 2026-09-15T20:02:49Z
- **Completed:** 2026-09-15T20:17:28Z
- **Tasks:** 3
- **Files modified:** 2

## Accomplishments

- extension of the 04-03 PURE module with the six upload helpers + UPLOAD_MAX_RECORDS (WSL-only, probe-independent, exactly the 04-08/04-10 assembly surface)
- TDD RED → GREEN → adapter-pin: 34 new tests (6 RED classes + adapter-pin class) over hand-built minimal SDF/MOL2 fixture strings, incl. CRLF byte-stability and cap-rationale pins
- purity re-audit over the EXTENDED module: `python3.6 -m unittest tests.test_purity` green with ZERO whitelist changes (os already whitelisted; manifest/generator/capability already PURE)
- full WSL suite: 654 baseline → 688 green; `py_compile aamatch/game_file.py` green

## Task Commits

Each task was committed atomically (TDD discipline):

1. **Task 1: RED — failing tests** - `226bdad` (test)
2. **Task 2: GREEN — implement the six upload helpers** - `99e34bb` (feat)
3. **Task 3: purity re-check + adapter pin** - `061695c` (test)

## Files Created/Modified

- `aamatch/game_file.py` - appended the upload-side pure surface (split_sdf_records, split_mol2_segments, check_upload_supply, read_upload_source, build_uploaded_row, validate_uploaded_rows, UPLOAD_MAX_RECORDS); imports += os + `from . import manifest`, `from .generator import _candidate_class`, `from .capability import _bond_order_int`; module docstring scope extended (layer statement now covers read_upload_source's stdlib-open I/O)
- `tests/test_game_file.py` - 6 RED test classes (TestSplitSdfRecords, TestSplitMol2Segments, TestCheckUploadSupply, TestReadUploadSource with tempfile setUp/tearDown, TestBuildUploadedRowShape, TestValidateUploadedRows) + TestValidateDelegationAdapter pin class

## Decisions Made

1. **set_id in the row.** build_uploaded_row emits 16 keys (14 REQUIRED_ENTRY_KEYS + 'set_id' + 'title'). The plan's test-5 wording ("exactly the 14 manifest keys + 'title'") conflicts with two pinned behaviors: validate_uploaded_rows' fail-closed set_id guard ("missing set_id refuses") and 04-08's direct `candidates=rows` feed into engine.new_game (the generator requires non-empty set_id strings). Reading "manifest-shaped candidate row" as the enumerate_entries shape (which carries set_id) satisfies all three; recorded here as the authoritative interpretation.
2. **CRLF terminator detection:** `line.rstrip('\r\n') == '$$$$'` after splitlines(True) — preserves original bytes on rejoin (no '\r' loss, pinned by test).
3. **Unrecognized bond order:** `_bond_order_int` returning None yields tally key 'None', then refused by the manifest's digit-string rule inside validate_uploaded_rows — fail-closed, one refusal home.
4. **read_upload_source I/O:** bare `open(path, 'rb')` (the same I/O persistence.read_json_file performs); the module docstring's layer statement was extended to say so — purity law is "no viewer/Qt", not "no stdlib open".

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing Critical] build_uploaded_row includes 'set_id' in the row**
- **Found during:** Task 1 (RED) — test-5/test-6 contradiction analysis
- **Issue:** Plan test-5 pins "exactly the 14 manifest keys + 'title'" but test-6 requires "a build_uploaded_row output passes" validate_uploaded_rows AND "missing set_id refuses"; 04-08 feeds rows straight into engine.new_game, whose candidate guard refuses rows without non-empty set_id
- **Fix:** row carries `'set_id': UPLOAD_SET_ID` (16 keys total); test key-set assertion written as REQUIRED_ENTRY_KEYS + ['set_id', 'title']
- **Files modified:** tests/test_game_file.py, aamatch/game_file.py
- **Verification:** test_built_rows_pass + test_missing_set_id_refused + generator-candidate contract all green
- **Committed in:** 226bdad, 99e34bb

---

**Total deviations:** 1 auto-fixed (1 missing critical — plan-reading resolution)
**Impact on plan:** Single interpretation fix; no scope creep, no contract weakening. Every pinned refusal message is verbatim from the plan.

## Issues Encountered

None — plan executed straight through; RED failed exactly on missing attributes, GREEN passed on first full run, purity re-check needed no whitelist edits.

## Authentication Gates

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- **04-08 (upload pipeline):** has everything it consumes — read_upload_source, split helpers, check_upload_supply, build_uploaded_row(record_text=..., fmt=..., index=...), validate_uploaded_rows; SMOKE-12 PART 2 flow (`records = split_sdf_records(text)` → per-record extraction → rows/content → validate) runs on exactly this surface. PART 3's timing print is the recorded-evidence hook for the cap value.
- **04-10 (upload handler):** pure glue over the same helpers + the setup_form upload fields.
- **Forward concern (unchanged owner):** `cmd.read_mol2str` is missing from this build's cmd namespace (04-04 finding) — 04-08's SMOKE-12 PART 4 probe is the canary for the MOL2 multi-segment fallback (Decision 14).

---
*Phase: 04-qt-setup-window*
*Completed: 2026-09-16*
