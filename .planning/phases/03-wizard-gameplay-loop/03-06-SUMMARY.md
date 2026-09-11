---
phase: 03-wizard-gameplay-loop
plan: 06
subsystem: ui
tags: [pymol, wizard, gameplay-loop, human-checkpoint, camera-framing, color-restore]

# Dependency graph
requires:
  - phase: 03-wizard-gameplay-loop
    provides: plans 03-01..03-05 (wizard_core/wizard_text/wizard/gamestart + SMOKE-07/08 headless proofs)
provides:
  - Human-verified core gameplay loop (PLAY-01/02/03) on stock PyMOL
  - Recorded keyboard-delivery verdict + msm save/restore law (Phase-5 input decisions)
  - Camera start-composition law: zoom-to-frame + ligand-above-grid roll
  - Display-rebuild law for any future recolor code
  - Molecule-scoped Confirm/scoring guard (multi-molecule design gap closed)
affects: [03-07 human checkpoint, phase-3 verifier, phase-4 Qt setup window, phase-5 input/start sequence, gap-closure planning]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Display-rebuild law: any AA recolor/restore must rebuild the object's display lists (cmd.alter display-list staleness vs cmd.color redraw)"
    - "Start-view composition: zoom-to-frame('segi AAM') then camera-only roll so the ACTIVE ligand sits above the grid; nudge math re-reads get_view per press, no movement-side change needed"
    - "Molecule-scoped scoring: Confirm runs detection scoped to the current molecule (cross-molecule guard)"

key-files:
  created:
    - ".planning/phases/03-wizard-gameplay-loop/03-06-SUMMARY.md"
  modified:
    - "aamatch/gamestart.py"
    - "aamatch/wizard.py"
    - "aamatch/wizard_text.py"
    - "aamatch/placement.py"
    - "aamatch/engine.py"
    - "smoke/smoke_07_wizard_loop.py"
    - "smoke/smoke_08_starter.py"

key-decisions:
  - "Keyboard map recorded: LEFT/RIGHT + ',' '.' + q/w/e/d delivered; UP/DOWN dead BY DESIGN (wizard owns only LEFT/RIGHT)"
  - "msm law field-verified: pre-game 1 / during 0 (defensive) / post-Done 1 (snapshot restore)"
  - "editor_scheme N/A: not a setting in this build (get_editor_scheme()=1 API fn) -- nothing to restore in 03-07"
  - "03-06 plan step-9 (generic pi_stacking pose) was a CHECKLIST DEFECT for unset-random levels; replaced by the H-bond scoring test (SER near benzamide -> 1.00)"
  - "Ligand-above-grid start framing: camera-only roll after zoom-to-frame (user preference; objects never moved)"

patterns-established:
  - "Human checkpoint -> debug memory (.planning/debug) -> fix batch -> smoke regression battery (SMOKE-07 PART F, SMOKE-08 fix asserts) -> human re-test loop"
  - "Recolor code must always rebuild display lists; headless color-map equality is NOT sufficient proof of on-screen color"

# Metrics
duration: 2d (checkpoint session 2026-09-10, debugging detour + fix batch 2026-09-11, re-test + finalize 2026-09-11)
completed: 2026-09-11
---

# Phase 3 Plan 6: Gameplay-Loop Human Checkpoint Summary

**Human-approved core gameplay loop on stock PyMOL -- click-select, move/rotate, scoring (1.00 h_bond field-verified), switch-restore with display-rebuild fix, uniform reps, zoom-to-frame + ligand-above-grid start composition, multi-molecule notice, and cross-molecule scoring guard.**

## Performance

- **Duration:** 2026-09-10 (checkpoint session 1-2) + 2026-09-11 (fix batch + re-test + finalization)
- **Completed:** 2026-09-11T19:45Z
- **Tasks:** 1 checkpoint task (APPROVED) + checkpoint-deviation fix batch + finalization

## Checkpoint Verdict: APPROVED (human, 2026-09-10, both sessions; re-test of fix batch approved 2026-09-11 -- all 9 items)

| Check | Verdict | Notes |
|-------|---------|-------|
| PLAY-01 click-select / camera drag / empty-space click | PASS | stock 3-Button Viewing, no dev tweaks |
| PLAY-02 move + Confirm, result matches screen | PASS (after fix batch) | H-bond test: SER/ASN near benzamide -> Confirm -> 1.00 h_bond formed; replaces the plan's invalid generic pi_stacking step-9 (checklist defect: assumed the unset-random level would require pi_stacking -- seed-42 mol-0 requires h_bond x1) |
| PLAY-03 switch selection (restore + highlight) | PASS (after 0409216 switch-restore display-rebuild fix) | strict mol-0 re-test aa02->aa03->aa04 exact |
| Arrow-key Qt-focus probe | Recorded | LEFT/RIGHT + comma + period + q/w/e/d delivered; UP/DOWN dead BY DESIGN (wizard owns only LEFT/RIGHT; UP/DOWN co-fire command history) |
| 'No key mapping for CTSH-V' | Ignorable | accidental Ctrl+Shift keypress while pasting; zero aamatch keymapping involvement |
| editor_scheme idle sanity | N/A | NOT a setting in this build ("Error: unknown Setting"); get_editor_scheme()=1 API fn; nothing to restore in 03-07 |
| msm lifecycle | VERIFIED | pre-game 1 / during 0 (by-design defensive set) / post-Done 1 -- save/restore field-verified |
| Helper visuals during play | NONE at any point | PLAY-04 half confirmed by human |
| In/Out direction | no complaint | nudge camera-relativity confirmed live (R^T live-verified, probe dev 2.51e-08) |

### Fix-batch re-test (human, all 9 items APPROVED)

1. Zoom framing at start -- PASS
2. Uniform sticks for every AA -- PASS
3. 'Only molecule 1 of 2 counts and is clickable' notice -- PASS
4. Single-green invariant (incl. same-slot re-click) -- PASS
5. Clicks on the other molecule's AAs are no-ops -- PASS
6. Reset behavior (colors of all but the selection restored) -- PASS
7. Scoring still 1.00 (h_bond test) -- PASS
8. 'Formed (not required): <type> xN' result line -- PASS
9. Done restore (msm + colors) -- PASS

Remaining cosmetic preference (RESOLVED during finalization): the small molecule appeared BELOW the AA grid at start; human prefers it ABOVE -> implemented as a camera-only roll (commit 1d48d71).

## Debugging Detour

Full memory: `.planning/debug/phase3-gui-checkpoint-failures.md` (6 verdicts, closed).

Headless probes (`tmp/probe_gui_0306.py` / `probe_gui_0306b.py`, same Python/build as the GUI) REPRODUCED every field symptom and eliminated every detector hypothesis:

- **PLAY-02 "no score change" = NOT a detector bug.** A perfect scripted PHE pose fires pi_stacking (d_center=4.5000, angle=0.00deg, offset=0.0000, sensitivity sweep: tilt 27deg passes/31 kills, lateral 1.9 passes/2.5 kills, vertical 5.4 passes/5.6 kills) while score stays 0.00 -- because seed-42 molecule-0 requires **h_bond x1**, and list-mode scoring counts only REQUIRED types. Root cause compound: (1) checklist defect above; (2) natural PHE ring tilt 31.18deg > 30deg threshold defeats by-eye translation-only poses; (3) mol-1 (acetate, no aromatic ring, click no-op) confuses targeting.
- **PLAY-03 "color not restored" = cmd.alter display-list STALENESS, not a data bug.** Headless restore was byte-exact (color maps identical) -- the data level was always correct. The on-screen staleness came from `cmd.alter`-based recolors not rebuilding the object's display lists, unlike `cmd.color` which does. Fix: after restoring the previous slot's colors, the wizard rebuilds the restored object's display lists (commit 0409216). Recorded law: **any future recolor code must rebuild display lists; headless color-map equality is not sufficient proof of on-screen color.**
- mol-1 part of the field report = by-design no-op clicks (build_slot_map scopes the game to molecule 0); fixed by the multi-molecule notice, not by code behavior change.
- Reps split (neutral bits=49 vs charged bits=2176) = PyMOL new-object display heuristic on chempy fragments -- detector never reads reps; homogenized to sticks at materialize.
- Cross-molecule scoring leak = real latent design gap found during the detour: whole-scene `engine.detect()` records could count toward molecule-0 required types; Confirm now runs a molecule-scoped detection pass (commit 5962bb2).

## Fix Batch Commits (checkpoint-deviation batch, 2026-09-11)

1. `0409216` (fix) switch-restore: rebuild display lists after AA color restore
2. `0409216` companion -- SMOKE-07/08 regression batteries grew around it:
   - `8d635bb` (test) SMOKE-07 PART F -- the field-bug batteries (+26 checks)
   - `24a0c94` (test) SMOKE-08 fix asserts -- uniform reps + zoom + scope notice
3. `d0b8cee` (fix) uniform sticks representation for every AA at materialize
4. `72e2c6c` (fix) zoom camera to frame the whole game at start
5. `7cf28f5` (feat) 'Formed (not required): <type> xN' result line
6. `97187c2` (feat) multi-molecule scope notice in prompt + panel
7. `5962bb2` (fix) scope Confirm/scoring to the current molecule
8. `d213771` (docs) msm baseline field-verified; verdict 4 closed
9. `ca051cc` (docs) checkpoint verdicts + fix batch recorded

### Finalization commits (2026-09-11)

10. `1d48d71` (fix) ligand-above-grid start framing (camera-only roll; SMOKE-08 view-matrix asserts)

**Plan metadata:** `docs(03-06): complete gameplay-loop checkpoint plan` (commit follows this file)

## Files Created/Modified

- `.planning/debug/phase3-gui-checkpoint-failures.md` - 6-verdict debug memory for the detour
- `aamatch/wizard.py` - display-rebuild after restore; molecule-scoped Confirm
- `aamatch/wizard_text.py` - 'Formed (not required)' line; scope notice strings
- `aamatch/placement.py` - uniform sticks at materialize
- `aamatch/engine.py` - molecule-scoped detection pass for scoring
- `aamatch/gamestart.py` - zoom-to-frame (72e2c6c) + ligand-above-grid roll (1d48d71)
- `smoke/smoke_07_wizard_loop.py` - PART F field-bug batteries
- `smoke/smoke_08_starter.py` - fix asserts (reps/zoom/notice/composition)

## Decisions Made

- **Keyboard map (feeds Phase-5 input decisions):** LEFT/RIGHT + ',' '.' + q/w/e/d delivered to the wizard; UP/DOWN dead by design (wizard owns only LEFT/RIGHT per 03-03; UP/DOWN co-fire command history).
- **msm law:** pre-game 1 / during 0 (defensive set) / post-Done 1 (snapshot restore) -- field-verified; the save/restore ordering (03-03 ORDER LAW) is correct and locked.
- **editor_scheme:** not a setting in this build; nothing to set/restore in 03-07. The 03-06 checklist line was wrong.
- **Scoring checklist replacement:** the H-bond test (SER near benzamide -> 1.00) is the valid PLAY-02 scoring check for unset-random levels; the plan's generic pi_stacking step-9 is retired.
- **Display-rebuild law:** any code that recolors/restores AA colors must rebuild the object's display lists (proven failure mode: cmd.alter display-list staleness vs cmd.color redraw).
- **Cross-molecule guard:** Confirm/scoring is molecule-scoped; wrong-ligand records can never count. Whole-scene `engine.detect()` is kept for grid/hygiene asserts only.
- **Start composition:** zoom-to-frame first, then camera-only roll so the ACTIVE ligand composes directly above the grid (user preference 2026-09-11). Game geometry is generator-owned and never moved for presentation.
- **Spec correction recorded by the human:** Plugins -> AA-match must ultimately open a SETUP POPUP per spec.md lines 12-21 (Phase-3 gap candidate; the full Qt setup window is Phase 4, UI code borrowable from bioCHEMeleon). Recorded for gap-closure planning.

## Deviations from Plan

The plan was a single human checkpoint with NO code changes; the checkpoint surfaced field bugs. All fixes auto-applied under the deviation rules, batched and re-tested:

### Auto-fixed Issues

**1. [Rule 1 - Bug] On-screen color restore staleness (display lists)**
- **Found during:** checkpoint PLAY-03
- **Issue:** restored AA colors were byte-exact in data but stale on screen (cmd.alter does not rebuild display lists)
- **Fix:** rebuild the restored object's display lists after color restore
- **Files modified:** `aamatch/wizard.py`
- **Verification:** SMOKE-07 PART F + strict mol-0 human re-test (aa02->aa03->aa04)
- **Committed in:** `0409216`

**2. [Rule 1 - Bug] Skewed AA representations at materialize (charged=lines vs neutral=sticks)**
- **Committed in:** `d0b8cee` (`aamatch/placement.py`; detector never reads reps -- homogenize at materialize)

**3. [Rule 2 - Missing Critical] Cross-molecule scoring leak (design gap)**
- **Found during:** debugging detour code read
- **Issue:** whole-scene records could count toward molecule-0 required types
- **Fix:** molecule-scoped detection pass behind Confirm
- **Committed in:** `5962bb2` (`aamatch/engine.py` / `aamatch/wizard.py`)

**4. [Rule 2 - Missing Critical] Start view unusable (zoomed-in fresh camera)**
- **Committed in:** `72e2c6c` (+ ligand-above-grid roll `1d48d71`)

**5. [Rule 2 - Missing Critical] Invisible detected-but-not-required interactions; silent mol-1 clicks**
- **Fix:** 'Formed (not required)' line + 'Only molecule 1 of 2 counts' notice
- **Committed in:** `7cf28f5`, `97187c2`

**6. [Rule 3 - Blocking] Checklist defect: step-9 pi_stacking test invalid for unset-random level**
- **Fix (process):** play the H-bond test instead; recorded as the standing PLAY-02 scoring check

**Total deviations:** 6 auto-fixed groups (9 code commits + 2 test commits; all gate-green)
**Impact on plan:** All fixes were correctness/usability essentials surfaced by the human checkpoint; no scope creep -- Qt/setup UX deliberately NOT touched (Phase 4).

## Issues Encountered

None beyond the checkpoint-deviation batch itself (documented above + in the debug memory).

## Test/Gate Counts

- WSL suite: **593 -> 614 tests** (all green, python3.6; purity gates included)
- SMOKE-07: 52 -> 78 checks (PART F added), PASS
- SMOKE-08: 26 -> 31 checks (fix asserts + composition asserts), PASS
- `python3.6 -m py_compile aamatch/*.py` clean

## User Setup Required

None.

## Next Phase Readiness

- **03-07 human checkpoint is next** (restoration + no-helper-visuals + drag diagnostics): wizard/msn-path restore already headlessly proven; no-helper-visuals human-confirmed here; drag feel + hybrid-drag diagnostics are the open items.
- Phase verifier after 03-07: this summary provides the ROADMAP [HUMAN] half of Phase-3 criteria 1-3.
- Phase-5 inputs staged: keyboard map; ligand-above-grid preference (implemented); start-sequence UX notes.
- Gap-closure planning: spec.md 12-21 setup popup from the menu item is a Phase-3 gap candidate (Phase 4 scope for the full Qt window).

---
*Phase: 03-wizard-gameplay-loop*
*Completed: 2026-09-11*
