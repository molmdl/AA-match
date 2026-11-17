---
phase: 09-help-docs-release-audit
plan: 07
subsystem: ui-help
tags: [help-panel, qdialog, qtextedit, help_text, single-home, smoke-11, smoke-99, modal-child]

# Dependency graph
requires:
  - phase: 09-help-docs-release-audit
    provides: 09-04 pure help_text.py (INTERACTION_LABELS/TIPS, MODE_CONTEXT, help_html/help_sections); 09-05 Cleanup confirmation guard; 09-01 Decision A (a-add)
  - phase: 08.3-drag-pivot
    provides: the shipped drag model wording carried inside help_text.help_html()
provides:
  - aamatch/setup_window.py -- btn_help in a window-level row below the tabs, _build_help_dialog() (construction-only child QDialog), _show_help() (the one thin-wrapper exec_), and the single-home repoint of the 3 UI dicts
  - smoke/smoke_11_window.py -- PART L, 10 additive construction-only checks (button, dialog, content, single-home labels)
affects: [09-11 ([HUMAN] help-open ritual), 09-10/09-12 (DOCS-02 drift audit)]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Modal-child split: construction-only IMPL (_build_help_dialog) + thin wrapper owning exec_ (_show_help) -- the smoke-99 law applied to the help panel"
    - "Window-level affordance below the tabs so both tabs inherit it; kept OUT of the pinned 7-button Setup row"
    - "Single-home reads: Qt widgets lazy-import the pure content module inside methods (module-identity law)"

key-files:
  created: []
  modified:
    - aamatch/setup_window.py
    - smoke/smoke_11_window.py

key-decisions:
  - "Help placement = 09-RESEARCH-help-ui.md SS3.2 Option A: one button in a window-level row under the tabs (both tabs inherit it)"
  - "Dialog is a modal CHILD QDialog (parent=self) built from help_text.help_html() in a read-only QTextEdit + OK; 520x600 v1 size; WindowStaysOnTopHint"
  - "exec_() exists ONLY in the thin wrapper _show_help; every smoke drives _build_help_dialog and never opens the modal"
  - "The 3 UI string dicts were deleted from SetupWindow; all widgets read help_text directly (byte-identical, behavior-preserving)"

patterns-established:
  - "_build_help_dialog() returns the built QDialog; _show_help() is one line self._build_help_dialog().exec_()"

# Metrics
duration: ~25 min
completed: 2026-11-18
---

# Phase 9 Plan 07: Setup-window Help Panel Summary

**Wired the HELP-01 panel into the setup window: a window-level Help button opens a modal child QDialog rendering `help_text.help_html()` in a read-only QTextEdit, while the 7 interaction labels, 7 tips, and 3 mode strings were re-homed from `SetupWindow` class dicts to the pure `aamatch/help_text.py` single home — all headless-proven by SMOKE-11 PART L (construction only, never `exec_`).**

## Performance

- **Duration:** ~25 min
- **Started:** 2026-11-18 (session, UTC 2026-11-17T~21:05Z)
- **Completed:** 2026-11-18T21:29Z
- **Tasks:** 3/3
- **Files modified:** 2

## Accomplishments

- **Single-home law completed (Task 1).** Deleted `SetupWindow._INTERACTION_LABELS`, `_INTERACTION_TIPS`, `_MODE_CONTEXT` (3 class attributes, 46 lines) and repointed the only 3 read sites to `help_text` via lazy in-method sibling imports. Diff: `1 file changed, 13 insertions(+), 46 deletions(-)` — net −33 lines. Zero widget-text change (strings byte-identical to the 09-04 pins).
- **Help row + dialog (Task 2).** A right-aligned `btn_help` row sits at WINDOW level immediately below `top.addWidget(self.tabs)`, so both the Setup and Game-status tabs inherit the affordance. It is deliberately outside the 7-button Setup row, whose inventory/order SMOKE-11 PART B pins.
- **Modal-child split (Task 2).** `_build_help_dialog()` constructs the `QDialog(self)` (title "AA-match Help", 520x600, `WindowStaysOnTopHint`, one read-only `QTextEdit` with `help_text.help_html()`, right-aligned OK → `dlg.accept()`); `_show_help()` is the single `exec_()` owner.
- **Headless proof (Task 3).** New additive SMOKE-11 PART L: 107 inserted lines, zero deletions, 10 check rows + 1 exception-fallback site; no existing part edited.

## Surface Map (`aamatch/setup_window.py`)

| Line | Symbol | Role |
|---|---|---|
| 252 | `help_row = QtWidgets.QHBoxLayout()` | stretched window-level row below the tabs |
| 254 | `self.btn_help = QtWidgets.QPushButton('Help', self)` | the Help button (tooltip set at 255-258) |
| 273 | `self.btn_help.clicked.connect(self._show_help)` | wiring beside the other button connections |
| 277-313 | `def _build_help_dialog(self)` | construction-only child QDialog (`help_html` read at 305) |
| 315-322 | `def _show_help(self)` | thin wrapper; the ONLY `exec_()` (322) |
| 536 | `help_text.MODE_CONTEXT[...]` | `_on_mode_toggled` live-label read |
| 556-557 | `help_text.INTERACTION_LABELS/TIPS[...]` | `_build_interactions` label/tooltip reads |
| 448-450 | dated comment | where the 3 dicts used to live |

`grep -n "_INTERACTION_LABELS\|_INTERACTION_TIPS\|_MODE_CONTEXT" aamatch/setup_window.py` → **zero matches**.
`grep -n "btn_help" aamatch/game_window.py` → **zero matches** (no naming collision; 09-RESEARCH SS7.12).

## SMOKE-11 PART L (additive rows)

- **L1 (2):** `btn_help` exists, text `'Help'`, non-empty tooltip.
- **L2 (6):** `_build_help_dialog()` → `QDialog`; `parentWidget() is win`; min 520x600; exactly one read-only `QTextEdit`; rendered `toHtml()` carries `'How to play'`, `'Hydrogen bond'`, `'Salt bridge'`, `'shift+left-drag'`, `'Tips'`; exactly one `'OK'` button.
- **L3 (2):** live checkbox labels == the canonical 7 in order AND == `help_text.INTERACTION_LABELS` values read through the live widgets (single-home proof end-to-end).
- Comment row records `_show_help` as `[HUMAN]`-only (offscreen `exec_` blocks — smoke-99); it is never smoke-driven.

## Verification Receipts

- `python3.6 -m py_compile aamatch/*.py` → **clean**.
- `python3.6 -m unittest discover -s tests` → **Ran 1006 tests — OK** (all pure pins byte-true; no pure-layer change).
- `bash smoke/run_smoke.sh smoke/smoke_11_window.py 240` → `=== SMOKE-11 PASS ===` (PART L rows all PASS).
- `bash smoke/run_smoke.sh smoke/smoke_09_qt_probe.py 120` → `=== PROBE PASS (platform=offscreen) ===`, `=== SMOKE-09 PASS ===`.
- `bash smoke/run_smoke.sh smoke/smoke_16_tab.py 240` → `=== SMOKE-16 PASS ===` (A 36 + B 23 + C 14 + D 10 + E 18 + F 12 + G 24 = 137 checks, 0 failures).
- `grep -n "exec_" aamatch/setup_window.py` → exactly **one call site** (line 322, inside `_show_help`); the remaining hits are docstring citations (15, 23, 284, 316, 318).

## Task Commits

Each task was committed atomically:

1. **Task 1: re-home the three dicts (single-home law)** — `e2ed272` (feat)
2. **Task 2: Help row + `_build_help_dialog` + `_show_help`** — `4d93c54` (feat)
3. **Task 3: SMOKE-11 additive help-surface part + battery** — `b51e4f8` (test)

**Plan metadata:** docs(09-07) commit (this SUMMARY + STATE).

## Files Created/Modified

- `aamatch/setup_window.py` — 3 UI dicts removed; 3 read sites repointed; help row, dialog impl, thin wrapper added (1097 → 1128 lines).
- `smoke/smoke_11_window.py` — PART L appended (1317 → 1424 lines; +107 insertions, 0 deletions).

## Decisions Made

- **Option A placement confirmed as implemented:** Help is a window-level row under the tabs, not a Setup-page button, so neither tab can hide the affordance and the pinned 7-button inventory stays true.
- **Construction/exec split is the contract:** `_build_help_dialog()` is the whole assertable surface; `_show_help()` is one line and is reserved for the 09-11 `[HUMAN]` ritual.
- **The re-home is behavior-preserving:** no widget string changed; `test_help_text.py`'s verbatim pins remain the single source of truth.

## Deviations from Plan

### Plan-text correction

**1. [Rule 1 - plan content-fragment casing] SMOKE L2 asserts `'shift+left-drag'`, not `'Shift+left-drag'`**

- **Found during:** Task 3 (SMOKE-11 PART L)
- **Issue:** the plan listed the pinned fragment as `'Shift+left-drag'` (capital S), but the authored canonical line that `help_html()` renders is lowercase — `'Drag the selected amino acid into place: shift+left-drag moves it…'` (`help_text.py:177-179`). The capital-S spelling lives only in `SELECTED_GESTURE_HINT`, which is NOT part of `help_sections()`/`help_html()`.
- **Fix:** the smoke asserts the actual rendered/pinned byte string `'shift+left-drag'` and documents the reason inline at the check site. Product code and pure pins untouched.
- **Files modified:** `smoke/smoke_11_window.py` only.
- **Verification:** SMOKE-11 PART L2 content row PASS (`missing=[]`).
- **Committed in:** `b51e4f8` (Task 3 commit)

---

**Total deviations:** 1 plan-text correction (no product-code deviation, no scope creep).
**Impact on plan:** the check tests exactly the content the pure module actually ships; the alternative would have forced a false FAIL or an unauthorized edit to the 09-04 pins.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- **09-11 `[HUMAN]` half is the only remaining HELP-01 step:** open the dialog from both tabs in a real Windows PyMOL session (click Help → panel renders → OK closes). Everything except the modal open is machine-proven here.
- **09-08** can import `SELECTED_GESTURE_HINT` as planned; no coupling to this plan beyond the shared pure module.
- **DOCS-02 audit** can now compare both the pure pins and the live dialog wiring; the re-home removed the last duplicate string home in the Qt tier.

---

*Phase: 09-help-docs-release-audit*
*Completed: 2026-11-18*
