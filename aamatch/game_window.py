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
transition fires once).

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
    bottom. Button inventory (Phase 6, plan 06-07): 'Hint' (05-08),
    'Confirm' (spec.md:41), and the 'Skip / Give Up' QToolButton+QMenu
    dropdown (spec.md:42) with 'Skip Molecule' / 'Give Up...' actions.
    The button row keeps its stretch LAST (insertions go BEFORE the
    stretch) so the remaining later-phase slots (Restart/Reset/Save/
    Import, Phases 6/7, research OQ-1 later-add recommendation) never
    reflow the timer row.
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
        layout.addLayout(btn_row)
        self.btn_hint.clicked.connect(self._on_hint)
        self.btn_confirm.clicked.connect(self._on_confirm)
        self.act_skip.triggered.connect(self._on_skip)
        self.act_giveup.triggered.connect(self._on_giveup)

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
        not a destructive one); still NON-MODAL in the wrapper -- the
        endgame MODAL tail is 06-09's addition, so this wrapper's
        structure stays stable for that edit."""
        self._guard(self._confirm_now)

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
        No). YES routes the impl through _guard; No/Escape is a safe
        no-op. NO rebase_timer here (the caller-owns-modal-detection
        law: the 1 Hz tick's activeModalWidget branch freezes the
        clock over ANY real modal). The 06-09 plan adds ONLY the
        endgame-modal scheduling tail here -- this structure stays
        stable for that edit."""
        from pymol import cmd
        from . import status_text, wizard as wizard_mod
        if not isinstance(cmd.get_wizard(), wizard_mod.GameWizard):
            return
        btns = (QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
        if QtWidgets.QMessageBox.question(
                self.window(), status_text.SKIP_WARNING_TITLE,
                status_text.SKIP_WARNING_TEXT,
                btns) == QtWidgets.QMessageBox.Yes:
            self._guard(self._skip_now)

    def _on_giveup(self):
        """'Give Up...' menu action: the MODAL warning wrapper -- the
        identical shape as _on_skip with the GIVEUP_ pinned strings
        routing to _giveup_now (YES = the wrapper's _guard call;
        No/Escape safe)."""
        from pymol import cmd
        from . import status_text, wizard as wizard_mod
        if not isinstance(cmd.get_wizard(), wizard_mod.GameWizard):
            return
        btns = (QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
        if QtWidgets.QMessageBox.question(
                self.window(), status_text.GIVEUP_WARNING_TITLE,
                status_text.GIVEUP_WARNING_TEXT,
                btns) == QtWidgets.QMessageBox.Yes:
            self._guard(self._giveup_now)

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
        color-restore burst that 06-09's refresh+singleShot modal
        lands AFTER). No modal here (P-6/the smoke-99 law): 06-09 adds
        ONLY the modal-scheduling tail on the WRAPPERS. Returns
        nothing."""
        from . import status_text
        self._timer.stop()
        self._timer_label.setText(
            status_text.format_mss(summary['final_time']))
        self._pop_game_wizard()

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
