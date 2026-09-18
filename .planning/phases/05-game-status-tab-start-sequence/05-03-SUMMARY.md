---
phase: 05-game-status-tab-start-sequence
plan: 03
subsystem: gameplay-feedback
tags: [pymol, hint-color, wizard_core, pure-module, tdd, constants]

# Dependency graph
requires:
  - phase: 03-wizard-interaction
    provides: aamatch/wizard_core.py (zero-imports pure home with HIGHLIGHT_COLOR = 'green' and the exact-constants battery in tests/test_wizard_core.py)
provides:
  - wizard_core.HINT_COLOR = 'orange' — the single-home hint color for GameWizard._hint_impl (plan 05-08), pinned by test
affects: [05-08 wizard hint mechanics, 05-11 phase checkpoint (color revisit = one-constant edit + one test update)]

# Tech tracking
tech-stack:
  added: []
  patterns: [single-home pure constant with provenance comment + exact-constants test pin, so any silent color change is a test failure]

key-files:
  created: []
  modified: [aamatch/wizard_core.py, tests/test_wizard_core.py]

key-decisions:
  - "HINT_COLOR = 'orange' lives in the PURE zero-imports module wizard_core.py beside HIGHLIGHT_COLOR (a string constant needs no import); 'orange' is a registered PyMOL 2.5.0 named color (Color.cpp:1039, live-probed index 13), is the v1 PA-game:12 hint precedent, and is distinct from the 'green' selection highlight and default element coloring"
  - "A human color revisit at the Phase-5 checkpoint is a one-constant edit + one test update, never a hunt — the pin test makes silent change impossible"
  - "Alternatives verified present on this build (magenta 8, salmon 9, pink 48) recorded in 05-RESEARCH-hint.md but intentionally NOT built now"

patterns-established:
  - "Micro-plan constant-first TDD: land the color constant as its own RED -> GREEN cycle BEFORE the recolor code exists (keeps plan 05-08 purely about mechanics)"

# Metrics
duration: 2min
completed: 2026-09-18
---

# Phase 05 Plan 03: HINT_COLOR Constant Pin Summary

**Hint color lands as ONE tested constant — `wizard_core.HINT_COLOR = 'orange'` beside `HIGHLIGHT_COLOR`, provenance-commented and pinned in the exact-constants battery, ahead of the 05-08 hint recolor mechanics.**

## Performance

- **Duration:** ~2 min
- **Started:** 2026-09-18T18:27:41Z
- **Completed:** 2026-09-18T18:29:44Z
- **Tasks:** 2/2 (RED, GREEN)
- **Files modified:** 2

## Tasks

| Task | Name | Commit | Files |
| ---- | ---- | ------ | ----- |
| 1 | RED: the HINT_COLOR pin | 92fdd98 | tests/test_wizard_core.py |
| 2 | GREEN: the constant | cd7b015 | aamatch/wizard_core.py |

## Accomplishments

- `HINT_COLOR = 'orange'` exists in the single pure zero-imports home (wizard_core.py, beside HIGHLIGHT_COLOR at former line 53), with a provenance comment carrying Color.cpp:1039 + live-probe index 13 + the v1 PA-game:12 hint precedent + the distinct-from-green rule.
- The exact-constants battery (`TestMovementAndFeedbackConstants`) now pins `HINT_COLOR == 'orange'`, pins it as a plain `str` (directly consumable by `cmd.color`), and pins hint_color != highlight_color — any silent color change fails the suite.
- RED proven for the right reason: AttributeError naming `HINT_COLOR` (2 errors across the two new assertions) before the constant existed.

## Verification

- `python3.6 -m py_compile aamatch/*.py` — clean.
- `python3.6 -m unittest tests.test_wizard_core -v` — 19/19 OK.
- `python3.6 -m unittest discover -s tests -v` — **689/689 OK** (34.2 s), including `tests/test_purity.py` gates (wizard_core stays zero-imports; the only `^import` grep hit in the module is docstring prose, not a statement; diff confirmed +8 lines, comment + constant only).
- No smoke required by this plan (pure-layer constant only; no PyMOL call site exists yet — 05-08 introduces `cmd.color(wizard_core.HINT_COLOR, ...)`).

## Deviations from Plan

None — plan executed exactly as written.

## Authentication Gates

None.

## Decisions Made

1. **HINT_COLOR's single home is the pure module.** `wizard_core.py` is a PURE_MODULES member under the zero-stubs AST gate; a string constant needs no import (05-RESEARCH-hint.md C gate-impact: "a string constant needs nothing"), so the constant lives there beside HIGHLIGHT_COLOR rather than in the cmd-tier `wizard.py`.
2. **Pin includes type + distinctness, not just the exact string.** Beyond `== 'orange'`, the battery pins `isinstance(str)` (cmd.color consumes the name directly) and `HINT_COLOR != HIGHLIGHT_COLOR` (the two feedback colors must never collide — the clarified PLAY-01 green semantic vs. the hint orange).
3. **Revisit path is explicitly narrow.** Per the plan's success criterion, a human color change at checkpoint 05-11 is a one-constant edit here plus a one-line test update; the research records only the verified alternates (magenta 8, salmon 9, pink 48) and none are built now.

## Next Phase Readiness

- No blockers. Plan 05-08 (`_hint_impl`) can consume `wizard_core.HINT_COLOR` with zero further constant work.
- Human-facing note for the 05-11 checkpoint: if a different hint color is preferred, change the single constant in wizard_core.py and the single assertion in tests/test_wizard_core.py — no other site references the color.
