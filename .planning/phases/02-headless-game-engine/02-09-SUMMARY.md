---
phase: 02-headless-game-engine
plan: 09
subsystem: geometry-bridge
tags: [pymol, cmd-tier, iterate_state, get_bonds, detector-contract, bounding-sphere, world-frame]

# Dependency graph
requires:
  - phase: 02-04
    provides: benzamide.sdf fixture (16 atoms / 16 bonds {1:12, 2:4}, charge 0) + MANIFEST.json + to_windows_path/package_data_path load recipe
  - phase: 02-06
    provides: the detector record contract (side/object/id/name/elem/resn/resi/alt/formal_charge/x/y/z) + detector.detect consuming records + [(i,j,order)] bond block
  - phase: 01-04
    provides: to_windows_path guard (every cmd.load routes through it; geometry itself does no file I/O)
provides:
  - aamatch/geometry.py — the ONE cmd-tier extraction boundary: extract_game_atoms (detector-contract records), ligand_bonds (0-based block + index→id map), bounding_sphere (generator ligand_data), coords_of/centroid_of (pose-assertion helpers)
  - probe-proven semantics: record field types (int resi via resv), get_bonds position→index-property mapping (i+1), float32 pose-assert tolerance (1e-6)
affects: [02-10 (engine detect()/ligand_data wiring), 02-13 (SMOKE-03), 02-14 (SMOKE-04/05 E2E), phase-3 wizard confirm]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "cmd-tier boundary module: `from pymol import cmd` at module level, NEVER in PURE_MODULES (Gate D compiles it; Gates A/B ignore it)"
    - "single iterate_state pass exposes properties AND coords (x/y/z); explicit space dict always; no round() in expressions; uppercase ID"
    - "resv (int residue value) read into the contract's resi key — resi string may be blank/insertion-coded"
    - "get_bonds 0-based walk positions resolve via index_to_id[i+1] for whole-object selections"
    - "fail-closed boundary: bounding_sphere raises ValueError on ligand-less records (NaN/empty bounds would only poison the generator later)"

key-files:
  created: ["aamatch/geometry.py", "tmp/probe_geometry.py (git-ignored probe)"]
  modified: []

key-decisions:
  - "resv (int) read into record['resi']: detector contract requires int resi; expression-space resi is a STRING (insertion-code capable, blank for SDF loads) — resv is the prior-art-proven int accessor (editing.py symbol table)"
  - "bounding_sphere filters side=='lig' internally and fails closed (ValueError) when no ligand-side records exist — the generator's ligand_data cannot be sized from a ligand-less scene, and house style is fail-early over silent NaN"
  - "index_to_id keyed by the 1-based index property (plan-literal); docstring pins bond position i → index_to_id[i+1] for whole-object selections so 02-10 can remap into sorted record order"
  - "records sorted by (object, id) — deterministic detector input regardless of PyMOL object walk order"

patterns-established:
  - "Probe tolerance rule: pose read-back asserts use 1e-6 (PyMOL stores float32; bake roundtrips accumulate ~1e-7) — matches research §6.2's stated tolerance"

# Metrics
duration: 4 min
completed: 2026-09-06
---

# Phase 2 Plan 09: Geometry Bridge Summary

**Cmd-tier geometry bridge (aamatch/geometry.py, 265 lines): one-pass iterate_state extraction of detector-contract atom records, ligand bond block + index→id map, ligand bounding sphere for generator ligand_data, and coords/centroid pose helpers — probe-proven on real PyMOL objects (benzamide 16 atoms / 16 bonds, 27 contract records).**

## Performance

- **Duration:** 4 min
- **Started:** 2026-09-06T12:39:43Z
- **Completed:** 2026-09-06T12:43:32Z
- **Tasks:** 3/3
- **Files modified:** 1 tracked (aamatch/geometry.py) + 1 git-ignored probe (tmp/probe_geometry.py)

## Accomplishments

- The pure/cmd geometry boundary exists as ONE module usable identically by SMOKE-03/04/05 and the Phase-3 wizard: `game_object_names` (prefix-only filter), `extract_game_atoms` (12-key detector-contract records, sorted by (object, id)), `ligand_bonds` (0-based (i,j,order) + {index: id}), `bounding_sphere` (ligand-side centroid + max-dist radius), `coords_of`/`centroid_of` (pose assertion via coordinates — never `get_object_matrix`).
- Extraction is ONE `cmd.iterate_state(1, sel, ...)` pass over the ' or '-joined game objects with an explicit space dict, no `round()` in the expression, uppercase `ID`, `resv` → int `resi` — every Pitfall-8/15 discipline honored and probe-verified.
- Headless probe proves the full contract on real objects: 16 ligand atoms / 16 bonds with order multiset {1:12, 2:4} (corrected 02-04 fixture), exact 12-key records with correct types on all 27 atoms, index_to_id covering 1..N with every bond endpoint resolving, bounding sphere matching an independent recomputation, fail-closed ValueError on ligand-less input, and a translate/untranslate pose roundtrip.

## Task Commits

Each task was committed atomically:

1. **Task 1: geometry.py — extraction + bounds + pose reads** - `c9d69cf` (feat)
2. **Task 2: Headless probe — extraction proves out on real objects** - no commit (tmp/probe_geometry.py is git-ignored by design; probe output carried the `=== PROBE-GEOM DONE ===` marker with all PASS)
3. **Task 3: Suite gate** - no commit (gate-only: 346/346 green, purity gates A/A2/B/D + negative control all ok, geometry.py correctly outside PURE_MODULES)

**Plan metadata:** see final docs commit.

_Note: Task 2/3 produce no tracked-file changes by design — the probe lives in git-ignored tmp/ per the established probe pattern; the suite gate is verification-only._

## Files Created/Modified

- `aamatch/geometry.py` — the cmd-tier geometry bridge (ONLY tracked file; cmd tier, NOT in PURE_MODULES)
- `tmp/probe_geometry.py` — headless Windows-PyMOL probe (git-ignored; rerunnable via the standing-rule command)

## Decisions Made

- **`resv` → record['resi'] (int):** the detector contract requires `"resi": int` and `_aa_features` does `int(recs[0]['resi'])`; the expression namespace's `resi` is a string (blank for SDF loads, insertion-code capable for PDB loads) which would violate the contract. `resv` is the int residue value (editing.py:1446 symbol table; prior-art wizard.py carried `resv`). Probe pins `isinstance(record['resi'], int)` across all records.
- **bounding_sphere filters ligand side internally + fails closed:** plan wording ("centroid of ALL ligand-side records") implemented as an internal `side == 'lig'` filter (idempotent for pre-filtered callers) and a ValueError when no ligand-side records exist — empty bounds would silently size grids to nothing or hand NaN to the generator's save-time `allow_nan=False` guard far from the cause.
- **index_to_id = {index_property: id} (plan-literal keying):** docstring documents the get_bonds querying.py:1078-1084 caveat — bond endpoints are 0-based walk positions, and for whole-object selections position i addresses `index_to_id[i + 1]`. Probe empirically pins walk order == index 1..N and endpoint resolution.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Probe pose-restore tolerance too tight for float32 storage**

- **Found during:** Task 2 (probe run 1)
- **Issue:** `pose restore` failed at 1e-9 tolerance — PyMOL stores coordinates as float32, so a translate(+1,+2,+3)/translate(-1,-2,-3) roundtrip accumulates ~1e-7 noise per atom
- **Fix:** assert tolerance 1e-6 — the exact tolerance research §6.2 already prescribes for pose asserts ("rigid assert: after[i] == before[i] + delta ... tolerance 1e-6")
- **Files modified:** tmp/probe_geometry.py (git-ignored, no commit)
- **Verification:** probe re-run: `pose restore PASS` + `=== PROBE-GEOM DONE ===`
- **Committed in:** n/a (probe-only; no aamatch code affected)

**2. [Rule 2 - Missing Critical] bounding_sphere fail-closed on empty ligand side**

- **Found during:** Task 1 (implementation)
- **Issue:** plan did not specify behavior for ligand-less record sets; a silent ((0,0,0), 0.0) would corrupt grid sizing or surface as a confusing allow_nan=False refusal inside the generator
- **Fix:** raise ValueError with a boundary-specific message ("no ligand-side records -- the generator's ligand_data needs the ligand's bounding sphere")
- **Files modified:** aamatch/geometry.py
- **Verification:** probe asserts `bounding fail-closed PASS` (ValueError on AA-only records)
- **Committed in:** c9d69cf

**3. [Plan-sketch adaptation] Expression reads `resv` for the contract's `resi` key** (recorded above under Decisions Made; the plan's tuple sketch named `resi`, whose expression value is a str and would violate the detector contract's int typing). Record KEYS are exactly as planned; only the expression accessor differs. Committed in c9d69cf.

---

**Total deviations:** 3 auto-fixed (1 bug, 1 missing-critical, 1 plan-sketch adaptation)
**Impact on plan:** All necessary for contract correctness (int resi), boundary safety (fail-closed bounds), and probe fidelity (float32 tolerance). No scope creep.

## Issues Encountered

- None beyond the deviations above. Note: the plan's Task 2 verify text said "benzamide 16 atoms, 11 bonds" — the stale pre-02-04-fix sketch; the standing rules pre-corrected this and the probe asserts the real fixture counts (16 atoms / 16 bonds, orders {1:12, 2:4}), which passed.
- Probe observations recorded for downstream plans: fragment-created AA objects carry atom ids starting at 0 (identity stays (object, id) — nothing downstream may assume 1-based ids); fragment 'ser' carries resv=2 (resi carried as-is; the detector int-coerces it).

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- **02-10 (engine) wiring recipe (pinned by the probe):** `records = extract_game_atoms()`; ligand bond block positions remap into the sorted ligand records via `index_to_id[i + 1]` → atom id → position in the (object, id)-sorted ligand subsequence — the detector validates indices fail-closed, so a mis-remap surfaces loudly, not silently.
- `bounding_sphere(records)` → `{'centroid': ..., 'radius': ...}` feeds `generate(..., ligand_data, ...)` directly (world frame == ligand-file frame under Phase-2 baked coordinates).
- SMOKE-03/04/05 need no runner changes; geometry helpers are import-ready. SMOKE-03's `unclassified_aa_atoms == 0` assertion operates on records from THIS module.
- No blockers. Purity untouched (PURE_MODULES stays 11; geometry is cmd-tier by design).

---
*Phase: 02-headless-game-engine*
*Completed: 2026-09-06*
