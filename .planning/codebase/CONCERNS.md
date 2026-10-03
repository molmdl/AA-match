# Codebase Concerns

**Analysis Date:** 2026-10-03

Repo guardrails verified against code before writing. Items marked *(inference)* are my reading of the code, not an established claim — the rest cite inspected files and line areas. VMD/port material, `Pymol-script-repo/`, `tmp/`, `pymol-src/`, `3rd_party_lib/` were excluded per scope.

## Tech Debt

**Engine module-level runtime singletons:**
- Issue: The live game is four module-level globals — `_payload`, `_registry`, `_game`, `_ligand_content` — mutated via `global` statements. This is a deliberate design (STATE SPLIT rule, docstring lines 11-20), but it silently couples ALL gameplay to exactly one module object and one game per PyMOL session.
- Files: `aamatch/engine.py:138-141` (globals), `aamatch/engine.py:332-336` (`new_game` rebinding), `aamatch/engine.py:380-389` (`adopt_game`)
- Impact: Two module objects (repo `aamatch` + installed `pmg_tk.startup.aamatch`) in one PyMOL session create duplicate singleton games with no visible error; see "Fragile Areas / Module identity".
- Fix approach: Documented as a house law (AGENTS.md gate 5), not scheduled for refactor. Any future class-based GameEngine should keep `adopt_game`/`new_game` signatures so the wizard (`aamatch/wizard.py:842-880`) and checkpoint (`aamatch/gamestart.py:760-763`) call sites still work.

**Smoke verdict mechanics come from grep, not exit codes:**
- Issue: `smoke/run_smoke.sh:4-17` runs Windows PyMOL via `cmd.exe /c` and greps `=== SMOKE-$NN PASS ===` from a teed log. Exit codes cannot survive `cmd.exe`, so a PyMOL hard-crash before the marker prints is indistinguishable from a FAIL loop except by absence. All smokes tee into ONE shared file `/tmp/smoke_out.txt` (line 16) and the console shows only `tail -60` of it.
- Files: `smoke/run_smoke.sh:14-17` (cd, timeout, tee, tail, grep)
- Impact: Concurrent smoke runs collide on `/tmp/smoke_out.txt` and can cross-report each other; a truncation-aware failure hides shape details in the last-60 tail; a hang requires the optional TIMEOUT arg (default 120 s) — several smokes need 180–240 s per `.planning/STATE.md` battery notes.
- Fix approach: Give each smoke invocation its own output file (e.g. `/tmp/smoke_out.$$.txt`) and fail loudly on timeout with the tail preserved; add a PID-namespace or mktemp per run.

**Purity-gate registration is pinned for only 3 of 19 pure modules:**
- Issue *(verified by code reading)*: `tests/test_purity.py` Gates A/B/D iterate `PURE_MODULES` (lines 99-103). Registration-pin tests exist ONLY for `generator`, `game_state`, `checkpoint` — `tests/test_purity.py:294-327` (TestGeneratorRegistration / TestGameStateRegistration / TestCheckpointRegistration). The remaining 16 pure modules (`setup_state`, `level_spec`, `persistence`, `backup`, `paths`, `vec3`, `spatial`, `manifest`, `capability`, `thresholds`, `detector`, `wizard_core`, `wizard_text`, `setup_form`, `game_file`, `status_text`) can be deleted from `PURE_MODULES` with zero test failures — the gates then silently skip them.
- Files: `tests/test_purity.py:99-103` (list), `tests/test_purity.py:294-327` (only pins), `tests/test_purity.py:211-226` (Gate A loop)
- Impact: Removing a module from `PURE_MODULES` is currently a silent gate weaken — the standing AGENTS.md gate ("must not be weakened") is not mechanically enforced at the list level for 16 modules.
- Fix approach: Add one registration-pin `assertIn` per remaining pure module (mirror the three existing TestCase classes); or add a source-scan test asserting that every stdlib-importing `aamatch/*.py` module is listed in `PURE_MODULES`.

**Heavyweight UI/test modules:**
- Issue: The four largest production modules are all UI/cmd-tier: `game_window.py` (1223 lines), `detector.py` (1188), `wizard.py` (1153), `setup_window.py` (1079), `gamestart.py` (843). Smoke scripts are bigger still: `smoke_16_tab.py` (1884 lines), `smoke_11_window.py` (1317), `smoke_15_lifecycle.py` (1296), `smoke_06_spike_movement.py` (1257).
- Files: `aamatch/game_window.py`, `aamatch/detector.py`, `aamatch/wizard.py`, `aamatch/setup_window.py`, `aamatch/gamestart.py`; `smoke/smoke_16_tab.py`, `smoke/smoke_11_window.py`, `smoke/smoke_15_lifecycle.py`, `smoke/smoke_06_spike_movement.py`
- Impact: Modifying the Confirm/lifecycle flow (the Phase 8.1 gate) requires reading the same `wizard.confirm_molecule` contract in the wizard (panel text), `game_window._on_confirm` (tab button + synchronous poll), and the two biggest smokes (F-part pins). The 06-05 law "engine.py + wizard_text.py BYTE-IDENTICAL" is recorded in STATE — any future byte-drift costs a full smoke re-green.
- Fix approach: Extract per-surface confirm adapters; pin the confirm contract in a pure-level test rather than two smoke surfaces.

**Privates seam coupling in cmd-tier consumers:**
- Issue: External modules reach into `engine` privates — `engine._current_game()` (timer read) and `engine._remap_ligand_bonds(...)` (upload bond remap). Both usages are documented inside their docstrings, but they are private-commitment sprawl.
- Files: `aamatch/game_window.py:407-418` (`_compute_elapsed` calls `engine._current_game()`), `aamatch/upload.py:153-154` (`engine._remap_ligand_bonds` named in docstring as "nothing in it is manifest-specific")
- Impact: Renaming or privatizing the engine internals breaks two import sites without a compile error — the boundary is textual (docstring) only.
- Fix approach: Promote both helpers to public engine API names (`engine.current_game()`, `engine.remap_ligand_bonds(...)`) and keep the private aliases as documented shims; add a WSL test pinning the public names.

**Doc-recorded gate-§3.3/§3.5 Met-halogen cell tension — resolved in code, doc reconciliation pending:**
- Issue: The approved DETECT-03 gate doc (`docs/DETECTION_THRESHOLDS.md`) has a §3.3 Met row that says "Y(S)" for halogen capability while §3.5's resolved set excludes Met. Code follows §3.5 (Met excluded) per the recorded 02-05 tension in `.planning/STATE.md` ("reconcile the doc row at the next versioned review — §4.7 bump event, never silent").
- Files: `aamatch/capability.py` (typing home — Met excluded from halogen set), `.planning/STATE.md` (recorded 02-05 decision), `docs/DETECTION_THRESHOLDS.md` (the doc that needs the §3.3 row fix)
- Impact: A future reader transcribing §3.3 instead of §3.5 silently re-types Met as a halogen donor → DETECTOR_VERSION-stamped specs disagree with regeneration. This is the §4.7 "never silent" hazard made concrete.
- Fix approach: Schedule a DETECTOR_VERSION bump event to edit the doc row; do NOT silently update the doc.

## Known Bugs

**None currently open and verified in code.**
The Phase 8.1 pass-gate defect (blind Confirm advanced the molecule) is FIXED by the Phase 8.1 rewrite — enforcement lives at `aamatch/wizard.py:842-880` (`_confirm_molecule_impl`, BETWEEN detect and record) with the failed branch at `aamatch/wizard.py:905-934` (`_confirm_failed`). The regression-battery verdict ("smokes 01–21 ALL PASS, 931/931 WSL") is recorded in `.planning/phases/08.1-confirm-pass-gate-restoration/08.1-07-SUMMARY.md`. Items below are recorded, mitigated quirks that must NOT regress:

**Manual player recolor of a selected AA is overwritten on slot-switch:**
- Symptoms: If the player manually recolors an AA mid-game, switching selection to it (or away from it) restores the wizard-snapshot color, overwriting their change.
- Files: `aamatch/wizard.py:379-399` (`_select_slot` — "Documented edge: if the player manually recolored an AA mid-game, our restore overwrites their change (acceptable; v1 precedent)")
- Trigger: `cmd.color` by hand during play, then a selection change.
- Workaround: None — accepted UX trade-off; do NOT surface as a bug in future phases.

**Broad `except Exception:` in color-restore sandbox fallback swallows arbitrary failures:**
- Symptoms: A genuinely broken `cmd.alter(obj, 'color=m[ID]', ...)` silently falls to a per-id loop; the original exception is discarded, so latent breakage in other parts of the expression (e.g. bad dict) is invisible.
- Files: `aamatch/wizard.py:307-313`
- Trigger: Any `cmd.alter` exception on a selected slot restore.
- Workaround: None — the fallback is load-bearing for builds that reject sandbox dict-subscripting; add a one-line log of the swallowed exception when debugging.

## Security Considerations

**Checkpoint `.aamz` import executes pickled Python inside the Windows PyMOL process:**
- Risk: `gamestart.load_checkpoint` extracts the `.pse` member and calls `cmd.load(pse_path)`. A `.pse` is a full PyMOL session whose restore executes pickled Python objects (including `__reduce__` payloads from a crafted archive). The `.aamz` sidecar gates (`checkpoint.read_checkpoint_zip`) validate JSON schema only — the `.pse` bytes are trusted wholesale AFTER the gates pass. A crafted `.aamz` shared with a user would run arbitrary code in PyMOL's Windows Python.
- Files: `aamatch/gamestart.py:736-747` (`read_checkpoint_zip` → `cmd.load(pse_path)`), `aamatch/checkpoint.py:336-380` (`read_checkpoint_zip` — sidecar gates precede extraction, but the extracted `.pse` is not content-checked), `aamatch/game_window.py:1109-1111` (the tab caller routes the user-chosen path through `paths.to_windows_path` and into `load_checkpoint`)
- Current mitigation: None in code. The `[HUMAN]` import dialog wording asks the user to pick their own file, but no trust prompt, hash pinning, or signature is enforced.
- Recommendations: (1) Document "checkpoints are trusted-author-only" in README/help (Phase 9 deliverable); (2) if AA-match checkpoints are ever shared (the spec's export/share use case), bind the `.pse` to the sidecar with a sha256 member verified before extraction (`checkpoint.write_checkpoint_zip` already produces the file deterministically — a sidecar `pse_sha256` field would be additive and refuse-newer-safe); (3) consider running the reconcile gate BEFORE `cmd.load` on the `.pse`'s object tree is impossible (PyMOL owns the loader) — accept the pickle hazard and gate it by documentation instead.

**Upload per-record size is unbounded; only the 50-record count is capped:**
- Risk *(inference)*: `game_file.read_upload_source` reads the whole user file into memory and `check_upload_supply` caps records at `UPLOAD_MAX_RECORDS = 50` but does not cap bytes per record. A 500 MB single-record SDF would load fully into RAM and then per-record `cmd.read_sdfstr` spawns a temp PyMOL object per record. Risk is low for an educational plugin (local files, small molecules), but the cap is not on bytes.
- Files: `aamatch/game_file.py:87` (`UPLOAD_MAX_RECORDS = 50`), `aamatch/game_file.py:359-384` (`read_upload_source` — full binary read), `aamatch/game_file.py:328-356` (`check_upload_supply` — count cap only), `aamatch/upload.py:120-168` (per-record temp object spawn)
- Current mitigation: The 50-record cap names the generation-cost rationale in the refusal message (upload.py:337-338 cites `engine.py:220-223`); multi-segment MOL2 is refused outright (`upload.py:114-118`).
- Recommendations: If user shares uploads across a classroom, add a byte ceiling (e.g. 1 MB/record) alongside the record-count cap in `check_upload_supply`; refuse naming the file and the cap.

**Backup path-traversal guard is CORRECT but underspecified for edge filenames:**
- Risk: `backup._check_key` rejects path separators and `.`/`..`, but allows any other simple filename including OS-illegal-on-Windows names (e.g. `CON`, `NUL`, `aux.h`) that would fail FileStore writes on the Windows side.
- Files: `aamatch/backup.py:111-120` (`_check_key`), `aamatch/backup.py:150-193` (FileStore — `open(path, 'rb')`/`os.replace(tmp, path)` on the joined path)
- Current mitigation: FileStore is only constructed with the injected `root_dir` — currently used only by tests (MemoryStore is the live adapter); `BACKUP_OBJECT_PREFIX = '_aam_backup'` (`backup.py:50`) marks the cmd-tier adapter as NOT-implemented-yet, so the live plugin never hits the FileStore path.
- Recommendations: When the cmd-tier adapter is implemented, extend `_check_key` with a Windows reserved-name guard; until then, treat the guard as correctly minimal.

**`persistence.peek_kind` skips the version gate by design — acceptable, but must stay documented:**
- Risk: A `.aamz` carrying a structurally-valid container from a NEWER format version peeks fine (`peek_kind` returns the kind without gating the version) so the Import-tab dispatch can route it; the kind's own consumer then enforces the version gate. If the routing logic ever trusts a peeked kind without calling the consumer's gate, a newer file would sneak through.
- Files: `aamatch/persistence.py:133-182` (`peek_kind` — docstring: "WITHOUT running any kind-specific validation (no version gate -- a wrong version must not refuse a PEEK; the kind's own consumer gates it)")
- Current mitigation: The routing in `aamatch/game_window.py:992-1004` calls `persistence.peek_kind` then dispatches through `game_file` or `checkpoint` loaders that each enforce their gates.
- Recommendations: Keep the peek-skip design; if a third kind joins the dispatch, re-check the consumer-gate coverage.

## Performance Bottlenecks

**Detector pipeline is asserted against a fixed-scene budget only:**
- Problem: The only mechanical perf gate is `smoke_05_perf.py` against the LARGEST bundled molecule and the tier-9 9×9 grid (81 AAs + 1 ligand = 82 objects; observed extract 16.7–21 ms / detect 0.0 ms per `.planning/STATE.md` 02-15 decision). Budgets: `DETECT_BUDGET_MS = 100`, `TOTAL_BUDGET_MS = 1000`. The WSL loose guard (2.0 s in `tests/test_detector_invariance.py`) is WSL-only and documented as not importing into the headless gate.
- Files: `smoke/smoke_05_perf.py:97-101` (budgets), `smoke/smoke_05_perf.py:121-onwards` (timed pass), `tests/test_detector_invariance.py` (WSL loose guard)
- Cause: `geometry.extract_game_atoms` does ONE `cmd.iterate_state` over an `' or '.join(names)` selection (`geometry.py:128-138`) — linear in atom count but builds an ~82-name selection string per call. `detector.detect` runs all 7 interaction types per pass with feature precomputation (`detector.py` module docstring, "features precompute ONCE").
- Improvement path: None needed at the current cap (tier 9); if tier 10 or a multi-molecule full-scene detect is ever added (the engine's `detect()` docstring `aamatch/engine.py:22-31` already notes the cross-molecule scoring landmine), add a per-molecule selection-string cache and pre-computed feature map keyed by object-name generation.

**1 Hz status poll latency vs synchronous refresh:**
- Problem: The Game tab polls the wizard at 1 Hz via `_on_tick` (`aamatch/game_window.py:427-457`) piggybacked on the elapsed-timer tick. Wizard-panel interactions (panel Confirm/Skip) don't run through `_on_confirm`/`_on_skip`, so their feedback can lag up to one second on the tab unless the op-driven synchronous `_refresh_status` is also called. The 06-07 design compensates by calling `_refresh_status` synchronously from `_confirm_now`/`_skip_now` etc. (`game_window.py:617-640`, `702-720`).
- Files: `aamatch/game_window.py:427-457` (tick + modal-pause branch), `aamatch/game_window.py:617-640` (`_confirm_now` synchronous poll), `aamatch/game_window.py:702-720` (`_skip_now` synchronous poll)
- Cause: Separation between the wizard's cmd-refresh loop (rebuild via `cmd.refresh_wizard`) and the Qt tab's own 1 Hz label refresh.
- Improvement path: Current design is correct; any NEW tab-side op must remember to call `self._refresh_status()` synchronously right after the wizard op or accept ≤1 s latency. Pin this rule in a future docstring/test when adding ops.

**Checkpoint restore reads the `.pse` twice (once into memory, once to temp file):**
- Problem: `checkpoint.read_checkpoint_zip` does `pse_bytes = zf.read(PSE_MEMBER)` (full buffered read), then writes the bytes to a `tempfile.mkdtemp` dir for `cmd.load`. On large user objects inside the session (full-session save by design per `gamestart.py:806-842`), that's a 2× memory spike.
- Files: `aamatch/checkpoint.py:371-379` (read + tmp write), `aamatch/checkpoint.py:304-333` (`write_checkpoint_zip` writes the full temp `.pse` via `zipfile`)
- Cause: `zipfile` requires a seekable file to extract member-by-member, and `cmd.load` takes a real path — in-memory restoration isn't available.
- Improvement path: Use `zf.extract(PSE_MEMBER, path=tmp_dir)` for streaming I/O (one inode copy instead of two memory copies); keep the same refusal-first order.

## Fragile Areas

**WSL/Windows path guard (`paths.to_windows_path`) with load-bearing guard term and a pinned case-9 asymmetry:**
- Files: `aamatch/paths.py:20-51` (`to_windows_path`), callers via grep: `engine.py:125,240`, `placement.py:77,240,342`, `gamestart.py:734-736,832`, `setup_window.py:100,112,760,796,852`, `game_window.py:991-992,1020,1049-1051,1109-1111`
- Why fragile: The `len(parts) == 4` term on `paths.py:46` is documented as LOAD-BEARING (without it `/mnt/c` raises IndexError); the case-9 asymmetry (bare `/mnt/c` returned unchanged, `/mnt/c/` → `C:\`) is pinned by `tests/test_paths.py` and is NOT intuitive. Every `cmd.load`/`cmd.save`/`cmd.read_*str`/file-API call site must route through this guard — a future direct `cmd.load(path)` site from WSL work breaks only on Windows.
- Safe modification: NEVER touch the guard's boolean shape without re-running the test matrix; new file-API sites must grep-verify `to_windows_path` is in the call chain. The `package_data_path` (`paths.py:54-63`) anchors data to `__file__`, never `os.getcwd()`.
- Test coverage: `tests/test_paths.py` (135 lines) pins the 9-case matrix; smoke field-verification via `smoke_01_bootstrap.py` (loads every manifest id through the converted path).

**Module identity (`aamatch` vs `pmg_tk.startup.aamatch`):**
- Files: `aamatch/wizard.py:103-133` (`_rebuild_game_wizard` + `is_game_wizard_any_identity`), `aamatch/engine.py:138-141` (module-level singletons), `aamatch/__init__.py:16-39` (`__init_plugin__` + lazy `run_plugin_gui`), `aamatch/setup_window.py:40-42` (the lazy-import pattern documented), `aamatch/upload.py:100-103` (inside-method sibling imports)
- Why fragile: pickle resolves `GameWizard` by module path — a session saved under one identity and loaded under the other fails `_rebuild_game_wizard` lookup with a ModuleNotFoundError. The engine's module-level `_registry`/`_game` state is per-module-object, so installed+repo copies in ONE PyMOL session hold separate live games silently. `is_game_wizard_any_identity` (`wizard.py:122-133`) is the codified workaround for `isinstance` failing across module objects; it is a name+module-suffix predicate, NOT a class check.
- Safe modification: Never call `cmd.set_wizard(GameWizard(...))` from a module-level class check; always go through `is_game_wizard_any_identity`. When the plugin-path install method is used (the recorded 01-09 PLUGIN-PATH method in `.planning/STATE.md`), repo edits are live and reinstall is NOT needed; when the dialog copy-install method is used, an installed copy does NOT see repo edits until reinstalled — this is the recorded "stale-copy hazard in human checkpoints".
- Test coverage: Gate A2 (`tests/test_purity.py:229-245`) pins the zero-module-level-import discipline on `__init__.py` that makes dual-identity imports possible; `tests/test_package_skeleton.py` pins the `run_plugin_gui` seam as an AST source contract.

**Two distinct version gates — refuse-newer for containers, EXACT-match for detector semantics:**
- Files: `aamatch/persistence.py:37` (`FORMAT_VERSION = 1`, refuse-newer at 82-85), `aamatch/level_spec.py:60-61` (`DETECTOR_VERSION = "det-1"`, `LEVEL_SPEC_VERSION = 1`), `aamatch/level_spec.py:111-121` (payload `format_version` gate then `detector_version` exact-match reference: "stale or newer game spec"), `aamatch/checkpoint.py:89` (`CHECKPOINT_VERSION = 1`, refuse-newer at 152-155), `aamatch/game_file.py:81` (`GAME_VERSION = 1`, refuse-newer at 140-143), `aamatch/manifest.py:63` (`MANIFEST_VERSION = 1`, refuse-newer at 151-155)
- Why fragile: SIX version constants exist; ONLY `DETECTOR_VERSION` is exact-match (both stale AND newer stamp refused, because changed detection semantics make old specs unsolvable, not merely incomplete — the refusal message at `level_spec.py:119-121` says "stale or newer game spec -- regenerate"). Conflating any two (e.g. making detector gate refuse-newer, or making FORMAT_VERSION exact-match) corrupts shared specs across AA-match versions.
- Safe modification: A DETECTOR_VERSION bump is the §4.7 event documented in `docs/DETECTION_THRESHOLDS.md` and `.planning/STATE.md` (e.g. the 02-07 veto-threshold note, "never silent"); it requires regenerating demos/tests that embed the stamped spec. Never bump FORMAT_VERSION to refuse-older.
- Test coverage: `tests/test_level_spec.py` (310 lines) pins the exact-match gate's refusal verbatim; `smoke_05_perf.py` does a positive-control roundtrip plus a 'det-0' re-stamp refusal case.

**Purity gates and the zero-sys.modules-stubs law:**
- Files: `tests/test_purity.py` (whole file — Gates A/A2/B/D, negative control at 329-352), plus all 19 pure modules listed at `PURE_MODULES` (lines 99-103)
- Why fragile: New pure modules must be added to `PURE_MODULES` to be gated; only 3 of 19 modules have registration-pin tests (see "Tech Debt"). sys.modules stubs are forbidden — the Phase-1 GATE is subprocess-level (`Gate B`, `test_purity.py:248-267`); stubbing to make Gate B pass would defeat the AST + subprocess cross-proof.
- Safe modification: Add the module to `PURE_MODULES` in the SAME commit as the module, plus a registration-pin test naming it (mirror `TestCheckpointRegistration`); keep the checker function `find_bad_imports` PURE (it consumes source text).
- Test coverage: Gates run inside the WSL unit suite (`python3.6 -m unittest discover -s tests -v`); the AGENTS.md command sequence enforces py_compile + unittest + smoke ordering.

**GUI/picking flows are untestable from WSL — `[HUMAN]` checkpoints are the only verification:**
- Files: `aamatch/wizard.py` (whole file — picking + do_select + do_pick handlers), `aamatch/game_window.py` (Qt tab interactions), `aamatch/setup_window.py` (Qt setup+upload dialogs), the four smokes `smoke/smoke_09_qt_probe.py`, `smoke/smoke_11_window.py`, `smoke/smoke_13_qt_timer_probe.py`, `smoke/smoke_16_tab.py`
- Why fragile: PyMOL needs a real display for Qt; WSL cannot exercise mouse picks or modal dialogs. The scripted-pick recipe (`cmd.select('sele', '<slot object> and name CA')` + `do_select('sele')`, recorded in `.planning/STATE.md` as the SMOKE-07 headless proof) reproduces pick ROUTING but not real mouse events. The pending `[HUMAN]` combined checkpoint (`.planning/phases/08.1-confirm-pass-gate-restoration/08.1-08-PLAN.md`) closes the Phase-8.1 GUI sign-off; until then the pass-gate semantics on real-display picking is headless-only.
- Safe modification: NEVER accept a "WSL green" as proof of a Qt-side change; require the human-checkpoint cycle. Keep SMOKE-07/11/16 scripted-pick recipes byte-stable — they are the headless proxy for the human matrix.
- Test coverage: None in WSL for picking; SMOKE-09/11/13/16 probe headless Qt timer/window lifecycle.

**Stale installed copies do not see repo edits (copy-install vs plugin-path method):**
- Files: `aamatch/__init__.py` (whole file — `__init_plugin__` + `run_plugin_gui`), `.planning/STATE.md` (01-09 [HUMAN] verdict records the PLUGIN-PATH method)
- Why fragile: PyMOL Plugin Manager copy-install copies `aamatch/` into the user's plugin directory; repo edits invisible until reinstall. AGENTS.md dev-loop law restricts headless smokes to the repo copy.
- Safe modification: Verify which install method a human checkpoint is on before testing a fix; prefer the PLUGIN-PATH method (repo root added to PyMOL plugin path) for development checkpoints.
- Test coverage: None automated; the 01-09 [HUMAN] verdict recorded in `.planning/STATE.md` is the canonical reference.

**Display-staleness law: `cmd.alter` does not rebuild display lists:**
- Files: `aamatch/wizard.py:285-314` (`_restore_slot_colors` — the docstring records the 03-06 field bug and mandates `cmd.rebuild(obj)` after the sandbox alter), `aamatch/wizard.py:903-904` (every branch falls through to the same restore)
- Why fragile: Post-restore the DATA is exact but the SCREEN can keep showing the highlight color until a later op refreshes. Two paths change atom colors (recolor-on-select and restore-on-deselect); BOTH must rebuild the object's display lists.
- Safe modification: Any NEW recolor path (e.g. hint, scoring feedback) must end with a scoped `cmd.rebuild(obj)`; never a global `cmd.rebuild()` (expensive redraw).
- Test coverage: The 03-06 field bug is recorded in `.planning/debug/phase3-gui-checkpoint-failures.md`; headless smoke data equality is proven but on-screen redraw is a human-checkpoint item.

**PyMOL-build capability: `cmd.read_mol2str` exists but is NOT re-exported on this 2.5.0 build:**
- Files: `aamatch/upload.py:47-63` (build-capability docstring), `aamatch/upload.py:114-118` (multi-segment MOL2 refused FormatError), `aamatch/upload.py:135-141` (single-molecule MOL2 per-record reader guard)
- Why fragile: importing.py DEFINES read_mol2str at line 1038, but api.py omits the re-export on the pinned Windows build (PyMOL 2.5.0 + Python 3.9.13 per `.planning/phases/01-bootstrap-pure-foundation/windows-env-versions.md`). The plugin refuses MOL2 uploads with a clear message; a future PyMOL upgrade silently ENABLES them — the `hasattr` guard means the fail-closed branch stops firing.
- Safe modification: Treat the missing-reader message as part of the capability surface; if the build changes, SMOKE-12 PART 4 (which pins the multi-segment refusal) needs a re-verification, not just a re-run.
- Test coverage: `smoke/smoke_12_upload_e2e.py` pins both refusals against the current build.

## Scaling Limits

**Grid size and molecule count caps:**
- Current capacity: Setup-window bounds (frozen by 01-09 human-verdict): `molecules_per_level` 2 (default 2/1..10), `difficulty_levels` 3 (1..10), grid tier ceilings at D=10 L9: `grid_n = 9` → 81 capped AAs per level + 1 ligand = 82 objects per molecule. Curated demo ligands top out at heme (75 atoms).
- Limit: `geometry.extract_game_atoms`'s `' or '.join(names)` selection string is linear in object count — at the 82-object cap it's fine; scaling to hundreds (multi-molecule full molecules or mega-grids) risks PyMOL selection-string limits and per-pass re-precompute in `detector`.
- Scaling path: Per-molecule scoped detection (already in `engine.detect_molecule`) is the polyfill; a multi-level detect never composes the full scene at once — future caps should enforce ≤ one molecule per detect pass and a selection-string cache keyed on object-set generation.

**Upload supply:**
- Current capacity: 50 records per upload (`game_file.py:87`), no byte cap; generation temp-loads EVERY candidate per Generate (`engine.new_game`, ~222→272).
- Limit: Per-record PyMOL temp object spawn inside `upload.prepare_uploaded_set` (`upload.py:120-168`) — at 50 records × pre-generate + post-generate this is already the slow path.
- Scaling path: Cache extraction results keyed on record sha256 (the row already stores one per `game_file.build_uploaded_row`); skip temp-load when hash matches.

**`.pse` full-session save:**
- Current capacity: Checkpoints save the FULL session per the recorded decision (`gamestart.py:806-842`), so a session with the user's own 200 kDa protein is included in every checkpoint.
- Limit: User-object bleed into game archives — by DESIGN (full-session replace on resume is intentional per the save decision), but file size scales with the user's entire session, not with the game.
- Scaling path: None planned; if file size becomes a UX issue, a game-scoped session save would need sidecar-based scene reconstruction (the never-ghost gate at `checkpoint.reconcile_registry` provides the registry half).

## Dependencies at Risk

**PyMOL 2.5.0 pinned Windows build:**
- Risk: The recorded environment (Python 3.9.13, PyQt5 5.12.3, Qt 5.12.9, PyMOL 2.5.0, numpy 1.25.2 — `.planning/phases/01-bootstrap-pure-foundation/windows-env-versions.md`) is load-bearing for: pickle-shaped GameWizard restore (`wizard.py:103-119`), `read_mol2str` re-export absence (`upload.py:47-63`), expression-sandbox dict-subscript support (`wizard.py:307-313` — fallback branch in place), and the `cmd.unpick()-deletes-pk1` empiric.
- Impact: A PyMOL/Qt upgrade can silently change any of these empirics; the empirical branches exist precisely because the behavior was probed on THIS build.
- Migration plan: Re-run the SMOKE-09/12/13 probe trio on any environment change before accepting it; treat each as a build-capability contract (documented in each smoke header).

**WSL-side Python 3.6.9 (syntax layer only):**
- Risk: Gate D pins the 3.6 syntax floor (`tests/test_purity.py:270-291`); production runtime is 3.9. Any 3.7+-only construct (dataclasses, walrus, positional-only) breaks Gate D immediately — which is the POINT of the gate but also the maintenance burden.
- Impact: Contributors on modern Python forget 3.6-only syntax; written-3.6-safe discipline is not auto-checked on editors.
- Migration plan: If the floor ever moves to 3.9-only (matching runtime), Gate D becomes a no-op guard and can be retired — a deliberate gate decision, not automatic.

**Zero third-party Python libs:**
- Risk: None from version churn. numpy/PyQt5/numpy come only via `pymol.Qt` and bundled PyMOL — outside AA-match's control.
- Impact: By design, the zero-extra-deps policy is a hard gate (purity `FORBIDDEN` set at `tests/test_purity.py:107-108`).
- Migration plan: Adding any dep is a spec-level decision (AGENTS.md "Any additional Python lib must be user-approved").

## Missing Critical Features

**In-game help + user docs (Phase 9 scope):**
- Problem: `spec.md` UI standard calls for "clear but sufficient in-game explanation"; ROADMAP Phase 9 (`.planning/ROADMAP.md` line 28) is unchecked. README.md exists but no in-game help surface yet.
- Blocks: [HUMAN] GUI sign-off for help text polish; Phase 9 plan.

**Interaction-set v2 extensions (deferred):**
- Problem: `.planning/REQUIREMENTS.md:82-95` defers EXT-01 (water-bridge — needs explicit waters), EXT-02 (face-to-face vs edge-to-face π-stacking split as teachable types), EXT-03 (protein/DNA-ligand modes), EXT-04 (upload validation helper — `game_file.check_upload_supply` docstring at line 331 already references it).
- Blocks: Each is a DETECTOR_VERSION event (§4.7) when added; the aio write-up of each is a Phase-9+ planning item.

**Ligand phosphate/sulfonate typing absent:**
- Problem: `detector.py` module docstring records "Ligand-side phosphate/sulfonate groups (gate §2.3 rows) are NOT typed in v1 — capability does not type them either; adding them is a versioned capability change."
- Blocks: Salt-bridge/cation-π detection on phosphorylated ligands (e.g. ATP's phosphate tail is currently caught by ammonium/carboxylate groups but phosphate-sulfonate groups aren't typed as charge centers).
- Fix approach: EXT item; extend `capability._charge_signs` and type tables, then a DETECTOR_VERSION bump, never silent.

**His is neutral-only in v1:**
- Problem: Per the 02-01 decision recorded in `.planning/STATE.md`, His = neutral in v1; protonation variants are "additive-later". `capability.py` holds no `HSP`/`HSD` tokens.
- Blocks: Charged-His cation-π / salt-bridge pedagogical content.
- Fix approach: Protonation variants = `AA_TOKENS` additive extension; already pre-authorized as additive (no version bump required for tokens themselves).

**VMD/Tcl port (v2) not in this repo:**
- Problem: The v2 VMD/Tcl port is explicitly out of scope (`.planning/ROADMAP.md` v1 line); any v2 work starts from scratch in a new tree and must re-derive the equivalents of `paths.to_windows_path` (the VMD variant needs `C:/` forward-slash per AGENTS.md) and the module-identity discipline.
- Blocks: Nothing in v1; v2 planning.

## Test Coverage Gaps

**Real-display picking and Qt modal interaction:**
- What's not tested: Real mouse clicks into the wizard (`do_pick`/`do_select` chain), native file-dialog round-trips through QFileDialog, true 3-Button Viewing mode switching, and any visual outcome of `cmd.rebuild` — the scripted-pick recipe used headlessly (`smoke_07_wizard_loop.py`) is a proxy.
- Files: `aamatch/wizard.py:316-341` (`do_select`), `aamatch/wizard.py:343-377` (`do_pick`), `aamatch/game_window.py` (whole tab), `aamatch/setup_window.py` (whole window)
- Risk: A Qt/display regression after a PyMOL/Qt upgrade is invisible until the next [HUMAN] checkpoint; the pending Phase-8.1-08 combined checkpoint is the next opportunity.
- Priority: HIGH — gated on a human session; the 08.1-08 plan (`.planning/phases/08.1-confirm-pass-gate-restoration/08.1-08-PLAN.md`) is already written but not executed.

**Gate weakening by PURE_MODULES list omission (16/19 modules):**
- What's not tested: As detailed under "Tech Debt", removing a non-pinned pure module from `PURE_MODULES` silently skips Gates A and B for that module.
- Files: `tests/test_purity.py:99-103` (list), `tests/test_purity.py:294-327` (only 3 registration pins)
- Risk: A future refactor accidentally drops `persistence` or `detector` from the list and the purity contract silently stops applying to a module that still loads in production.
- Priority: HIGH — one-line test per module, mechanical to add.

**Smoke verdict robustness (shared /tmp log + no timeout escalation):**
- What's not tested: Collision behavior when two smokes run concurrently; what the developer sees when the smoke output's final 60 lines don't include the PASS marker (the full log is in `/tmp/smoke_out.txt` but the awk/tail prefix isn't). No mechanical escalation from "exit 1 + tail" to "grep the full file for the marker vs show the last failure".
- Files: `smoke/run_smoke.sh` (whole file)
- Risk: Developer misreads a timeout/hang as a FAIL; concurrent smoke runs in parallel GSD waves can cross-report.
- Priority: MEDIUM — fix by per-invocation log file + timeout message.

**Detection count-level correctness under real molecules at scale:**
- What's not tested: The full demo catalog (10 sets, 18 entries per 08-07) is exercised via `smoke_02_manifest.py` (load-by-id), `smoke_03_generate.py` (candidate-panel diversity), and `smoke_04_e2e.py` (E2E), but a per-entry detector-record count assertion against a human-curated ORACLE exists only for the benzamide scripted scene in SMOKE-03/05. The 08-11 Task 2 detector-coverage probe (`.planning/STATE.md`) verified halogen/metal presence on chloramphenicol/thyroxine/heme as a one-off; that probe is NOT part of the standing test battery.
- Files: `aamatch/data/MANIFEST.json` + `aamatch/data/ligands/` (the curated catalog), `tmp/detector_coverage_phase8.py` (the one-off probe per STATE — git-ignored `tmp/`)
- Risk: A threshold or typing change appears green against UNIT tests (constructed scenes) but silently breaks the curated molecules' expected records; only the DETECTOR_VERSION stamp forces regeneration, not content verification.
- Priority: MEDIUM — fold the phase-8 coverage probe into a standing smoke (e.g. SMOKE-02 or a new SMOKE-22) before any threshold revisit.

**`test_code_audit.py` covers only the AST/token-level conventions:**
- What's not tested (*inference*): The mechanical source audit (`tests/test_code_audit.py`, 377 lines) pins `cross_pairs`/`brute_force_pairs` routing, naive-pair-loop bans, and banned-`cmd`-call counts (`get_model`, `matrix_reset`, `get_object_ttt`). It does NOT cover the equivalent prohibitions inside NEW cmd-tier modules unless `SCANNED_MODULES` is extended (per `tests/test_wizard_source.py`'s pattern).
- Files: `tests/test_code_audit.py`, `tests/test_wizard_source.py`
- Risk: New cmd-tier module added → audit silently skips it until someone extends the scanned set.
- Priority: LOW — convention documented; future modules should register.

---

*Concerns audit: 2026-10-03*
