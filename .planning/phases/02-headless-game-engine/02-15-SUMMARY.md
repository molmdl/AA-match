---
phase: 02-headless-game-engine
plan: 15
subsystem: perf-audit-gates
tags: [smoke-05, perf, detect-05, code-audit, ast, cross-pairs, brute-force-oracle, banned-calls, detector-version, stamp-gate, float32, max-grid, headless]

# Dependency graph
requires:
  - phase: 02-03
    provides: manifest.largest_entry over enumerate_entries — the perf-target selector (max heavy_atom_count, ties-first)
  - phase: 02-06/02-07b
    provides: detector.detect (7-type surface) routing ALL candidates through spatial.cross_pairs; brute_force_pairs test-oracle-only
  - phase: 02-10/02-08
    provides: generator payload carrying detector_version + format_version stamps via level_spec
  - phase: 02-13/02-14
    provides: placement/geometry/engine cmd-tier surfaces; SMOKE-04's proven pi_stacking scripted-placement recipe (alignment bake + 4.5 A ring translate) and float32 budget vocabulary
provides:
  - smoke/smoke_05_perf.py (401 lines, 23 checks) — HEADLESS DETECT-05 proof on the largest bundled molecule + tier-9 9x9 grid: extract 16.7–21 ms / detect 0.0 ms / 1285 atoms vs the REAL budgets (detect < 100 ms, extract+detect < 1000 ms) + the stale-stamp parse-gate refusal
  - tests/test_code_audit.py (377 lines, 10 tests) — the permanent mechanical vectorization/pruning audit (ROADMAP Phase-2 criterion 5's machine half)
  - ROADMAP Phase-2 success criterion 5 — GREEN; Phase 2 (headless game engine) COMPLETE, all 5 criteria demonstrated
  - fix(02-15): placement._assert_pose is float32-realizable (1e-6 floor + per-axis ulp slack) — max-grid materialization can no longer raise on a legitimate rounding
affects: [phase-3 (pose scripting keeps engine surfaces; max-grid games are now bake-safe), phase-4 (cleanup/materialize at D=10 tier-9), 02-15 audit extends: any new aamatch module is automatically scanned for banned calls/prose drift]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "real-vs-WSL budget split pinned mechanically: the <100 ms DETECT-05 detect budget is headless-only (SMOKE-05 local literals); the WSL 2.0 s loose guard (tests/test_detector_invariance.py) never leaks into the smoke gate"
    - "AST audit over grep audit: banned-cmd-call gate walks ast.Call nodes (docstring prohibition prose is a string constant by construction — Gate-C immune); prose mentions are separately pinned by EXACT per-(file,token) count so drift demands human re-review, never blind-fail"
    - "negative controls for every custom AST finder (test_purity.py pattern): per-atom-pair traps and points_a x points_b traps must fire; the legitimate packing shape (objects x one-object-atoms) is pinned as NOT flagged"
    - "float32-realizable absolute+relative tolerance: POSE_TOLERANCE floor + FLOAT32_ULP_REL * max(|actual|,|target|) per axis — 'never looser' is now 'tighter than the floor is impossible BY STORAGE, not by choice'"

key-files:
  created: ["smoke/smoke_05_perf.py", "tests/test_code_audit.py"]
  modified: ["aamatch/placement.py"]

key-decisions:
  - "Nested-pair-loop audit semantics: flag only when BOTH nested loops iterate atom/record namespaces (underscore-split token rule) — _atom_candidate_pairs' linear packing pass (outer over objects feeding one object's atoms into cross_pairs) is the detector's required input assembly, never a per-atom-pair walk; the plan's substring-shaped rule would have flagged this legitimate pattern and detector.py was out of the allowed file set"
  - "POSE_TOLERANCE becomes floor+ulp after SMOKE-05 proved tier-9 (9x9, |coord|~32.9 A) slots ROUND past a fixed 1e-6 by storage (observed 1.24e-6 on a legitimate bake; 1 ulp at 32.9 A ~ 2.4e-6) — consistent with 02-14's recorded not-float32-realizable metric-assert decision; all regression smokes (01-04) still PASS"
  - "Timing stays plan-litteral (stdlib time.time, 3 decimals): Windows clock granularity (~15.6 ms tick) makes detect read 0.000 ms — the detector truly answers sub-ms after the AA prefilter empties candidate space on a wide grid; extract stage (16.7-21 ms) carries the wall"

patterns-established:
  - "SMOKE-05 shape: manifest-driven largest_entry target => D=10 last-tier materialize (82 objects exact) => scripted placement => ONE timed extract/detect pass with per-stage assert budgets => stamp-gate round trip (fresh parse positive control + stale re-stamp refusal) => exact teardown"
  - "audit test file contract: pure (ast+os+sys+unittest), fast (~0.5 s), zero imports of aamatch, negative controls proving every finder can FIRE"

# Metrics
duration: 29 min
completed: 2026-09-07
---

# Phase 2 Plan 15: Headless Perf Smoke + Code Audit (DETECT-05) Summary

**DETECT-05 is CLOSED headlessly: SMOKE-05 builds the largest bundled molecule (benzamide via `manifest.largest_entry`) with the tier-9 9x9 max grid (82 objects, count-exact), forms a scripted pi_stacking, and the timed pipeline runs extract=16.7–21 ms / detect=0.0 ms over 1285 atoms — orders of magnitude inside the REAL headless budgets (detect < 100 ms, extract+detect < 1000 ms) — while a `'det-0'` re-stamped deep copy of the payload is refused by the exact-match parse gate ("stale or newer — regenerate"). The permanent AST audit (`tests/test_code_audit.py`, 10 tests, ~0.5 s) mechanically pins cross_pairs routing, brute_force_pairs oracle isolation, the no-naive-pair-loop bans (with firing negative controls), and zero call sites for get_model / matrix_reset / get_object_ttt. Phase 2's fifth and final ROADMAP criterion is GREEN — the headless game-engine phase is COMPLETE (531 WSL tests, 5/5 smokes).**

## Performance

- **Duration:** 29 min
- **Started:** 2026-09-07T03:14:10Z
- **Completed:** 2026-09-07T03:43:57Z
- **Tasks:** 3/3
- **Smoke verdict:** `=== SMOKE-05 PASS ===` (23/23 checks, first run after the tolerance fix; re-run after the full battery also PASS)

## Test Counts + Smoke Verdicts

- WSL suite: `python3.6 -m py_compile aamatch/*.py` clean; `python3.6 -m unittest discover -s tests -v` — **531/531 OK** (521 baseline + 10 audit), 32 s
- Headless battery (generalized runner, Windows PyMOL 2.5.0 / Python 3.9.13):
  - `=== SMOKE-01 PASS ===`, `=== SMOKE-02 PASS ===` (regression of the placement tolerance change)
  - `=== SMOKE-03 PASS ===`, `=== SMOKE-04 PASS ===` (regression: small-magnitude scenes keep 1e-6 base behavior)
  - `=== SMOKE-05 PASS ===` (23/23) — perf: `SMOKE-ENV perf extract_ms=17 detect_ms=0 atoms=1285` (re-run: extract 21 ms)

## Task Commits

| Task | Name | Commit | Files |
| --- | --- | --- | --- |
| 1 | Mechanical code audit (AST test) | 4923eb8 | tests/test_code_audit.py |
| 2 | float32-realizable pose tolerance (deviation fix) | de286f9 | aamatch/placement.py |
| 2 | SMOKE-05 perf smoke + stamp gate | e187290 | smoke/smoke_05_perf.py |

## What Was Built

- **`tests/test_code_audit.py`** (10 tests, 377 lines, pure ast+os+sys+unittest): (1) **cross_pairs routing** — detector.py imports AND calls `cross_pairs` (import alone proves nothing); (2) **oracle isolation** — `brute_force_pairs` exists with its 'test oracle' docstring and has ZERO call/import sites anywhere in `aamatch/` or `smoke/`; (3) **no naive pair loops** — detector.py has no nested For pair in which BOTH loops iterate atom/record namespaces, and `cross_pairs` itself has no full `points_a × points_b` double loop (the 3x3x3 dx/dy/dz constants-scan is the only legal nesting); both finders carry negative controls that must FIRE plus a pinned NOT-flagged proof for the legitimate objects×one-object-atoms packing shape; (4) **banned cmd calls** — `get_model` / `matrix_reset` / `get_object_ttt` have zero `ast.Call` sites anywhere (docs are string constants, Gate-C immune), with prose mentions pinned exactly per (file, token): placement.py matrix_reset ×3 + get_object_ttt ×1, engine.py matrix_reset ×2, geometry.py get_model ×1.
- **`smoke/smoke_05_perf.py`** (23 checks, 401 lines): manifest-driven largest_entry target (benzamide, heavy=9, selected programmatically from 2 entries) → D=10 game (10 levels built) → tier-9 9x9 grid materialized (82 objects exact) → seed-agnostic required pi_stacking slot (seed 7 drew HIS at r1c6; natural line angle 7.718° ≤ 30°, no alignment bake needed; ring landed at drift 3.8e-07) → timed extract (geometry.extract_game_atoms + engine._remap_ligand_bonds wall: 16.7–21 ms) and detect (0.0 ms) with per-stage 3-decimal prints and the single-line `SMOKE-ENV perf` record → ≥ 1 pi_stacking on the placed object → stamp gate: fresh payload `detector_version 'det-1'` parses (positive control returns all 10 tiers), `'det-0'` deep-copied re-stamp refused with `FormatError: unsupported detector_version 'det-0' … stale or newer game spec - regenerate it with a current AA-match generator` → exact teardown (82 deleted, scene == pre-game snapshot).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug / outside allowed file set, required for the gate] `placement._assert_pose`'s fixed 1e-6 is physically unattainable on the tier-9 max grid**

- **Found during:** Task 2 first SMOKE-05 run — 9x9 materialization raised `PlacementError` at slot r1c8: baked centroid 32.9387512207 vs target 32.9387499839, drift **1.24e-6** > 1e-6
- **Issue:** float32 ulp at |coord| ≈ 32.9 Å is ~2.4e-6, so a fixed 1e-6 assert is *below one quantum of the storage format* on max-grid slots — no correct bake can satisfy it. Smaller grids (SMOKE-03/04, ≤ ~15 Å) never bound this, so the defect stayed dormant; SMOKE-05's max-grid materialization was the first headless exercise of the path, and failing it would have silently capped playable difficulty below tier 9 in the GUI phases. Placement.py was outside the plan's `files_modified`, but the deviation rules make correctness fixes automatic and the alternative (weakening anything in the smoke) was expressly forbidden by the plan.
- **Fix:** single-site change in `_assert_pose` — per-axis tolerance = `POSE_TOLERANCE` (1e-6 absolute floor) + `FLOAT32_ULP_REL` (1.1920929e-7, one float32 ulp relative) × max(|actual|, |target|). At 32.9 Å the assert allows ~4.9e-6 (the rounding class observed); at ≤ 15 Å the previous behavior is within slack and all four regression smokes (01–04) PASS on re-run. Same precedent as 02-14's recorded decision that uniform 1e-6 metric asserts are not float32-realizable.
- **Files modified:** aamatch/placement.py (constant + docstring truthfulness updates; "never looser" rephrased as "tighter than the floor is impossible BY STORAGE")
- **Commit:** de286f9

**2. [Rule 1 - Plan-text bug] The audit's nested-loop rule (substring scan for 'atom'/'record') flags the detector's required input assembly**

- **Found during:** Task 1 verification — first audit run reported `_atom_candidate_pairs (line 642): inner loop over _pair_atoms`
- **Issue:** the plan's pragmatic rule ("any ast.For whose body contains another ast.For whose iter mentions 'atoms' or 'records'") matches `for obj in near_objs: for rec in _pair_atoms(features, obj)` — the LINEAR packing pass that assembles cross_pairs' a-side points. Outer iter is objects, inner iter is one object's atoms; this is the pipeline's **intended** shape, not a per-atom-pair walk, and detector.py was off-limits (files discipline), so the plan's own remedy (rename/refactor) was unreachable.
- **Fix:** token-pair semantics in the audit: a namespace is record-ish only when an underscore-split identifier token is atom/atoms/rec/recs/record/records, and the pair is flagged only when BOTH loops iterate such namespaces. The gate now matches the true naive shape exactly; the audit file documents the distinction and pins it with a NOT-flagged negative control (`PACKING_SHAPE_OK`) plus the two firing traps.
- **Files modified:** tests/test_code_audit.py
- **Commit:** 4923eb8

### Plan Notes Followed Beyond Letter

- Budget literals are SMOKE-05-local constants (`DETECT_BUDGET_MS`, `TOTAL_BUDGET_MS`); the WSL-only `WSL_PERF_GUARD_SECONDS = 2.0` from `tests/test_detector_invariance.py` was never imported, per the next-actions binding note and the plan's warning.
- Seed-agnostic placement: seed 7 drew HIS (not PHE/TYR); the same feature-layer ring discovery handled it without any alignment bake (natural line angle 7.718°), leaving the bake path exercised-but-dormant just as in SMOKE-04's design.
- Stale stamp chosen as `'det-0'` (bumped DOWN by 1 from the live `'det-1'`), per the plan text; the orchestrator note said "bumped by 1" — both directions are refused by the exact-match gate, and the refusal message text ("stale or newer") is asserted verbatim.

## Authentication Gates

None.

## Next Phase Readiness (Phase 3 — wizard interaction)

- **Phase 3 spawn notes (binding):** Confirm handler = `engine.confirm(...)` wrapper; Reset = `engine.reset_to_grid()`; pose scripting/hints must include the baked ring-alignment step when needed (02-14 decision) — SMOKE-05 is the reference implementation of the seed-agnostic ring discovery.
- **Max-grid games are now bake-safe:** the `_assert_pose` fix removes the only known float32 blocker at tier 9/10 (81–100+ atom slots at |coord| ≥ 33 Å); Phase 4's cross-level staging at high difficulty inherits it.
- **The audit suite runs against any future module automatically:** `aamatch/*.py` and `smoke/*.py` are re-scanned every suite run for banned-call sites and prose-pin drift — new docstring mentions require a deliberate PROSE_PIN update (human re-review by construction).
- **Phase 2 — COMPLETE:** all five ROADMAP criteria demonstrated (pure foundation gates 531 tests green; manifest+generator invariants; detector 7-type property battery; SMOKE-04 E2E; SMOKE-05 perf/audit/stamp). Next: orchestrator's phase verifier, then Phase 3 spike (movement model: `cmd.drag(wizard=0)` / `editor_scheme` — still UNVERIFIED, listed in carried concerns).
- **Carried concern closed:** none new. Still open: Phase-7 `.pse` matrix round-trip smoke before committing checkpoint design; Phase-3 movement-model spike.
