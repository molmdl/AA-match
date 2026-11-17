---
phase: 09-help-docs-release-audit
plan: 09
subsystem: docs
tags: [readme, project-structure, tiers, pure-modules, smoke-battery]

# Dependency graph
requires:
  - phase: 09-help-docs-release-audit
    provides: 09-04 help_text.py (the 29th module / 20th PURE module)
  - phase: 09-help-docs-release-audit
    provides: 09-06 demo table + acknowledgements + banner b-drop (README state)
provides:
  - "README '## Project Structure' filled from the live tree (29 modules, 3 enforced tiers)"
  - "README fully TBD-free (all four DOCS-01 sections filled)"
affects: [09-10 docs-audit battery, 09-12 docs audit, 09-13 battery sweep]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Live enumeration at write time - never trust a pre-phase research count"
    - "README structure mirrors the enforced tier registries (PURE_MODULES / cmd / Qt)"

key-files:
  created: []
  modified:
    - README.md

key-decisions:
  - "Module counts read live: 29 aamatch/*.py = 1 entry + 20 PURE + 6 CMD + 2 Qt"
  - "No per-file test counts; name the standing gate files instead (counts churn)"
  - ".planning/ deliberately excluded from the tree with a 'not shipped' closing line"

patterns-established:
  - "Structure section is a fenced tree (non-empty for 09-10's block parser) + tier prose"

# Metrics
duration: ~15min
completed: 2026-11-18
---

# Phase 09 Plan 09: README Project Structure Summary

**README's last placeholder replaced with the live 29-module layered tree (1 entry + 20 PURE + 6 CMD + 2 Qt) and a docs/gates/data/scripts map - README now fully TBD-free**

## Performance

- **Duration:** ~15 min (docs-only plan; start not precisely instrumented)
- **Started:** 2026-11-17T21:24:00Z (approx)
- **Completed:** 2026-11-18
- **Tasks:** 2 (write section; commit + read-back)
- **Files modified:** 1 (`README.md`, +60 / -1)

## Live enumeration receipts (at write time)

| Item | Live value | Command |
|------|-----------|---------|
| `aamatch/*.py` modules | **29** | `ls aamatch/*.py \| wc -l` |
| PURE_MODULES | **20** | `tests/test_purity.py:101-105` |
| CMD tier (non-UI) | **6** (`engine`, `geometry`, `placement`, `upload`, `gamestart`, `wizard`) | `NON_UI_CMD_CORE` + `SCANNED_MODULES` (`tests/test_wizard_source.py:51-75`) |
| Qt tier | **2** (`setup_window`, `game_window`) | const-tier partition |
| Entry point | **1** (`__init__.py`, exempt) | `CMD_TIER_EXEMPT` |
| Smoke scripts | **25** (`smoke_01`..`smoke_25` + `run_smoke.sh`) | `ls smoke/smoke_*.py \| wc -l` |
| Test files | **29** `test_*.py` (+ `__init__.py`) | `ls tests/test_*.py \| wc -l` |
| MANIFEST sets / entries | **10 / 18** | `json` parse of `aamatch/data/MANIFEST.json` |
| Bundled ligand SDFs | **18** | `ls aamatch/data/ligands` |
| Demo specs | **10** | `ls scripts/demo_specs/*.json \| wc -l` |

Module-name cross-check: all **29** module names in the README block exist in
`ls aamatch/*.py`, and **no** live module is unlisted (`set(names) ==
set(live)` verified by script).

## Accomplishments
- Replaced the sole remaining `#TBD` fenced block with the real tree: entry
  point, the 20 PURE modules with 2-5-word roles, the 6 CMD-tier modules, the
  2 Qt-tier modules, `data/`, `tests/`, `smoke/`, `scripts/`.
- Named the enforced tier law (PURE = stdlib + pure-only, pinned by
  `tests/test_purity.py`; CMD drives `cmd`; Qt = two-tab shell).
- Named the gate files (`test_purity.py`, `test_wizard_source.py`,
  `test_code_audit.py`, `test_demo_data.py`, `test_demo_supply.py`) with no
  volatile per-file counts; `test_docs_audit.py` deliberately not listed
  (lands in 09-10).
- `grep -c 'TBD' README.md` = **0** - README is fully placeholder-free.

## Task Commits

1. **Tasks 1+2: fill Project Structure + commit/read-back** - `16dea28` (docs) `docs(09-09): fill README Project Structure`
2. **Plan metadata** - docs commit (SUMMARY + STATE), separate

## Files Created/Modified
- `README.md` - `## Project Structure` now holds the live 29-module tree +
  tier prose + gates/data/scripts map; `#TBD` removed.

## Decisions Made
- Use the LIVE tree (29 modules / 20 PURE), not the research pack's pre-help_text
  28/19 counts.
- Keep the structure as a fenced code block so 09-10's
  `TestReadmePlaceholders` block parser sees non-empty content.
- Exclude `.planning/` from the user-facing tree; one closing line says it is
  not shipped.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None. `python3.6 -m py_compile aamatch/*.py` = PYC-OK;
`python3.6 -m unittest discover -s tests` = **1007 tests OK** (docs-only change,
standing gates unaffected).

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- DOCS-01 content complete: Usage (09-03), demo table + Acknowledgements
  (09-06), Project Structure (09-09).
- Ready for 09-10 (`tests/test_docs_audit.py` machine pins), 09-12 (docs audit),
  09-13 (battery sweep).
- Read-back: vibe-warning lines 1-2 byte-identical, banner already dropped by
  09-06; links `docs/DATA_SOURCES.md` and `LICENSE` resolve; `git diff HEAD~1
  --stat` = `README.md` only.

---
*Phase: 09-help-docs-release-audit*
*Completed: 2026-11-18*
