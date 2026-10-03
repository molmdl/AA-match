---
phase: quick-001
plan: 001
subsystem: testing
tags: [purity-gates, ast-audit, unittest, smoke-runner, bash, parallel-safety]

# Dependency graph
requires:
  - phase: 01-bootstrap-pure-foundation
    provides: PURE_MODULES purity gates (tests/test_purity.py, 01-08)
  - phase: 02-data-generation
    provides: run_smoke.sh generalization + verdict-grep contract (02-04)
provides:
  - Per-name registration pins for all 19 PURE_MODULES entries (mutation-proven)
  - Package-coverage direction check (every aamatch/*.py registered or documented non-pure)
  - Parallel-safe per-invocation smoke logs (mktemp, zero shared /tmp/smoke_out.txt)
  - Timeout-vs-missing-marker FAIL block in run_smoke.sh (status 124 named explicitly)
affects: [all later phases — every phase inherits the purity gates and smoke runner]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Registration-pin TestCase pattern extended from 3 per-module classes to a full 19-name subTest loop + direction-2 package coverage"
    - "Per-run mktemp log + PIPESTATUS[0] fail-diagnosis pattern for verdict-by-grep wrapper scripts"

key-files:
  created: []
  modified:
    - tests/test_purity.py (+55 lines, purely additive)
    - smoke/run_smoke.sh (17 -> 42 lines)

key-decisions:
  - "Inline 19-name literal inside the test method (NOT a module-level twin of PURE_MODULES) — editing the test is the only way to silence it, house pattern per the 3 legacy pin classes"
  - "assertIn per name only — NO set-equality, NO length pin — additions stay governed by the established per-module pin-class pattern"
  - "non_pure list = engine, geometry, placement, wizard, gamestart, upload, setup_window, game_window (cmd/Qt tier; Gate D still compiles them); __init__ skipped (Gate A2 covers it)"
  - "mktemp logs persist in /tmp for inspection — never cleaned up (rm is denied; the OS owns /tmp)"

patterns-established:
  - "Two-direction registration coverage: direction 1 (every declared pure name pinned individually) + direction 2 (every package file registered-or-documented-non-pure) — a new module file can never silently escape all gates"
  - "TMO_STATUS from PIPESTATUS[0] captured as the IMMEDIATE next command after the pipeline; grep verdict byte-compatible (exit 0 iff PASS marker present)"

# Metrics
duration: ~5 min
completed: 2026-10-03
---

# Quick Task 001: Purity Pins + Smoke Hardening Summary

**All 19 PURE_MODULES names are now mutation-proven registered (deleting any one fails the suite) and smoke verdicts are parallel-safe with timeout-vs-missing-marker FAIL diagnostics — the two CONCERNS.md must-fix items closed with zero gate weakening.**

## Performance

- **Duration:** ~5 min
- **Started:** 2026-10-03T12:41:40Z
- **Completed:** 2026-10-03T12:45:43Z
- **Tasks:** 2/2
- **Files modified:** 2

## Accomplishments

- **CONCERNS.md issue 1 (HIGH) CLOSED:** `TestPureModuleRegistrationPins` pins every one of the 19 PURE_MODULES names (previously only 3 of 19 were pinned — deleting the other 16 failed nothing, so Gates A/A2/B/D silently skipped unregistered modules). A second method enforces the reverse direction: every `aamatch/*.py` file must be registered or on the documented non-pure list, so a brand-new module can never escape all gates silently.
- **CONCERNS.md issue 2 (MEDIUM-HIGH) CLOSED:** `run_smoke.sh` now tees each invocation into its own `mktemp /tmp/smoke_out.XXXXXX.txt` (zero occurrences of the shared `/tmp/smoke_out.txt` remain — parallel GSD waves can no longer cross-report verdicts), and a missing PASS marker now produces a printed FAIL block naming the script, the reason (timeout status 124 vs wrapper exit vs marker missing), the log path, and the last 40 lines.
- Verdict semantics byte-compatible: same `=== SMOKE-$NN PASS ===` grep as the single verdict, NN basename derivation + legacy 01 fallback unchanged, exit status == grep verdict, `set -e` pipeline behavior preserved.

## Task Commits

| Task | Commit | Message |
|------|--------|---------|
| 1 | `88519a1` | `test(quick-001): pin all 19 PURE_MODULES registrations + package coverage gate` |
| 2 | `bff584d` | `fix(quick-001): per-run smoke logs + timeout-vs-missing-marker FAIL block in run_smoke.sh` |

## Task 1 — Mutation Proof (mandatory, never committed)

**Procedure:** temporarily deleted `'persistence', ` from the PURE_MODULES literal (edit tool), ran `python3.6 -m unittest tests.test_purity -v`, then restored.

### Mutated state (FAIL — observed)

```
FAIL: test_every_pure_module_name_is_pinned (tests.test_purity.TestPureModuleRegistrationPins) (module='persistence')
AssertionError: 'persistence' not found in ['setup_state', 'level_spec', 'backup', 'paths', 'vec3', 'spatial', 'manifest', 'capability', 'thresholds', 'detector', 'generator', 'game_state', 'wizard_core', 'wizard_text', 'setup_form', 'game_file', 'status_text', 'checkpoint'] : aamatch/persistence.py must be registered in PURE_MODULES (unregistered pure modules are silently ungated)

FAIL: test_every_package_module_is_registered_or_documented_non_pure (tests.test_purity.TestPureModuleRegistrationPins) (module='persistence')
AssertionError: False is not true : aamatch/persistence.py is registered in NEITHER PURE_MODULES nor the documented non-pure list -- register it (and gate it) or add it to the non-pure list with a reason

Ran 10 tests in 2.797s
FAILED (failures=3)
```

The third failure was Gate A (`test_pure_modules_only_whitelisted_imports_anywhere`, 4 findings: `level_spec`/`manifest`/`game_file`/`checkpoint` all import `from .persistence import ...`, a target no longer pure). The plan predicted Gate A/B would "simply shrink scope … this pin should be the only failure" — that held for Gate B (subprocess import of 18 modules stayed green) but not Gate A, because `persistence` is a *relative-import target* of four still-registered pure modules, so removing it is also a Gate-A violation. The pin fires loudly either way (recorded honestly; not a defect — STRONGER than planned: removal trips both the explicit pin AND the import-target gate).

### Restored state (PASS — observed)

```
test_every_package_module_is_registered_or_documented_non_pure (tests.test_purity.TestPureModuleRegistrationPins) ... ok
test_every_pure_module_name_is_pinned (tests.test_purity.TestPureModuleRegistrationPins) ... ok
Ran 10 tests in 2.858s
OK
```

`git diff --stat` after restore: `tests/test_purity.py | 55 ++++ (1 file changed, 55 insertions(+))` — purely additive; the 3 legacy pin classes byte-identical (`grep -c "Registration(unittest.TestCase)"` → 3; `sys.modules` count 4, unchanged from baseline, docstring mentions only — zero stubs).

## Task 2 — Verdict Semantics Proofs

### FAIL-path proof (bogus script, fast)

`bash smoke/run_smoke.sh smoke/no_such_smoke_zz.py 30; echo "exit=$?"` produced:

```
=== run_smoke: no_such_smoke_zz (timeout 30s, log /tmp/smoke_out.B4I7zV.txt) ===
[pymol.CmdException: Error: failed to open file "smoke\no_such_smoke_zz.py"]
=== SMOKE-01 FAIL ===
script: smoke/no_such_smoke_zz.py
reason: PASS marker '=== SMOKE-01 PASS ===' missing from output
full log: /tmp/smoke_out.B4I7zV.txt
--- last 40 lines of this run ---
[40-line traceback tail]
exit=1
```

NN legacy fallback → 01 works; the marker-missing branch fired (cmd.exe exited 0 despite the PyMOL error — exactly the "exit codes cannot carry verdicts through cmd.exe" property the grep-verdict contract exists for).

### Real PASS run (load-bearing)

`bash smoke/run_smoke.sh smoke/smoke_01_bootstrap.py; echo "exit=$?"`:

```
=== run_smoke: smoke_01_bootstrap (timeout 120s, log /tmp/smoke_out.CGUstu.txt) ===
SMOKE-ENV root: C:\Users\nglok\Desktop\WORKDIR\molmdl\AA-match
SMOKE-01 import aamatch                         PASS 0.1.0
... (loader registered/module/loaded/name PASS, env probes OK) ...
=== SMOKE-01 PASS ===
exit=0
```

Header log path `/tmp/smoke_out.CGUstu.txt` grep-verified to contain the PASS marker (`grep -c` → 1).

## Final Verification (both tasks landed, from repo root)

| Gate | Result |
|------|--------|
| `python3.6 -m py_compile aamatch/*.py` | exit 0, silent |
| `python3.6 -m unittest discover -s tests -v` | **933 tests, OK** (931 baseline + 2 new, as predicted), zero failures/errors |
| `bash -n smoke/run_smoke.sh` | exit 0, silent |
| `grep -c "/tmp/smoke_out.txt" smoke/run_smoke.sh` | 0 (shared log eliminated); `PIPESTATUS` and `sed -n` NN derivation present |
| Real `bash smoke/run_smoke.sh smoke/smoke_01_bootstrap.py` | `=== SMOKE-01 PASS ===`, exit 0 |
| `git log --oneline -2` | exactly the two quick-001 commits (`test` then `fix`), no mutated intermediates, clean tree |

## Deviations from Plan

**1. [Rule 1 — plan-prediction correction, no code change] Mutation proof fired 3 tests, not 1.**

- **Found during:** Task 1 verification (mutation step)
- **Issue:** The plan predicted removing `'persistence'` from PURE_MODULES would fail ONLY the new pin test ("Gate A/B simply shrink scope … this pin should be the only failure"). Observed: 3 failures — the new pin test, the new coverage test (also an explicit registration pin — expected in hindsight), and Gate A, because `persistence` is a relative-import target of 4 still-registered pure modules (`level_spec`, `manifest`, `game_file`, `checkpoint`), which Gate A then flags.
- **Resolution:** No fix needed — the outcome is STRONGER than planned (a silent unregistration trips both the explicit pin and the import-target gate). Recorded verbatim above; the mutated state was never committed.
- **Files modified:** none beyond the plan's file set.

No authentication gates, no architectural decisions, no environmental smoke failures.

## Next Steps

- Orchestrator performs the final `docs(quick-001)` STATE.md commit (this SUMMARY + STATE.md position update).
- `.planning/codebase/CONCERNS.md` issues 1 and 2 can be marked CLOSED on the next codebase-map refresh (out of scope per repo laws — not touched here).
