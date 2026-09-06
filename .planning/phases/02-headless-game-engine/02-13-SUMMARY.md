---
phase: 02-headless-game-engine
plan: 13
subsystem: cmd-tier-materialization
tags: [placement, materialize, smoke-03, sentinels, baked-coordinates, spec-replay, fragments, registry, ligand-profile, e2e]

# Dependency graph
requires:
  - phase: 02-04
    provides: script-built fixtures + MANIFEST.json (benzamide 16 atoms / 16 bonds {"1":12,"2":4}) + SMOKE-02 conventions
  - phase: 02-05
    provides: capability.AA_TOKENS (the ONE generator-token -> fragment/resn vocabulary) + ligand_profile
  - phase: 02-08
    provides: generator.generate payload (serialized poses, placement.offset) + the ligand_data {'centroid','radius','profile'} CONTRACT (deviation 3)
  - phase: 02-09
    provides: geometry.extract_game_atoms / ligand_bonds (index-map remap) / bounding_sphere / coords_of / centroid_of + the float32 1e-6 pose rule
provides:
  - aamatch/placement.py — cmd-tier materializer: materialize/reset_to_grid/translate_to/transform_baked/cleanup_game_objects + PlacementError; the Phase-2 "bake coordinates, never matrices" rule with the banned-call list in the docstring
  - the sentinel + reserved-prefix conventions LIVE-proven in real PyMOL (segi='AAM' + b=-999.0, '_aam_lig'/'_aam_aa' naming, pre_game_names snapshot) for Phase 4 Cleanup and Phase 7 reconstruction
  - smoke/smoke_03_generate.py — count-asserted generate+materialize smoke (28 checks, all PASS)
affects: [02-10 (engine.new_game/materialize), 02-14 (E2E: translate_to/transform_baked scripted placement), 02-15 (audit of banned calls), phase-3 picking/drag setup, phase-4 Cleanup, phase-7 sentinel-first reconstruction]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "cmd-tier module house rule: pymol.cmd imports legal in placement.py/geometry.py; NEVER added to PURE_MODULES; Gate D (py_compile) is the WSL coverage; behavior proven by Windows-PyMOL smokes"
    - "count+pose assert after EVERY mutating cmd call (count_atoms >= 1 after creation; centroid within 1e-6 after every translate) — fail-closed at the step, never downstream"
    - "registry = slot_id -> (object_name, sorted atom ids) + pre_game_names snapshot — the identity map Phase 7's sidecar reconciles against"
    - "reset = spec REPLAY (re-bake from CURRENT pose to spec grid pose), never matrix_reset (probe-proven reverter)"

key-files:
  created: ["aamatch/placement.py", "smoke/smoke_03_generate.py"]
  modified: []

key-decisions:
  - "materialize(payload, level_index=0) materializes ONE level at a time (the game's current level) — a D=3 payload stays the source of truth; cross-level staging is Phase 4 flow"
  - "slot['aa'] (uppercase RESN from the generator) is resolved to fragments via a reverse index derived from capability.AA_TOKENS at import — the token table stays the ONE vocabulary (DETECT-04), never a re-transcribed mapping"
  - "ligand objects get a unique get_unused_name('_aam_lig') every time and are sentinel-tagged exactly like AAs (segi='AAM', b=-999.0) — the game-materialized ligand is cleanup-deletable by prefix; user-adopted ligands (never prefixed) are a Phase 4 flow"
  - "SMOKE-03 restricts the candidate list to the benzamide row: block_exclusive ['pi_stacking'] refuses (correctly) on aromatic-ring-less molecules, so passing both manifest entries would make the smoke seed-fragile — deterministic by construction, the diversity proof stays with SMOKE-02"
  - "PlacementError subclasses ValueError and every message NAMES the cause (object, slot, expected vs actual) — house fail-closed style"

patterns-established:
  - "SMOKE-03 ligand_data build pattern (SMOKE-04/05 + 02-10/02-14 must follow): temp _aam_tmp load -> geometry.extract_game_atoms (side=='lig') -> geometry.bounding_sphere + capability.ligand_profile over remapped get_bonds -> {'centroid','radius','profile'} -> temp deleted in a finally"
  - "get_bonds 0-based walk-position -> sorted-record remap helper (index_to_id[pos+1] -> id -> position in the (object,id)-sorted ligand records) — duplicated in smoke_local code, productionized by 02-10"

# Metrics
duration: 20 min
completed: 2026-09-06
---

# Phase 2 Plan 13: Placement + SMOKE-03 Summary

**Cmd-tier materializer (`aamatch/placement.py`, ~370 lines) + SMOKE-03: payload -> real PyMOL objects with sentinel/identity conventions and count+pose-asserted baked placement — 28/28 smoke checks PASS in real Windows PyMOL (object growth exactly 1+9=10, sentinels 174/174, spec pose worst 3.3e-07 vs 1e-6 tolerance, `unclassified_aa_atoms` == 0, reset-replay worst 2.9e-07, teardown exact to pre-game snapshot); WSL suite 438/438 green.**

## Performance

- **Duration:** ~20 min
- **Started:** 2026-09-06T16:52:00Z
- **Completed:** 2026-09-06T17:12:56Z
- **Tasks:** 3/3 (Tasks 1+2 = one same-file commit; Task 3 = smoke commit)
- **Smoke verdict:** `=== SMOKE-03 PASS ===` (28/28 checks) — first run, no reconciliations needed

## Accomplishments

- **`materialize(payload, level_index=0)`** creates exactly `1 + n*n` objects per molecule: ligands via `cmd.load(to_windows_path(package_data_path('data', file)))` into fresh `_aam_lig` names (never load-into-existing — the appends-a-state hazard), AAs via `cmd.fragment(AA_TOKENS[token]['fragment'])` into fresh `_aam_aa` names. Every atom sentinel-tagged (`segi='AAM'`, `b=-999.0` + `cmd.sort`); registry records `(object, sorted ids)` + the `pre_game_names` snapshot. Every creation count-asserted; every baked translate pose-asserted within 1e-6.
- **`reset_to_grid`** = spec REPLAY: each AA re-bakes from its CURRENT pose to the spec effective pose — never `matrix_reset` (probe-proven reverter). **`translate_to`/`transform_baked`** are the baked-move primitives SMOKE-04's scripted placement and Phase 3's game-driven moves build on, with the assert-coordinates-never-get_object_matrix discipline in the docstrings.
- **`cleanup_game_objects`** deletes the `_aam_` prefix set ONLY (no chemical filters) and returns `{'deleted': n}`.
- **SMOKE-03 (28 checks, all PASS):** manifest parsed inside PyMOL; ligand_data built per the 02-08 deviation-3 contract (bounding sphere (0.939, -0.208, 0.000)/R=3.742 + full `capability.ligand_profile`, ring_count=1); `generate(seed=42, block_exclusive ['pi_stacking'])` -> parse-gate round-trip identity inside PyMOL; object growth 10/10; sentinel coverage 174/174 (`b < 0 and segi AAM` selects all); spec pose agreement worst 3.3e-07; live-detector `unclassified_aa_atoms` == 0 over the 9 materialized fragments (capability atom naming field-VERIFIED — no reconciliation needed); translate_to + transform_baked perturbations land per-atom within 1e-6; reset_to_grid replay worst 2.9e-07; cleanup deletes exactly 10 and the scene equals the pre-game snapshot exactly.

## Task Commits

1. **Tasks 1+2:** `b391a34` — `feat(02-13): placement.py — materialize + registry, baked-move primitives`
2. **Task 3:** `44ee3fa` — `test(02-13): SMOKE-03 count-asserted generate + materialize`

## Test Counts + Smoke Verdicts

- WSL suite: `python3.6 -m py_compile aamatch/*.py` OK; `python3.6 -m unittest discover -s tests -v` — **438/438 OK** (placement.py is cmd-tier and enters via Gate D compile only; baseline grew from the 423 recorded for 02-08 because the worktree base e475fd6 carries the full wave-6 merge set)
- Headless: `bash smoke/run_smoke.sh smoke/smoke_03_generate.py 180` — **`=== SMOKE-03 PASS ===`** (28/28 checks)

## Files Created/Modified

- `aamatch/placement.py` — materialize / reset_to_grid / translate_to / transform_baked / cleanup_game_objects / effective_position + PlacementError; module docstring carries the Phase-2 bake rule + the banned-call list (`matrix_reset`, `get_object_ttt`, create-onto-existing, load-into-existing)
- `smoke/smoke_03_generate.py` — the count-asserted SMOKE-03 (~415 lines incl. docstring contract notes)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Tasks 1 and 2 committed as ONE commit**

- **Found during:** implementation
- **Issue:** `materialize` consumes `translate_to`-equivalent logic for slot placement, so Task 1 and Task 2 land in the same creation of the same file and cannot be split into two honest commits without staging word-soup.
- **Fix:** single `feat(02-13)` commit naming both tasks; the RED/GREEN ritual belongs to plans with test files (placement is cmd-tier — its proof is SMOKE-03).
- **Files modified:** none extra
- **Commit:** `b391a34`

### Plan Notes Followed Beyond Letter

- The plan's "n=3 -> 10 objects" growth assertion is realized as `materialize(payload, level_index=0)` (D=3 payload, level 0 grid_n=3): one-level-at-a-time materialization is the documented game-flow model.
- SMOKE-03's candidate list is restricted to the benzamide row (documented in the smoke docstring) — `block_exclusive ['pi_stacking']` correctly refuses aromatic-less molecules, and a coin-flip acetate pick would make the smoke seed-fragile.
- **No capability/detector reconciliation was needed:** the materialized chempy fragments classify 100% against capability's atom naming (`unclassified_aa_atoms` == 0) — the pre-authorized "extend _KNOWN_NON_SIDE_CHAIN" escape hatch stayed unused; detector.py and capability.py are untouched.

## Next Phase Readiness

- 02-10 (engine): productionize the smoke's ligand_data build + bond remap (currently smoke-local helpers) behind `new_game`; wire `bounding_sphere` + `ligand_profile` into `generate` per the keyed (set_id, entry_id) form.
- 02-14 (SMOKE-04): scripted placement consumes `translate_to`/`transform_baked`; rotation-invariance Part B bakes whole-scene rotates with `camera=0`.
- Phase 4 Cleanup: `cleanup_game_objects` + `pre_game_names` snapshot are the convention proof; the button adds user-object atom-count asserts.
- Banned-call audit for 02-15: `grep -n "matrix_reset\|get_object_ttt" aamatch/` must return hits only inside placement.py's docstring prohibition list.
