---
phase: quick-002
plan: 002
subsystem: smoke-battery
tags: [smoke, detector, halogen, metal, curated-molecules, DETECT-03]

provides:
  - "Standing record-level halogen+metal detector oracle over the bundled curated molecules (chloramphenicol / thyroxine / heme) as smoke/smoke_22_detector_coverage.py"
  - "Mechanically re-provable 08-11 verdict on every regression battery ('NO threshold surprise -- DETECT-03 provisional values hold')"
requires: "quick-001 (hardened runner, 933-baseline), 08-07 (curated bundle), 08-11 (source probe + verdict)"
affects: "All future DETECTOR_VERSION bump discussions now cite a standing oracle; future battery plans now expect smokes 01-22"

tech-stack:
  added: []
  patterns:
    - "One-off probe -> standing smoke port pattern: mechanical renames only (anchor basename, -ENV/-NN prefixes, marker), byte-faithful scenes"

key-files:
  created:
    - smoke/smoke_22_detector_coverage.py
  modified: []

decisions:
  - "Docstring wording rephrase (verbatim-docstring exception): the probe's 'ONE-OFF / NOT a smoke / prints NO SMOKE-NN marker' prose was replaced with a provenance + run-line + verdict-rule docstring -- mandatory because the old prose is now FALSE in the file's standing-battery role (plan item 7 authorized the full replacement)."

metrics:
  duration: "~35 min (ended 2026-10-04 02:28 +0800; includes one aborted Write-recovery pass)"
  completed: 2026-10-04
---

# Phase quick-002 Plan 002: Detector-Coverage Standing Smoke (SMOKE-22) Summary

**One-liner:** The plan-08-11 Task 2 one-off detector-coverage probe (`tmp/detector_coverage_phase8.py`, git-ignored) was folded byte-faithfully into the standing battery as `smoke/smoke_22_detector_coverage.py` -- the curated halogen/metal rows (chloramphenicol C-Cl, thyroxine C-I, heme Fe) now have a re-runnable record-level oracle with the exact `=== SMOKE-22 PASS ===` marker derived by the runner off the basename (zero runner edits).

## Tasks Completed

| Task | Name | Commit | Files |
| ---- | ---- | ------ | ----- |
| 1 | Port tmp/detector_coverage_phase8.py into standing smoke_22 | 6cad59c | smoke/smoke_22_detector_coverage.py (new, 491 lines) |

## Port Fidelity

Body-from-`import math` diff vs the probe shows ONLY the plan's mechanical renames and nothing else:

- `mine = 'detector_coverage_phase8.py'` -> `mine = 'smoke_22_detector_coverage.py'` (anchor logic untouched)
- `PROBE-ENV root:` / `pymol:` / `python:` / `%s donor:` -> `SMOKE-ENV ...` (4 print sites)
- check-ledger prefix `'PROBE %-44s %s %s'` -> `'SMOKE-22 %-44s %s %s'`
- check labels `'clean pre-probe scene'` -> `'clean pre-smoke scene'`; `'probe entries present'` -> `'smoke entries present'`
- both `'PROBE VERDICT:'` branches -> `'SMOKE-22 VERDICT:'` (informative text VERBATIM)
- final marker `=== DETECTOR-COVERAGE PHASE-08 PASS ===` -> `=== SMOKE-22 PASS ===` (still in the `else` branch -- prints ONLY when `failures` is empty)
- docstring replaced per plan item 7 (provenance + run line + scenes + heme -4 note + verdict rule; the old 'NOT a smoke' prose could not survive)

Everything else is byte-identical: constructed targets (3.3 A / 180 deg / 120 deg / 2.5 A), slacks (0.30 A / 12.0 deg), thresholds imports (`HALOGEN_ACC_ANGLE_DEG, HALOGEN_D_MAX, HALOGEN_DONOR_ANGLE_DEG, METAL_D_MAX` -- zero hardcoded windows), heme formal_charge_sum == -4 pin (08-07 recorded input), all three try/finally scenes, and the pre/post `cmd.get_names('objects')` zero-leakage contract.

## Verification Battery (all real, run from repo root)

1. `python3.6 -m py_compile smoke/smoke_22_detector_coverage.py` -> exit 0, silent.
2. `python3.6 -m unittest discover -s tests -v` -> **Ran 933 tests in 30.5 s, OK** (zero failures/errors). This run IS the audit-walk proof: audit 2 (brute_force_pairs isolation) and audit 4 (`test_no_banned_call_sites`) in tests/test_code_audit.py now scan smoke_22 as part of the `smoke/*.py` walk and are green over it; purity gates unaffected (file is a smoke, not a pure module).
3. `grep -nE "get_model|matrix_reset|get_object_ttt"` -> **0 matches** (code AND prose clean; the docstring does not name the banned tokens).
4. `grep -n "PROBE"` -> **0 matches** (all prefixes renamed; docstring provenance references the probe only in lowercase prose).
5. `grep -c "=== SMOKE-22 PASS ==="` -> **exactly 1** (the marker print).
6. Real headless proof: `bash smoke/run_smoke.sh smoke/smoke_22_detector_coverage.py 240` -> **exit 0**, runner log `/tmp/smoke_out.wiY8s3.txt`. 24/24 checks PASS, verbatim tail:

   ```
   SMOKE-22 chloramphenicol metric frame d_ax/donor/acc  PASS d_ax=3.300 donor=180.0 acc=120.0 (targets 3.3/180/120)
   SMOKE-22 thyroxine metric frame d_ax/donor/acc        PASS d_ax=3.300 donor=180.0 acc=120.0 (targets 3.3/180/120)
   SMOKE-22 heme formal_charge_sum == -4 (08-07 recorded input) PASS sum=-4
   SMOKE-22 heme metric frame d_metal                    PASS d_metal=2.500 (target 2.5, window (0.5, 3.0])
   SMOKE-22 heme metric frame d_metal                    PASS d_metal=2.586 (target 2.5, window (0.5, 3.0])
   SMOKE-22 zero object leakage                          PASS post=[] pre=[]
   SMOKE-22 VERDICT: NO threshold surprise -- DETECT-03 provisional values hold on real data (halogen records provable on chloramphenicol C-Cl and thyroxine C-I geometry inside the approved 4.0 A / [135,195] / [90,150] windows; metal record provable on HEM Fe inside the 3.0 A window; heme formal_charge_sum -4 as recorded at 08-07); no DETECTOR_VERSION bump proposal needed
   === SMOKE-22 PASS ===
   ```

   (Scene notes: chloramphenicol donors=2 (2x C-Cl), thyroxine donors=4 (4x C-I), heme metals=['FE'], porphyrin Ns=4; heme metal tally=2 records -- the constructed OE1 at 2.500 and a second GLU carboxylate chelator at 2.586, both inside the (0.5, 3.0] window, matching the 08-11 probe observation.)
7. `git show --stat HEAD` -> exactly ONE file (smoke/smoke_22_detector_coverage.py, 491 insertions), message exactly `test(quick-002): fold phase-8 detector-coverage probe into standing SMOKE-22`; `git status --porcelain` -> clean; `ls smoke/` -> smokes 01-21 unrenamed and untouched + the one new smoke_22 file.

## Deviations from Plan

**None.** The honest-deviation rule had no trigger: all three scenes green on the first real run, no checks/slacks/thresholds weakened, no environmental failures to report. The port is byte-faithful modulo the authorized renames (including the plan-authorized docstring replacement).

## Authentication Gates

None.

## Next Phase Readiness

- The standing battery is now 22 smokes; future battery-verdict plans (e.g. phase-final regression batteries) must include smoke_22 at 240 s.
- Any future DETECTOR_VERSION bump proposal can cite smoke_22 as the standing oracle that will re-run on the same curated rows.
- The 08-11 'NO threshold surprise' verdict is now mechanically re-provable instead of living only in STATE.md + a git-ignored tmp/ file.
- tmp/detector_coverage_phase8.py remains byte-untouched (git-ignored historical one-off), per plan.
