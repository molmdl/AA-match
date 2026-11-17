---
phase: 09-help-docs-release-audit
plan: 10
subsystem: testing
tags: [docs-audit, coverage-checks, readme, data-sources, tooltips, version-pin, gate-c]

# Dependency graph
requires:
  - phase: 09-help-docs-release-audit
    provides: 09-03/06/09 final README (Install/Usage, demo table, Project Structure, TBD-free)
  - phase: 09-help-docs-release-audit
    provides: 09-04/05/07/08 final help surfaces + single-home wiring (help_text read sites)
provides:
  - "tests/test_docs_audit.py - 21-check mechanical floor for DOCS-02 (README/DATA_SOURCES/tooltips/versions)"
  - "docs drift now turns a bare `python3.6 -m unittest discover -s tests` run red"
affects: [09-12 docs audit (cite the battery rows), 09-13 battery sweep (runs it)]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Coverage/presence checks only (a required string must EXIST) - Gate-C safe"
    - "Qt-tier tooltips pinned via SOURCE-text substring after joining line-split literals (never imported)"
    - "Expectations derived from MANIFEST at runtime, never hardcoded per-set lists"

key-files:
  created:
    - tests/test_docs_audit.py
  modified: []

key-decisions:
  - "NEW test file (test_demo_data.py 'may NOT be relaxed' - left byte-untouched)"
  - "Tooltip pins join implicitly-concatenated literals before substring matching (live text is line-split)"
  - "Private-name prohibitions (_INTERACTION_LABELS/_INTERACTION_TIPS/_MODE_CONTEXT) are identifier-scoped, not prose greps"

patterns-established:
  - "Docs surfaces are pinned by presence of exact strings; a doc edit that drops a pinned string fails the suite"

# Metrics
duration: ~20min
completed: 2026-11-18
---

# Phase 09 Plan 10: Docs-Audit Battery Summary

**21-check `tests/test_docs_audit.py` turns DOCS-02 into a standing suite floor: README completeness, DATA_SOURCES file/section/license coverage, version sync, load-bearing tooltips, and the help_text single-home wiring all fail red on drift, with zero stubs and zero prose greps**

## Performance

- **Duration:** ~20 min
- **Started:** 2026-11-17T21:42:07Z
- **Completed:** 2026-11-17T23:33:06Z (metadata)
- **Tasks:** 2 (author battery; full-suite run + commit)
- **Files modified:** 1 created (`tests/test_docs_audit.py`, 291 lines)

## Battery count & suite delta

| Metric | Value |
|--------|-------|
| New test classes | 7 |
| New tests | **21** |
| Baseline WSL suite | 1007 (09-09) |
| Final WSL suite | **1028** (1007 + 21) |
| Result | `Ran 1028 tests ... OK` |

## Test class -> check-family map

| Class | Tests | Check family |
|-------|------:|--------------|
| `TestReadmePlaceholders` | 4 | No `TBD`; `## Usage` non-empty; `## Project Structure` fenced block non-empty (!= `#TBD`); `## Acknowledgements` TBD-free |
| `TestReadmeDemoTable` | 4 | Manifest has 10 sets; every set_id appears in README; `development fixture` present; `docs/DATA_SOURCES.md` link present |
| `TestReadmeVibeWarning` | 2 | README line 1 and line 2 byte-exact (line 1 trailing hard-break space asserted) |
| `TestDataSourcesCoverage` | 4 | 18 ligand `.sdf` files; every `ligands/<basename>` named; every set has a `^### <set_id>\b` section; each curated set's MANIFEST license appears verbatim inside its own section span |
| `TestVersionConsistency` | 3 | `# Version: 0.1.0` in first 3 lines; `__version__ = '0.1.0'`; both parsed strings equal |
| `TestTooltipPins` | 2 | Confirm / Save / Import / Hint / Skip-GiveUp dropdown (game_window.py) + Browse / Cleanup fragment (setup_window.py) present in source text |
| `TestSingleHomeWiring` | 2 | `help_text.INTERACTION_LABELS` / `INTERACTION_TIPS` / `MODE_CONTEXT` read sites present; old privates `_INTERACTION_LABELS` / `_INTERACTION_TIPS` / `_MODE_CONTEXT` gone |

## Tooltip pins (verified against LIVE source, no delta)

All seven plan-quoted strings matched the live sources exactly (none drifted):

- Confirm: `Attempt to finish this molecule: runs detection; it advances only when all required interactions are formed.`
- Save: `Save the running game (PyMOL session + game state) to a checkpoint file.`
- Import: `Load a saved checkpoint (.aamz) to resume playing, or an exported game file (.aamatch.json) to start it fresh.`
- Hint: `Highlight the amino acids that could still form a required interaction (carbon recolor only).`
- Skip/Give Up dropdown: `Skip the current molecule or give up the game (both ask for confirmation).`
- Browse: `Pick an SDF or MOL2 molecule file (single file; a multi-record file provides several molecules).`
- Cleanup fragment: `game-generated object` (from `Remove the game-generated objects from the scene.`)

## Files Created/Modified

- `tests/test_docs_audit.py` — NEW; reads README.md, docs/DATA_SOURCES.md, aamatch/data/MANIFEST.json, aamatch/data/ligands/, aamatch/__init__.py, aamatch/setup_window.py, aamatch/game_window.py as text/data only. No Qt/PyMOL import.

## Decisions Made

- New file rather than extending `tests/test_demo_data.py` (its header forbids relaxation).
- Expectations derived from the MANIFEST at runtime (10 sets; 9 curated = 8 PubChem + 1 wwPDB), never hardcoded per-set lists.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Tooltip presencing required joining line-split literals**

- **Found during:** Task 1 (authoring the battery)
- **Issue:** The plan says "source-text substring asserts", but every live tooltip sentence is written across implicitly concatenated literals (`'... it '` newline `'advances ...'`), so a raw substring over the file text does NOT match (probe: `probe in src` -> False).
- **Fix:** `_joined_string_source()` collapses `'` + newline + whitespace + `'` before matching, yielding the logical sentence (probe: True for all pins). Still pure text, stdlib `re` only; Qt modules never imported; the plan's stdlib set (json/os/re) is honored unchanged.
- **Files modified:** `tests/test_docs_audit.py`
- **Verification:** Deliberate red/green — flipped the Save pin locally -> `TestTooltipPins` FAILED; restored -> OK; `diff` against backup identical.
- **Committed in:** b9b32d3 (Task 2 commit)

**2. [Rule 1 - Bug] Docstring wording tripped the Gate-C sanity grep**

- **Found during:** Task 2 (sanity greps)
- **Issue:** The header docstring originally contained the literal token `sys.modules` (prose describing compliance), so `grep -c "sys.modules" tests/test_docs_audit.py` returned 1 instead of the required 0 — the exact prose-grep trap AGENTS.md gate 3 warns about.
- **Fix:** Reworded the docstring to "ZERO module-stub injections"; grep now returns 0. No code/assert change.
- **Files modified:** `tests/test_docs_audit.py`
- **Verification:** `grep -c "sys.modules"` == 0; `grep -n subprocess` empty; full suite still 1028 OK.
- **Committed in:** b9b32d3 (Task 2 commit)

---

**Total deviations:** 2 auto-fixed (both Rule 1 implementation details; no semantic scope change)
**Impact on plan:** Both were required to satisfy the plan's own acceptance greps and to make presence checks actually match the live source. No new scope.

## Issues Encountered

None.

## Verification receipts

- `python3.6 -m py_compile aamatch/*.py` -> PYC-OK
- `python3.6 -m unittest tests.test_docs_audit -v` -> 21 tests OK
- `python3.6 -m unittest discover -s tests -v` -> `Ran 1028 tests ... OK`
- `grep -c "sys.modules" tests/test_docs_audit.py` -> 0
- `grep -n "subprocess" tests/test_docs_audit.py` -> empty
- `tests/test_demo_data.py` untouched (no diff)

## User Setup Required

None.

## Next Phase Readiness

- DOCS-02 now has a permanent mechanical floor. 09-12's audit table can cite a machine row per check; 09-13's battery sweep runs this file.
- `tests/test_docs_audit.py` is deliberately NOT listed in README's Project Structure gate-file prose (09-09 decision: no volatile per-file counts) — no follow-up needed.

---

*Phase: 09-help-docs-release-audit*
*Completed: 2026-11-18*
