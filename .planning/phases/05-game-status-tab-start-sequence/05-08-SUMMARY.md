---
phase: 05-game-status-tab-start-sequence
plan: 08
subsystem: ui
tags: [pymol, wizard, hint, capability, color-bookkeeping, qt, smoke]

# Dependency graph
requires:
  - phase: 05-game-status-tab-start-sequence
    provides: hint_required_types + hint_candidate_slots pure battery (05-02); wizard_core.HINT_COLOR 'orange' (05-03); GameTab skeleton with btn_hint/start_countdown/_log (05-06)
  - phase: 03-gameplay-wizard
    provides: GameWizard.playing loop, PLAY-01 ensure_snapshot _color_store machinery, _guard handler contract, stack-native lifecycle (03-03); display-rebuild law (03-06)
  - phase: 02-headless-engine
    provides: capability.aa_capable/residue_capabilities (02-05), engine ops + _remap_ligand_bonds (02-14), ligand_data profile contract (02-08)
provides:
  - engine.ligand_profile_molecule(level_index, molecule_index) — live ligand chemistry profile recomputed from the materialized ligand object (byte-equal to generation-time; DETECT-04 by construction)
  - GameWizard.hint()/_hint_impl — PLAY-05 capability recolor: ensure_snapshot into the ONE _color_store BEFORE the first cmd.color(HINT_COLOR, '<obj> and elem C') per candidate
  - GameTab._guard (04-09 verbatim contract, first on the class) + _on_hint/_hint_now + connected btn_hint + the pinned info-box line 'Hint: %d eligible amino acid(s) highlighted.'
  - wizard._guard now returns the op's result (None on guarded refusal) — plain data can cross the seam
  - SMOKE-11 PART J: end-to-end headless proof of the hint mechanics (11 checks, J1-J7)
affects: [05-09 (PART G start rework / deferred drive + dialog handler interplay), 06-scoring-debrief, 09-docs-help (hint UX text)]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "hint = capability-live recompute (resn x live ligand profile x resolved required), NEVER generation-time can_form provenance"
    - "ONE color store, snapshot-before-recolor: every recolor path (selection green, hint orange) feeds wizard_core.ensure_snapshot; cleanup() is the single restore owner"
    - "Qt handler family on GameTab: non-modal impl + _guard + isinstance-gated silent no-op before GO"

key-files:
  created: []
  modified:
    - aamatch/engine.py
    - aamatch/wizard.py
    - aamatch/game_window.py
    - smoke/smoke_11_window.py

key-decisions:
  - "_guard (wizard.py) returns the op result on success and None on a guarded refusal — the only seam change needed so hint() can hand plain data out; every prior caller ignores the return"
  - "Empty candidate set fail-closes into WizardError: solvability-by-construction makes it unreachable for a real payload, and a silent no-op would hide a bug"
  - "The handler logs 'Hint: %d eligible amino acid(s) highlighted.' only when result is not None — the unreachable WizardError path already surfaced on the wizard panel; a TypeError there would misreport"

patterns-established:
  - "Capability recolor op: per-candidate-object 'obj and elem C' selection strings built ONLY from _objects_by_slot (molecule-scoped by construction — H-5); cmd.color (redraw-safe apply) never alter on the apply path (03-06 law)"
  - "SMOKE hint PART recipe: whole-scene (ID, color, elem) maps compared before/after every phase (no-op, recolor, idempotence, coexistence, restore) — equality of the maps, never sample reads"

# Metrics
duration: 17 min
completed: 2026-09-18
---

# Phase 5 Plan 08: Hint vertical slice Summary

**PLAY-05 Hint shipped end-to-end: capability-live candidate computation (pure helpers + live ligand profile) driving a carbon-only orange recolor through the ONE existing color store — idempotent, coexistant with selection green, fully restored on Done — plus the GameTab button handler and an 11-check headless smoke PART proving every mechanic.**

## Performance

- **Duration:** 17 min
- **Started:** 2026-09-18T19:55:10Z
- **Completed:** 2026-09-18T20:12:13Z
- **Tasks:** 3
- **Files modified:** 4

## Accomplishments

- `engine.ligand_profile_molecule` (op 5c): the hint's "could form" input recomputed from the LIVE ligand object via `_remap_ligand_bonds` + `capability.ligand_profile`, scoped exactly like `detect_molecule`; byte-equal to generation-time because the ligand is loaded once at materialize and never modified (movement is AA-only)
- `GameWizard.hint()`/`_hint_impl`: candidates via `capability.hint_candidate_slots(slots, profile, required)` — NEVER reads `can_form` provenance (generator.py:453-456); the (a) trap (H-1) is closed by `ensure_snapshot` into `_color_store` BEFORE the first `cmd.color(HINT_COLOR, '<obj> and elem C')` per candidate; empty candidates fail-close into WizardError
- `GameTab._guard` (04-09 verbatim, first on this class) + `_on_hint`/`_hint_now`: isinstance-gated silent no-op pre-GO (H-8/P-1), pinned log line post-GO; `btn_hint` connected in `__init__` per the 04-05 shell law
- SMOKE-11 PART J (11 checks, all PASS): J1 pre-GO no-op, J2 pure/cmd candidate agreement + GEN-04 parity, J3 carbon-only recolor with ligand/distractors/other-molecule/baseline untouched (H-5), J4 idempotence, J5 hint-over-green per-atom coexistence, J6 pinned log line, J7 whole-scene Done restore incl. hinted-never-selected objects (H-1); the Gate-A2 echo re-lettered J → K

## Task Commits

Each task was committed atomically:

1. **Task 1: engine.ligand_profile_molecule** - `c18866a` (feat)
2. **Task 2: GameWizard.hint capability recolor** - `95a53ed` (feat)
3. **Task 3: hint handler + SMOKE-11 hint part** - `0739dd9` (test)

## Files Created/Modified
- `aamatch/engine.py` — op 5c `ligand_profile_molecule` + module docstring OP list entry
- `aamatch/wizard.py` — `hint()`/`_hint_impl` (methods only, zero new attributes per contract 2) + `_guard` return-value seam
- `aamatch/game_window.py` — `GameTab._guard`/`_on_hint`/`_hint_now`, `btn_hint` connect, docstring ROLE update (button now connected)
- `smoke/smoke_11_window.py` — new hint PART J (11 checks), Gate-A2 echo re-lettered to PART K, header part list updated, I2 label updated ("05-08 connected")

## Decisions Made

- **wizard._guard returns the op result** (None on guarded refusal): the plan's return contract (`hint()` hands `{'count', 'slot_ids'}` through the established `_guard` seam) was blocked by `_guard` discarding the return; adding `return op(...)` is behavior-neutral for all prior callers (they ignore it) and keeps the single-seam contract intact
- **The handler guards `result is not None` before logging**: the empty-candidate WizardError path (unreachable under solvability) already surfaced on the wizard panel; logging `result['count']` there would TypeError and misreport
- **`can_form` occurrence in wizard.py = 1, docstring-only**: the plan mandates the "never reads can_form" prose; zero CODE reads exist (grep verification: "zero NEW reads" — reads, not prose)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] wizard._guard now returns the op result**
- **Found during:** Task 2 (GameWizard.hint implementation)
- **Issue:** `_guard` ran `op(*args, **kwargs)` without returning, so `hint()` could not deliver the plan-mandated `{'count', 'slot_ids'}` plain data to the tab handler through the established seam (adding a new wizard attribute to ferry the result would violate contract 2)
- **Fix:** `return op(*args, **kwargs)` on success, `return None` in the guarded-refusal branch; updated the `_guard` docstring to state the seam behavior; verified all 8 prior call sites ignore the return (no behavior change)
- **Files modified:** aamatch/wizard.py
- **Verification:** full WSL suite (incl. all wizard-loop tests) stays green; SMOKE-11 PART J asserts `wiz.hint()` and `dlg.game_tab._hint_now()` return the dict
- **Committed in:** 95a53ed (Task 2 commit)

**2. [Rule 2 - Missing Critical] _hint_now guards the unreachable None result before logging**
- **Found during:** Task 3 (handler implementation)
- **Issue:** the plan's verbatim shape logs `result['count']` unconditionally; on the unreachable-but-designed fail-closed WizardError path `hint()` returns None (via `_guard`) and the unconditional subscript would TypeError through the Qt slot, hiding the real refusal already shown on the wizard panel
- **Fix:** log the pinned line only when `result is not None`
- **Files modified:** aamatch/game_window.py
- **Verification:** SMOKE-11 PART J1/J6 assert both branches' reachability shape (None pre-GO, dict + log line post-GO); full suite green
- **Committed in:** 0739dd9 (Task 3 commit)

---

**Total deviations:** 2 auto-fixed (1 blocking, 1 missing critical)
**Impact on plan:** Both fixes are contract-completing edge handling; the delivered surface matches the plan exactly. No scope creep.

## Issues Encountered

None — every planned check passed on the first full SMOKE-11 run (J2 candidate count 6 on the seed-42 defaults game; pure and cmd paths agreed exactly).

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- 05-09 (PART G start rework / deferred activation drive) can land: the hint PART is written against the CURRENT drive (`start_game` default-activates) and its pre-GO no-op assert (J1) already exercises the deferred `activate=False` + `start_countdown` shape, so the rework must keep J1 green (the isinstance gate is the invariant, not the activation timing)
- PLAY-05 mechanics are closed headlessly; on-screen redrawing of hint colors (the 03-06 display-law class) is a human checkpoint item for the phase checkpoint, expected-pass (cmd.color invalidate is C-cited)
- The pinned info-box line wording 'Hint: %d eligible amino acid(s) highlighted.' is now contractual (SMOKE-11 J6) — the status-poll plan should not reword it

---
*Phase: 05-game-status-tab-start-sequence*
*Completed: 2026-09-18*
