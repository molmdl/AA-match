---
phase: 05-game-status-tab-start-sequence
plan: 06
subsystem: qt-window
tags: [pymol, qt, tab-widget, countdown, timer, gametab, setup11]

# Dependency graph
requires:
  - phase: 04-qt-setup-window
    provides: modeless SetupWindow singleton + 7-button form (04-05..04-13), the T1b offscreen probe verdict (04-01), the smoke-99 zero-modals law (04-09)
  - phase: 05-game-status-tab-start-sequence
    provides: GameState.rebase_timer pure pause-freeze op (05-04); gamestart activate kwarg + activate_game GO home + _last_start (05-05); status_text module (05-01)
provides:
  - aamatch/game_window.py — the Qt-tier GameTab: read-only rolling info box + _log, timer label +
    1 Hz live-anchor tick with modal-pause rebase, required label, unconnected btn_hint,
    cancellable member-QTimer countdown (start_countdown/_countdown_tick/_begin_play/
    cancel_pending_start)
  - aamatch/setup_window.py restructured to a two-tab QTabWidget (Setup + Game status) with every
    pre-existing attribute intact
  - SMOKE-11 T1b PART I: tab structure, shell state, method-driven countdown/cancel/timer-label proofs
affects: [05-09 window start rework (drives start_countdown + cancels on cleanup),
          05-10 status surface (poll piggybacks on _on_tick, owns _last_status content),
          the hint plan (connects btn_hint)]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Cancellable countdown = reusable member QTimer stepping 3->2->1->GO (never a singleShot chain, P-2); every new start cancels pending first (self-healing)"
    - "One anchor rule: tick reads the LIVE GameState.timer_anchor each tick; modal-open pause rebase via rebase_timer freezes at the last shown second (P-4)"
    - "Wizard-free countdown window: _pending_wizard off the stack; only _begin_play (GO) calls activate_game (P-1)"
    - "QTabWidget re-wrap of an existing dialog: minimal churn — existing code lines kept, only the layout parent changed; asserts are parentage-blind"

key-files:
  created:
    - aamatch/game_window.py
  modified:
    - aamatch/setup_window.py
    - tests/test_wizard_source.py
    - smoke/smoke_11_window.py

key-decisions:
  - "btn_hint created with spec tooltip but NOT connected (the 04-05 shell law: the hint handler plan connects its own button)"
  - "Hint button row reserves its slot with a stretch so later phases' game-lifecycle rows never reflow the timer row (research OQ-1 later-add)"
  - "game_window.py docstrings avoid the banned-matrix tokens AND the literal shim-vendor import phrase — the zero-mention scan + the smoke's source sanity greps are enforced on every SCANNED_MODULES file"
  - "Modal-pause granularity documented at <= 1 s over-count (the 1 Hz rebase; research Q6 recommendation A)"

# Metrics
duration: 12 min
completed: 2026-09-18
---

# Phase 5 Plan 06: GameTab Shell & Two-Tab Window Summary

**Two-tab QTabWidget SetupWindow (Setup + Game status, every attribute preserved) with the NEW Qt-tier GameTab — read-only rolling info box, 1 Hz live-anchor tick with modal-pause rebase, cancellable member-QTimer 3-2-1-GO countdown, unconnected Hint button — proven headlessly by the new SMOKE-11 T1b PART I with all prior parts re-green.**

## Performance

- **Duration:** 12 min
- **Started:** 2026-09-18T19:39:58Z
- **Completed:** 2026-09-18T19:51:44Z
- **Tasks:** 3
- **Files modified:** 3 (1 created)

## Accomplishments

- `aamatch/game_window.py` (NEW, 257 lines, Qt tier — never PURE_MODULES, never WSL-imported; SCANNED_MODULES-covered): `GameTab(QtWidgets.QWidget)` with the pinned attribute names — `_info_log` (read-only QTextEdit), `_timer_label` ('0:00' initial), `_required_label` ('Required: -' initial), `btn_hint` (created unconnected), `_countdown_timer`/`_countdown_n`/`_pending_wizard`, `_timer`/`_last_shown_elapsed`. Layout: timer + required top row (timer OUTSIDE the info box, spec.md:37), the info box with stretch, the button row with a reserved stretch.
- Cancellable countdown (P-2): reusable member QTimer; `start_countdown` cancels any pending countdown FIRST (self-healing), logs 'Get ready...', arms n=3; `_countdown_tick` steps 3->2->1->GO; `cancel_pending_start` stops and clears the pending wizard — a cancelled countdown NEVER fires GO (no stale activation over deleted objects or the next game).
- Wizard-free countdown window (P-1): `start_countdown` only STORES the prepared wizard; `_begin_play` (GO) is the single point calling `gamestart.activate_game`, then a defensive stop + start of the 1 Hz `_timer`.
- Live-anchor tick with pause (P-4): `_on_tick` computes elapsed from the LIVE `GameState.timer_anchor` every tick (never a GUI-side copy); while `QApplication.activeModalWidget()` is not None it rebase-freezes the single anchor via `game_state.rebase_timer` and skips the label update (granularity <= 1 s, documented). `_format_mss` = v1's exact M:SS (minutes unbounded).
- `aamatch/setup_window.py` restructured: `setup_page` wraps the EXISTING form_area + stretch + 7-button row (code lines kept; only the layout parent changed), `self.tabs = QTabWidget` with 'Setup'/'Game status' tabs (spec.md:33 same window; spec.md:21 buttons stay on Setup), `self.game_tab = game_window.GameTab(self)` via lazy relative import inside `__init__` (module-identity law). Module/class docstrings updated; the stale 'NO SETUP-11 pieces' notes in `_on_start`/`_start_impl` corrected.
- `tests/test_wizard_source.py`: SCANNED_MODULES grows `'game_window.py'` (growth protocol, 03-05/04-05 precedent) — both AST scans now cover the new Qt module.
- SMOKE-11 T1b PART I (16 checks, inserted before the Gate-A2 echo; echo re-lettered I -> J): I1 two-tab structure + 7-button re-green; I2 shell state; I3 method-driven countdown (NO processEvents gap) landing 3/2/1/GO! each on its own line + GO pushed THAT wizard + float anchor + 1 Hz on; I4 '1:15' via anchor manipulation; I5 cancel drive (no GO, no stale activation); exact-scene restore. ALL prior parts (A..H) re-green unchanged.

## Task Commits

Each task was committed atomically:

1. **Task 1: game_window.py — the GameTab shell** - `cde2dc5` (feat)
2. **Task 2: two-tab SetupWindow + SCANNED_MODULES growth** - `b44bc1c` (feat)
3. **Task 3: SMOKE-11 tab + countdown + timer parts** - `80ae46f` (test)

**Plan metadata:** (docs commit below)

## Files Created/Modified

- `aamatch/game_window.py` — NEW Qt-tier module (the GameTab shell; `import time` + `from pymol.Qt import QtWidgets, QtCore` at module level; lazy sibling/cmd imports inside methods)
- `aamatch/setup_window.py` — QTabWidget restructure + docstring updates (no new module-level imports)
- `tests/test_wizard_source.py` — SCANNED_MODULES + 'game_window.py'
- `smoke/smoke_11_window.py` — new PART I before the Gate-A2 echo; echo re-lettered to PART J; header part list updated

## Decisions Made

- `cancel_pending_start` clears `_pending_wizard` UNCONDITIONALLY and guards only the timer `stop()` on `isActive()` — the plan text gated both; unconditional clearing is the safer semantics for an idempotent cancel (restore paths call it on an already-cancelled tab).
- `GameTab._format_mss` is a `@staticmethod` (pure formatting, no self needed) — the v1 format kept verbatim: `'%d:%02d' % (int(s) // 60, int(s) % 60)`.
- The no-game tick guard: `_compute_elapsed` returns 0.0 when the anchor is None, and the modal-pause branch's `engine.EngineError` catch lets the tick survive a mid-restart no-game window — documented P-6-adjacent hygiene (no boxes in tick paths, ever).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug / Gate-C tripwire] docstring prose triggered the plan's own grep verify**

- **Found during:** Task 1 verification
- **Issue:** the first draft's module docstring contained the literal shim-vendor import phrase (`from Py...`) as prose, and the plan's Task-1 verify greps for that token repo-file-wide expecting a count of 0 — the documented Gate-C warning (token greps fire on prose) hit exactly as the standing gates describe.
- **Fix:** rephrased the sentence to avoid the literal token ("Qt comes ONLY through the pymol.Qt wrapper shim -- the vendor binding is never imported directly"); the AST gates are the enforced mechanism and were unaffected.
- **Files modified:** `aamatch/game_window.py`
- **Commit:** `cde2dc5`

### Planned-scope additions (documented)

**2. [Rule 2 - Missing Critical] PART I restore stops the 1 Hz `_timer`**

- **Found during:** Task 3 authoring
- **Issue:** the plan's restore sequence (cancel + pop + cleanup) leaves the 1 Hz `_timer` ACTIVE from the I3 GO step; after `cleanup_game_objects`, a real pumped tick would call `_compute_elapsed` -> `engine._current_game()` and raise `EngineError` (no game live) inside a timer callback — a traceback mid-smoke (and the same late-fire hazard exists for later dialog close/pump events).
- **Fix:** `dlg.game_tab._timer.stop()` added to the restore block (commented: "defensive: no 1 Hz tick over the post-cleanup no-game state").
- **Files modified:** `smoke/smoke_11_window.py`
- **Commit:** `80ae46f`

## Authentication Gates

None.

## Verification Results

- `python3.6 -m py_compile aamatch/*.py` — OK (3.6 floor)
- `python3.6 -m unittest discover -s tests -v` — 753/753 OK (incl. tests/test_purity.py and the test_wizard_source.py scans now covering game_window.py; `grep -c 'from PyQt5'`/`'QMessageBox'` on game_window.py both 0)
- `bash smoke/run_smoke.sh smoke/smoke_11_window.py 120` — `=== SMOKE-11 PASS ===` (new PART I 16 checks + ALL prior parts + re-lettered PART J echo)
- `bash smoke/run_smoke.sh smoke/smoke_13_qt_timer_probe.py 120` — `=== SMOKE-13 PASS ===` (regression view of the Qt timer mechanics)
- `bash smoke/run_smoke.sh smoke/smoke_08_starter.py 120` — `=== SMOKE-08 PASS ===` (the default start path untouched by the window work)

## Issues Encountered

Only the Gate-C prose-tripwire fix (deviation 1). SMOKE-11 PART I passed on the first smoke run with all 16 checks green and zero regressions in prior parts.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- 05-09 (window start rework) can drive `_start_impl` down the deferred path: pop prior GameWizard -> `start_game(activate=False)` -> `tabs.setCurrentWidget(game_tab)` -> `game_tab.start_countdown(wiz)`; and `_on_cleanup` should call `game_tab.cancel_pending_start()` (P-2 is already armed in the tab).
- 05-10 (status surface) consumes the shell: the poll piggybacks on `_on_tick` (its modal-pause branch already skips), first level line + required label land in `_begin_play`, and `status_text` builders feed `_log`/`_required_label` (`_last_status` is plan 05-10's only new tab state).
- The hint plan connects `btn_hint` (the lore says the hint handler plan connects its own button — the 04-05 shell law).
- No blockers. T2 [HUMAN] watch items for the phase checkpoint: real-modal timer freeze (P-5 mechanism not headlessly provable), countdown look/feel, tab layout.

---
*Phase: 05-game-status-tab-start-sequence*
*Completed: 2026-09-18*
