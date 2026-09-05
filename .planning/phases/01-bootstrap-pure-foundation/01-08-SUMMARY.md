---
phase: 01-bootstrap-pure-foundation
plan: 08
subsystem: testing
tags: [ast, unittest, purity-gates, python3.6, subprocess, py_compile, zero-stubs]

# Dependency graph
requires:
  - phase: 01-bootstrap-pure-foundation
    provides: "Plans 01-02..01-06 built the five pure modules the gates scan (setup_state, level_spec, persistence, backup, paths) and the lazy-__init__ skeleton (01-01)"
provides:
  - "Gate A: AST import scan over all 5 pure modules — every Import/ImportFrom node in any scope (module level AND function bodies), FORBIDDEN roots + stdlib whitelist + relative-import-to-pure rule"
  - "Gate A2: lazy-__init__ rule — aamatch/__init__.py must keep zero module-level imports (function-level pymol imports in __init_plugin__ allowed by design, R8.5)"
  - "Gate B: clean-subprocess import proof — every pure module imports under bare python3.6, cwd=repo-root, ZERO sys.modules stubs (P10: exit codes, not in-process inspection)"
  - "Gate D: 3.6 syntax floor — every aamatch/*.py compiles via python3.6 -m py_compile"
  - "Negative control: proves the gate fails on real forbidden imports AND ignores docstring prose (P2/G3 grep-trap immunity, pinned by exact-count assertions)"
  - "AGENTS.md standing-gates section: commands, purity contract, grep warning, two-version-gates rule, module-identity rule, dev-loop rule, env pointer"
affects: [all later phases (02-generator, 03-replay, 04-gui, 07-packaging) — the gates run inside the normal suite and AGENTS.md makes the rules standing policy]

# Tech tracking
tech-stack:
  added: []   # stdlib only (ast, subprocess, unittest); zero new dependencies
  patterns:
    - "AST-based import gating (immune to docstring false positives that broke the prior art's grep gate)"
    - "Subprocess import proof for purity (fresh interpreter + cwd=repo-root, never in-process sys.modules checks)"
    - "Negative-control testing: gate sensitivity + docstring immunity pinned by exact finding counts"
    - "Checker as pure function over source text (find_bad_imports(src)) callable on strings, not only files"

key-files:
  created:
    - tests/test_purity.py
  modified:
    - AGENTS.md

key-decisions:
  - "find_bad_imports is a pure function over source text so the negative control exercises it without touching real files (per plan); the file-naming for greppable failures happens in the Gate A test wrapper"
  - "subprocess.run uses stdout/stderr PIPE instead of capture_output — capture_output is Python 3.7+ and these gates must run under python3.6"
  - "No function annotations on find_bad_imports — the plan's prose suggested `-> list[str]`, but 3.6 evaluates annotations at def time and would raise TypeError; documented in the docstring instead"
  - "Negative control pins EXACTLY 2 findings (one pymol, one PyQt5): a grep-based checker would count 4 hits (2 real + 2 docstring) and fail this test — the tripwire is enforced, not just warned about"

patterns-established:
  - "Purity is enforced, not aspired: any future pure module must be added to PURE_MODULES (or it escapes Gate A) and must import only ALLOWED_STDLIB + pure siblings"
  - "Standing rules live in AGENTS.md § 'AA-match standing gates (Phase 1 — inherit into every phase)' so every later session/phase inherits them"

# Metrics
duration: 6min
completed: 2026-09-05
---

# Phase 1 Plan 08: Purity Gates + Standing Rules Summary

**Purity contract mechanically enforced via AST import scan + zero-stub clean-subprocess import proof + 3.6 py_compile floor (5 new tests, suite 109→114 OK), with the standing rules installed in AGENTS.md for every later phase.**

## Performance

- **Duration:** 6 min
- **Started:** 2026-09-05T17:14:58Z
- **Completed:** 2026-09-05T17:21:01Z
- **Tasks:** 3
- **Files modified:** 2 (1 created, 1 modified)

## Accomplishments
- Phase-1 success criterion 2 is now mechanically proven and permanent: `tests/test_purity.py` (280 lines) runs Gate A (AST import scan, all scopes), Gate A2 (lazy-`__init__` rule), Gate B (clean-subprocess import, zero stubs), Gate D (3.6 py_compile) and the negative control as part of the normal `python3.6 -m unittest discover -s tests -v` suite.
- Negative control proves the gate can FAIL: `import pymol` + `from PyQt5 import QtWidgets` in synthetic source yield exactly 2 findings while the same tokens in a docstring yield none (the prior art's grep false-positive is structurally impossible and pinned by test).
- AGENTS.md now carries `## AA-match standing gates (Phase 1 — inherit into every phase)`: the three commands (py_compile floor, unittest discover, smoke runner), the purity contract with the zero-stubs rule (ARCHITECTURE.md's stub pattern explicitly superseded), the grep-gate warning, the two-version-gates rule, module identity, the repo-copy dev loop, and the windows-env-versions pointer.

## Task Commits

Each task was committed atomically:

1. **Task 1: Write tests/test_purity.py (AST gate + subprocess gate + syntax gate + negative control)** - `54090c3` (test)
2. **Task 2: Document standing gates in AGENTS.md** - `30fc6a0` (docs)
3. **Task 3: Full-suite green run** - verification-only; see Deviations below (both files were already committed atomically by Tasks 1–2, so the plan's umbrella `feat(01-08)` commit would have been empty, which is prohibited)

**Plan metadata:** committed with the SUMMARY commit (`docs(01-08): complete purity-gates plan`).

## Files Created/Modified
- `tests/test_purity.py` (created, 280 lines) - Gates A/A2/B/D + negative control; pure stdlib, no stubs anywhere
- `AGENTS.md` (modified, +17 lines) - additive standing-gates section between "GSD workflow" and "Parallel subagent execution"; no existing content rewritten

## Decisions Made
- Checker exposed as pure function `find_bad_imports(src)` over source text (plan-mandated) — enables the negative control without touching real files; Gate A wraps it to prefix failures with file paths so regressions stay greppable.
- 3.6-compat shims: `capture_output` → `stdout/stderr=PIPE`; no `-> list[str]` annotation (3.6 evaluates annotations eagerly). Both are invisible to the gate semantics.
- Task 3 executed as verification-only (no empty commit); the umbrella commit message from the plan is realized by the two atomic per-task commits above.

## Deviations from Plan

None in scope or behavior — plan executed as written. Two execution-level notes:

1. **Task 3 commit realization (protocol, not code):** the plan named an umbrella `feat(01-08)` commit for Task 3, but Tasks 1–2 already committed `tests/test_purity.py` and `AGENTS.md` atomically per the executor commit protocol; an empty third commit is prohibited. Task 3 is therefore the full-suite verification run (114/114 OK).
2. **3.6 compatibility adjustments (Rule 3-class, inside Task 1):** `capture_output` (3.7+) replaced with `stdout/stderr=PIPE`, and the `list[str]` annotation dropped (3.6 eager annotation evaluation would TypeError). No behavior change; gates verified green under python3.6.

---

**Total deviations:** 0 auto-fixed bugs/critical/blocking; 2 execution-level notes (1 commit-protocol, 2 micro-shims for 3.6)
**Impact on plan:** None — all success criteria met exactly as specified.

## Issues Encountered
None. Baseline suite was green (109 tests) before this plan; the 5 new gate tests pass on the first run.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Phase-1 success criterion 2 is permanently enforced: any future regression (e.g. someone adds `import numpy` or a lazy `from pymol import cmd` inside a pure module's function body, or a module-level import in `__init__.py`) fails the normal suite with a greppable message naming the file and the offending import.
- To cover a future pure module, add its name to `PURE_MODULES` in `tests/test_purity.py`; the AST whitelist (`ALLOWED_STDLIB`) is the only sanctioned import surface.
- Ready for 01-09 (the remaining wave-3 plan) and then phase transition; no blockers or concerns.

---
*Phase: 01-bootstrap-pure-foundation*
*Completed: 2026-09-05*
