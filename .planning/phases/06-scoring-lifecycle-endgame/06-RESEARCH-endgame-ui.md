# Phase 6: Scoring Lifecycle & Endgame — RESEARCH (Endgame Screen, Confirmation Warnings, Modal/Timer Patterns)

**Researched:** 2026-09-20
**Scope:** SCORE-05 (Skip warning UI), SCORE-06 (Give Up warning + endgame trigger), SCORE-07 (the endgame screen itself) — the UI side of Phase 6 only. SCORE-01/02/03/09/10 lifecycle/engine mechanics are the sibling research stream; where they touch this surface (op seams, event kinds, data shapes) the contract is recorded here so both streams converge.
**Confidence:** HIGH (every load-bearing claim cites shipped repo code, Phase-4/5 summary laws, or the runtime-verified v1 prior art in the same PyMOL 2.5.0 / PyQt5 5.12.3 environment)

**Primary recommendation:** Endgame screen = a modal child QMessageBox (v1 `_finish_win` shape: parent `self.window()` + `WindowStaysOnTopHint` + `exec_()`), shown ~100 ms after the endgame scene changes via `cmd.refresh()` + `QTimer.singleShot(100, ...)`; the Skip/Give-Up warnings are `QMessageBox.question` Yes/No modals owned by thin tab wrappers (the `_X_impl` law); the timer needs NO new pause machinery (the 1 Hz tick's existing modal-pause rebase covers the warnings) but DOES need an explicit stop + exact-final-elapsed render at game end (v1 `_on_win`'s `self._timer.stop()` precedent); all endgame wording lives in pure `status_text.py` (the reserved `EVENT_KINDS` kinds get their text pinned there).

---

## 1. Current widget/state inventory (what exists today)

### 1.1 The window and tab structure

| Item | Location | Evidence |
|---|---|---|
| Modeless `SetupWindow(QDialog)`, module-scope `_window` singleton, `open_window()` reuse-and-raise | aamatch/setup_window.py:66-83 | Contract 1/2 in the module docstring (:14-31); NO closeEvent override (:32-36) |
| Two-tab `QTabWidget`: 'Setup' + 'Game status' | setup_window.py:241-245 | `self.tabs.addTab(setup_page, 'Setup')`; `self.game_tab = game_window.GameTab(self)`; `addTab(self.game_tab, 'Game status')` |
| 7 Setup buttons live on the Setup page (spec.md:21); game-lifecycle buttons belong to the Game tab | setup_window.py:202-233, 235-245 | The 05-06 restructure kept the button row on Setup |
| Tab switch to Game status happens in `_start_impl` step 3 | setup_window.py:1025 (`self.tabs.setCurrentWidget(self.game_tab)`) | The window is the sequencer (05-09 law) |

### 1.2 GameTab's widget inventory (aamatch/game_window.py — whole file read)

| Widget/member | Line | State today |
|---|---|---|
| `_timer_label` QLabel `'0:00'` (timer OUTSIDE the info box, spec.md:37) | game_window.py:99-101 | Rendered by the 1 Hz tick |
| `_required_label` QLabel `'Required: -'` | game_window.py:102-105 | Rendered by `_refresh_status` on molecule change |
| `_info_log` read-only QTextEdit + `_log(line)` append channel | game_window.py:110-113, 150-157 | The rolling info box (auto-scrolls) |
| `btn_hint` QPushButton 'Hint' — the ONLY button | game_window.py:119-126 | Connected to `_on_hint` (05-08). **The button row is `btn_hint` + `addStretch(1)` — NO confirm, NO skip/give-up dropdown, NO restart, NO reset, NO save, NO import exist today** (the stretch reserves their slots, game_window.py:84-87, 124) |
| `_countdown_timer` member QTimer + `_countdown_n` + `_pending_wizard` | game_window.py:131-134 | Cancellable 3-2-1 countdown (P-1/P-2) |
| `_timer` member QTimer (1 Hz) + `_last_shown_elapsed` | game_window.py:138-140 | Started only at `_begin_play` (GO) |
| `_last_status` plain-dict poll baseline | game_window.py:146 | 05-10 poll-diff state |
| `_format_mss` staticmethod `'%d:%02d'` (minutes unbounded, v1 exact format) | game_window.py:250-255 | **This is the timer formatter the endgame screen must reuse** |
| `_on_tick` modal-pause branch | game_window.py:276-283 | `if QtWidgets.QApplication.activeModalWidget() is not None:` → `engine._current_game().rebase_timer(time.time(), self._last_shown_elapsed)` → early return (label frozen, poll skipped) |
| `_compute_elapsed` | game_window.py:237-248 | `max(0.0, time.time() - gs.timer_anchor)`, 0.0 when anchor None; reads the LIVE `engine._current_game()` |
| `_refresh_status` poll-diff | game_window.py:291-328 | `cmd.get_wizard()` + isinstance gate → `status_text.status_events(self._last_status, state)`; no wizard → `'Required: -'` + baseline cleared |
| `_guard(fn)` — the 04-09 contract VERBATIM on GameTab | game_window.py:332-343 | catch `(ValueError, OSError)` → `QtWidgets.QMessageBox.warning(self, 'AA-match', str(e))`; anything else propagates; returns fn()'s value, None on refusal |
| `_on_hint` / `_hint_now` — the thin-wrapper/non-modal-impl + wizard-op-through-seam precedent | game_window.py:345-371 | `prior = cmd.get_wizard(); if not isinstance(prior, wizard.GameWizard): return None; result = prior.hint()`; logs the pinned line from the returned dict |

**Key structural facts for Phase 6:**
- `_begin_play` owns the FIRST status content (level line + required label + `_last_status` seed) at GO (game_window.py:195-221) — the "start sequence owns the first observation" law any endgame sequence should mirror ("the end sequence owns its own lines").
- The `engine._current_game()` accessor is the tick's only engine touch (game_window.py:244-246); the grep law is zero `engine._game`/`_payload` attribute hits in game_window.py (05-10, STATE.md:188) — `_current_game()` is a call, not an attribute hit, and stays legal.
- `from pymol import cmd` is function-level inside `_refresh_status`/`_hint_now` (game_window.py:313, 359) — new handlers keep this shape.

### 1.3 Engine/wizard state the endgame surface reads

| Data | Shape | Evidence |
|---|---|---|
| `GameState` fields | `current_level_index`, `current_molecule_index`, `molecule_scores` (flat list of floats, record order), `skip_count`, `giveup_count`, `timer_anchor` (float/None), `formed_types_per_molecule` (`'L{i}M{j}'` → formed type list) | game_state.py:168-175 |
| `total_score` | property = `sum(molecule_scores)` | game_state.py:182-185 |
| `advance_molecule` / `advance_level` | index mutators only — **nothing materializes the next level; Phase 6 must wire materialize-on-advance (sibling stream)** | game_state.py:226-233 |
| `record_molecule_result(level, molecule, required, results)` | appends to `molecule_scores` UNCONDITIONALLY — **re-Confirm double-append hazard is live today** (wizard.py:552-553 caveat: "repeated Confirm appends to the engine GameState's molecule_scores — score-history semantics are Phase 6's lifecycle") | game_state.py:235-248; wizard.py:544-553 |
| `rebase_timer(now, elapsed)` | `timer_anchor = float(now) - float(elapsed)`; negative elapsed → ValueError; "The CALLER (the 1 Hz tick) owns modal detection" | game_state.py:193-224 (caller note :207-209) |
| `engine.game_status()` | read-only 7-key `to_dict()` snapshot, EngineError before new_game | engine.py:472-478 |
| `engine.confirm(level, molecule, required)` | `(records, score, formed)` = detect_molecule + score_current (records+score stored in ONE call) | engine.py:462-469 |
| `GameWizard._guard(op,...)` | maps ValueError family → `self._error` + refresh, returns op value or None — **lifecycle ops can deliver endgame data through this seam (05-08)** | wizard.py:436-449; STATE.md:186 |
| `GameWizard.get_status()` | plain dict incl. `level_pos`, `level_total`, `molecule_pos`, `molecule_total`, `result`, `error` | wizard.py:333-362 |
| `GameWizard.activate/cleanup` | stack-native lifecycle; pop = canonical `cmd.set_wizard()` → cleanup (msm restore, color restores + `cmd.rebuild`) runs, prior wizard auto-resumes; `_aam_*` objects SURVIVE the pop (Done semantics) | wizard.py:154-206, 31-39 |
| `gamestart._last_start` | module-level `{'setup','seed','candidates','ligand_content'}` captured after a successful start — the Restart replay source (sibling stream, cited here because the endgame's post-game state must not corrupt it) | gamestart.py:167-178, 408-416 |
| `gamestart.activate_game(wiz)` | push + `start_timer(time.time())` anchoring from zero | gamestart.py:323-339 |

### 1.4 Gates that will run on the new code

- **Gate D** compiles every `aamatch/*.py` under python3.6 (tests/test_purity.py:265-286) — %-formatting only, no f-strings, 3.6 syntax.
- **test_wizard_source.py SCANNED_MODULES** already contains `setup_window.py` AND `game_window.py` (tests/test_wizard_source.py:51-55) — **adding endgame Qt code to game_window.py requires NO SCANNED_MODULES growth** (both AST scans — helper-visual calls `indicate/distance/load_cgo` + banned-matrix tokens `get_model/matrix_reset/get_object_ttt` — already cover it). Growth protocol only applies if a NEW module file is created.
- **PURE_MODULES** (tests/test_purity.py:94-98): if endgame text goes into the EXISTING `status_text.py`, no registration is needed; a NEW pure module would need (a) the PURE_MODULES list entry, (b) a registration-pin TestCase (the generator/game_state precedent, test_purity.py:289-311). Recommendation in §6 favors extending status_text.py.
- **PROSE_PIN** (tests/test_code_audit.py:64-69 + STATE.md:271): any docstring mention of banned tokens demands a deliberate pin update — endgame docstrings should refer to "the banned matrix calls" only (the wizard.py contract-5 style).
- **The `exec_()` rule** (PITFALLS.md:105, STACK.md:85): `.exec_()` is legal on QMessageBox/QFileDialog children only, never the main window — the endgame modal and the warning boxes are exactly the sanctioned class.

---

## 2. Endgame-screen design analysis + recommendation

### 2.1 The three candidate placements, evaluated

**(a) Modal child dialog — RECOMMENDED.**
- **Spec fit:** spec.md:44 "give up ... end the game at the stage to show the endgame count and message" and spec.md:58 "show a winning message and the time taken, total molecules and levels, and number of skip/give up for the user to finish the game" — the endgame report is a MOMENT (a closure message the user must see to finish the game), not a persistent surface. A modal delivers the moment.
- **Prior art (runtime-verified v1, same env):** the entire win screen is a modal QMessageBox — tmp/bioCHEMeleon/biochemeleon/gui_game.py:306-345: `msg = QtWidgets.QMessageBox(self.window())`, `setIcon(Information)`, `setWindowTitle('You win!')`, `setText(headline)`, `setInformativeText(rich text stats)`, `setWindowFlags(msg.windowFlags() | QtCore.Qt.WindowStaysOnTopHint)`, `msg.exec_()`. The `.planning` research already distilled this as the recommended pattern: FEATURES.md:38 "Proven stats-modal pattern" + SUMMARY.md:113 "win screen (delay modal ~100 ms after last `cmd.color` + refresh)". The v1 codebase carried an exec_ grep gate that allowed exactly this class (v1 AGENTS.md; gui_game.py:345 is the single allowed hit).
- **PITFALL 4 legality:** "exec_() allowed ONLY on brief child dialogs (QFileDialog, QMessageBox) — and any modal child must pause the game timer" (.planning/research/PITFALLS.md:105). At endgame the timer is STOPPED (see §5.3), so the pause obligation is vacuously met — but the stop must actually happen (§5.3 shows why the tick alone cannot stop the clock).
- **Why QMessageBox and not a custom QDialog first:** the stats are a headline + a short rich-text block — exactly `setText`/`setInformativeText` territory (v1 shipped `<b>Time:</b> %d:%02d<br><b>Hints used:</b> %d<br>...` at gui_game.py:341-343). A custom QDialog subclass in game_window.py is the fallback if the human wants a richer layout (per-level list as a real table, buttons like "Restart now?"); it is MORE code and unproven in this repo. The v1 modal proved sufficient for the identical content class.

**(b) A third tab / a state of the Game tab — REJECTED as the primary surface.**
- The Game tab already renders durable state (info box + labels); endgame lines logged there survive dismissal (good), but a tab cannot deliver the "winning message" moment (no attention capture), and the user might be on the Setup tab when the game ends (the natural end can fire from the wizard panel's Confirm button, not only from the Game tab). A third tab also churns the two-tab structure pinned by SMOKE-11 PART I1 (05-06-SUMMARY.md:73) for no spec benefit.
- **However**: the info-box log MUST still receive the endgame lines (the reserved `EVENT_KINDS` wording) — the modal is the moment, the info box is the record. Two surfaces, two roles — the same two-surface discipline recorded at 05-11 (wizard panel vs Qt tab vocabularies, 05-11-SUMMARY.md:71-78).

**(c) Wizard-panel text only — REJECTED.**
- Panel lines clip at 255 chars/line (wizard_text.py:64 `_clip`, pinned 03-02) and the panel disappears entirely the moment the wizard is popped (and the endgame sequence SHOULD pop the wizard — §2.3). A per-level score list with totals does not fit the panel's role (in-game feedback surface, 04-15 ruling STATE.md:174).

### 2.2 The ~100 ms post-scene-change modal timing pattern (the exact mechanics)

**Source of the pattern (v1, runtime-verified):** tmp/bioCHEMeleon/biochemeleon/gui_game.py:289-304:

- `_on_win(elapsed)`: (1) `self._timer.stop()` — stop the 1 Hz timer FIRST; (2) `cmd.refresh()` — "trigger a scene redraw now; 100 ms lets it land"; (3) `QtCore.QTimer.singleShot(100, lambda: self._finish_win(elapsed))`.

**Why the delay exists (v1 docstring, gui_game.py:290-299 — verbatim rationale):** "schedule the win dialog after a short delay so PyMOL redraws the 3D scene (the last `cmd.color('green')` from on_pick becomes visible) BEFORE the modal dialog blocks the Qt event loop... Deactivating in the same call as cmd.color (the previous approach) let the wizard-teardown WizardRefresh clobber the pending green redraw; separating them by 100 ms lets PyMOL render the green first." Two coupled causes:
1. A modal `exec_()` runs a nested event loop that stops PyMOL's normal redraw servicing — any scene change made immediately before the modal never paints (v1 "Bug A: the last hider never appears green").
2. The wizard teardown (pop → `cleanup()` → per-object color restore + `cmd.rebuild`, wizard.py:179-206, 217-246) is itself a burst of display-affecting calls; issuing it in the same event-loop turn as the modal risks the redraw being clobbered or deferred until after the modal.

**Repo-pinned research statements of the same pattern:** FEATURES.md:38 ("delay the modal ~100 ms after the last `cmd.color` + `cmd.refresh()` so the redraw lands before Qt blocks the event loop"); SUMMARY.md:113; ROADMAP.md:144 ("win-screen modal timing pattern (~100 ms after last `cmd.color`) applies to later endgame work"); STATE.md:264(f).

**Application to SCORE-07:** the AA-match endgame moment is preceded by the SAME class of scene changes — the final confirm/skip runs detection (no recolor, but reads the scene) and then the wizard pop fires `cleanup()`'s color restores + `cmd.rebuild` per recolored object (every hinted/selected slot changes color back). The endgame sequence therefore mirrors v1 exactly: do all state/scene work (record scores, pop the wizard, stop the 1 Hz timer, set the label, log the lines) → `cmd.refresh()` → `QTimer.singleShot(100, show-endgame-modal)`. The 100 ms figure is the v1-shipped value — keep it verbatim rather than inventing a new constant.

**Stay-on-top + parent (v1 "Bug B"):** gui_game.py:313-314, 335-344 — the modal is parented to `self.window()` (the top-level modeless window, i.e. AA-match's SetupWindow) and carries `WindowStaysOnTopHint`, "so it appears ABOVE the PyMOL OpenGL window (not hidden behind it)". Without this the win dialog landed BEHIND the viewer in v1. Both details are mandatory for the AA-match endgame modal and the warning boxes (v1 applies the same parent fix to `_confirm`, gui_game.py:132-137).

### 2.3 What happens around the modal (the endgame sequence, recommended order)

The recommendation (for the planner to task-ify; sequence responsibilities, not code):

1. **The lifecycle op** (wizard/engine, sibling stream) records the final molecule score / skip / give-up into `GameState`, computes the final elapsed `time.time() - gs.timer_anchor` ONCE at the end moment, and RETURNS the endgame summary (plain data) through the `GameWizard._guard` seam (05-08: `_guard` RETURNS the op result, wizard.py:436-449).
2. **The tab impl** (non-modal) consumes the summary: logs the pinned status_text endgame lines into the info box (handler-direct emission, the `_hint_now` precedent game_window.py:364-370), stops the 1 Hz `_timer` (v1 `_on_win` precedent), sets `_timer_label` to the exact final M:SS via `_format_mss`, and RETURNS the summary + a game-over flag.
3. **The thin wrapper** (the ONLY modal owner, the `_X_impl` law 04-09): on game-over, `cmd.refresh()` + `QTimer.singleShot(100, show)` → the modal (parent `self.window()`, `WindowStaysOnTopHint`, `exec_()`). On a guarded refusal (None) it shows nothing extra (the `_guard` box already fired).
4. **The wizard pop**: the endgame op or the window pops the GameWizard via the canonical `cmd.set_wizard()` None-pop (wizard.py:31-39 contract; the window's `_pop_game_wizard` helper setup_window.py:826-845 already encapsulates the isinstance-gated pop). Pop BEFORE the refresh+delay so the cleanup's color restores are what the redraw frame lands. `_aam_*` objects STAY (Done semantics; Cleanup is the explicit removal op) — v1 auto-cleaned its scene after the win dialog, but v1's game WAS a scene mutation of the user's object, whereas AA-match game objects are separate `_aam_*` objects the player may want to inspect; spec is silent, so keep the scene and leave Cleanup explicit (flagged as Decision candidate D6).

**Dismissal:** the QMessageBox's default OK button dismisses (`exec_()` returns); after dismissal the tab sits in the post-game state (timer stopped, log complete, required label showing its last value or `Required: -` if a poll ran — with the timer stopped no poll runs, so the label is stable). The window itself stays open (modeless singleton; re-open = reuse-and-raise).

---

## 3. Confirmation-warning design + verbatim wording proposals

### 3.1 Widget pattern (proven precedent)

**`QMessageBox.question` with explicit Yes|No buttons, parented to `self.window()`** — the v1 `_confirm` helper verbatim (gui_game.py:132-137):

> `btns = QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No`
> `return QtWidgets.QMessageBox.question(self.window(), title, text, btns) == QtWidgets.QMessageBox.Yes`

- v1 used this exact helper for its two destructive-ish actions ("Reveal one hider?", "Reveal all hiders? This ends the game." — gui_game.py:154-156, 164-166), the closest prior-art analog to Skip/Give-Up.
- `.planning/research/FEATURES.md:36` already verdicts it: "Proven `QMessageBox.question` pattern; skip stores partial score".
- Gate-legal: QMessageBox child modals are the sanctioned `.exec_()` class (PITFALLS.md:105; v1 grep gate allowed exactly QFileDialog/QMessageBox).
- The static `question()` opens an application-modal loop internally, so `QApplication.activeModalWidget()` sees it — the tick's freeze branch engages with zero new code (§5.1).
- Escape/closing the box reads as No (Qt default) — a safe accidental-dismiss semantic.

### 3.2 Who shows it and where the YES branch lives (the _X_impl mapping)

- The **thin tab wrapper** (`_on_skip` / `_on_giveup`) owns BOTH modals: gate pre-game FIRST (the `_hint_now` isinstance gate shape: no live GameWizard → silent no-op, BEFORE any box — no warning modal when no game is running, mirroring v1's controller-None guards gui_game.py:149-153), then `question()`, then on Yes `self._guard(self._skip_impl)` / `self._guard(self._giveup_impl)`.
- The **impls never own boxes** (the smoke-99 law, 04-09-SUMMARY.md:95-106: a static QMessageBox BLOCKS indefinitely under platform=offscreen; "impls must never own boxes, or T1b smokes hang"). The endgame modal's refresh+singleShot+exec_ tail also lives in the wrapper, never the impl (§7 smoke hazard).
- **Refusals after confirmation still surface**: the wrapper's `_guard` maps `(ValueError, OSError)` → warning box (game_window.py:332-343 — already ON GameTab). Note the layered guard behavior: wizard lifecycle ops that internally `_guard` (the hint pattern) return None on a house refusal and the refusal text lands on the WIZARD PANEL (`self._error`), not a Qt box — the tab then treats None as "already surfaced" (exactly the hint comment, game_window.py:366-368). The planner must CHOOSE per-op: (i) hint-style (wizard op self-guards → panel text, tab silent on None) or (ii) raise-through (wizard op re-raises → tab `_guard` boxes it). For Skip/Give-Up the ops are player-initiated lifecycle moves with few refusal paths (no game / already at boundary); recommendation: follow the hint precedent (i) for consistency, and make the ops raise EngineError only for genuinely impossible states (no live game) which the isinstance gate already prevents reaching. Flag as planner decision D7.

### 3.3 Verbatim wording proposals (WSL-pin candidates — flag for human approval)

All endgame wording belongs in pure `status_text.py` (the ONE wording home, 05-01; EVENT_KINDS says "Reserved wording/format is NOT pinned; Phase 6/7 research pins the final text", status_text.py:36-37). Score format: 2 decimals matches the existing result-lines convention (wizard_text.py:128 "Score renders with exactly 2 decimals"). Time format: `_format_mss` M:SS (game_window.py:250-255).

**Skip warning modal (title + text):**
- Title: `Skip this molecule?`
- Text: `Skip this molecule and move to the next one? Your score so far on this molecule (%.2f) will be kept.`
  - Rationale: names the consequence (partial score kept, molecule advances) per the spec semantics ("store only up to current score of the molecule, move to the next molecule", spec.md:43). Alternative shorter form: `Skip this molecule and move to the next one? The score formed so far is kept.` — the exact score number in a warning is optional; pick one at planning.

**Give Up warning modal:**
- Title: `Give up?`
- Text: `Give up and end the game now? The game ends at this stage and the endgame summary is shown.`
  - v1 analog: "Reveal all hiders? ... This ends the game." (gui_game.py:164-166) — the ends-the-game clause is the load-bearing sentence.

**Info-box event lines (reserved kinds, handler-direct emission):**
- `molecule_scored` → `Molecule %d of %d scored %.2f (total %.2f).` — spec 7.3 wants molecule score + total "til the stage" in the info box. (Candidate variant: `Score %.2f for molecule %d of %d -- total %.2f.`)
- `molecule_skipped` → `Skipped molecule %d of %d (partial score %.2f, total %.2f).`
- `gave_up` → `Game ended at level %d, molecule %d of %d (total %.2f).`
- `level_advanced` → possibly redundant with the poll's automatic `Level %d, molecule %d of %d.` line on the position change (status_text.status_events fingerprints `level_pos`, so the next 1 Hz tick already announces the new level). Recommendation: do NOT emit a separate level_advanced log line for normal advances; reserve the kind for documentation only unless the human wants an explicit banner. Flag as D8.
- `game_reset` / `game_restarted` → sibling stream's wording (SCORE-09/10); only noted here because they share the same emission mechanism.

All of the above are PROPOSALS — the human approves final strings at planning (the 05-01 precedent pinned strings via WSL tests only after research proposals were accepted).

---

## 4. Skip/Give-Up control-widget recommendation

**Current inventory:** the GameTab button row has ONLY `btn_hint` + a stretch (game_window.py:118-126). **There is NO skip/give-up control today** — verified against the whole file.

**Spec wording:** "Skip Mol/give up dropdown button" (spec.md:42) — one control offering two actions.

**Candidates:**

| Candidate | Assessment |
|---|---|
| **(a) QToolButton + QMenu (RECOMMENDED)** | The literal "dropdown button": `QToolButton` with `setMenu(...)`, popup mode `InstantPopup` (whole button opens the menu) or `MenuButtonPopup`; two QActions 'Skip Molecule' / 'Give Up...' connected to the wrappers. Standard Qt 5 (PyQt5 5.12.3 recorded env, STATE.md:63). Headless-provable: constructing a QToolButton + QMenu + QActions under offscreen is plain widget construction (04-01 probe class), and `QAction.trigger()` drives the connected slot WITHOUT opening a popup — so the T1b smoke can drive both actions headlessly (unlike a real popup, which needs a mouse). Untested in THIS repo — the smoke proves it. |
| (b) QComboBox with placeholder (v1-proven fallback) | v1's `_found_mgmt_combo` pattern (gui_game.py:66-74, 106, 198-205): index-0 placeholder item, `activated` signal (NOT currentIndexChanged — placeholder must not fire on construction), reset to index 0 after handling so the same action can be re-picked. This is the only dropdown pattern ALREADY shipped in the prior art. Con: looks like a text field, not a button; the reset-to-placeholder dance is extra state. |
| (c) Two separate buttons | Simplest, but contradicts the spec's explicit "dropdown button" wording. Rejected unless the human overrides the spec wording (D5). |

**Recommendation:** (a), with (b) as the documented fallback. Rationale: spec-literal, `Give Up` being destructive argues for it being a deliberate menu choice rather than an always-visible peer of Skip, and QAction.trigger() keeps the T1b tier intact. Give the 'Give Up' action a tooltip carrying the warning semantics ("Ends the game at the current stage — asks for confirmation."), consistent with the house tooltip standard (spec.md:87 "clear but sufficient in-game explanation"; every existing widget is tooltipped).

**Row layout consequence:** the reserved stretch (game_window.py:124) exists precisely so added buttons never reflow the timer row (05-06 "research OQ-1 later-add recommendation"). The Phase-6 row becomes Hint + Confirm (sibling stream) + Skip/Give-Up dropdown + Restart + Reset (+ Save/Import in Phase 7) before the stretch. Construction order and tooltips are pinned by the plan; SMOKE-11 PART I2's fresh-GameTab placeholder pin ('0:00' / 'Required: -', STATE.md:189) must keep passing (new buttons don't touch those labels).

---

## 5. Modal/timer interplay mechanics (exact predecessor patterns)

### 5.1 During the Skip/Give-Up warning modals: NO new pause code is needed

The pause mechanism ALREADY ships and covers ANY modal child:

- game_window.py:276-283 — every 1 Hz tick: `if QtWidgets.QApplication.activeModalWidget() is not None:` → `engine._current_game().rebase_timer(time.time(), self._last_shown_elapsed)` → `return` (label not updated → the clock freezes at the last shown second; the status poll is skipped too).
- The mechanism's contract: "The CALLER (the 1 Hz tick) owns modal detection" (game_state.py:207-209) — and P-8: "timers fire THROUGH nested event loops, so the tick is designed to run while a modal child is open" (game_window.py:57-59). The tick keeps firing inside the modal's nested loop and rebases every second.
- Granularity ≤ 1 s over-count at the modal-open edge, documented and accepted (game_window.py:61-66; 05-11 human-confirmed the freeze under a REAL modal file dialog: "timer FREEZES under the modal file dialog (P-5...)" — 05-11-SUMMARY.md:66).
- **Consequence for the wrappers:** they must NOT call `rebase_timer` themselves (that would be a second modal-detector, violating the caller-owns-detection law); they only need the modals to be REAL modals (static QMessageBox question/warning are). The `[HUMAN]` checkpoint re-verifies the freeze under the NEW warning modals (same mechanism, new dialog class).

### 5.2 The `_X_impl` law applied to modals (binding, with the exact receipt)

- 04-09-SUMMARY.md:26-27 + 95-106: "clicked signal → thin MODAL wrapper (_on_X) → NON-MODAL _X_impl that headless smokes drive directly. The smoke-99 probe receipt: a static QMessageBox BLOCKS INDEFINITELY under platform=offscreen (modal event loop nothing closes; 'after box' never printed within a 60s timeout)."
- Wrapper-owns-boxes examples to mirror: setup_window.py:685-700 (`_on_save_setup` = QFileDialog + `_guard` + success `QMessageBox.information` gated on the impl's return) vs the impl returning data (setup_window.py:702-719).
- For Phase 6 this law extends to the endgame modal's SCHEDULING: `cmd.refresh()` + `QTimer.singleShot(100, ...)` + `exec_()` belong in the WRAPPER. If the singleShot lived in the impl, a smoke's event-loop pump (processEvents) inside the 100 ms window would fire the modal and hang the smoke — the same failure class as smoke-99, one indirection later.

### 5.3 At game end: the timer must be STOPPED explicitly — the tick cannot do it

**The trap:** `_compute_elapsed` reads the LIVE `engine._current_game().timer_anchor` (game_window.py:244-248). At endgame the engine's GameState REMAINS LIVE — `engine._game` is only replaced by the next `new_game` (engine.py:292-295); the wizard pop and `cleanup_game_objects` do NOT clear it. If the 1 Hz `_timer` kept running after game end, the label would keep ADVANCING forever over a finished game ("stop the timer and get the time", spec.md:57, would be false).

**The proven fix (v1 `_on_win` first line):** `self._timer.stop()` (gui_game.py:301). The tab stops its 1 Hz render loop at the endgame moment; the label then holds whatever it was last set to — so the impl must ALSO set `_timer_label` to the EXACT final elapsed captured by the lifecycle op (`_format_mss(final_elapsed)`), rather than trusting the ≤1 s-stale last tick. Two agreeing surfaces (label + endgame modal) from one captured value.

**Why not rebase_timer to "stop" the anchor:** `rebase_timer(now, elapsed)` sets `anchor = now - elapsed` (game_state.py:217-224) — the anchor still lives in wall-clock time, so `time.time() - anchor` keeps growing on every later computation. A rebase freezes the clock only WHILE the tick keeps rebasing each second; remove the tick and the clock resumes from the rebased anchor. There is no "frozen forever" anchor value. (A `final_elapsed` field on GameState WOULD be a pure-layer "stopped time" home — see §6.3 for the tradeoff.)

**Restart hygiene:** `_begin_play` already restarts the tick defensively (`self._timer.stop(); self._timer.start(1000)`, game_window.py:220-221) and re-seeds `_last_status` — so a post-endgame Restart self-heals the stopped tick, the label, and the baseline. Also note the 05-06 smoke lesson: restore blocks MUST stop the 1 Hz timer before scene cleanup, or a pumped tick raises EngineError inside a timer callback (05-06-SUMMARY.md:112-118) — Phase-6 smokes inherit that restore discipline.

### 5.4 Pre-game / mid-countdown gating

The wrappers gate on a live GameWizard BEFORE any box (the `_hint_now` isinstance gate, game_window.py:359-363). Pre-GO the countdown window is wizard-free by construction (P-1), so a Skip/Give-Up press during the countdown is a silent no-op — no modal over a wizard-free game. Mid-countdown Cleanup already cancels the countdown first (P-2, setup_window.py:875).

---

## 6. Endgame data contract + pure-formatter proposal

### 6.1 Data available at game end (all plain data, no new engine reads needed)

| Needed for SCORE-07 | Source | Note |
|---|---|---|
| Per-level scores | slice the flat `molecule_scores` by walking `payload['levels'][i]['molecules']` lengths (record order == play order L0M0, L0M1, L1M0, ... — PROVIDED one-record-per-molecule holds, §6.2) | game_state.py:149-152, 171; payload shape level_spec.py:15-35 |
| Total score | `GameState.total_score` property | game_state.py:182-185 |
| Stopped time | final elapsed captured ONCE by the lifecycle op: `time.time() - gs.timer_anchor` at the end moment | rendered via `_format_mss` (game_window.py:250-255) |
| Total molecules | `sum(len(l['molecules']) for l in payload['levels'])` (game size) — OR `len(molecule_scores)` (molecules actually finished/skipped). AMBIGUOUS in spec.md:58 "total molecules and levels" → Decision candidate D2 | |
| Levels | `len(payload['levels'])` and/or reached `current_level_index + 1` | level_spec.py:20-33 |
| Skips / Give-ups | `skip_count` / `giveup_count` | game_state.py:152-153, 172-173 |
| Ended-at stage | `current_level_index`, `current_molecule_index` | game_state.py:147-148, 169-170 |
| Ended how | the op's own branch (natural final confirm vs give_up) — drives differentiated wording (D1) | |

### 6.2 Two hazards the data contract MUST close (evidence-backed)

1. **Re-Confirm double-append** — `record_molecule_result` appends unconditionally (game_state.py:245) and wizard.py:552-553 explicitly defers the fix to Phase 6: "repeated Confirm appends to the engine GameState's molecule_scores — score-history semantics are Phase 6's lifecycle". A double append (a) inflates `total_score`, (b) breaks the flat-list→level slicing that the per-level endgame summary relies on. The lifecycle must guarantee ONE record per molecule (refuse re-confirm after scoring, or overwrite the molecule's entry — sibling stream decides; this stream's contract is: the summary formatter may ASSUME one record per molecule only if the lifecycle enforces it; the pure formatter should fail-closed if the slice lengths mismatch).
2. **Grouping integrity** — the pure formatter should derive per-level grouping from the payload's molecule counts + the flat list and REFUSE (ValueError, fail-closed house style) when `len(molecule_scores)` ≠ the expected count for the reached stage. Silent mis-grouping would print a wrong scoreboard.

### 6.3 Pure-formatter home: extend `status_text.py` (recommended) vs a new module

- **Recommendation: extend aamatch/status_text.py** — it is already the tab's pure text surface (05-01), already in PURE_MODULES (no registration churn), already imports only `.wizard_text` (status_text.py:40), and the EVENT_KINDS reserve explicitly awaits Phase-6 pins there (status_text.py:35-37). New pure functions (plain-data-in → list-of-lines-out, fail-closed ValueErrors) for: (i) the endgame summary block (per-level lines + total + time + counts + headline), (ii) the warning-modal strings and the event lines of §3.3. Zero new stdlib imports needed.
- A new `endgame_text.py` would buy nothing and cost a PURE_MODULES entry + registration-pin test (test_purity.py:289-311 pattern). Only choose it if the planner wants the endgame surface isolated (defensible, not recommended).
- **The summary FUNCTION should take the endgame snapshot as plain data** (payload levels structure + game_state_dict from `engine.game_status()`/`GameState.to_dict()` + captured elapsed + ended-reason) so WSL tests pin everything without PyMOL (the 05-01 method: "every string it can show is pinned here in WSL before any Qt wiring exists", status_text.py:14-17).
- **Optional pure-layer alternative for "stopped time":** add a `final_elapsed` field to GameState (set by the endgame op; `to_dict`/`from_dict` must round-trip it ADDITIVELY — `from_dict` currently indexes every key with `data['...']` (game_state.py:266-276), so an older saved dict would KeyError unless `.get(default)` is used — the two-version-gate law says accept-older with `.get` defaults on read, AGENTS.md gate 4). Only worth it if Phase 7 must reconstruct a FINISHED game's stopped clock from a checkpoint; otherwise the tab-side capture suffices. Flag as D9 (coordinate with the Phase-7 stream).

### 6.4 What the 1 Hz poll needs from Phase 6 (answer: nothing new, by design)

- `status_events` deliberately does NOT fingerprint `result` (status_text.py:33-34, 152-154 — "score lines are reserved for Phase 6 (pitfall 7)"). The recommendation is to KEEP it unfingerprinted and emit score/skip/give-up lines handler-direct from the ops' returned data (the `_hint_now` precedent, game_window.py:364-370) — instant and ordered right after the action (the same rationale that gave `_begin_play` the first status content), with totals the poll could not compute anyway.
- The poll KEEPS handling: the level/molecule line after any advance (it fingerprints `level_pos`/`molecule_pos` — the next tick after a skip/advance announces the new position automatically), and the no-wizard reset (`Required: -`) once the endgame pop removes the wizard (game_window.py:315-319) — though with the timer stopped that reset never fires; harmless either way since `_begin_play` re-seeds on Restart.
- `gave_up`'s info-box line is therefore handler-emitted, NOT poll-emitted (the wizard is gone by the time any poll could see the change — there is nothing to diff against).

---

## 7. T1b smoke strategy + [HUMAN] checkpoint items

### 7.1 What is provable headlessly (consistent with SMOKE-11 PART letters + SMOKE-14 T1b)

**WSL (not even a smoke) — pure first:**
- The endgame-summary/warning/status_text battery: per-level slicing happy path, mismatch fail-closed, elapsed M:SS formatting, 0-skip/0-giveup rendering, differentiated end-vs-gave-up wording, warning-text determinism. TDD RED→GREEN per house style; extends tests/test_status_text.py (no new registration).

**SMOKE (new PARTs on smoke_11_window.py, or a new smoke_15 — planner's call; SMOKE-11 is the window/tab home, already PARTs A-K):**
- **ALWAYS/T1a part** (no Qt): the lifecycle chain through the cmd tier — `start_game` → scripted place → confirm-style op → assert `molecule_scores`/`skip_count`/advance; the give-up op → assert pop + counters + captured elapsed (SMOKE-08-shaped drive; the sibling stream owns the exact ops, this smoke proves the seam returns the summary data).
- **T1b part** (probe-gated on the 04-01 verdict, `QT_QPA_PLATFORM=offscreen` before the pymol.Qt import, QApplication reuse-or-create — the 04-05 recipe, STATE.md:153):
  - GameTab construction: the new dropdown control exists with the two actions; tooltips set; the timer-row layout intact (PART I2 placeholder pin re-green).
  - Drive the skip/give-up IMPLS DIRECTLY (never the wrappers — zero modals, the smoke-99 law): assert wizard-op effects (molecule advanced / game ended), the info-box lines appended (pinned wording), `skip_count`/`giveup_count`, the 1 Hz `_timer` STOPPED at game end, `_timer_label` holding the exact final M:SS.
  - Drive the endgame-summary assembly from a real finished game and assert the returned plain data (per-level scores, total, counts) — the data the wrapper would render.
  - Restore block: cancel countdown + stop the 1 Hz timer + pop wizard + cleanup (the 05-06 deviation-2 discipline) before the scene-restore asserts.
- **The modal tails are NEVER driven headlessly**: `question()`, the refresh+singleShot+exec_ endgame tail live in wrappers; smokes never call wrappers. If a future smoke needs the wrapper's non-modal prefix, split it (`_on_X` = gate + box + `_guarded_X`; keep the modal scheduling in `_on_X` only).

### 7.2 [HUMAN] checkpoint items (the not-headlessly-provable set)

1. Skip warning: modal look/text, Yes advances (partial score kept, next molecule appears), No resumes play, **timer freeze under the warning modal** (P-5 class — new dialog instance of the already-confirmed mechanism).
2. Give Up warning + endgame screen: modal text, Yes → endgame screen appears ~100 ms after the scene settles, **stays ON TOP of the OpenGL viewer** (the v1 Bug-B fix), stats legible and correct.
3. Natural end: playing the final molecule of the final level shows the SAME endgame screen with winning-message wording (vs give-up wording — D1).
4. Stopped timer: after the endgame, the label holds the final time and does not advance while the window stays open.
5. Post-endgame state: scene retained for inspection, wizard panel gone (msm/colors restored), Restart works from the endgame state (fresh countdown from 0:00), Cleanup still available.
6. Dropdown control feel (QToolButton menu vs combobox — whichever D5 picks).

---

## 8. Decision candidates for the human

| # | Decision | Options + recommendation |
|---|---|---|
| D1 | Winning-message wording: is a give-up-ended game still "You win"? | Spec: natural end = "a winning message" (spec.md:58); give-up = "show the endgame count and message" (spec.md:44) — differentiated wording is defensible. Propose: natural end headline `You win!` + "You finished all %d level(s) in %d:%02d."; give-up headline `Game over` + "You gave up at level %d, molecule %d of %d." Flag: human picks/edits the exact strings. |
| D2 | "Total molecules and levels" meaning | Game size (all molecules/levels the game contained) vs molecules actually completed. Recommend game size for molecules ("Molecules: %d of %d completed" resolves both readings in one line) + `Levels: %d`. Human confirms. |
| D3 | Per-level score aggregation | Sum of the level's molecule scores (consistent with `total_score` = sum, game_state.py:182-185) vs average. Recommend SUM. Human confirms. |
| D4 | Endgame screen widget | QMessageBox with rich informative text (v1-proven, recommended) vs custom QDialog. Human confirms the simpler form suffices. |
| D5 | Skip/Give-Up control widget | QToolButton+QMenu (recommended, spec-literal) vs v1-proven QComboBox placeholder vs two buttons. |
| D6 | Post-endgame scene policy | Keep `_aam_*` objects for inspection (recommended; Cleanup/Restart explicit) vs v1-style auto-cleanup after the dialog. Spec silent. |
| D7 | Refusal surfacing for lifecycle ops | Hint-style: wizard op self-guards → panel `_error`, tab silent on None (recommended, consistent) vs raise-through to the tab's `_guard` box. |
| D8 | Explicit `level_advanced` log line | Redundant with the poll's automatic level line (recommend NO extra line; the EVENT_KINDS entry stays documentation-only) vs an explicit banner line. |
| D9 | Pure-layer "stopped time" home | Tab-side capture only (recommended now) vs a `final_elapsed` GameState field with additive `.get` from_dict (needed only if Phase 7 must reconstruct a finished game's clock). Coordinate with the Phase-7 research stream. |
| D10 | Skip-with-zero-score behavior | Skipping a molecule with nothing formed stores 0.00 and advances (v1 mercy pattern — no refusal) vs refusing a pointless skip. Recommend allow (fairness; the warning already shows the kept score). |

---

## Sources

### Primary (HIGH — shipped repo code, runtime-verified in this project's env)
- aamatch/game_window.py (whole file) — GameTab shell, tick/modal-pause (:276-283), `_format_mss` (:250-255), `_guard` (:332-343), hint seam (:345-371)
- aamatch/setup_window.py — two-tab structure (:241-258), `_guard` (:638-648), wrapper/impl split (:685-719), `_pop_game_wizard` (:826-845), `_start_impl` (:953-1027)
- aamatch/game_state.py — fields/scoring/rebase (:141-277); aamatch/engine.py — confirm/game_status (:443-478); aamatch/wizard.py — `_guard` seam (:436-449), confirm caveat (:544-553), lifecycle (:31-39, 154-206)
- aamatch/status_text.py — EVENT_KINDS reserve (:49-75), diff rules (:143-179); aamatch/wizard_text.py — result lines + 2-decimal law (:106-175), `_clip` (:64)
- aamatch/gamestart.py — `_last_start` (:167-178), `activate_game` (:323-339); aamatch/level_spec.py — payload shape (:9-35)
- tmp/bioCHEMeleon/biochemeleon/gui_game.py — `_confirm` (:132-137), `_on_win` (:289-304), `_finish_win` (:306-357), debrief (:384-414), combo placeholder pattern (:66-74, 198-205) — the v1 win-screen/warning prior art, runtime-verified
- tests/test_purity.py (:94-98, 265-311), tests/test_wizard_source.py (:51-55), tests/test_code_audit.py (:64-69), smoke/run_smoke.sh

### Secondary (HIGH — phase summaries and planning laws)
- .planning/phases/04-qt-setup-window/04-09-SUMMARY.md (smoke-99 receipt + _X_impl law)
- .planning/phases/05-game-status-tab-start-sequence/05-04/05-06/05-09/05-10/05-11-SUMMARY.md (rebase contract, GameTab laws, deferred start, poll-diff, human verdicts incl. timer freeze)
- .planning/research/FEATURES.md:36-38 · PITFALLS.md:105, 448-456 · ARCHITECTURE.md:175-192, 354 · SUMMARY.md:113 · ROADMAP.md:136-171 · STATE.md:162-193, 264-271 · REQUIREMENTS.md SCORE-05/06/07 · spec.md:35-58

### Confidence notes
- Qt API behaviors (QMessageBox.question/exec_, WindowStaysOnTopHint, activeModalWidget, QTimer.singleShot) are HIGH by the repo's own hierarchy: runtime-verified in the shipped v1 plugin under the SAME PyMOL 2.5.0 / PyQt5 5.12.3 / Qt 5.12.9 build (STATE.md:63 records the env versions). No external web verification was needed or performed; Context7 was not available in this session's toolset — the v1 source IS the authoritative in-repo reference.
- LOW/flagged items: the exact verbatim strings (proposals pending human approval, §3.3/D1) and the QToolButton+QMenu offscreen drive (standard Qt, but unproven in this repo until the T1b part runs).

**Research date:** 2026-09-20
**Valid until:** stable — all claims are anchored to committed code and completed phase records; re-verify only if Phase 6's sibling stream changes the lifecycle-op seam shapes.

## RESEARCH COMPLETE
