"""Headless smoke 20 - THE checkpoint E2E: save -> quit -> relaunch -> load.

Run (from WSL, repo root; TWICE -- the TWO-RUN contract):
    bash smoke/run_smoke.sh smoke/smoke_20_checkpoint_e2e.py 240
Verdict is carried by the printed marker (exit codes cannot carry
verdicts through the cmd.exe wrapper): grep '=== SMOKE-20 PASS ==='.
Each run prints the SAME marker (the SMOKE-17 two-process precedent).

TWO-RUN design (each run_smoke.sh call is a separate Windows PyMOL
process -- run 2 IS the quit->relaunch half):

  RUN 1 (SAVE; runs when the .aamz fixture does not exist yet):
    start_game(seed 42, wizard ACTIVE) -> scripted pick (SMOKE-07
    recipe) -> baked move_to + rotate_axis -> hint() (non-trivial
    _color_store) -> skip_molecule() (score 0.00 recorded +
    skip_count 1 + molecule advance) ->
    data = gamestart.capture_checkpoint_snapshot(elapsed=123.0) ->
    gamestart.save_checkpoint(game.aamz, data) -> snapshot the EXPECTED
    post-load facts (game_status minus timer_anchor, per-object
    centroids of the moved slot + two controls, len(engine.detect()),
    the capture-time wizard books, the sidecar registry) into a
    persistence container -> teardown -> print PASS.

  RUN 2 (VERIFY; fresh process = the relaunch):
    prove the dead start state (engine._game is None AND
    engine.game_status() raises EngineError; cmd.get_wizard() is None;
    no game objects) -> summary = gamestart.load_checkpoint(game.aamz)
    -> ADOPT branch asserts:
      summary fields (adopted True, level 1, molecule 2, game_over
      False, elapsed 123.0); restored wizard isinstance GameWizard with
      books == run 1's (tuple/list-normalized -- the pickle keeps
      in-memory tuples, the sidecar JSON keeps lists);
      engine.game_status() == saved to_dict EXCEPT timer_anchor with
      the rebase |((now - anchor) - 123.0)| <= 5.0; reconciled registry
      == the sidecar registry (modulo tuple->list); moved/control slot
      centroids within the float32-realizable tolerance; detect count
      equal; post-load identity invariant on every recolored slot;
      _last_start rebuilt (5 keys, payload-direct); CONTINUE-PLAY proof
      (pick molecule 2 slot 1 -> confirm_molecule returns a dict with
      game_over False and L0M1 recorded).
    -> FORCED-REBUILD scenario (the SMOKE-17 part-C in-memory patch
      shape): save real_pred, patch
      wizard.is_game_wizard_any_identity = lambda w: False, run
      load_checkpoint AGAIN on the same zip -> adopted False; a NEW
      GameWizard is pushed (activate(replace=0)) with books restored
      from the sidecar (resume_from), _registry == the sidecar registry
      (modulo tuple->list), get_status() a dict; the msm REPAIR landed
      in the rebuilt wizard's _saved_msm (== the sidecar saved_msm)
      while the LIVE msm is the in-game defensive 0 (the 03-03 ORDER
      LAW: activate() snapshots-then-zeroes -- a literal
      cmd.get('mouse_selection_mode') == saved_msm during live play is
      mechanically impossible, so the repair's live-value proof goes
      through ONE pop: cleanup restores _saved_msm and THEN
      cmd.get == saved_msm); real predicate restored in a try/finally.
    -> rmtree fixtures -> print PASS.

Fixtures live in the git-ignored tmp/smoke fixtures/aam_pse20/
directory. Python floor: runs inside PyMOL's Windows Python (3.9);
written 3.6-safe.
"""
import os
import sys
import time
import traceback


def _find_repo_root():
    """Anchor the repo root WITHOUT trusting __file__ (01-07 discovery:
    inside a -cq script __file__ points at pymol/__init__.py)."""
    mine = 'smoke_20_checkpoint_e2e.py'
    for arg in sys.argv:
        if arg.endswith(mine) and os.path.exists(arg):
            return os.path.dirname(os.path.dirname(os.path.abspath(arg)))
    return os.getcwd()


_ROOT = _find_repo_root()
print('SMOKE-ENV root:', _ROOT, flush=True)

if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from pymol import cmd  # noqa: E402

import aamatch  # noqa: E402
from aamatch import (engine, gamestart, geometry,  # noqa: E402
                     persistence, placement, wizard)
from aamatch.wizard import GameWizard  # noqa: E402

print('SMOKE-ENV pymol: %s' % (cmd.get_version()[0],), flush=True)
print('SMOKE-ENV python: %s' % (sys.version.split()[0],), flush=True)

FIXTURE_DIR = os.path.join(_ROOT, 'tmp', 'smoke fixtures', 'aam_pse20')
ZIP_PATH = os.path.join(FIXTURE_DIR, 'game.aamz')
SNAP_PATH = os.path.join(FIXTURE_DIR, 'game.expected.json')
ELAPSED = 123.0

failures = []
REC = {}


def check(name, cond, detail=''):
    print('SMOKE-20 %-50s %s %s' % (name, 'PASS' if cond else 'FAIL',
                                    detail), flush=True)
    if not cond:
        failures.append(name)


def _norm(value):
    """tuple->list deep normalizer: the pickle keeps in-memory tuples
    (color_store rows, last_event tuples) while the sidecar JSON keeps
    lists -- equality checks run against the normalized form."""
    if isinstance(value, tuple):
        return [_norm(v) for v in value]
    if isinstance(value, list):
        return [_norm(v) for v in value]
    if isinstance(value, dict):
        return dict((k, _norm(v)) for k, v in value.items())
    return value


def _registry_json_form(registry):
    """materialize registry -> the JSON sidecar form (smoke_18 PART-B
    conversion: tuples -> lists, pre_game_names dropped)."""
    molecules = []
    for row in registry['molecules']:
        molecules.append({
            'molecule_id': row['molecule_id'],
            'offset': [float(x) for x in row['offset']],
            'ligand': [row['ligand'][0],
                       [int(i) for i in row['ligand'][1]]],
            'slots': dict(
                (sid, [entry[0], [int(i) for i in entry[1]]])
                for sid, entry in row['slots'].items()),
        })
    return {'level_index': int(registry['level_index']),
            'molecules': molecules}


def _teardown():
    """Wizard pops (all layers) -> prefix cleanup -> _last_start None."""
    try:
        while cmd.get_wizard() is not None:
            cmd.set_wizard()
    except Exception:
        pass
    try:
        placement.cleanup_game_objects()
    except Exception:
        pass
    gamestart._last_start = None


# ======================================================================
# PHASE SELECTION
# ======================================================================
if os.path.exists(ZIP_PATH):
    PHASE = 'verify'
else:
    PHASE = 'save'
print('SMOKE-ENV phase: %s' % (PHASE,), flush=True)
REC['phase'] = PHASE

# ======================================================================
# RUN 1: SAVE
# ======================================================================
if PHASE == 'save':
    try:
        if not os.path.exists(FIXTURE_DIR):
            os.makedirs(FIXTURE_DIR)
        for stale in (ZIP_PATH, SNAP_PATH):
            if os.path.exists(stale):
                os.remove(stale)
        pre_names = list(cmd.get_names('objects'))
        check('A clean pre-start scene',
              not geometry.game_object_names(),
              'pre game objects=%s' % (geometry.game_object_names(),))

        wiz = gamestart.start_game()              # seed 42, ACTIVE
        check('A start_game returns a GameWizard',
              isinstance(wiz, GameWizard), 'type=%r' % (type(wiz),))
        check('A wizard is top-of-stack', cmd.get_wizard() is wiz,
              'get_wizard()=%r' % (cmd.get_wizard(),))

        slots = sorted(wiz._registry['molecules'][0]['slots'])
        slot_id = slots[0]
        obj = wiz._registry['molecules'][0]['slots'][slot_id][0]
        cmd.select('sele', '%s and name CA' % obj)
        wiz.do_select('sele')
        cmd.deselect()
        check('A scripted pick selected slot %s' % (slot_id,),
              wiz._current_slot == slot_id,
              'current=%r want %r' % (wiz._current_slot, slot_id))

        cen = geometry.centroid_of(obj)
        wiz.move_to((cen[0] + 2.5, cen[1] + 1.25, cen[2] - 0.75))
        wiz.rotate_axis((0.0, 0.0, 1.0), 30.0)
        try:
            wiz._assert_identity(obj)
            ident_ok = True
        except Exception as exc:
            ident_ok = False
            print('SMOKE-20 identity-assert detail: %s' % (exc,),
                  flush=True)
        check('A moved AA keeps the identity object matrix', ident_ok,
              'baked-transform invariant (post move_to + rotate)')

        hint_result = wiz.hint()
        check('A hint() recolored candidates (non-trivial books)',
              bool(hint_result) and bool(wiz._color_store),
              'store_objects=%d' % (len(wiz._color_store),))

        skip_result = wiz.skip_molecule()
        gs1 = engine.game_status()
        check('A skip_molecule recorded a partial + advanced',
              bool(skip_result)
              and bool(gs1['score_per_molecule'])
              and gs1['skip_count'] == 1
              and gs1['current_molecule_index'] == 1,
              'scores=%s skip_count=%r mol_index=%r'
              % (sorted(gs1['score_per_molecule']),
                 gs1['skip_count'], gs1['current_molecule_index']))
        check('A skip advance cleared the selection',
              wiz._current_slot is None,
              'current_slot=%r' % (wiz._current_slot,))

        # -- capture + save -------------------------------------------
        data = gamestart.capture_checkpoint_snapshot(elapsed=ELAPSED)
        check('A snapshot captured with elapsed == 123.0 (VERBATIM)',
              isinstance(data, dict)
              and data['elapsed_at_save'] == ELAPSED,
              '%r' % (data.get('elapsed_at_save') if isinstance(data, dict)
                      else data,))
        detect_n = len(engine.detect())
        gs_stripped = dict(gs1)
        gs_stripped.pop('timer_anchor', None)
        m1_slots = sorted(wiz._registry['molecules'][0]['slots'])
        m2_slots = sorted(wiz._registry['molecules'][1]['slots'])
        ctrl1 = wiz._registry['molecules'][0]['slots'][m1_slots[1]][0]
        ctrl2 = wiz._registry['molecules'][1]['slots'][m2_slots[0]][0]
        centroids = dict(
            (name, [float(v) for v in geometry.centroid_of(name)])
            for name in (obj, ctrl1, ctrl2))
        expected = {
            'game_state': _norm(gs_stripped),   # timer-anchor stripped
            'centroids': centroids,
            'detect_n': int(detect_n),
            'books': data['wizard'],
            'registry': data['registry'],
            'seed_row': [obj, ctrl1, ctrl2],
        }
        final = gamestart.save_checkpoint(ZIP_PATH, data)
        check('A save_checkpoint wrote the .aamz archive',
              os.path.exists(final), 'final=%s' % (final,))
        persistence.save_container(SNAP_PATH, 'checkpoint', expected)
        check('A expected-facts container written',
              os.path.exists(SNAP_PATH), SNAP_PATH)
        REC['n_detect'] = detect_n
        REC['n_books_objects'] = len(data['wizard']['color_store'])
        print('SMOKE-20 RUN1 saved: %s (detect=%d books_objects=%d '
              'elapsed=%.1f)' % (final, detect_n,
                                 len(data['wizard']['color_store']),
                                 ELAPSED), flush=True)

        # -- teardown run 1 (fixtures STAY for run 2) -------------------
        _teardown()
        check('A teardown restores the pre-start scene',
              list(cmd.get_names('objects')) == pre_names,
              'post=%s' % (cmd.get_names('objects'),))
    except Exception:
        traceback.print_exc()
        check('A save run', False, 'raised (see traceback above)')
        _teardown()

# ======================================================================
# RUN 2: VERIFY (fresh process = the quit->relaunch half)
# ======================================================================
if PHASE == 'verify':
    try:
        check('B fixtures exist',
              os.path.exists(ZIP_PATH) and os.path.exists(SNAP_PATH),
              'zip=%s snap=%s' % (os.path.exists(ZIP_PATH),
                                  os.path.exists(SNAP_PATH)))
        check('B fresh process: engine has NO live game',
              engine._game is None,
              'engine._game=%r (quit->relaunch proof)' % (engine._game,))
        dead_raise = False
        try:
            engine.game_status()
        except engine.EngineError:
            dead_raise = True
        check('B fresh process: game_status() refuses EngineError',
              dead_raise, 'the dead-start safe probe')
        check('B fresh process: no wizard on the stack',
              cmd.get_wizard() is None,
              'get_wizard()=%r' % (cmd.get_wizard(),))
        check('B fresh process: no game objects in the scene',
              not geometry.game_object_names(),
              'objects=%s' % (geometry.game_object_names(),))
        snap = persistence.load_container(SNAP_PATH, 'checkpoint')
        check('B expected-facts container reads back',
              isinstance(snap, dict)
              and sorted(snap.keys()) == ['books', 'centroids',
                                          'detect_n', 'game_state',
                                          'registry', 'seed_row'],
              'keys=%s' % (sorted(snap.keys()),))
        books = snap['books']
        saved_msm = books.get('saved_msm')

        # -- THE LOAD (ADOPT branch) -------------------------------------
        summary = gamestart.load_checkpoint(ZIP_PATH)
        check('B load_checkpoint summary fields (adopt path)',
              isinstance(summary, dict)
              and summary.get('adopted') is True
              and summary.get('level_pos') == 1
              and summary.get('molecule_pos') == 2
              and summary.get('game_over') is False
              and summary.get('elapsed_at_save') == ELAPSED,
              '%s' % (summary,))
        restored = cmd.get_wizard()
        check('B restored top-of-stack is a GameWizard (ADOPT)',
              isinstance(restored, GameWizard),
              'get_wizard()=%r' % (restored,))
        books_eq = (isinstance(restored, GameWizard)
                    and _norm(restored.snapshot_books()) == _norm(books))
        check('B adopted wizard books == run-1 capture (normalized)',
              books_eq,
              '_current_slot=%r seq=%r store=%d (want None/%r/%d)'
              % (getattr(restored, '_current_slot', '?'),
                 getattr(restored, '_event_seq', '?'),
                 len(getattr(restored, '_color_store', {})),
                 books.get('event_seq'),
                 len(books.get('color_store') or {})))
        check('B adopted _current_slot is None post-skip',
              restored._current_slot is None,
              '%r' % (restored._current_slot,))
        check('B adopted _color_store non-empty (hint + pick landed)',
              bool(restored._color_store), '')

        # -- engine state: scores/counters/level module-exact ------------
        status = engine.game_status()
        got_stripped = dict(status)
        anchor = got_stripped.pop('timer_anchor', None)
        check('B game_status == saved to_dict EXCEPT timer_anchor',
              _norm(got_stripped) == snap['game_state'],
              'skip_count=%r mol=%r scores=%s'
              % (status.get('skip_count'),
                 status.get('current_molecule_index'),
                 sorted(status.get('score_per_molecule') or {})))
        drift = abs((time.time() - float(anchor)) - ELAPSED) \
            if isinstance(anchor, float) else float('nan')
        check('B timer REBASED from elapsed_at_save (|drift| <= 5.0 s)',
              isinstance(anchor, float) and drift <= 5.0,
              'now-%.3f anchor=%.6f drift=%.3f s (clock continues '
              'from the save moment)' % (time.time(), anchor or -1.0,
                                         drift))

        # -- registry reconciled == sidecar -------------------------------
        reg_json = _registry_json_form(engine._registry)
        check('B reconciled registry == the sidecar registry',
              reg_json == snap['registry'],
              'molecules=%d' % (len(reg_json['molecules']),))
        check('B adopted wizard registry == the reconciled registry',
              _norm(restored._registry) == _norm(engine._registry),
              'the adopt-with-verify condition the seam ran (normalized: '
              'materialize ids ride as sorted lists, reconcile as tuples)')

        # -- positions: moved + control slot centroids ---------------------
        bad_cen = []
        for name, want_w in snap['centroids'].items():
            got_w = geometry.centroid_of(name)
            for axis in range(3):
                slack = placement.POSE_TOLERANCE \
                    + placement.FLOAT32_ULP_REL * max(
                        abs(float(got_w[axis])), abs(float(want_w[axis])))
                if abs(float(got_w[axis]) - float(want_w[axis])) > slack:
                    bad_cen.append('%s axis %d %r != %r'
                                   % (name, axis, got_w[axis],
                                      want_w[axis]))
        check('B moved/control slot centroids round-trip (float32-tight)',
              not bad_cen, 'bad=%s' % (bad_cen[:3],))

        # -- detector-equivalence of the restored scene --------------------
        n_detect2 = len(engine.detect())
        check('B detect() record count equals run 1', 
              n_detect2 == snap['detect_n'],
              'detect=%d want %d (the restored scene is '
              'detector-equivalent)' % (n_detect2, snap['detect_n']))

        # -- post-load identity invariant on recolored slot objects --------
        ident_bad = []
        for sel_obj in sorted(books.get('color_store') or {}):
            try:
                restored._assert_identity(sel_obj)
            except Exception as exc:
                ident_bad.append('%s: %s' % (sel_obj, exc))
        check('B post-load identity invariant on recolored slots',
              not ident_bad,
              'objects=%d bad=%s'
              % (len(snap['books'].get('color_store') or {}),
                 ident_bad[:2]))

        # -- _last_start rebuilt (payload-direct Restart) -------------------
        ls = gamestart._last_start
        check('B _last_start rebuilt (5-key payload-direct tuple)',
              isinstance(ls, dict)
              and sorted(ls.keys()) == ['candidates', 'ligand_content',
                                        'payload', 'seed', 'setup']
              and ls['seed'] == 42 and ls['payload']['seed'] == 42,
              'keys=%s seed=%r'
              % (sorted(ls.keys()) if isinstance(ls, dict) else ls,
                 ls.get('seed') if isinstance(ls, dict) else None))

        # -- CONTINUE-PLAY proof: molecule 2 confirm ------------------------
        mol2 = restored._registry['molecules'][1]
        m2_first = sorted(mol2['slots'])[0]
        m2_obj = mol2['slots'][m2_first][0]
        cmd.select('sele', '%s and name CA' % m2_obj)
        restored.do_select('sele')
        cmd.deselect()
        check('B continue-play pick selected molecule-2 slot %s'
              % (m2_first,), restored._current_slot == m2_first,
              'current=%r' % (restored._current_slot,))
        result = restored.confirm_molecule()
        status2 = engine.game_status()
        check('B confirm_molecule returned game_over False',
              isinstance(result, dict) and result.get('game_over')
              is False,
              'advanced=%r' % (result.get('advanced')
                               if isinstance(result, dict) else result,))
        check('B molecules 1+2 both recorded; the game LIVES on',
              sorted(status2['score_per_molecule']) == ['L0M0', 'L0M1'],
              'scores=%s game_over=%r level=%r'
              % (sorted(status2['score_per_molecule']),
                 status2['game_over'],
                 status2['current_level_index']))
        print('SMOKE-20 VERDICT resume: adopt path books/status/pose/'
              'timer/detect/continue-play -> PROVEN', flush=True)

        # -- FORCED-REBUILD scenario (predicate patched False) --------------
        real_pred = wizard.is_game_wizard_any_identity
        wizard.is_game_wizard_any_identity = lambda w: False
        try:
            summary2 = gamestart.load_checkpoint(ZIP_PATH)
            check('C forced-rebuild: summary adopted is False',
                  isinstance(summary2, dict)
                  and summary2.get('adopted') is False,
                  '%s' % (summary2,))
            rebuilt = cmd.get_wizard()
            check('C forced-rebuild: NEW GameWizard pushed on top',
                  isinstance(rebuilt, GameWizard)
                  and rebuilt is not restored,
                  'get_wizard()=%r' % (rebuilt,))
            books2_eq = (isinstance(rebuilt, GameWizard)
                         and _norm(rebuilt.snapshot_books())
                         == _norm(books))
            check('C forced-rebuild: books restored via resume_from',
                  books2_eq,
                  'seq=%r store=%d current=%r'
                  % (getattr(rebuilt, '_event_seq', '?'),
                     len(getattr(rebuilt, '_color_store', {})),
                     getattr(rebuilt, '_current_slot', '?')))
            check('C forced-rebuild: _color_store non-empty',
                  isinstance(rebuilt, GameWizard)
                  and bool(rebuilt._color_store), '')
            reg_json2 = _registry_json_form(rebuilt._registry) \
                if isinstance(rebuilt, GameWizard) else {}
            check('C forced-rebuild: _registry == sidecar registry',
                  reg_json2 == snap['registry'],
                  'molecules=%d' % (len(reg_json2.get('molecules') or ()),
                                    ))
            status_r = rebuilt.get_status() \
                if isinstance(rebuilt, GameWizard) else None
            check('C forced-rebuild: get_status() returns a dict',
                  isinstance(status_r, dict),
              'keys=%s'
              % (sorted(status_r.keys()) if isinstance(status_r, dict)
                 else status_r,))
            # msm repair: the ORDER LAW makes a live-equality check
            # impossible (activate() snapshots-then-zeroes) -- the
            # repair's landing spot is _saved_msm, and ONE pop proves
            # cleanup restores the repaired value to the session.
            check('C forced-rebuild: _saved_msm == sidecar saved_msm',
                  rebuilt._saved_msm == saved_msm,
              'saved_msm=%r want %r (msm repair landed in the books)'
              % (rebuilt._saved_msm, saved_msm))
            live_msm = int(cmd.get('mouse_selection_mode'))
            check('C forced-rebuild: live msm is the in-game defensive 0',
                  live_msm == 0,
                  'cmd.get(mouse_selection_mode)=%d (the session '
                  'carried the save-time defensive value; the repair '
                  'owns _saved_msm not the live value)' % (live_msm,))
            cmd.set_wizard()            # pop the rebuilt wizard
            popped_msm = int(cmd.get('mouse_selection_mode'))
            check('C forced-rebuild: pop->cleanup restores the repaired '
                  'msm', popped_msm == saved_msm,
                  'post-pop msm=%d want %r' % (popped_msm, saved_msm))
            print('SMOKE-20 VERDICT resume: forced-rebuild branch '
                  '(predicate patched False) -> PROVEN', flush=True)
        finally:
            wizard.is_game_wizard_any_identity = real_pred

        # -- teardown run 2: fixtures deleted after green verify ------------
        _teardown()
        import shutil as _sh
        try:
            _sh.rmtree(FIXTURE_DIR)
        except OSError:
            pass
        check('B teardown: fixtures removed + scene clean',
              not os.path.exists(ZIP_PATH)
              and not geometry.game_object_names(),
              'zip=%s objects=%s' % (os.path.exists(ZIP_PATH),
                                     geometry.game_object_names()))
    except Exception:
        traceback.print_exc()
        check('B verify run', False, 'raised (see traceback above)')
        _teardown()

# ======================================================================
# Verdict marker (the SOLE verdict carrier)
# ======================================================================
print('SMOKE-ENV record: %s'
      % dict((k, v) for k, v in sorted(REC.items())), flush=True)
print('=== SMOKE-20 %s ==='
      % ('FAIL: ' + ', '.join(failures) if failures else 'PASS'),
      flush=True)
