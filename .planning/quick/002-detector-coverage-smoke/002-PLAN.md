---
phase: quick-002
plan: 002
type: execute
wave: 1
depends_on: []
files_modified: [smoke/smoke_22_detector_coverage.py]
autonomous: true

must_haves:
  truths:
    - "Running `bash smoke/run_smoke.sh smoke/smoke_22_detector_coverage.py 240` exits 0 with '=== SMOKE-22 PASS ===' in that run's per-invocation log -- the runner derives NN=22 off the basename with ZERO runner edits"
    - "The pass body carries the informative 'NO threshold surprise -- DETECT-03 provisional values hold' verdict and pins heme formal_charge_sum == -4 (08-07 recorded input)"
    - "Any FAIL check prints NO pass marker; the fix path is a DETECTOR_VERSION bump PROPOSAL in a new plan -- thresholds.py / detector.py / capability.py are NEVER silently editable to force green"
    - "All three oracle scenes survive the port verbatim: chloramphenicol C-Cl and thyroxine C-I -> halogen record (d_ax ~3.3 within slack 0.30, donor ~180 in [135,195], acc ~120 in [90,150]); heme Fe -> metal record (d_metal ~2.5 within slack 0.30, window (0.5, 3.0])"
    - "Every metric window comes from the imported thresholds constants (HALOGEN_D_MAX / HALOGEN_DONOR_ANGLE_DEG / HALOGEN_ACC_ANGLE_DEG / METAL_D_MAX) -- none hardcoded"
    - "Zero object leakage: the pre/post cmd.get_names('objects') equality check stays green"
    - "The full WSL suite stays 933/933 with the new file inside tests/test_code_audit.py's smoke/ walk (zero banned-call sites, zero brute_force_pairs sites)"
    - "Smokes 01-21, run_smoke.sh, aamatch/, tests/ and the tmp/ probe are all untouched"
  artifacts:
    - path: "smoke/smoke_22_detector_coverage.py"
      provides: "Standing record-level halogen+metal detector oracle over the bundled curated molecules (count-level oracle existed only for benzamide in SMOKE-03/05)"
      contains: "=== SMOKE-22 PASS ==="
  key_links:
    - from: "smoke/run_smoke.sh verdict grep"
      to: "the smoke's final printed marker"
      via: "NN=22 from basename (sed pattern already in the runner); grep is exactly '=== SMOKE-22 PASS ===' in the per-run mktemp log"
      pattern: "=== SMOKE-22 PASS ==="
    - from: "smoke_22 metric sanity asserts"
      to: "aamatch/thresholds.py approved windows"
      via: "imported constants, never literals"
      pattern: "HALOGEN_D_MAX"
    - from: "smoke_22 scenes"
      to: "bundled curated SDFs (chloramphenicol / thyroxine / heme)"
      via: "MANIFEST.json -> parse_manifest_dict -> enumerate_entries -> package_data_path + to_windows_path -> cmd.load"
      pattern: "enumerate_entries"
    - from: "smoke_22 (whole file, code AND prose)"
      to: "banned-token discipline"
      via: "zero occurrences of get_model / matrix_reset / get_object_ttt anywhere in the new file (no PROSE_PIN entry exists for smoke files -- the docstring must simply not name them)"
      pattern: "HALOGEN_D_MAX"
---

<objective>
Fold the phase-8 detector-coverage probe -- the git-ignored one-off from plan 08-11 Task 2 -- into the standing smoke battery as `smoke/smoke_22_detector_coverage.py`, making the curated-molecules halogen/metal record-level detector oracle repeatable on every regression battery.

Purpose: The 08-11 probe proved "NO threshold surprise -- DETECT-03 provisional values hold on real data" but its verdict lives only in STATE.md and a git-ignored tmp/ file; the standing battery's record-level detector oracle covers benzamide only (count-level, SMOKE-03/05). The curated halogen/metal molecules (chloramphenicol, thyroxine, heme) are exactly the rows most likely to expose detector regressions, and every future DETECTOR_VERSION discussion needs this oracle in the suite.
Output: ONE new file `smoke/smoke_22_detector_coverage.py` (a faithful port of the probe), verified via the standing gates and committed atomically. Nothing else changes.
</objective>

<execution_context>
@~/.config/opencode/get-shit-done/workflows/execute-plan.md
@~/.config/opencode/get-shit-done/templates/summary.md
</execution_context>

<context>
@AGENTS.md
@.planning/STATE.md
@tmp/detector_coverage_phase8.py
@smoke/run_smoke.sh
@smoke/smoke_02_manifest.py

**Established facts (all spot-checked 2026-10-03, no research needed):**

- **The probe is conversion-ready.** `tmp/detector_coverage_phase8.py` (482 lines, read in full) is a standing-smoke-shaped script: `_find_repo_root()` basename anchor (01-07 law: `__file__` unusable under `-cq`), `check()` ledger + module-level `failures`, `try/finally` scene cleanup deleting `_aam_tmp_lig`/`_aam_aatmp`, pre/post `cmd.get_names('objects')` snapshot equality, thresholds constants imported (`from aamatch.thresholds import HALOGEN_ACC_ANGLE_DEG, HALOGEN_D_MAX, HALOGEN_DONOR_ANGLE_DEG, METAL_D_MAX`), construction targets `TARGET_D_AX = 3.3`, `TARGET_ACC_ANGLE = 120.0`, `TARGET_D_METAL = 2.5` with slacks `0.30` / `12.0` deg, three scenes (chloramphenicol C-Cl, thyroxine C-I, heme Fe + formal_charge_sum == -4 pin), final verdict line then `=== DETECTOR-COVERAGE PHASE-08 PASS ===` only when `failures` is empty.
- **The anchor pattern is house-identical.** smoke_02/smoke_21's `_find_repo_root` is byte-identical to the probe's except the `mine = '<basename>'` literal; `smoke/` is one directory deep like `tmp/`, so the two-dirnames-up logic ports unchanged.
- **The runner needs zero edits.** `smoke/run_smoke.sh` derives NN from the basename (`sed -n 's/^smoke_\([0-9][0-9]*\)_.*/\1/p'`): `smoke_22_detector_coverage.py` => NN=22 => the verdict grep is exactly `=== SMOKE-22 PASS ===` in this run's per-invocation mktemp log; optional TIMEOUT arg (probe header itself recommends 240 s).
- **`geometry.GAME_PREFIX` is REAL** -- `aamatch/geometry.py:81` defines `GAME_PREFIX = '_aam_'`. The probe's `'clean pre-probe scene'` check (`not [n0 for n0 in pre_names if n0.startswith(geometry.GAME_PREFIX)]`) ports as-is; never invent a different name.
- **The new file automatically enters `tests/test_code_audit.py`'s smoke/ walk**: audit 2 (brute_force_pairs oracle isolation) and audit 4's `test_no_banned_call_sites` scan every `smoke/*.py`. The probe has ZERO banned calls (`get_model`/`matrix_reset`/`get_object_ttt`) and ZERO `brute_force_pairs` mentions. The prose-pin whitelist is scoped to `aamatch/` only, but the house rule still demands ZERO prose mentions of the banned tokens in the new file (no PROSE_PIN entry exists for smoke files; tests/ is untouchable) -- encode zero mentions, enforce via grep.
- **The naive-pair-loop gate cannot fire on a smoke file.** `find_nested_record_loops` is applied only to `aamatch/detector.py`; the probe's `for i in range(len(ns))` / `for j in range(i+1, len(ns))` porphyrin-normal construction is geometric-vector work and carries no atom/record token.
- **Baseline:** WSL suite 933/933 (quick-001 post-state); smokes 01-21 all pass headless under the hardened runner; MANIFEST entries `chloramphenicol` / `thyroxine` / `heme` confirmed present (08-07 bundling, 08-11 probe green, 08.1-07 battery green).

**Repo laws (binding):**
- WSL Ubuntu dev shell; `python3.6` for py_compile + unit tests ONLY. NEVER pip/apt/conda install; `rm` is denied by opencode.json.
- Headless smoke proof: `bash smoke/run_smoke.sh smoke/smoke_22_detector_coverage.py 240` from repo root.
- Smokes import `aamatch` directly (repo identity; never mix installed `pmg_tk.startup.aamatch` in the same session).
- **Do NOT touch:** smokes 01-21 (08.1-07 verdict: "KEEP smokes unchanged" -- no renumbering anywhere), `smoke/run_smoke.sh`, `aamatch/`, `tests/`, `.planning/codebase/`, ROADMAP.md, `tmp/detector_coverage_phase8.py` (git-ignored historical one-off; it stays byte-untouched as the 08-11 record), any opencode/config file. This plan is strictly **smoke-file-additive**.
- Commit style: `test(quick-002): fold phase-8 detector-coverage probe into standing SMOKE-22` -- a single atomic commit. Solo main-line is correct (single plan, no worktree protocol).
- Honest-deviation rule: if a scene check fails for an environmental reason, report it verbatim as a deviation and STOP -- never weaken checks, slacks, or thresholds to force green (verdict rule; also `tests/`, `aamatch/` are out of file scope anyway).
</context>

<tasks>

<task type="auto">
  <name>Task 1: Port tmp/detector_coverage_phase8.py into standing smoke/smoke_22_detector_coverage.py</name>
  <files>smoke/smoke_22_detector_coverage.py</files>
  <action>
    Read `tmp/detector_coverage_phase8.py` (482 lines) IN FULL first -- it is the authoritative port source. Create `smoke/smoke_22_detector_coverage.py` as a faithful line-level port: copy the import block, all helpers (`_sub`..`_unit`, `_alignment_matrix`, `_remap_ligand_bonds`, `_atom_positions`, `_scene_records_and_remap`, `_scene_features`, `_detect`, `_load_ligand`, `_place_halogen_scene`, `_place_metal_scene`, `_oe1_record`), the constant block (`LIG_OBJ = '_aam_tmp_lig'`, `AA_OBJ = '_aam_aatmp'`, `TARGET_D_AX = 3.3`, `TARGET_ACC_ANGLE = 120.0`, `TARGET_D_METAL = 2.5`, `METRIC_SLACK_D = 0.30`, `METRIC_SLACK_ANGLE = 12.0` -- same values), the manifest-entries preamble, all three try/finally scenes, and the leakage + verdict tail BYTE-IDENTICAL except exactly these mechanical renames:

    1. `_find_repo_root()`: `mine = 'detector_coverage_phase8.py'` -> `mine = 'smoke_22_detector_coverage.py'`. Keep the endswith/two-dirnames-up/cwd-fallback logic untouched (house pattern, smoke_02/smoke_21-identical).
    2. Print prefixes: `print('PROBE-ENV root:', ...)` -> `'SMOKE-ENV root:'`; `'PROBE-ENV pymol:'` -> `'SMOKE-ENV pymol:'`; `'PROBE-ENV python:'` -> `'SMOKE-ENV python:'`; `'PROBE-ENV %s donor:'` -> `'SMOKE-ENV %s donor:'` (house style per smoke_02/smoke_21).
    3. `check()` ledger line: `'PROBE %-44s %s %s'` -> `'SMOKE-22 %-44s %s %s'` (prefix rename only; the %-44s min-width is cosmetic and may stay).
    4. Check-name labels (printed labels only, nothing asserts on them): `'clean pre-probe scene'` -> `'clean pre-smoke scene'`; `'probe entries present'` -> `'smoke entries present'`.
    5. Verdict lines: both `PROBE VERDICT:` branches -> `SMOKE-22 VERDICT:`. Keep the informative text VERBATIM (the pass text "NO threshold surprise -- DETECT-03 provisional values hold on real data (...) no DETECTOR_VERSION bump proposal needed" is the 08-11 recorded verdict STATE.md carries, and the fail text "DETECTOR_VERSION bump PROPOSAL required -- failed checks: ..." names the fix path).
    6. Final marker (the SOLE verdict carrier -- the runner greps exactly this): `print('=== DETECTOR-COVERAGE PHASE-08 PASS ===', flush=True)` -> `print('=== SMOKE-22 PASS ===', flush=True)`. It stays in the `else` branch (prints ONLY when `failures` is empty).
    7. Docstring: replace the probe's 51-line docstring ENTIRELY with a new one (below). The probe docstring's "ONE-OFF ... NOT a smoke" and "This script prints NO '=== SMOKE-NN PASS ===' marker" prose is now FALSE and must not survive in any form.

    New docstring -- required content, written 3.6-safe plain text (adapt wording freely EXCEPT the quoted verdict-rule sentences below, which carry over verbatim in spirit):
    - Identity: Standing smoke 22 -- detector-coverage oracle over the bundled curated molecules (halogen + metal rows); before this, a count-level detector oracle existed only for benzamide (SMOKE-03/05).
    - Provenance: quick-002 (2026-10-03) folded the plan-08-11 Task 2 ONE-OFF probe (`tmp/detector_coverage_phase8.py`, git-ignored) into the standing battery -- same scenes, same constructed targets and slacks, same ledger/leak checks; only smoke-house prefixes and the SMOKE-22 marker changed.
    - Run line: `bash smoke/run_smoke.sh smoke/smoke_22_detector_coverage.py 240` (240 s: Windows loader startup + three SDF scenes); verdict carrier grep: `=== SMOKE-22 PASS ===`.
    - Purpose and the three scenes with their constructed targets and windows (chloramphenicol C-Cl: GLU OE1 at 3.3 A on the C->X extension, donor ~180 deg in [135,195], acc ~120 deg in [90,150], d_ax <= 4.0; thyroxine C-I: same construction; heme Fe: OE1 at 2.5 A along the porphyrin normal, metal record window (0.5, 3.0], distance-only row 7). State that windows come from imported thresholds constants, never hardcoded.
    - Heme formal-charge note: the bundled HEM_ideal.sdf derives formal_charge_sum -4 (08-07 honesty note: the proposal narrative said 'charge field 0'); printed AND pinned as a recorded input; does not affect the metal record (Fe typing is element-based).
    - VERDICT RULE (must carry over): any FAIL check fires, NO pass marker prints, and the fix path is a DETECTOR_VERSION bump PROPOSAL in a new plan, NEVER a silent edit of thresholds.py, detector.py or capability.py.
    - Scene hygiene (finally-delete + pre/post object-snapshot equality) and Python floor ("runs inside PyMOL's Windows Python 3.9; written 3.6-safe").
    - The docstring must NOT contain the tokens `get_model`, `matrix_reset`, or `get_object_ttt` anywhere (banned-token prose rule; no PROSE_PIN whitelist entry exists for smoke files).

    HARD RESTRICTIONS:
    - 3.6-safe syntax (the probe already is -- no f-strings, no walrus, no dataclasses). `python3.6 -m py_compile` must pass.
    - Do NOT restructure, reformat, or "improve" any logic -- the 08-11 verdict was produced by exactly this code; the port must be byte-faithful modulo the renames above.
    - Do NOT touch anything else: smokes 01-21, run_smoke.sh, aamatch/, tests/, the tmp/ probe, .planning/ docs, opencode/config files.
    - Per-scene 08-07 recorded input and thresholds imports stay exactly as in the probe.

    After all verify steps below pass, commit EXACTLY one file:
    ```
    git add smoke/smoke_22_detector_coverage.py
    git commit -m "test(quick-002): fold phase-8 detector-coverage probe into standing SMOKE-22"
    ```
  </action>
  <verify>
    From repo root, in this order:
    1. `python3.6 -m py_compile smoke/smoke_22_detector_coverage.py` -> exit 0, silent (3.6 syntax floor).
    2. `python3.6 -m unittest discover -s tests -v` -> OK, 933 tests, zero failures/errors. This run IS the proof the new file entered the code-audit walk: audit 2 (brute_force_pairs isolation) and audit 4 (`test_no_banned_call_sites`) now scan smoke_22 and are green over it.
    3. `grep -nE "get_model|matrix_reset|get_object_ttt" smoke/smoke_22_detector_coverage.py` -> 0 matches (banned tokens absent from code AND prose).
    4. `grep -n "PROBE" smoke/smoke_22_detector_coverage.py` -> 0 matches (all probe prefixes renamed; lowercase prose references to the historical probe in the docstring provenance lines are allowed).
    5. `grep -c "=== SMOKE-22 PASS ===" smoke/smoke_22_detector_coverage.py` -> exactly 1 (the marker).
    6. REAL headless proof (allow up to ~4 min): `bash smoke/run_smoke.sh smoke/smoke_22_detector_coverage.py 240; echo "exit=$?"` -> console tail shows the SMOKE-22 scene checks PASS (chloramphenicol, thyroxine, heme rows + 'heme formal_charge_sum == -4 (08-07 recorded input)' PASS), `zero object leakage ... PASS`, the informative `SMOKE-22 VERDICT: NO threshold surprise -- DETECT-03 provisional values hold on real data (...)` line, then `=== SMOKE-22 PASS ===`; `exit=0`. If any scene check FAILs: report the failing check lines verbatim as a deviation and STOP -- never weaken checks, slacks, or thresholds to force green (verdict rule; aamatch/ and tests/ are out of file scope).
    7. `git show --stat HEAD` -> exactly ONE file: smoke/smoke_22_detector_coverage.py (new), commit message exactly `test(quick-002): fold phase-8 detector-coverage probe into standing SMOKE-22`; `git status --porcelain` -> clean.
  </verify>
  <done>
    SMOKE-22 is a standing battery member: real headless run exits 0 with the `=== SMOKE-22 PASS ===` marker, the full DETECT-03 no-threshold-surprise verdict, and zero leakage; the runner picked NN=22 off the basename with zero edits; full WSL suite stays 933/933 including the code-audit walk over the new file; zero banned tokens in code or prose; the three scenes/constructed targets/slacks are byte-faithful to the probe; tmp/ probe and every other file untouched; single atomic test(quick-002) commit.
  </done>
</task>

</tasks>

<verification>
Overall gates, in order, from repo root (single task landed):
1. `python3.6 -m py_compile smoke/smoke_22_detector_coverage.py` -> exit 0.
2. `python3.6 -m unittest discover -s tests -v` -> 933 tests, OK, zero failures (purity gates + code audit incl. the new smoke file).
3. `bash smoke/run_smoke.sh smoke/smoke_22_detector_coverage.py 240` -> `=== SMOKE-22 PASS ===`, `SMOKE-22 VERDICT: NO threshold surprise -- DETECT-03 provisional values hold ...`, `zero object leakage ... PASS`, exit 0.
4. `git log --oneline -2` -> the quick-002 test commit on top of the quick-001 docs commit; `git show --stat HEAD` -> exactly one new smoke file.
5. `git status --porcelain` -> clean; `ls smoke/` -> smokes 01-21 unrenamed and untouched + the one new smoke_22 file.
</verification>

<success_criteria>
- The curated-molecules halogen/metal oracle is part of the standing battery: SMOKE-22 green headless through the standing runner (zero runner edits, zero renumbering, smokes 01-21 byte-untouched).
- The 08-11 verdict became mechanically re-provable: pass = "NO threshold surprise -- DETECT-03 provisional values hold" + SMOKE-22 marker; any fail check = NO marker + honest deviation report, with thresholds.py / detector.py / capability.py untouchable outside a versioned DETECTOR_VERSION bump proposal.
- Substance byte-faithful: same three scenes, same constructed targets (3.3 A / 180 deg / 120 deg / 2.5 A) and slacks (0.30 A / 12 deg), same thresholds imports, same heme -4 pin, same ledger/finally/leak contract; only smoke-house prefixes + marker changed.
- Full WSL suite 933/933; new file passes the 3.6 syntax floor; zero banned-token mentions (code or prose); single atomic `test(quick-002)` commit touching exactly one new file.
</success_criteria>

<output>
After completion, create `.planning/quick/002-detector-coverage-smoke/002-SUMMARY.md` recording: the SMOKE-22 run verdict (verbatim SMOKE-22 VERDICT + marker lines and the three scene rows + leakage line from the log), run duration, the WSL suite count (933 expected), the audit-walk observation (audit 2/4 now scan the new file, green), and zero deviations or any deviation reported honestly (fail-verdict rule honored -- no checks weakened). The orchestrator performs the final `docs(quick-002)` STATE.md commit.
</output>
