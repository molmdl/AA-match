---
phase: 02-headless-game-engine
plan: 04
subsystem: data
tags: [sdf, manifest, pymol, headless-smoke, sha256, fixture-data, cmd-api, bash]

# Dependency graph
requires:
  - phase: 02-headless-game-engine
    provides: "02-03 frozen manifest schema (14 keys, parse_manifest_dict/enumerate_entries/largest_entry, 'manifest' kind in KINDS)"
  - phase: 02-headless-game-engine
    provides: "02-01 DETECT-03 approved chemistry policy (metal list {MG ZN FE CA MN CU NI CO CD}; halogen {Cl Br I}, C-F excluded) behind the flags"
  - phase: 01-bootstrap-pure-foundation
    provides: "01-04 to_windows_path (all cmd.load call sites route through it); 01-07 headless smoke conventions (sys.argv anchor, marker verdict, flush)"
provides:
  - "Bundled Phase-2 data: aamatch/data/ligands/benzamide.sdf (aromatic ring + amide donor/acceptor) + acetate.sdf (carboxylate anion, M CHG round-trip)"
  - "Versioned manifest container aamatch/data/MANIFEST.json (kind='manifest', 1 set 'demo-dev-1', 2 entries, sha256-pinned, schema validated by the 02-03 pure gate)"
  - "Generalized smoke runner smoke/run_smoke.sh (SMOKE-NN derived from filename, any smoke_NN_name.py, legacy fallback)"
  - "SMOKE-02: every-manifest-id count-asserted headless load proof (GEN-02 supply, PITFALL 11.3 anti-drift)"
affects: [02-08 generator (enumerate_entries input), 02-13 placement, 02-14 E2E, 02-15 perf smoke (largest_entry -> benzamide), phase-8 demo curation]

# Tech tracking
tech-stack:
  added: "none (stdlib hashlib only; builder is a throwaway git-ignored script)"
  patterns:
    - "Script-built fixtures: SDFs emitted programmatically so atom/bond/charge counts are consistent BY CONSTRUCTION; manifest counts derived from the same lists; sha256 pins the written bytes -- never hand-edit an SDF after manifest creation, regenerate instead"
    - "Marker-deriving smoke runner: SMOKE-NN grepped from tee'd output is the sole verdict carrier (exit codes cannot cross cmd.exe)"
    - "SMOKE-02 shape: pure container parsed INSIDE PyMOL, per-entry private _aam_tmp* object with delete-in-finally, exact multiset comparison of get_bonds orders"

key-files:
  created:
    - "aamatch/data/MANIFEST.json"
    - "aamatch/data/ligands/benzamide.sdf"
    - "aamatch/data/ligands/acetate.sdf"
    - "smoke/smoke_02_manifest.py"
  modified:
    - "smoke/run_smoke.sh"

key-decisions:
  - "Benzamide counts come from the builder script's lists (16 atoms/16 bonds, {\"1\":12,\"2\":4}), not the plan sketch (11 bonds, {\"1\":7,\"2\":4}) -- the sketch omitted the 5 ring C-H bonds; 16 atoms + explicit H + 1 ring forces 16 bonds. The plan's own trust-the-script rule was applied (acetate's sketch matched exactly)."
  - "Both ligands carry metal_present=false / halogen_present=false, consistent with the approved DETECT-03 metal list and the C-F halogen exclusion policy (02-01)."
  - "license='' and provenance={} are deliberate Phase-8 placeholders (HELP-02 gate before curated bundling)."
  - "set_id 'demo-dev-1' with tier 'easy' marks this as the Phase-2 development set (not curated demo data)."

patterns-established:
  - "Fixture regeneration contract: tmp/build_fixtures.py (git-ignored) is the single source of truth for SDF + manifest counts; sha256 in the manifest is taken over the written bytes in the same run"
  - "SMOKE-NN convention generalized: any smoke_<NN>_<name>.py gets its marker derived by the runner; legacy smoke_01_bootstrap falls back to 01"

# Metrics
duration: 6 min
completed: 2026-09-06
---

# Phase 2 Plan 4: Bundled Fixtures + MANIFEST + SMOKE-02 Summary

**Two sha256-pinned fixture ligands (benzamide 16-atom, acetate 7-atom anion) + versioned MANIFEST.json proven count-exact in headless Windows PyMOL by a marker-deriving SMOKE-02 runner.**

## Performance

- **Duration:** 6 min
- **Started:** 2026-09-06T09:29:11Z
- **Completed:** 2026-09-06T09:36:09Z
- **Tasks:** 3
- **Files modified:** 5 (4 created, 1 modified)

## Accomplishments
- benzamide.sdf + acetate.sdf emitted programmatically (counts consistent by construction); MANIFEST.json built through the pure stack (`make_container('manifest')` + `write_json_atomic`) and accepted by the frozen 02-03 validator
- run_smoke.sh generalized: SMOKE-NN derived from the script filename (`sed` on basename, empty → `01` legacy fallback), optional timeout arg — SMOKE-01 recipe unchanged in behavior (backward compat proven with a real boot)
- SMOKE-02 passes on first boot: both entries load count-exactly (atoms / bond-order multiset / formal_charge_sum / states / sha256 / metal+halogen flags), pure container gate runs inside PyMOL, zero `_aam_tmp` leaks
- WSL suite still green: 211/211 including purity gates

## Task Commits

Each task was committed atomically:

1. **Task 1: Fixture ligands + MANIFEST.json (script-built)** - `6a65dc8` (feat)
2. **Task 2: Generalize run_smoke.sh (derive NN from filename)** - `fe7fb92` (feat)
3. **Task 3: SMOKE-02 every-manifest-id load proof** - `4962551` (feat)

## Files Created/Modified
- `aamatch/data/ligands/benzamide.sdf` - C7H7NO, 16 atoms (7C/7H/1N/1O), 16 bonds {"1":12,"2":4}, kekulé ring + amide C(=O)NH2, charge 0 — pi_stacking + h_bond exercisable
- `aamatch/data/ligands/acetate.sdf` - CH3C(=O)O⁻, 7 atoms, 6 bonds {"1":5,"2":1}, `M  CHG` −1 on the single-bonded O — salt-bridge-capable, charge round-trips (probe-proven property)
- `aamatch/data/MANIFEST.json` - container {magic AAMATCH, version 1, kind 'manifest'}; payload {manifest_version 1, 1 set 'demo-dev-1', 2 entries}; each entry carries the 14 frozen schema keys with real sha256 over the written bytes
- `smoke/run_smoke.sh` - marker-deriving runner (usage: `bash smoke/run_smoke.sh smoke/smoke_NN_name.py [timeout_sec]`)
- `smoke/smoke_02_manifest.py` - every-manifest-id load proof: `read_json_file` + `parse_manifest_dict` inside PyMOL, per-entry `to_windows_path(package_data_path('data', entry['file']))` → `cmd.load` into `get_unused_name('_aam_tmp')`, exact count assertions, `cmd.delete` in finally, `get_names('objects')` leak check

## Decisions Made
- Benzamide bond counts follow the builder script's lists, not the plan's sketch (see Deviations) — the plan itself prescribes "TRUST THE SCRIPT's lists … then update the manifest to match"
- Element-scan flags cross-checked against the DETECT-03 policy lists ({MG ZN FE CA MN CU NI CO CD} metals; {Cl Br I} halogens, F excluded) — both fixtures flag-free as expected
- sha256 is computed inside the builder over the exact bytes written, so manifest and SDF can never drift apart within one regeneration

## Deviations from Plan

### Auto-fixed Issues

**1. [Plan-internal count inconsistency, resolved by the plan's own rule] Benzamide 16 bonds, not the sketched 11**
- **Found during:** Task 1 (fixture construction)
- **Issue:** The plan sketched benzamide as 16 atoms / 11 bonds / {"1":7,"2":4}, but 16 atoms (explicit H) in a connected molecule with one ring requires 16 − 1 + 1 = 16 bonds; the sketch omitted the 5 ring C-H single bonds
- **Fix:** Builder script's atom/bond lists are the source of truth; manifest carries bond_count 16 and {"1":12,"2":4} (the sketched {"2":4} matched; acetate's sketch matched exactly)
- **Files modified:** aamatch/data/ligands/benzamide.sdf, aamatch/data/MANIFEST.json
- **Verification:** SMOKE-02 `benzamide bonds PASS got [1×12, 2×4] want [1×12, 2×4] (n=16)` in real PyMOL
- **Committed in:** 6a65dc8

**2. [Rule 1 - Bug] Malformed SDF header in first builder draft (never committed)**
- **Found during:** Task 1, caught by inspecting the generated file BEFORE any Windows boot
- **Issue:** The three V2000 header lines were emitted without trailing newlines, gluing the counts line onto the title line (title/program/comment/counts collapsed into one line → unparseable header)
- **Fix:** Added `\n` to the header strings in tmp/build_fixtures.py (git-ignored throwaway); regenerated both SDFs; sha256 re-pinned automatically by the same run
- **Files modified:** tmp/build_fixtures.py only (not tracked); regenerated aamatch/data/* artifacts committed corrected
- **Verification:** `cat -A` shows proper 4-line header; SMOKE-02 loads parse cleanly in PyMOL
- **Committed in:** 6a65dc8 (corrected artifacts; the throwaway script lives in git-ignored tmp/)

---

**Total deviations:** 2 auto-fixed (1 plan-internal count inconsistency via the plan's trust-the-script rule, 1 bug in the throwaway builder)
**Impact on plan:** Both fixes were necessary for a loadable, drift-proof data supply. No scope creep.

## Issues Encountered
None — both Windows smokes passed on their first boot; the only rework was the pre-boot header-newline fix in the throwaway builder.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Data supply is proven: 02-08 (generator) can consume `enumerate_entries` over MANIFEST.json; 02-13 (placement) and 02-14 (E2E) have stable fixture geometry to script against; 02-15 (perf smoke) gets its target via `largest_entry` → benzamide (heavy_atom_count 9 > acetate 4)
- The generalized runner unblocks all Phase-2 smokes (SMOKE-03/04/05 need no runner changes)
- Fixtures are intentionally tiny; Phase-8 curated data (with real license/provenance) replaces them without schema change (additive evolution)
- No blockers carried forward

---
*Phase: 02-headless-game-engine*
*Completed: 2026-09-06*
