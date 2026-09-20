# Phase 7: Checkpoint & Game-File Persistence — Research (Save/Import flows, dialogs, timer, status lines)

**Researched:** 2026-09-21
**Domain:** Game-tab Save button (SCORE-08) + Import button (PERSIST-02) flows, file-dialog integration, timer-vs-modal interplay, status_text extensions, headless/HUMAN test split
**Confidence:** HIGH for every repo-mechanics claim (read from source this session with file:line); MEDIUM only where explicitly marked ([UNVERIFIED] items carry cheap probes).

**Citation shorthand:**
- Repo files cited as plain paths (`aamatch/game_window.py:383`).
- `PA-*` = `tmp/bioCHEMeleon/biochemeleon/*` (shipped v1 prior art, read this session) — [PA-OBS] evidence.
- `pymol-src/<f>` = `pymol-src/modules/pymol/<f>` (the repo's own PyMOL 2.5.0 source tree).
- `04-RESEARCH-export-upload` = `.planning/phases/04-qt-setup-window/04-RESEARCH-export-upload.md`; `05-RESEARCH-window-start-timer` = `.planning/phases/05-game-status-tab-start-sequence/05-RESEARCH-window-start-timer.md`; `05-RESEARCH-status-surface` = `.planning/phases/05-game-status-tab-start-sequence/05-RESEARCH-status-surface.md`; `06-RESEARCH-restart-reset` = `.planning/phases/06-scoring-lifecycle-endgame/06-RESEARCH-restart-reset.md`.

---

## Summary

Both button flows are thin compositions over already-proven seams. **Import** re-runs the 04-12-proven five-gate parse chain (`game_file.parse_game_data`) and then needs exactly ONE new cmd-tier seam that materializes the **embedded payload directly** — `start_game` itself is the WRONG seam because it *regenerates* from `setup+seed+candidates` (`aamatch/gamestart.py:424-427`), and the embed-don't-regenerate verdict forbids that (`04-RESEARCH-export-upload` regenerate_vs_embed; `aamatch/engine.py:13-15` "Nothing re-derives from the seed at replay"). **Save** wraps the v1-proven pause-capture-dialog-save shape (`PA-__init__:745-788`) adapted to AA-match's tick-level modal freeze: **no manual timer bracket is needed for clock correctness** — the 1 Hz tick's `activeModalWidget()` rebase already freezes the clock under a file dialog, **human-verified 2026-09-20** (`05-11-SUMMARY.md:66`); the roadmap note "capture timer before modal file dialogs" concretely requires only that the sidecar's **elapsed value is captured before the dialog opens** (v1 doctrine, `PA-persistence.py:62-68`).

**The single biggest new finding is a load-side landmine:** `cmd.save(.pse)` pickles the whole wizard stack (`pymol-src/wizarding.py:176-179`), but the base `Wizard.__reduce__` reconstructs via `self.__class__()` with **no args** (`pymol-src/wizard/__init__.py:34-36`) — and `GameWizard.__init__` requires `payload, registry` (`aamatch/wizard.py:140`), so **unpickling a saved session raises TypeError and `session_restore_wizard` swallows it with "Session-Warning: unable to restore wizard."** (`pymol-src/wizarding.py:189-192`; verified by a live python3.6 pickle simulation this session). Phase 7 must override `GameWizard.__reduce__` or the `.pse` round-trip loses the wizard AND prints console noise, violating ROADMAP criterion 3 ("console clean during save/load").

**Primary recommendation:** Plan 1 = pure checkpoint container + `GameWizard.__reduce__` fix + the matrix/`.pse` round-trip smoke (the standing STATE.md:290 gate) BEFORE any button work; Plan 2 = Save button (wrapper/impl law, v1 capture doctrine); Plan 3 = Import button + the payload-direct `gamestart` seam; Plan 4 = [HUMAN] checkpoint. Import rides the exact deferred-start orchestration (cancel-first P-2 → pop-first P-3 → prepare → countdown → line-after-arm D7).

---

## SAVE flow map (per house law, step-by-step)

Spec: "save button to save the state of the game as a pymol session and some state info specific for this game so the user can load/checkpoint any time" (`spec.md:46`). Requirement SCORE-08; ROADMAP criterion 1 is "zipped `.pse` + JSON-sidecar container" — the zip shape is pinned by the roadmap (v1's `.bcmz` → the recorded `.aamz` analog, `.planning/research/SUMMARY.md:28,67`).

### S1. Button + wiring (Qt tier, `aamatch/game_window.py`)

- Attribute **`btn_save_game`**, label **'Save'**. The D7 naming law (`06-RESEARCH-restart-reset` §7 + `game_window.py:219-221`): distinct attribute names avoid smoke-assert ambiguity; `btn_save_game` is suffixed exactly where a collision exists (`btn_save_setup` on the Setup tab, `setup_window.py:212`).
- Inserted via `btn_row.insertWidget(btn_row.count() - 1, self.btn_save_game)` — the stretch stays LAST (`game_window.py:170,176,181,206,216,226`); the class docstring explicitly reserves the "Save/Import, Phase 7" slots (`game_window.py:130-133`). It lands after `btn_reset_grid` → row order: Hint, Confirm, Skip/Give Up, Restart, Reset, Save, Import. (The spec.md:39-47 bullet order lists import first and save before restart/reset, but that list is an inventory, not a layout order — the landed Phase-6 row already deviates; append-before-stretch is the only law. Cosmetic; planner may note it.)
- Tooltip in the spec-meaning style (cf. `setup_window.py:213-214` 'Save the game setup parameters to a file.'): e.g. 'Save the running game (PyMOL session + game state) to a checkpoint file.' — plan pins verbatim.
- Connected in `__init__` by its own handler plan (the 04-05 shell law, `game_window.py:22-24,228-233`).

### S2. Wrapper `_on_save_game` — thin, gate-first, owns the ONLY modals

House law chain (06-07/06-09 shape, `game_window.py:505-522,551-583`):

1. **GATE FIRST, silent no-op BEFORE any box** (06-07 law, `game_window.py:558-572`): `if not isinstance(cmd.get_wizard(), wizard_mod.GameWizard): return`. This covers pre-GO (wizard-free countdown, P-1, `game_window.py:77-82`), no-game-at-all, and the post-endgame popped state (`_endgame_sequence` pops, `game_window.py:786`). v1 gated the same way: `if (controller is None or not _started or _start_time is None): return` (`PA-__init__:752-755`).
   - **Residue to decide:** a game ended via the wizard PANEL's own Confirm (not the tab) leaves the wizard live-but-inert on the stack with the timer running (06-06 "inert-but-present"; the tab impls' `_endgame_sequence` never ran). Save would then checkpoint a `game_over` state. Options: allow (the state round-trips — `GameState.from_dict` carries `game_over`/`end_state`/`final_time`, `aamatch/game_state.py:452-454`) vs refuse with the pinned `'The game is over.'` (the `_require_playing` wording, `aamatch/wizard.py:569`). Planner decision; allowing is simpler and lossless.
2. **Capture the elapsed BEFORE the dialog** (the roadmap note's concrete requirement — see the timer section): `elapsed = <live read>` from the anchor (e.g. `game_tab._compute_elapsed()`, `game_window.py:344-355`, or `engine._current_game()` + `time.time() - gs.timer_anchor`). v1: `elapsed = _time.time() - controller._start_time` immediately before `getSaveFileName` (`PA-__init__:757-763`); the doctrine is documented at `PA-persistence.py:62-68` ("Caller should pass it explicitly to avoid the modal-dialog timer pitfall … capture BEFORE the file dialog"). The elapsed is passed INTO the impl as a parameter (keeps the impl a pure function of its args; no second wall-clock read racing the dialog).
3. **File dialog:** `QtWidgets.QFileDialog.getSaveFileName(self, 'Save AA-match Game', <default>, 'AA-match Checkpoint (*.aamz);;All Files (*)')` — the exact house pattern (`setup_window.py:693-695` Save Setup; `setup_window.py:896-898` Export with a default filename `'game.aamatch.json'`). Cancel (`if not path`) = safe no-op (v1 resumed identically on cancel, `PA-__init__:764-768`; here nothing to undo — the tick-level freeze already handled the clock).
4. **Extension auto-append law** (04-09 Decision 2, `setup_window.py:715-716`): `if not path.endswith('.aamz'): path += '.aamz'`. (`04-RESEARCH-export-upload` OQ-5 precedent: default filename/extension = human preference at plan time.)
5. **Impl via `_guard`** (`game_window.py:462-473` — the verbatim 04-09 contract: catches `(ValueError, OSError)`, shows `str(e)` verbatim in a modal warning child, returns None on refusal, propagates unexpected exceptions).
6. **Feedback:** log the pinned `game_saved` line via `self._log(...)` — **no success box** (v1's game-tab Save did exactly `_log("Saved checkpoint to %s" % path)` with no box, `PA-__init__:786-787`; the Game-tab feedback convention is "the info-box line IS the feedback", 05-08/`game_window.py:476-479`). The alternative (04-12 Export's `QMessageBox.information` with a summary, `setup_window.py:901-903`) is recorded for the planner; the v1 game-tab precedent + the "a Start that opened a modal would be noise" rationale (`setup_window.py:976-978`) favor the log line.

### S3. Impl `_save_game_to(path, elapsed)` — NON-MODAL, box-free, smoke-drivable

(the smoke-99 law: impls never own boxes — `game_window.py:71-73`, `setup_window.py:688-691`)

1. Read the live state through sanctioned surfaces only: `engine._current_game().to_dict()` (the 05-07 read path, `engine.py:690-697`) and the engine's payload/registry (see the seam note below — the tab never touches `engine._game/_payload` privates, the 05-07/05-10 grep law, `06-RESEARCH-restart-reset` Q6; the SAVE impl runs on GameTab, so the payload/registry reads must go through a cmd-tier seam or a public engine read op, not `engine._payload`).
2. Build the sidecar `data` dict (new pure module, e.g. `aamatch/checkpoint.py`, registered in `PURE_MODULES`; `zipfile` is ALREADY whitelisted in `ALLOWED_STDLIB`, `tests/test_purity.py:108-111`):
   - `checkpoint_format_version` (new refuse-newer constant, the `GAME_VERSION` pattern, `aamatch/game_file.py:81,135-143`), `created_at`, `generator` provenance (the `make_game_data` header shape, `game_file.py:109-117`).
   - `game_state`: `GameState.to_dict()` VERBATIM — the recorded 02-10 decision: "to_dict/from_dict lossless NOW (Phase 7 wraps it, never reshapes)" (`.planning/STATE.md:107`). The wall-clock `timer_anchor` inside it is meaningless across sessions; the restore always overrides it — store the authoritative `timer_elapsed` as a sibling key (captured in S2-2). On a game_over save, `final_time` is already frozen and `timer_elapsed` is informational.
   - `level_spec`: the payload VERBATIM (needed for the engine rebind and as the reconcile authority; `engine._payload` is module state, NOT in the `.pse`).
   - `registry`: the materialize registry's plain data (`placement.py:295-298` — `{'level_index', 'pre_game_names', 'molecules'}` with object names + sorted atom ids) for sentinel-first reconcile + engine rebind.
   - `ligand_files`: `game_file.encode_ligand_files(...)` of the live `ligand_content` — REQUIRED for a checkpoint of an uploaded game (engine `advance_level` re-materializes from `_ligand_content`, `engine.py:625`; module state dies with the process).
   - `last_start`: the `gamestart._last_start` tuple (`{'setup','seed','candidates','ligand_content'}`, `gamestart.py:455-456`) — module state also dies with the process; without it, Restart after a checkpoint restore would refuse 'Restart: no game has been started yet.' (`game_window.py:706-707`).
3. Write the `.pse`: `cmd.save(<temp>, 'segi AAM')` or `cmd.save(<temp>)` (scope = open question OQ-4). Temp via `tempfile.NamedTemporaryFile(suffix='.pse', delete=False)` in the Windows process (`PA-__init__:771-773`); no `to_windows_path` needed for a temp path minted inside the Windows process.
4. Zip: `zipfile.ZipFile(zip_path, 'w', ZIP_DEFLATED)` with arcnames `game.pse` + the sidecar JSON (v1 arcname convention `game.pse`/`game.bcm`, `PA-persistence.py:211-214`); zip path routes `paths.to_windows_path` (the AGENTS path law — QFileDialog Windows paths pass through unchanged, `aamatch/paths.py:20-51`, `setup_window.py:706-708`).
5. Delete the temp `.pse` (`os.unlink`, `PA-__init__:775`); return the final path.
6. NO `cmd.refresh()`/modal/scheduling tail — Save never ends the game.

**Do NOT wire `backup.py` into Save/Load.** It "remains the Phase-7 persistence policy home" as the PITFALL-9 provenance note only (`06-RESEARCH-restart-reset` §3 verdict; zero `aamatch/` consumers today). The checkpoint container + version gates + atomic-ish zip write are the mechanism; backup.py's injected-store snapshot/restore solves a different problem (v1 mutated user objects in place; AA-match owns its objects).

---

## IMPORT flow map

Spec: "import button to import a game prepared by (3.5) Generate and export" (`spec.md:39`); PERSIST-02; ROADMAP criterion 2 ([HUMAN]). The export side is COMPLETE and round-trip-proven (`game_file.py` whole file; SMOKE-11 PART F2 per the phase brief; `04-12-SUMMARY.md:123`: "`load_container(path, 'game')` -> `parse_game_data` gate chain is already the import-consumer contract").

### I1. Button + wiring

- Attribute **`btn_import`**, label **'Import'** (no naming collision anywhere → bare name per the D7 logic that left `btn_restart` bare; `btn_import_game` is the consistent alternative). Inserted before the stretch (after `btn_save_game`). Tooltip e.g. 'Load a game file exported by Generate and export and start playing it.' — plan pins.

### I2. Wrapper `_on_import` — thin, gate-free (Import works with NO game live)

- `getOpenFileName(self, 'Import AA-match Game', '', 'AA-match Game (*.aamatch.json);;All Files (*)')` — the EXACT export filter (`setup_window.py:896-898`); cancel = silent no-op (`setup_window.py:899` shape).
- NO isinstance gate upfront: unlike Hint/Confirm/Skip/Reset, Import is legal with no game live (it CREATES one — v1's import ran with any prior state, `PA-__init__:790-812`). The gate lives inside the deferred sequence (pop-if-present).
- **NO confirmation warning for mid-game replacement**: house law — spec warnings exist ONLY for Skip/Give Up (`spec.md:43-45`; restart-reset D9, `game_window.py:209-211`). Import mid-game discards the running game exactly like Start does. (Planner may still record this explicitly.)

### I3. Impl `_import_game_from(path)` — the deferred-start replay, payload-direct

**CRITICAL: Import must NOT call `start_game`.** `start_game(setup, seed, candidates, ...)` REGENERATES the payload via `engine.new_game` → `generator.generate` (`gamestart.py:424-427`, `engine.py:267-332`). The embedded payload is THE TRUTH (`game_file.py:17-20`); regeneration is (a) manifest-content-dependent — Phase 8 WILL change MANIFEST.json, silently re-bucketing the same seed (`04-RESEARCH-export-upload` regenerate_vs_embed item 2), and (b) IMPOSSIBLE for uploaded games on the importer machine (no bytes; `game_file.py:19-20`). The `04-RESEARCH-export-upload` phase_7_contract item 7 names the reconstruction target precisely: "`engine.materialize(payload, level_index=0)` + `game_state.GameState()` — the same two calls `start_game` makes — the payload fully determines the initial game".

Step-by-step (mirrors `_start_impl`'s deferred sequence, `setup_window.py:1020-1027`, and `_restart_now`, `game_window.py:704-716`):

1. **Parse + gates (pure, already complete):** `container = persistence.load_container(paths.to_windows_path(path), 'game')` then `parsed = game_file.parse_game_data(container)` → `{'setup', 'payload', 'ligand_texts'}` (`game_file.py:120-164`). Every refusal is a `FormatError` (ValueError family) with a user-appropriate message — `_guard` shows it verbatim; **no catch-and-humanize layer** (see the refusal inventory below). `ligand_texts` feeds the 04-04 `ligand_content` seams directly (`04-03-SUMMARY.md:99`).
2. **`self.cancel_pending_start()` FIRST** (P-2 belt-and-braces, the `_restart_now`:708 / `_on_cleanup`:875 shape) — an in-flight countdown's GO must never activate an orphaned wizard over the imported game.
3. **`self._pop_game_wizard()`** (P-3, `game_window.py:836-855`) — the live GameWizard pops (cleanup restores msm/colors/pk1); a user wizard is never popped. Mid-game Import therefore = **replace semantics identical to Start/Restart**: `start_game`'s cleanup-first law deletes the old `_aam_*` generation (`gamestart.py:31-33,424`), the fresh prepare rebuilds from the file. No residue.
4. **NEW cmd-tier seam (gamestart), e.g. `start_game_from_payload(payload, ligand_content, activate=False)`** — `start_game` minus `new_game`:
   - `placement.cleanup_game_objects()` FIRST (gamestart step-1 law, `gamestart.py:424`).
   - Engine rebind: set `engine._payload = payload`, `_game = game_state.GameState()` (FRESH — a game file is an initial game), `_ligand_content = ligand_content or None` (advance_level's re-materialization input, `engine.py:132,327`), then `engine.materialize(payload, 0, ligand_content=...)`. Today `materialize` sets only `_payload/_registry` (`engine.py:349-351`) — the `_game`/`_ligand_content` writes need either a new engine op (e.g. `engine.prepare_from_payload(...)`) or an additive optional param on `materialize`. The Qt tier must NEVER write these globals (05-07/05-10 law) — the seam lives in the cmd tier.
   - `wiz = GameWizard(payload, registry, 0, 0)` + `compose_molecule_view(registry)` (`gamestart.py:430,447`) — the compose is mandatory (the deferred path's scene must be framed before the countdown; the 03-07 regression law).
   - **`_last_start` capture** — see OQ-3. The naive capture `{'setup': parsed_setup, 'seed': payload['seed'], 'candidates': None, 'ligand_content': ligand_texts}` makes Restart-after-import regenerate: byte-identical for demo games at the same AA-match version, SILENTLY WRONG for imported uploaded games (candidates=None falls back to the bundled manifest, `engine.py:290-302`, and `ligand_content` keys never match demo rows). Recommendation: extend the seam so Restart can replay the exact imported game (e.g. an additive `payload=None` passthrough on `start_game` stored in `_last_start`, or the import seam storing a payload-bearing tuple) — a deliberate SMOKE-11 PART H key-pin evolution (`sorted(ls) == ['candidates','ligand_content','seed','setup']`, `smoke_11_window.py:835-838`).
5. **`self.start_countdown(wiz)`** (`game_window.py:268-284` — self-healing cancel, box clear, 'Get ready...').
6. **Log the pinned `game_imported` line AFTER the arm** (`game_window.py:715` restart-D7 law: the countdown's box clear would wipe a pre-arm line).
7. At GO the EXISTING `_begin_play` runs: `activate_game` (conditional replace re-evaluated, `gamestart.py:365-381`) + `start_timer(time.time())` — **timer from ZERO, correctly** (a game file carries no elapsed; the sidecar elapsed belongs to the checkpoint path only). First level line + `_last_status` seed + 1 Hz start (`game_window.py:302-328`).

**v1 contrast [PA-OBS]:** v1's ONE import handler loaded `.bcmz` bundles (pse+sidecar) for BOTH puzzle and checkpoint kinds and resumed the timer from the sidecar (`PA-__init__:790-868`), with a refuse-first name-collision check before `cmd.load(pse, partial=1)` (`PA-__init__:815-824`). AA-match deliberately split the formats (`04-RESEARCH-export-upload` phase_7_contract item 9: "game file = viewer-independent truth; checkpoint = live session state"), so the base Import here materializes FRESH objects (no `cmd.load` merge, no collision class — `cleanup_game_objects` + `get_unused_name` make collisions structurally impossible, `placement.py:33-39,442-455`). The collision check matters only if Import ALSO learns the checkpoint-zip path (OQ-1).

---

## Timer-before-modal analysis (the trap, resolved)

**The tick's modal-detection code, exactly** (`aamatch/game_window.py:383-394`):

```python
if QtWidgets.QApplication.activeModalWidget() is not None:
    from . import engine
    try:
        engine._current_game().rebase_timer(
            time.time(), self._last_shown_elapsed)
    except engine.EngineError:
        return
    return
self._last_shown_elapsed = self._compute_elapsed()
self._timer_label.setText(self._format_mss(self._last_shown_elapsed))
self._refresh_status()
```

**Does a QFileDialog count as `activeModalWidget()`? YES — resolved, not a guess:**

1. `QFileDialog.getOpenFileName/getSaveFileName` static functions create an application-modal dialog and run it through `exec_()` (standard Qt semantics; PyMOL's own plugins use exactly these statics — `Pymol-script-repo/plugins/vina.py:746`, `plugins/outline.py:170`, cited in `04-RESEARCH-export-upload` Step 0).
2. While it runs, `QApplication.activeModalWidget()` returns it, and timers FIRE THROUGH the nested event loop (P-8, `game_window.py:97-99`; `05-RESEARCH-window-start-timer` P-5: "modal children (QMessageBox, QFileDialog, future confirmations) run a nested event loop that STILL processes timers").
3. **This exact behavior is HUMAN-VERIFIED on this build:** the 05-11 checkpoint recorded "timer FREEZES under the modal file dialog (P-5, the not-headlessly-provable behavior, human-confirmed)" (`05-11-SUMMARY.md:66`, `05-VERIFICATION.md:179-181`, human verdict 2026-09-20). The tick's modal branch was designed for precisely this: "file dialogs, warning boxes alike, which catch the v1 gap of Setup-tab dialogs mid-game" (`game_window.py:368-371`).

**What the wrapper therefore needs (and does NOT need):**

- **NO manual `stop()`/`start()` bracket and NO explicit `rebase_timer` call.** The tick owns the one anchor's pause (P-4 one-anchor law — a second mutation site in the wrapper would reintroduce the v1 two-clock bug class, `05-RESEARCH-window-start-timer` P-4). The v1 manual bracket (`PA-__init__:755-786`: stop → capture → dialog → rebase on ALL exit paths → resume) is SUPERSEDED by the tick-level mechanism (`05-RESEARCH-window-start-timer` Q6/OQ-6: "Recommend (A) [tick-level] now; Phase 7's checkpoint save adds the exact manual bracket" — the bracket's REMNANT that Phase 7 actually needs is only the capture, below).
- **The roadmap note "capture timer before modal file dialogs" concretely requires:** capture the **elapsed VALUE for the sidecar** in the Save wrapper BEFORE `getSaveFileName` opens, and pass it into the impl. Rationale: (a) determinism — the impl then writes a value that does not depend on whether a 1 Hz tick happened to fire and rebase during the dialog (the freeze pins elapsed to the last SHOWN second, ≤1 s coarse, `game_window.py:101-106`); (b) the v1 doctrine verbatim (`PA-persistence.py:62-68`); (c) it keeps the impl a pure function of `(path, elapsed)`. The clock itself stays consistent either way within the documented ≤1 s granularity.
- **Import needs NO timer capture:** a game file is an initial game (timer from zero at GO); pre-GO the anchor is None and `_compute_elapsed()` returns 0.0 (`game_window.py:344-355`).
- **`cmd.save` itself is tick-safe:** it is synchronous on the main thread with no event-loop re-entry, so no tick fires mid-write; the `.pse` size cost (seconds) is absorbed AFTER the dialog with the clock still frozen-until-next-tick. (Load analog: `cmd.load` of a checkpoint `.pse` — same reasoning.)
- **EngineError guard already covers the no-game window** (`game_window.py:387-389`) — e.g. ticks firing between Import's cleanup and the new materialize.

**[UNVERIFIED — needs probe, cheap]:** nothing material remains. The one residual unknown — whether a selection-scoped `cmd.save(path, 'segi AAM')` still carries the wizard/session blobs — is answered by source: `get_session` runs ALL `_session_save_tasks` (including `session_save_wizard`) unconditionally, regardless of `names`/`partial` (`pymol-src/exporting.py:442-455`; task registration `pymol-src/cmd.py:52-53`). The round-trip smoke asserts it in the field anyway.

---

## The wizard-pickle landmine (gate 3) — verified, must-plan

- `cmd.save(.pse)` → `get_session` → `session_save_wizard`: `session['wizard'] = cPickle.dumps(stack, 1)` — the WHOLE stack is in every `.pse` (`pymol-src/wizarding.py:176-179`; HIGH, source-read).
- `cmd.load(.pse)` → `set_session` → ALL `_session_restore_tasks` run unconditionally (also for `partial=1` merges) → `session_restore_wizard`: unpickle, `wiz.cmd = _self`, `wiz.migrate_session(version)`, `set_wizard_stack` (`pymol-src/importing.py:143-166`, `wizarding.py:182-193`).
- **The base `Wizard.__reduce__` returns `(self.__class__, (), self.__getstate__())`** (`pymol-src/wizard/__init__.py:34-36`) — reconstruction calls `GameWizard()` with NO args → `TypeError: __init__() missing 2 required positional arguments: 'payload' and 'registry'` (VERIFIED by live python3.6 pickle simulation this session, mirroring the exact base-class contract). `session_restore_wizard` catches everything and prints `"Session-Warning: unable to restore wizard."` (`wizarding.py:189-192`) — wizard LOST + console noise, double-violating ROADMAP criterion 3 ("the wizard pickles cleanly … console clean during save/load"). v1 had the same latent shape (`PA-wizard.py:37` `__init__(self, controller, target_object, _self=cmd)` — required args) but masked it because its import built a fresh controller.
- **The fix (additive, one method):** `GameWizard.__reduce__` returns `(self.__class__, (self._payload, self._registry, self._level_index, self._molecule_index), self.__getstate__())` — reconstruction runs the real `__init__` (plain-data args, `wizard_core.build_slot_map` over the pickled registry is pure), then pickle applies the state dict on top (all books — `_slot_by_object`, `_color_store`, `_current_slot`, `_saved_msm`, `_last_event`, `_event_seq` — survive). `self.cmd` is rebound by `session_restore_wizard` AFTER construction (`wizarding.py:187`), and `Wizard.__getstate__` already strips it (`wizard/__init__.py:29-32`). A cheap headless probe (construct → `pickle.dumps(,1)` → `loads` → attribute asserts, inside real PyMOL) pins it.
- **Module-identity hazard (document-only):** the pickle records the class by its import path; restore imports THAT path. Same-identity save/load (installed `pmg_tk.startup.aamatch` → relaunch → installed) is consistent; cross-identity (repo-import smoke session ↔ installed session) yields a second module object where `isinstance` gates fail — the AGENTS gate-5 law already forbids mixing identities in one session; the round-trip smoke must save and load under ONE identity, and the human flow is naturally same-identity.

---

## Refusal/message inventory (existing vs new, exact wording)

**Existing, reused verbatim by Import (`_guard` shows `str(e)` — the "every house refusal already names its cause" contract, `game_window.py:464-467`):**

| Refusal | Exact message | Source |
|---|---|---|
| foreign file | `not an AA-match file (magic=%r, expected %r)` | `persistence.py:73-75` |
| missing/invalid header version | `missing or invalid version field in AA-match file` | `persistence.py:76-79` |
| newer container | `unsupported AA-match format version %d (expected <= %d). Please update AA-match.` | `persistence.py:80-83` |
| misfiled kind | `expected an AA-match %s file, found kind=%r` | `persistence.py:84-87` |
| unparseable JSON | `could not parse AA-match JSON: %s` | `persistence.py:126-128` |
| game_format_version missing/invalid | `game file data is missing or has an invalid 'game_format_version'` | `game_file.py:135-139` |
| game_format_version too new | `unsupported game file version %d (expected <= %d). Please update AA-match.` | `game_file.py:140-143` |
| missing setup / level_spec | `game file data is missing 'setup'` / `...'level_spec'` | `game_file.py:145-150` |
| ligand_files shape / base64 | `game file data has an invalid 'ligand_files' ...` / `game file ligand_files entry %r is not valid base64 text (%s)` | `game_file.py:154-159,196-198` |
| integrity/source cross-checks | `game file is missing embedded content for uploaded molecule %r (key %r)` / `game file embeds content for bundled molecule %r ...` / `game file ligand content %r sha256 mismatch ...` / `game file embeds unused ligand content %r` | `game_file.py:214-250` |
| **detector stamp (exact match, both directions)** | `unsupported detector_version %r in level spec (expected %r): stale or newer game spec - regenerate it with a current AA-match generator` | `level_spec.py:116-121` |
| level-spec version/seed/structure | the `parse_level_spec_dict` chain (refuse-newer + minimums) | `level_spec.py:100-125` |

These are user-appropriate as-is (ROADMAP criterion 2's "clear message"): the version messages name the remedy ("Please update AA-match"); the detector message names the cause — for an IMPORTER the "regenerate it" remedy reads as "get a current AA-match / ask the sharer to regenerate"; acceptable v1 wording, planner may confirm at the human checkpoint. **Do NOT build a wrapper-level catch-and-humanize layer** — the 04-13/06-08 convention is `_guard`-verbatim.

**Runtime refusal to mirror (STATE.md:147(b), recorded deviation):** `placement.materialize`'s package-resolved demo-ligand `cmd.load` path is deliberately UNWRAPPED — a missing/corrupt bundled fixture raises raw `pymol.CmdException`, which is OUTSIDE `_guard`'s `(ValueError, OSError)` family and would propagate out of the Qt handler. `engine._ligand_data_for` already wraps its own package loads into `EngineError` naming the ligand (`engine.py:231-241`). **The Phase-7 payload-direct seam must mirror that wrap** (or the import impl gains one try/except mapping CmdException → ValueError-family with the ligand named).

**New wordings Phase 7 pins (pure homes, plan-verbatim):**

- `game_saved` line: sketch `'Game saved to %s.'` (`05-RESEARCH-status-surface.md:290` — v1's was `'Saved checkpoint to %s'`, `PA-__init__:787`). Handler-logged.
- `game_imported` line: sketch `'Game imported: %s.'` (`05-RESEARCH-status-surface.md:291`). Handler-logged AFTER the countdown arms.
- Optional Save gate refusal (if the planner refuses game_over saves): reuse the pinned `'The game is over.'` (`wizard.py:569`), never new wording.
- Zip-structure refusals (checkpoint-load path, if built): mirror v1's shapes — `not an AA-match archive (missing <sidecar arcname>)` / `archive missing game.pse (cannot reconstruct)` (`PA-persistence.py:236-241`).

---

## status_text extensions

- **NO `EVENT_KINDS` changes.** The 15-key set is pinned (`tests/test_status_text.py:304-315`); the `game_saved`/`game_imported` notes must keep containing `'reserved for Phase 7'` (`:329-331`) — and the Phase-6 precedent kept the reserved notes BYTE-UNCHANGED even after the builders landed (all six Phase-6 kinds still read "reserved for Phase 6", `status_text.py:83-89`). Vocabulary work = docstring note only.
- **NO `_EVENT_BUILDERS` entries and NO `status_events` changes.** Both lines are **handler-logged** (`_log`) exactly like `game_restarted_line()` (`status_text.py:260-265` — "it takes no event argument and is EXCLUDED from _EVENT_BUILDERS"): Save/Import are tab-side operations (the wizard is not the actor; for Import the wizard doesn't exist yet), the poll's fingerprint set has no key for them, and an unknown marker kind would fail closed in `status_events` (`status_text.py:381-387`). The 05 research pre-decided this: both reserved kinds are "direct `_log`" (`05-RESEARCH-status-surface.md:290-291`).
- **New pure builders (following the `game_restarted_line` shape):**
  - `game_saved_line(path)` → `'Game saved to %s.' % path` — called by the Save wrapper/impl after success.
  - `game_imported_line(path)` → `'Game imported: %s.' % path` — called AFTER `start_countdown` arms (the countdown's `_info_log.clear()` at `game_window.py:281` would wipe a pre-arm line — the restart D2/D7 law verbatim, `game_window.py:686-689`).
- **No endgame/level interactions:** neither line participates in the poll diff; no new fingerprint keys; `'result'` stays unfingerprinted; the sticky-error rules are untouched. The imported game's first level line still comes from `_begin_play` (`game_window.py:322`).
- Wording detail: long Windows paths in the info box wrap (QTextEdit append wraps); the 04-15 two-line-label fix was a LABEL-side fix, not a log-line law — no action needed.

---

## Headless vs HUMAN test split

Smoke numbering: `smoke/smoke_01..16` exist (dir listing); **next free number = 17**. Runner contract: `bash smoke/run_smoke.sh smoke/smoke_17_*.py [timeout]` greps `=== SMOKE-17 PASS ===` (`smoke/run_smoke.sh:1-17`); ZERO modals headless (the smoke-99 law); PART-lettered, count-asserted (SMOKE-16 shape, `smoke_16_tab.py:13-60`); restore block = cancel_pending_start + `_timer.stop()` + done pop + prefix cleanup + `gamestart._last_start = None` (05-06 Rule-2 + PART-H shape, `06-RESEARCH-restart-reset` §6).

**WSL (pure, python3.6, zero stubs) — new `tests/test_checkpoint.py` (or into `test_game_file.py`):**
- Checkpoint container round-trip: make/parse, `checkpoint_format_version` refuse-newer + missing/invalid refusals (the `game_file.py:135-143` pattern), `kind='checkpoint'` accepted by `check_container` (KINDS already pins it, `persistence.py:37`, `tests/test_persistence.py:46-47`).
- `GameState.to_dict/from_dict` lossless (already proven, `tests/test_game_state.py`) — the sidecar-wraps-verbatim law.
- Timer-elapsed semantics: elapsed ≥ 0; restore rebase math (`rebase_timer(now, elapsed)` → anchor = now − elapsed, `game_state.py:212-243`).
- Zip assembly/parse over temp dirs (stdlib zipfile, whitelisted): arcnames present, missing-member refusals, `to_windows_path` is NOT the pure module's business (callers route).
- The payload-direct seam's pure half if any (e.g. a validate-before-materialize guard) — otherwise none.

**[HEADLESS] T1a (real PyMOL, cmd tier) — the gate-1 round-trip smoke (STATE.md:290 "before committing the checkpoint design"):**
- **Matrix/pose round-trip:** live game → move one AA (bake coords via the movement law) + one scripted rotate → `cmd.save(tmp.pse)` → `cmd.load(tmp.pse)` → centroid equality within `POSE_TOLERANCE` + float32-ulp slack (`placement.py:84-95`), object matrices STILL identity (`wizard.py:523-541` invariant), sentinels intact (`segi AAM`/`b=-999`, `placement.py:97-99`), `detect()` reproduces the pre-save record set. **Records the ROADMAP criterion-1 smoke verdict.**
- **Wizard pickle round-trip:** with the `__reduce__` fix — save → load → `cmd.get_wizard()` isinstance-PASSES, `_color_store`/`_current_slot`/`_last_event` intact, and NO restore failure (a failed restore leaves the stack empty → the isinstance assert fires). Save/load under ONE module identity.
- **Engine rebind + sentinel-first reconcile:** after `cmd.load`, the sidecar/wizard registry reconciles against `extract_game_atoms()` by (object, id) (`placement.py:50-53` identity convention); a mutated-atom negative control refuses fail-closed.
- **Checkpoint resume E2E (headless):** save mid-game (scores + skips + counters + elapsed) → fresh-process-equivalent state (reset engine globals) → load + rebind → `engine.game_status()` equals the saved `to_dict` (minus the rebased anchor) → detect/score continue → timer label resumes from the saved elapsed.
- **Import E2E:** export a game (`export_game`, `setup_window.py:86-117`) → drive the import impl with the PATH (no dialog) → fresh GameState zeros, payload-direct materialize (atom counts match the payload), countdown arms, GO activates, timer from zero, `game_imported` line last; detect on-grid → 0 records.
- **Import refusals (drive the impl directly, assert the raise):** foreign file, newer container version, misfiled kind, unparseable JSON, wrong `game_format_version`, stale detector stamp (`'det-0'` re-stamp — the 02-15 template, `04-RESEARCH-export-upload` detector_stamp_placement), sha256 mismatch, upload-without-content. Exact-message asserts (the refusal inventory above).
- **Save impl:** drive `_save_game_to(path, elapsed)` headlessly → zip exists, contains both members, sidecar parses, `.pse` loads; cancel path needs nothing (wrapper-level).

**[HEADLESS] T1b (offscreen Qt, SMOKE-17 parts or SMOKE-16 extension):**
- Buttons exist with exact labels + non-empty tooltips; the stretch stays LAST after both insertions (the no-reflow law, `game_window.py:130-133`).
- Save/Import impls driven AS METHODS; wrapper-gate silent no-ops (no wizard → `_on_save_game`/`_on_import` produce nothing — box paths are [HUMAN]-only).
- The elapsed-capture ordering assert: `timer_anchor = time.time() - 75` → wrapper capture reads ≈75 → impl receives it (deterministic-value proof).
- `_last_start` shape/aliasing pins (SMOKE-11 PART-H pattern) + whatever OQ-3 decides.

**[HUMAN] (the ROADMAP criterion 1 [HUMAN] half + criterion 2 + criterion 3 [GATE]):**
- Real dialogs: Save dialog default/filter/extension-append feel; Import dialog picks a real `.aamatch.json`; cancel paths.
- **The full save → quit → relaunch → load round-trip on setenv.bat PyMOL** (positions/orientations, scores, counters, timer resuming; Game status tab usable after restore).
- Console cleanliness during save/load (no `Session-Warning`, no tracebacks) — criterion 3's [GATE] recording.
- Restore after a plugin reload (criterion 3); mid-game Import feel (old game replaced, countdown, fresh timer); the wizard-pickle identity story on an installed session.

---

## Open questions for the planner

1. **The checkpoint LOAD affordance (largest scope decision).** The spec has no Load button (`spec.md:39-47`); criterion 1 requires "save → quit → relaunch → load". Options: (a) **Import dispatches on file kind** — `.aamatch.json` game vs `.aamz` checkpoint zip (v1's one-button model, `PA-__init__:790-868`; the filter grows to both extensions; the checkpoint branch = unzip → cleanup-first → `cmd.load(pse, partial=1)` → engine rebind from sidecar → sentinel-first reconcile → timer re-anchor → resume WITHOUT the 3-2-1, or with a resumed-elapsed countdown per v1); (b) PyMOL File→Open of the `.pse` + a plugin-side rebind hook (no natural trigger exists; the restored wizard's first engine op would raise 'engine: no live game', `engine.py:135-140`); (c) defer checkpoint-load UX to a human decision at the phase checkpoint. **Recommend (a)** — it is the only affordance the spec's button inventory supports and mirrors the shipped v1 exactly.
2. **`GameWizard.__reduce__` override** — treat as a MUST (gate 3), not an option; without it every `.pse` save/load prints "Session-Warning: unable to restore wizard." and loses the wizard (verified above). One additive method + the headless pickle probe.
3. **`_last_start` / Restart-after-import.** Naive capture makes Restart regenerate: byte-identical for demo games (deterministic generator, same manifest version), SILENTLY WRONG for imported uploaded games (`candidates=None` → bundled manifest fallback, `engine.py:290-302`). Options: (c1) accept + document the residue; (c2) make the replay payload-direct (additive `payload` passthrough on `start_game`/`_last_start` — a deliberate SMOKE-11 PART-H key-pin evolution); (c3) import leaves `_last_start` untouched (Restart replays the PRE-import game — surprising). **Recommend (c2)**; the same mechanism then serves Restart-after-checkpoint-restore (sidecar carries `last_start`).
4. **`cmd.save` scope:** `'segi AAM'` (game objects only — lean, avoids merging user objects back on load, v1 saved target-only for the same reason, `PA-__init__:773-774`) vs `'(all)'` (whole session incl. user objects — fuller resume, collision risk on merge, bloat). Settings/wizard blobs are saved regardless (source-verified). Probe both in the round-trip smoke; **lean 'segi AAM'** unless the probe shows lost state.
5. **Sidecar schema pin-downs:** `timer_elapsed` sibling key vs overwriting `game_state['timer_anchor']`; registry in the sidecar vs wizard-carried (if OQ-2's fix lands, the wizard self-carries it — the sidecar copy is then the reconcile authority only); whether `pre_game_names` belongs in a resumed session at all (it is cleanup bookkeeping, not game truth).
6. **Save gating on a panel-ended game** (wizard still on stack, `game_over` True, timer running): allow-and-roundtrip vs refuse with `'The game is over.'` (see S2-1).
7. **Cosmetics at plan time:** default Save filename + `.aamz` filter wording (04-RESEARCH OQ-5 precedent); whether Import's filter gains `*.aamz` now or at the checkpoint-load plan; button order vs the spec bullet order.
8. **Do NOT touch:** the movement/nudge code (a separate human re-open is tracked at `STATE.md:309` — Phase 7 must not perturb it; the round-trip smoke only READS poses); `backup.py` wiring (§3 verdict); `EVENT_KINDS`.

---

## Sources

### Primary (HIGH — read this session, file:line)
- `aamatch/game_window.py` (whole file — button row/insert law, tick modal branch, handler family, `_restart_now`, `_endgame_sequence`, `_guard`, `_pop_game_wizard`)
- `aamatch/gamestart.py` (whole — `start_game` steps/ordering, `activate_game`, `_last_start`)
- `aamatch/engine.py` (whole — new_game/materialize/global-state split, lifecycle ops, `game_status`)
- `aamatch/game_file.py` (whole — five-gate chain + every refusal message), `aamatch/persistence.py` (whole — KINDS/container/atomic I/O), `aamatch/level_spec.py:100-125` (detector exact-match)
- `aamatch/game_state.py` (whole — to_dict/from_dict, rebase_timer/stop_timer), `aamatch/wizard.py` (whole — contracts 2/5, `__init__` signature, `_guard`, `_require_playing`), `aamatch/placement.py` (materialize/registry/sentinels/cleanup), `aamatch/setup_window.py` (whole — all five QFileDialog sites, `_guard`, `_start_impl`, `export_game`), `aamatch/paths.py`, `aamatch/status_text.py` (whole), `aamatch/backup.py` (whole)
- `pymol-src/modules/pymol/wizarding.py:150-193` (session save/restore wizard), `pymol-src/modules/pymol/wizard/__init__.py:17-40` (`migrate_session`, `__getstate__`, `__reduce__`), `pymol-src/modules/pymol/exporting.py:782-830,370-460` (`save`, `get_session` + unconditional session_save_tasks), `pymol-src/modules/pymol/importing.py:125-166` (`set_session` + unconditional restore tasks), `pymol-src/modules/pymol/cmd.py:43-53` (task registration)
- Live python3.6 pickle simulation (this session): base `__reduce__` contract + required-arg `__init__` → `TypeError` on unpickle — the GameWizard landmine.
- `tests/test_purity.py` (PURE_MODULES=18 + `zipfile` whitelisted), `tests/test_status_text.py:300-345` (kind pins), `tests/test_persistence.py:46-68` (KINDS pin)

### Secondary (HIGH/MEDIUM — recorded project evidence)
- `05-11-SUMMARY.md:66` + `05-VERIFICATION.md:179-181` — **human-confirmed** timer freeze under a real modal file dialog (2026-09-20)
- `05-RESEARCH-window-start-timer.md` (P-1..P-8, Q5/Q6/OQ-6 — the pause-mechanism decision + v1 manual-bracket doctrine), `05-RESEARCH-status-surface.md:290-291` (the reserved-kind sketches + direct-`_log` routing)
- `04-RESEARCH-export-upload.md` (game_file design, regenerate_vs_embed, detector_stamp_placement, **phase_7_contract** items 1-9, OQ-4/5)
- `06-RESEARCH-restart-reset.md` (deferred-sequence replay, P-2/P-3, D7/D9, the cross-game state ledger, backup.py no-role verdict, the Import-interplay note §8-OQ3)
- `04-12-SUMMARY.md:123`, `04-03-SUMMARY.md:16-17,99` (the import-consumer contract), `STATE.md:107,147,290,305,309` (02-10 wrap-don't-reshape; the CmdException deviation to mirror; the Phase-7 gates)
- [PA-OBS] `tmp/bioCHEMeleon/biochemeleon/__init__.py:676-868` (`_on_export`/`_on_save`/`_on_import` full flows), `persistence.py:40-250` (sidecar schema, capture-before-dialog doctrine, `.bcmz` zip I/O), `wizard.py:37` (v1's same-shape required-arg wizard init)

### Tertiary (LOW — flagged)
- QFileDialog static-call modality internals beyond the human-verified freeze (standard Qt semantics; no further probe needed for planning)
- Cross-identity pickle restore behavior (module-identity hazard — document-only; same-identity flows verified by construction)

## Metadata

**Confidence breakdown:**
- Save/Import flow maps: HIGH — every step cites current repo source; the handler family and deferred sequence are landed, proven code.
- Timer-before-modal: HIGH — source-read tick + human-verified freeze (05-11); the capture-doctrine mapping is the v1-recorded rationale.
- Wizard-pickle landmine: HIGH — source-read save/restore mechanics + live unpickle simulation; the fix is additive and probe-cheap.
- Pitfalls/ refusing inventory: HIGH — every message quoted from source.
- Scope decisions (load affordance, `_last_start`, save scope): MEDIUM — evidence-complete, but they are planner/human calls, not facts.

**Research date:** 2026-09-21 · **Valid until:** ~2026-10-21 (stable repo baselines; re-verify only if gamestart/game_window/game_file/wizarding change materially)
