---
phase: 04-qt-setup-window
plan: 04
subsystem: cmd-tier engine
tags: [pymol-cmd, ligand_content, upload-flow, read_sdfstr, read_mol2str, engine, placement, gamestart, smoke]

# Dependency graph
requires:
  - phase: 02-headless-game-engine
    provides: engine.new_game/materialize seam, placement.materialize, _ligand_data_for temp-load discipline, manifest 14-key row contract
  - phase: 03-wizard-gameplay-loop
    provides: gamestart.start_game one-call seam + return-value smoke pattern
provides:
  - additive ligand_content=None on engine._ligand_data_for, engine.new_game, engine.materialize, placement.materialize, gamestart.start_game (None path byte-identical everywhere)
  - string loading via cmd.read_sdfstr/read_mol2str (same C parser as file loads) with format/extension-derived reader selection and count_states==1 fail-closed
  - SMOKE-10: synthetic 'uploads/mol-001.sdf' uploaded flow proven end-to-end in real headless PyMOL (new_game -> materialize -> start_game -> cleanup) + EngineError negative control + bare-start regression
  - recorded build findings: read_mol2str missing from this 2.5.0 build's cmd namespace; cmd.load of a missing sdf raises CmdException (file-read path)
affects: [04-08 upload pipeline, 04-12 export, 04-13 start, Phase 7 import]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Synthetic file key ('uploads/mol-00N.sdf') as ligand_content dict key -- embedded text, never a filesystem path (os.path.join hazard structurally impossible)"
    - "Reader derivation: row['format'] in engine (manifest-shaped rows), synthetic-key EXTENSION in placement (payload ligand blocks carry no 'format' key, 04-DECISIONS #18); anything else fail-closes"
    - "count_states == 1 fail-closed after every read_*str (records split one molecule per content entry)"
    - "Reader availability guards fail closed with the house error family when a build omits a cmd export"

key-files:
  created: [smoke/smoke_10_upload_flow.py]
  modified: [aamatch/engine.py, aamatch/placement.py, aamatch/gamestart.py]

key-decisions:
  - "Package cmd.load failure wrapped into EngineError naming the ligand -- the gamestart guard contract maps the ValueError family only, and the negative-control must-have demands a clear EngineError"
  - "mol2 branches guarded with hasattr(cmd,'read_mol2str') -- this 2.5.0 build defines it (importing.py:1038) but omits the api.py export; mol2 uploads fail closed naming the missing reader"
  - "SMOKE-10 single-candidate setup uses molecules_per_level=1 (generator requires 2 distinct molecules at DEFAULTS)"

patterns-established:
  - "Additive cmd-tier parameter threading: None default on every seam point, pass-through at every delegate, zero existing call-site changes, regression proven by bare-start smoke part"
  - "Negative-control discipline: synthetic key without content must fail closed with the house error family AND leave the scene byte-unchanged"

# Metrics
duration: 16 min
completed: 2026-09-15
---

# Phase 4 Plan 04: ligand_content Upload Pipe Summary

**Additive `ligand_content=None` threaded through the whole cmd-tier game seam (engine new_game/materialize, placement.materialize, gamestart.start_game) so uploaded molecules load from embedded text via `read_sdfstr`/`read_mol2str` — None defaults keep every existing call site byte-identical, proven headlessly by SMOKE-10.**

## Performance

- **Duration:** 16 min
- **Started:** 2026-09-15T04:28:59Z
- **Completed:** 2026-09-15T04:45:20Z
- **Tasks:** 3
- **Files modified:** 4 (3 modified + 1 created)

## Accomplishments

- `ligand_content=None` on all five seam signatures (`engine._ligand_data_for`, `engine.new_game`, `engine.materialize`, `placement.materialize`, `gamestart.start_game`); the None path is byte-identical — SMOKE-04 and SMOKE-08 regression PASS unchanged.
- String path: `engine` routes by `row['format']` (manifest-shaped rows); `placement` routes by the synthetic key's extension (payload ligand blocks carry no 'format' key — 04-DECISIONS #18); non-sdf/mol2 fail-closes; `count_states == 1` asserted; the atom_count cross-check stays active on the string path.
- SMOKE-10 PASS (19 checks): synthetic `uploads/mol-001.sdf` row (benzamide copy, record-text sha256 per 04-DECISIONS #19) flows through new_game → materialize → full start_game (live wizard, exact object growth) → Done + cleanup restores baseline; PART 2 negative control fails closed with EngineError and an untouched scene; PART 3 bare-start regression.
- Phase 7's import side now needs zero new cmd-tier loading code: the same dict feeds new_game (regenerate) and materialize (replay) — research `phase_7_contract` item 5 satisfied.

## Task Commits

Each task was committed atomically:

1. **Task 1: engine — ligand_content on _ligand_data_for + new_game** — `b98b747` (feat)
2. **Task 2: placement + gamestart — materialize and start_game params** — `e145a72` (feat, includes deviation 1)
3. **Task 3: SMOKE-10 + fail-closed refinements** — `819c3ac` (fix, deviations 2-3), `b089575` (test, smoke)

## Files Created/Modified

- `aamatch/engine.py` — `_ligand_data_for`/`new_game`/`materialize` gain `ligand_content=None`; string path before package resolution; package `cmd.load` failure wrapped as EngineError; mol2 branch guarded.
- `aamatch/placement.py` — `materialize` gains `ligand_content=None`; extension-derived reader; `import os` added.
- `aamatch/gamestart.py` — `start_game` gains `ligand_content=None`, passed through to BOTH `engine.new_game` and `engine.materialize` (one-call seam stays complete for uploaded payloads).
- `smoke/smoke_10_upload_flow.py` — SMOKE-10: PART 1 uploaded flow, PART 2 EngineError negative control, PART 3 bare-start regression.

## Decisions Made

1. **`gamestart.start_game` passes `ligand_content` to both `new_game` and `materialize`.** The plan named only the new_game pass-through explicitly, but Task 3's full start path materializes from the synthetic key — the delegate pass-through (Task 2 step 3: "start_game's param reaches placement") requires it.
2. **Signature count is five, not the "exactly four" in the plan's grep metric.** must_have truth 1 + plan objective name four, but Task 2 step 3 adds the `engine.materialize` delegate and Task 3 calls it directly with the kwarg — the 5th signature is structurally required. `grep -n 'def .*ligand_content=None' aamatch/*.py` shows exactly 5; no existing default changed (`candidates=None` untouched).
3. **`import os` added to placement.py** (deviation 1 below).
4. **Package-load wrap + mol2 guards** (deviations 2-3 below).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] placement.py lacked `import os`**
- **Found during:** Task 2 (placement materialize string path)
- **Issue:** Plan snippet uses `os.path.splitext` and asserts "`os` is already imported"; it was not (placement.py imported only pymol cmd + capability/geometry/paths).
- **Fix:** added `import os` ahead of the pymol import (stdlib-first house style).
- **Files modified:** aamatch/placement.py
- **Verification:** py_compile; full WSL suite green.
- **Committed in:** e145a72 (part of Task 2 commit)

**2. [Rule 1 - Bug / house-contract] `cmd.load` of a missing package fixture raises `pymol.CmdException`, not a silent 0-atom temp**
- **Found during:** Task 3 first SMOKE-10 run (PART 2 failed: `raised: CmdException: failed to open file ...`)
- **Issue:** This build file-reads `.sdf` text first (`internal.py:359-360` `_load2str` path → `file_read` → CmdException), so the plan's expected "atom_count fires on 0 atoms" never happens; worse, CmdException sits OUTSIDE the gamestart/wizard-guarded ValueError family -- a load failure would escape every handler guard. The must_have demands "a clear EngineError".
- **Fix:** `engine._ligand_data_for`'s package-load branch wraps `cmd.load`; any failure becomes `EngineError` naming the ligand and that the row may name a synthetic key without ligand_content. The wrapped call sits inside the existing try/finally, so the temp/leak checks are untouched.
- **Files modified:** aamatch/engine.py
- **Verification:** SMOKE-10 PART 2 PASS (EngineError raised, scene unchanged); SMOKE-04/08 regression PASS (existing paths unchanged).
- **Committed in:** 819c3ac

**3. [Rule 2 - Missing Critical] This 2.5.0 build omits the `cmd.read_mol2str` export**
- **Found during:** Task 3 first SMOKE-10 run (`hasattr(cmd, 'read_mol2str')` → False).
- **Issue:** Installed `importing.py:1038` defines `read_mol2str`, but the installed `api.py` re-export block lists read_sdfstr/read_pdbstr/etc. and NOT read_mol2str — `cmd.read_mol2str` is an AttributeError crash on this build (the repo's pymol-src reference has it; environment asymmetry).
- **Fix:** `hasattr(cmd, 'read_mol2str')` guard on both mol2 branches (engine + placement); absence fail-closes with the house error naming the missing reader. SMOKE-10 keeps the availability probe as RECORD-ONLY. SDF uploads (this plan's exercised path) are unaffected.
- **Files modified:** aamatch/engine.py, aamatch/placement.py, smoke/smoke_10_upload_flow.py
- **Verification:** SMOKE-10 PASS with the probe recording False; full WSL suite green.
- **Committed in:** 819c3ac (code), b089575 (smoke)
- **Forward note for 04-06/04-08:** mol2 upload support on this build needs an alternative route (e.g. `cmd.load_raw('mol2', text, name)` — same C parser per importing.py's load_raw machinery) or a vendored api call; recorded here for the upload-pipeline plans.

**4. [Rule 3 - Blocking / smoke design] Plan's setup snippet cannot generate with one candidate**
- **Found during:** Task 3 smoke authoring (pre-run analysis of generator.py:803-816).
- **Issue:** `dict(setup_state.DEFAULTS, demo_set_id='uploaded')` + `candidates=[row]` would GenerationError — DEFAULTS has molecules_per_level=2 and the generator requires 2 DISTINCT candidates.
- **Fix:** the smoke's setup adds `molecules_per_level=1` (SMOKE-04's own precedent for single-candidate games); everything else verbatim.
- **Files modified:** smoke/smoke_10_upload_flow.py
- **Verification:** SMOKE-10 PASS.
- **Committed in:** b089575

---

**Total deviations:** 4 auto-fixed (2 blocking, 1 bug/house-contract, 1 missing critical)
**Impact on plan:** All fixes necessary for correctness or for the plan's own must_haves to hold on the pinned build. No scope creep; the additive contract (None = byte-identical) is intact and regression-proven.

## Issues Encountered

- **Plan sketch imprecision (no code impact):** Task 3 asserts the level-0 ligand block "reads source 'uploaded'"; `ligand['source']` is generator.py:854's verbatim echo of setup `source_mode` and 'uploaded' is not a legal source_mode ('demo'|'upload' only — setup_state.py:52). The smoke pins what the generation contract actually carries (`set_id 'uploaded'` + the synthetic file key), prints the source echo, and documents the reconciliation in its docstring (both readings covered by PART 1's checks).
- Three parallel wave-1 agents ran sibling smokes concurrently; no transient environment failures hit this plan's runs (every smoke passed on first non-diagnostic run).

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Ready: the `ligand_content` seam plans 04-08 (upload pipeline), 04-13 (Start-after-upload), 04-12 (export) and Phase 7 (import replay/regenerate) all consume this plan's parameter — Phase 7 adds zero cmd-tier loading code (`phase_7_contract` item 5 closed).
- **Concern (recorded for 04-06/04-08):** mol2 uploads cannot use `cmd.read_mol2str` on this build (api.py export missing). The sdf path is proven; the mol2 branches fail closed with a clear message until an alternative route is chosen. The availability probe in SMOKE-10 is the canary.
- **Note:** `placement.materialize`'s PACKAGE path was deliberately not wrapped (deviation minimalism): a missing bundled fixture at materialize still raises CmdException. If Phase 7's import replay hits that class, mirror the engine wrap there then.

---
*Phase: 04-qt-setup-window*
*Completed: 2026-09-15*
