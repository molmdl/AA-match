---
phase: 01-bootstrap-pure-foundation
plan: 02
subsystem: persistence
tags: [json, atomic-io, versioned-container, formaterror, python36, stdlib-only, tdd]

# Dependency graph
requires: []
provides:
  - "Versioned-container core in aamatch/persistence.py: AAM_MAGIC, FORMAT_VERSION, KINDS, FormatError, make_container, check_container"
  - "Atomic JSON file I/O: write_json_atomic (temp+fsync+os.replace), read_json_file (binary + clear parse-failure message)"
  - "Container file wrappers: save_container / load_container (header transparent to callers)"
  - "19-test RED-first suite in tests/test_persistence.py (refusals message-asserted, older-version acceptance, atomicity proofs)"
affects: [01-05-setup-file, 01-06-level-spec, phase-4-game-container, phase-7-checkpoint-sidecar, purity-gates]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Versioned container {magic, version, kind, data} — one format discipline for every AA-match file kind"
    - "Refuse-newer / accept-older format-version policy (additive-only evolution, .get() default readers)"
    - "Atomic writes: temp file + fsync + os.replace, binary mode, sort_keys, allow_nan=False, best-effort tmp cleanup"
    - "Message-asserted FormatError refusals (foreign / unsupported / misfiled / unparseable)"

key-files:
  created:
    - aamatch/persistence.py
    - tests/test_persistence.py
  modified: []

key-decisions:
  - "Atomic write uses os.fdopen(fd,'wb') context manager around write+fsync instead of manual os.fsync(fd)+os.close(fd): identical semantics, but the fd is closed on the write/fsync failure path too (prevents fd leak before tmp cleanup)"
  - "Cleanup guarded with except BaseException + inner try/except OSError so any failure (including KeyboardInterrupt) removes the .aam_*.tmp file and re-raises"
  - "No header checksum by design (R2): hand-editable educator files are a feature; corruption surfaces via the 'could not parse AA-match JSON' FormatError"

patterns-established:
  - "Container refusal phrasing: 'not an AA-match file' / 'unsupported AA-match format version ... Please update AA-match.' / 'expected an AA-match <kind> file' — downstream modules must not invent new phrasing"
  - "Round-trip tests assert exact == equality (never assertAlmostEqual)"

# Metrics
duration: 11 min
completed: 2026-09-05
---

# Phase 1 Plan 2: Versioned Container Core + Atomic JSON I/O Summary

**Versioned-container core (magic/version/kind + three message-asserted refusal classes) and atomic JSON I/O (temp+fsync+os.replace, NaN-refusing, byte-stable) in a pure stdlib-only `aamatch/persistence.py`, built RED-first with 19 passing tests.**

## Performance

- **Duration:** 11 min
- **Started:** 2026-09-05T09:06:38Z
- **Completed:** 2026-09-05T09:17:45Z
- **Tasks:** 1 TDD feature (RED → GREEN → REFACTOR)
- **Files modified:** 2 created

## Accomplishments
- `aamatch/persistence.py` (137 lines, pure): container construction/validation with all three refusal classes — foreign magic, unsupported newer version ("Please update AA-match"), misfiled kind — plus corrupt-version and unparseable-JSON refusals; older versions accepted (refuse-newer/accept-older, additive-only evolution documented in docstring)
- `write_json_atomic`: temp file (`mkstemp`, `.aam_*.tmp`) → write → fsync → `os.replace`, binary mode, `sort_keys=True`, `allow_nan=False`; best-effort tmp removal and original-file integrity on any failure
- `tests/test_persistence.py` (212 lines, 19 tests): every refusal message asserted, exact-equality round-trips with unicode + boundary ints, no-tmp-litter proof, mocked-`os.replace` failure simulation, NaN refusal, byte-stability across key insertion orders

## Task Commits

Each TDD cycle was committed atomically:

1. **RED: failing tests for versioned container + atomic JSON I/O** - `4cc3364` (test)
2. **GREEN: implement versioned container core + atomic JSON I/O** - `0ff1c0d` (feat)
3. **REFACTOR: clean up persistence container** - skipped (no changes needed; implementation matched the R2/R3 sketch exactly)

## Files Created/Modified
- `aamatch/persistence.py` - versioned container core (AAM_MAGIC/FORMAT_VERSION/KINDS/FormatError, make_container/check_container) + atomic JSON I/O (write_json_atomic/read_json_file) + save_container/load_container
- `tests/test_persistence.py` - 19-test RED-first suite covering container contract, refusal classes, older-version acceptance, and all five atomic-write behaviors

## Decisions Made
- Used `os.fdopen(fd, 'wb')` context manager instead of the sketch's manual `os.fsync(fd)` + `os.close(fd)`: same bytes-on-disk semantics, but guarantees fd closure on the write/fsync exception path before tmp cleanup (behavior verified by the failure-simulation test)
- Guarded write cleanup with `except BaseException` (re-raise preserved) so tmp litter is removed on any failure class, per the plan's "on ANY exception" wording
- Accepted-older policy + no-checksum rationale documented in the module docstring so future phases inherit the versioning contract without re-deriving it

## Deviations from Plan

None - plan executed exactly as written. (The fdopen variant above is an implementation detail inside the plan's stated semantics, not unplanned work; tests prove identical behavior.)

## Issues Encountered
None. Note for the orchestrator/merge: `aamatch/persistence.py` and `tests/test_persistence.py` work as namespace-package members without `aamatch/__init__.py` / `tests/__init__.py` (verified on python3.6.9); plan 01-01 supplies those `__init__.py` files and both import forms (`tests.test_persistence` and `discover -s tests`) remain green either way.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Persistence core is ready for its kind-specific consumers: setup-file save/load (01-05) and level-spec file I/O (01-06) should build on `save_container`/`load_container`/`check_container` and reuse the established refusal phrasing
- Phase 4 game container and Phase 7 checkpoint sidecar reuse the same core (research H3)
- Purity-gate plans can list `aamatch.persistence` among pure modules: imports are exactly `json, os, tempfile`
- No blockers

---
*Phase: 01-bootstrap-pure-foundation*
*Completed: 2026-09-05*
