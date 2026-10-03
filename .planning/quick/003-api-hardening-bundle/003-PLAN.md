---
phase: quick-003
plan: 003
type: execute
wave: 1
depends_on: []
files_modified: [aamatch/engine.py, aamatch/gamestart.py, aamatch/game_window.py,
                 aamatch/wizard.py, aamatch/upload.py, tests/test_engine_public_api.py,
                 aamatch/checkpoint.py, tests/test_wizard_source.py]
autonomous: true

must_haves:
  truths:
    - "Every production caller of the promoted engine helpers uses the PUBLIC names after Task 1: `grep -rn 'engine\\._current_game\\|engine\\._remap_ligand_bonds' aamatch/` returns ZERO hits, and inside aamatch/engine.py the ONLY remaining `_current_game`/`_remap_ligand_bonds` mentions are the two module-level alias assignments + their comments"
    - "The byte-frozen smokes keep working through the aliases: SMOKE-08 (`bash smoke/run_smoke.sh smoke/smoke_08_starter.py 180`) and SMOKE-12 (`bash smoke/run_smoke.sh smoke/smoke_12_upload_e2e.py 120`) both print their PASS markers with ZERO smoke edits -- a smoke failure after Task 1 means the alias contract broke; fix the alias, NEVER the smoke"
    - "read_checkpoint_zip streams game.pse to disk: the `zf.read(PSE_MEMBER)` full-member RAM read is GONE, replaced by `zf.extract(PSE_MEMBER, path=tmp_dir)` inside the open-zip block using the returned path"
    - "Refusal-first + contract preserved in Task 2: every sidecar gate still precedes extraction; an extract-time BadZipFile/RuntimeError cleans the fresh tmp_dir via `shutil.rmtree(tmp_dir, ignore_errors=True)` and raises FormatError in the same 'not an AA-match archive (unreadable zip: %s)' family; signature/return/caller-owns-rmtree-on-success unchanged, so tests/test_checkpoint.py (46 test methods) stays green UNTOUCHED (never edit existing tests to fit)"
    - "SMOKE-20 per its documented TWO-RUN recipe at 240 s: BOTH invocations print `=== SMOKE-20 PASS ===` -- run 2's fresh Windows PyMOL process load_checkpoint -> read_checkpoint_zip exercises the new streamed-extract path end-to-end on the archive run 1 just saved"
    - "upload.py sits inside the PLAY-04 gate after Task 3 (SCANNED_MODULES = [wizard, gamestart, setup_window, game_window, upload]) and BOTH scans stay green over it -- zero banned visual CALLS + zero banned matrix-token PROSE (pre-verified in planning)"
    - "The cmd-tier roster is pinned: the derived set (aamatch/*.py basenames minus PURE_MODULES minus __init__) is EXACTLY partitioned into SCANNED_MODULES u NON_UI_CMD_CORE {engine, geometry, placement} -- a NEW cmd-tier module can never again silently escape both registries; the pin is mutation-proven (temporarily dropping 'wizard.py' FAILS it naming wizard; restore re-greens) with the trip recorded in 003-SUMMARY.md"
    - "Full WSL suite ALL-GREEN after each task with the REAL total reported in the SUMMARY (baseline 933 + Task 1's new AST tests + Task 3's new registration tests; expect roughly 936-940 -- report actuals)"
  artifacts:
    - path: "tests/test_engine_public_api.py"
      provides: "AST source-scan pin of the promoted seam: public FunctionDefs present, private names are module-level alias Assigns (NOT defs), zero engine.<private> attribute calls outside engine.py, plus a synthetic negative control proving the finder fires"
      contains: "current_game"
    - path: "aamatch/engine.py"
      provides: "public current_game / remap_ligand_bonds with documented legacy private aliases; all engine-internal callers on the public names"
      contains: "_current_game = current_game"
    - path: "aamatch/checkpoint.py"
      provides: "streamed zf.extract .pse read + shutil cleanup-on-extract-refusal (shutil joins json/os/tempfile/zipfile in the stdlib imports)"
      contains: "zf.extract(PSE_MEMBER"
    - path: "tests/test_wizard_source.py"
      provides: "upload.py registration in SCANNED_MODULES (dated comment) + TestCmdTierRegistration coverage gate importing PURE_MODULES from tests.test_purity"
      contains: "upload.py"
  key_links:
    - from: "the byte-frozen smokes' alias calls (engine._current_game in 08/11/15/16/17/19; engine._remap_ligand_bonds in 05/12/16; smoke_04's prose mention)"
      to: "engine.py's alias block"
      via: "module-level assignments _current_game = current_game / _remap_ligand_bonds = remap_ligand_bonds -> the ONLY thing keeping smokes 01-22 byte-unchanged green"
      pattern: "_current_game = current_game"
    - from: "aamatch production modules (gamestart:409 incl. its :26 docstring reference, game_window:415/:449, wizard:516, upload:153-154 incl. its :35 docstring reference)"
      to: "engine.py's public API"
      via: "engine.current_game() / engine.remap_ligand_bonds( -- the former textual-only private seam becomes the documented public seam"
      pattern: "engine.current_game()"
    - from: "read_checkpoint_zip's extract-refusal branch"
      to: "no-leak cleanup"
      via: "shutil.rmtree(tmp_dir, ignore_errors=True) before raising the same-family FormatError (ckpt.py did not import shutil before; it is whitelisted in test_purity.py ALLOWED_STDLIB:115)"
      pattern: "rmtree\\(tmp_dir, ignore_errors=True\\)"
    - from: "TestCmdTierRegistration (Task 3)"
      to: "tests/test_purity.py PURE_MODULES"
      via: "from tests.test_purity import PURE_MODULES; derived cmd-tier set = sorted(aamatch/*.py basenames - PURE_MODULES - {'__init__'}); ANY new module auto-lands in the set and FAILS until registered -- quick-001's direction-2 coverage-gate pattern"
      pattern: "from tests.test_purity import PURE_MODULES"
---

<objective>
Close three residual API-hygiene concerns from `.planning/codebase/CONCERNS.md` in one atomic bundle:
(A) promote the two engine private helpers `_current_game` / `_remap_ligand_bonds` to a documented public API (`current_game` / `remap_ligand_bonds`) with private names retained as documented module-level aliases for the byte-frozen smokes, moving every production + engine-internal caller to the public names;
(B) switch the checkpoint `.pse` read from a full-member RAM read (`zf.read`) to streaming `zf.extract` inside the open-zip block, halving the 2x memory spike while preserving refusal-first order and the exact I/O contract;
(C) register the one missing cmd-tier module (`upload.py`) in the PLAY-04 source-scan set and add a registration-coverage gate so a new cmd-tier module can never again silently escape both registries.

Purpose: the engine module seam is currently textual/docstring-only (5 production files call entered privates), the checkpoint read double-buffers a potentially large `.pse` in RAM, and the audit registry has exactly one module silently outside every gate -- all three are recurring-audit residues with zero behavior change intended, provable by the standing gates.
Output: 3 atomic commits (`refactor(quick-003):` / `perf(quick-003):` / `test(quick-003):`), ONE new test file `tests/test_engine_public_api.py`, edits to `aamatch/engine.py`, `aamatch/checkpoint.py`, 5 production call-site files, `tests/test_wizard_source.py`. Nothing else changes.
</objective>

<execution_context>
@~/.config/opencode/get-shit-done/workflows/execute-plan.md
@~/.config/opencode/get-shit-done/templates/summary.md
</execution_context>

<context>
@AGENTS.md
@.planning/STATE.md
@aamatch/engine.py
@aamatch/checkpoint.py
@tests/test_wizard_source.py
@tests/test_purity.py
@aamatch/gamestart.py
@aamatch/game_window.py
@aamatch/wizard.py
@aamatch/upload.py

**Established facts (all spot-checked 2026-10-03/04, no research needed):**

- **Definitions to promote:** `aamatch/engine.py:144` `def _current_game():` and `:160` `def _remap_ligand_bonds(records, lig_objects):`. `_current_registry` at `:152` is **NOT in scope** -- it stays private and untouched.
- **Production external call sites (full verified list):** `aamatch/gamestart.py:409` (`engine._current_game().start_timer(time.time())`, docstring reference at `:26`), `aamatch/game_window.py:415` + `:449` (`engine._current_game()` reads / `rebase_timer`), `aamatch/wizard.py:516` (`gs = engine._current_game()`), `aamatch/upload.py:153-154` (`engine._remap_ligand_bonds(...)` call, docstring reference at `:35`).
- **Engine-internal call sites:** `_remap_ligand_bonds(` at engine.py:261/454/486/527; `_current_game()` at :542/583/609/620/627/667/699/717/736/743/753. All inside function bodies -- late-bound, safe to call public defs declared anywhere at module level.
- **Smoke alias dependence (08.1-07 law "KEEP smokes unchanged" -- smokes 01-22 are byte-frozen):** `engine._current_game()` in smokes 08/11/15/16/17/19; `engine._remap_ligand_bonds` in smokes 05/12/16; smoke_04:100 carries a PROSE mention (`engine.engine._remap_ligand_bonds`, pre-existing wording) -- all stay valid through the aliases. If a smoke FAILS after Task 1, the alias contract broke: fix the alias, NEVER the smoke.
- **CRITICAL WSL constraint:** `tests/` CANNOT import `aamatch/engine.py` (it imports pymol; WSL has no PyMOL) and the purity law forbids sys.modules stubs (01-08 law). House precedent for source-scan tests: `tests/test_wizard_source.py`, `tests/test_package_skeleton.py`, `tests/test_code_audit.py` (AST-based, zero imports of the scanned target).
- **PROSE_PIN hazard (tests/test_code_audit.py:64-69):** exact prose counts are pinned: `('placement.py','matrix_reset'): 3`, `('engine.py','matrix_reset'): 2`, `('placement.py','get_object_ttt'): 1`, `('geometry.py','get_model'): 1`. Do NOT add/remove ANY mention of `get_model`/`matrix_reset`/`get_object_ttt` in ANY docstring you touch. Additionally `tests/test_wizard_source.py`'s `test_no_banned_matrix_token_mentions` (lines 180-192) requires ZERO mentions of those tokens in EVERY SCANNED_MODULES file (prose included) -- wizard.py already obeys; do not add such prose there.
- **Checkpoint shape (aamatch/checkpoint.py:336-380 `read_checkpoint_zip`):** with-block does gates (namelist -> sidecar `zf.read` -> `json.loads` -> `parse_checkpoint_data`), then `pse_bytes = zf.read(PSE_MEMBER)` (line 372, FULL member into RAM); AFTER the with-block: `tmp_dir = tempfile.mkdtemp(prefix='aamatch_checkpoint_')` + manual byte write (:376-379); caller owns rmtree on success (docstring says so). Current imports: json/os/tempfile/zipfile + `.game_file` + `.persistence` pieces.
- **`shutil` purity status:** whitelisted in `tests/test_purity.py` ALLOWED_STDLIB (line 115, verified) -- adding the import keeps all purity gates green. Update the checkpoint.py module docstring's import roster (line 4-5) when you add it.
- **SMOKE-20 two-run recipe (verify by reading its header):** fixtures live in the git-ignored `tmp/smoke fixtures/aam_pse20/`; run 1 = SAVE (fixture absent, writes `game.aamz`, fixtures STAY), run 2 = VERIFY (fresh Windows PyMOL process: `load_checkpoint` -> `read_checkpoint_zip`, then teardown deletes the fixtures). Both invocations print `=== SMOKE-20 PASS ===`. A leftover fixture (interrupted battery) makes the next run a VERIFY run -- see Task 2's contingency.
- **test_wizard_source.py structure:** `SCANNED_MODULES` at lines 51-55; `find_visual_calls` + `test_no_banned_matrix_token_mentions` scan EVERY module in the set; negative-control rule in-file ("a gate that cannot fail proves nothing", lines 16-19); sys.path bootstrap at lines 42-46 inserts REPO_ROOT; `tests/__init__.py` exists so `from tests.test_purity import PURE_MODULES` works under `python3.6 -m unittest discover -s tests`.
- **Cmd-tier roster (verified by ls):** 28 `*.py` files in aamatch/ = 19 PURE_MODULES (tests/test_purity.py:99-103) + `__init__` + exactly 8 cmd-tier: engine, geometry, placement, wizard, gamestart, upload, setup_window, game_window. engine/geometry/placement are deliberately non-UI core (banned-token prose pinned in PROSE_PIN instead); `upload.py` is the ONE module missing from any registry, and it is PRE-VERIFIED clean for both scans (zero banned visual tokens, zero banned matrix-token prose).
- **Baseline:** full WSL suite 933/933 (quick-002 post-state); `python3.6 -m py_compile aamatch/*.py` green; smokes 01-22 all pass headless under the hardened runner (which FAILs on a missing per-run marker -- exit 0 is meaningful again).

**Repo laws (binding):**
- WSL Ubuntu dev shell; `python3.6` for py_compile + unit tests ONLY. NEVER pip/apt/conda install; `rm` denied by opencode.json (mutation proofs: edit + revert via the edit tool, never rm).
- Purity gates NOT weakened: zero sys.modules stubs anywhere; PURE_MODULES list in test_purity.py UNTOUCHED by this plan.
- Smokes 01-22 byte-unchanged (aliases are precisely what keeps them green).
- Do NOT touch: ROADMAP.md, `.planning/codebase/`, ROADMAP, opencode/config files, `tmp/` fixtures (except as consumed by SMOKE-20 itself), any other `tests/` file than the ones named.
- Solo main-line (single plan, no worktree protocol). Commit style per task, atomic: Task 1 `refactor(quick-003): promote engine current_game/remap_ligand_bonds to public API (private aliases kept for standing smokes)`; Task 2 `perf(quick-003): stream checkpoint .pse extraction (zf.extract) instead of full-member RAM read`; Task 3 `test(quick-003): register upload.py in PLAY-04 scan + cmd-tier coverage pin`.
</context>

<tasks>

<task type="auto">
  <name>Task 1 (A): Promote engine._current_game/_remap_ligand_bonds to public API with documented aliases</name>
  <files>aamatch/engine.py, aamatch/gamestart.py, aamatch/game_window.py, aamatch/wizard.py, aamatch/upload.py, tests/test_engine_public_api.py</files>
  <action>
    1. **Rename the two defs in `aamatch/engine.py`** (and NOTHING else in the file's API surface -- `_current_registry` at :152 stays private and untouched):
       - `def _current_game():` (line 144) -> `def current_game():`; reword its docstring to public-API wording (behavior-stated truth unchanged: live GameState created by new_game, EngineError before).
       - `def _remap_ligand_bonds(records, lig_objects):` (line 160) -> `def remap_ligand_bonds(records, lig_objects):`; reword its docstring from "Productionized SMOKE-03 remap helper" to the public seam wording, KEEPING the full technical contract (02-13 pattern, 0-based walk-position bonding mapping, the `(lig_records, lig_bonds)` return shapes).
       - Directly under each public def's closing, add the documented module-level alias with a one-line comment, e.g.:
         `_current_game = current_game  # legacy private name, retained for the byte-frozen standing smokes' alias calls (08.1-07 KEEP-smokes law) -- never for new code (promoted quick-003)`
         and identically `_remap_ligand_bonds = remap_ligand_bonds`.
       - Update ALL engine-internal call sites to the public names: `_remap_ligand_bonds(` at :261/:454/:486/:527 -> `remap_ligand_bonds(`; `_current_game()` at :542/:583/:609/:620/:627/:667/:699/:717/:736/:743/:753 -> `current_game()` (line numbers are pre-edit; grep, do not trust blindly after edits). Also update any engine.py DOCSTRING prose mentioning the private names to the public names.
       - PROSE_PIN guard while editing: do NOT add/remove any mention of `get_model`/`matrix_reset`/`get_object_ttt` anywhere. engine.py must keep exactly its 2 `matrix_reset` prose mentions.
    2. **Update the production call sites to the public names** (mechanical renames only, no docstring drive-bys beyond these):
       - `aamatch/gamestart.py:409`: `engine._current_game().start_timer(...)` -> `engine.current_game()...`; the `:26` docstring reference -> public name.
       - `aamatch/game_window.py:415` and `:449`: `engine._current_game()` -> `engine.current_game()`.
       - `aamatch/wizard.py:516`: `gs = engine._current_game()` -> `gs = engine.current_game()`. wizard.py zero-mention law: add NO `get_model`/`matrix_reset`/`get_object_ttt` prose while touching the file.
       - `aamatch/upload.py:153-154`: `engine._remap_ligand_bonds(` -> `engine.remap_ligand_bonds(`; the `:35` docstring reference -> public name.
       - Do NOT touch ANY smoke file (smoke_04's prose `engine.engine._remap_ligand_bonds` mention stays valid through the alias).
    3. **Create `tests/test_engine_public_api.py`** -- an AST SOURCE-scan test (WSL cannot import `aamatch/engine.py`; zero imports of aamatch, zero sys.modules stubs -- follow the `tests/test_wizard_source.py` skeleton: module docstring telling the seam contract story [privates promoted quick-003; aliases retained only for the byte-frozen smokes; new code uses public names only], the `_HERE`/REPO_ROOT/PKG_DIR + sys.path bootstrap pattern at its lines 42-46, `_read_source` helper):
       - A pure finder `find_private_engine_calls(src)`: walk every `ast.Call`; flag when `node.func` is an `ast.Attribute` whose `attr` is `'_current_game'` or `'_remap_ligand_bonds'` and whose value chain resolves to Name id `'engine'` (walk `.value` until an `ast.Name`; the production pattern is `engine._current(...)`). Return line-annotated problem strings.
       - `test_public_functions_defined`: parse `aamatch/engine.py`; top-level FunctionDef names MUST include `current_game` and `remap_ligand_bonds`.
       - `test_privates_are_module_level_aliases`: top-level `ast.Assign` nodes bind `_current_game = current_game` and `_remap_ligand_bonds = remap_ligand_bonds` (target Name id + value Name id), AND NO FunctionDef named `_current_game`/`_remap_ligand_bonds` exists anywhere in the module (they must be aliases, not shadowing defs).
       - `test_no_private_engine_calls_outside_engine`: for every `aamatch/*.py` EXCEPT `engine.py`, `find_private_engine_calls(source) == []` (list files via sorted os.listdir of PKG_DIR; use the `_read_source` helper).
       - `test_finder_fires_on_negative_control` (house rule: a gate that cannot fail proves nothing): a synthetic source string containing `engine._current_game()` and `engine._remap_ligand_bonds(r, l)` yields EXACTLY 2 findings, plus a `game._current_game()`-style non-engine line proves the value-chain scoping (ignored) -- mirror `test_wizard_source.py`'s VISUAL_TRAP discipline.
       - 3-4 test methods is right (the four pins above are the contract; report the real count in the SUMMARY). The file must be discovered by `python3.6 -m unittest discover -s tests` and add no banned-token prose of its own.
  </action>
  <verify>
    1. `python3.6 -m py_compile aamatch/*.py` -> clean.
    2. `grep -rn "engine\._current_game\|engine\._remap_ligand_bonds" aamatch/` -> ZERO hits.
    3. `grep -n "_current_game\|_remap_ligand_bonds" aamatch/engine.py` -> ONLY the two alias lines + their comments.
    4. `python3.6 -m unittest discover -s tests -v` -> ALL green; REPORT the real total (expect 933 + 3-4 new; the PROSE_PIN / purity gates re-prove the token discipline automatically).
    5. `python3.6 -m unittest tests.test_engine_public_api -v` -> all 4 pins green (quick direct run).
    6. Real smokes (both mandatory -- they are the alias-contract proofs): `bash smoke/run_smoke.sh smoke/smoke_08_starter.py 180` -> exit 0 with `=== SMOKE-08 PASS ===`; `bash smoke/run_smoke.sh smoke/smoke_12_upload_e2e.py 120` -> exit 0 with `=== SMOKE-12 PASS ===` (hardened runner FAILs on missing marker, so exit 0 carries the verdict).
    7. `git status` shows ONLY: aamatch/engine.py, aamatch/gamestart.py, aamatch/game_window.py, aamatch/wizard.py, aamatch/upload.py, tests/test_engine_public_api.py. Then commit: `refactor(quick-003): promote engine current_game/remap_ligand_bonds to public API (private aliases kept for standing smokes)`.
  </verify>
  <done>
    Public `current_game` / `remap_ligand_bonds` are the real implementations with documented private aliases; all 5 production call sites + all engine-internal sites use public names; zero `engine._current_game`/`engine._remap_ligand_bonds` attribute calls outside engine.py; the new AST pin file passes (4 pins + negative control); SMOKE-08 and SMOKE-12 PASS with byte-untouched smokes; full suite green at the reported real count.
  </done>
</task>

<task type="auto">
  <name>Task 2 (B): Stream the checkpoint .pse extraction (zf.extract) instead of full-member RAM read</name>
  <files>aamatch/checkpoint.py</files>
  <action>
    1. Add `shutil` to checkpoint.py's stdlib import block and update the module docstring's import roster (line 4-5: "imports stdlib json/os/tempfile/zipfile + ..." -> include shutil; the "zipfile is whitelisted in tests/test_purity.py ALLOWED_STDLIB" sentence extends naturally). Purity gates stay green -- shutil IS whitelisted (test_purity.py:115, verified in planning).
    2. Rework `read_checkpoint_zip` (lines 336-380). The gates stay in EXACT refusal-first order; only the extraction half changes:
       - DELETE the `pse_bytes = zf.read(PSE_MEMBER)` try/except (lines 371-375) and the post-with block (lines 376-379: `tmp_dir = tempfile.mkdtemp(...)`, `pse_path = os.path.join(tmp_dir, PSE_MEMBER)`, the `open(...,'wb')` byte write).
       - INSIDE the `with zf:` block, immediately after `data = parse_checkpoint_data(container)` (line 370), insert:
         ```python
             tmp_dir = tempfile.mkdtemp(prefix='aamatch_checkpoint_')
             try:
                 pse_path = zf.extract(PSE_MEMBER, path=tmp_dir)
             except (zipfile.BadZipFile, RuntimeError) as exc:
                 shutil.rmtree(tmp_dir, ignore_errors=True)
                 raise FormatError(
                     'not an AA-match archive (unreadable zip: %s)' % exc)
         ```
       - Use the RETURNED path from `zf.extract` (it is the full path to the created file) and keep `return pse_path, data` at the end of the function body (pse_path/data are function-scoped and survive the with-block) -- extraction MUST happen inside the open-zip block because zf.extract requires the open handle; do NOT broaden the except family beyond `(zipfile.BadZipFile, RuntimeError)` (it mirrors the module's two existing except clauses at :361-365; verified-findings contract -- no scope creep).
       - Old-vs-new failure-mode note (encode in the code order, no comment invention needed): the OLD code leaked nothing on extract failure because mkdtemp ran after the read; the NEW code creates tmp_dir first, so the except branch MUST rmtree before raising. `ignore_errors=True` is best-effort cleanup that never masks the FormatError.
       - Update the `read_checkpoint_zip` docstring: game.pse is STREAMED to disk by `zf.extract` inside the open-zip block (no full-member RAM read -- the 2x memory spike is halved); refusal-first preserved (every sidecar gate precedes extraction); the CALLER owns the rmtree on success while an extract-time refusal cleans its own tmp_dir. Keep the v1 read_bcmz provenance reference.
    3. Contract UNCHANGED: signature `read_checkpoint_zip(zip_path)`, return `(extracted_pse_path, parsed_data)`, `.aamz` refusal message families byte-identical (`'not an AA-match archive (unreadable zip: %s)'`), caller-owns-rmtree-on-success. `tests/test_checkpoint.py` (46 test methods) must stay green UNTOUCHED -- tests pin behavior, never edit them to fit.
  </action>
  <verify>
    1. `python3.6 -m py_compile aamatch/*.py` -> clean.
    2. `python3.6 -m unittest discover -s tests -v` -> ALL green INCLUDING the UNTOUCHED tests/test_checkpoint.py; total identical to Task 1's total (this task adds ZERO tests); purity gates green (shutil whitelisted).
    3. `grep -n "zf.read\|zf.extract\|shutil\|os.path.join(tmp_dir" aamatch/checkpoint.py` -> ZERO `zf.read(PSE_MEMBER`; exactly ONE `zf.extract(PSE_MEMBER, path=tmp_dir)`; exactly ONE `shutil.rmtree(tmp_dir, ignore_errors=True)`; the `os.path.join(tmp_dir, PSE_MEMBER)` manual write path is GONE; `import shutil` present.
    4. Real smoke (the ONLY behavioral proof, mandatory): FIRST read `smoke/smoke_20_checkpoint_e2e.py`'s header -- the documented recipe is TWO separate `run_smoke.sh` invocations at 240 s (each is a separate Windows PyMOL process; run 2 IS the quit->relaunch half). From repo root: `bash smoke/run_smoke.sh smoke/smoke_20_checkpoint_e2e.py 240` TWICE in immediate succession; BOTH invocations must exit 0 with `=== SMOKE-20 PASS ===`. Run 1 = SAVE (writes `tmp/smoke fixtures/aam_pse20/game.aamz`, fixtures STAY); run 2 = VERIFY (fresh process: `load_checkpoint` -> `read_checkpoint_zip` exercises the NEW streamed-extract path end-to-end on the archive run 1 saved; its teardown deletes the fixtures). Contingency: if run 1 reports VERIFY mode (a leftover fixture from an interrupted earlier battery sits in `tmp/smoke fixtures/aam_pse20/`), let it run to PASS (it exercises the new read path + its teardown clears the fixture), THEN execute the full two-run pair -- every invocation must print PASS, and note the extra run in the SUMMARY.
    5. `git status` shows ONLY aamatch/checkpoint.py. Then commit: `perf(quick-003): stream checkpoint .pse extraction (zf.extract) instead of full-member RAM read`.
  </verify>
  <done>
    read_checkpoint_zip streams `game.pse` straight to disk via `zf.extract` inside the open-zip block using the returned path; refusal-first order and every sidecar gate precede extraction exactly as before; an extract-time BadZipFile/RuntimeError cleans its own tmp_dir via `shutil.rmtree(ignore_errors=True)` and raises the same-family FormatError; signature/return/caller-owns-rmtree-on-success unchanged; the 46 untouched checkpoint tests stay green; SMOKE-20's save + verify runs BOTH print `=== SMOKE-20 PASS ===`.
  </done>
</task>

<task type="auto">
  <name>Task 3 (C): Register upload.py in the PLAY-04 scan + add the cmd-tier registration-coverage gate</name>
  <files>tests/test_wizard_source.py</files>
  <action>
    1. Add `'upload.py'` to `SCANNED_MODULES` (lines 51-55) with a dated comment, e.g. `'upload.py']  # quick-003 (2026-10-04): upload.py -- the last cmd-tier module missing from any registry (pre-verified clean for both scans)`. Both standing scans (`find_visual_calls` CALL sites + `test_no_banned_matrix_token_mentions` PROSE) now apply to upload.py and must stay green -- pre-verified in planning (upload.py has zero banned visual tokens + zero banned matrix-token prose; confirmed by grep).
    2. Add the registration-coverage gate right after the SCANNED_MODULES block:
       - Two documented constants: `NON_UI_CMD_CORE = ['engine', 'geometry', 'placement']` (deliberately non-UI core; their banned-token prose allowances are pinned in tests/test_code_audit.py's PROSE_PIN instead) and `CMD_TIER_EXEMPT = ['__init__']` (the 01-01 composition root -- zero-module-level-imports law gates it via test_package_skeleton.py; it is neither a pure module nor a cmd-tier module to scan).
       - Import `PURE_MODULES` via `from tests.test_purity import PURE_MODULES` (the file's lines 42-46 bootstrap already inserts REPO_ROOT; `tests/__init__.py` exists).
       - A derived-set helper + a new TestCase `TestCmdTierRegistration`:
         a. `test_every_cmd_tier_module_is_registered`: derive cmd_tier = sorted(set(basename of every aamatch/*.py) - set(PURE_MODULES) - set(CMD_TIER_EXEMPT)) (listdir-based, the quick-001 direction-2 pattern -- ANY new module automatically lands in the derived set); registered = set(SCANNED_MODULES names minus '.py') | set(NON_UI_CMD_CORE); assert the unregistered remainder == [] with a message NAMING any offender + the policy (new UI module -> SCANNED_MODULES; new core module -> NON_UI_CMD_CORE; never both).
         b. `test_registered_modules_all_exist`: every registered name must exist as `aamatch/<name>.py` (guards registry rot on rename/delete).
         c. `test_no_registry_overlap`: SCANNED_MODULES-derived names and NON_UI_CMD_CORE are disjoint.
       - Document the today-partition in the constants' comments: derived set = exactly [engine, game_window, gamestart, geometry, placement, setup_window, upload, wizard] (8 = 28 files - 19 PURE_MODULES - `__init__`, verified by ls in planning).
    3. MANDATORY mutation proof (quick-001 precedent; NEVER committed): via the edit tool (never rm), temporarily drop `'wizard.py'` from SCANNED_MODULES -> run `python3.6 -m unittest tests.test_wizard_source -v` -> `test_every_cmd_tier_module_is_registered` MUST FAIL with wizard named as unregistered (wizard leaving the scan does NOT fail the visual scans -- prove the NEW gate is the one firing) -> restore the exact original registration -> re-run to green. Record the mutation trip (test name + failure message verbatim) in the SUMMARY.
  </action>
  <verify>
    1. `python3.6 -m unittest tests.test_wizard_source -v` -> ALL green: the pre-existing 5 tests over the now-5-module scan set (both scans green over upload.py) + the new TestCmdTierRegistration (3 methods).
    2. Mutation proof executed and REVERTED: `grep -n "upload.py" tests/test_wizard_source.py` shows the registration present; `git diff` after the restore shows ONLY the intended additions (SCANNED_MODULES entry + constants + new TestCase).
    3. `python3.6 -m unittest discover -s tests -v` -> ALL green; REPORT the real total (expect Task 1's total + 3).
    4. `python3.6 -m py_compile aamatch/*.py` -> clean cheap floor (no aamatch edits in this task -- git status confirms zero accidental touches; `git status` must show ONLY tests/test_wizard_source.py).
    5. Commit: `test(quick-003): register upload.py in PLAY-04 scan + cmd-tier coverage pin`.
  </verify>
  <done>
    upload.py is under the PLAY-04 gate (5-module scan set stays fully green); the cmd-tier roster is EXACTLY partitioned into SCANNED_MODULES u NON_UI_CMD_CORE (with `__init__` the sole documented exempt); the derived-set assert means a NEW cmd-tier module can never again silently escape both registries; the gate is mutation-proven to FAIL naming wizard when unregistered, with the trip recorded in 003-SUMMARY.md and never committed.
  </done>
</task>

</tasks>

<verification>
All three tasks run sequentially (A -> B -> C) with zero file overlap; each commits atomically on the main line. The complete proof packet:
1. After EACH task: `python3.6 -m py_compile aamatch/*.py` + full `python3.6 -m unittest discover -s tests -v` green with the real count reported per task (933 baseline; Task 1 adds ~3-4 AST tests; Task 2 adds none; Task 3 adds ~3).
2. Targeted real smokes on their respective cumulative trees: SMOKE-08 (180 s) + SMOKE-12 (120 s) after Task 1 -- the alias-contract proofs; SMOKE-20 two-run per its documented recipe (240 s, read the header first) after Task 2 -- the streamed-extract proof via run 2's fresh-process load_checkpoint. Task 3's failure-proof is the mutation proof itself (test-only task).
3. Byte-freeze: `git status` between tasks shows only each task's declared files; smokes 01-22, run_smoke.sh, and every untouched test file show ZERO diff.
4. docs: `.planning/quick/003-api-hardening-bundle/003-SUMMARY.md` records per-task commits + real test totals + smoke verdicts + the SMOKE-20 run-mode observation + the mutation-proof trip verbatim + any deviations.
</verification>

<success_criteria>
- 3 atomic commits in Task 1/2/3 order, conventional style with quick-003 scope, ONLY the 8 declared files touched in total.
- `grep -rn "engine\._current_game\|engine\._remap_ligand_bonds" aamatch/` -> empty; engine.py's only private-name mentions are the alias block; ALL production + engine-internal callers on public names.
- checkpoint.py: `zf.read(PSE_MEMBER` gone, `zf.extract(PSE_MEMBER, path=tmp_dir)` inside the open-zip block after ALL sidecar gates, refusal-family FormatError messages byte-identical, `shutil` imported, untouched tests/test_checkpoint.py green.
- TestCmdTierRegistration pins the 8-module cmd-tier partition and fires on ANY unregistered addition; mutation-proven; upload.py scanned by both PLAY-04 scans green.
- Full WSL suite green at the reported real count (expect ~936-940); SMOKE-08, SMOKE-12, and SMOKE-20 (two runs) all PASS with smokes byte-untouched.
</success_criteria>

<output>
After completion, create `.planning/quick/003-api-hardening-bundle/003-SUMMARY.md` per the summary template: per-task commits, real test counts per task, smoke log verdicts (SMOKE-08 / SMOKE-12 / SMOKE-20 both runs + any contingency re-runs), the mutation-proof trip recorded verbatim, zero-deviation statement or honest deviations, and a must-haves self-check.
</output>
