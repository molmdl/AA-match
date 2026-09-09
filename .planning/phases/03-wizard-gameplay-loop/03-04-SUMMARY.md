---
phase: 03-wizard-gameplay-loop
plan: 04
subsystem: testing
tags: [pymol, wizard, smoke-test, e2e, ast-source-gate, baked-transforms]

# Dependency graph
requires:
  - phase: 03-wizard-gameplay-loop/03-03
    provides: aamatch/wizard.py GameWizard cmd tier (the class under test)
  - phase: 03-wizard-gameplay-loop/03-01
    provides: wizard_core (view_camera_to_world R^T convention, color bookkeeping, movement constants)
  - phase: 03-wizard-gameplay-loop/03-02
    provides: wizard_text panel/prompt/result text builders (live-rendered result lines asserted)
  - phase: 02-data-and-headless-engine
    provides: engine new_game/materialize/confirm/reset_to_grid, SMOKE-04 pose-scripting pattern, SMOKE-06 identity-matrix helpers, 02-15 float32 pose tolerance
provides:
  - smoke/smoke_07_wizard_loop.py — the 52-check count-asserted headless E2E wizard loop (activation/pick routing/recolor/switch/no-ops, movement + identity invariant with the LIVE R^T verification, confirm composition scoring 1.0, reset replay, the full Done restore table, multi-molecule scoping) — === SMOKE-07 PASS ===
  - tests/test_wizard_source.py — permanent AST source gate banning helper-visual calls (indicate/distance/load_cgo) in the wizard source, with a firing negative control and a zero-mention banned-token pin
  - Live-verified record: wizard_core.view_camera_to_world's R^T convention is correct against scripted cmd.set_view (dev 2.5e-08); cmd.unpick() deletes the pk1 selection buffer in this build (probe-pinned); the sandbox color-restore branch (color=m[ID]) fires (fallback stays dormant)
affects: [03-05 gamestart wiring (source gate grows a scanned module), 03-06/03-07 human checkpoints (only real-mouse delivery remains), Phase 6 score-history lifecycle, Phase 9 orientation-kept help note]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Scripted-pick recipe for headless wizard testing: cmd.select('sele', '<slot object> and name CA') -> do_select('sele') reproduces the C-layer pick route exactly"
    - "Live-convention verification: script only the get_view rotation block (tail copied verbatim from the captured view) so world-frame math is checked against the build, not assumptions"
    - "Movement smoke re-asserts the identity matrix itself after every press (the wizard's internal invariant fail-closes into _error, so the smoke checks both _error and the matrix)"

key-files:
  created: [smoke/smoke_07_wizard_loop.py, tests/test_wizard_source.py]
  modified: []

key-decisions:
  - "cmd.unpick() DELETES the pk1 selection buffer in this build (probe-pinned) — do_pick's hygiene unpick consumes pk1 per pick; cleanup's pk1 deletion is the defensive post-Done guarantee"
  - "wizard_core.view_camera_to_world's R^T-over-get_view convention is LIVE-CORRECT (scripted Rz(90deg) set_view nudge lands within 2.5e-08 of the hand-computed (0,-1,0) step) — the 03-01 single fix site stays untouched"
  - "Color restore fires the SANDBOX branch (cmd.alter 'color=m[ID]' dict subscript accepted by this build; the per-id fallback stays dormant)"

patterns-established:
  - "Wizard smoke parts consume handler-level state (_current_slot/_result/_error) read-back alongside scene read-backs (color maps, centroids, selections) — never trust a PASS without a scene-side assert"
  - "Eager check-detail strings: never call cmd APIs that may throw inside a check detail (build details from already-known data) — one eager count_atoms('pk1') masked a full PART run until fixed"

# Metrics
duration: 27min
completed: 2026-09-09
---

# Phase 3 Plan 04: SMOKE-07 Wizard E2E Summary

**The 03-03 GameWizard is proven end-to-end in real headless PyMOL: a 52-check count-asserted smoke drives activation state, scripted pick routing with recolor + switch-restore semantics and ligand/scratch/empty-space no-ops, baked-transform movement with the identity-matrix invariant re-asserted after every press (including the LIVE R^T camera-convention check against scripted cmd.set_view), the explicit ring-alignment + move_to → confirm composition scoring the scripted π-stacking pose at 1.0 with result text rendered in the live panel/prompt, reset_grid position replay, the full Done restore table (msm snapshot, no pk1, all recolored slots restored, game objects kept, stack empty, idempotent cleanup), and molecule-0 pick scoping — plus a permanent AST source gate banning helper-visual calls in the wizard source; === SMOKE-07 PASS === with zero wizard.py fixes needed.**

## Performance

- **Duration:** ~27 min
- **Started:** 2026-09-09T02:10:41Z
- **Completed:** 2026-09-09T02:37:56Z
- **Tasks:** 2 completed
- **Files modified:** 2 (smoke/smoke_07_wizard_loop.py, tests/test_wizard_source.py — both created)

## Accomplishments

- SMOKE-07 PASS (52/52 checks) on the first post-fix run; **no bugs in aamatch/wizard.py surfaced** — 03-03's implementation survived real-PyMOL field-verification unchanged (the expected Rule-1 fix budget stayed unspent).
- PLAY-01 headless-verified: scripted do_select routes picks to slot identity ('r0c0'/'r0c1'/'r0c2' routed exactly), recolors via HIGHLIGHT_COLOR (all atoms color==green index), restores the previous slot's snapshotted colors on switch (row-exact match), and no-ops ligand/scratch-object/empty-space picks.
- PLAY-02 headless-verified: R^T convention LIVE-VERIFIED against scripted cmd.set_view (dev 2.51e-08 vs a 2.1e-06 float32 tol — the 03-01 single fix site never fired); 3 nudges = exactly 3×NUDGE_STEP world-X (dev 7.8e-09); rotate_view/rotate_axis keep the centroid (devs 6.5e-07/4.3e-07) while moving atoms ~4–5 Å; step_to_ligand lands exactly 1.0 Å toward the ligand centroid (12.900 → 11.900 Å, dev 1.9e-07); object matrix identity after EVERY press (smoke re-asserts).
- PLAY-03 headless-verified: ring alignment via the wizard's own rotate_axis (79.606° → 0.000023°), move_to ring-target drift 2.4e-07, confirm_molecule composes engine.detect + score → 1.0 with 'pi_stacking' formed, result lines render through the LIVE cmd.get_wizard() panel AND prompt, engine._game.molecule_scores == [1.0]; reset_grid replays grid positions (worst 2.9e-07), detect returns 0 records, _result clears, selection + recolor persist.
- PLAY-04 headless-verified: Done (canonical cmd.set_wizard()) restores msm to the snapshot (1, never hard-coded 0), leaves no pk1, restores every recolored slot (row-exact vs pre-recolor snapshots), NEVER deletes the 10 game objects, pops the stack to empty; cleanup() is idempotent. PART E documents molecule-0 scoping (a molecule-1 AA pick leaves _current_slot None); teardown returns the scene to the pre-game snapshot EXACTLY.
- tests/test_wizard_source.py: permanent AST gate scanning every ast.Call site of aamatch/wizard.py for the helper-visual primitives (exactly-2-findings negative control proves the finder fires; Gate-C immune), plus a zero-mention pin for the placement.py banned-token list scoped to the wizard file.

## Task Commits

Each task was committed atomically:

1. **Task 1: helper-visuals source gate (WSL)** — `c2b1c26` (test)
2. **Task 2: SMOKE-07 — the headless E2E wizard loop** — `238b272` (feat)

**Plan metadata:** (this commit) `docs(03-04): complete smoke-07 wizard-e2e plan`

## Files Created/Modified

- `tests/test_wizard_source.py` (created, 147 lines) — AST source gate: find_visual_calls(src) scans all ast.Call sites; PLAY-04 no-helper-visuals made mechanical; SCANNED_MODULES grows as cmd-tier UI modules land (03-05: gamestart.py).
- `smoke/smoke_07_wizard_loop.py` (created, 737 lines) — the 52-check E2E; imports `from aamatch.wizard import GameWizard` (repo module identity); drives engine.new_game/materialize and wizard handlers directly; 5 parts + worst-drift evidence summary; sole verdict carrier `=== SMOKE-07 PASS ===`.

## Decisions Made

- **pk1 lifecycle empirically pinned:** `cmd.unpick()` DELETES the pk1 selection buffer in this build (standalone probe: select pk1 → survives deselect → unpick removes it). do_pick's hygiene unpick therefore consumes pk1 per pick; cleanup()'s pk1 deletion is the defensive guarantee, not the primary path.
- **R^T convention live-verified correct:** only the 3×3 rotation block of the view was scripted (Rz(90°)); the tail was copied verbatim from the captured view (build-dependent, never transcribed by hand). The scripted nudge landed within 2.51e-08 of the hand-computed (0,−1,0)×NUDGE_STEP — wizard_core stays untouched.
- **Color-restore branch recorded:** the preferred sandbox expression `color=m[ID]` (dict subscript) is accepted by this build (probe: restored=True, no exception) — the per-id alter fallback stays available but dormant.
- All other behavior matched the plan exactly (no wizard.py edits).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug, plan-text bug in the smoke expectation] pk1 "present but unpicked" contradicted the live build**
- **Found during:** Task 2 (SMOKE-07 PART A first run)
- **Issue:** The plan specified asserting "'pk1' is present but unpicked (03-03's do_pick leaves pk1 until cleanup deletes it)". The live build proves `cmd.unpick()` deletes the pk1 selection buffer entirely, so do_pick's hygiene unpick consumes pk1 before the assert — `cmd.count_atoms('pk1')` inside the check detail raised "Invalid selection name pk1", cascading PART A (and, transiently, the switch-restored snapshot needed downstream).
- **Fix:** Probe-pinned the semantics (standalone headless probe), then rewrote the smoke asserts to the recorded contract: PART A asserts 'sele' deleted AND 'pk1' absent (consumed by do_pick's unpick); PART D's Done check asserts no pk1 buffer as cleanup's defensive guarantee. wizard.py itself needed NO change — its per-pick hygiene is the correct behavior (measurement.py unpick-after-read pattern); only the plan's expectation was stale.
- **Files modified:** smoke/smoke_07_wizard_loop.py
- **Verification:** probe (unpick_deletes_pk1=True), then `=== SMOKE-07 PASS ===` 52/52; SMOKE-03/04 regressions PASS; 593 WSL tests green.
- **Committed in:** `238b272` (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (Rule 1; against the plan's expectation text, NOT aamatch/wizard.py — the wizard required zero fixes)
**Impact on plan:** None — the wizard went field-verified unchanged; the smoke now records the empirical pk1 contract for all later phases.

## Issues Encountered

- Eager check-detail evaluation: a `cmd.count_atoms('pk1')` inside a check detail string threw on the invalid selection and aborted PART A mid-run, masking later checks. Fixed by keeping details built from already-known data (the corrected assert needs no live cmd call). Recorded as a smoke-authoring pattern.

## User Setup Required

None — no external service configuration required.

## Next Phase Readiness

**03-05 (gamestart) notes:**
- Add `gamestart.py` to `SCANNED_MODULES` in tests/test_wizard_source.py when it lands (the gate is one line to extend).
- The scripted-pick recipe (`cmd.select('sele', '<slot object> and name CA')` + `do_select('sele')`) is proven; reuse it for any headless gamestart smoke.
- activate(replace=1) semantics are untested headless here (single activate only); gamestart owns the restart-or-push decision — a mid-game restart probe belongs in its own smoke if desired.

**For 03-06/03-07 human checkpoints:** only REAL-mouse delivery remains open — arrow-key delivery through the Windows Qt focus path, drag feel, q/e z-sign feel, and the visual recolor/measure-free feedback review. Everything else about the wizard loop is now headlessly proven (52/52) in real PyMOL.

**Blockers:** none carried forward by this plan.

---
*Phase: 03-wizard-gameplay-loop*
*Completed: 2026-09-09*
