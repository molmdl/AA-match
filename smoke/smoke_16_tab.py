"""Headless SMOKE-16 - the Game tab lifecycle controls (plans
06-07/06-08, T1b).

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

PART B  restart/reset (06-08, SCORE-09/10):
        B1 construction - btn_restart ('Restart') + btn_reset_grid
        ('Reset') land AFTER btn_skip_menu, tooltips non-empty, the
        stretch stays LAST.
        B2 live game - the countdown drive -> scripted move of one AA
        -> confirm_molecule (a score exists) -> the SMOKE-08 :146-162
        marker band stamped on the whole generation (INSTANCE
        identity, never name sets).
        B3 restart impl - _restart_now() returns True; the pending
        wizard is armed and NOT on the stack; the info box is
        ['Get ready...', 'Game restarted.'] in that order (restart-
        reset D7 / the plan's must_haves sequence: the line logs
        AFTER the countdown arm so the box clear cannot wipe it).
        B4 GO - the REPLAY wizard pushed; float anchor; fresh zeros
        (scores [], skips 0, give-ups 0, game_over False); marker
        survivors 0 with exactly one fresh generation (derived count);
        the moved slot re-baked to its effective_position target
        (1e-6 + float32 ulp slack).
        B5 refusal - with gamestart._last_start = None, _restart_now()
        raises ValueError with the EXACT pinned message 'Restart: no
        game has been started yet.'; scene/log/stack untouched
        (fail-closed FIRST, restart-reset D1).
        B6 reset impl - scripted move + 90 deg rotation about the AA
        centroid (the SMOKE-06 camera=0 recipe); _reset_grid_now()
        returns True; centroid back at the target (float32 slack);
        detect() on-grid -> 0 records (the rotation PERSISTS); the
        game_reset marker stamped; the pinned line in the info box;
        GameState to_dict + timer anchor UNCHANGED (Q3b/Q7); the
        selection key unchanged.
        B7 the no-wizard gate - post-cleanup, _reset_grid_now()
        returns None silently (H-8) with scene/log untouched, then
        restore per A9.

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
from aamatch import engine, gamestart, geometry, placement  # noqa: E402
from aamatch import setup_state, status_text  # noqa: E402

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

# ============================================================
# PART B (06-08): Restart / Reset through the tab impls (T1b; ZERO
# modals -- the _X_impl drive, the same smoke-99 receipt as PART A).
# ============================================================
part_a_checks = REC['checks']

# The SMOKE-08 :146-162 instance marker band: same-seed restarts
# REBUILD the same _aam_* names, so NAME-set equality can never prove
# the old generation is gone; stamp the live generation's b-factor
# (game sentinels sit at b=-999.0, outside the band).
MARK_LOW_B, MARK_HIGH_B = -2.0, -0.5


def _game_objects_b():
    """Sorted live scene objects carrying the reserved game prefix."""
    return sorted(n for n in cmd.get_names('objects')
                  if n.startswith(geometry.GAME_PREFIX))


def _stamp_b(objects):
    """Write the marker band onto every atom of ``objects``."""
    for name in objects:
        cmd.alter(name, 'b=-1.0', space={})


def _marked_atoms_b():
    """Atoms currently carrying the generation marker (0 post-clean)."""
    return cmd.count_atoms('b > %f and b < %f'
                           % (MARK_LOW_B, MARK_HIGH_B))


def _expected_count_b(wiz):
    """Whole-scene game-object count derived from a wizard's registry
    + difficulty spec (1 + n*n per molecule) -- never hard-coded."""
    n = int(wiz._payload['levels'][0]['difficulty']['grid_n'])
    return len(wiz._registry['molecules']) * (1 + n * n)


def _slot_geometry_b(slot_id):
    """(object, effective_position target) for a molecule-0 slot,
    derived from the LIVE payload/registry (seed-replay invariant)."""
    mol = engine._registry['molecules'][0]
    obj = mol['slots'][slot_id][0]
    mol_payload = engine._payload['levels'][0]['molecules'][0]
    slot_payload = None
    for sp in mol_payload['grid']['slots']:
        if sp['slot_id'] == slot_id:
            slot_payload = sp
            break
    offset = (mol_payload.get('placement') or {}).get(
        'offset', (0.0, 0.0, 0.0))
    target = placement.effective_position(
        slot_payload['grid_pose']['position'], offset)
    return obj, target


dlg2 = None
try:
    dlg2 = setup_window.SetupWindow()
    tab2 = dlg2.game_tab
    baseline_b = cmd.get_names('objects')

    # ---- B1: construction inventory --------------------------------
    btn_row_b = None
    lay2 = tab2.layout()
    for i in range(lay2.count()):
        sub2 = lay2.itemAt(i).layout()
        if sub2 is None:
            continue
        for j in range(sub2.count()):
            if sub2.itemAt(j).widget() is tab2.btn_hint:
                btn_row_b = sub2
    row_b_ok = False
    if btn_row_b is not None:
        ws_b = [btn_row_b.itemAt(j).widget()
                for j in range(btn_row_b.count())]
        last_b = btn_row_b.itemAt(btn_row_b.count() - 1)
        row_b_ok = (ws_b[:5] == [tab2.btn_hint, tab2.btn_confirm,
                                 tab2.btn_skip_menu, tab2.btn_restart,
                                 tab2.btn_reset_grid]
                    and ws_b[-1] is None
                    and last_b.spacerItem() is not None)
    check("B1: btn_restart ('Restart') + btn_reset_grid ('Reset') "
          'exist',
          tab2.btn_restart.text() == 'Restart'
          and tab2.btn_reset_grid.text() == 'Reset',
          'texts=%r %r' % (tab2.btn_restart.text(),
                           tab2.btn_reset_grid.text()))
    check('B1: tooltips non-empty on the new buttons',
          bool(tab2.btn_restart.toolTip())
          and bool(tab2.btn_reset_grid.toolTip()), '')
    check('B1: row order Hint/Confirm/Skip-GiveUp/Restart/Reset, '
          'stretch LAST', row_b_ok, '')

    # ---- B2: live game, move+confirm, stamp the generation ----------
    wiz_b = gamestart.start_game(activate=False)
    tab2.start_countdown(wiz_b)
    for _ in range(4):
        tab2._countdown_tick()
    slot_b0 = sorted(engine._registry['molecules'][0]['slots'])[0]
    obj_b0, target_b = _slot_geometry_b(slot_b0)
    cmd.select('sele', '%s and name CA' % obj_b0)
    wiz_b.do_select('sele')
    wiz_b.move_to((target_b[0] + 3.0, target_b[1] + 5.0,
                   target_b[2] - 2.0))
    conf_b = wiz_b.confirm_molecule()
    gen_b = _game_objects_b()
    _stamp_b(gen_b)
    check('B2: live game with a score recorded pre-restart',
          cmd.get_wizard() is wiz_b
          and isinstance(conf_b, dict)
          and len(engine.game_status().get('molecule_scores')
                  or []) == 1,
          'scores=%r'
          % (engine.game_status().get('molecule_scores'),))
    check('B2: marker band stamped on the whole generation (> 0 '
          'marked atoms over the derived object count)',
          _marked_atoms_b() > 0
          and len(gen_b) == _expected_count_b(wiz_b),
          'marked=%d objects=%d expect=%d'
          % (_marked_atoms_b(), len(gen_b), _expected_count_b(wiz_b)))

    # ---- B3: the restart impl (arm + line placement) ----------------
    r_restart = tab2._restart_now()
    pending_b = tab2._pending_wizard
    lines_b3 = tab2._info_log.toPlainText().splitlines()
    check('B3: _restart_now returns True; the replay wizard is armed '
          'and NOT on the stack (P-1)',
          r_restart is True
          and isinstance(pending_b, wizard.GameWizard)
          and pending_b is not wiz_b
          and cmd.get_wizard() is None,
          'pending=%r top=%r' % (pending_b, cmd.get_wizard()))
    check("B3: info box == ['Get ready...', 'Game restarted.'] (D7: "
          'the line logs AFTER the countdown arm)',
          lines_b3 == ['Get ready...', 'Game restarted.'],
          'lines=%r' % (lines_b3,))

    # ---- B4: GO on the replay (fresh game, fresh generation) --------
    for _ in range(4):
        tab2._countdown_tick()
    gs_b = engine.game_status()
    check('B4: GO pushed the REPLAY wizard; float anchor; fresh zeros '
          '(scores [], skips 0, give-ups 0, game_over False)',
          cmd.get_wizard() is pending_b
          and isinstance(engine._current_game().timer_anchor, float)
          and len(gs_b.get('molecule_scores') or []) == 0
          and gs_b.get('skip_count') == 0
          and gs_b.get('giveup_count') == 0
          and gs_b.get('game_over') is False,
          'anchor=%r scores=%r skip=%r giveup=%r over=%r'
          % (engine._current_game().timer_anchor,
             gs_b.get('molecule_scores'), gs_b.get('skip_count'),
             gs_b.get('giveup_count'), gs_b.get('game_over')))
    check('B4: marker-band survivors == 0 (old generation dead) with '
          'exactly one fresh generation (derived count)',
          _marked_atoms_b() == 0
          and len(_game_objects_b()) == _expected_count_b(pending_b),
          'marked=%d objects=%d expect=%d'
          % (_marked_atoms_b(), len(_game_objects_b()),
             _expected_count_b(pending_b)))
    obj_b0_new, target_b_new = _slot_geometry_b(slot_b0)
    cen_b = geometry.centroid_of(obj_b0_new)
    dev_b = 0.0
    tol_b = 0.0
    for i in range(3):
        dev_b = max(dev_b, abs(cen_b[i] - target_b_new[i]))
        tol_b = max(tol_b,
                    placement.POSE_TOLERANCE
                    + placement.FLOAT32_ULP_REL
                    * max(abs(cen_b[i]), abs(target_b_new[i])))
    check('B4: the previously-moved slot re-bakes to the '
          'effective_position target (1e-6 + ulp slack)',
          dev_b <= tol_b, 'dev=%g tol=%g' % (dev_b, tol_b))

    # ---- B5: the None refusal (house fail-closed FIRST) -------------
    tab2._timer.stop()
    cmd.set_wizard()
    placement.cleanup_game_objects()
    gamestart._last_start = None
    names_pre5 = cmd.get_names('objects')
    log_pre5 = tab2._info_log.toPlainText()
    exc_b = None
    try:
        tab2._restart_now()
    except ValueError as exc_caught:
        exc_b = exc_caught
    check('B5: _restart_now with _last_start None raises ValueError '
          'with the EXACT pinned message',
          exc_b is not None
          and str(exc_b) == 'Restart: no game has been started yet.',
          'exc=%r' % (exc_b,))
    check('B5: the refusal leaves scene + log + stack untouched '
          '(fail-closed FIRST)',
          cmd.get_names('objects') == names_pre5
          and tab2._info_log.toPlainText() == log_pre5
          and cmd.get_wizard() is None, '')
    gamestart._last_start = None    # restore per the plan's tail

    # ---- B6: the reset impl (mechanism + invariants + marker) -------
    wiz_r = gamestart.start_game(activate=False)
    tab2.start_countdown(wiz_r)
    for _ in range(4):
        tab2._countdown_tick()
    slot_r0 = sorted(engine._registry['molecules'][0]['slots'])[0]
    obj_r0, target_r = _slot_geometry_b(slot_r0)
    cmd.select('sele', '%s and name CA' % obj_r0)
    wiz_r.do_select('sele')
    sel_pre6 = wiz_r.get_status().get('selected') or {}
    target_tuple = (target_r[0], target_r[1], target_r[2])
    wiz_r.move_to((target_tuple[0] + 3.0, target_tuple[1] + 5.0,
                   target_tuple[2] - 2.0))
    # Scripted rotation (the SMOKE-06 recipe): selection-form
    # cmd.rotate(camera=0) about the AA centroid -- bakes a real
    # orientation residual the reset must PRESERVE.
    cen_moved6 = geometry.centroid_of(obj_r0)
    cmd.rotate([0.0, 1.0, 0.0], 90.0, obj_r0, camera=0,
               origin=list(cen_moved6))
    moved_dev6 = max(abs(geometry.centroid_of(obj_r0)[i]
                         - target_tuple[i]) for i in range(3))
    check('B6: scripted move lands the AA off-grid pre-reset (> 1 A)',
          moved_dev6 > 1.0, 'dev=%g' % (moved_dev6,))
    gs_pre6 = engine.game_status()
    anchor_pre6 = engine._current_game().timer_anchor
    r_reset = tab2._reset_grid_now()
    check('B6: _reset_grid_now returns True (the dispatch fired)',
          r_reset is True, 'ret=%r' % (r_reset,))
    cen_post6 = geometry.centroid_of(obj_r0)
    dev_r6 = 0.0
    tol_r6 = 0.0
    for i in range(3):
        dev_r6 = max(dev_r6, abs(cen_post6[i] - target_tuple[i]))
        tol_r6 = max(tol_r6,
                     placement.POSE_TOLERANCE
                     + placement.FLOAT32_ULP_REL
                     * max(abs(cen_post6[i]), abs(target_tuple[i])))
    check('B6: the moved AA centroid is back at the '
          'effective_position target (float32 slack class)',
          dev_r6 <= tol_r6, 'dev=%g tol=%g' % (dev_r6, tol_r6))
    records_r6 = engine.detect()
    check('B6: detect() on-grid -> 0 records (the 90 deg rotation '
          'PERSISTS through the position replay)',
          len(records_r6) == 0, 'records=%d' % (len(records_r6),))
    st_r6 = wiz_r.get_status()
    ev_r6 = st_r6.get('last_event') or {}
    check("B6: last_event kind is 'game_reset' (int seq)",
          ev_r6.get('kind') == 'game_reset'
          and isinstance(ev_r6.get('seq'), int),
          'kind=%r seq=%r' % (ev_r6.get('kind'), ev_r6.get('seq')))
    check('B6: the info box carries the pinned reset line',
          'Amino acids reset to grid positions (orientations kept).'
          in tab2._info_log.toPlainText(), '')
    gs_post6 = engine.game_status()
    check('B6: GameState to_dict UNCHANGED (scores/counters/anchor '
          'untouched -- Q3b)',
          gs_post6 == gs_pre6,
          'changed=%s'
          % (sorted(k for k in gs_post6
                    if gs_post6.get(k) != gs_pre6.get(k)),))
    check('B6: timer anchor UNCHANGED float (Q7 -- the timer keeps '
          'running)',
          isinstance(engine._current_game().timer_anchor, float)
          and engine._current_game().timer_anchor == anchor_pre6,
          'anchor=%r pre=%r'
          % (engine._current_game().timer_anchor, anchor_pre6))
    sel_post6 = st_r6.get('selected') or {}
    check('B6: the selection key is unchanged (selection persists '
          'through the replay)',
          sel_pre6.get('slot_id') == slot_r0
          and sel_post6.get('slot_id') == sel_pre6.get('slot_id')
          and sel_post6.get('object') == sel_pre6.get('object'),
          'pre=%r post=%r'
          % (sel_pre6.get('slot_id'), sel_post6.get('slot_id')))

    # ---- B7: the no-wizard silent gate (H-8) + restore --------------
    tab2.cancel_pending_start()
    tab2._timer.stop()
    cmd.set_wizard()
    placement.cleanup_game_objects()
    gamestart._last_start = None
    names_pre7 = cmd.get_names('objects')
    log_pre7 = tab2._info_log.toPlainText()
    r_none = tab2._reset_grid_now()
    check('B7: _reset_grid_now post-cleanup returns None silently '
          '(H-8), scene + log untouched',
          r_none is None
          and cmd.get_wizard() is None
          and cmd.get_names('objects') == names_pre7
          and tab2._info_log.toPlainText() == log_pre7, '')
    check('B7: teardown returns the baseline scene EXACTLY + stack '
          'empty',
          list(cmd.get_names('objects')) == list(baseline_b)
          and cmd.get_wizard() is None
          and gamestart._last_start is None,
          'post=%r baseline=%r'
          % (cmd.get_names('objects'), baseline_b))
    app.processEvents()
    dlg2.close()
except Exception:
    traceback.print_exc()
    check('part B restart/reset drive', False,
          'raised (see traceback above)')
    try:
        if dlg2 is not None:
            dlg2.game_tab.cancel_pending_start()
            dlg2.game_tab._timer.stop()
        cmd.set_wizard()
        placement.cleanup_game_objects()
        gamestart._last_start = None
    except Exception:
        traceback.print_exc()

# --- Verdict marker (the SOLE verdict carrier) ------------------------
print('SMOKE-16 PART A: %d checks; PART B: %d checks; total %d, %d '
      'failure(s)'
      % (part_a_checks, REC['checks'] - part_a_checks, REC['checks'],
         len(failures)), flush=True)
print('=== SMOKE-16 %s ==='
      % ('FAIL: ' + ', '.join(failures) if failures else 'PASS'),
      flush=True)
