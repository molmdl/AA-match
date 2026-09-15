---
phase: 04-qt-setup-window
plan: 05
subsystem: qt-window
tags: [pymol, pyqt5, qt, modeless-dialog, singleton, setup-window, smoke-test, plugin-menu]

# Dependency graph
requires:
  - phase: 04-qt-setup-window/04-01
    provides: T1b offscreen-Qt verdict (QT_QPA_PLATFORM=offscreen widget construction PASSES) — SMOKE-11 therefore INCLUDES PART B (construct/reuse/close-reopen + button-drive asserts)
  - phase: 03-wizard-gameplay-loop/03-05
    provides: gamestart.start_game one-call seam + the deliberate-contract-replacement precedent (03-05-SUMMARY.md:103-109) + the SMOKE-08 entry-path smoke now re-pointed at the seam
  - phase: 01-bootstrap-pure-foundation/01-09
    provides: Gate A2 zero-module-level-import discipline in aamatch/__init__.py + the metadata-block-frozen loader contract
provides:
  - aamatch/setup_window.py — Qt-tier modeless SetupWindow shell: module-level pymol.Qt imports (legal+required), module-scope _window singleton, open_window() create-if-None + show/raise_/activateWindow returning the dialog; 7 buttons in spec order with tooltips, unconnected; deliberately NO closeEvent
  - run_plugin_gui rewired: lazy `from . import setup_window` + `return setup_window.open_window()` (metadata block byte-identical, __version__ 0.1.0, Gate A2 green)
  - tests/test_package_skeleton.py — replaced AST contract (test_run_plugin_gui_opens_setup_window_lazily), 03-05 precedent invoked deliberately
  - tests/test_wizard_source.py — SCANNED_MODULES += 'setup_window.py' per the recorded growth protocol
  - smoke/smoke_08_starter.py — re-pointed to aamatch.gamestart.start_game() directly; === SMOKE-08 PASS === with all 31 checks preserved
  - smoke/smoke_11_window.py — === SMOKE-11 PASS === (9 checks): T1a import-proof (PART A) + T1b construct/reuse/close-reopen/7-button-labels (PART B, probe verdict PASS) + Gate A2 echo (PART C)
affects: [04-07 (form fields into the placeholder), 04-09..04-13 (the handler plans — each connects its own button on this shell; 04-11 adds the module-level cmd import), 05+ (window stays open during gameplay), 07 (import replay over the same shell)]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Qt-tier module pattern: module-level `from pymol.Qt import QtWidgets, QtCore, QtGui` legal+REQUIRED in the Qt module (class creation needs QtWidgets), while the module stays forever out of PURE_MODULES and out of WSL test imports (AST source gates only)"
    - "Modeless modeless-singleton open: module-scope `_window = None` + create-if-None + show/raise_/activateWindow + return-the-dialog (v1 PA-__init__:3-5/:141-153 trio adapted verbatim; no closeEvent anywhere = SETUP-01's hide-and-survive mechanism)"
    - "Menu-rewire contract evolution: replace the AST seam test deliberately (03-05 precedent) + grow SCANNED_MODULES one line + re-point the entry-path smoke to the seam — never a workaround"

key-files:
  created: [aamatch/setup_window.py, smoke/smoke_11_window.py]
  modified: [aamatch/__init__.py, tests/test_package_skeleton.py, tests/test_wizard_source.py, smoke/smoke_08_starter.py]

key-decisions:
  - "Probe verdict used: 'Probe verdict: PASS (platform=offscreen) first attempt succeeded' (04-01-SUMMARY.md:45) — SMOKE-11 includes PART B (T1b); QT_QPA_PLATFORM=offscreen is set BEFORE any pymol.Qt import in the smoke, the exact 04-01 recipe"
  - "NO closeEvent override, deliberately: default close hides; the module-level singleton keeps the object alive; re-open is reuse-and-raise — that IS SETUP-01 (v1 repo-wide grep: zero closeEvent overrides recorded in the module docstring)"
  - "Buttons created but NOT connected in the shell: each handler plan (04-09..04-13) connects its own button — no dead stub handlers"
  - "Module-level `from pymol import cmd` NOT added (plan Decision 17): only 04-11's cleanup handler needs cmd; it lands there"
  - "__version__ stays 0.1.0; the metadata block + NOTE comment are byte-identical (diff-scoped: only run_plugin_gui's body+docstring changed)"

patterns-established:
  - "The Plugins-menu function is now the Qt window opener: smokes drive the game-entry SEAM directly (start_game) and drive the WINDOW through open_window()'s returned dialog — two distinct assertion handles, one per surface"
  - "T1b smoke recipe for Qt-tier modules: QT_QPA_PLATFORM=offscreen at script top -> repo-root anchor -> import the Qt module -> QApplication.instance() or QApplication([...]) -> construct/assert processEvents -> ZERO modals"

# Metrics
duration: 17min
completed: 2026-09-15
---

# Phase 4 Plan 05: Setup Window Shell Summary

**The modeless Qt setup window exists and is headlessly proven end-to-end: `aamatch/setup_window.py` (module-scope singleton + create-if-None show/raise_/activateWindow `open_window()` + the 7-button spec-ordered row, unconnected, no closeEvent) is what Plugins → AA-match now opens via a lazy `from . import setup_window`; SMOKE-11 PASS (T1a import-proof + T1b construct/reuse/close-reopen-same-instance/7-exact-labels under the offscreen probe verdict) proves the shell in real headless PyMOL, SMOKE-08 PASS (31 checks) confirms the re-pointed game seam is untouched, and all three deliberately-broken recorded contracts (skeleton AST seam, SCANNED_MODULES, SMOKE-08 call sites) were replaced per the 03-05 precedent. 632/632 WSL tests green, Gate A2 preserved.**

## Performance

- **Duration:** ~17 min
- **Started:** 2026-09-15T18:22:36Z
- **Completed:** 2026-09-15T18:39:05Z
- **Tasks:** 3/3
- **Files modified:** 6 (2 created, 4 modified)

## Accomplishments

- **aamatch/setup_window.py (141 lines) — the SETUP-01 keystone shell:** Qt-tier layer declaration in the module docstring (never PURE_MODULES, never imported by WSL tests); module-level `from pymol.Qt import QtWidgets, QtCore, QtGui` (shim only — no `from PyQt5` anywhere); `_window = None` at module scope (GC-prevention receipt); `open_window()` = create-if-None + show/raise_/activateWindow + `return _window`; `SetupWindow(QtWidgets.QDialog)` with NO parent, `setWindowTitle('AA-match Setup')`, `setMinimumWidth(420)`; top QVBoxLayout = form-area placeholder QWidget (own QVBoxLayout; form lands in 04-07) + stretch + the QHBoxLayout 7-button row created IN SPEC ORDER (`btn_reset`..`btn_start`, labels exactly 'Reset', 'Randomize', 'Save Setup', 'Load Setup', 'Generate and export', 'Cleanup model', 'Start', spec-meaning tooltips) — created but NOT connected; NO other methods; NO closeEvent (comment cites SETUP-01 + the v1 grep-zero receipt).
- **run_plugin_gui rewired, deliberately replacing its recorded contract (03-05 precedent):** `from . import setup_window` + `return setup_window.open_window()` — the metadata block/`# Version:`/`Citation-Required:` lines + NOTE comment are byte-identical (git-diff-scoped to run_plugin_gui only), `__version__` stays `0.1.0`, `__init_plugin__` untouched, Gate A2 (`test_no_module_level_imports`) green.
- **Three deliberate test evolutions (P9/P10), zero workarounds:** (1) `tests/test_package_skeleton.py` — `test_run_plugin_gui_opens_setup_window_lazily` REPLACES the 03-05 gamestart-seam test (same AST mechanics: lazy relative ImportFrom named 'setup_window' inside the body + a Return whose value is a Call `setup_window.open_window()`; no-print assert + `test_entry_points_exist` kept; docstring cites 03-05-SUMMARY.md:103-109); (2) `tests/test_wizard_source.py` — `SCANNED_MODULES` grows `'setup_window.py'` per the recorded growth protocol, so the PLAY-04 no-helper-visuals AST gate + the zero-banned-token-mention pin now cover the new module; (3) `smoke/smoke_08_starter.py` — every `aamatch.run_plugin_gui()` call re-pointed to `aamatch.gamestart.start_game()` (from-import at top; header docstring updated) — **=== SMOKE-08 PASS === with all 31 checks intact** (starter state, restore-table spot check, both restart paths with instance markers, msm ORDER LAW, seed-42 determinism, exact teardown).
- **=== SMOKE-11 PASS === (9 checks)** in real headless PyMOL (`bash smoke/run_smoke.sh smoke/smoke_11_window.py 120`), QT_QPA_PLATFORM=offscreen set before any Qt import (the 04-01 recipe): PART A (always, T1a) — headless `import aamatch.setup_window` succeeds, `open_window` callable, `_window` starts None, source carries `from pymol.Qt import` and NOT `from PyQt5`; PART B (T1b — the cited probe verdict is PASS) — `open_window()` returns a `QtWidgets.QDialog`, the second call is the SAME instance, `close()` + re-open is STILL the same instance (the SETUP-01 hide-and-survive mechanism proven, not just asserted), all 7 buttons exist with the exact spec-order labels via `text()`, processEvents, zero modals; PART C (always) — Gate A2 shape sanity echoed inside PyMOL's interpreter (zero column-0 import/from lines in `aamatch/__init__.py`).
- **Regression sweep green:** 632/632 WSL tests (`python3.6 -m unittest discover -s tests`), `python3.6 -m py_compile aamatch/*.py` clean (Gate D covers the new module), SMOKE-08 PASS.

## Task Commits

Each task was committed atomically:

1. **Task 1: setup_window.py shell — singleton, open_window, minimal dialog + button row** — `f4baac0` (feat)
2. **Task 2: Rewire __init__ + replace the AST contract + grow SCANNED_MODULES + re-point SMOKE-08** — `a8fb800` (feat)
3. **Task 3: SMOKE-11 shell parts + full gates** — `ae03049` (test)

**Plan metadata:** (see docs commit below)

## Files Created/Modified

- `aamatch/setup_window.py` (created, 141 lines) — Qt tier (never PURE_MODULES): the modeless shell; form fields land in 04-07 and the button handlers in 04-09..04-13 on this exact skeleton.
- `aamatch/__init__.py` (modified, diff-scoped to run_plugin_gui) — the menu entry now opens the setup window lazily; returns the dialog (assertion handle).
- `tests/test_package_skeleton.py` (modified) — replaced AST seam contract + updated header contract item 5.
- `tests/test_wizard_source.py` (modified, one growth line + comment) — `SCANNED_MODULES = ['wizard.py', 'gamestart.py', 'setup_window.py']`.
- `smoke/smoke_08_starter.py` (modified) — re-pointed to `aamatch.gamestart.start_game()`; header docstring + 3 call sites + 2 label/comment touches; all 31 check conditions byte-identical.
- `smoke/smoke_11_window.py` (created, 176 lines) — 9-check window-shell smoke with the A/B/C part structure; verdict marker `=== SMOKE-11 PASS ===`.

## Decisions Made

- **SMOKE-11 ran WITH widget-construction parts (PART B)** because the binding probe verdict read: `Probe verdict: PASS (platform=offscreen) first attempt succeeded` (.planning/phases/04-qt-setup-window/04-01-SUMMARY.md:45). No degradation to T1a+[HUMAN] was needed; the smoke sets `QT_QPA_PLATFORM='offscreen'` at its top before any `pymol.Qt` import, the 04-01 first-attempt recipe.
- **closeEvent stays absent by construction** — the default close hides and the singleton keeps the object; SMOKE-11's close()+re-open-same-instance check gives the SETUP-01 mechanism mechanical regression teeth.
- **The smoke proves the window path through `open_window()` directly** (run_plugin_gui is a documented one-line pass-through of the same call); asserting the menu function's AST shape stays with the WSL skeleton test — same split as 03-05 (AST in WSL, execution in smoke).
- **SMOKE-08 label touches were label-only** (`run_plugin_gui returns a GameWizard` → `start_game returns a GameWizard`, PART-1 header comment) — the 31 check conditions and their asserts are byte-identical, per the plan's "ALL 31 checks preserved".

## Deviations from Plan

None — plan executed exactly as written. The three test evolutions are the plan's own recorded P9/P10 items (deliberate replacements), not deviations.

## Issues Encountered

None. The SMOKE-11 run printed benign offscreen-platform Qt warnings (`QFontDatabase: Cannot find font directory`, `This plugin does not support propagateSizeHints()/raise()`) — cosmetic offscreen noise of the same family recorded in 04-01; `raise_()` is a no-op offscreen but the call shape is what the singleton+reuse asserts verify.

## Authentication Gates

None.

## User Setup Required

None — no external service configuration required.

## Next Phase Readiness

- **04-07 (form):** the `form_area` placeholder QWidget with its own QVBoxLayout is the stable layout slot for the 7-field form; `collect_state`/`apply_state` + `_loading` guard attach there (04-RESEARCH borrowed pattern 2).
- **04-09..04-13 (handlers):** the 7 buttons exist unconnected as `self.btn_reset`..`self.btn_start` — each handler plan connects its own button and imports its siblings lazily inside the handler (`from . import setup_state, gamestart, persistence, placement`). Module-level `from pymol import cmd` is 04-11's to add (plan Decision 17).
- **T2 [HUMAN] checkpoints remain for look/feel/modal behavior only** (modeless interactivity, minimize/re-open feel, double-menu-fire raise on a real display) — the mechanical halves are SMOKE-11's.
- **T1b smoke recipe recorded for every later Qt plan:** env var at script top → anchor → import → QApplication reuse-or-create → processEvents → ZERO modals.
- **Blockers:** none carried forward by this plan.

---
*Phase: 04-qt-setup-window*
*Completed: 2026-09-15*
