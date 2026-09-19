"""Headless smoke 14 - the status-surface READ path (plan 05-07, T1a)
+ the status-surface WIRING drive (plan 05-10, T1b).

Run (from WSL, repo root):
    bash smoke/run_smoke.sh smoke/smoke_14_status_surface.py 120
Verdict is carried by the printed marker (exit codes cannot carry
verdicts through the cmd.exe wrapper): grep '=== SMOKE-14 PASS ==='.

Proves the two additive status accessors of the Phase-5 status access
path (05-RESEARCH-status-surface.md, researcher B's Q6) headlessly in
REAL PyMOL. The Game status tab must NEVER reach engine/wizard privates
and must NEVER push callbacks onto the wizard (session save pickles the
whole wizard stack -- wizarding.py:175-180; wizard.py contract 2), so
everything the tab polls is plain data behind these public accessors:

T1a (THIS smoke, always runs, no dialog):
PART 1  accessors -- engine.game_status() raises EngineError BEFORE
        any game (the _current_game guard, engine.py:98-103); after
        gamestart.start_game() (defaults -- the default path activates,
        fine for the accessor drive), GameWizard.get_status() returns
        the _state_dict shape PLUS the 05-07 additive level keys
        (level_pos/level_total), is plain data (json.dumps succeeds --
        no Qt objects/callables can reach the tab), carries the right
        molecule counting (molecule_pos == 1, molecule_total ==
        len(registry['molecules'])), and is mutation-free across calls
        (s2 == status); engine.game_status() then returns the EXACT
        7-key GameState.to_dict() shape with molecule_scores == [].
        timer_anchor tolerance is UNCONDITIONAL (None or float): same-
        wave plan 05-05 makes the DEFAULT start_game path anchor the
        timer at activation, so a merged-tree regression run may
        legitimately read a float here.
PART 2  restore -- Done (canonical cmd.set_wizard()) +
        placement.cleanup_game_objects() returns the scene to the
        pre-start snapshot EXACTLY.

T1b (PARTs 3-4, the 05-10 status-surface WIRING drive; the 04-01 probe
verdict is PASS (platform=offscreen), so these RUN; the GameTab is
constructed STANDALONE via game_window.GameTab(None) -- no dialog
needed; NO modals anywhere; the countdown/tick are driven AS METHODS
and processEvents is NEVER pumped between start_countdown and the
tick drive):
PART 3  import gate (ALWAYS -- mirrors SMOKE-11's PART A):
        aamatch.game_window imports headless; GameTab exists.
PART 4  the surface drive:
        4.1/4.2 shell: the box is read-only, _log('test line') lands,
        labels start '0:00' / 'Required: -'.
        4.3 the no-wizard branch (FIRST, before any start_game in this
        part): a fresh tab's _refresh_status resets 'Required: -' and
        clears _last_status.
        4.4 deferred start: start_game(activate=False) ->
        start_countdown (n == 3, defensive) -> 4 direct _countdown_tick
        drives -> _timer.stop() IMMEDIATELY (hermetic -- the real 1 s
        member QTimer must not fire afterwards and shift the line
        counts) -> the level line 'Level 1, molecule 1 of N.' IS in
        the box (from _begin_play) + the label is a required_display
        string + _last_status a plain dict.
        4.5 first-observation silence: _refresh_status adds NO lines
        (pitfall 4 -- _begin_play seeded the baseline).
        4.6 selection event: scripted pick (the SMOKE-07 recipe:
        cmd.select('sele', '<slot object> and name CA') + do_select)
        -> exactly ONE 'Selected: slot %s (%s).' line; re-poll adds
        none (same-slot dedupe).
        4.7 error event + sticky dedupe: pop the game; fresh default
        game + fresh tab -> first _refresh_status silent with the
        label set + baseline seeded; a no-selection nudge_cam (the
        public movement handler -- _current_object sets _error) ->
        exactly ONE 'ERROR:' line; the SAME error again -> no new
        line (sticky dedupe, pitfall 3).
        4.8 both required modes from LIVE deferred-start games:
        EXCLUSIVE setup -> 'Required: any 1 interaction'; UNSET setup
        (DEFAULTS) -> the list-mode 'Required: N interaction...'
        prefix (N = the live items count).
        4.9 the scoring reserve (structural form; the exhaustive
        no-score battery is WSL-pinned in tests/test_status_text.py):
        no 'score' substring across every driven box.
        restore: cancel + pop + cleanup -> baseline scene EXACTLY +
        stack empty.

The PART count grows additively; the verdict marker stays the sole
carrier.

Conventions (frozen Phase 1, kept): anchor repo root via sys.argv
first / cwd fallback (never __file__); import aamatch directly (module
identity 'aamatch'); every print on ONE line and flushed; check details
built from already-known data only (the 03-04 eager-detail lesson --
never call into the code under test to build an assert message).

Python floor: runs inside PyMOL's Windows Python (3.9); written 3.6-safe.
"""
import json
import os
import sys
import traceback

# QT_QPA_PLATFORM MUST be set BEFORE any pymol.Qt import (the offscreen
# recipe the 04-01 probe proved, SMOKE-11's PART A contract) -- the T1b
# parts construct a GameTab standalone under PyMOL's Python.
os.environ['QT_QPA_PLATFORM'] = 'offscreen'


def _find_repo_root():
    """Anchor the repo root WITHOUT trusting __file__ (01-07 discovery:
    inside a -cq script __file__ points at pymol/__init__.py)."""
    mine = 'smoke_14_status_surface.py'
    for arg in sys.argv:
        if arg.endswith(mine) and os.path.exists(arg):
            return os.path.dirname(os.path.dirname(os.path.abspath(arg)))
    return os.getcwd()


_ROOT = _find_repo_root()
print('SMOKE-ENV root:', _ROOT, flush=True)

failures = []
REC = {}


def check(name, cond, detail=''):
    print('SMOKE-14 %-44s %s %s' % (name, 'PASS' if cond else 'FAIL',
                                     detail), flush=True)
    if not cond:
        failures.append(name)


if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from pymol import cmd  # noqa: E402

import aamatch  # noqa: E402
from aamatch import engine, gamestart, placement  # noqa: E402
from aamatch.wizard import GameWizard  # noqa: E402

print('SMOKE-ENV pymol: %s' % (cmd.get_version()[0],), flush=True)
print('SMOKE-ENV python: %s' % (sys.version.split()[0],), flush=True)

_STATE_KEYS = ('molecule_id', 'molecule_pos', 'molecule_total',
               'required', 'selected', 'result', 'error',
               'level_pos', 'level_total')
_GAME_KEYS = ('current_level_index', 'current_molecule_index',
              'molecule_scores', 'skip_count', 'giveup_count',
              'timer_anchor', 'formed_types_per_molecule')

# ============================================================
# PART 0: pre-start snapshot
# ============================================================
pre_names = list(cmd.get_names('objects'))

# ============================================================
# PART 1 (T1a): the accessor drive
# ============================================================
wiz = None
try:
    # -- 1: EngineError BEFORE any game ---
    raised = None
    try:
        engine.game_status()
    except engine.EngineError as e:
        raised = str(e)
    check('game_status raises EngineError before new_game',
          raised is not None,
          'raised=%r' % (raised,))

    # -- 2: start the default game ---
    wiz = gamestart.start_game()
    check('start_game returns a GameWizard',
          isinstance(wiz, GameWizard), 'type=%r' % (type(wiz),))

    # -- 3: get_status shape + plain-data + level/molecule counting ---
    status = wiz.get_status()
    missing = [k for k in _STATE_KEYS if k not in status]
    check('get_status carries the full state shape + level keys',
          isinstance(status, dict) and not missing,
          'missing=%s' % (missing,))
    check('level counting (level_pos 1, level_total int >= 1)',
          status.get('level_pos') == 1
          and isinstance(status.get('level_total'), int)
          and status.get('level_total', 0) >= 1,
          'level_pos=%r level_total=%r'
          % (status.get('level_pos'), status.get('level_total')))
    jsonable = None
    try:
        json.dumps(status)
        jsonable = True
    except (TypeError, ValueError):
        jsonable = False
    check('status is plain data (json round-trip; contract 2)',
          jsonable is True,
          'json.dumps(status) succeeded' if jsonable else
          'json.dumps raised -- Qt/callable leaked into the snapshot')
    mtotal = len(wiz._registry['molecules'])
    check('molecule counting matches the live registry',
          status.get('molecule_pos') == 1
          and status.get('molecule_total') == mtotal,
          'molecule_pos=%r molecule_total=%r registry=%d'
          % (status.get('molecule_pos'), status.get('molecule_total'),
             mtotal))
    REC['level_total'] = status.get('level_total')
    REC['molecule_total'] = mtotal

    # -- 4: no mutation across calls ---
    s2 = wiz.get_status()
    check('repeated get_status is mutation-free (s2 == status)',
          s2 == status, '')

    # -- 5: engine.game_status exact 7-key shape ---
    gs = engine.game_status()
    check('game_status key set is EXACTLY the 7 to_dict keys',
          isinstance(gs, dict) and set(gs) == set(_GAME_KEYS),
          'keys=%s' % (sorted(gs) if isinstance(gs, dict) else type(gs),))
    anchor = gs.get('timer_anchor')
    check('timer_anchor None or float (UNCONDITIONAL 05-05 tolerance)',
          anchor is None or isinstance(anchor, float),
          'timer_anchor=%r' % (anchor,))
    check('fresh game: molecule_scores empty',
          gs.get('molecule_scores') == [],
          'molecule_scores=%r' % (gs.get('molecule_scores'),))
except Exception:
    traceback.print_exc()
    check('part 1 accessor drive', False, 'raised (see traceback above)')

# ============================================================
# PART 2: restore -- scene back to the pre-start snapshot EXACTLY
# ============================================================
try:
    if cmd.get_wizard() is not None:
        cmd.set_wizard()
    cleaned = placement.cleanup_game_objects()
    REC['teardown_deleted'] = cleaned['deleted']
    check('teardown returns the scene to pre-start EXACTLY',
          list(cmd.get_names('objects')) == pre_names,
          'deleted=%d post=%s' % (cleaned['deleted'],
                                  cmd.get_names('objects')))
except Exception:
    traceback.print_exc()
    check('part 2 teardown', False, 'raised (see traceback above)')
    placement.cleanup_game_objects()

game_window = None

# ============================================================
# PART 3 (T1b import gate -- ALWAYS; mirrors SMOKE-11's PART A)
# ============================================================
try:
    import aamatch.game_window as game_window
    check('part 3: import aamatch.game_window headless', True,
          'module-level pymol.Qt binding loaded')
    check('part 3: GameTab class exists',
          callable(getattr(game_window, 'GameTab', None)),
          'GameTab=%r' % (getattr(game_window, 'GameTab', None),))
except Exception:
    traceback.print_exc()
    check('part 3 import gate', False, 'raised (see traceback above)')

# ============================================================
# PART 4 (T1b): the status-surface WIRING drive (05-10). Standalone
# GameTab(None), drives AS METHODS, NO processEvents pumped between
# start_countdown and the tick drive, NO modals anywhere; the real
# 1 s member timers are stopped immediately after each driven GO.
# ============================================================
try:
    if game_window is None:
        raise RuntimeError('part 3 failed')
    from pymol.Qt import QtWidgets
    from aamatch import setup_state

    app = QtWidgets.QApplication.instance()
    if app is None:
        app = QtWidgets.QApplication(['aamatch-smoke-14'])
    baseline_t = list(cmd.get_names('objects'))

    # -- 4.1/4.2: standalone tab shell (PART 2 left no game live) ----
    tab = game_window.GameTab(None)
    ro = tab._info_log.isReadOnly()
    tab._log('test line')
    check("part 4.1: information box read-only + _log('test line') "
          "lands", ro and 'test line' in tab._info_log.toPlainText(),
          'readOnly=%r' % (ro,))
    check("part 4.2: shell labels '0:00' + 'Required: -'",
          tab._timer_label.text() == '0:00'
          and tab._required_label.text() == 'Required: -',
          'timer=%r required=%r' % (tab._timer_label.text(),
                                    tab._required_label.text()))

    # -- 4.3: the no-wizard branch FIRST (before any start_game in
    # this part; the branch needs NO active wizard) -------------------
    tab0 = game_window.GameTab(None)
    tab0._refresh_status()
    check("part 4.3: no-wizard refresh resets 'Required: -' + clears "
          "the baseline",
          tab0._required_label.text() == 'Required: -'
          and tab0._last_status is None,
          'label=%r last=%r' % (tab0._required_label.text(),
                                tab0._last_status))

    # -- 4.4: deferred start + countdown drive on `tab` (the box is
    # cleared by start_countdown, retiring the 4.1 test line) ---------
    wiz = gamestart.start_game(activate=False)     # frozen DEFAULTS
    tab.start_countdown(wiz)
    check('part 4.4: start_countdown arms n=3 (defensive -- a '
          'premature real tick would have shifted it)',
          tab._countdown_n == 3, 'n=%r' % (tab._countdown_n,))
    for _ in range(4):
        tab._countdown_tick()
    tab._timer.stop()            # hermetic; driven GO owns the cadence
    expect_level = 'Level 1, molecule 1 of %d.' % REC['molecule_total']
    label44 = tab._required_label.text()
    check("part 4.4: GO logged the level line + rendered the required "
          "label + seeded the baseline (_begin_play, pitfall 4)",
          expect_level in tab._info_log.toPlainText()
          and label44.startswith('Required: ')
          and label44 != 'Required: -'
          and isinstance(tab._last_status, dict),
          'level=%r label=%r last-dict=%r'
          % (expect_level, label44, isinstance(tab._last_status, dict)))

    # -- 4.5: first-observation silence (the poll only reports
    # CHANGES -- the start sequence already logged the level line) ----
    n45 = len(tab._info_log.toPlainText().splitlines())
    tab._refresh_status()
    n45b = len(tab._info_log.toPlainText().splitlines())
    check('part 4.5: first poll observation is SILENT (baseline seeded '
          'by _begin_play)', n45b == n45, 'lines %d -> %d' % (n45, n45b))

    # -- 4.6: selection event + same-slot dedupe (SMOKE-07 script
    # recipe: select by slot object + CA, then do_select) --------------
    mol46 = wiz._registry['molecules'][0]
    slot46 = sorted(mol46['slots'])[0]
    aa46 = mol46['slots'][slot46][0]
    cmd.select('sele', '%s and name CA' % aa46)
    wiz.do_select('sele')
    n46 = len(tab._info_log.toPlainText().splitlines())
    tab._refresh_status()
    lines46 = tab._info_log.toPlainText().splitlines()
    new46 = lines46[n46:]
    expect46 = 'Selected: slot %s (%s).' % (slot46, aa46)
    check("part 4.6: scripted pick -> exactly ONE 'Selected:' line",
          new46 == [expect46],
          'new=%r expect=%r' % (new46, expect46))
    tab._refresh_status()
    check('part 4.6: same-slot re-poll adds NO line (dedupe)',
          len(tab._info_log.toPlainText().splitlines()) == len(lines46),
          'lines=%d' % (len(tab._info_log.toPlainText().splitlines()),))

    # -- 4.7: error event + sticky dedupe on a FRESH default game ----
    cmd.set_wizard()                      # canonical Done pop of wiz
    placement.cleanup_game_objects()
    wiz2 = gamestart.start_game()         # fresh wizard, NO selection
    tab2 = game_window.GameTab(None)
    tab2._refresh_status()                # first observation -- silent
    label47 = tab2._required_label.text()
    n47 = len(tab2._info_log.toPlainText().splitlines())
    check('part 4.7: fresh tab first observation SILENT + label set + '
          'baseline seeded',
          n47 == 0
          and label47.startswith('Required: ')
          and label47 != 'Required: -'
          and isinstance(tab2._last_status, dict),
          'lines=%d label=%r' % (n47, label47))
    wiz2.nudge_cam(1, 0, 0)       # public movement, no selection -> error
    tab2._refresh_status()
    lines47 = tab2._info_log.toPlainText().splitlines()
    new47 = lines47[n47:]
    check("part 4.7: no-selection nudge -> exactly ONE 'ERROR:' line",
          len(new47) == 1 and new47[0].startswith('ERROR: '),
          'new=%r' % (new47,))
    wiz2.nudge_cam(1, 0, 0)       # the SAME error string again
    tab2._refresh_status()
    check('part 4.7: unchanged error string is NOT re-logged (sticky '
          'dedupe, pitfall 3)',
          len(tab2._info_log.toPlainText().splitlines()) == len(lines47),
          'lines=%d' % (len(tab2._info_log.toPlainText().splitlines()),))

    # -- 4.8: BOTH required modes from LIVE deferred-start games ------
    cmd.set_wizard()                      # pop wiz2
    placement.cleanup_game_objects()
    setup_x = setup_state.validate_state(
        {'interaction_mode': 'exclusive',
         'allowed_interactions': ['h_bond']})
    wiz3 = gamestart.start_game(setup=setup_x, activate=False)
    tab3 = game_window.GameTab(None)
    tab3.start_countdown(wiz3)
    for _ in range(4):
        tab3._countdown_tick()
    tab3._timer.stop()
    check("part 4.8: EXCLUSIVE mode -> 'Required: any 1 interaction'",
          tab3._required_label.text() == 'Required: any 1 interaction',
          'label=%r' % (tab3._required_label.text(),))

    cmd.set_wizard()                      # pop wiz3
    placement.cleanup_game_objects()
    wiz4 = gamestart.start_game(activate=False)     # DEFAULTS: unset
    tab4 = game_window.GameTab(None)
    tab4.start_countdown(wiz4)
    for _ in range(4):
        tab4._countdown_tick()
    tab4._timer.stop()
    n_items48 = len(wiz4.get_status()['required']['items'])
    prefix48 = 'Required: %d interaction' % n_items48
    check('part 4.8: UNSET mode (DEFAULTS) -> the list-mode label '
          'prefix (N = the live items count)',
          tab4._required_label.text().startswith(prefix48)
          and tab4._required_label.text() != 'Required: any 1 '
          'interaction',
          'label=%r prefix=%r' % (tab4._required_label.text(),
                                  prefix48))

    # -- 4.9: the scoring reserve (structural form; the exhaustive
    # battery is WSL-pinned in tests/test_status_text.py) --------------
    text49 = '\n'.join(t._info_log.toPlainText()
                       for t in (tab, tab2, tab3, tab4))
    check("part 4.9: NO 'score' substring in ANY driven info box "
          '(Phase-6 reserve)', 'score' not in text49, '')

    # -- restore: cancel everything + pop + cleanup + EXACT baseline --
    for t in (tab, tab2, tab3, tab4):
        t.cancel_pending_start()
        t._timer.stop()
    if cmd.get_wizard() is not None:
        cmd.set_wizard()
    cleaned_t = placement.cleanup_game_objects()
    check('part 4: restore -- baseline scene EXACTLY, stack empty',
          cmd.get_wizard() is None
          and cmd.get_names('objects') == baseline_t,
          'deleted=%d post=%s baseline=%s'
          % (cleaned_t['deleted'], cmd.get_names('objects'),
             baseline_t))
    REC['t1b'] = ('standalone tab, no-wizard branch, deferred GO + '
                  'level line + label, silent first poll, Selected + '
                  'dedupe, ERROR + sticky dedupe, both modes, reserve')
except Exception:
    traceback.print_exc()
    check('part 4 status-surface drive', False,
          'raised (see traceback above)')
    try:
        if cmd.get_wizard() is not None:
            cmd.set_wizard()
        placement.cleanup_game_objects()
    except Exception:
        traceback.print_exc()

# --- evidence summary -------------------------------------------------
print('SMOKE-ENV record: %s'
      % dict((k, v) for k, v in sorted(REC.items())), flush=True)

# --- Verdict marker (the SOLE verdict carrier) --------------------------
print('=== SMOKE-14 %s ==='
      % ('FAIL: ' + ', '.join(failures) if failures else 'PASS'),
      flush=True)
