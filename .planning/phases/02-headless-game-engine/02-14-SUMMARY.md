---
phase: 02-headless-game-engine
plan: 14
subsystem: cmd-tier-engine
tags: [engine, composition-root, smoke-04, e2e, rotation-invariance, reset-replay, score, game-state, ligand-data, transform-baked, headless]

# Dependency graph
requires:
  - phase: 02-07b
    provides: detector.detect — the complete canonical 7-type surface (NOT detect_part1)
  - phase: 02-08
    provides: generator.generate + the ligand_data {'centroid','radius','profile'} contract (deviation 3) keyed by (set_id, entry_id)
  - phase: 02-09
    provides: geometry.extract_game_atoms / ligand_bonds (probe-pinned bond-position remap) / bounding_sphere + the float32 1e-6 pose rule
  - phase: 02-10
    provides: game_state.score / record_molecule_result (score + formed types in ONE call)
  - phase: 02-13
    provides: placement.materialize / translate_to / transform_baked / reset_to_grid / cleanup_game_objects + the SMOKE-03 ligand_data build pattern (reused verbatim, productionized)
provides:
  - aamatch/engine.py (305 lines) — the headless composition root Phases 3-7 call: new_game / materialize / place_aa / reset_to_grid / detect / score_current / confirm; cmd tier, no Qt
  - smoke/smoke_04_e2e.py (498 lines, 26 checks) — the count-asserted E2E: generate -> materialize -> scripted placement -> detect -> score, rotation invariance, spec-replay reset; ALL PASS in real Windows PyMOL
  - ROADMAP Phase-2 success criterion 4 ([HEADLESS] E2E) — GREEN
affects: [phase-3 (Confirm handler = engine.confirm wrapper), phase-4 (Cleanup wiring over cleanup_game_objects), phase-6 (Reset = engine.reset_to_grid), phase-7 (runtime-state sidecar wraps the engine's GameState), 02-15 (final audit/perf stamp)]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "engine module-level runtime (_payload/_registry/_game) with the state-split rule in the docstring: spec payload = single source of truth, runtime in GameState, PyMOL holds atoms + sentinels only; a new game resets the GameState and invalidates the registry"
    - "bond-block remap productionized as engine._remap_ligand_bonds keyed by (object, id) — the multi-ligand generalization of SMOKE-03's smoke-local helper; bond position i -> index_to_id[i+1] -> atom id -> position in the (object, id)-sorted ligand records"
    - "scene-hygiene assert across new_game: the object-name list is snapshot-compared before/after (temp ligand loads must never leak) — EngineError names the leaked temp"
    - "scripted aromatic placement = optional baked normal alignment (transform_baked Rodrigues about the ring center) + ring-center-delta translate (place_aa) — orientation handled explicitly, never assumed"
    - "rigid-transform invariance proof shape: structural record identity (types/objects/ids/roles) byte-equal EXACTLY + numeric metric drift inside a documented float32 budget (5e-6 A distances / 3e-4 deg angles), worst drift printed"

key-files:
  created: ["aamatch/engine.py", "smoke/smoke_04_e2e.py"]
  modified: []

key-decisions:
  - "detect() composes geometry.extract_game_atoms() + geometry.ligand_bonds per registered ligand object (probe-pinned remap) -> detector.detect (the 7-type surface, NOT detect_part1) — the identical wiring the Phase-3 Confirm handler will reuse"
  - "score_current records into the module-level GameState via record_molecule_result (score + formed types in ONE call; formed_types_per_molecule keyed 'L{m}M{n}') and returns (score, formed_types) as plain data"
  - "new_game accepts an optional candidates override — SMOKE-04 restricts to the benzamide row so block_exclusive stays deterministic-by-construction (SMOKE-03 precedent); the default path parses MANIFEST.json and filters by demo_set_id when set"
  - "seed-agnostic scripted placement: the required slot's resn is read FROM the slot (seed 42 drew TYR) and ring centers/normals come from detector.extract_features — the same feature layer detect() itself consumes"

patterns-established:
  - "confirm() = detect + score_current composition returning (records, score, formed_types) — the exact shape the Phase-3 Confirm handler wraps; no Qt anywhere in the chain"

# Metrics
duration: 16 min
completed: 2026-09-06
---

# Phase 2 Plan 14: Headless Engine + SMOKE-04 Summary

**The headless engine (`aamatch/engine.py`, 305 lines) is the composition root for the whole phase — new_game / materialize / place_aa / reset_to_grid / detect / score_current / confirm over the pure generator/detector/scoring + cmd placement/geometry, no Qt anywhere — and SMOKE-04 proves the full generate -> place -> detect -> score loop in real Windows PyMOL: 26/26 checks PASS including whole-scene rotation invariance (structural record set byte-equal; metric drift 2.6e-9 A / 0.0 deg) and spec-replay reset (grid poses restored within 2.9e-07 of spec, score back to 0.0, teardown exact to the pre-game snapshot). ROADMAP Phase-2 criterion 4 ([HEADLESS] E2E) is GREEN; WSL suite 507/507; SMOKE-02/03 still PASS.**

## Performance

- **Duration:** 16 min
- **Started:** 2026-09-06T17:57:59Z
- **Completed:** 2026-09-06T18:13:56Z
- **Tasks:** 3/3
- **Smoke verdict:** `=== SMOKE-04 PASS ===` (26/26 checks) — PARTS A/B passed first run (with the pre-planned alignment bake); PART C passed first run

## Test Counts + Smoke Verdicts

- WSL suite: `python3.6 -m py_compile aamatch/*.py` clean; `python3.6 -m unittest discover -s tests -v` — **507/507 OK** (engine.py is cmd-tier: Gate D compiles it; purity registry untouched at 13 modules)
- Headless: `bash smoke/run_smoke.sh smoke/smoke_04_e2e.py 240` — **`=== SMOKE-04 PASS ===`** (26/26)
- Regression: `smoke_03_generate.py` — **`=== SMOKE-03 PASS ===`** (28/28); `smoke_02_manifest.py` — **`=== SMOKE-02 PASS ===`**

## Task Commits

| Task | Name | Commit | Files |
| --- | --- | --- | --- |
| 1 | engine.py — headless operation set | d5a7bda | aamatch/engine.py |
| 2 | SMOKE-04 parts A+B (happy path + rotation invariance) | 3048ede | smoke/smoke_04_e2e.py |
| 3 | SMOKE-04 part C (reset replay + full gate) | d6651dc | smoke/smoke_04_e2e.py |

## What Was Built

- **`engine.new_game(setup, seed, candidates=None)`** — manifest parse (read_json_file + parse_manifest_dict + enumerate_entries; demo_set_id filter when set), per-candidate ligand_data built the SMOKE-03 way (`_aam_tmp` load -> extract -> bounding_sphere + capability.ligand_profile over the remapped get_bonds block -> `{'centroid','radius','profile'}` keyed by (set_id, entry_id), temp deleted in a finally, object list asserted unchanged), then `generator.generate`. Resets the module GameState and invalidates any old registry.
- **`engine.detect()`** — extract_game_atoms + per-ligand get_bonds with the probe-pinned remap (position i -> index_to_id[i+1] -> id -> position in the (object, id)-sorted ligand records; generalized to multi-ligand registries by keying the map on (object, id)) -> `detector.detect` (the 7-type surface).
- **`engine.score_current` / `confirm`** — game_state.score via record_molecule_result (score + formed types stored together in the module GameState); confirm = detect + score composition returning (records, score, formed_types).
- **SMOKE-04 PART A (happy path):** block_exclusive ['pi_stacking'], molecules 1, D 3, seed 42 -> payload (levels 3, n 3, slots 9, required list/pi_stacking x1) -> materialize (growth exactly 10) -> grid detects zero records and scores 0.0 -> the required slot (seed-agnostic: seed 42 drew **TYR**, slot r0c2) placed with its ring 4.5 A directly above the benzamide ring center (`d_center` 4.5000, `offset` 2.865e-07, `angle_deg` 0.0000, subtype **P**) -> exactly 1 pi_stacking record on the placed object -> score 1.0.
- **SMOKE-04 PART B (rotation invariance):** `cmd.rotate('z', 37.0, <all 10 game objects>, camera=0, origin=ligand ring center)` bakes the whole scene; re-detect: record set structurally byte-equal (types/objects/ids/roles), metric drift worst 2.61e-9 (distances) / 0.0 deg (angles) vs the documented float32 budgets (5e-6 A / 3e-4 deg); score stays 1.0.
- **SMOKE-04 PART C (reset replay):** engine.reset_to_grid() re-bakes every AA to its spec grid pose (worst 2.9e-07 vs 1e-6 tolerance); detect returns zero pi_stacking records (grid beyond the gap) and score_current returns 0.0; cleanup deletes exactly 10 objects and the scene equals the pre-game snapshot exactly.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Plan-text bug] The plan's scripted pose assumed parallel ring normals**

- **Found during:** Task 2 implementation (design-time, confirmed live: the seed-42 required AA is TYR and its materialized fragment's natural ring-normal line angle vs the benzamide ring is **79.606 deg**)
- **Issue:** the plan scripts a pure translate (`place_aa` so the ring center lands 4.5 A above the ligand ring center) and asserts "normals parallel" — translation preserves orientation, and a chempy fragment's ring plane is in no guaranteed orientation. At 79.6 deg the natural geometry is inside NEITHER the parallel (<= 30 deg) NOR the perpendicular (>= 60 deg) window, so the plan's pose as written would have formed NOTHING.
- **Fix:** the smoke computes both ring normals from `detector.extract_features` (the same feature layer detect() consumes); when the line angle exceeds PISTACK_ANGLE_TOL_DEG it bakes a Rodrigues alignment (`placement.transform_baked`, rotation about the AA ring center) before the translate — 79.606 -> 0.000023 deg. The plan's translate-only path is kept as the fast path when the natural plane already qualifies. This is seed-robust for all four aromatic AAs.
- **Files modified:** smoke/smoke_04_e2e.py (`_alignment_matrix` + the alignment step)
- **Commit:** 3048ede

**2. [Rule 1 - Plan-text imprecision] Part B uniform "metrics within 1e-6" is not float32-realizable for angular metrics**

- **Found during:** Task 2 design
- **Issue:** PyMOL stores coordinates as float32 (02-09). A baked rotation re-stores every atom; distance metrics can drift a few e-6 and angle metrics (unit-normal recomputation from the re-stored coords, then acos) can drift ~1e-6 rad ~ 6e-5 deg. A single 1e-6 assert on ALL metrics would fail on physics, not on a leak.
- **Fix:** Part B asserts the structurally meaningful part EXACTLY (record-set identity: types/objects/ids/roles byte-equal) and numeric drift against documented float32 budgets — distances/offsets <= 5e-6 A, angles <= 3e-4 deg — with the worst observed drift printed for audit (observed: 2.61e-9 A / 0.0 deg, orders of magnitude inside budget). The float32-budget rationale lives in the smoke docstring.
- **Files modified:** smoke/smoke_04_e2e.py (drift budget + docstring)
- **Commit:** 3048ede

### Additive API notes (not plan-breaking)

**3. [Rule 2 - Missing Critical] `new_game` needs a way to enroll a deterministic candidate list**

- **Issue:** SMOKE-03 established that `block_exclusive` + the mixed 2-entry dev manifest is seed-fragile (a coin-flip acetate pick makes the setup refuse); SMOKE-03 avoided it by restricting candidates by hand. The plan's fixed `new_game(setup, seed)` surface had no equivalent, which would have forced the smoke off the engine ops (violating its own E2E contract).
- **Fix:** optional additive kwarg `candidates=None` (default parses MANIFEST.json / demo_set_id filter exactly as planned); the smoke passes `[benz]`. Also generalized the SMOKE-03 bond remap to multi-ligand registries (keyed by (object, id)) as the productionized home `engine._remap_ligand_bonds`.
- **Commit:** d5a7bda

### Plan Notes Followed Beyond Letter

- Slot discovery is resn-agnostic (`role == 'required'` + `'pi_stacking' in can_form`, exactly one such slot asserted) — seed 42 actually produced TYR, not the PHE the plan sketched; the script would have been wrong had it hard-coded PHE.
- Ring centers come from `detector.extract_features` rings (capability ring typing + row-9 geometry) — functionally the plan's "capability typing on records + bonds -> ring atom indices -> mean their coords", and additionally supplies the normals the alignment step and the 30-deg window need.
- No reconciliation edits to any existing module were needed; the allowed file set was respected (engine.py + smoke_04_e2e.py only).

## Authentication Gates

None.

## Next Phase Readiness

- **Phase 3 Confirm** wraps `engine.confirm(level_index, molecule_index, required)` verbatim; **Phase 6 Reset** is `engine.reset_to_grid()`; cross-level staging re-materializes from the payload per level.
- **02-15 (final audit/perf):** engine.py is cmd-tier like geometry/placement (Gate D compiles it; never in PURE_MODULES); SMOKE-05 inherits the same engine/geometry surfaces.
- **Banned-call audit:** engine.py + smoke_04_e2e.py contain no matrix_reset/get_object_ttt calls; SMOKE-04's Part C retirees the last "reset via matrix" temptation by proving spec replay end-to-end with score recovery.
- **GameState sidecar (Phase 7):** the engine's module-level `_game` already holds per-molecule scores + formed types in `to_dict`-lossless shape.
