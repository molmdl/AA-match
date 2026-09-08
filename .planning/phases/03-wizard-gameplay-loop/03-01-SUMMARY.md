---
phase: 03-wizard-gameplay-loop
plan: 01
subsystem: pure-logic
tags: [wizard, pymol, pick-routing, camera-math, color-snapshot, tdd]

# Dependency graph
requires:
  - phase: 02-headless-game-engine
    provides: placement.materialize registry shape ({slot_id: (object, sorted ids)}), vec3 floats-in/floats-out contract, PURE_MODULES gating pattern
provides:
  - "aamatch/wizard_core.py: build_slot_map, transient_selection, view_camera_to_world, ensure_snapshot, color_map, snapshot_objects (PURE, gated)"
  - "movement constants NUDGE_STEP 1.0 / ROTATE_STEP_DEG 10.0 / ROTATE_BUTTON_STEP_DEG 90.0 / HIGHLIGHT_COLOR 'green'"
  - "RED-first pinned camera->world R^T.step convention (single fix site if SMOKE-07 disproves it)"
affects: [03-02 movement layer, 03-03 GameWizard cmd tier, 03-04 SMOKE-07]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Phase-3 pure/cmd split: every wizard decision that is not a cmd call is a pure, WSL-tested helper"
    - "TDD rhythm RED test -> GREEN feat -> PURE_MODULES registration test commit (02-02 pattern)"
    - "fail-closed ValueError on registry-shape violation; never KeyError/TypeError leak to pick routing"

key-files:
  created:
    - aamatch/wizard_core.py
    - tests/test_wizard_core.py
  modified:
    - tests/test_purity.py

key-decisions:
  - "build_slot_map scoped to ONE molecule_index (Phase 3 scopes the wizard to molecule 0 per registry-molecule; RESEARCH section 5.4)"
  - "transient-only delete guard: sele/pk1..pk4/'_'-prefixed deletable, named user selections survive (RESEARCH section 10.2 recorded decision)"
  - "camera->world step = R^T.step over get_view's row-major world->camera block; identity view is pass-through; live confirmation deferred to SMOKE-07, wizard_core is the single fix site"
  - "color snapshot taken exactly once per slot (lazy, before first recolor) and idempotent afterwards; restore view = plain {ID: color} map; cleanup order = sorted object names"

patterns-established:
  - "Wizard pure-core: pick identity via reverse map built from the registry, all bookkeeping as plain picklable caller-owned data"
  - "Snapshot-before-first-recolor idempotency contract (PLAY-01 feedback + PLAY-04 restore precondition)"

# Metrics
duration: ~15 min
completed: 2026-09-08
---

# Phase 3 Plan 01: Pure Wizard Core Summary

**Pure wizard gameplay logic (slot reverse-map, camera-to-world nudge math, PLAY-01 color snapshot bookkeeping, movement constants) proven RED-first and gated as PURE_MODULES #14**

## Performance

- **Duration:** ~15 min
- **Started:** 2026-09-08T19:21Z (resumed executor session; no prior work existed)
- **Completed:** 2026-09-08T19:34Z
- **Tasks:** 2 (RED battery; GREEN implementation + PURE_MODULES registration)
- **Files modified:** 3 (2 created, 1 modified)

## Accomplishments

- `aamatch/wizard_core.py` (192 lines): six pure helpers + four pinned constants, ZERO imports of any kind, fail-closed ValueError refusals naming the cause on every bad-shape path
- `tests/test_wizard_core.py` (239 lines): 18 tests — hand-computed Rz(+90) expectations for the R^T.step convention, exact reverse-map equality, 5 refusal classes, snapshot idempotency + defensive-copy proofs
- Registered in `tests/test_purity.py` PURE_MODULES (= 14): Gates A/B now scan the module mechanically
- WSL suite 531 -> 549 tests, fully green; `python3.6 -m py_compile aamatch/*.py` clean

## Task Commits

Each task was committed atomically (TDD cycle):

1. **Task 1: RED — failing test battery** — `325e3ca` (test: add failing tests for pure wizard core helpers; RED proof = ImportError on `from aamatch import wizard_core`)
2. **Task 2: GREEN — implement wizard_core.py** — `eeeb354` (feat: implement pure wizard core helpers; 18/18 tests green)
3. **Task 2: REGISTER in PURE_MODULES** — `a7e01d3` (test: register wizard_core in PURE_MODULES; full suite 549 green)

Post-cycle docstring precision commit: `922dd0a` (docs: pin `registry['molecules'][molecule_index]['slots']` consumption path in build_slot_map docstring — plan key_link; `.get`-based access retained for fail-closed ValueError on bad shapes)

**Plan metadata:** see final `docs(03-01)` commit (PLAN.md + SUMMARY.md)

## Files Created/Modified

- `aamatch/wizard_core.py` — PURE wizard core: build_slot_map, transient_selection, view_camera_to_world, ensure_snapshot, color_map, snapshot_objects + NUDGE_STEP/ROTATE_STEP_DEG/ROTATE_BUTTON_STEP_DEG/HIGHLIGHT_COLOR
- `tests/test_wizard_core.py` — RED-first unit battery (18 tests, hand-computed expectations, fail-closed refusals)
- `tests/test_purity.py` — PURE_MODULES += 'wizard_core' with Phase-3 comment

## Decisions Made

- **build_slot_map consumes ONE molecule:** the plan pins Phase-3 scoping to a single `molecule_index` (RESEARCH §5.4; Phase 6 owns multi-molecule lifecycle) — two-molecule registry test proves the other molecule's objects stay out of the map.
- **`.get`-based registry access instead of indexing:** refuse with ValueError *naming the cause* (registry non-dict, no molecules list, no slots dict) rather than leaking KeyError/TypeError into pick routing; the consumption path `registry['molecules'][molecule_index]['slots']` is pinned in the docstring (plan key_link).
- **Slot entries must be true 2-tuples with a non-empty str object name** (list-entries refused too — placement.materialize produces tuples; shape drift must refuse loudly).
- **R^T.step convention pinned by unit tests, live-confirmed later:** identity view = pass-through; Rz(+90) block hand-computed. Module docstring marks wizard_core as the single fix site if SMOKE-07 (03-04) proves the opposite convention.
- **Snapshot store is caller-owned plain picklable data**, mutated in place; `ensure_snapshot` defensively copies rows so later caller mutation cannot drift the restore data.

## Deviations from Plan

None — plan executed exactly as written. (The `922dd0a` docstring commit carries no behavior change; it pins documentation the plan's key_link greps for.)

## Issues Encountered

None. RED failed with the expected ImportError; GREEN passed 18/18 on first run; registration kept the full suite green.

## User Setup Required

None — no external service configuration required.

## Next Phase Readiness

- **03-02** can build the movement layer on `view_camera_to_world` + NUDGE_STEP/ROTATE_STEP_DEG/ROTATE_BUTTON_STEP_DEG without inventing math inline
- **03-03 GameWizard** wires proven helpers: reverse map at activation, transient-only delete in do_select, snapshot/recolor bookkeeping per slot
- **03-04 SMOKE-07** must live-verify the R^T rotation-block convention against a scripted cmd.set_view; wizard_core is the single fix site if disproven
- Note: prior plans (02-08 generator, 02-10 game_state) added a registration-pin TestCase class in test_purity.py; 03-01 per plan added only the comment annotation — consider a pin test in a later plan if desired

---
*Phase: 03-wizard-gameplay-loop*
*Completed: 2026-09-08*
