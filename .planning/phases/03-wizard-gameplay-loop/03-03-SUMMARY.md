---
phase: 03-wizard-gameplay-loop
plan: 03
subsystem: ui
tags: [pymol, wizard, gameplay-loop, cmd-tier, baked-transforms]

# Dependency graph
requires:
  - phase: 03-wizard-gameplay-loop/03-01
    provides: wizard_core pure helpers (slot map, transient guard, camera math, color bookkeeping, movement constants)
  - phase: 03-wizard-gameplay-loop/03-02
    provides: wizard_text pure panel/prompt/result text builders
  - phase: 02-data-and-headless-engine
    provides: engine ops (confirm/reset_to_grid/place_aa), placement registry, geometry.centroid_of
provides:
  - aamatch/wizard.py — the complete cmd-tier GameWizard (PLAY-01..04): stack-native lifecycle with msm/pk1/sele/color save-restore, canonical pick routing to slot identity, recolor selection feedback, baked-transform movement (panel + keyboard), engine.confirm/reset_to_grid wrappers
  - the full headless-callable gameplay-loop surface that SMOKE-07 (03-04) drives in real PyMOL
affects: [03-04 SMOKE-07 + gamestart wiring, Phase 4 Qt shell (same engine calls), Phase 6 score-history lifecycle, Phase 7 pse wizard-pickle round-trip, Phase 9 help text (orientation-kept note)]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Thin input adapter: wizard holds only plain picklable data; engine imported relatively inside methods (module-identity-safe by construction)"
    - "Stack-native wizard lifecycle: push on activate, canonical cmd.set_wizard() Done pops + auto-resumes prior wizard; no saved-wizard pattern"
    - "Push-before-snapshot msm ORDER LAW (a popped GameWizard's cleanup restores the user's true msm inside set_wizard)"
    - "Baked-transform movement with a fail-closed identity-object-matrix invariant after every move (on-screen == stored == detected by construction)"
    - "_guard wrapper: house errors (ValueError family) become visible self._error + refresh; unexpected exceptions propagate"

key-files:
  created: [aamatch/wizard.py]
  modified: []

key-decisions:
  - "Transient-only selection delete guard in do_select (a user's NAMED selection is never deleted; canonical always-delete rejected as user-data loss)"
  - "Position-only reset (option a): rotations persist through Reset; re-materialize rejected (invalidates pick map + color snapshots mid-game)"
  - "Selection + recolor persist through reset_grid; stale result cleared; identity-matrix asserted for every recolored-slot object after replay"
  - "UP/DOWN never used as game keys (co-fire command-line history unconditionally); do_special owns LEFT(100)/RIGHT(102); do_key owns w/s/q/e + ','/'.'"
  - "Alter expression sandbox dict-subscript ('color=m[ID]') preferred for color restore with a per-id cmd.alter fallback (SMOKE-07 field-verifies which branch fires)"

patterns-established:
  - "Handler split: public handler -> _guard -> _impl; engine access lazily relative inside the impl"
  - "_current_object/_matrix16/_assert_identity primitives as the single movement guard sites (error lines visible, never silent)"

# Metrics
duration: 14min
completed: 2026-09-09
---

# Phase 3 Plan 03: GameWizard cmd-tier Summary

**aamatch/wizard.py (601 lines, 3.6-clean) implements the full Phase-3 gameplay loop: stack-native wizard lifecycle with push-before-snapshot msm save-restore, canonical do_select→do_pick pick routing into the placement registry's slot map, recolor-only selection feedback with lazy per-slot color snapshots, baked world-transform movement with a fail-closed identity-matrix invariant after every move, and engine.confirm / engine.reset_to_grid wrappers rendered as pure-builder panel/prompt text — zero banned-token mentions, 590-test WSL suite still green.**

## Performance

- **Duration:** ~14 min
- **Started:** 2026-09-09T01:49:54Z
- **Completed:** 2026-09-09T02:03:53Z
- **Tasks:** 3 completed
- **Files modified:** 1 (aamatch/wizard.py, created)

## Accomplishments

- PLAY-01: click → slot identity via the reverse object map (clicks on ligands/user objects/other molecules' AAs are no-ops); recolor feedback with exactly-once lazy snapshot per slot + full restore on switch/cleanup (detection-safe: extract_game_atoms never reads color).
- PLAY-02: movement only via `cmd.translate(state=1, camera=0)` / `cmd.rotate(selection, camera=0, origin=)` baked world-frame transforms; `_assert_identity` (rotation block + translation within 1e-6) after every move is the on-screen == stored == detected contract.
- PLAY-03: confirm_molecule wraps engine.confirm verbatim and renders score/formed/missing as text; reset_grid wraps engine.reset_to_grid (position replay, rotations persist — documented) and keeps the selection.
- PLAY-04: cleanup() restores the msm SNAPSHOT (never hard-coded 0), unpicks + deletes pk1-if-present, deselects, restores every recolored slot's colors, is idempotent, guards `self.cmd is None`; never deletes game objects, touches user objects, or mutates engine state.
- Lifetime: activate() push-before-snapshot ORDER LAW implemented exactly (set_wizard → msm snapshot → defensive 0); Done = canonical `cmd.set_wizard()` (stack auto-resumes the prior wizard) — the v1 saved-wizard pattern explicitly rejected in the docstring.

## Task Commits

Each task was committed atomically:

1. **Task 1: GameWizard shell — lifecycle, msm snapshot, cleanup contract** — `45d7d59` (feat)
2. **Task 2: pick routing + recolor feedback + panel/prompt wiring** — `a0faec9` (feat)
3. **Task 3: baked-transform movement, confirm/reset handlers, keyboard channels** — `1c3737c` (feat)

**Plan metadata:** (this commit) `docs(03-03): complete game-wizard plan`

## Files Created/Modified

- `aamatch/wizard.py` (created, 601 lines) — the cmd-tier GameWizard: module docstring pins 6 binding contracts (thin adapter, plain-data pickle discipline, stack-native lifecycle, msm snapshot ORDER LAW, baked-transform movement model + PROSE discipline for the banned matrix calls, no helper visuals); class surface: `WizardError`, `GameWizard` with `activate`/`cleanup`, `do_select`/`do_pick`/`_select_slot`, `nudge_cam`/`rotate_axis`/`rotate_view`/`step_to_ligand`/`move_to`, `confirm_molecule`/`reset_grid`, `get_prompt`/`get_panel`, `get_event_mask` (=15), `do_special`/`do_key`.

## Decisions Made

- **Handler/guard split:** every movement/engine handler is `public() -> _guard(_impl)`; `_guard` catches the ValueError family (EngineError/PlacementError/WizardError are all ValueError subclasses, so one `except ValueError` covers the plan's named set) into `self._error` + `cmd.refresh_wizard()`; unexpected exceptions propagate (bug surfacing).
- **Color restore expression:** preferred `cmd.alter(obj, 'color=m[ID]', space={'m': m})` with a per-id fallback loop if the build's expression sandbox rejects dict subscripting — SMOKE-07 field-verifies which branch fires (plan-authorized fallback).
- **Minor task-boundary adjustment:** `_atom_colors`/`_restore_slot_colors` (the plan's Task 2) were implemented in Task 1's commit because Task 1's cleanup() calls `_restore_slot_colors` — kept each commit runtime-coherent; Task 2's own surface (do_select/do_pick/_select_slot/getters) committed as specified.
- All other decisions followed the plan/research verbatim (transient-only delete, position-only reset, keyboard ownership, result rendering through wizard_text).

## Deviations from Plan

None of substance — plan executed as specified. (The task-boundary note above is a commit-ordering choice, not a behavior change; no Rule 1/2/3 auto-fixes were needed — no bugs, missing-critical functionality, or blockers were found.)

## Issues Encountered

None. Audit gate (`tests/test_code_audit.py` prose-pin + banned-call AST scan), purity gates, and the 3.6 syntax floor all pass on the new file on the first run.

## User Setup Required

None — no external service configuration required.

## Next Phase Readiness

**03-04 (SMOKE-07) notes:**

- Drive `GameWizard` headlessly: `engine.new_game` → `engine.materialize` → `GameWizard(payload, registry)` → `activate()`; script picks by `cmd.select('sele', '<slot object> and name CA')` + `do_select('sele')` directly (real-mouse delivery is the human checkpoint; RESEARCH-wizard §8).
- Use `move_to` for the deterministic 4.5 Å π-stacking pose — with the EXPLICIT baked ring-alignment step scripted first (02-14 decision: fragments carry no guaranteed ring orientation; SMOKE-06 PART A is the reference pattern).
- Live-verify `wizard_core.view_camera_to_world` against a scripted `cmd.set_view` (single fix site if the live build proves the opposite convention); also probe the camera z-sign feel of 'q'/'e' at the human checkpoint (cosmetic, detector-neutral).
- Observe which color-restore branch fires: the `color=m[ID]` sandbox expression vs the per-id fallback (both house-legal).
- Field-check the lazy engine import works identically under the smoke's `aamatch` identity (plugin-path).
- Confirm arrow-key delivery through the Windows Qt GUI focus path at the human checkpoint (RESEARCH-wizard §10.1 — the one soft spot); panel buttons remain the guaranteed path.
- Repeated Confirm appends to the engine GameState's molecule_scores (documented caveat; Phase 6 owns score-history lifecycle).

**Blockers:** none carried forward by this plan.
