---
phase: 01-bootstrap-pure-foundation
plan: 07
subsystem: headless-toolchain
tags: [pymol, headless, cmd-exe, smoke, plugin-loader, windows-conda, pyqt5, numpy]

# Dependency graph
requires:
  - phase: 01-bootstrap-pure-foundation (01-01)
    provides: "aamatch/ installable plugin skeleton at repo root (metadata-first __init__.py, __init_plugin__, Qt-free placeholder) — the subject this smoke proves"
provides:
  - "Frozen headless toolchain recipe: smoke/run_smoke.sh (cd to repo root + timeout 120 + cmd.exe run-conda-pymol.bat -cq + PASS-marker grep) — reusable by every later headless smoke (Phases 2, 7, 8)"
  - "smoke/smoke_01_bootstrap.py: headless proof Parts A-D (direct import + QtNotAvailableError, findPlugins/plugin_load loader path, SMOKE-ENV record, cmd.load path probes) with '=== SMOKE-01 PASS/FAIL ===' verdict marker"
  - "windows-env-versions.md: committed one-time record of the Windows conda env (Python 3.9.13, PyQt5 5.12.9/5.12.3, PyMOL 2.5.0, numpy 1.25.2) + probe answers — closes STACK.md LOW-confidence flag and OQ4/OQ7"
  - "Two verified headless-runtime discoveries: __file__ points at pymol/__init__.py inside -cq scripts; PluginInfo.loaded stays False on the clean Qt-unavailable load path"
affects: [01-08, 01-09, phase-2-headless-engine, phase-7-checkpoints, phase-8-demos]

# Tech tracking
tech-stack:
  added: []   # stdlib only in the smoke scripts; Windows env already shipped PyQt5/numpy with PyMOL
  patterns:
    - "Headless verdict by printed marker only: '=== SMOKE-01 PASS ===' grepped by the runner (exit codes cannot carry verdicts through cmd.exe; sys.exit swallowed by tee|tail pipeline)"
    - "Self-bootstrapping smoke: mirrors winpath conversion locally, never imports aamatch.paths (bootstrap order); anchors repo root from sys.argv with cwd fallback — NEVER __file__"
    - "Record-only probes: diagnostic questions (path acceptance) print answers but never gate the PASS marker"
    - "Loader-contract testing headless: assert info.load() verdict / info.module, not the loaded property"

key-files:
  created:
    - smoke/smoke_01_bootstrap.py
    - smoke/run_smoke.sh
    - .planning/phases/01-bootstrap-pure-foundation/windows-env-versions.md
  modified: []

key-decisions:
  - "No staging step: repo lives on /mnt/c = C:\\Users\\nglok\\Desktop\\WORKDIR\\molmdl\\AA-match, so the runner cds to the repo root and PyMOL consumes the script + package in place (user-confirmed 2026-09-05)"
  - "Recipe frozen with -cq ONLY; -k would set options.plugins=0 and kill plugin loading entirely (invocation.py:481-483)"
  - "Repo-root anchor: sys.argv script path first, os.getcwd() fallback; __file__ is UNUSABLE inside -cq scripts (points at pymol/__init__.py — probe-verified 2026-09-06)"
  - "Part D probes are record-only (to_windows_path already outputs the proven backslash form), so probe failures cannot block Phase 1"
  - "Smoke asserts load success, not menu presence — menu registration is not assertable headless (HAVE_QT=False) and belongs to the 01-09 [HUMAN] checkpoint"

patterns-established:
  - "run_smoke.sh contract: 'bash smoke/run_smoke.sh <script>' → tee to /tmp/smoke_out.txt → tail -60 → grep PASS marker; nonzero runner exit == missing/FAIL marker"
  - "SMOKE-ENV <key>: <value> one-line print convention for env records; every print stays on ONE line for greppability"
  - "3.6 syntax floor gate: python3.6 -m py_compile before any ~60s Windows launch (a syntax error wastes a PyMOL boot)"

# Metrics
duration: 10 min
completed: 2026-09-06
---

# Phase 1 Plan 7: Headless Toolchain Proof Summary

**Headless WSL→Windows PyMOL pipeline proven end-to-end: aamatch loads via direct import AND the real findPlugins/plugin_load path under real PyMOL 2.5.0 (marker PASS, exit 0), Windows env recorded (Python 3.9.13 / PyQt5 5.12.9 / numpy 1.25.2), cmd.load accepts forward-slash and space paths**

## Performance

- **Duration:** 10 min
- **Started:** 2026-09-05T16:25:31Z
- **Completed:** 2026-09-05T16:35:53Z
- **Tasks:** 3
- **Files modified:** 3 (all created)

## Accomplishments

- Phase-1 success criterion 3 proven: `bash smoke/run_smoke.sh smoke/smoke_01_bootstrap.py` under real Windows PyMOL 2.5.0 ends with `=== SMOKE-01 PASS ===`, runner exit 0
- **Part A** (direct import): `import aamatch` → 0.1.0; direct `__init_plugin__(None)` raises exactly `QtNotAvailableError` headless — the loader's clean-catch contract verified
- **Part B** (real loader path): `startup.__path__.append(repo_root)` + `plugin_load('aamatch')` (auto-`initialize(-2)`) → registered, module imported as `pmg_tk.startup.aamatch`, `load()` returns True on the Qt-warning path
- **Part C**: one-time Windows env record transcribed into committed `windows-env-versions.md` — closes STACK.md's LOW-confidence "Windows env Python/Qt exact versions" flag
- **Part D** (record-only): `cmd.load` accepts BOTH the forward-slash form AND the backslash-with-spaces form (n=1 atom each) — pure-foundation OQ4/OQ7 answered
- The frozen recipe (`cd repo root → timeout 120 cmd.exe run-conda-pymol.bat -cq → marker grep`) is now a repo script every later headless smoke reuses

## Task Commits

Each task was committed atomically:

1. **Task 1: Write smoke/smoke_01_bootstrap.py (Parts A-D)** - `0ca2645` (feat)
2. **Task 2: Write smoke/run_smoke.sh (frozen recipe wrapper)** - `b6f5bda` (feat)
3. **Task 3: Run smoke, record env versions + probe results** - `a7855d4` (feat; includes two smoke-script fixes from the first failing run — see Deviations)

## Files Created/Modified

- `smoke/smoke_01_bootstrap.py` - headless proof Parts A-D + `=== SMOKE-01 PASS/FAIL ===` verdict marker (167 lines, python3.6-compatible)
- `smoke/run_smoke.sh` - frozen toolchain recipe: cd to repo root + `timeout 120 cmd.exe /c "C:\src\run-conda-pymol.bat -cq ..."` + tee/tail + PASS-marker grep
- `.planning/phases/01-bootstrap-pure-foundation/windows-env-versions.md` - committed env record (verbatim SMOKE-ENV table), OQ4/OQ7 answers, and the two headless-runtime discoveries

## Decisions Made

- Followed the plan's pre-made decisions: no staging step (repo is Windows-visible at `C:\Users\nglok\Desktop\WORKDIR\molmdl\AA-match`); `-cq` only, never `-k`; self-bootstrapping smoke (no `aamatch.paths` import — mirrors winpath locally); Part D record-only; assert load success not menu presence
- Anchor choice inside the smoke: `sys.argv` script-path first, `os.getcwd()` fallback — forced by the `__file__` discovery (see Deviations 1)
- Loader-success assertion uses `info.load()`'s return value — forced by the `loaded`-property discovery (see Deviations 2)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] `__file__` inside a `-cq` script points at `pymol/__init__.py`, not the script**

- **Found during:** Task 3 (first headless run — Part B failed with `CmdException('no such plugin')`)
- **Issue:** The plan's sketch anchored the repo root via the v1-era guard `_HERE = dirname(abspath(__file__)) if '__file__' in dir() else os.getcwd()`. A headless probe (readable installed loader source + probe script) proved `__file__` EXISTS in `-cq` scripts but equals `...\site-packages\pymol\__init__.py` — so `_ROOT` resolved to `site-packages`, Part A only passed because PyMOL puts the cwd (repo root) on `sys.path`, and Part B appended the WRONG dir to `startup.__path__` (the scan never saw `aamatch/`). Side effect: the Part-D fixture was written into the conda env's `site-packages\tmp\` — removed same day (recorded in windows-env-versions.md)
- **Fix:** Replaced the anchor with `_find_repo_root()`: match a `sys.argv` entry ending in the script name (absolute or cwd-relative), else fall back to `os.getcwd()` (the frozen runner `cd`s to the repo root and PyMOL inherits that cwd — probe-proven). Added a `SMOKE-ENV root:` print so the anchor is always visible in the record
- **Files modified:** smoke/smoke_01_bootstrap.py
- **Verification:** Second run: root anchor correct, Part B registered/module/name PASS (still `loaded` FAIL → Deviation 2), third run full PASS
- **Committed in:** a7855d4

**2. [Rule 1 - Bug] `PluginInfo.loaded` stays `False` on the clean headless Qt-unavailable load path**

- **Found during:** Task 3 (second headless run — `loader loaded FAIL` despite `Plugin 'aamatch' only available with PyQt GUI.` + registered/module/name PASS)
- **Issue:** The plan (and research §1.3) asserted `info.loaded` is `True` "even with the Qt warning (:287-300)". The installed 2.5.0 source shows `load()` catches `QtNotAvailableError`, prints the warning and falls through to `return True` — but `self.loadtime` is only assigned on the fully-successful branch, and `loaded` is the property `loadtime is not None`. So the property is `False` after a perfectly clean headless load; the original assertion could never pass with a correctly-working skeleton
- **Fix:** Assert the loader's own verdict instead: `check('loader loaded', bool(info and info.load()))` — `load()` returns True on the Qt-warning path, False only on a real failure. Discovery + rationale documented in windows-env-versions.md (load-bearing for all future headless smokes and the 01-09 checkpoint)
- **Files modified:** smoke/smoke_01_bootstrap.py
- **Verification:** Third run: all Part A/B checks PASS, `=== SMOKE-01 PASS ===`, runner exit 0
- **Committed in:** a7855d4

---

**Total deviations:** 2 auto-fixed (2 bugs — both in the new smoke script, zero skeleton regressions)
**Impact on plan:** Both fixes were required to make the smoke assert the verified loader behavior; the skeleton (01-01) needed no changes. No scope creep.

## Issues Encountered

- First headless run FAILed on Part B (root cause = Deviation 1); second run FAILed only on the `loaded` property (root cause = Deviation 2); third run PASS. Debugging was done against the installed loader source at `C:\Users\nglok\.conda\envs\chemtools-win10\Lib\site-packages\pymol\plugins\__init__.py` plus a one-off probe script (`tmp/probe_plugins.py`, uncommitted, git-ignored) — no Windows GUI needed
- Stray fixture from run 1 landed in the conda env's `site-packages\tmp\smoke fixtures\` — removed same day; re-runs write it to the checkout's git-ignored `tmp\smoke fixtures\`

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- The toolchain recipe is frozen and proven: Phases 2, 7, 8 headless smokes reuse `smoke/run_smoke.sh <script>` unchanged (only the script name varies)
- `windows-env-versions.md` gives later phases exact runtime facts (Python 3.9.13, PyQt5 5.12.9, PyMOL 2.5.0, numpy 1.25.2) and two headless-runtime caveats (`__file__` unusable; `loaded` property False on Qt-warning path)
- OQ4/OQ7 closed: `cmd.load` accepts forward-slash AND space paths — path handling can rely on `to_windows_path`'s backslash output with no additional quoting workarounds
- Remaining Phase-1 work: 01-08 (pymol/AGENTS.md + docs) and 01-09 ([HUMAN] Plugin-Manager install checkpoint — the menu-registration proof that is NOT assertable headless)

---
*Phase: 01-bootstrap-pure-foundation*
*Completed: 2026-09-06*
