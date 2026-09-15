---
phase: 04-qt-setup-window
plan: 01
subsystem: testing
tags: [pymol, pyqt5, qt, offscreen, headless, smoke, probe]

# Dependency graph
requires:
  - phase: 01-bootstrap-pure-foundation
    provides: run_smoke.sh headless Windows PyMOL harness, smoke header conventions, recorded conda env (PyMOL 2.5.0 / PyQt5 5.12.3 / Qt 5.12.9)
provides:
  - smoke/smoke_09_qt_probe.py — headless offscreen-Qt widget-construction probe
  - Definite research-Q1 verdict: offscreen widget construction WORKS → T1b tier (headless widget construction + round-trips + button drive-through) is AVAILABLE for plans 04-05..04-13
affects: [04-qt-setup-window (all later plans' verify tiers), 05+, 06+, 07+ (any Qt-tier headless verification)]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Offscreen-Qt probe ladder: QT_QPA_PLATFORM=offscreen set BEFORE the pymol.Qt import, default-platform fallback on any exception, both exception summaries recorded on double failure"
    - "QApplication reuse-or-create idiom (`QtWidgets.QApplication.instance() or QtWidgets.QApplication([...])`) — usable by every later T1b verify step in a `-cq` session"

key-files:
  created:
    - smoke/smoke_09_qt_probe.py
  modified: []

key-decisions:
  - "Research Q1 CLOSED: QT_QPA_PLATFORM=offscreen widget construction works in the exact Windows conda env — no default-platform fallback needed; later plans' T1b verify steps may construct dialogs, drive collect/apply round-trips, and click buttons headlessly"
  - "Probe verdict rests on CONSTRUCTION success + live-widget round-trip (QSpinBox/QCheckBox), not pixel visibility; visibility assert is soft (offscreen semantics may differ — here it passed anyway, no visible-assert line printed)"

patterns-established:
  - "Probe pattern: set os.environ['QT_QPA_PLATFORM']='offscreen' at the very top before `from pymol.Qt import QtWidgets, QtCore` (wrapper shim only); construct → show → processEvents; ZERO modals (PITFALL P5)"
  - "Dual marker family: research verdict (=== PROBE PASS (platform=...) ===) + harness verdict (=== SMOKE-09 PASS === as the FINAL line, run_smoke.sh grep contract)"

# Metrics
duration: 10min
completed: 2026-09-15
---

# Phase 4 Plan 01: Offscreen-Qt Widget-Construction Probe Summary

**Research Q1 CLOSED with a definite verdict: `QT_QPA_PLATFORM=offscreen` QApplication + QDialog construction, show/processEvents, and live-widget round-trips (QSpinBox/QCheckBox) all WORK headlessly in the Windows conda PyMOL 2.5.0 env (PyQt5 5.12.3 / Qt 5.12.9) — the T1b verify tier is available to plans 04-05..04-13.**

Probe verdict: PASS (platform=offscreen) first attempt succeeded — `=== PROBE PASS (platform=offscreen) ===` + `=== SMOKE-09 PASS ===` in run_smoke.sh output (12-14 of the probe block), no exception, no visible-assert failure, no PART B fallback needed.

## Performance

- **Duration:** ~10 min
- **Started:** 2026-09-15T04:18:31Z
- **Completed:** 2026-09-15T04:28:34Z
- **Tasks:** 2/2
- **Files modified:** 1 (created)

## Accomplishments
- Headless widget construction PROVEN under `QT_QPA_PLATFORM=offscreen` in the exact target env: QApplication (reuse-or-create), `QDialog()` with `setMinimumWidth(420)`, QVBoxLayout + QLabel + QPushButton, `show()`, `processEvents()`, `isVisible()` True — zero exceptions, no PART B fallback.
- Live object semantics proven, not just construction: QSpinBox `setRange(1, 10)`/`setValue(7)` reads back 7; QCheckBox `toggle()` sets `isChecked()`.
- Research Q1 (04-RESEARCH-qt-window-architecture.md §verification_tiers, §open_questions 1) is no longer UNVERIFIED; every later Phase-4 plan's `<verify>` may use T1b instead of degrading to T1a + [HUMAN].

## Task Commits

Each task was committed atomically:

1. **Task 1: Write the offscreen-Qt probe smoke script** — `5913bb2` (test)
2. **Task 2: Run the probe via run_smoke.sh and record the verdict** — no code change (verdict recorded here and in the plan-metadata commit)

**Plan metadata:** (see docs commit below)

## Files Created/Modified
- `smoke/smoke_09_qt_probe.py` — the offscreen→default probe ladder: env var set BEFORE the `pymol.Qt` import (wrapper shim only, never raw PyQt5); soft visibility assert; QSpinBox/QCheckBox round-trip; dual marker families (`=== PROBE PASS (platform=...) ===` / `=== PROBE FAIL ===` + trailing `=== SMOKE-09 PASS ===`); ZERO modals (PITFALL P5).

## Decisions Made
- **Verdict platform = offscreen (first attempt).** PART B (default platform) was never reached; the reuse-or-create QApplication idiom and the construct→show→processEvents→round-trip sequence are proven verbatim for later T1b steps.
- **Repo-root anchor intentionally omitted** in the probe: smoke_01's `sys.argv`/cwd anchor exists to support `aamatch` imports; this probe imports no repo modules, so the anchor would be dead code. Header conventions (one-line prints, marker verdict carrier, 3.6 syntax floor) otherwise followed. (Plan structure item 1 read as *conditional* on needing the root.)

## Deviations from Plan

None — plan executed exactly as written (the omitted repo-root anchor is recorded above as a decision consistent with the header-convention rationale, not a deviation).

## Issues Encountered

None. The run printed benign Qt font warnings (`QFontDatabase: Cannot find font directory .../Library/lib/fonts`; `This plugin does not support propagateSizeHints()`) — cosmetic, offscreen-platform noise; no impact on the verdict.

## User Setup Required

None — no external service configuration required.

## Next Phase Readiness
- **T1b AVAILABLE** for plans 04-05..04-13: dialog construction, `apply_state`/`collect_state` round-trips, and `btn.click()` drive-through may all be verified headlessly under `QT_QPA_PLATFORM=offscreen` using this exact QApplication reuse-or-create recipe. [HUMAN] T2 checkpoints remain for look/feel/modal-behaviour only (ROADMAP Phase-4 criteria are all [HUMAN]).
- Research §open_questions Q4 (default-platform show() semantics) is SUBSUMED — offscreen won; PART B was never exercised.
- Standing caveat for later T1b authors: keep ZERO modals in headless tests (PITFALL P5) — a modal hangs until the run_smoke.sh timeout backstop.

---
*Phase: 04-qt-setup-window*
*Completed: 2026-09-15*
