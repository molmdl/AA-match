---
phase: 01-bootstrap-pure-foundation
plan: 04
subsystem: pure-foundation
tags: [paths, wsl, windows, guard, unittest, python3.6, stdlib-pure]

# Dependency graph
requires: []
provides:
  - "aamatch/paths.py::to_windows_path — WSL→Windows path guard (converts ONLY /mnt/<letter>/ paths; idempotent; spaces preserved)"
  - "aamatch/paths.py::package_data_path — __file__-anchored bundled-data resolution, never cwd-relative"
  - "tests/test_paths.py — green 17-test suite: full R7 14-case matrix + 3 package_data_path assertions"
affects: [02-data-cmd-engine, 03-wizard-interaction, 04-07-qt-phases, "any phase calling cmd.load/cmd.save/file APIs on Windows PyMOL"]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Guard-not-transform path conversion: only /mnt/<single-letter>/ converts, everything else passes through unchanged"
    - "Pure-layer module: stdlib-only imports + purity docstring, unit-testable under bare python3.6"
    - "__file__-anchored resource resolution instead of os.getcwd()"

key-files:
  created:
    - aamatch/paths.py
    - tests/test_paths.py
  modified: []

key-decisions:
  - "Ported prior-art guard (demos.py:59-78) verbatim, incl. load-bearing len(parts)==4 term — no drive-letter validation beyond single-alpha, no special-casing of /mnt//x"
  - "Named one test per matrix row (14 tests) instead of table-driven, for bisectable failure names"
  - "Documented the case-9 asymmetry ('/mnt/c' unchanged vs '/mnt/c/' → 'C:\\') in the docstring and pinned it with a dedicated test"

patterns-established:
  - "Pure module contract: module-level imports stdlib only + purity docstring (no pymol/Qt in aamatch/paths.py)"
  - "TDD RED-first test file naming: test_XX_<behavior> matching the research matrix rows"
  - "All future cmd.load/cmd.save/file-API calls route through to_windows_path before touching the filesystem"

# Metrics
duration: 33 min
completed: 2026-09-05
---

# Phase 1 Plan 04: Pure Path Guard Summary

**WSL→Windows path guard (`to_windows_path`) ported verbatim from proven prior art into a pure, stdlib-only module, plus `__file__`-anchored `package_data_path` — proven by a green 17-test suite covering the full 14-case R7 matrix.**

## Performance

- **Duration:** 33 min
- **Started:** 2026-09-05T09:12:54Z
- **Completed:** 2026-09-05T09:45:25Z
- **Tasks:** 1 feature (RED → GREEN → REFACTOR)
- **Files modified:** 2 created

## Accomplishments
- `to_windows_path()`: guard semantics ported verbatim from prior-art `demos.py:59-78` (research F1-F2) — converts ONLY `/mnt/<single-letter>/` WSL-mount paths to backslash Windows form; already-Windows, UNC, relative, and genuine Linux paths (and `''`) pass through unchanged; idempotent; spaces preserved
- `package_data_path()`: bundled-data resolution anchored to the installed package directory (`__file__`), never `os.getcwd()` (PITFALLS.md Pitfall 2 / :58)
- Full R7 14-case conversion matrix green, plus 3 package_data_path assertions — 17/17 passing under bare python3.6
- The load-bearing `len(parts) == 4` term and the case-9 asymmetry (`/mnt/c` unchanged vs `/mnt/c/` → `C:\`) are documented in the docstring and pinned by tests

## Task Commits

Each TDD phase was committed atomically:

1. **RED: failing 14-case matrix** - `bfdaf9f` (test)
2. **GREEN: implement pure path guard** - `5126f07` (feat)
3. **REFACTOR:** none needed — verbatim port, already minimal; tests stayed green (no commit)

## Files Created/Modified
- `aamatch/paths.py` - pure path helpers: `to_windows_path` guard + `package_data_path` (stdlib-only, purity docstring)
- `tests/test_paths.py` - 17 tests: 14 named matrix cases + 3 package_data_path assertions (135 lines)

## Decisions Made
- Ported the prior-art guard **verbatim** (research F1-F2) rather than "improving" it: it is shipped-and-proven across all v1 phases of the prior art; no drive-letter validation beyond single-alpha, no special handling of `/mnt//x`, nothing upper/lower-cased except the drive letter (per plan implementation constraints)
- Wrote **one named test per matrix row** (rather than a table-driven test) so a regression names the exact R7 case that broke
- Documented the **case-9 asymmetry** in the module docstring (bare mount root `/mnt/c` passes through while `/mnt/c/` converts) — real call sites always carry a filename below the mount root, so the asymmetry is harmless but pinned by `test_09`

## Deviations from Plan

None - plan executed exactly as written.

(Note: the prior-art file `tmp/bioCHEMeleon/` is git-ignored and absent in the execution worktree; per the plan's own NOTE, the guard was ported from the tracked research doc §F1-F2 — whose quoted semantics were cross-checked against the actual prior-art source in the main checkout before implementation.)

## Issues Encountered
None.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- `to_windows_path` is ready for every future `cmd.load`/`cmd.save`/file-API call site (Phases 2-8) — call sites must route Windows-viewer paths through it
- `package_data_path` is ready for bundled-data lookup (levels, demo sets) in Phase 2+
- No blockers; this plan is wave-1 parallel work alongside 01-01/01-02/01-03 (disjoint files)

---
*Phase: 01-bootstrap-pure-foundation*
*Completed: 2026-09-05*
