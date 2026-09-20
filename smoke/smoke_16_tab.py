"""Headless SMOKE-16 - the Game tab lifecycle controls (plan 06-07, T1b).

Run (from WSL, repo root):
    bash smoke/run_smoke.sh smoke/smoke_16_tab.py 120
Verdict is carried by the printed marker (exit codes cannot carry
verdicts through the cmd.exe wrapper): grep '=== SMOKE-16 PASS ==='.

Proves the Phase-6 tab lifecycle wiring (aamatch/game_window.py,
SCORE-01/05/06 UI) headlessly in REAL PyMOL under the T1b house recipe
(the 04-01 probe verdict is PASS, platform=offscreen; QApplication
reuse-or-create; the 04-05 recipe). ZERO modals anywhere: the smoke
drives the NON-MODAL impls as METHODS (_confirm_now/_skip_now/
_giveup_now), NEVER the wrappers -- the smoke-99 receipt: a static
QMessageBox BLOCKS indefinitely under offscreen, so _on_skip/_on_giveup
(the QMessageBox.question owners) are [HUMAN]-only (06-10).

PART A  the tab drive:
        A1 construction - SetupWindow() built offscreen; GameTab
        inventory: btn_hint ('Hint'), btn_confirm ('Confirm'),
        btn_skip_menu ('Skip / Give Up', QToolButton, InstantPopup)
        with the 2-action menu ('Skip Molecule', 'Give Up...'),
        tooltips non-empty on every control; the stretch stays LAST
        in the button row (the timer-row no-reflow law, 05-06 OQ-1);
        a FRESH GameTab shows the placeholder labels '0:00' /
        'Required: -' (the PART I2 pin class, SMOKE-11).
        A2 live game - start_game(activate=False) + start_countdown +
        4 direct _countdown_tick drives -> GO (that wizard pushed,
        float timer anchor, 'Level 1, molecule 1 of 2.' logged).
        A3 Confirm impl - _confirm_now() -> the pinned scored line
        ('Molecule 1 of 2 scored 0.00 (total 0.00).') + the result_lines
        debrief shapes + the new position line; _last_status updated;
        the live wizard advanced to molecule 2.
        A4 sync-refresh proof - every A3 assert runs IMMEDIATELY after
        the impl call with NO processEvents between (zero 1 Hz loss).
        A5 Skip impl - _skip_now() -> 'Skipped molecule 2 of 2 (partial
        score 0.00, total 0.00).' + the level-2 line; skip_count 1.
        A6 Give-up impl - _giveup_now() -> 'Game ended at level 2,
        molecule 1 of 2 (total 0.00).' + the endgame block (headline
        'Game over -- gave up at level 2, molecule 1 of 2.' logged
        EXACTLY once, per-level + total + time + molecules + skips
        lines per status_text.endgame_lines); the 1 Hz _timer STOPPED;
        _timer_label == format_mss(summary['final_time']); the wizard
        POPPED (stack empty); the required label holds its LAST
        required value (the timer is stopped -- no post-pop poll can
        reset it).
        A7 label-fix proof - fresh game via the countdown drive;
        confirm through level 1's two molecules -> the level advance;
        _required_label text == required_display(fetch from get_status)
        -- molecule_id repeats across levels ('mol-001' again), so the
        level_pos-aware refresh condition is what updates the label.
        A8 wrapper-gate proof - with NO wizard on the stack, driving
        the impls directly returns None (the isinstance gate) and the
        scene/log stay untouched (the box path is [HUMAN]-only 06-10).
        A9 restore - cancel + stop timers + done pop + prefix cleanup
        + gamestart._last_start reset -> the baseline scene EXACTLY.

Conventions (frozen Phase 1, kept): anchor repo root via sys.argv
first / cwd fallback (never __file__); import aamatch directly (module
identity 'aamatch'); every print on ONE line and flushed; check details
built from already-known data only (the 03-04 eager-detail lesson);
NEVER pump processEvents between start_countdown and the tick drive
(the 05-RESEARCH anti-flakiness strategy).

Python floor: runs inside PyMOL's Windows Python (3.9); written 3.6-safe.
"""
import os
import sys
import traceback

# QT_QPA_PLATFORM MUST be set BEFORE any pymol.Qt import (the offscreen
# recipe the 04-01 probe proved; aamatch.setup_window/game_window carry
# module-level pymol.Qt imports).
os.environ['QT_QPA_PLATFORM'] = 'offscreen'


def _find_repo_root():
    """Anchor the repo root WITHOUT trusting __file__ (01-07 discovery:
    inside a -cq script __file__ points at pymol/__init__.py)."""
    mine = 'smoke_16_tab.py'
    for arg in sys.argv:
        if arg.endswith(mine) and os.path.exists(arg):
            return os.path.dirname(os.path.dirname(os.path.abspath(arg)))
    return os.getcwd()


_ROOT = _find_repo_root()
print('SMOKE-ENV root:', _ROOT, flush=True)

failures = []
REC = {'checks': 0}


def check(name, cond, detail=''):
    REC['checks'] += 1
    print('SMOKE-16 %-44s %s %s' % (name, 'PASS' if cond else 'FAIL',
                                     detail), flush=True)
    if not cond:
        failures.append(name)


if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

import aamatch  # noqa: E402
from aamatch import engine, gamestart, placement, setup_state  # noqa: E402
from aamatch import status_text  # noqa: E402

print('SMOKE-ENV python: %s' % (sys.version.split()[0],), flush=True)

# ============================================================
# PART A: the tab lifecycle drive (T1b -- the 04-01 probe verdict is
# PASS (platform=offscreen), so the dialog portions RUN; ZERO modals:
# impls as methods, never wrappers)
# ============================================================
try:
    from pymol import cmd
    from pymol.Qt import QtWidgets
    from aamatch import game_window, setup_window, wizard

    app = QtWidgets.QApplication.instance()
    if app is None:
        app = QtWidgets.QApplication(['aamatch-smoke-16'])

    dlg = setup_window.SetupWindow()
    tab = dlg.game_tab
    baseline_a = cmd.get_names('objects')

    # ---- A1: construction inventory ---------------------------------
    check('A1: btn_hint + btn_confirm + btn_skip_menu exist with exact '
          'texts',
          tab.btn_hint.text() == 'Hint'
          and tab.btn_confirm.text() == 'Confirm'
          and tab.btn_skip_menu.text() == 'Skip / Give Up',
          'texts=%r %r %r' % (tab.btn_hint.text(),
                              tab.btn_confirm.text(),
                              tab.btn_skip_menu.text()))
    check('A1: btn_skip_menu is a QToolButton in InstantPopup mode',
          isinstance(tab.btn_skip_menu, QtWidgets.QToolButton)
          and tab.btn_skip_menu.popupMode()
          == QtWidgets.QToolButton.InstantPopup,
          'mode=%r' % (tab.btn_skip_menu.popupMode(),))
    menu = tab.btn_skip_menu.menu()
    acts = menu.actions() if menu is not None else []
    check("A1: 2-action menu ('Skip Molecule' / 'Give Up...')",
          menu is not None and len(acts) == 2
          and [a.text() for a in acts] == ['Skip Molecule',
                                           'Give Up...'],
          'actions=%r' % ([a.text() for a in acts],))
    check('A1: tooltips non-empty on all lifecycle controls',
          bool(tab.btn_hint.toolTip())
          and bool(tab.btn_confirm.toolTip())
          and bool(tab.btn_skip_menu.toolTip())
          and bool(tab.act_skip.toolTip())
          and bool(tab.act_giveup.toolTip()), '')
    # The button row = the sub-layout holding btn_hint; the stretch
    # stays LAST (timer-row no-reflow, 05-06 OQ-1).
    btn_row_layout = None
    lay = tab.layout()
    for i in range(lay.count()):
        sub = lay.itemAt(i).layout()
        if sub is None:
            continue
        for j in range(sub.count()):
            if sub.itemAt(j).widget() is tab.btn_hint:
                btn_row_layout = sub
    row_ok = False
    if btn_row_layout is not None:
        ws = [btn_row_layout.itemAt(j).widget()
              for j in range(btn_row_layout.count())]
        last = btn_row_layout.itemAt(btn_row_layout.count() - 1)
        row_ok = (ws[:3] == [tab.btn_hint, tab.btn_confirm,
                             tab.btn_skip_menu]
                  and ws[-1] is None
                  and last.spacerItem() is not None)
    check('A1: button row order Hint/Confirm/Skip-GiveUp, stretch LAST',
          row_ok, 'row-layout=%r' % (btn_row_layout,))
    tab_fresh = game_window.GameTab(None)
    check("A1: fresh-construction placeholders '0:00' / 'Required: -' "
          '(the PART I2 pin class)',
          tab_fresh._timer_label.text() == '0:00'
          and tab_fresh._required_label.text() == 'Required: -',
          'fresh=%r/%r' % (tab_fresh._timer_label.text(),
                           tab_fresh._required_label.text()))

    # ---- A2: live game through the countdown drive -------------------
    wiz = gamestart.start_game(activate=False)
    tab.start_countdown(wiz)
    for _ in range(4):
        tab._countdown_tick()
    lines_a2 = tab._info_log.toPlainText().splitlines()
    check('A2: GO pushed THAT wizard; float anchor; 1 Hz running',
          cmd.get_wizard() is wiz
          and isinstance(engine._current_game().timer_anchor, float)
          and tab._timer.isActive(),
          'top=%r anchor=%r'
          % (cmd.get_wizard(),
             engine._current_game().timer_anchor))
    check("A2: countdown lines + 'Level 1, molecule 1 of 2.'",
          lines_a2 == ['Get ready...', '3', '2', '1', 'GO!',
                       'Level 1, molecule 1 of 2.'],
          'lines=%r' % (lines_a2,))

    # ---- A3: the Confirm impl ----------------------------------------
    conf = tab._confirm_now()
    text_a3 = tab._info_log.toPlainText()
    check('A3: _confirm_now returns the dict (game_over False)',
          isinstance(conf, dict) and conf.get('game_over') is False,
          'conf=%r' % (conf,))
    check("A3: info box has the pinned scored line",
          'Molecule 1 of 2 scored 0.00 (total 0.00).' in text_a3, '')
    check('A3: the result_lines debrief shapes follow the header',
          'required interactions formed (score 0.00)' in text_a3
          and 'Formed: (none)' in text_a3, '')
    check('A3: the new position line landed (molecule 2 of 2)',
          'Level 1, molecule 2 of 2.' in text_a3, '')
    check('A3: the wizard really advanced (get_status molecule_pos 2)',
          cmd.get_wizard().get_status().get('molecule_pos') == 2, '')
    check('A3: _last_status baseline updated synchronously',
          isinstance(tab._last_status, dict)
          and tab._last_status.get('molecule_pos') == 2, '')

    # ---- A4: the sync-refresh proof ----------------------------------
    # Every A3 line assert already ran IMMEDIATELY after the impl call
    # above, with NO app.processEvents() in between -- a real 1 Hz tick
    # cannot fire without event processing, so the lines PROVABLY came
    # from the op's synchronous _refresh_status, not a poll.
    check('A4: zero-latency logging (A3 asserts ran pre-pump)',
          True, 'no processEvents between _confirm_now and asserts')

    # ---- A5: the Skip impl -------------------------------------------
    skip = tab._skip_now()
    text_a5 = tab._info_log.toPlainText()
    check("A5: _skip_now returns the dict (game_over False -- levels "
          "remain)",
          isinstance(skip, dict) and skip.get('game_over') is False,
          'skip=%r' % (skip,))
    check("A5: the pinned skip line + the level-2 position line",
          ('Skipped molecule 2 of 2 (partial score 0.00, total 0.00).'
           in text_a5)
          and 'Level 2, molecule 1 of 2.' in text_a5, '')
    check('A5: skip_count == 1 in the live GameState',
          engine.game_status().get('skip_count') == 1,
          'skip_count=%r' % (engine.game_status().get('skip_count'),))

    # ---- A6: the Give-Up impl + the endgame sequence -----------------
    req_before_giveup = tab._required_label.text()
    giveup = tab._giveup_now()
    summary_g = giveup.get('summary') if isinstance(giveup, dict) \
        else None
    text_a6 = tab._info_log.toPlainText()
    check('A6: _giveup_now returns the endgame tuple (game_over True)',
          isinstance(giveup, dict)
          and giveup.get('game_over') is True
          and isinstance(summary_g, dict), '')
    check("A6: the pinned gave-up line",
          'Game ended at level 2, molecule 1 of 2 (total 0.00).'
          in text_a6, '')
    check('A6: the give-up headline logged EXACTLY once '
          '(one transition home, no double-log)',
          text_a6.count('Game over -- gave up at level 2, molecule 1 '
                        'of 2.') == 1, '')
    block_ok = False
    if summary_g is not None:
        block = status_text.endgame_lines(summary_g)
        block_ok = all(line in text_a6 for line in block)
    check('A6: the full endgame_lines block present (per-level, total, '
          'time, molecules, skips)',
          block_ok and 'Skips: 1. Give-ups: 1.' in text_a6, '')
    check('A6: the 1 Hz timer is STOPPED (the tick cannot stop the '
          'clock -- v1 _on_win precedent)',
          not tab._timer.isActive(), '')
    label_ok = False
    if summary_g is not None:
        label_ok = (tab._timer_label.text()
                    == status_text.format_mss(summary_g['final_time']))
    check('A6: _timer_label pinned to the EXACT final elapsed '
          'format_mss(final_time)',
          label_ok,
          'label=%r' % (tab._timer_label.text(),))
    check('A6: the wizard is POPPED (the endgame sequence owns the '
          'pop)',
          cmd.get_wizard() is None,
          'top=%r' % (cmd.get_wizard(),))
    check('A6: required label holds its LAST required value (stopped '
          'timer -> no post-pop poll reset)',
          tab._required_label.text() == req_before_giveup
          and tab._required_label.text() != 'Required: -',
          'label=%r' % (tab._required_label.text(),))

    # ---- A7: the required-label level-change fix ---------------------
    placement.cleanup_game_objects()
    wiz2 = gamestart.start_game(activate=False)
    tab.start_countdown(wiz2)
    for _ in range(4):
        tab._countdown_tick()
    tab._confirm_now()           # molecule 1 of level 1
    conf2 = tab._confirm_now()   # molecule 2 of level 1 -> level advance
    st2 = cmd.get_wizard().get_status()
    check('A7: two confirms advanced to LEVEL 2 (same instance on the '
          'stack)',
          isinstance(conf2, dict)
          and conf2.get('advanced') == 'level'
          and conf2.get('game_over') is False
          and st2.get('level_pos') == 2
          and cmd.get_wizard() is wiz2,
          'advanced=%r level_pos=%r'
          % (conf2 and conf2.get('advanced'), st2.get('level_pos')))
    check('A7: required label == required_display(level-2 required) '
          '(level_pos-aware refresh; molecule_id repeats across '
          'levels)',
          tab._required_label.text()
          == status_text.required_display(st2['required']),
          'label=%r' % (tab._required_label.text(),))

    # ---- A8: wrapper-gate proof (impls with NO wizard -> None) -------
    tab.cancel_pending_start()
    tab._timer.stop()            # defensive: no 1 Hz tick over no-game
    cmd.set_wizard()             # done pop of wiz2
    placement.cleanup_game_objects()
    text_a8_pre = tab._info_log.toPlainText()
    names_a8_pre = cmd.get_names('objects')
    gate_none = (tab._confirm_now() is None
                 and tab._skip_now() is None
                 and tab._giveup_now() is None)
    check('A8: impls with no wizard return None (the isinstance gate -- '
          'the box path is [HUMAN]-only 06-10)',
          gate_none and cmd.get_wizard() is None
          and tab._info_log.toPlainText() == text_a8_pre
          and cmd.get_names('objects') == names_a8_pre, '')

    # ---- A9: restore -> the baseline scene EXACTLY -------------------
    gamestart._last_start = None
    check('A9: teardown returns the baseline scene EXACTLY + stack '
          'empty',
          list(cmd.get_names('objects')) == list(baseline_a)
          and cmd.get_wizard() is None
          and gamestart._last_start is None,
          'post=%r baseline=%r'
          % (cmd.get_names('objects'), baseline_a))
    app.processEvents()
    dlg.close()
except Exception:
    traceback.print_exc()
    check('part A tab lifecycle drive', False,
          'raised (see traceback above)')
    try:
        dlg.game_tab.cancel_pending_start()
        dlg.game_tab._timer.stop()
        cmd.set_wizard()
        placement.cleanup_game_objects()
        gamestart._last_start = None
    except Exception:
        traceback.print_exc()

# --- Verdict marker (the SOLE verdict carrier) ------------------------
print('SMOKE-16 PART A: %d checks, %d failure(s)'
      % (REC['checks'], len(failures)), flush=True)
print('=== SMOKE-16 %s ==='
      % ('FAIL: ' + ', '.join(failures) if failures else 'PASS'),
      flush=True)
