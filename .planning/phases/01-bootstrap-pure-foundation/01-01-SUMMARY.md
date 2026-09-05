---
phase: 01-bootstrap-pure-foundation
plan: 01
subsystem: plugin-skeleton
tags: [pymol, plugin-loader, lazy-imports, metadata-block, unittest, python3.6]

# Dependency graph
requires: []
provides:
  - "aamatch/ installable plugin package skeleton: metadata-first __init__.py (# Version: 0.1.0 / # Citation-Required: No), __init_plugin__ entry point, Qt-free run_plugin_gui placeholder"
  - "tests/ package + 5-test loader-contract suite (test_package_skeleton.py) green under bare python3.6 with ZERO sys.modules stubs"
  - "Lazy-import discipline at the composition root — the prerequisite that lets every later pure-layer test run stub-free"
affects: [01-02, 01-03, 01-04, 01-05, phase-2-headless-engine, phase-4-qt-ui, phase-9-docs]

# Tech tracking
tech-stack:
  added: []   # stdlib only by design (unittest, ast, io, os, sys, contextlib)
  patterns:
    - "Metadata-first __init__.py: '# Key: value' comment block as the literal first lines, before the docstring (loader parses them, plugins/__init__.py:193-210)"
    - "Zero module-level imports in the composition root; pymol imports are function-level and FIRST inside __init_plugin__"
    - "WSL-pure unittest with sys.path bootstrap (works via module spec and discover) — no stubs ever"
    - "AST-based import gate instead of grep (immune to docstring false positives)"

key-files:
  created:
    - aamatch/__init__.py
    - tests/__init__.py
    - tests/test_package_skeleton.py
  modified: []

key-decisions:
  - "Repo-root aamatch/ package (NOT pymol/aamatch/) — matches ARCHITECTURE.md:79-109 sketch (planner decision U5)"
  - "ZERO module-level imports in __init__.py — not even stdlib; makes the pure-layer zero-stubs proof trivial and permanent (PITFALLS.md Pitfall 1, R8.5)"
  - "addmenuitemqt called FIRST inside __init_plugin__ — headless QtNotAvailableError is caught cleanly by the loader and avoids the cmd.extend restore quirk"
  - "No _version.py, no dialog singleton, no Qt in Phase 1 — those arrive in later phases (no pre-creation)"
  - "Menu label 'AA-match' independent of package name 'aamatch' (installation.py:83-88; research §1.4)"

patterns-established:
  - "Metadata block placement: # Version must precede the docstring or it parses to {} (breaks reinstall version compares — research pitfall G)"
  - "Contract-test style: replicate loader behavior (metadata parse, co_consts[0] docstring, AST import scan) rather than import pymol"
  - "3.6 syntax floor gate: python3.6 -m py_compile over every shipped file (research pitfall L)"

# Metrics
duration: 30 min
completed: 2026-09-05
---

# Phase 1 Plan 1: Bootstrap aamatch Package Skeleton Summary

**Metadata-first `aamatch/__init__.py` plugin skeleton (loader-contract entry, Qt-free placeholder) proven by 5 stub-free WSL contract tests under bare python3.6**

## Performance

- **Duration:** 30 min
- **Started:** 2026-09-05T09:12:32Z
- **Completed:** 2026-09-05T09:42:46Z
- **Tasks:** 3
- **Files modified:** 3 (all created)

## Accomplishments

- `aamatch/` installable plugin package skeleton at repo root: `# Version: 0.1.0` + `# Citation-Required: No` metadata block as the literal first two lines (loader-contract placement), docstring, `__version__`, `__init_plugin__` (local `addmenuitemqt` import called FIRST), and a deliberately Qt-free `run_plugin_gui` print placeholder
- ZERO module-level imports anywhere in the composition root — the package imports cleanly under bare `python3.6` with no pymol/Qt/numpy and no stubs, permanently securing the pure-layer test discipline (PITFALLS.md Pitfall 1, research R8.5)
- 5-test loader-contract suite (`tests/test_package_skeleton.py`, 122 lines): metadata parse replication, `co_consts[0]` docstring survival, AST zero-module-level-import gate, entry-point existence, placeholder stdout version check — green under both `python3.6 -m unittest tests.test_package_skeleton -v` and `discover -s tests -v`
- 3.6 syntax floor gate passed over all three shipped files

## Task Commits

Each task was committed atomically:

1. **Task 1: Create aamatch/__init__.py (metadata-first, Qt-free skeleton)** - `e3e5ea0` (feat)
2. **Task 2: Create tests package + skeleton contract test** - `62190f6` (test)
3. **Task 3: Syntax gate + commit** — gate passed clean (`py_compile` exit 0 on all 3 files); no separate commit was needed because Tasks 1–2 already carried the atomic per-task commits and Task 3's prescribed commit message (`feat(01-01): aamatch package skeleton...`) is Task 1's commit. No empty commit was created.

**Plan metadata:** see final `docs(01-01)` commit (SUMMARY.md)

## Files Created/Modified

- `aamatch/__init__.py` - plugin entry point: metadata block + docstring + `__version__` + `__init_plugin__` (addmenuitemqt first) + Qt-free `run_plugin_gui`
- `tests/__init__.py` - one-line package marker enabling `unittest discover -s tests`
- `tests/test_package_skeleton.py` - WSL-pure contract suite: metadata parse replication, docstring survival via `compile(...).co_consts[0]`, AST module-level-import scan, entry-point existence, placeholder stdout check

## Decisions Made

- Repo-root `aamatch/` layout (not `pymol/aamatch/`) — planner decision recorded in plan; doc-only impact, no renames later
- Zero module-level imports in `__init__.py` — even stdlib — so `import aamatch` under bare python3.6 is the purity proof itself
- `from pymol.plugins import addmenuitemqt` is function-level and the FIRST statement of `__init_plugin__` (headless-safe; loader catches `QtNotAvailableError` cleanly)
- Placeholder is a `print`, not a stub dialog — proves menu wiring at the [HUMAN] install checkpoint (01-09) with zero code Phase 4 must rewrite

## Deviations from Plan

None - plan executed exactly as written.

(Note: Task 3's "commit" resolved to the gate itself — see Task Commits; not an unplanned change, just an atomic-commit protocol consequence.)

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Composition root exists and is import-clean; sibling wave-1 plans (pure modules: setup_state / level_spec / persistence / backup / paths) can now assume stub-free `import aamatch.<module>` (their `tests/__init__.py` note says "leave if exists" — it now exists, identical one-liner)
- Ready for `python3.6 -m unittest discover -s tests -v` to scale with later plans' suites
- [HUMAN] install checkpoint (01-09) remains: build zip + Plugin Manager install to prove menu registration (not assertable headless — research §1.3)

---
*Phase: 01-bootstrap-pure-foundation*
*Completed: 2026-09-05*
