---
phase: quick-003
plan: 003
subsystem: api-hygiene
tags: [engine-api, checkpoint-io, memory, source-gates, AST-pin, registration-gate, CONCERNS]

provides:
  - "Documented public engine seam current_game / remap_ligand_bonds with legacy private names retained as module-level aliases ONLY (smokes 01-22 byte-frozen + green through the aliases)"
  - "tests/test_engine_public_api.py: AST source pin (4 tests) -- public defs present, privates are aliases not shadowing defs, zero engine.<private> calls outside engine.py, negative control"
  - "checkpoint read_checkpoint_zip streaming zf.extract .pse extraction (2x memory spike halved) with refusal-first order + cleanup-on-extract-refusal preserved"
  - "upload.py inside the PLAY-04 gate + TestCmdTierRegistration derived-set coverage pin (a new cmd-tier module can never again silently escape both registries)"
requires: "quick-001 (hardened runner + purity pins, 933-baseline), 08.1-07 KEEP-smokes law (smokes byte-frozen)"
affects: "All future engine consumers use the public names; any future cmd-tier module MUST register (UI -> SCANNED_MODULES, non-UI core -> NON_UI_CMD_CORE)"

tech-stack:
  added: []
  patterns:
    - "Promote-private-to-public with documented module-level alias for byte-frozen callers (alias ONLY for the standing smokes; new code calls public names)"
    - "Streamed zip member extraction via zf.extract inside the open-zip block, with rmtree cleanup on the extract-refusal branch before the same-family FormatError"
    - "Derived-set registry partition gate (listdir - PURE_MODULES - exempt == SCANNED_MODULES u NON_UI_CMD_CORE), quick-001 direction-2 pattern"

key-files:
  created:
    - tests/test_engine_public_api.py
  modified:
    - aamatch/engine.py
    - aamatch/gamestart.py
    - aamatch/game_window.py
    - aamatch/wizard.py
    - aamatch/upload.py
    - aamatch/checkpoint.py
    - tests/test_wizard_source.py

decisions:
  - "Alias placement: immediately under each promoted def's closing, one assignment line + one comment ('legacy private name, retained for the byte-frozen standing smokes' alias calls (08.1-07 KEEP-smokes law) -- never for new code (promoted quick-003)'); _current_registry deliberately NOT promoted (stays private, no alias)"
  - "Extract-refusal cleanup: tmp_dir is created BEFORE zf.extract, so the except (zipfile.BadZipFile, RuntimeError) branch MUST rmtree tmp_dir (ignore_errors=True) before raising -- the old code's mkdtemp-after-read ordering made the leak impossible; the new ordering makes the cleanup mandatory"
  - "CMD_TIER_EXEMPT = ['__init__']: the 01-01 composition root is gated by test_package_skeleton.py (zero-module-level-imports law), not by either registry"

metrics:
  duration: "~13 min (2026-10-03 18:43Z - 18:56Z; includes 4 real headless smoke runs)"
  completed: 2026-10-03
---

# Phase quick-003 Plan 003: API Hardening Bundle Summary

**One-liner:** Three residual CONCERNS.md API-hygiene items closed in one bundle: the engine's textual-only private seam became a documented public API (`current_game` / `remap_ligand_bonds`, private names kept as module-level aliases ONLY for the byte-frozen smokes), the checkpoint `.pse` read switched to streaming `zf.extract` inside the open-zip block (halving the 2x memory spike with refusal-first preserved), and `upload.py` -- the one cmd-tier module outside every registry -- was registered in the PLAY-04 scan with a derived-set coverage pin so the escape class cannot recur.

## Tasks Completed

| Task | Name | Commit | Files |
| ---- | ---- | ------ | ----- |
| 1 (A) | Promote engine._current_game/_remap_ligand_bonds to public API with documented aliases | 4262684 | aamatch/engine.py, aamatch/gamestart.py, aamatch/game_window.py, aamatch/wizard.py, aamatch/upload.py, tests/test_engine_public_api.py (new) |
| 2 (B) | Stream the checkpoint .pse extraction (zf.extract) instead of full-member RAM read | 88a4c05 | aamatch/checkpoint.py |
| 3 (C) | Register upload.py in the PLAY-04 scan + cmd-tier registration-coverage gate | 8948287 | tests/test_wizard_source.py |

## Verification Battery (all real, run from repo root)

**Per-task WSL gates:**

- Task 1: `python3.6 -m py_compile aamatch/*.py` -> clean; `python3.6 -m unittest discover -s tests` -> **Ran 937 tests, OK** (933 baseline + 4 new AST pin tests); `python3.6 -m unittest tests.test_engine_public_api -v` -> 4/4 ok; `grep -rn "engine\._current_game\|engine\._remap_ligand_bonds" aamatch/ --include='*.py'` -> **zero hits**; `grep -n "_current_game\|_remap_ligand_bonds" aamatch/engine.py` -> exactly the two alias lines + comments (nothing else).
- Task 2: py_compile clean; full suite **Ran 937 tests, OK** (unchanged total -- task adds zero tests; UNTOUCHED tests/test_checkpoint.py's 46 methods green inside it; purity gates green with shutil whitelisted at test_purity.py:115); grep gate: ZERO `zf.read(PSE_MEMBER`, exactly ONE `zf.extract(PSE_MEMBER, path=tmp_dir)` (line 379), exactly ONE `shutil.rmtree(tmp_dir, ignore_errors=True)` (line 381), the `os.path.join(tmp_dir, PSE_MEMBER)` manual write path GONE, `import shutil` present (line 84).
- Task 3: `python3.6 -m unittest tests.test_wizard_source -v` -> **8/8 ok** (5 pre-existing over the now-5-module scan set incl. upload.py + the 3 new TestCmdTierRegistration methods); `python3.6 -m py_compile aamatch/*.py` -> clean; full suite **Ran 940 tests, OK** (933 + 4 + 3); `git status` between tasks showed ONLY each task's declared files.

**Real headless smokes (the behavioral proofs):**

- Task 1 alias-contract proofs: `bash smoke/run_smoke.sh smoke/smoke_08_starter.py 180` -> **=== SMOKE-08 PASS ===** (all checks PASS, incl. both restart paths + part-5 compose + part-7 payload seam); `bash smoke/run_smoke.sh smoke/smoke_12_upload_e2e.py 120` -> **=== SMOKE-12 PASS ===** (upload parity probes + prepare/validate + MOL2-MULTI refusal verbatim). Both smokes call through the aliases (`engine._current_game` / `engine._remap_ligand_bonds`) with **zero smoke edits** -- smokes byte-frozen.
- Task 2 streamed-extract proof per SMOKE-20's documented TWO-RUN recipe at 240 s, header read first; fixture dir `tmp/smoke fixtures/aam_pse20/` was ABSENT pre-run, so the recipe ran clean with no contingency:
  - RUN 1 (`SMOKE-ENV phase: save`) -> **=== SMOKE-20 PASS ===** (12 checks: scripted pick + baked transforms + hint books + skip-record + snapshot elapsed 123.0 + save_checkpoint wrote game.aamz + expected-facts container; fixtures STAY).
  - RUN 2 (`SMOKE-ENV phase: verify`, fresh Windows PyMOL process) -> **=== SMOKE-20 PASS ===** (32 checks: dead-start proof, load_checkpoint adopt branch with books/status/registry/centroids/detect/timer-rebase asserts, continue-play confirm proof, forced-rebuild second load [predicate patched False: adopted False, rebuilt wizard, resume_from books, msm repair verified via pop], teardown removed fixtures). Run 2's `load_checkpoint -> read_checkpoint_zip` exercised the NEW `zf.extract` path end-to-end TWICE on the archive run 1 saved (adopt + forced-rebuild) -- the streamed extract is the only read path that ran.
- Contingency re-runs: none needed (no leftover fixture from an interrupted battery).

**Mutation proof (Task 3, mandatory, NEVER committed):** temporarily dropped `'wizard.py'` from SCANNED_MODULES via the edit tool; `python3.6 -m unittest tests.test_wizard_source -v` tripped EXACTLY ONE failure while the visual scans stayed green -- verbatim:

```
======================================================================
FAIL: test_every_cmd_tier_module_is_registered (tests.test_wizard_source.TestCmdTierRegistration)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/mnt/c/Users/nglok/Desktop/WORKDIR/molmdl/AA-match/tests/test_wizard_source.py", line 269, in test_every_cmd_tier_module_is_registered
    % unregistered)
AssertionError: Lists differ: ['wizard'] != []

First list contains 1 additional elements.
First extra element 0:
'wizard'

- ['wizard']
+ [] : cmd-tier module(s) outside EVERY registry: ['wizard'] -- a new cmd-tier module must register: a new UI module goes into SCANNED_MODULES (the PLAY-04 scans); a new deliberately non-UI core module goes into NON_UI_CMD_CORE; never both

----------------------------------------------------------------------
Ran 8 tests in 0.109s

FAILED (failures=1)
```

The trip proves the NEW gate is the one firing (wizard leaving the scan does NOT fail the visual scans) and that it names the offender. Registration restored verbatim; re-ran to 8/8 green; post-restore `git diff` showed only the intended additions (SCANNED_MODULES entry + constants + helpers + TestCase).

## Deviations from Plan

**None.** Plan executed exactly as written: 3 atomic commits in A -> B -> C order with the plan's commit types/messages, ONLY the 8 declared files touched in total, smokes 01-22 byte-untouched (aliases are precisely what kept them green), zero environmental failures, zero follow-up fixes.

## Authentication Gates

None.

## Must-Haves Self-Check (plan frontmatter truths)

1. **Every production caller on public names; only the alias block mentions privates in engine.py** -- grep-verified (zero `engine.<private>` hits in aamatch/*.py; engine.py's only `_current_game`/`_remap_ligand_bonds` mentions are the two alias lines + comments). PASS.
2. **Byte-frozen smokes keep working through the aliases** -- SMOKE-08 PASS + SMOKE-12 PASS, zero smoke edits. PASS.
3. **read_checkpoint_zip streams game.pse via zf.extract; zf.read(PSE_MEMBER) gone** -- grep-verified; extract inside the open-zip block using the returned path. PASS.
4. **Refusal-first + contract preserved in Task 2** -- every sidecar gate precedes extraction; extract-refusal rmtree(ignore_errors=True) + same-family FormatError; signature/return/caller-owns-rmtree unchanged; 46 checkpoint tests green UNTOUCHED. PASS.
5. **SMOKE-20 two-run recipe BOTH PASS** -- run 1 SAVE + run 2 VERIFY (fresh process load_checkpoint on the run-1 archive = the new streamed-extract path). PASS.
6. **upload.py inside the PLAY-04 gate, both scans green** -- 5-module scan set, 8/8 direct run. PASS.
7. **Cmd-tier roster pinned + mutation-proven** -- derived set EXACTLY partitioned into SCANNED_MODULES u NON_UI_CMD_CORE with __init__ exempt; mutation trip recorded verbatim above; never committed. PASS.
8. **Full WSL suite ALL-GREEN per task with real counts** -- 937 / 937 / 940 reported above. PASS.

## Next Phase Readiness

- New code calling the engine must use `current_game` / `remap_ligand_bonds`; the private alias names are marked never-for-new-code and the AST pin fires on any `engine.<private>` call outside engine.py.
- A new cmd-tier module fails `test_every_cmd_tier_module_is_registered` loudly by name until registered: UI module -> SCANNED_MODULES; deliberately non-UI core -> NON_UI_CMD_CORE; never both (overlap is separately pinned).
- Standalone-battery plans continue to expect smokes 01-22 plus the 933-baseline-plus-this-plan's 940-test WSL suite as the green reference (quick-002's 22-smoke battery, quick-003's 937 -> 940 suite).
- If a larger .pse ever makes even streamed extraction interesting, the next step is caller-side (e.g. direct cmd.load from the zip handle) -- out of scope here; the current task closed the RAM double-buffer only, per plan.
