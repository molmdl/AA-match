---
phase: 09-help-docs-release-audit
plan: 08
subsystem: ui-help
tags: [wizard-text, prompt-line, drag-model, single-home, help_text, purity-gate, smoke-07, smoke-16]

# Dependency graph
requires:
  - phase: 09-help-docs-release-audit
    provides: 09-04 pure help_text.py SELECTED_GESTURE_HINT (single-home gesture sentence, ASCII)
  - phase: 08.3-drag-movement-pivot
    provides: the shipped drag model (shift+left move / ctrl+shift+left depth / shift+right rotate)
provides:
  - aamatch/wizard_text.py -- selected-prompt tail composed from help_text.SELECTED_GESTURE_HINT
  - tests/test_wizard_text.py -- gesture-presence + legacy-absence + 255-char/ASCII pins
affects: [09-10/09-12 (DOCS-02 in-game help wording audit), 09-11 ([HUMAN] help ritual if wording is amended)]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Pure -> pure module-level sibling import (from . import help_text) -- both modules are PURE_MODULES"
    - "Single-home consumption: the gesture sentence lives once (help_text) and the prompt composes it with %s"

key-files:
  created: []
  modified:
    - aamatch/wizard_text.py
    - aamatch/status_text.py
    - tests/test_wizard_text.py
    - tests/test_help_text.py

key-decisions:
  - "The selected prompt now teaches the three shipped gestures at the moment of selection, discharging the recorded prompt_tail deferral"
  - "The gesture sentence is never restated: wizard_text imports help_text.SELECTED_GESTURE_HINT"
  - "The legacy-token supersession pin assembles its token from source fragments so the stale-wording audit grep stays literally clean"

patterns-established:
  - "Prompt tail = 'Selected: slot %s (%s). <gesture hint> Then Confirm.' (overline-safe: 142 chars at realistic inputs, ASCII)"

# Metrics
duration: ~20 min
completed: 2026-11-18
---

# Phase 9 Plan 08: Selected-Prompt Drag-Model Reword Summary

**Reworded the in-viewer selected prompt from the pre-pivot generic "Move/rotate it, then Confirm." to the three shipped drag gestures — composed from the pure `help_text.SELECTED_GESTURE_HINT` single home — closing the recorded 08.3 `prompt_tail` deferral with two-sided pins and a clean stale-wording grep.**

## Performance

- **Duration:** ~20 min
- **Started:** 2026-11-18 (session)
- **Completed:** 2026-11-18
- **Tasks:** 2/2
- **Files modified:** 4

## Old / New prompt string pair

**Old** (`wizard_text.py:_status_line`):

```python
return ('Selected: slot %s (%s). Move/rotate it, then Confirm.'
        % (selected.get('slot_id'), selected.get('object')))
```

**New**:

```python
return ('Selected: slot %s (%s). %s Then Confirm.'
        % (selected.get('slot_id'), selected.get('object'),
           help_text.SELECTED_GESTURE_HINT))
```

Rendered with realistic state (pure-module probe, no PyMOL needed):

```text
'Selected: slot r0c2 (_aam_aa003). Shift+left-drag moves it; shift+right-drag rotates it; ctrl+shift+left-drag changes its depth. Then Confirm.'
len=142  ascii=True
```

142 chars — comfortably under the 255-char `WordType[256]` panel clip — and pure ASCII (overlay-font law).

## Accomplishments

- **Task 1 — reword + single home.** `aamatch/wizard_text.py` now does `from . import help_text` (pure→pure; both are registered `PURE_MODULES`, so Gate A/B scan the import) and composes the selected tail from `help_text.SELECTED_GESTURE_HINT`. The module docstring's old "imports NOTHING" claim was corrected to name the one pure sibling import (prose staleness created by this change).
- **Task 1 — all prose sites updated.** `prompt_lines` docstring: "Move/rotate guidance" → "drag-gesture guidance"; `status_text.selected_line` docstring: old tail quote → `'<gesture hint> Then Confirm.'`. No code, constant, or string changed in `status_text.py`.
- **Task 2 — two-sided pin.** Replaced `test_selected_shows_move_guidance_and_slot_identity` with `test_selected_names_drag_gestures_and_slot_identity` (gestures present, `Then Confirm.` present, legacy token absent, slot identity `r0c2` / `_aam_aa003` retained) and added `test_selected_prompt_within_clip_and_ascii` (every selected-state prompt line `len <= 255` and ASCII-only).
- **Fifth stale site resolved (Rule-1).** `tests/test_help_text.py:test_prompt_plus_hint_fits_the_overlay_clip` still built a prompt containing "Move/rotate it, then Confirm."; it now composes the real new line and asserts `len < 255`.

## Four (+1) touched sites

| # | Site | Change |
|---|---|---|
| 1 | `aamatch/wizard_text.py:_status_line` | prompt string → `%s Then Confirm.` with `help_text.SELECTED_GESTURE_HINT` |
| 2 | `aamatch/wizard_text.py:prompt_lines` docstring | "Move/rotate guidance" → "drag-gesture guidance" |
| 3 | `aamatch/status_text.py:selected_line` docstring | old tail quote → `'<gesture hint> Then Confirm.'` |
| 4 | `tests/test_wizard_text.py` old pin | replaced with gesture + legacy-absence pins |
| 5 | `tests/test_help_text.py` clip probe | (plan predicted a possible fifth site) re-shaped to the composed line |

`grep -rn "Move/rotate" aamatch/ tests/ smoke/ --include=*.py` → **ZERO HITS**.

## SMOKE-07 prompt-line receipt (headless, no screenshots)

```text
SMOKE-07 prompt carries the click instruction     PASS prompt[0]='Click an amino acid to select it.'
```

SMOKE-07 exercises the prompt-rendering path; its receipt covers the no-selection branch (unchanged by this plan) while the selected branch is pinned in WSL by the new tests above (composed line quoted in the Old/New section). Final marker: `=== SMOKE-07 PASS ===`.

## Test-count delta

- Before: **1006** tests.
- After: **1007** tests — net **+1** (replaced 1 pin, added 1 clip/ASCII test), matching the plan's expectation.
- `python3.6 -m unittest discover -s tests` → **Ran 1007 tests — OK**.

## Task Commits

Each task was committed atomically:

1. **Task 1: reword the selected-prompt tail via the canonical hint** — `4400885` (feat) — `aamatch/wizard_text.py`, `aamatch/status_text.py`, `tests/test_help_text.py`
2. **Task 2: replace the pin test + verify the continuity laws** — `61fc662` (test) — `tests/test_wizard_text.py`

**Plan metadata:** docs(09-08) commit (this SUMMARY + STATE).

## Verification Receipts

- `python3.6 -m py_compile aamatch/*.py` → **PYC-OK**.
- `python3.6 -m unittest discover -s tests -v` → **1007/1007 — OK** (purity gates included; `wizard_text`'s new import is Gate-A/B-scanned).
- `bash smoke/run_smoke.sh smoke/smoke_07_wizard_loop.py 240` → `=== SMOKE-07 PASS ===`.
- `bash smoke/run_smoke.sh smoke/smoke_16_tab.py 240` → `=== SMOKE-16 PASS ===` (A 36 + B 23 + C 14 + D 10 + E 18 + F 12 + G 24 = 137 checks, 0 failures).
- `grep -rn "Move/rotate" aamatch/ tests/ smoke/ --include=*.py` → **zero hits**.

## Files Created/Modified

- `aamatch/wizard_text.py` — module-level `from . import help_text`, gesture-composed selected tail, corrected module + `prompt_lines` docstrings.
- `aamatch/status_text.py` — `selected_line` docstring only.
- `tests/test_wizard_text.py` — gesture/legacy/clip pins; legacy token fragment constant.
- `tests/test_help_text.py` — clip probe re-shaped to the composed line.

## Decisions Made

- **The prompt tail is the gesture hint plus "Then Confirm."** — the selected prompt now names the movement input exactly when the player needs it; no extra sentence was invented.
- **Single home is structural, not stylistic.** `help_text.SELECTED_GESTURE_HINT` is the one place the gesture wording lives; a future 09-11 human wording amendment lands there and flows into the prompt automatically.
- **Supersession pin keeps its teeth without tripping the audit grep.** The legacy token is assembled at runtime (`'Move' '/rotate'`) so `assertNotIn` still proves the old tail absent while the literal-token grep is clean.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Prose staleness] Resolved the fifth `Move/rotate` site in `tests/test_help_text.py`**

- **Found during:** Task 1 (live-tree grep, exactly as the plan's verification anticipated)
- **Issue:** beyond the four known sites, `test_prompt_plus_hint_fits_the_overlay_clip` constructed a prompt carrying the old "Move/rotate it, then Confirm." wording.
- **Fix:** the probe now composes the real new line (`SELECTED_GESTURE_HINT` + "Then Confirm.") and asserts `len < 255`.
- **Files modified:** `tests/test_help_text.py`.
- **Verification:** `tests.test_help_text` all green; repo-wide grep zero.
- **Committed in:** `4400885` (Task 1 commit)

**2. [Rule 1 - Gate consistency] Legacy token in the supersession pin assembled from fragments**

- **Found during:** Task 2 (the required `assertNotIn` literal would itself be the only remaining grep hit)
- **Issue:** the plan requires both `assertNotIn('Move/rotate', text)` and a zero-hit repo-wide grep; the literal in the test violates the latter.
- **Fix:** `_LEGACY_MOVE_TAIL = 'Move' '/rotate'` (runtime-equal, source-clean) is asserted absent, with an inline rationale.
- **Files modified:** `tests/test_wizard_text.py`.
- **Verification:** assertion passes; `grep -rn "Move/rotate" ...` zero.
- **Committed in:** `61fc662` (Task 2 commit)

---

**Total deviations:** 2 auto-fixed (both Rule 1; prose/gate consistency only)
**Impact on plan:** No behavior or scope change; both fixes are required for the plan's own verification gates to hold simultaneously.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- **The recorded 08.3 `prompt_tail` deferral is discharged**: the prompt teaches the drag model, pinned from both sides (gestures present, legacy absent, clip/ASCII safe).
- **09-10/09-12 (DOCS-02 in-game help audit)** can now cite the prompt as drag-model-correct; the only remaining help surface is the 09-11 `[HUMAN]` dialog-open ritual.
- If the 09-11 human ritual amends the gesture wording, the edit lands in `help_text.py` only — this plan's compositional shape guarantees the prompt follows.

---

*Phase: 09-help-docs-release-audit*
*Completed: 2026-11-18*
