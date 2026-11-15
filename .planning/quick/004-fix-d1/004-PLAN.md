---
phase: quick-004
plan: 004
type: execute
wave: 1
depends_on: []
files_modified: [aamatch/engine.py, aamatch/game_state.py, aamatch/status_text.py,
                 aamatch/game_window.py, aamatch/wizard.py, aamatch/gamestart.py,
                 tests/test_status_text.py, tests/test_game_state.py,
                 smoke/smoke_16_tab.py, smoke/smoke_07_wizard_loop.py,
                 smoke/smoke_20_checkpoint_e2e.py]
autonomous: true

must_haves:
  truths:
    - "Clicking Done in the wizard panel mid-game no longer leaves the Qt Game-tab clock counting: within one 1 Hz tick of the pop the timer is STOPPED, the label is frozen at the abandon instant (<= 1 s poll granularity, the documented modal-pause law), and the info box shows EXACTLY ONE clearly-ended line ('Game abandoned.') -- never an endgame block, never a modal, never a summary record (Done != Give-Up)"
    - "The engine GameState is truthfully ended by the abandon: game_status() reads game_over True + end_state 'abandoned' + final_time frozen, so the existing game-over locks (advance/give_up/complete_game/record refusals) gate every engine op on the abandoned game; endgame_summary keeps FAIL-CLOSING on 'abandoned' (a pinned WSL refusal -- no summary can EVER build for an abandoned game)"
    - "Give-Up is byte-unchanged: still the scored, confirmation-guarded exit with its endgame modal + summary; panel Confirm-completion stays the F3-F7 receipted path (standing SMOKE-16 PART F rows green, byte-untouched)"
    - "The Done-that-races-the-poll case (panel Confirm completes the game, the user clicks Done before the next tick) converges on the LEGITIMATE end: one endgame block + the exact final M:SS + the once-latched modal arm -- never re-branded as an abandon"
    - "A user wizard stacked OVER a live GameWizard (cmd.drag stock-recipe) does NOT stop the clock: the abandon detector requires NO GameWizard ANYWHERE in cmd.get_wizard_stack(); after the user wizard pops, the GameWizard auto-resumes and the tab keeps working"
    - "Restart/Start remain available after an abandon (a fresh game arms the countdown per F6-composition); every tab impl (Confirm/Skip/Give-Up/Hint/Reset/Save) is inert on the abandoned game behind the no-wizard gates"
    - "Deferred (b) closed additive-only: snapshot_books/resume_from carry _saved_button_mode, and a checkpoint-rebuilt wizard's eventual cleanup restores the pre-arm button_mode profile (old checkpoints without the key load EXACTLY as today -- .get -> None -> repair skipped)"
  artifacts:
    - path: "aamatch/engine.py"
      provides: "public op 18 abandon_game(now=None) -> final_time (float): refuses 'the game is already over' (EngineError), sets end_state 'abandoned', stop_timer freeze, builds NO summary; OPS docstring list grows op 18; give_up/complete_game/endgame_summary byte-untouched"
      contains: "def abandon_game"
    - path: "aamatch/status_text.py"
      provides: "pure handler-logged builder game_abandoned_line() -> 'Game abandoned.' in the game_restarted_line shape (no event arg, NOT in _EVENT_BUILDERS, ZERO EVENT_KINDS change -- the vocabulary pin stays exactly 16)"
      contains: "def game_abandoned_line"
    - path: "aamatch/game_window.py"
      provides: "_abandon_check() -- the D1 detector called at the head of _refresh_status's no-live-GameWizard branch: guards (timer active / countdown inactive / _last_status held / not game_over / NO GameWizard in get_wizard_stack()), timer.stop() FIRST, then the missed-transition convergence tail or the abandon tail (stop/freeze/'Game abandoned.'); the game_over transition block (lines 539-586) byte-untouched"
      contains: "_abandon_check"
    - path: "tests/test_status_text.py"
      provides: "additive TestGameAbandonedLine mirroring TestGameRestartedLine: pinned wording / not in _EVENT_BUILDERS / no event argument"
      contains: "game_abandoned_line"
    - path: "tests/test_game_state.py"
      provides: "additive WSL refusal pin: end_state 'abandoned' makes endgame_summary raise ValueError (the no-record law, mechanically)"
      contains: "abandoned"
    - path: "aamatch/wizard.py"
      provides: "books carry: snapshot_books gains 'saved_button_mode': self._saved_button_mode; resume_from reads books.get('saved_button_mode') (absent -> None); activate/cleanup bodies byte-untouched (the 08.3-13 AST pins stay green)"
      contains: "saved_button_mode"
    - path: "aamatch/gamestart.py"
      provides: "checkpoint-rebuild button_mode repair: in load_checkpoint's rebuild branch (after the msm repair, before activate) cmd.set('button_mode', str(int(saved_bm)), quiet=1) + cmd.mouse() when the books carry it -- the probe-D2 restore pair mirrored so a rebuilt wizard's activate snapshots the TRUE pre-arm profile"
      contains: "saved_button_mode"
    - path: "smoke/smoke_16_tab.py"
      provides: "PART G (dated 2026-11-16): the Done-abandon drive G1-G6 -- live mid-game / one-tick stop+freeze+mark+line+objects-survive / poll inertness / post-abandon locks + Restart composition / the missed-transition convergence / the buried-wizard negative control (cmd.drag recipe); PART rows A-F byte-untouched; verdict count line grows the PART G field"
      contains: "Game abandoned."
    - path: "smoke/smoke_07_wizard_loop.py"
      provides: "PART G additive rows (dated): snapshot_books carries saved_button_mode (7-key roster) + resume_from restores the corrupted _saved_button_mode; existing rows byte-untouched"
      contains: "saved_button_mode"
    - path: "smoke/smoke_20_checkpoint_e2e.py"
      provides: "forced-rebuild additive rows (dated): _saved_button_mode == sidecar saved_button_mode (repair landed) + ONE pop restores the saved button_mode profile; existing rows byte-untouched"
      contains: "saved_button_mode"
  key_links:
    - from: "aamatch/game_window.py _refresh_status no-GameWizard branch"
      to: "GameTab._abandon_check"
      via: "called at the branch head before the 'Required: -' reset; falls through to the wizard-free reset (required label + baseline clear) AFTER the abandon tail so the SMOKE-11/'Required: -' receipts stay green"
      pattern: "_abandon_check\\(\\)"
    - from: "GameTab._abandon_check"
      to: "cmd.get_wizard_stack() membership"
      via: "abandon ONLY when NO stack entry isinstance GameWizard -- the buried-wizard guard (stock cmd.drag installs Dragging OVER the GameWizard; the game must keep running)"
      pattern: "get_wizard_stack\\(\\)"
    - from: "GameTab._abandon_check abandon tail"
      to: "aamatch/engine.py abandon_game"
      via: "engine.abandon_game() returns the frozen final_time; the label pins through the pure status_text.format_mss -- the Qt tier never touches engine/wizard privates (the 05-07/05-10 accessor law)"
      pattern: "engine\\.abandon_game\\(\\)"
    - from: "GameTab._abandon_check missed-transition tail"
      to: "engine.endgame_summary() + ending singleShot"
      via: "the 08.1-08 path-outcome parity tail verbatim-in-shape: endgame_lines logged once, exact final M:SS, cmd.refresh + 100 ms singleShot modal arm gated by _endgame_modal_shown + platform=offscreen (P-6/smoke-99 law)"
      pattern: "singleShot"
    - from: "smoke_16_tab.py PART G"
      to: "the D1 defect (08.3-VERIFICATION routing)"
      via: "G2 receipts the one-tick stop/freeze/mark; G5 receipts the race convergence; G6 receipts the buried-stack negative control -- the headless Done-path lifecycle proof the 08.3 checkpoint could not give"
      pattern: "PART G"
    - from: "wizard.snapshot_books / gamestart.run_rebuild"
      to: "resume_from('saved_button_mode') + the cmd.set/cmd.mouse() repair"
      via: "the additive-only persistence law (persistence.py FORMAT_VERSION refuses-only-newer, .get-default reads): a checkpoint saved by this fix restores the pre-arm profile; an older file reads the key absent and skips -- byte-identical legacy behavior"
      pattern: "get\\('saved_button_mode'\\)"
---

<objective>
Fix D1, the Done-path lifecycle defect the 08.3-16 [HUMAN] checkpoint surfaced (verbatim: "clicking Done in panel the qt window timer still counting after panel clear. giveup does give up") and fold the adjacent deferred item (b) that lives in the same lifecycle seam.

Root cause (verifier-located, .planning/phases/08.3-drag-movement-pivot/08.3-VERIFICATION.md routing section, commit 85699ff): the Game tab's timer stop rides ONLY the `game_over` transition in `game_window.py _refresh_status` (+ `_endgame_sequence`); the wizard panel's Done button is the canonical `cmd.set_wizard()` pop -- NOT an end path -- so no signal ever reaches the tab and the 1 Hz timer keeps advancing the label over a game whose panel is gone. Give-Up exits through `engine.give_up`/`complete_game` (game_over transition), which is why it works. A pre-existing Phase-5/6 lifecycle gap; `game_window.py` was byte-untouched by the entire 8.3 pivot.

The fix lands the APPLIED-DEFAULT Done semantics ([HUMAN]-lite; yolo mode + the human imperative "fix D1" = implement the proposed default and record a DATED note amendable at the next GUI touch, the 08.3-01 convention, never silent): **panel Done mid-game = abandon-stop** -- the tab's poll detects the pop (no GameWizard left anywhere in the wizard stack), STOPS the 1 Hz timer FIRST (the phase-7 timer law), freezes the elapsed display at the abandon instant via a new `engine.abandon_game` op (end_state `'abandoned'` + stop_timer freeze; NO endgame modal, NO summary record, no giveup counter -- Done != Give-Up: Give-Up stays the scored, confirmation-guarded exit while Done = closing the board), logs ONE clearly-ended line via a new pure `status_text.game_abandoned_line()`, and the existing game-over locks gate every further op. Restart/Start stay available for a fresh game. The Done-that-raced-the-poll case (panel Confirm completed the game, Done popped before the tick observed it) converges on the LEGITIMATE end (endgame block + exact final time + the once-latched modal) -- every end path converges on one moment (the 08.1-08 parity law); a user wizard merely stacked OVER the game wizard never triggers a false abandon (the `cmd.get_wizard_stack()` membership guard).

Fold deferred item (b) (08.3-04 follow-up, confirmed still true in the 08.3 verification): `_saved_button_mode` is not carried by `snapshot_books`/`resume_from` and the checkpoint REBUILD path repairs msm only -- a resumed (rebuilt) game's eventual cleanup restores the session's button_mode instead of the user's pre-arm profile. The fold is a small additive row in the same seam: books key + `.get` read + a `cmd.set`/`cmd.mouse()` repair in the rebuild branch, additive-only so old checkpoints load exactly as today.

Purpose: the 08.3-16 human approved the drag core and docketed D1 as the one working defect; this closes the docket row (plus (b)) so Phase 9 (help wording) inherits a correct lifecycle instead of documenting a bug.
Output: 3 committed tasks -- (1) `feat(quick-004):` engine op 18 + pure builder + WSL pins; (2) `feat(quick-004):` GameTab poll detection + SMOKE-16 PART G; (3) `feat(quick-004):` + `test(quick-004):` the (b) fold + dated smoke rows. Full battery green at 969 + 4 new tests; touched smokes 07/16/20 green (+18 receipted untouched), standing rows byte-untouched. A dated [HUMAN]-lite applied-default note the human can amend at the next GUI touch; (a) stays deferred.
</objective>

<execution_context>
@~/.config/opencode/get-shit-done/workflows/execute-plan.md
@~/.config/opencode/get-shit-done/templates/summary.md
</execution_context>

<context>
@AGENTS.md
@.planning/STATE.md
@.planning/phases/08.3-drag-movement-pivot/08.3-16-SUMMARY.md
@aamatch/engine.py
@aamatch/game_state.py
@aamatch/status_text.py
@aamatch/game_window.py
@aamatch/wizard.py
@aamatch/gamestart.py
@tests/test_status_text.py
@tests/test_game_state.py
@tests/test_engine_public_api.py
@smoke/smoke_16_tab.py
@smoke/smoke_07_wizard_loop.py
@smoke/smoke_20_checkpoint_e2e.py

**The human record (08.3-16-SUMMARY.md, 2026-11-15, verbatim):** "most working as expect, but clicking Done in panel the qt window timer still counting after panel clear. giveup does give up". Routing (.planning/phases/08.3-drag-movement-pivot/08.3-VERIFICATION.md): D1 = OUT-OF-PHASE pre-existing Phase-5/6 lifecycle gap (`game_window.py` absent from the 8.3 production diff), timer stop rides the endgame transition only; deferred (b) `_saved_button_mode` absent from the books methods folds into the same fix; O1 was resolved separately (works-as-designed, commit 116d13d) and is NOT in this plan; (a) `_drag` residual STAYS DEFERRED.

**Design facts (all verified in the code this session, line numbers pre-edit):**

- **The defect site.** `aamatch/game_window.py:507-514` -- `_refresh_status`'s no-live-GameWizard branch (isinstance gate on `cmd.get_wizard()`): today it only resets the required label to `'Required: -'`, clears `_last_status`, and returns; the 1 Hz timer (`self._timer`) keeps firing and `_on_tick` (:447-477) keeps advancing `_timer_label` from the LIVE GameState anchor. The timer stop lives in three places only: the game_over transition block (:539-586, polls `state.get('game_over') and not prev_go` -- unreachable once the wizard is popped), `_endgame_sequence` (:1170-1194, tab ops only), and the resume game_over branch (:1154-1158). Panel Done = `cmd.set_wizard()` pop (wizard.py:40-42, the 03-02 canonical Done pin) -> the popped wizard's `cleanup()` (wizard.py:340-386: msm restore, drag dearm, button_mode restore, pk1 hygiene, color restores -- do NOT touch) -- no signal reaches the tab.
- **Why Restart/Import can't false-trigger.** `_restart_now` (:796-862) / `_import_game_from` (:1037-1098) pop and arm `start_countdown` in the SAME synchronous stack: during the countdown `_countdown_timer.isActive()` is True and `_pending_wizard` is held; the poll's wizard-free fall-through already clears `_last_status` there today. `_resume_checkpoint_from` (:1100-1166) re-arms instantly with the wizard ON the stack. Teardowns in every smoke stop the tab timer BEFORE `cmd.set_wizard()` + `processEvents` (the A9/D5/E6/F7 pattern) -- verified across smokes 07/11/13/14/15/16/17/20/24: the ONLY `_on_tick` drives in the battery are smoke_11:1078 (wizard live) and smoke_16:1796/1814 (post-game_over), so no standing row can enter the abandon branch.
- **The buried-wizard discriminator.** `cmd.get_wizard_stack()` is the verified PyMOL 2.5 stack read (SMOKE-24 rows + 08.3-RESEARCH-drag.md probe B1-B6 receipts: `cmd.drag(<obj>)` installs stock Dragging OVER a live GameWizard -> stack `['GameWizard', 'Dragging']` -> Done-pop of Dragging auto-resumes the GameWizard). A user wizard on top makes `cmd.get_wizard()` non-GameWizard WHILE the game stays live under it -- so top-of-stack alone can never mean "popped"; the detector requires NO GameWizard ANYWHERE in the stack.
- **The engine seam for the mark.** `engine.give_up` (:694-713) and `complete_game` (:716-731) are the twins: `game_over` guard (EngineError 'the game is already over'), caller-owned `end_state`, `stop_timer(now)` capture+freeze, then `endgame_summary()` (:734-744) returns the SCORE-07 dict. `GameState` (aamatch/game_state.py) needs ZERO code change: `stop_timer` (:282-304) already freezes `final_time` + sets `game_over=True`; the reason `end_state` is caller-owned (:209-213); `endgame_summary` (:341-446) fail-closes on `end_state not in ('completed', 'gave_up')` -- so `'abandoned'` is REFUSED by existing code, exactly the no-record law (pinned by tests/test_game_state.py:680-698; the new VALUE breaks nothing). `adopt_game`'s rebase gate `if elapsed_at_save is not None and not game.game_over` (engine.py:398) and the tab's resume game_over branch (:1154) make a hypothetical abandoned checkpoint resume freeze gracefully. Docstrings documenting the domain (`game_state.py:209-213, :288-292`) get the additive `'abandoned'` mention.
- **The pure line surface.** `status_text.game_restarted_line()` (:301-306) is the builder template: no event argument, handler-logged by the tab, EXCLUDED from `_EVENT_BUILDERS` (:344-351), NO EVENT_KINDS entry (vocabulary pinned at EXACTLY 16 keys by tests/test_status_text.py `test_exact_16_keys`; the 07-03 law: handler-logged lines need no kind). New builder: `game_abandoned_line()` returning the pinned `'Game abandoned.'` -- wording = the proposed default (records as a dated [HUMAN]-lite applied-default; the Phase-9 discuss plan inherits a re-word candidate: Done = "closing the board").
- **The engine public-API test is additive-safe.** tests/test_engine_public_api.py pins ONLY `current_game`/`remap_ligand_bonds` (present + aliased) -- adding a new public op trips nothing. The OPS docstring list (engine.py:33-116, ops 1-17) grows op 18 in the same prose style. `EngineError(ValueError)` (engine.py:130).
- **Prose/AST pin discipline while editing.** BANNED tokens never in touched prose: `get_model`/`matrix_reset`/`get_object_ttt` (tests/test_code_audit.py PROSE_PIN pins engine.py's `matrix_reset` count at exactly 2 -- do not touch those docstrings; wizard.py may carry ZERO of the three); banned visual calls `indicate`/`distance`/`load_cgo` in SCANNED_MODULES [wizard.py, gamestart.py, setup_window.py, game_window.py, upload.py] (tests/test_wizard_source.py:51-55) -- the gamestart repair's `cmd.set`/`cmd.mouse()` are NOT banned (they are the wizard cleanup's own restore pair, wizard.py:374-377, probe D2). 08.3-13's AST order pins (activate push->msm->button_mode->gesture-wiring; cleanup restore ordering; arm-last-in-do_pick) cover ONLY activate/cleanup/do_pick bodies -- the (b) fold touches `snapshot_books` (:568-592) / `resume_from` (:594-616) which carry NO order pins.
- **The (b) fold surface.** `snapshot_books` carries exactly {current_slot, color_store, event_seq, last_event, error, saved_msm} (grep-confirmed; the 08.3 verification's "keys carried are current_slot/color_store/event_seq/last_event/error/saved_msm only"). Books consumers: `capture_checkpoint_snapshot` (gamestart.py:563 `wizard_books=wiz.snapshot_books()`, VERBATIM embed -- SMOKE-18's B row compares `data['wizard'] == wiz.snapshot_books()`, auto-adapting) and the checkpoint rebuild branch (gamestart.py:717-731): `wiz.resume_from(books)` then the msm REPAIR `saved_msm = books.get('saved_msm'); if saved_msm is not None: cmd.set('mouse_selection_mode', int(saved_msm))` BEFORE `wiz.activate(replace=0)` -- because activate() snapshots-then-remaps (the 03-03 ORDER LAW), the repair is what makes the rebuilt wizard's cleanup restore the true profile. button_mode needs the SAME repair with the probe-D2 pair (`cmd.set('button_mode', str(int(v)), quiet=1)` + `cmd.mouse()`), plus the books key + `.get` read (absent -> None -> skip -- additive-only persistence law; persistence FORMAT_VERSION refuses-newer only, `tests/test_checkpoint.py:540 test_missing_blocks_accepted_as_none`; the 6-key WIZARD_BOOKS fixture (:172-174) and `parsed['wizard'] == WIZARD_BOOKS` (:292) stay green because the FIXTURE stays 6-key). The ADOPT path needs nothing (the pickled wizard carries `_saved_button_mode` since 08.3-04, a plain int attr).
- **Smoke anchors.** SMOKE-16 (`smoke/smoke_16_tab.py`, 1892 lines, T1b offscreen recipe, `check()` + `REC['checks']` at :327-333, verdict printer :1881-1891 carrying `=== SMOKE-16 PASS ===` -- the marker stays byte-identical; append PART G after PART F's `except` block at :1870, extend ONLY the count-summary line with a PART G field, keep the six-smoke NOT-RUN regression loop :1876-1878 untouched). PART F (:1738-1871) is the structural template (fresh `SetupWindow()` + `gamestart.start_game(setup=SETUP_D, seed=42, candidates=[BENZ, SECOND], activate=False)` + `start_countdown` + 4 `_countdown_tick()` drives; teardown = cancel + `_timer.stop()` + `cmd.set_wizard()` + `placement.cleanup_game_objects()` + `gamestart._last_start = None` + baseline compare). PART A owns `place_required_pi(wiz)` (:447) and the PASSING panel-confirm recipe (F1-F2: five `skip_molecule()` + placed confirm -> `game_over` + `summary['end_state'] == 'completed'`, headline 'You win! All 3 level(s) finished in'). `_game_objects_b()` helper exists for the objects-survive assertion. Smoke counts today: 16 = 113 (A36/B23/C14/D10/E18/F12); 07 = 83 (PART G books round trip at :945-1005 is the (b) anchor: snapshot -> DEEPCOPY save -> corrupt `_saved_msm = 7` etc. -> `resume_from` -> equality rows; extend with `_saved_button_mode` corruption + re-resume + 7-key roster); 20 = the two-run save->verify recipe with the forced-rebuild C rows at :483-499 (the msm repair landing + ONE-pop proof -- the button_mode rows mirror them; `saved_bm` read at the snap block :306-310).
- **Baselines.** WSL `python3.6 -m unittest discover -s tests` = 969/969 (08.3-15 receipt on a byte-identical tree + 08.3 verification re-run); py_compile green; smokes 01-24 ALL PASS; touched-smoke timeouts per the 08.3-15 map: 07/16/18/20 at 240 s each via `bash smoke/run_smoke.sh <script> <timeout>`; SMOKE-20 = TWO invocations (save run + fresh-process verify run) per its header recipe, with the documented stale-fixture contingency (a leftover `tmp/smoke fixtures/aam_pse20/` makes run 1 a VERIFY run -- see Task 3 verify step 5).

**Repo laws (binding):**
- WSL Ubuntu dev shell; `python3.6` (3.6.9) for py_compile + unit tests ONLY; NEVER pip/apt/conda install; no sys.modules stubs anywhere; PURE_MODULES untouched (game_state.py + status_text.py stay pure: docstring + a pure no-import builder only).
- Deliberate-evolution law: NO standing pin is edited silently. This plan's smoke/test work is ADDITIVE (new rows/methods only); if an in-place edit proves unavoidable, it gets a DATED EXPECTED-RED bridge in 004-SUMMARY.md naming the row, never a quiet rewrite. Smokes 01-15 + 17-19 + 21-24 are byte-frozen and untouched entirely; SMOKE-16 rows A-F, SMOKE-07 existing rows, SMOKE-20 existing rows stay byte-identical.
- The [HUMAN]-lite record: yolo mode + the imperative "fix D1" -- the Done semantics land as the PROPOSED DEFAULT with DATED (2026-11-16) applied-default notes in the touched production docstrings (game_window module docstring + game_abandoned_line + abandon_game), amendable by the human at the next GUI touch; the 08.3-01 convention, never silent. The full decision row + the Phase-9 help re-word note + the still-deferred (a) carry-forward go in 004-SUMMARY.md.
- Do NOT update ROADMAP.md (quick tasks are separate); do not touch `.planning/phases/`, `Pymol-script-repo/`, `vmd-ref/`, `3rd_party_lib/`, `tmp/` fixtures except as SMOKE-20's own recipe consumes them.
- Solo main-line (single plan, no worktree).
</context>

<tasks>

<task type="auto">
  <name>Task 1: Engine op 18 abandon_game + pure game_abandoned_line + WSL pins</name>
  <files>aamatch/engine.py, aamatch/game_state.py, aamatch/status_text.py, tests/test_status_text.py, tests/test_game_state.py</files>
  <action>
    1. **`aamatch/engine.py` -- add op 18 `abandon_game`.** Position the def directly after `complete_game` (before the `endgame_summary` def at :734). Body mirrors the give_up shape with the payload differences spelled in the docstring:
       ```python
       def abandon_game(now=None):
           """Op 18 (quick-004, 2026-11-16): Done-pop abandon -- end the
           game WITHOUT a record. The panel Done button's canonical
           cmd.set_wizard() pop is not an end path; the Game tab's poll
           observer (aamatch/game_window.py _abandon_check) reaches HERE
           on detecting the popped wizard. Sets ``end_state`` 'abandoned'
           + ``stop_timer`` capture/freeze, then returns the frozen
           ``final_time`` float -- NO endgame_summary is built (Done !=
           Give-Up: 'abandoned' fail-closes in GameState.endgame_summary,
           so no endgame block, no modal payload, no giveup_count -- the
           scored exit stays give_up's alone). Refuses an already-ended
           game with the give_up message family. [HUMAN]-lite applied
           default (2026-11-16): amendable at the next GUI touch."""
           game = current_game()
           if game.game_over:
               raise EngineError(
                   'engine.abandon_game: the game is already over')
           game.end_state = 'abandoned'
           game.stop_timer(now)
           return game.final_time
       ```
       - Append the corresponding OPS docstring row (item 18) to the module docstring's op list (engine.py:33-116) in the same prose style. PROSE_PIN guard: do NOT add/remove any `matrix_reset`/`get_model`/`get_object_ttt` mention anywhere (the two existing `(never matrix_reset)` stays untouched); give_up (:694-713), complete_game (:716-731), endgame_summary (:734-744) stay BYTE-IDENTICAL.
       - Do NOT touch anything else in the file (the quick-003 public/alias pins and all call sites are additive-safe).
    2. **`aamatch/game_state.py` -- docstring-only additive mention.** Extend ONLY the end_state domain prose (class docstring field rows around :209-213 and `stop_timer`'s end-REASON sentence around :288-292) to read `'completed' | 'gave_up' | 'abandoned'`, with one added sentence: "'abandoned' (quick-004, Done-pop) is set only by the engine lifecycle op; `endgame_summary` keeps refusing it fail-closed -- an abandoned game never builds a summary (Done is not a scored exit)." ZERO code/logic/import changes -- this module stays byte-identical in every executable statement.
    3. **`aamatch/status_text.py` -- the pure builder.** Add `game_abandoned_line()` directly after `game_restarted_line()` (:301-306), copying its exact structural shape (no event arg; a one-line docstring stating: handler-logged by the Game tab's Done-pop abandon detector (quick-004/D1) in the game_restarted_line pattern; EXCLUDED from ``_EVENT_BUILDERS``; the handler-logged pattern needs no EVENT_KINDS entry -- the 07-03 law; wording 'Game abandoned.' is the dated [HUMAN]-lite applied default 2026-11-16, amendable at the next GUI touch). Return value pinned: `return 'Game abandoned.'`. Do NOT touch EVENT_KINDS, `_EVENT_BUILDERS`, or any existing builder.
    4. **`tests/test_status_text.py` -- additive `TestGameAbandonedLine`** mirroring `TestGameRestartedLine` (:556-568) exactly: (a) `test_basic` -- `game_abandoned_line() == 'Game abandoned.'`; (b) `test_not_in_poll_builder_table` -- the function is not a value in `_EVENT_BUILDERS`; (c) `test_takes_no_event_argument` -- `inspect` the signature for zero parameters (mirror `TestPhase7BuildersHandlerLogged`'s take-no-event-arg style at :840, but as a fresh method on the new class -- do NOT edit any existing test). Also assert the EVENT_KINDS vocabulary is untouched by importing it and checking `'game_abandoned' not in EVENT_KINDS` inside `test_not_in_poll_builder_table`.
    5. **`tests/test_game_state.py` -- additive refusal pin.** In the endgame-summary fail-closed area (right after `test_fail_closed_unknown_end_state` :690-698), add `test_abandoned_end_state_refused_by_summary`: build a GameState, record enough for a would-be 'completed' summary not to matter, set `gs.end_state = 'abandoned'`, assert `gs.endgame_summary([1])` raises ValueError (and that `str(e)` mentions `end_state`) -- pinning mechanically that NO summary can ever build for an abandoned game. Follow the file's existing fail-closed assertion style.
  </action>
  <verify>
    1. `python3.6 -m py_compile aamatch/*.py` -> clean.
    2. `python3.6 -m unittest tests.test_status_text -v` -> ALL green (53 existing + 3 new).
    3. `python3.6 -m unittest tests.test_game_state -v` -> ALL green (existing + 1 new; every existing endgame/round-trip/refusal test untouched-green).
    4. `python3.6 -m unittest discover -s tests -v` -> ALL green, REPORT the real total with attributed arithmetic: 969 + 3 (TestGameAbandonedLine) + 1 (abandoned-refusal) = 973 expected -- report actuals; purity gates green (game_state/status_text still in PURE_MODULES, zero new imports there).
    5. `python3.6 -m unittest tests.test_engine_public_api -v` -> green (the op addition trips nothing).
    6. `grep -n "abandoned" aamatch/engine.py aamatch/game_state.py aamatch/status_text.py tests/test_status_text.py tests/test_game_state.py` -> only the new op/builder/docstring/test mentions; `grep -c "matrix_reset" aamatch/engine.py` -> still exactly 2.
    7. `git status` shows ONLY the 5 named files. Commit: `feat(quick-004): D1 core half 1 -- engine abandon_game (op 18, no-record end state) + pure game_abandoned_line + WSL pins`.
  </verify>
  <done>
    abandon_game() refuses an already-over game, sets end_state 'abandoned', freezes final_time, returns the float, builds no summary; the OPS docstring lists op 18; game_state end_state domain prose names 'abandoned' with the no-summary note; game_abandoned_line() pins 'Game abandoned.' in the handler-logged shape with zero EVENT_KINDS drift; WSL battery green at the reported count (973 expected); no prose-pin token touched; the 5-file commit landed atomically.
  </done>
</task>

<task type="auto">
  <name>Task 2: GameTab poll detects the panel-Done pop (abandon-stop) + SMOKE-16 PART G</name>
  <files>aamatch/game_window.py, smoke/smoke_16_tab.py</files>
  <action>
    1. **`aamatch/game_window.py` -- add the `_abandon_check` helper** (place it right after `_refresh_status`, before the Hint-handler section at :589), and call it as the FIRST statement inside `_refresh_status`'s no-live-GameWizard branch ({game_window.py:510-514} -- after the isinstance check's `return`-guard shape: the branch becomes `self._abandon_check()` + the existing label reset/baseline clear lines, then `return`). Helper contract (THE chosen minimal-risk fix seam -- pure tab-side observation, zero wizard.py changes, zero 08.3-13 pin-surface wakes):
       ```python
       def _abandon_check(self):
           """quick-004 (2026-11-16, D1): closing the Done-path lifecycle gap ...

           Called ONLY from _refresh_status's no-live-GameWizard branch.
           Guards: 1 Hz timer active (else pre-GO/post-endgame/never-
           started -- nothing to abandon); NO pending countdown (a
           Restart/Import owns its pop->arm window, P-1/P-2 -- the
           pending countdown's GO re-seeds the baseline); a held
           _last_status (else nothing was ever observed); the held
           state not game_over (the game_over transition + _endgame_
           sequence own the endgame tail, idempotently); and NO
           GameWizard ANYWHERE in cmd.get_wizard_stack() (a user wizard
           merely stacked over the game wizard -- cmd.drag of a stock
           editor being the receipted case -- leaves top-of-stack
           non-GameWizard while the game stays live; only a genuine
           Done-pop empties the stack of GameWizards).

           STOP ORDER (the phase-7 timer law): self._timer.stop() runs
           BEFORE any engine/modal work, and detection runs inside the
           one tick being serviced -- no further tick can fire, so the
           poll cannot race the final tick. Then:
           - engine.is_over() True -> the Done CLICK RACED THE POLL (a
             panel Confirm completed the game and Done popped it before
             this tick observed the game_over transition): converge on
             the 08.1-08 parity tail -- log status_text.endgame_lines
             (the sanctioned engine.endgame_summary() accessor), pin
             the EXACT final M:SS, cmd.refresh() + the 100 ms
             singleShot modal arm (offscreen gate + once-latch inside
             _show_endgame_modal keep smokes hang-proof and the box
             once-per-game). Never re-brand a completed game as an
             abandon.
           - else -> ABANDON-STOP (the applied-default Done semantics):
             engine.abandon_game() (returns the frozen final_time),
             pin the label to it via status_text.format_mss, log ONE
             'Game abandoned.' line. NO endgame block, NO modal, NO
             record (Done != Give-Up). The fall-through wizard-free
             reset (the caller's 'Required: -' + baseline clear) still
             runs -- the required label reads no-game, the frozen
             timer label survives it.
           The ValueError family mid-poll soft-returns with the clock
           already stopped (the render-loop soft-error discipline;
           practically unreachable given the guards). The 1 Hz freeze
           granularity is <= 1 s after the pop (the documented
           modal-pause granularity law)."""
           if not self._timer.isActive():
               return
           if self._countdown_timer.isActive():
               return
           if self._last_status is None:
               return
           if self._last_status.get('game_over'):
               return
           from pymol import cmd
           from . import wizard as wizard_mod
           for entry in cmd.get_wizard_stack():
               if isinstance(entry, wizard_mod.GameWizard):
                   return
           self._timer.stop()
           try:
               from . import engine, status_text
               if engine.is_over():
                   summary = engine.endgame_summary()
                   for line in status_text.endgame_lines(summary):
                       self._log(line)
                   self._timer_label.setText(
                       status_text.format_mss(summary['final_time']))
                   cmd.refresh()
                   QtCore.QTimer.singleShot(
                       100, lambda: self._show_endgame_modal(summary))
                   return
               elapsed = engine.abandon_game()
               self._timer_label.setText(
                   status_text.format_mss(elapsed))
               self._log(status_text.game_abandoned_line())
           except ValueError:
               return
       ```
       Implementation notes: `engine.is_over()` refusal (EngineError before new_game) is inside the `except ValueError` family and soft-returns -- with the guards, a no-game window with a held baseline and an active timer is unreachable anyway. Lazy relative imports INSIDE the method (the module-identity law). The game_over transition block (:539-586), `_endgame_sequence`, `_show_endgame_modal`, `_pop_game_wizard` stay BYTE-IDENTICAL. PROSE_PIN guard: no banned-token prose. Also extend the module docstring with a short dated paragraph (2026-11-16): panel Done mid-game = abandon-stop -- the poll now detects the pop, stops/freezes/marks via engine.abandon_game (op 18); Done-that-raced-the poll converges on the endgame tail; Done != Give-Up ([HUMAN]-lite applied default, amendable at the next GUI touch); a stacked user wizard never triggers it (the get_wizard_stack membership guard).
    2. **`smoke/smoke_16_tab.py` -- append PART G** (dated 2026-11-16) after PART F's `except` block (:1870), mirroring PART F's construction/teardown skeleton (`dlg7`/`tab7`, baseline capture, `try/except` with the house teardown in both paths, `processEvents` + `dlg7.close()`), `REC['checks']`-counted via the existing `check()`. Rows:
       - **G1 live mid-game**: `wiz_g = gamestart.start_game(setup=SETUP_D, seed=42, candidates=[BENZ, SECOND], activate=False)` + `tab7.start_countdown(wiz_g)` + 4 `_countdown_tick()` drives -> `cmd.get_wizard() is wiz_g` AND `tab7._timer.isActive()` AND `engine.game_status()['game_over'] is False`.
       - **G2 the Done-pop + ONE tick** (the defect row): record `names_g1 = cmd.get_names('objects')`; `cmd.set_wizard()` (the canonical Done pop) -> **assert the honest symptom**: `tab7._timer.isActive()` STILL True (pre-fix this counted forever; the fix is the STOP after detection) AND no 'Game abandoned.' in the box yet; then ONE `tab7._on_tick()` drive -> assert ALL: `not tab7._timer.isActive()`; `engine.game_status()['game_over'] is True` AND `['end_state'] == 'abandoned'`; `tab7._timer_label.text() == status_text.format_mss(engine.game_status()['final_time'])`; box contains EXACTLY one `'Game abandoned.'`; NO endgame block (`'You win!' not in text` AND `'Game over -- gave up' not in text`); `cmd.get_wizard() is None`; `_aam_*` objects SURVIVE the pop (Done semantics: `sorted(_game_objects_b())` equal to the G1 roster); the required label fell through to `'Required: -'`.
       - **G3 poll inertness**: ONE direct `tab7._refresh_status()` drive -> no second 'Game abandoned.' (still exactly one), still stopped, label unchanged.
       - **G4 post-abandon locks + fresh-game composition**: `tab7._confirm_now() is None` + `_skip_now() is None` + `_giveup_now() is None` + `_hint_now() is None` + `_reset_grid_now() is None` with log/scene untouched (the no-wizard gates; the engine's game-over locks are the belt behind them); then `r_restart_g = tab7._restart_now()` returns True AND `tab7._pending_wizard` is a GameWizard AND the box's last two lines are `['Get ready...', 'Game restarted.']` (Restart stays available -- the F6 mirror); house teardown (cancel + `_timer.stop()` + `cmd.set_wizard()` + `placement.cleanup_game_objects()` + `gamestart._last_start = None`) + baseline-EXACT compare.
       - **G5 the missed-transition convergence** (a fresh `dlg8`/`tab8`, the F1-F2 recipe): five `skip_molecule()` panel ops + `place_required_pi(wiz8)` + a PASSING `confirm_molecule()` -> `last8.get('game_over') is True` (the engine completed); **before any tick**: `cmd.set_wizard()` (Done races the poll) -> assert `engine.game_status()['game_over'] is True` AND `tab8._timer.isActive()` (the transition never observed) AND `cmd.get_wizard() is None`; then ONE `tab8._on_tick()` drive -> assert ALL: box counts `'You win! All 3 level(s) finished in'` == 1; `'Game abandoned.' NOT in the box` (a completed game is never re-branded); `not tab8._timer.isActive()`; `tab8._timer_label.text() == status_text.format_mss(summ8['final_time'])`; `processEvents()` runs clean (the armed 100 ms shot lands on the offscreen gate and no-ops -- the smoke-99 receipt). House teardown + baseline compare.
       - **G6 the buried-wizard negative control** (a fresh `dlg9`/`tab9`, G1 drive): `obj9 = sorted(_game_objects_b())[0]`; `cmd.drag(obj9)` (the SMOKE-24 P1 stock recipe) -> assert `type(cmd.get_wizard()).__name__ == 'Dragging'` AND `'GameWizard'` in the `cmd.get_wizard_stack()` type names; ONE `tab9._on_tick()` drive -> assert `tab9._timer.isActive()` (NO false abandon) AND `'Game abandoned.' not in box` AND `engine.game_status()['game_over'] is False`; `cmd.set_wizard()` -> Dragging pops, GameWizard auto-resumes (`cmd.get_wizard() is wiz9`); ONE more `tab9._on_tick()` -> the resumed game still works: `tab9._required_label.text() == status_text.required_display(wiz9.get_status()['required'])` (the held-baseline reseeded silently). House teardown + baseline compare.
       - Extend the verdict count-summary print (:1881-1889) with a PART G field (additive edit of that line ONLY; the `=== SMOKE-16 PASS ===` marker and the six-smoke NOT-RUN regression loop stay byte-identical); add the dated docstring note: PART G (2026-11-16 quick-004): the Done-abandon battery, checks 113 -> 113+G (report actuals); rows A-F byte-untouched.
       - Docstring/rows prose guard: no banned tokens.
  </action>
  <verify>
    1. `python3.6 -m py_compile aamatch/*.py` -> clean.
    2. `python3.6 -m unittest discover -s tests -v` -> ALL green at Task 1's total (973 expected; this task adds ZERO tests) -- purity + wizard_source 29/29 + status_text gates re-prove the touched-source discipline automatically.
    3. `bash smoke/run_smoke.sh smoke/smoke_16_tab.py 240` -> exit 0 with `=== SMOKE-16 PASS ===`; the count line reports PART A-F at their byte-unchanged counts (A36/B23/C14/D10/E18/F12) + PART G; the F3-F7 receipt rows PASS unmodified. If a standing A-F row FAILS, the tab change broke a pinned behavior: fix game_window.py, NEVER the row.
    4. Regression spot receipts (heads-up-only documentation): SMOKE-11's I4 tick drive and SMOKE-15's endgame battery rely on surfaces this task leaves byte-identical; the full-battery sweep in the plan verification re-runs the touched set. (No run required this task.)
    5. `git status` shows ONLY aamatch/game_window.py + smoke/smoke_16_tab.py. Commit: `feat(quick-004): D1 tab half -- GameTab poll detects the panel-Done pop (stop/freeze/one-line; done != gave_up) + SMOKE-16 PART G`.
  </verify>
  <done>
    One tick after a mid-game panel Done: the 1 Hz timer is stopped, the label frozen at the abandon instant, 'Game abandoned.' logged once, the engine marked game_over/'abandoned' with final_time frozen, NO endgame block/modal/record, the _aam_* objects survive, Restart arms a fresh countdown; the raced case converges on the completed-game endgame exactly once; a stacked user wizard leaves the clock running and the game live; SMOKE-16 green with A-F byte-untouched and PART G counted; WSL battery green at 973.
  </done>
</task>

<task type="auto">
  <name>Task 3: Fold deferred (b) -- _saved_button_mode books carry + rebuild repair + dated smoke rows</name>
  <files>aamatch/wizard.py, aamatch/gamestart.py, smoke/smoke_07_wizard_loop.py, smoke/smoke_20_checkpoint_e2e.py</files>
  <action>
    1. **`aamatch/wizard.py` -- books carry (additive, ~3 lines).** In `snapshot_books` (:568-592): add `'saved_button_mode': self._saved_button_mode,` to the returned dict (right after the `'saved_msm'` row). In `resume_from` (:594-616): after the `saved_msm` row, add `saved_button_mode = books.get('saved_button_mode')` + `self._saved_button_mode = None if saved_button_mode is None else int(saved_button_mode)` (the saved_msm mirror -- absent key -> None -> exactly today's behavior; the additive-only persistence law). Extend the two method docstrings: the books row list names the new key (08.3-04 attribute, quick-004 carry) and resume_from's P9 passthrough sentence gains "`saved_button_mode` rides the `saved_msm` pattern (`.get` -> None legacy default)". DO NOT touch `activate` / `cleanup` / any other body (the 08.3-13 AST pins + SMOKE-24 row 4b receipts stay green by construction).
    2. **`aamatch/gamestart.py` -- the rebuild-path repair.** In `load_checkpoint`'s rebuild branch (:717-731), right after the msm repair (`saved_msm = books.get('saved_msm'); if saved_msm is not None: cmd.set('mouse_selection_mode', int(saved_msm))`) and BEFORE `wiz.activate(replace=0)`, add the probe-D2 mirror:
       ```python
       saved_bm = books.get('saved_button_mode')
       if saved_bm is not None:
           cmd.set('button_mode', str(int(saved_bm)), quiet=1)
           cmd.mouse()
       ```
       Rationale (encode in the step-7 docstring sentence): a REBUILT wizard's activate() snapshots the CURRENT button_mode after the push (the msm ORDER-LAW analog; wizard.py:308-313), and the session restored the SAVE-TIME game profile -- so without the repair the rebuilt wizard's eventual cleanup would restore the game profile instead of the user's pre-arm profile. The ADOPT path needs nothing (the pickled wizard already carries `_saved_button_mode`). Legacy files (key absent) -> None -> skipped -> byte-identical today-behavior. PROSE_PIN guard: no banned tokens (`matrix_reset`/`get_model`/`get_object_ttt` never in gamestart prose; `cmd.set`/`cmd.mouse` are not banned calls).
    3. **`smoke/smoke_07_wizard_loop.py` -- additive PART G rows (dated 2026-11-16).** Inside the existing part-G drive (after the 'resume_from restores the scalar books exactly' check at :991-999): corrupt + re-resume + roster --
       ```python
       # quick-004 (2026-11-16) deferred-(b) rows: the books carry
       check('part G snapshot_books carries saved_button_mode (7-key roster)',
             sorted(saved_books) == ['color_store', 'current_slot', 'error',
                                     'event_seq', 'last_event',
                                     'saved_button_mode', 'saved_msm'],
             'keys=%s' % (sorted(saved_books),))
       wiz_g._saved_button_mode = 999      # corrupt then re-resume
       wiz_g.resume_from(saved_books)
       check('part G resume_from restores saved_button_mode',
             wiz_g._saved_button_mode == saved_books['saved_button_mode']
             and isinstance(wiz_g._saved_button_mode, int),
             'got=%r want %r'
             % (wiz_g._saved_button_mode,
                saved_books['saved_button_mode']))
       ```
       Existing part-G checks stay byte-identical (the earlier scalar-books check already resumed over an uncorrupted button field once -- the new corruption happens after it). Add the dated count/docstring note (83 -> 85).
    4. **`smoke/smoke_20_checkpoint_e2e.py` -- additive forced-rebuild rows (dated 2026-11-16).** At the snap block (:306-310, right after `saved_msm = books.get('saved_msm')`) add `saved_bm = books.get('saved_button_mode')`. In the C forced-rebuild section: right after the `_saved_msm == saved_msm` check (:483-489) add
       ```python
       # quick-004 (2026-11-16) deferred-(b) rows: the repair landed
       check('C forced-rebuild: _saved_button_mode == sidecar '
             'saved_button_mode (the quick-004 repair landed)',
             saved_bm is not None
             and rebuilt._saved_button_mode == saved_bm,
             'got=%r want=%r'
             % (getattr(rebuilt, '_saved_button_mode', '?'), saved_bm))
       ```
       and after the msm ONE-POP pair (:496-499) add
       ```python
       popped_bm = int(cmd.get('button_mode'))
       check('C pop->cleanup restores the repaired button_mode profile',
             popped_bm == saved_bm,
             'post-pop button_mode=%d want %r' % (popped_bm, saved_bm))
       ```
       Existing rows byte-identical; dated docstring note (+2 checks).
    5. **`smoke/smoke_18_save_checkpoint.py` -- NO EDITS.** Its B row compares `data['wizard'] == wiz.snapshot_books()` (verbatim embed) and auto-adapts to the 7-key books; SMOKE-17's facts rig pins wizard __dict__ (unchanged -- no new attribute) -- both stay green; both are receipted in the verification runs only.
  </action>
  <verify>
    1. `python3.6 -m py_compile aamatch/*.py` -> clean; full discover green at Task 2's total (973; this task adds ZERO WSL tests -- wizard/gamestart are cmd-tier).
    2. `python3.6 -m unittest tests.test_wizard_source -v` -> 29/29 (the activate/cleanup/do_pick AST pins + both scans green over the edited wizard.py/gamestart.py).
    3. **Production commit first** (receipts: every EXISTING row green on the folded code): `bash smoke/run_smoke.sh smoke/smoke_07_wizard_loop.py 240` -> `=== SMOKE-07 PASS ===` (83 existing still counted); `bash smoke/run_smoke.sh smoke/smoke_18_save_checkpoint.py 240` -> `=== SMOKE-18 PASS ===` (B row green over the 7-key books, ZERO script edits); `bash smoke/run_smoke.sh smoke/smoke_16_tab.py 240` -> PASS (the books key rides the Save/D paths SMOKE-16 drives; rows byte-untouched). Commit: `feat(quick-004): fold deferred (b) -- wizard books carry _saved_button_mode + checkpoint-rebuild profile repair`.
    4. **Then the dated rows**: `bash smoke/run_smoke.sh smoke/smoke_07_wizard_loop.py 240` -> PASS with 85 checks (report the count line); `bash smoke/run_smoke.sh smoke/smoke_16_tab.py 240` -> PASS (unchanged from step 3). Commit: `test(quick-004): dated smoke rows -- SMOKE-07 books round trip + SMOKE-20 rebuild (2026-11-16)`.
    5. **SMOKE-20 two-run per its header recipe**: check `tmp/smoke fixtures/aam_pse20/` first -- if fixtures are absent, run `bash smoke/run_smoke.sh smoke/smoke_20_checkpoint_e2e.py 240` TWICE in immediate succession (run 1 SAVE, run 2 VERIFY, both must print `=== SMOKE-20 PASS ===`). STALE-FIXTURE contingency: if fixtures are present (an interrupted earlier battery), the first invocation is a VERIFY run over OLD books that lack the key -- its teardown still clears the fixtures; note any `(b)`-row FAIL from that stale pass, then run the full two-run pair again -- the recorded pair must be ALL-PASS. Record every invocation + counts in the SUMMARY.
    6. `git status` clean of unintended files across the two commits; no other smoke/test file touched (`git diff --stat` shows exactly: wizard.py, gamestart.py, smoke_07, smoke_20 across the two commits).
  </verify>
  <done>
    snapshot_books carries saved_button_mode (7-key roster, SMOKE-07 receipt); resume_from restores it (int-coerced/None legacy default); a checkpoint-rebuilt wizard snapshots the REPAIRED pre-arm profile (SMOKE-20 `_saved_button_mode == saved_bm` + ONE-pop live equality receipts); old checkpoints (6-key books) load byte-identically as today (`.get` -> None -> repair skipped); SMOKE-07/16/18/20 + the fresh two-run pair ALL PASS with every pre-existing row byte-untouched; two atomic commits landed (feat + test).
  </done>
</task>

</tasks>

<verification>
The FULL battery on the final tree, from repo root, all mandatory:
1. `python3.6 -m py_compile aamatch/*.py` -> PYC-OK.
2. `python3.6 -m unittest discover -s tests -v` -> `Ran 973 tests` (attributed: 969 baseline + 3 TestGameAbandonedLine + 1 abandoned-summary refusal) with ZERO failures AND the standing gates individually visible in the -v output: test_purity (pure registry unchanged at 19 + game_state/status_text still pure), test_wizard_source 29/29, test_status_text (all), test_code_audit 10/10, test_engine_public_api, TestConfirmPassGatePresent 2/2. Report actuals if the leading count differs (never pad -- investigate an attribution surprise instead).
3. Touched-smoke receipts: SMOKE-16 (240 s) `=== SMOKE-16 PASS ===` with A-F at their byte-unchanged counts (A36/B23/C14/D10/E18/F12) + PART G (report G + total); SMOKE-07 (240 s) PASS at 85; SMOKE-20 pair (240 s x2) PASS per its recipe; SMOKE-18 (240 s) PASS byte-untouched (the 7-key books VERBATIM row).
4. `git diff HEAD~N` end-inspection over the branch: no smoke 01-15/17/19/20-pre-existing-rows/21-24 byte touched; no ROADMAP.md; no `.planning/phases/` edits; EVENT_KINDS untouched in status_text.py; the give_up/complete_game/endgame_summary bodies byte-identical; the game_over transition block + `_endgame_sequence` + `_show_endgame_modal` byte-identical in game_window.py; the two commits-per-plan-task scope integrity (quick-004 scopes only).
5. Zero silent pin edits: any in-place edit to a standing row that the executor could not avoid (none is expected -- the plan is additive by construction) MUST carry a DATED EXPECTED-RED bridge row in 004-SUMMARY.md naming the row + reason.
</verification>

<success_criteria>
- D1 CLOSED at the UI level: a mid-game panel Done stops the Qt clock within one tick, freezes the display at the abandon instant, marks the engine game honestly ('abandoned', no record), shows exactly one 'Game abandoned.' line, never shows a modal/summary for it, and leaves Restart/Start available -- while Give-Up is untouched and the raced-completion case still gets its real endgame.
- The false-positive seams receipted headlessly: a stacked user wizard (G6) never stops a live game; Restart/Import countdowns never trigger the detector (existing A/B/D/E/F rows green); the missed-transition case converges on the legitimate end (G5).
- Deferred (b) CLOSED additive-only with receipts in SMOKE-07 (roster + round trip) and SMOKE-20 (repair landed + one-pop restore), legacy-tolerance by construction (`.get` -> None mirror of saved_msm).
- Battery truth: py_compile clean; WSL 973/973 with attributed arithmetic; touched smokes 07/16/20 (+ untouched 18) ALL PASS; nothing outside the plan's files_modified touched; the dated [HUMAN]-lite applied-default note + the Phase-9 help-word note + the still-deferred (a) row recorded in the SUMMARY.
</success_criteria>

<output>
After completion, create `.planning/quick/004-fix-d1/004-SUMMARY.md` carrying: the dated (2026-11-16) [HUMAN]-lite applied-default record for the Done semantics (abandon-stop vs the rejected alternatives -- endgame-on-Done would erase Done != Give-Up; tab-only-stop would leave the engine lying about a live game -- amendable at the next GUI touch); the exact test/smoke count arithmetic; every receipt marker line; the SMOKE-20 invocation ledger (including any stale-fixture contingency run); zero/silent-pin-edit accounting; the Phase-9 carry-forward note (help wording: panel Done = closing the board, no summary by design; a 'Game abandoned.' re-word candidate); and the still-deferred (a) `_drag` residual one-liner (un-met; SMOKE-24 row 4b continues to receipt the wizard-side empty set + the residual).
</output>
