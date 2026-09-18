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
game wizard on the stack yet). The status POLL (what else the info
box shows and when) lands on a later plan.

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
    info box with stretch below, and the Hint button row at the
    bottom. The button row reserves its slot with a stretch so the
    later phases' game-lifecycle button rows (Confirm/Skip/Save/
    Restart/Reset/Import arrive with Phases 6/7, research OQ-1
    later-add recommendation) never reflow the timer row.
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
        layout.addLayout(btn_row)
        self.btn_hint.clicked.connect(self._on_hint)

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
        """GO: activate the pending wizard and start the 1 Hz render.

        ``gamestart.activate_game`` (the cmd tier's Pattern-2 single
        activation home) pushes the wizard per the msm ORDER LAW --
        with the conditional replace re-evaluated at activation -- and
        anchors the GameState timer from zero. This is the ONLY point
        where the countdown's wizard reaches the stack (P-1). The 1 Hz
        timer restart is a defensive stop + start (the prior-art
        shape). The level line / required-label content / status poll
        are the status-surface plan's; mechanics only here.
        """
        from . import gamestart
        gamestart.activate_game(self._pending_wizard)
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
