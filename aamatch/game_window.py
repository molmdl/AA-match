"""aamatch.game_window -- the Game status tab (Phase 5, plan 05-06).

Layer: QT TIER. Module-level ``from pymol.Qt import ...`` is legal and
REQUIRED here (the class definition needs QtWidgets at class-creation
time); stdlib ``time`` is legal. This module must NEVER be added to
``PURE_MODULES`` in ``tests/test_purity.py`` and is NEVER imported by
WSL tests -- it is covered by the AST source gates only (Gate D still
compiles it under the 3.6 syntax floor), and both
``tests/test_wizard_source.py`` scans (banned helper-visual call
sites + zero banned-matrix-token prose mentions) cover it via
SCANNED_MODULES. Qt comes ONLY through the pymol.Qt wrapper shim --
the vendor binding is never imported directly (the shim-only law).

ROLE: the 'Game status' page of the modeless setup window (SETUP-11 /
SCORE-04 -- spec.md:33 "the Game status tab of the same window", the
timer + required line + rolling info box of spec.md:36-40). GameTab
ships the status-surface SHELL: the read-only rolling info box, the
elapsed-timer label OUTSIDE the box, the required-interactions label,
the cancellable 3-2-1 countdown, and the 1 Hz tick that renders from
the live GameState timer anchor. The Hint button is CONNECTED (05-08
landed its handler on this exact skeleton -- the 04-05 shell law: the
handler plan connects its own button): isinstance-gated dispatch to
the live GameWizard's capability hint, SILENT no-op before GO (no
game wizard on the stack yet). The status POLL (05-10) rides the
same 1 Hz tick: ``_on_tick`` calls ``_refresh_status`` AFTER the
timer-label half; the poll reads ONLY the live GameWizard's public
``get_status()`` behind a lazy-import isinstance gate and diffs
through the pure ``status_text.status_events``, so the tab stays a
dumb renderer (event log only: no wizard-panel mirroring, no
movement lines, no timestamps, no score lines). ``_begin_play``
owns the FIRST level line + first required label (instant, ordered
right after 'GO!') and seeds ``_last_status`` so the poll's first
observation is silent. Phase 6 (06-07) lands the tab's lifecycle
CONTROLS: the Confirm button (spec.md:41) and the Skip/Give-Up
dropdown (spec.md:42) with the spec-required confirmation warnings,
both factored as thin MODAL wrapper -> NON-MODAL impl (the 04-09
_X_impl law -- impls never own boxes, so headless smokes drive them
directly), the impls dispatching to the live GameWizard's lifecycle
ops behind the SAME isinstance gate and running the poll-diff
SYNCHRONOUSLY right after the op so the event lines land with ZERO
poll latency (no 1 Hz loss). A completed/given-up game runs
``_endgame_sequence``: stop the 1 Hz timer (v1 _on_win precedent --
the tick cannot stop the clock), pin the timer label to the EXACT
final elapsed, and pop the wizard via the local ``_pop_game_wizard``
 helper (the setup_window.py:826 seam shape). The poll owns ONE
 logging home for the game_over transition (tab-triggered ends via
 the sync refresh, panel-triggered ends via the 1 Hz tick -- the
 transition fires once). Plan 06-08 lands the restart/reset half:
 Restart replays the stored ``gamestart._last_start`` INPUT tuple
 verbatim through the 05-09 deferred start sequence (pop ->
 start_game(activate=False) -> countdown; the pinned 'Game
 restarted.' line logs AFTER the arm so the countdown's box clear
 cannot wipe it -- restart-reset D7), fail-closed with a clear
 refusal when nothing was ever started (house fail-closed). Reset
 routes through the wizard's PUBLIC grid-replay op behind the SAME
 isinstance gate (PITFALL 6 at the widget layer -- never the
 engine's replay direct), the game_reset marker carrying the pinned
 reset line through the SYNCHRONOUS poll while the timer keeps
 running and NO GameState is touched (positions only; rotations
 persist). Plan 06-09 lands the endgame MODAL (SCORE-07's winning
 message): the wrappers capture the guarded result and, on a truthy
 ``game_over``, run ``cmd.refresh()`` + ``QtCore.QTimer.singleShot``
 (the v1 _on_win mechanics -- the pop's color-restore burst paints
 BEFORE the modal's exec_() blocks the event loop; the 100 ms figure
 is the v1-shipped constant, no new constant) to schedule
 ``_show_endgame_modal(summary)`` -- a child QMessageBox (parent
 ``self.window()`` + WindowStaysOnTopHint, the v1 Bug-B fix) whose
 headline + rich-text stats are EXACTLY the pure
 ``status_text.endgame_lines`` block the info box also carries (two
 surfaces, one wording home: the modal is the MOMENT, the info box
 is the RECORD). The scheduling lives in the WRAPPERS ONLY (the
 smoke-99 law -- impls and the tick never own boxes, so headless
    smokes drive the impls and never fire the tail). Plan 07-06 lands
    the Save button (SCORE-08): a gate-first wrapper (silent no-op
    pre-GO/no-game/post-endgame, pre-dialog elapsed capture, the
    '.aamz' default+auto-append, NO success box -- the info-box 'Game
    saved to <path>.' line IS the feedback) driving the box-free
    ``_save_game_to(path, elapsed)`` impl over the 07-04 gamestart
    capture/save seams. Plan 07-07 lands the Import button
    (PERSIST-02, spec.md:39): a GATE-FREE wrapper (Import is legal
    with NO game live -- it CREATES one; NO confirmation warning
    mid-game, the Start/Restart replacement semantics) driving the
    refusal-first, box-free ``_import_game_from(path)`` impl -- parse
    + gates BEFORE any scene touch (a foreign/corrupt file leaves the
    session untouched), then cancel (P-2) -> pop (P-3) -> the 07-05
    payload-direct ``gamestart.start_game_from_payload`` seam (the
    EMBEDDED payload is the truth -- never regenerated) -> countdown
    -> the 'Game imported: <path>.' line logged AFTER the arm (the
    restart D7 law).

LAWS this module enforces (05-RESEARCH-window-start-timer.md):

- P-1: the countdown runs with NO wizard on the stack --
  ``start_countdown`` only STORES the prepared wizard in
  ``_pending_wizard``; ``_begin_play`` (GO) is the single point where
  ``gamestart.activate_game`` pushes it ("countdown ... then start the
  game", spec.md:34). No pre-GO picks/moves/confirms are possible.
- P-2: the countdown is CANCELLABLE -- a reusable member QTimer steps
  the cadence (never a singleShot chain, which cannot be cancelled:
  v1's chain leaked a stale GO activation after Cleanup/double-Start,
  the recorded v1 latent bug). Every new ``start_countdown`` cancels
  any pending countdown FIRST (self-healing), and the window's cleanup
  handler cancels too.
- P-4: ONE anchor -- the 1 Hz tick computes elapsed from the LIVE
  ``GameState.timer_anchor`` on every tick (never a GUI-side clock
  copy; v1's dual-anchor produced a real drift bug). Pause = rebase
  the one anchor in place (plan 05-04's pure op), never a second
  clock.
- P-6: NO modal boxes anywhere in the tick/countdown paths -- a modal
  box inside a timer callback re-enters a modal loop, and a static box
  under platform=offscreen blocks a headless smoke indefinitely (the
  04-09 smoke-99 receipt). Failures surface via handler wrappers only.
- P-8: timers fire THROUGH nested event loops, so the tick is designed
  to run while a modal child is open (the rebase freeze below) instead
  of assuming a modal suspends it.

Timer-fairness pause (ROADMAP Phase-5 rule): while
``QApplication.activeModalWidget()`` is not None the tick REBASES the
anchor via ``game_state.rebase_timer`` so the clock freezes at the
last shown second. Granularity: <= 1 s over-count at the modal-open
edge -- documented coarse, and acceptable for a game clock (research
Q5/Q6 recommendation).

House rules: python-3.6 syntax floor, %-formatting only, no f-strings;
lazy relative sibling imports INSIDE methods (the module-identity law,
setup_window.py's contract 4).
"""

import time

from pymol.Qt import QtWidgets, QtCore


class GameTab(QtWidgets.QWidget):
    """The Game status page: timer + required label + info box + Hint.

    Layout (spec.md:36-40): a top row with the elapsed-timer label and
    the required-interactions reference label, the read-only rolling
     info     box with stretch below, and the Hint button row at the
     bottom. Button inventory (Phase 6, plans 06-07/06-08): 'Hint'
     (05-08), 'Confirm' (spec.md:41), the 'Skip / Give Up'
     QToolButton+QMenu dropdown (spec.md:42) with 'Skip Molecule' /
     'Give Up...' actions, 'Restart' (06-08, SCORE-09), and 'Reset'
         (06-08, SCORE-10 -- attribute ``btn_reset_grid``, DISTINCT from
         the Setup tab's game-setup ``btn_reset`` per the restart-reset
         D7 naming law), 'Save' (07-06, SCORE-08 -- checkpoint the
         running game to an .aamz archive; wrapper+impl factored per the
         04-09 _X_impl law), and 'Import' (07-07, PERSIST-02 -- start a
         game from an exported .aamatch.json game file; attribute
         ``btn_import`` bare, no naming collision anywhere per the D7
         logic that left ``btn_restart`` bare). The button row keeps
         its stretch LAST (insertions go BEFORE the stretch) so a
         new button never reflows the timer row.
         """

    def __init__(self, parent=None):
        super(GameTab, self).__init__(parent)
        layout = QtWidgets.QVBoxLayout(self)

        # Top row: the elapsed timer OUTSIDE the info box (spec.md:37)
        # + the required-interactions reference label (the prior-art
        # 'Remaining: -' label-row shape). Initial values are the
        # no-game values; the timer starts counting at GO.
        top_row = QtWidgets.QHBoxLayout()
        self._timer_label = QtWidgets.QLabel('0:00', self)
        self._timer_label.setToolTip('Time since the game started.')
        top_row.addWidget(self._timer_label)
        self._required_label = QtWidgets.QLabel('Required: -', self)
        self._required_label.setToolTip(
            'The interactions the current molecule requires.')
        top_row.addWidget(self._required_label, 1)
        layout.addLayout(top_row)

        # The generic rolling info box (the prior-art shape: read-only,
        # append log, no timestamps -- the timer label carries time).
        self._info_log = QtWidgets.QTextEdit(self)
        self._info_log.setReadOnly(True)
        self._info_log.setToolTip('What happened, in order.')
        layout.addWidget(self._info_log, 1)

        # Hint button (05-08: CONNECTED by its handler plan -- the
        # 04-05 shell law, verbatim). The stretch reserves the
        # remaining game-lifecycle button slots for later phases.
        btn_row = QtWidgets.QHBoxLayout()
        self.btn_hint = QtWidgets.QPushButton('Hint', self)
        self.btn_hint.setToolTip(
            'Highlight the amino acids that could still form a '
            'required interaction (carbon recolor only).')
        btn_row.addWidget(self.btn_hint)
        btn_row.addStretch(1)
        # Confirm button (06-07, SCORE-01/03 UI -- spec.md:41): the
        # tab's lifecycle-op button, connected HERE by its handler plan
        # (the 04-05 shell law). The stretch stays LAST in the row --
        # every new button inserts BEFORE it via
        # insertWidget(btn_row.count() - 1, ...) so the timer row never
        # reflows (the 05-06 OQ-1 design).
        self.btn_confirm = QtWidgets.QPushButton('Confirm', self)
        self.btn_confirm.setToolTip(
            'Finish this molecule: run detection, score it, and '
            'advance.')
        btn_row.insertWidget(btn_row.count() - 1, self.btn_confirm)
        # Skip/Give-Up dropdown (06-07, SCORE-05/06 UI -- spec.md:42's
        # 'Skip Mol/give up dropdown button'): ONE QToolButton with a
        # QMenu of two actions, InstantPopup so the whole button opens
        # the menu (the endgame-ui sec 4 recommendation -- spec-literal
        # and QAction.trigger()-driveable headlessly, unlike a real
        # popup). BOTH actions ask the spec-required confirmation
        # warning in their wrappers (endgame-ui sec 3). Inserted
        # BEFORE the stretch, which stays LAST.
        self.btn_skip_menu = QtWidgets.QToolButton(self)
        self.btn_skip_menu.setText('Skip / Give Up')
        self.btn_skip_menu.setToolTip(
            'Skip the current molecule or give up the game (both ask '
            'for confirmation).')
        self.btn_skip_menu.setPopupMode(QtWidgets.QToolButton.InstantPopup)
        menu = QtWidgets.QMenu(self.btn_skip_menu)
        self.act_skip = menu.addAction('Skip Molecule')
        self.act_skip.setToolTip(
            'Store the partial score and move to the next molecule '
            '(asks for confirmation).')
        self.act_giveup = menu.addAction('Give Up...')
        self.act_giveup.setToolTip(
            'Ends the game at the current stage -- asks for '
            'confirmation.')
        self.btn_skip_menu.setMenu(menu)
        btn_row.insertWidget(btn_row.count() - 1, self.btn_skip_menu)
        # Restart button (06-08, SCORE-09): verbatim replay of the
        # stored initial-state INPUT tuple through the deferred start
        # sequence (pop -> start_game -> countdown). NO confirmation
        # warning (spec.md:43-45 requires warnings for Skip/Give Up
        # only -- restart-reset D9).
        self.btn_restart = QtWidgets.QPushButton('Restart', self)
        self.btn_restart.setToolTip(
            'Replay the stored initial state into a fresh game '
            '(countdown, timer from zero, scores cleared).')
        btn_row.insertWidget(btn_row.count() - 1, self.btn_restart)
        # Reset button (06-08, SCORE-10): position-only grid replay
        # through the wizard's PUBLIC op behind the isinstance gate
        # (PITFALL 6 at the widget layer). Attribute name
        # btn_reset_grid -- DISTINCT from the Setup tab's game-setup
        # btn_reset (the restart-reset D7 naming law).
        self.btn_reset_grid = QtWidgets.QPushButton('Reset', self)
        self.btn_reset_grid.setToolTip(
            'Place all amino acids back to their grid positions; '
            'orientations are kept.')
        btn_row.insertWidget(btn_row.count() - 1, self.btn_reset_grid)
        # Save button (07-06, SCORE-08): one-click .aamz checkpoint of
        # the running game (PyMOL session + game state) through the
        # 07-04 gamestart seams. Inserted BEFORE the stretch, which
        # stays LAST (the 05-06 OQ-1 no-reflow law; this is the slot
        # the class docstring reserved for Phase 7).
        self.btn_save_game = QtWidgets.QPushButton('Save', self)
        self.btn_save_game.setToolTip(
            'Save the running game (PyMOL session + game state) to a '
            'checkpoint file.')
        btn_row.insertWidget(btn_row.count() - 1, self.btn_save_game)
        # Import button (07-07, PERSIST-02 -- spec.md:39): start a game
        # from an exported .aamatch.json game file (the 04-12 export's
        # EXACT filter). Bare attribute -- no naming collision anywhere
        # (the D7 logic that left btn_restart bare). Inserted BEFORE
        # the stretch, which stays LAST.
        self.btn_import = QtWidgets.QPushButton('Import', self)
        self.btn_import.setToolTip(
            'Load a game file exported by Generate and export and '
            'start playing it.')
        btn_row.insertWidget(btn_row.count() - 1, self.btn_import)
        layout.addLayout(btn_row)
        self.btn_hint.clicked.connect(self._on_hint)
        self.btn_confirm.clicked.connect(self._on_confirm)
        self.act_skip.triggered.connect(self._on_skip)
        self.act_giveup.triggered.connect(self._on_giveup)
        self.btn_restart.clicked.connect(self._on_restart)
        self.btn_reset_grid.clicked.connect(self._on_reset_grid)
        self.btn_save_game.clicked.connect(self._on_save_game)
        self.btn_import.clicked.connect(self._on_import)

        # The CANCELLABLE countdown: a reusable member QTimer stepping
        # 3 -> 2 -> 1 -> GO (P-2). Constructed here; started only by
        # start_countdown; stop() cancels (probe-proven, SMOKE-13).
        self._countdown_timer = QtCore.QTimer(self)
        self._countdown_timer.timeout.connect(self._countdown_tick)
        self._countdown_n = 0
        self._pending_wizard = None

        # The 1 Hz elapsed render loop (the prior-art 1 Hz QTimer
        # shape); NOT started until _begin_play (GO).
        self._timer = QtCore.QTimer(self)
        self._timer.timeout.connect(self._on_tick)
        self._last_shown_elapsed = 0.0

        # The status poll's plain-data baseline (05-10): the previous
        # get_status() snapshot the 1 Hz diff compares against. The
        # DIALOG is never pickled, so a plain dict store is free
        # (05-RESEARCH-status-surface.md pitfall 1).
        self._last_status = None

    # ---- the rolling info box ----

    def _log(self, line):
        """Append one plain line to the rolling info box (auto-scrolls).

        The single append channel every tab-visible event uses (the
        prior-art _log shape). The status-poll plan calls this for
        diff lines; the countdown calls it directly.
        """
        self._info_log.append(str(line))

    # ---- the 3-2-1 countdown (P-1 wizard-free window; P-2 cancellable) ----

    def start_countdown(self, wizard):
        """Arm the countdown for a fully PREPARED (not yet activated)
        wizard.

        Self-healing (P-2): any pending countdown is cancelled FIRST,
        so a double-Start never leaves two pending countdowns whose
        first GO would activate an orphaned wizard over the second
        game. Clears the info box, logs 'Get ready...', and starts the
        1 s member timer. The wizard stays OFF the stack until GO
        (P-1) -- only ``_begin_play`` activates it.
        """
        self.cancel_pending_start()
        self._pending_wizard = wizard
        self._info_log.clear()
        self._log('Get ready...')
        self._countdown_n = 3
        self._countdown_timer.start(1000)

    def _countdown_tick(self):
        """One countdown step: log n and count down, or GO at n == 0.

        Deterministic when driven directly (the headless smoke drives
        the steps AS METHODS -- the SMOKE-13 probe already proved the
        real-timer cadence), identical when the member timer fires.
        """
        n = self._countdown_n
        if n > 0:
            self._log('%d' % n)
            self._countdown_n = n - 1
        else:
            self._countdown_timer.stop()
            self._log('GO!')
            self._begin_play()

    def _begin_play(self):
        """GO: activate the pending wizard, own the FIRST status
        content, and start the 1 Hz render.

        ``gamestart.activate_game`` (the cmd tier's Pattern-2 single
        activation home) pushes the wizard per the msm ORDER LAW --
        with the conditional replace re-evaluated at activation -- and
        anchors the GameState timer from zero. This is the ONLY point
        where the countdown's wizard reaches the stack (P-1). The
        START SEQUENCE owns the first status content (pitfall 4): the
        FIRST level line and the FIRST required label render here from
        the PENDING wizard's get_status() -- instant, ordered right
        after 'GO!', no poll race -- and ``_last_status`` is seeded so
        the poll's first observation is SILENT (status_events(None,
        state) -> []). The poll only reports CHANGES. The 1 Hz timer
        restart is a defensive stop + start (the prior-art shape).
        """
        from . import gamestart, status_text
        gamestart.activate_game(self._pending_wizard)
        state = self._pending_wizard.get_status()
        self._log(status_text.level_molecule_line(state))
        self._required_label.setText(
            status_text.required_display(state['required']))
        self._last_status = state
        self._pending_wizard = None
        self._timer.stop()
        self._timer.start(1000)

    def cancel_pending_start(self):
        """Cancel a pending countdown (P-2: stop() cancels).

        Called by every new start_countdown (self-healing) and by the
        window's cleanup handler (plan 05-09) -- a cancelled countdown
        NEVER reaches GO, so it can never activate a stale wizard over
        deleted objects or over the next game.
        """
        if self._countdown_timer.isActive():
            self._countdown_timer.stop()
        self._pending_wizard = None

    # ---- the 1 Hz elapsed timer (P-4: single live-read anchor) ----

    def _compute_elapsed(self):
        """Seconds since GO, computed from the LIVE GameState anchor.

        One anchor home (P-4): never a GUI-side clock copy. Returns
        0.0 before the anchor exists (a never-started game) and clamps
        at 0 so a rebase edge case can never show a negative time.
        """
        from . import engine
        gs = engine._current_game()
        if gs.timer_anchor is None:
            return 0.0
        return max(0.0, time.time() - gs.timer_anchor)

    @staticmethod
    def _format_mss(seconds):
        """M:SS with minutes unbounded: 75 s -> '1:15', 90 min ->
        '90:12' (v1's exact shipped format)."""
        s = int(seconds)
        return '%d:%02d' % (s // 60, s % 60)

    def _on_tick(self):
        """1 Hz render: update the label, or freeze under a modal child.

        Pause rule (timer fairness): while ANY modal child is open
        (``QApplication.activeModalWidget()`` is not None -- file
        dialogs, warning boxes alike, which catch the v1 gap of
        Setup-tab dialogs mid-game) the elapsed time must not advance
        visibly, so the tick REBASES the single anchor in place via
        ``GameState.rebase_timer`` and does NOT update the label (the
        clock freezes at the last shown second; granularity <= 1 s at
        the modal-open edge, documented in the module docstring). No
        boxes here (P-6); timers fire through nested loops, so this
        branch is designed for exactly that state (P-8). The EngineError
        guard lets the tick survive a no-game window (mid-restart).
        The STATUS HALF (05-10) runs AFTER the label render: the same
        1 Hz tick carries the poll-diff (piggybacked, no second timer);
        the modal-pause branch returns EARLY, so the poll is skipped
        while the clock is frozen.
        """
        if QtWidgets.QApplication.activeModalWidget() is not None:
            from . import engine
            try:
                engine._current_game().rebase_timer(
                    time.time(), self._last_shown_elapsed)
            except engine.EngineError:
                return
            return
        self._last_shown_elapsed = self._compute_elapsed()
        self._timer_label.setText(
            self._format_mss(self._last_shown_elapsed))
        self._refresh_status()

    # ---- the 1 Hz status poll (05-10: the poll-diff read path) ----

    def _refresh_status(self):
        """The 1 Hz poll-diff: append only CHANGES + keep the
        required label truthful (SCORE-04's dynamic half).

        Public accessors ONLY -- ``cmd.get_wizard()`` behind a lazy
        relative import + isinstance gate (the module-identity law,
        pitfall 2; a module-level GameWizard import would silently
        fail the gate under the installed identity), then the live
        wizard's plain-data get_status() (05-07; the tab never
        registers itself on the wizard -- the whole stack is pickled
        on session save, pitfall 1). No GameWizard live -> the
        required label resets to 'Required: -' and the baseline
        clears. Otherwise the PURE diff (``status_text.status_events``)
        owns every event line -- first observation SILENT (pitfall 4:
        the start sequence owns the first level line), a molecule/
        level change -> one level line, a selection change -> the
        'Selected:' line, a NEW error string -> the 'ERROR:' line with
        sticky dedupe (pitfall 3). The required label is reference
        info (Pattern 3): refreshed on molecule OR level change
        (molecule_id repeats across levels -- the 06-07 fix), never a
        log line, never scrolled away -- rendered by the pure
        ``status_text.required_display``. 06-07: a game_over
        TRANSITION additionally logs the pure
        ``status_text.endgame_lines`` block over
        ``engine.endgame_summary()`` (the sanctioned accessor CALL,
        never attribute privates) -- one block per game end.
        """
        from pymol import cmd
        from . import status_text, wizard
        w = cmd.get_wizard()
        if not isinstance(w, wizard.GameWizard):
            self._required_label.setText('Required: -')
            self._last_status = None
            return
        state = w.get_status()
        for line in status_text.status_events(self._last_status, state):
            self._log(line)
        prev = self._last_status
        # 06-07 stale-label fix: molecule_id repeats ACROSS levels
        # ('mol-001' again on level 2 -- generator numbers molecules
        # within each level), so keying the refresh on molecule_id
        # alone left the LEVEL-2 requirement showing level 1's label.
        # level_pos does not repeat; refresh when EITHER moved.
        if (prev is None
                or prev.get('molecule_id') != state.get('molecule_id')
                or prev.get('level_pos') != state.get('level_pos')):
            self._required_label.setText(
                status_text.required_display(state['required']))
        # 06-07: the ONE logging home for the game_over TRANSITION --
        # tab-triggered ends reach it via the lifecycle impls'
        # SYNCHRONOUS refresh; panel-triggered ends (the wizard's own
        # Confirm) reach it via the 1 Hz tick. Transition-only (prev
        # game_over False -> curr True), so the block logs exactly once
        # per game end with no double-log.
        prev_go = bool(prev.get('game_over')) if prev else False
        if state.get('game_over') and not prev_go:
            from . import engine
            for line in status_text.endgame_lines(
                    engine.endgame_summary()):
                self._log(line)
        self._last_status = state

    # ---- the Hint handler (05-08 PLAY-05) ----

    def _guard(self, fn):
        """The 04-09 _guard contract, VERBATIM (setup_window.py:637) --
        the FIRST _guard on this class: run fn() mapping the ValueError
        family + OSError to a modal warning box (modal CHILD -- allowed;
        not a tick/countdown path, so P-6 does not apply). str(e) shown
        verbatim: every house refusal already names its cause. Unexpected
        exceptions PROPAGATE. Returns fn()'s value, None on refusal."""
        try:
            return fn()
        except (ValueError, OSError) as e:
            QtWidgets.QMessageBox.warning(self, 'AA-match', str(e))
            return None

    def _on_hint(self):
        """Hint button: capability hint via _guard. NON-MODAL: the
        recolor on-screen IS the feedback; NO success box (the
        _on_start precedent, setup_window.py:920)."""
        self._guard(self._hint_now)

    def _hint_now(self):
        """The non-modal impl: dispatch to the live GameWizard's
        capability hint (recolor-only, PLAY-05). SILENT no-op when no
        GameWizard is active -- pre-GO (the countdown window is
        wizard-free, P-1) or no game at all (H-8; the
        PA-gui_game:142-145 precedent); the recolor op is reachable
        ONLY through an active wizard. Logs the pinned count line on
        success; returns the hint's plain-data dict (or None pre-GO)."""
        from pymol import cmd
        from . import wizard as wizard_mod
        prior = cmd.get_wizard()
        if not isinstance(prior, wizard_mod.GameWizard):
            return None
        result = prior.hint()
        if result is not None:
            # result None == the wizard _guard already surfaced a
            # refusal on the wizard panel (unreachable under
            # solvability-by-construction) -- never crash logging it.
            self._log('Hint: %d eligible amino acid(s) highlighted.'
                      % result['count'])
        return result

    # ---- the Confirm handler (06-07: SCORE-01/03 tab UI) ----

    def _on_confirm(self):
        """Confirm button: the wizard's confirm op via _guard. NO
        confirmation warning (Confirm is the routine gameplay action,
        not a destructive one). The 06-09 endgame tail: when the op
        completed the game (truthy dict + game_over), ``cmd.refresh()``
        fires a scene redraw NOW and ``_show_endgame_modal`` is
        scheduled 100 ms out via ``QtCore.QTimer.singleShot`` (the v1
        _on_win mechanics) so the pop's color-restore burst paints
        BEFORE the modal's exec_() blocks the event loop (v1 Bug A).
        A None result (guarded refusal, already surfaced) schedules
        nothing."""
        result = self._guard(self._confirm_now)
        if result and result.get('game_over'):
            from pymol import cmd
            cmd.refresh()
            summary = result['summary']
            QtCore.QTimer.singleShot(
                100, lambda: self._show_endgame_modal(summary))

    def _confirm_now(self):
        """The non-modal impl (06-07): dispatch to the live
        GameWizard's confirm_molecule() behind the isinstance gate
        (silent no-op pre-GO, the _hint_now shape), then run the poll
        SYNCHRONOUSLY right after the op so the info box gets the
        scored line + debrief + position line with ZERO poll latency
        (no 1 Hz loss) -- and, when the op completed the game, the
        game_over transition block in the same call. A None result
        means the wizard _guard already surfaced the refusal on the
        PANEL (the hint precedent); the tab stays silent. A completed
        game runs _endgame_sequence. Returns the op's plain-data dict
        (or None pre-GO / on refusal)."""
        from pymol import cmd
        from . import wizard as wizard_mod
        prior = cmd.get_wizard()
        if not isinstance(prior, wizard_mod.GameWizard):
            return None
        result = prior.confirm_molecule()
        if result is None:
            return None
        self._refresh_status()
        if result.get('game_over'):
            self._endgame_sequence(result['summary'])
        return result

    # ---- the Skip / Give-Up handlers (06-07: SCORE-05/06 tab UI) ----

    def _on_skip(self):
        """'Skip Molecule' menu action: the MODAL warning wrapper.

        GATE FIRST (endgame-ui sec 5.4): a press with no live
        GameWizard -- pre-GO (the countdown window is wizard-free,
        P-1) or no game at all -- is a SILENT no-op BEFORE any box; no
        modal over a wizard-free game. Then the spec-required
        QMessageBox.question Yes|No (the pinned 06-02 wording) as a
        modal CHILD of the window (PITFALL 4 legal; Escape reads as
        No).         YES routes the impl through _guard; No/Escape is a safe
        no-op. NO rebase_timer here (the caller-owns-modal-detection
        law: the 1 Hz tick's activeModalWidget branch freezes the
        clock over ANY real modal). The 06-09 endgame tail: when the
        impl's op completed the game, the SAME refresh + singleShot
        tail as _on_confirm schedules ``_show_endgame_modal`` 100 ms
        after the pop's color-restore burst (a last-molecule skip of
        the last level COMPLETES the game, 06-06). A None result
        (guarded refusal, already surfaced) schedules nothing."""
        from pymol import cmd
        from . import status_text, wizard as wizard_mod
        if not isinstance(cmd.get_wizard(), wizard_mod.GameWizard):
            return
        btns = (QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
        if QtWidgets.QMessageBox.question(
                self.window(), status_text.SKIP_WARNING_TITLE,
                status_text.SKIP_WARNING_TEXT,
                btns) == QtWidgets.QMessageBox.Yes:
            result = self._guard(self._skip_now)
            if result and result.get('game_over'):
                cmd.refresh()
                summary = result['summary']
                QtCore.QTimer.singleShot(
                    100, lambda: self._show_endgame_modal(summary))

    def _on_giveup(self):
        """'Give Up...' menu action: the MODAL warning wrapper -- the
        identical shape as _on_skip with the GIVEUP_ pinned strings
        routing to _giveup_now (YES = the wrapper's _guard call;
        No/Escape safe). A successful give-up is ALWAYS game-over
        (06-06), so the 06-09 refresh + singleShot tail fires on every
        truthy result here (the game_over key check stays, mirroring
        _on_confirm/_on_skip verbatim)."""
        from pymol import cmd
        from . import status_text, wizard as wizard_mod
        if not isinstance(cmd.get_wizard(), wizard_mod.GameWizard):
            return
        btns = (QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
        if QtWidgets.QMessageBox.question(
                self.window(), status_text.GIVEUP_WARNING_TITLE,
                status_text.GIVEUP_WARNING_TEXT,
                btns) == QtWidgets.QMessageBox.Yes:
            result = self._guard(self._giveup_now)
            if result and result.get('game_over'):
                cmd.refresh()
                summary = result['summary']
                QtCore.QTimer.singleShot(
                    100, lambda: self._show_endgame_modal(summary))

    def _skip_now(self):
        """The non-modal Skip impl (06-07): defensive isinstance gate ->
        GameWizard.skip_molecule() (partial score stored, then the
        shared advancement site -- the op IS the Yes-branch; the
        warning lives in the wrapper). None = a guarded refusal
        already surfaced on the PANEL; the tab stays silent. The
        SYNCHRONOUS poll then lands the skipped line + the new
        position line with zero 1 Hz loss; a skip of the LAST
        molecule of the last level completes the game (06-06), so
        game_over runs the shared _endgame_sequence. NO boxes here
        (the smoke-99 law -- headless smokes drive this directly).
        Returns the op's plain-data dict (or None pre-GO / on
        refusal)."""
        from pymol import cmd
        from . import wizard as wizard_mod
        prior = cmd.get_wizard()
        if not isinstance(prior, wizard_mod.GameWizard):
            return None
        result = prior.skip_molecule()
        if result is None:
            return None
        self._refresh_status()
        if result.get('game_over'):
            self._endgame_sequence(result['summary'])
        return result

    def _giveup_now(self):
        """The non-modal Give-Up impl (06-07): defensive isinstance gate
        -> GameWizard.give_up() (ends the game AT THE CURRENT STAGE --
        the current molecule is NOT scored, spec.md:44-45). Successful
        give_up is ALWAYS game-over, so the sync poll lands the
        'Game ended ...' line + the endgame block (via the game_over
        transition, exactly once) and _endgame_sequence stops the
        clock, pins the exact final time, and pops the wizard. NO
        boxes here (the smoke-99 law). Returns the op's plain-data
        dict (or None pre-GO / on refusal)."""
        from pymol import cmd
        from . import wizard as wizard_mod
        prior = cmd.get_wizard()
        if not isinstance(prior, wizard_mod.GameWizard):
            return None
        result = prior.give_up()
        if result is None:
            return None
        self._refresh_status()
        if result.get('game_over'):
            self._endgame_sequence(result['summary'])
        return result

    # ---- the Restart handler (06-08: SCORE-09) ----

    def _on_restart(self):
        """Restart button: replay the stored initial state via _guard.
        NO confirmation warning (spec.md:43-45 requires warnings for
        Skip/Give Up only -- restart-reset D9; the countdown log is the
        feedback, the _on_start precedent)."""
        self._guard(self._restart_now)

    def _restart_now(self):
        """The non-modal impl (06-08): the verbatim ``_last_start``
        replay through the 05-09 deferred start sequence.

        RESTART = spec replay of the ``gamestart._last_start`` INPUT
        tuple (05-05) -- the PITFALL-9 mechanism; backup.py has NO
        Phase-6 role (it remains the Phase-7 persistence policy home;
        the module itself is never wired here). Steps: the fail-closed
        None refusal FIRST (restart-reset D1 -- the '_last_start is
        None' refusal surfaces via the wrapper's _guard box in the
        GUI; headless smokes assert the raise on this impl directly);
        the P-2 belt-and-braces pending-start cancel (the _on_cleanup
        handler-top cancel precedent); the P-3 pop (the LIVE
        GameWizard pops -- its cleanup restores msm/colors/pk1; a USER
        wizard on top is never popped); then the replayed
        ``gamestart.start_game(..., activate=False)`` over the tuple's
        4 keys -- NO build_state pre-checks (the tuple was validated
        at first start; the replay is deterministic; OSError/ValueError
        e.g. a deleted fixture still surfaces through _guard -- the
        04-13 clean-then-refuse residue law); then the countdown arms
        (self-healing cancel + box clear + 'Get ready...'); ONLY THEN
        is the pinned restart line logged (restart-reset D7: logging
        it BEFORE the arm would let the countdown's box clear wipe it
        -- the line must survive as the LAST pre-tick entry). At GO
        the existing _begin_play re-anchors the timer from zero and
        re-seeds _last_status -- a FRESH GameState by construction
        (engine.new_game), correct for a NEW game.

        The op is NOT gated behind an active wizard (restart-reset
        D1): it works from the post-endgame popped state, and
        mid-countdown too (the self-healing arm cancels the pending
        one first). The pre-existing dormant-user-wizard stack-hole
        (restart-reset D6) is documented-only -- NOT a Phase-6 fix.

        Returns True on a successful arm; raises the ValueError family
        on refusal (the wrapper maps it to the _guard box; the smoke
        drives this impl directly)."""
        from . import gamestart, status_text
        ls = gamestart._last_start
        if ls is None:
            raise ValueError('Restart: no game has been started yet.')
        self.cancel_pending_start()
        self._pop_game_wizard()
        wiz = gamestart.start_game(setup=ls['setup'], seed=ls['seed'],
                                   candidates=ls['candidates'],
                                   ligand_content=ls['ligand_content'],
                                   activate=False)
        self.start_countdown(wiz)
        self._log(status_text.game_restarted_line())
        return True

    # ---- the Reset handler (06-08: SCORE-10) ----

    def _on_reset_grid(self):
        """Reset button: the wizard's grid replay via _guard. NO
        confirmation warning and NO box in the wrapper -- the reset is
        non-destructive (positions only; rotations persist); house
        refusals land on the PANEL via the wizard's own _guard."""
        self._guard(self._reset_grid_now)

    def _reset_grid_now(self):
        """The non-modal impl (06-08): the reset OWNER LAW (restart-
        reset research sec 4) -- the tab calls the wizard's PUBLIC
        reset op behind the isinstance gate (PITFALL 6 at the widget
        layer). What this impl must NEVER do: dispatch the engine's
        grid replay itself, reach the engine's module privates, touch
        wizard privates (the color store / result clearing are
        instance-internal), or add pose data to the poll.

        Silent no-op (returns None) when no GameWizard is live --
        pre-GO (the countdown window is wizard-free, P-1) or no game
        (H-8); the AAs are already AT their grid poses in a fresh
        game, so no countdown-state check is needed (restart-reset
        D8). The op returns None always; a house refusal (e.g. 'The
        game is over.') surfaces on the wizard PANEL through the
        wizard's own _guard, and the tab stays silent.

        The SYNCHRONOUS poll afterwards renders the pinned reset line:
        positions are invisible to the poll's diff (_state_dict
        carries no pose keys and 'result' is never fingerprinted), so
        the game_reset marker (06-06) is the ONLY channel -- it flows
        into the 06-02 pinned 'Amino acids reset to grid positions
        (orientations kept).' line. The timer keeps running and NO
        GameState is touched (positions only; rotations persist -- the
        03-03 replay law).

        Returns True on dispatch, None on the silent no-op gate."""
        from pymol import cmd
        from . import wizard as wizard_mod
        prior = cmd.get_wizard()
        if not isinstance(prior, wizard_mod.GameWizard):
            return None
        prior.reset_grid()
        self._refresh_status()
        return True

    # ---- the Save handler (07-06: SCORE-08 save half) ----

    def _on_save_game(self):
        """Save button: checkpoint the running game via _guard. The
        THIN wrapper owns the ONLY modal (the file dialog); the impl is
        box-free (the 04-09 _X_impl law, the 06-07/06-09 shape).

        GATE FIRST (the 06-07 gate-first law): a press with no live
        GameWizard -- pre-GO (the countdown window is wizard-free,
        P-1), no game at all, or the post-endgame popped state -- is a
        SILENT no-op BEFORE any dialog. NO game_over refusal (07-04
        Recorded Decision 3 -- a panel-ended-but-live wizard saves
        losslessly; game_over/end_state/final_time round-trip in the
        game_state block). NO rebase_timer here (the
        caller-owns-modal-detection law: the tick's activeModalWidget
        branch freezes the clock over ANY real modal, human-verified
        05-11).

        The elapsed is captured BEFORE the dialog opens (the v1
        capture-before-dialog doctrine, PA-persistence.py:62-68): the
        sidecar's elapsed_at_save must not depend on whether a 1 Hz
        tick fired while the dialog was open. The default filename is
        'game.aamz' with the '.aamz' extension auto-appended (the 04-09
        Decision-2 law); the filter is 'AA-match Checkpoint (*.aamz);;
        All Files (*)'. Cancel is a safe no-op (nothing to undo -- the
        clock freeze is already handled by the tick branch).

        A successful save logs 'Game saved to <path>.' via the pure
        status_text builder AFTER the impl returns (the 07-03
        handler-logged law) -- NO success box: the info-box line IS the
        feedback (the v1 game-tab Save precedent,
        PA-__init__:786-787)."""
        from pymol import cmd
        from . import status_text, wizard as wizard_mod
        if not isinstance(cmd.get_wizard(), wizard_mod.GameWizard):
            return
        elapsed = self._compute_elapsed()
        path, _filter = QtWidgets.QFileDialog.getSaveFileName(
            self, 'Save AA-match Game', 'game.aamz',
            'AA-match Checkpoint (*.aamz);;All Files (*)')
        if not path:
            return
        if not path.endswith('.aamz'):
            path += '.aamz'
        final = self._guard(lambda: self._save_game_to(path, elapsed))
        if final is not None:
            self._log(status_text.game_saved_line(final))

    def _save_game_to(self, path, elapsed):
        """Non-modal save impl (Phase 7 SCORE-08). The elapsed arrives
        PRE-DIALOG-captured (the v1 doctrine, PA-persistence.py:62-68):
        the impl writes a value that does not depend on whether a 1 Hz
        tick fired during the dialog. The clock itself needs NO manual
        stop/rebase bracket -- the tick's activeModalWidget branch
        freezes it under the dialog (human-verified 05-11).

        A pure function of (path, elapsed): capture the live snapshot
        through the 07-04 cmd-tier seam (scene-read-only) and write the
        atomic .aamz archive -- the Qt tier never touches engine /
        wizard privates (the 05-07/05-10 accessor law). NO boxes here
        (the smoke-99 law -- headless smokes drive this directly).
        Returns the final (Windows-converted) written path; failures
        propagate to the wrapper's _guard (the 04-09 contract)."""
        from . import gamestart
        data = gamestart.capture_checkpoint_snapshot(elapsed)
        return gamestart.save_checkpoint(path, data)

    # ---- the Import handler (07-07: PERSIST-02) ----

    def _on_import(self):
        """Import button: load an exported game file and start it via
        _guard. The THIN wrapper owns the ONLY modal (the file dialog);
        the impl is box-free (the 04-09 _X_impl law).

        GATE-FREE (07-RESEARCH-import.md I2): unlike every other tab
        handler there is NO isinstance gate upfront -- Import is legal
        with NO game live (it CREATES one; the v1 import ran with any
        prior state, PA-__init__:790-812), so a pre-GO/no-game press
        must reach the same dialog. NO confirmation warning mid-game
        (07-07 Recorded Decision 2): house law -- spec warnings exist
        ONLY for Skip/Give Up (spec.md:43-45, restart-reset D9); a
        mid-game Import discards the running game exactly like Start
        does. The filter is the 04-12 export's EXACT filter ('AA-match
        Game (*.aamatch.json);;All Files (*)' -- the game-files-only
        half; the .aamz checkpoint extension + kind dispatch land in
        the later plan, no dead branch here). Cancel is a silent
        no-op. NO success box: the countdown + armed wizard + the
        after-arm info-box line ARE the feedback (the _on_start
        precedent). Refusals surface VERBATIM through _guard (no
        catch-and-humanize layer -- the 04-13/06-08 convention)."""
        path, _filter = QtWidgets.QFileDialog.getOpenFileName(
            self, 'Import AA-match Game', '',
            'AA-match Game (*.aamatch.json);;All Files (*)')
        if not path:
            return
        self._guard(lambda: self._import_game_from(path))

    def _import_game_from(self, path):
        """Non-modal import impl (07-07, PERSIST-02): materialize the
        game file's EMBEDDED payload directly into a fresh, prepared
        game and arm the countdown.

        REFUSAL-FIRST (parse + gates BEFORE any scene touch): the
        04-12-proven five-gate consumer contract -- read the JSON
        container (unparseable refuses inside the pure reader) and run
        game_file.parse_game_data (foreign magic / newer container /
        misfiled kind / wrong game_format_version / the exact-match
        detector stamp / ligand integrity + source cross-checks). A
        refusal raises the ValueError family BEFORE this impl mutates
        anything: the scene, the tab log, the wizard stack, the
        countdown, and the running game stay EXACTLY as they were.
        (07-07 in-flight fix: the import reads the container via
        persistence.read_json_file -- parse_game_data takes the FULL
        container header + data so its gate 1 can run; a
        load_container(...,'game') return value already STRIPS the
        header the gate needs. Every gate class still runs through
        these two calls.) The disk path routes paths.to_windows_path
        (the AGENTS path law; on Windows the dialog's own path passes
        through unchanged).

        THEN the deferred replacement sequence, mirroring _restart_now
        and _start_impl: cancel_pending_start FIRST (P-2 belt-and-
        braces -- an in-flight countdown's GO must never activate an
        orphaned wizard over the imported game), _pop_game_wizard
        (P-3 -- the live GameWizard pops with its cleanup; a user
        wizard is never popped), then the 07-05 payload-direct seam
        -- cleanup -> materialize the embedded payload (the truth,
        NEVER regenerated: setup+seed regeneration is manifest-content
        -dependent and impossible for uploaded games on the importer
        machine) -> adopt a FRESH GameState (zeros; the timer anchors
        from zero at GO -- a game file carries no elapsed; the sidecar
        elapsed belongs to the checkpoint path only) -> wizard ->
        compose. NO seed arg: the seam derives it from payload['seed']
        (the spec's authoritative seed). NO upfront gate: an import
        with NO game live just skips the cancel/pop no-ops into the
        same sequence.

        LOG AFTER THE ARM (the restart D7 law / 07-03's placement
        law): the pure status_text.game_imported_line logs AFTER
        start_countdown arms -- the arm's _info_log.clear() would
        wipe a pre-arm line. NO boxes here (the smoke-99 law --
        headless smokes drive this impl directly). Returns True on a
        successful arm; raises the ValueError/OSError family on
        refusal or viewer failure (the wrapper's _guard boxes it
        verbatim)."""
        from . import game_file, gamestart, paths, persistence
        from . import status_text
        container = persistence.read_json_file(paths.to_windows_path(path))
        parsed = game_file.parse_game_data(container)
        self.cancel_pending_start()
        self._pop_game_wizard()
        wiz = gamestart.start_game_from_payload(
            parsed['payload'],
            ligand_content=(parsed['ligand_texts'] or None),
            setup=parsed['setup'],
            activate=False)
        self.start_countdown(wiz)
        self._log(status_text.game_imported_line(path))
        return True

    # ---- the endgame sequence (06-07: the shared game-over tail) ----

    def _endgame_sequence(self, summary):
        """Stop the clock, pin the exact final time, pop the wizard.

        Shared by every game-over path a tab impl can trigger
        (_confirm_now / _skip_now / _giveup_now). ORDER (v1's _on_win
        precedent, gui_game.py:301): ``self._timer.stop()`` FIRST --
        the tick can never stop the clock on its own (the engine's
        GameState stays LIVE after the game ends, so a running tick
        would keep the label advancing forever over a finished
         game); then pin
        ``_timer_label`` to the EXACT final elapsed from the summary
        (the live tick value can be up to 1 s stale); then the
        isinstance-gated pop (the pop's own cleanup fires the
        color-restore burst that the 06-09 refresh+singleShot modal
        lands AFTER). No modal here (P-6/the smoke-99 law): the
        scheduling tail lives on the WRAPPERS only. Returns
        nothing."""
        from . import status_text
        self._timer.stop()
        self._timer_label.setText(
            status_text.format_mss(summary['final_time']))
        self._pop_game_wizard()

    # ---- the endgame modal (06-09: SCORE-07's winning message) ----

    def _show_endgame_modal(self, summary):
        """The endgame MODAL: a child QMessageBox carrying the pure
        ``status_text.endgame_lines`` block (SCORE-07; the v1
        _finish_win precedent, gui_game.py:306-345).

        WRAPPER-ONLY -- NEVER call from an impl or the tick (the
        smoke-99 receipt: a static/modal box under platform=offscreen
        blocks a headless smoke indefinitely; and a modal inside a
        timer callback re-enters a modal loop, P-6). Only the
        wrappers schedule it, via ``cmd.refresh()`` +
        ``QtCore.QTimer.singleShot(100, ...)``, AFTER the endgame
        sequence's pop has fired its color-restore burst.

        Both v1 bug-fix rationales are retained verbatim. (Bug A --
        the clobbered redraw): exec_() runs a nested event loop that
        stops normal redraw servicing, so a modal shown in the same
        event-loop turn as the pop's color restores would defer the
        redraw until after dismissal; the 100 ms gap lets PyMOL paint
        the restored scene FIRST (100 ms is the v1-shipped value --
        kept verbatim, no new constant). (Bug B -- the hidden
        dialog): the parent is ``self.window()`` (the top-level
        modeless window) and ``Qt.WindowStaysOnTopHint`` keeps the box
        ABOVE the PyMOL OpenGL viewer instead of landing behind it.

        Content is EXACTLY the pure endgame block (the two-surface
        discipline -- the modal is the MOMENT, the info box is the
        RECORD): setText carries lines[0] (the headline -- 'You
        win! ...' or 'Game over -- gave up ...', the block's pinned
        first line) and setInformativeText carries the remaining lines
        joined with '<br>' (Qt rich text -- the v1 stats shape
        gui_game.py:341-343), so modal and info box show one wording
        home. exec_() on a child QMessageBox is the sanctioned modal
        class (PITFALLS.md:105); the 1 Hz timer is already STOPPED by
        the endgame sequence before this fires, so the modal needs no
        pause handling. Returns nothing."""
        from . import status_text
        lines = status_text.endgame_lines(summary)
        msg = QtWidgets.QMessageBox(self.window())
        msg.setIcon(QtWidgets.QMessageBox.Information)
        msg.setWindowTitle('AA-match')
        msg.setText(lines[0])
        msg.setInformativeText('<br>'.join(lines[1:]))
        msg.setWindowFlags(msg.windowFlags()
                           | QtCore.Qt.WindowStaysOnTopHint)
        msg.exec_()

    def _pop_game_wizard(self):
        """Pop a GameWizard iff it is top-of-stack; returns popped-bool.

        The GameTab's OWN copy of the 04-11 isinstance-pop pattern
        (setup_window.py:826-845 -- the dialog helper is not reachable
        from the tab without crossing the composition root): lazy
        cmd+wizard imports (the module-identity law), isinstance gate
        (a USER wizard is never popped), canonical ``cmd.set_wizard()``
        None-pop -- the popped wizard's own cleanup runs (msm restore
        + color restores) and the prior wizard (if any) auto-resumes.
        No deletion: the _aam_* game objects SURVIVE the pop (Done
        semantics; Cleanup is the explicit removal op, endgame-ui
        D6)."""
        from pymol import cmd
        from . import wizard as wizard_mod
        prior = cmd.get_wizard()
        if isinstance(prior, wizard_mod.GameWizard):
            cmd.set_wizard()
            return True
        return False
