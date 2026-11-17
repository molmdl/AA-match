---
phase: 09-help-docs-release-audit
plan: 04
subsystem: ui-help
tags: [help-content, pure-module, pymol, drag-gestures, done-semantics, PURE_MODULES, WSL-pins]

# Dependency graph
requires:
  - phase: 09-help-docs-release-audit
    provides: 09-RESEARCH-help-ui.md §4 content-sourcing map + §5 tier placement; 09-01 Decision A (a-add Cleanup confirmation) + Decision B (b-drop, 09-06)
  - phase: 08.3-drag-pivot
    provides: the shipped drag model (shift+left move, ctrl+shift+left depth, shift+right rotate; keyboard direction keys deleted)
provides:
  - aamatch/help_text.py -- PURE canonical home for the 7 interaction labels+tips, the 3 mode-context strings, the 3-gesture drag hint, a 7-section help_sections() builder, and a fragment-only help_html() builder
  - PURE_MODULES 19 -> 20 (help_text gated by Gates A/B/D)
  - tests/test_help_text.py -- 31 byte-verbatim WSL pins (the DOCS-02 audit surface)
affects: [09-07 (Setup-tab Help button + dialog consumes help_text.help_html), 09-08 (wizard prompt imports SELECTED_GESTURE_HINT), 09-10/09-12 (DOCS-02 drift audit now has a mechanical pin surface)]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Per-surface pure content module: canonical user-facing strings live in a pure module and are WSL-pinned before any Qt/cmd wiring (status_text.py/setup_form.py precedent)"
    - "Re-home-then-repoint: dicts are copied byte-identically into the pure home now; the Qt widget repoint in 09-07 is behavior-preserving"
    - "Atomic new-pure-module registration: file creation + PURE_MODULES edit in ONE commit, so no red-on-main window exists"

key-files:
  created:
    - aamatch/help_text.py
    - tests/test_help_text.py
  modified:
    - tests/test_purity.py
    - tests/test_wizard_source.py

key-decisions:
  - "09-01 Decision A = a-add: the Buttons help bullet reads 'Cleanup model removes every game-generated object from the scene, after asking for confirmation.' (the a-accept wording is DEAD)"
  - "SELECTED_GESTURE_HINT is ASCII-only and worded to the shipped drag model, with zero arrow/wasd tokens (Phase-8.3 supersession law)"
  - "Help states Done = closing the board: no record, no endgame screen; Done is explicitly not Give Up (quick-004)"
  - "The O1 tip follows the recorded phase_9_help_recommendation (5.5 A salt alone is not an H-bond; 4.0 A + 140 deg H-bond thresholds, docs/DETECTION_THRESHOLDS.md row 1)"

patterns-established:
  - "help_sections() returns [(title, [plain-text line, ...]), ...] -- plain data in, plain data out; help_html() is the only HTML surface and stays a fragment"

# Metrics
duration: ~12 min
completed: 2026-11-18
---

# Phase 9 Plan 04: Canonical Pure Help Content Summary

**Created `aamatch/help_text.py` as the PURE single home for all Phase-9 help content — the 7 interaction labels/tips and 3 mode strings re-homed byte-identically from `setup_window.py`, a new ASCII three-gesture drag hint, a 7-section `help_sections()` builder, and a fragment-only `help_html()` — registered as PURE_MODULES entry 20 and pinned by 31 new WSL tests, with the suite green at 1004/1004.**

## Performance

- **Duration:** ~12 min
- **Started:** 2026-11-18 (session)
- **Completed:** 2026-11-18T21:08Z
- **Tasks:** 2/2
- **Files modified:** 4 (2 created, 2 modified)

## Accomplishments

- `aamatch/help_text.py` (PURE, stdlib + `.setup_state` only):
  - `INTERACTION_LABELS` / `INTERACTION_TIPS` / `MODE_CONTEXT` copied byte-identically from `setup_window.py:386-394`, `:397-415`, `:418-425` — the single home for the 09-07 widget repoint.
  - `SELECTED_GESTURE_HINT` = "Shift+left-drag moves it; shift+right-drag rotates it; ctrl+shift+left-drag changes its depth." — ASCII, no arrow/wasd tokens, matching the shipped `cmd.button` map (`wizard.py:335-337`).
  - `help_sections()` — seven sections in fixed order: How to play, Interaction types, Scoring and Confirm, Interaction modes, Buttons, Saving and loading, Tips. Every line sourced from the research §4 canonical rows and cited in comments at the point of use.
  - `help_html()` — one escaped fragment (`<h2>` + `<ul>/<li>`), no `<html>`/`<body>` wrapper.
- `PURE_MODULES` extended 19 -> 20 in the SAME commit; the new name is also pinned in the quick-001 registration list. `tests/test_wizard_source.py` partition docstring arithmetic refreshed (28/19 -> 29/20; roster stays 8).
- `tests/test_help_text.py` — 31 pins covering dict coverage/byte-verbatim wording, gesture exactness + ASCII + no-keyboard-token + clip safety, section order/content, Done/destructive truth, the O1 tip, and HTML fragment/escape laws.
- Full WSL suite: **1004/1004 green** (973 prior + 31 new); `py_compile aamatch/*.py` clean under python3.6.

## Module Map

| Constant / function | Purpose | Consumers (planned) |
|---|---|---|
| `INTERACTION_LABELS` | enum -> display label (7) | 09-07 widgets |
| `INTERACTION_TIPS` | enum -> one-sentence help (7) | 09-07 widgets/dialog |
| `MODE_CONTEXT` | mode -> context sentence (3) | 09-07 mode label |
| `SELECTED_GESTURE_HINT` | the three shipped drag gestures | 09-08 wizard prompt |
| `help_sections()` | `[(title, lines)]`, 7 sections | 09-07 dialog |
| `help_html()` | escaped rich-text fragment | 09-07 dialog |

## Decisions Made

- **09-01 Decision A branch taken (a-add):** the Buttons section carries "Cleanup model removes every game-generated object from the scene, after asking for confirmation." The a-accept wording is not present anywhere.
- Gesture hint is ASCII and drag-model-only per the 08.3-03/08.3-16 supersession (all keyboard movement keys deleted).
- Help never promises an endgame summary on Done; Done is worded as closing the board and explicitly "not Give Up" (quick-004).
- O1 tip content and numbers transcribed from the recorded debug recommendation + approved H-bond row (4.0 A / ≥140 deg; 5.5 A salt alone insufficient).

## Task Commits

Each task was committed atomically:

1. **Task 1: author help_text.py + PURE_MODULES registration** — `9f7b590` (feat)
2. **Task 2: pin help content verbatim** — `4f3a5fc` (test)

**Plan metadata:** `docs(09-04)` (this SUMMARY + STATE).

## Files Created/Modified

- `aamatch/help_text.py` — new PURE canonical help content module (303 lines added in Task 1 incl. registry/doc edits).
- `tests/test_help_text.py` — new 31-test WSL battery (261 lines).
- `tests/test_purity.py` — PURE_MODULES 19 -> 20 + registration-list pin.
- `tests/test_wizard_source.py` — partition docstring arithmetic 28/19 -> 29/20.

## Deviations from Plan

None - plan executed exactly as written. (The inline quick-001 registration list in `tests/test_purity.py` was extended alongside `PURE_MODULES`; the plan's registration intent, and the file was already in Task 1's file set.)

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- **09-07 (Help button + dialog):** import `help_text.help_html()` / `help_sections()` from the Qt tier (lazy relative sibling import per the module-identity law) and repoint `_INTERACTION_LABELS` / `_INTERACTION_TIPS` / `_MODE_CONTEXT` at the pure dicts — the strings are byte-identical, so the repoint is behavior-preserving.
- **09-08 (wizard prompt reword):** import `SELECTED_GESTURE_HINT`; it is ASCII and short enough for the 255-char overlay clip (probe pinned).
- DOCS-02/criterion-3 audit can now diff user-facing help strings against `tests/test_help_text.py` mechanically.

---

*Phase: 09-help-docs-release-audit*
*Completed: 2026-11-18*
