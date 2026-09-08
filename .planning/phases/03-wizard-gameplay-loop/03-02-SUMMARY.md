---
phase: 03-wizard-gameplay-loop
plan: 02
subsystem: pure-logic
tags: [wizard, panel, prompt, text-rendering, pymol-wizard-cpp-contract, tdd]

# Dependency graph
requires:
  - phase: 03-wizard-gameplay-loop (plan 03-01)
    provides: wizard_core movement constants (NUDGE_STEP, ROTATE_BUTTON_STEP_DEG) -- single home, imported by wizard_text
  - phase: 02-headless-game-engine
    provides: engine.confirm plain-data triple (records, score, formed), game_state SCORE-01 fail-closed semantics, setup_state INTERACTION_TYPES canonical order
provides:
  - "aamatch/wizard_text.py: required_summary, panel_entries, prompt_lines, result_lines, _clip (PURE, gated #15)"
  - "THE pinned panel contract: always-3-element [kind, text, code] entries (kinds 0/1/2), 255-char ASCII clip, cmd.get_wizard() button codes, canonical cmd.set_wizard() Done"
  - "pinned text-only result-rendering shapes: 'Formed: (none)', 'Nothing formed (score 0.00)', 'N/M required interactions formed (score x.xx)'"
affects: [03-03 GameWizard panel/prompt wiring, 03-04 SMOKE-07 panel asserts, 03-06/03-07 human UAT]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "pure builders are PLAIN-DATA in/out: plain-data state dict -> text; never import cmd, never touch PyMOL (GameWizard assembles the state dict it hands in)"
    - "button codes are module-identity-safe BY CONSTRUCTION: only cmd.set_wizard() / cmd.get_wizard().method(...) may appear -- no module name, dodging aamatch vs pmg_tk.startup.aamatch (AGENTS.md gate 5)"
    - "overflow policy = _clip to 255 (WordType[256] panel cap): clip, never crash; shared by panel/prompt/result so both views show identical text"

key-files:
  created:
    - aamatch/wizard_text.py
    - tests/test_wizard_text.py
  modified:
    - tests/test_purity.py

key-decisions:
  - "PINNED result shapes: 'Formed: (none)' when no types formed; 'Nothing formed (score 0.00)' single line for empty 'any' mode; 'Missing:' line omitted when nothing missing"
  - "prompt composition order: status line first (click instruction / 'Selected: slot <id> (<object>). Move/rotate it, then Confirm.'), result lines VERBATIM, 'ERROR'-prefixed line appended LAST (measurement.py:262-263 shape)"
  - "panel build order: header ('Molecule <id> (pos/total)'), required summary, result lines (when set), ERROR line (when set), blank, movement header (embeds NUDGE_STEP via %g), 6 nudges + Toward ligand + Rotate 90 deg, blank, Confirm, Reset to Grid, Done"
  - "nudge_cam button code step vector pinned: Left (-1,0,0) Right (1,0,0) Up (0,1,0) Down (0,-1,0) In (0,0,-1) Out (0,0,1) -- camera-frame steps consumed by 03-03's movement layer"
  - "required_summary renders items IN GIVEN ORDER (payload carries canonical order already; builder never re-sorts) -- pinned by a reversed-order test"

patterns-established:
  - "RED battery pins mechanical C-parser facts (3-element entries, kinds, 255 cap, PParse-at-click codes) BEFORE the cmd tier wires them -- the panel contract never depends on a live PyMOL run"

# Metrics
duration: ~55 min
completed: 2026-09-08
---

# Phase 3 Plan 02: Pure Wizard Text Builders Summary

**Pure panel/prompt/result text builders pinned RED-first -- the entire Wizard.cpp panel contract (3-element entries, 255-char cap, click-time PParse codes, canonical Done) plus text-only SCORE-01 result rendering -- gated as PURE_MODULES #15**

## Performance

- **Duration:** ~55 min
- **Started:** 2026-09-08T19:30Z
- **Completed:** 2026-09-08T20:24Z
- **Tasks:** 2 (RED battery; GREEN implementation + PURE_MODULES registration)
- **Files modified:** 3 (2 created, 1 modified)

## Accomplishments

- `aamatch/wizard_text.py` (240 lines): four pure builders + `_clip`, module-level imports ONLY `NUDGE_STEP, ROTATE_BUTTON_STEP_DEG` from `.wizard_core` (single home never re-transcribed), zero pymol/Qt/numpy anywhere, fail-closed ValueError refusals mirroring game_state.score
- `tests/test_wizard_text.py` (399 lines): 41 tests -- the full panel contract battery (3-element list / kind {0,1,2} / entry[1] str / ASCII / 255-cap / exactly-one canonical Done / cmd.get_wizard() regex on every other button / no module name in any code / exact button inventory + exact codes / labels exactly once), prompt composition (instruction-first, verbatim result inclusion, ERROR-last), text-only result rendering (SCORE-01 + no-geometry-words assert), and the `_clip` helper contract
- Registered in `tests/test_purity.py` PURE_MODULES (= 15): Gates A/B/D now scan the module mechanically
- WSL suite 549 -> 590 tests, fully green; `python3.6 -m py_compile aamatch/*.py` clean

## Task Commits

Each task was committed atomically (TDD cycle):

1. **Task 1: RED — failing test battery** — `28cd678` (test: add failing tests for wizard text builders; RED proof = ImportError on `from aamatch import wizard_text`)
2. **Task 2: GREEN — implement wizard_text.py** — `fa7d6ab` (feat: implement pure wizard text builders; 41/41 tests green; includes the 2-decimal regex pin fix)
3. **Task 2: REGISTER in PURE_MODULES** — `0b1cac9` (test: register wizard_text in PURE_MODULES; full suite 590 green)

## Files Created/Modified

- `aamatch/wizard_text.py` — PURE text half of the Phase-3 wizard: required_summary, panel_entries, prompt_lines, result_lines, _clip; docstring carries every binding Wizard.cpp fact (3-element entries, 255-cap, PParse-at-click, ASCII, text-only results)
- `tests/test_wizard_text.py` — RED-first unit battery (41 tests) pinning the panel contract, prompt composition, result rendering, and the clip behavior, including a 400-char error-string clip proof in BOTH panel and prompt
- `tests/test_purity.py` — PURE_MODULES += 'wizard_text' with Phase-3 (03-02) comment annotation

## Decisions Made

- **Result-rendering shapes PINNED** where the plan offered a choice: 'Formed: (none)' when a list-mode confirm forms nothing; 'Nothing formed (score 0.00)' as the single line for an empty 'any'-mode result; 'Missing:' omitted entirely when nothing is missing (rule: absence of the line == nothing missing, both 'list' and 'any').
- **Prompt error placement LAST** (measurement.py:262-263 precedent): an 'ERROR'-prefixed line is appended after status + result lines in prompt_lines, and placed after the result lines as a text entry in panel_entries.
- **Button step vectors pinned** in the exact code strings: nudge_cam(-1/1, 0/±1, 0) for Left/Right/Up/Down, (0,0,∓1) for In/Out (camera frame), rotate_view(90) built from ROTATE_BUTTON_STEP_DEG.
- **Movement header derives 'A per press' text from NUDGE_STEP via %g** -- if the constant changes, every user-facing movement label follows (no re-transcribed literal).
- **required_summary / result_lines mirror game_state.score's fail-closed contract**: unknown mode, list mode with missing/empty items -> ValueError naming the cause (the panel can never silently render a malformed required payload).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] 2-decimal score assert regex anchored mid-line**
- **Found during:** Task 2 (GREEN run, first failure)
- **Issue:** my own RED pin `r'score \d+\.\d\d$'` could never match -- the rendered line ends with a closing paren ('... (score 0.50)'), not after the digits
- **Fix:** anchored the regex after the closing paren (`r'score \d+\.\d\d\)$'`) -- the PINNED requirement (exactly-2-decimal rendering) is unchanged; only the anchor was wrong
- **Files modified:** tests/test_wizard_text.py
- **Verification:** full 41/41 battery green
- **Committed in:** `fa7d6ab` (part of the GREEN commit)

---

**Total deviations:** 1 auto-fixed (Rule 1 - Bug, test-side only)
**Impact on plan:** None -- the pinned behavior was never weakened; GREEN implementation landed on first run otherwise.

## Issues Encountered

None beyond the deviation above. RED failed with the expected ImportError; GREEN passed 41/41 after the regex fix; registration kept the full suite green.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- **03-03 GameWizard** can wire `get_panel()`/`get_prompt()` as: assemble the plain-data state dict ({'molecule_id', 'molecule_pos', 'molecule_total', 'required' from payload, 'selected', 'result' from engine.confirm, 'error'}) and delegate to wizard_text.panel_entries / wizard_text.prompt_lines -- exactly the key_link shapes pinned here.
- **03-04 SMOKE-07** panel asserts (3-element entries, valid kinds, 'Click an amino acid' prompt, result text in panel/prompt) are pre-proven at the unit level here; the smoke only adds the live wiring.
- **03-06/03-07 UAT:** all text a human will see (header, required summary, movement labels, result lines, error lines) exists and is pinned -- UAT reviews the same strings the unit tests assert.
- Note (carried from 03-01): tests/test_purity.py still lacks a registration-pin TestCase for the Phase-3 additions (02-08/02-10 added pin classes; 03-01 and 03-02 added only comment annotations) -- a pin test remains an optional later-plan addition.

---
*Phase: 03-wizard-gameplay-loop*
*Completed: 2026-09-08*
