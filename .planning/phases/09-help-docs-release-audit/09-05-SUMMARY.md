---
phase: 09-help-docs-release-audit
plan: 05
subsystem: ui-warning-guard
tags: [cleanup-confirmation, destructive-action, QMessageBox, status_text, smoke-99, criterion-1, SMOKE-11, SMOKE-21]

# Dependency graph
requires:
  - phase: 09-help-docs-release-audit
    provides: 09-01 Decision A verdict "a-add" (human, verbatim) + the Consumers table routing 09-05 to BRANCH ADD only; 09-RESEARCH-help-ui.md §2d identifying Cleanup as the only uncovered destructive action
  - phase: 04-setup-tab
    provides: the original cancel-first _on_cleanup wrapper + modal-free _cleanup_now/_guard split (04-11 Decision 17)
provides:
  - aamatch/status_text.py -- CLEANUP_WARNING_TITLE/CLEANUP_WARNING_TEXT constants beside SKIP/GIVEUP (the only strings the Qt wrapper may show)
  - aamatch/setup_window.py -- guarded thin-wrapper _on_cleanup (empty-scene ask-free; Yes/No default No) with _cleanup_now/placement.cleanup_game_objects still modal-free
  - tests/test_status_text.py -- 2 byte-verbatim pins; status_text battery 96 -> 98, full suite 1004 -> 1006
affects: [09-07 (setup Help dialog wiring; criterion-1 warning story finalization), 09-10/09-12 (release audit: Cleanup now carries a confirm per Decision A), any future smoke that must drive the Cleanup button (use the endgame-modal entry-gate precedent, game_window.py:1344-1349)]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Destructive-action guard at the thin-wrapper layer only: pure wording constants + a lazy pre-check + QMessageBox.question(default No), while the driven impls stay modal-free (the smoke-99 law)"
    - "Empty-scene ask-free pre-check: count _aam_-prefixed objects BEFORE the modal, mirroring placement.py's prefix-only enumeration law (geometry.GAME_PREFIX)"
    - "Default-safe destructive dialogs: default button is No; only an explicit Yes proceeds"

key-files:
  created: []
  modified:
    - aamatch/status_text.py
    - aamatch/setup_window.py
    - tests/test_status_text.py

key-decisions:
  - "09-01 Decision A applied exactly as recorded: a-add (human's clicked answer verbatim: 'Add confirmation (Recommended)'); BRANCH ACCEPT was NOT executed (dead)"
  - "The confirmation lives ONLY in _on_cleanup (thin wrapper); _cleanup_now and placement.cleanup_game_objects remain modal-free so SMOKE-11 PART E and SMOKE-21 are untouched"
  - "Empty scene stays ask-free (pre-check on cmd.get_names('objects') + geometry.GAME_PREFIX); cancel-first countdown order preserved (pitfall P-2)"
  - "Default button is No (destructive default-safety); any non-Yes reply returns before cleanup"

patterns-established:
  - "Guarded wrapper template: cancel_pending_start() -> lazy prefix pre-check -> default-No question -> _guard(modal-free impl) -> after-info box"

# Metrics
duration: ~10 min
completed: 2026-11-18
---

# Phase 9 Plan 05: Cleanup Destructive-Action Guard Summary

**Setup-tab Cleanup now asks a default-No Yes/No question before deleting any `_aam_*` game object (09-01 Decision A = a-add), with the wording pinned byte-verbatim at the pure layer and the driven impls left modal-free**

## Performance

- **Duration:** ~10 min
- **Started:** 2026-11-18T05:05Z (approx.)
- **Completed:** 2026-11-18T05:16Z
- **Tasks:** 3/3
- **Files modified:** 3

## Verdict consumed (verbatim from 09-01-SUMMARY.md)

### Question A -- Cleanup model confirmation

### Verdict A: **a-add — ADD THE CONFIRMATION**

Human's verbatim answer (clicked): **"Add confirmation (Recommended)"**

**Branch taken: BRANCH ADD only.** BRANCH ACCEPT was not executed (recorded dead by 09-01).

## Accomplishments

- `aamatch/status_text.py:205-207` — `CLEANUP_WARNING_TITLE` / `CLEANUP_WARNING_TEXT` added directly below the untouched `SKIP_*`/`GIVEUP_*` constants (196-201), with a dated 09-05/09-01 Decision A comment.
- `aamatch/setup_window.py:907-938` — `_on_cleanup` became the guarded thin wrapper: `cancel_pending_start()` FIRST → lazy `from . import geometry` prefix pre-check over `cmd.get_names('objects')` → when any `_aam_*` object exists, lazy `from . import status_text` + `QMessageBox.question(self, TITLE, TEXT, Yes | No, No)` → non-Yes returns → existing `_guard(self._cleanup_now)` + after-info box unchanged.
- `aamatch/setup_window.py:890-905` — `_cleanup_now` byte-unchanged; `placement.cleanup_game_objects` untouched (modal-free boundary intact).
- `tests/test_status_text.py:414-421` — `test_cleanup_warning_title` + `test_cleanup_warning_text` byte-verbatim pins in `TestWarningConstants` (the class law: the Qt wrappers can show ONLY these strings).
- Skip/Give-Up constants byte-untouched; game_window.py's pre-existing Skip/Give-Up `QMessageBox.question` sites are the only ones there (no new boxes for Restart / mid-game Import / Start).

## Task Commits

Each logical unit was committed atomically (plan-specified messages):

1. **Task 1+2: constants + guarded wrapper** - `008700c` (feat)
   - `feat(09-05): guard Cleanup with a confirmation (09-01 Decision A)` — `aamatch/status_text.py` + `aamatch/setup_window.py`
2. **Task 1: byte-verbatim pins** - `8871463` (test)
   - `test(09-05): pin the cleanup warning constants` — `tests/test_status_text.py`

**Plan metadata:** (this docs commit, created immediately after this SUMMARY + STATE update)

_Note: the plan explicitly prescribed this feat+test pair; the constants and the wrapper share one feature commit because the guard is the feature, and the pins are the test commit._

## Files Created/Modified

- `aamatch/status_text.py` — CLEANUP_WARNING_TITLE/TEXT pure constants (`:205-207`).
- `aamatch/setup_window.py` — guarded `_on_cleanup` wrapper (`:907-938`; guard at `:925-937`, question at `:930`); docstring updated with the dated 09-01 Decision A line.
- `tests/test_status_text.py` — two byte-verbatim pins (`:414-421`).

## Battery Receipts

| Gate | Command | Result |
|------|---------|--------|
| Syntax floor | `python3.6 -m py_compile aamatch/*.py` | PYC-OK |
| WSL suite | `python3.6 -m unittest discover -s tests -v` | **1006/1006 OK** (before: 1004/1004; +2 = the two CLEANUP pins) |
| status_text battery | `python3.6 -m unittest tests.test_status_text -v` | **98/98 OK** (before: 96/96; +2) |
| SMOKE-11 (PART E drives `_cleanup_now` directly) | `bash smoke/run_smoke.sh smoke/smoke_11_window.py 240` | **`=== SMOKE-11 PASS ===`** (PART E cleanup deleted=20, baseline exact) |
| SMOKE-21 (cleanup isolation field test) | `bash smoke/run_smoke.sh smoke/smoke_21_demo_cleanup.py 180` | **`=== SMOKE-21 PASS ===`** (c: deleted=10, name set + atom counts restored, zero `_aam_`/AAM-segi leakage) |

## Verification Details

- `grep -n "QMessageBox.question" aamatch/setup_window.py` → exactly one new site (`:930`).
- `grep -n "GAME_PREFIX" aamatch/setup_window.py` → exactly one lazy-import use (`:927`).
- `git diff aefc091 -- aamatch/status_text.py` → **additions only**; the SKIP/GIVEUP block at `:193-201` has zero changed lines.
- `git diff --name-only aefc091` → only `aamatch/setup_window.py`, `aamatch/status_text.py`, `tests/test_status_text.py`; `game_window.py` byte-untouched.

## Decisions Made

- Applied the recorded human verdict exactly (a-add); no re-ask, no accept-branch fallback.
- Default button = **No**, and any non-Yes reply returns before `_cleanup_now` — destructive default-safety.
- Empty-scene pre-check uses the same `name.startswith(geometry.GAME_PREFIX)` law as `placement.py:504-505`; no modal fires on the 0-object no-op.

## Deviations from Plan

**Minor implementation note (no behavior change):** the plan action text said "lazy `from pymol import cmd` + `from . import geometry`". `setup_window.py:56` already imports `cmd` at MODULE level (documented as legal in the Qt tier, 04-11 Decision 17), so a second local import would be dead duplication. The wrapper uses the existing module-level `cmd` and only adds the genuinely lazy sibling import `from . import geometry`. The intended pre-check (`cmd.get_names('objects')` + `GAME_PREFIX`) is exactly as specified.

No Rule 1/2/3 auto-fixes were needed. No architectural (Rule 4) change.

## Issues Encountered

None.

## Authentication Gates

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Criterion 1's Cleanup clause is CLOSED per the human's recorded verdict, with the driven-impl boundary (smoke-99) proven intact by SMOKE-11 PART E + SMOKE-21.
- 09-06 remains: README banner Decision B = b-drop (delete exactly line 4).
- 09-07 (help-panel wiring) can cite these constants/behavior; no API surface was changed beyond additive constants and the wrapper guard.

---
*Phase: 09-help-docs-release-audit*
*Completed: 2026-11-18*
