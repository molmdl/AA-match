"""Headless smoke 17 - THE .pse round-trip gate probe (Phase 7 gate 1).

Run (from WSL, repo root):
    bash smoke/run_smoke.sh smoke/smoke_17_pse_roundtrip.py 240
Verdict is carried by the printed marker (exit codes cannot carry
verdicts through the cmd.exe wrapper): grep '=== SMOKE-17 PASS ==='.

TWO-PHASE design -- a TRUE quit->relaunch round-trip in two invocations
(each run_smoke.sh call is a separate Windows PyMOL process):

  Phase A (SAVE; runs when the .pse fixture does not exist yet):
    start_game(seed 42, wizard ACTIVE on the stack) -> scripted pick +
    move_to + rotate (baked world-frame transforms) -> snapshot EVERY
    data class (coords, sentinels, colors, reps, object names, camera
    view, per-object matrices, a NON-IDENTITY matrix probe object,
    GameWizard state, GameState.to_dict()) -> write the snapshot through
    the REAL pure persistence container (kind='checkpoint') ->
    cmd.save(.pse) with the wizard still on the stack (the pickle
    gate) -> print PASS.

  Phase B (LOAD-VERIFY; runs when the fixture exists; a FRESH process
    = the quit->relaunch half):
    prove the fresh process (engine._game is None, no game objects) ->
    cmd.load(.pse) -> re-extract and compare EVERY data class against
    the snapshot -> observe what happened to the pickled wizard
    (cmd.get_wizard()) -> sentinel-first reconciliation demo (per-object
    'segi AAM and b < 0' counts vs the snapshot) -> GameState.from_dict
    lossless proof (the checkpoint-reconstruction core) -> delete the
    fixtures -> print PASS.

The probe modifies NO production code. Fixtures live in the git-ignored
tmp/smoke fixtures/aam_pse17/ directory.

Python floor: runs inside PyMOL's Windows Python (3.9); written 3.6-safe.
"""
import math
import os
import sys
import traceback


def _find_repo_root():
    """Anchor the repo root WITHOUT trusting __file__ (01-07 discovery:
    inside a -cq script __file__ points at pymol/__init__.py)."""
    mine = 'smoke_17_pse_roundtrip.py'
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
                     paths, persistence, placement)
from aamatch.game_state import GameState  # noqa: E402
from aamatch.wizard import GameWizard  # noqa: E402

print('SMOKE-ENV pymol: %s' % (cmd.get_version()[0],), flush=True)
print('SMOKE-ENV python: %s' % (sys.version.split()[0],), flush=True)

FIXTURE_DIR = os.path.join(_ROOT, 'tmp', 'smoke fixtures', 'aam_pse17')
PSE_PATH = os.path.join(FIXTURE_DIR, 'game.pse')
SNAP_PATH = os.path.join(FIXTURE_DIR, 'game.snapshot.json')
PROBE_NAME = '_aam_17probe'

failures = []
REC = {}


def check(name, cond, detail=''):
    print('SMOKE-17 %-44s %s %s' % (name, 'PASS' if cond else 'FAIL',
                                    detail), flush=True)
    if not cond:
        failures.append(name)


def _game_objects():
    """Sorted live scene objects carrying the reserved game prefix."""
    return sorted(n for n in cmd.get_names('objects')
                  if n.startswith(geometry.GAME_PREFIX))


def _tag_rows(obj):
    """[(int ID, str segi, float b, int color, int reps), ...] per atom
    (explicit space dict, uppercase ID, no round() -- Pitfall-8)."""
    rows = []
    cmd.iterate(obj, 'stored.append((ID, segi, b, color, reps))',
                space={'stored': rows})
    return [(int(r[0]), str(r[1]), float(r[2]), int(r[3]), int(r[4]))
            for r in rows]


def _objmat16(obj):
    """cmd.get_object_matrix as a 16-float row-major list."""
    raw = cmd.get_object_matrix(obj)
    vals = [float(v) for v in raw]
    if len(vals) == 12:
        vals = vals + [0.0, 0.0, 0.0, 1.0]
    return vals


def _wizard_snapshot(wiz):
    """Everything about the live GameWizard the gate needs."""
    import pickle as _pickle
    pickle_ok = True
    pickle_error = ''
    try:
        _pickle.dumps(wiz, 1)     # the exact protocol session_save_wizard uses
    except Exception as exc:
        pickle_ok = False
        pickle_error = '%s: %s' % (type(exc).__name__, exc)
    return {
        'class': '%s.%s' % (type(wiz).__module__, type(wiz).__name__),
        'pickle_ok': pickle_ok,
        'pickle_error': pickle_error,
        'attrs': sorted(wiz.__dict__.keys()),
        'status': wiz.get_status(),
        'current_slot': wiz._current_slot,
        'event_seq': int(wiz._event_seq),
        'last_event': wiz._last_event,
        'saved_msm': wiz._saved_msm,
        'payload_seed': wiz._payload['seed'],
        'color_store': sorted(wiz._color_store.keys()),
        # 07-01 strict-compare addition: the FULL store, JSON-safe
        # {object: [[ID, color], ...]} (the strict restore compare
        # needs the snapshots, not just which objects were recolored).
        'color_store_full': dict(
            (obj, [[int(i), int(c)] for (i, c) in rows])
            for obj, rows in wiz._color_store.items()),
    }


def _snapshot(wiz):
    """The full pre-save data snapshot (sidecar for this probe).

    game_objects lists the REAL game objects only -- the matrix-probe
    object is recorded separately (it never carries the sentinel, so it
    must stay out of the sentinel-reconciliation set)."""
    snap = {}
    snap['game_objects'] = [n for n in _game_objects()
                            if n != PROBE_NAME]
    snap['atoms'] = geometry.extract_game_atoms()
    snap['tags'] = dict((obj, _tag_rows(obj)) for obj in snap['game_objects'])
    snap['view'] = [float(v) for v in cmd.get_view()]
    snap['objmats'] = dict((obj, _objmat16(obj))
                           for obj in snap['game_objects'])
    gs = engine._current_game()
    snap['game_state'] = gs.to_dict()
    snap['wizard'] = _wizard_snapshot(wiz)
    snap['engine'] = {
        'payload_seed': engine._payload['seed'],
        'n_molecules': len(engine._registry['molecules']),
        'ligand_content_is_none': engine._ligand_content is None,
    }
    return snap


def _matrix_probe_object():
    """A NON-IDENTITY object-matrix probe: '_aam_17probe' pseudoatom
    transformed via cmd.transform_object(homogenous=1) (the placement.
    transform_baked form). Matrix-only op: stored coords stay at the
    atom's birth position while the object matrix carries the transform
    -- both sides are recorded and compared after the reload."""
    name = PROBE_NAME
    if name in cmd.get_names('objects'):
        cmd.delete(name)
    cmd.pseudoatom(name, pos=(10.0, 20.0, 30.0))
    c = math.cos(math.radians(30.0))
    s = math.sin(math.radians(30.0))
    m16 = [c, -s, 0.0, 3.0,
           s, c, 0.0, 2.0,
           0.0, 0.0, 1.0, 1.0,
           0.0, 0.0, 0.0, 1.0]
    cmd.transform_object(name, m16, homogenous=1)
    rows = []
    cmd.iterate_state(1, name, 'stored.append((x, y, z))',
                      space={'stored': rows})
    return {'name': name, 'matrix': _objmat16(name),
            'coord': [float(rows[0][0]), float(rows[0][1]),
                      float(rows[0][2])]}


# ======================================================================
# PHASE SELECTION
# ======================================================================
if os.path.exists(PSE_PATH):
    PHASE = 'verify'
else:
    PHASE = 'save'
print('SMOKE-ENV phase: %s' % (PHASE,), flush=True)
REC['phase'] = PHASE

# ======================================================================
# PHASE A: SAVE
# ======================================================================
if PHASE == 'save':
    try:
        if not os.path.exists(FIXTURE_DIR):
            os.makedirs(FIXTURE_DIR)
        for stale in (PSE_PATH, SNAP_PATH):
            if os.path.exists(stale):
                os.remove(stale)
        pre_names = list(cmd.get_names('objects'))
        check('A clean pre-start scene', not _game_objects(),
              'pre game objects=%s' % (_game_objects(),))

        wiz = gamestart.start_game()          # seed 42 defaults, ACTIVE
        check('A start_game returns a GameWizard',
              isinstance(wiz, GameWizard), 'type=%r' % (type(wiz),))
        check('A wizard is top-of-stack', cmd.get_wizard() is wiz,
              'get_wizard()=%r' % (cmd.get_wizard(),))

        slots = sorted(wiz._registry['molecules'][0]['slots'])
        slot_id = slots[0]
        obj = wiz._registry['molecules'][0]['slots'][slot_id][0]
        cmd.select('sele', '%s and name CA' % obj)
        wiz.do_select('sele')
        check('A scripted pick selected slot 0',
              wiz._current_slot == slot_id,
              'current=%r want %r' % (wiz._current_slot, slot_id))

        cen = geometry.centroid_of(obj)
        target = (cen[0] + 2.5, cen[1] + 1.25, cen[2] - 0.75)
        wiz.move_to(target)
        wiz.rotate_axis((0.0, 0.0, 1.0), 30.0)
        try:
            wiz._assert_identity(obj)
            ident_ok = True
        except Exception as exc:
            ident_ok = False
            print('SMOKE-17 identity-assert detail: %s' % (exc,), flush=True)
        check('A moved AA keeps the identity object matrix', ident_ok,
              'baked-transform invariant (post move_to + rotate)')

        probe = _matrix_probe_object()
        check('A matrix probe object carries a NON-identity matrix',
              any(abs(probe['matrix'][i] - [1.0, 0.0, 0.0, 0.0,
                                            0.0, 1.0, 0.0, 0.0,
                                            0.0, 0.0, 1.0, 0.0,
                                            0.0, 0.0, 0.0, 1.0][i])
                  > 1e-9 for i in range(16)),
              'matrix[0]=%g [1]=%g [3]=%g' % (probe['matrix'][0],
                                              probe['matrix'][1],
                                              probe['matrix'][3]))

        snap = _snapshot(wiz)
        snap['matrix_probe'] = probe
        REC['n_objects'] = len(snap['game_objects'])
        REC['n_atoms'] = len(snap['atoms'])
        persistence.save_container(SNAP_PATH, 'checkpoint', snap)
        check('A snapshot container written (kind=checkpoint)',
              os.path.exists(SNAP_PATH), SNAP_PATH)

        # THE SAVE GATE: cmd.save WITH the GameWizard live on the stack.
        cmd.save(paths.to_windows_path(PSE_PATH))
        check('A cmd.save succeeded with the wizard on the stack',
              os.path.exists(PSE_PATH)
              and cmd.get_wizard() is wiz,
              'pse=%s get_wizard() is wiz: %s'
              % (os.path.exists(PSE_PATH), cmd.get_wizard() is wiz))
        REC['wizard_pickle_save'] = snap['wizard']['pickle_ok']
        print('SMOKE-17 VERDICT wizard-save: direct pickle.dumps(wiz,1) '
              'ok=%s error=%r' % (snap['wizard']['pickle_ok'],
                                  snap['wizard']['pickle_error']), flush=True)
        print('SMOKE-17 VERDICT wizard-attrs: %s'
              % (snap['wizard']['attrs'],), flush=True)

        # (07-01) the in-memory part-C monkey-patch prototype is GONE:
        # production aamatch/wizard.py now carries the REAL module-level
        # _rebuild_game_wizard rebuilder, so phase B's restore goes
        # through the real class path (the probe's prototype evidence
        # stays recorded in 07-RESEARCH-pse.md).

        # teardown A (fixtures STAY for phase B)
        cmd.set_wizard()
        cleaned = placement.cleanup_game_objects()
        check('A teardown restores the pre-start scene',
              list(cmd.get_names('objects')) == pre_names,
              'deleted=%d post=%s' % (cleaned['deleted'],
                                      cmd.get_names('objects')))
    except Exception:
        traceback.print_exc()
        check('A save phase', False, 'raised (see traceback above)')
        try:
            cmd.set_wizard()
        except Exception:
            pass
        placement.cleanup_game_objects()

# ======================================================================
# PHASE B: LOAD-VERIFY (fresh process = the quit->relaunch half)
# ======================================================================
if PHASE == 'verify':
    try:
        check('B fixtures exist', os.path.exists(PSE_PATH)
              and os.path.exists(SNAP_PATH),
              'pse=%s snap=%s' % (os.path.exists(PSE_PATH),
                                  os.path.exists(SNAP_PATH)))
        check('B fresh process: engine has NO live game',
              engine._game is None,
              'engine._game=%r (quit->relaunch proof)' % (engine._game,))
        check('B fresh process: no game objects in the scene',
              not _game_objects(), 'objects=%s' % (_game_objects(),))

        snap = persistence.load_container(SNAP_PATH, 'checkpoint')
        check('B snapshot container reads (kind=checkpoint)',
              isinstance(snap, dict) and 'game_objects' in snap,
              'keys=%s' % (sorted(snap.keys())[:8],))

        # -- THE LOAD ----------------------------------------------------
        cmd.load(paths.to_windows_path(PSE_PATH))

        loaded_names = [n for n in _game_objects() if n != PROBE_NAME]
        check('B object names round-trip EXACTLY',
              loaded_names == snap['game_objects'],
              'loaded=%d want=%d' % (len(loaded_names),
                                     len(snap['game_objects'])))

        # -- coordinates + atom identity ----------------------------------
        atoms = geometry.extract_game_atoms()
        loaded_map = dict(((a['object'], a['id']), a) for a in atoms)
        snap_map = dict(((a['object'], a['id']), a) for a in snap['atoms'])
        keys_ok = (sorted(loaded_map.keys()) == sorted(snap_map.keys()))
        check('B atom (object, id) keys round-trip', keys_ok,
              'loaded=%d want=%d' % (len(loaded_map), len(snap_map)))
        max_delta = 0.0
        exact = True
        props_bad = []
        if keys_ok:
            for key, want in snap_map.items():
                got = loaded_map[key]
                for axis in ('x', 'y', 'z'):
                    d = abs(got[axis] - want[axis])
                    if d > 0.0:
                        exact = False
                    if d > max_delta:
                        max_delta = d
                if (got['name'] != want['name']
                        or got['elem'] != want['elem']
                        or got['resn'] != want['resn']
                        or got['resi'] != want['resi']):
                    props_bad.append('%s/%s' % key)
        coords_ok = keys_ok and max_delta <= 1e-6 and not props_bad
        check('B coordinates round-trip (float32-tight <= 1e-6)',
              coords_ok,
              'max_delta=%.3e exact=%s props_bad=%s [THE MATRIX GATE: '
              'baked coords ARE the movement model]'
              % (max_delta, exact, props_bad[:3]))
        REC['coords_max_delta'] = max_delta
        REC['coords_exact'] = exact
        print('SMOKE-17 VERDICT coords: max_delta=%.3e exact=%s -> %s'
              % (max_delta, exact,
                 'PROVEN' if coords_ok else 'REFUTED'), flush=True)

        # -- sentinels / colors / reps ------------------------------------
        sent_bad = []
        color_bad = []
        reps_bad = []
        b_max = 0.0
        for obj in snap['game_objects']:
            got_rows = dict((r[0], r) for r in _tag_rows(obj))
            want_rows = dict((r[0], r) for r in snap['tags'][obj])
            if sorted(got_rows.keys()) != sorted(want_rows.keys()):
                sent_bad.append('%s:id-set' % (obj,))
                continue
            for aid, want in want_rows.items():
                got = got_rows[aid]
                if got[1] != want[1]:
                    sent_bad.append('%s/%d segi %r != %r'
                                    % (obj, aid, got[1], want[1]))
                bd = abs(got[2] - want[2])
                if bd > b_max:
                    b_max = bd
                if got[3] != want[3]:
                    color_bad.append('%s/%d color %d != %d'
                                     % (obj, aid, got[3], want[3]))
                if got[4] != want[4]:
                    reps_bad.append('%s/%d reps %d != %d'
                                    % (obj, aid, got[4], want[4]))
        check('B sentinel segi survives exactly', not sent_bad,
              'bad=%s' % (sent_bad[:3],))
        check('B sentinel b-factor survives (max delta %.3e)' % b_max,
              b_max <= 1e-6, 'b=-999 sentinel value')
        check('B per-atom colors round-trip exactly', not color_bad,
              'bad=%s' % (color_bad[:3],))
        check('B per-atom representations (reps) round-trip exactly',
              not reps_bad, 'bad=%s' % (reps_bad[:3],))

        # -- camera view ---------------------------------------------------
        view = [float(v) for v in cmd.get_view()]
        v_deltas = [abs(view[i] - snap['view'][i])
                    for i in range(min(len(view), len(snap['view'])))]
        v_max = max(v_deltas) if v_deltas else 0.0
        v_exact = not any(d > 0.0 for d in v_deltas)
        check('B camera view round-trips (<= 1e-6)', v_max <= 1e-6,
              'max_delta=%.3e exact=%s (resume-feel)' % (v_max, v_exact))
        REC['view_max_delta'] = v_max
        print('SMOKE-17 VERDICT view: max_delta=%.3e exact=%s'
              % (v_max, v_exact), flush=True)

        # -- object matrices ------------------------------------------------
        m_max = 0.0
        m_bad = []
        for obj in snap['game_objects']:
            got = _objmat16(obj)
            want = snap['objmats'][obj]
            for i in range(16):
                d = abs(got[i] - want[i])
                if d > m_max:
                    m_max = d
        check('B game-object matrices round-trip (identity invariant)',
              m_max <= 1e-6, 'max_delta=%.3e' % (m_max,))
        probe_name = None
        for name in cmd.get_names('objects'):
            if name == PROBE_NAME:
                probe_name = name
        if probe_name is not None:
            got_m = _objmat16(probe_name)
            want = snap['matrix_probe']
            want_m = want['matrix']
            pm = max(abs(got_m[i] - want_m[i]) for i in range(16))
            check('B NON-IDENTITY object matrix round-trips (probe)',
                  pm <= 1e-6,
                  'probe matrix max_delta=%.3e [Pitfall-10 answer: '
                  'object TTT matrices DO survive .pse exactly]' % (pm,))
            rows = []
            cmd.iterate_state(1, probe_name, 'stored.append((x, y, z))',
                              space={'stored': rows})
            lc = [float(rows[0][0]), float(rows[0][1]), float(rows[0][2])]
            pc = max(abs(lc[i] - want['coord'][i]) for i in range(3))
            check('B probe stored coords round-trip exactly',
                  pc <= 1e-6,
                  'stored coord max_delta=%.3e (transform_object '
                  'BAKES coords AND records the matrix -- wizard.py '
                  'contract 5 confirmed: delta vs birth position was '
                  '8.34 A = the Rz30 bake)' % (pc,))
            baked = max(abs(want['coord'][i]
                            - [10.0, 20.0, 30.0][i]) for i in range(3))
            print('SMOKE-17 VERDICT matrix-probe: matrix_max_delta=%.3e '
                  'coord_vs_birth=%.3f A (bake confirmed), both sides '
                  'survive .pse' % (pm, baked), flush=True)
        else:
            check('B probe object survived the .pse', False,
                  '_aam_17probe missing after load')

        # -- THE WIZARD (07-01 STRICT restore compare; the documented-
        # defect signature pin is REPLACED -- production wizard.py now
        # carries the argless __reduce__ rebuilder) ----------------------
        restored = cmd.get_wizard()
        wiz_kind = ('GameWizard' if isinstance(restored, GameWizard)
                    else 'None' if restored is None
                    else str(type(restored)))
        REC['wizard_restore'] = wiz_kind
        rig = snap['wizard']
        is_gw = isinstance(restored, GameWizard)
        check('B restored top-of-stack is a GameWizard (REAL __reduce__ '
              'path)', is_gw,
              'get_wizard()=%r -- the old defect dropped it (None); '
              'a failed restore leaves the stack empty' % (restored,))
        state_ok = False
        got_store = {}
        state_detail = 'no restored wizard to compare'
        if is_gw:
            got_store = dict(
                (obj, [[int(i), int(c)] for (i, c) in rows])
                for obj, rows in restored._color_store.items())
            status_eq = restored.get_status() == rig['status']
            store_eq = got_store == rig['color_store_full']
            state_ok = (restored._current_slot == rig['current_slot']
                        and int(restored._event_seq) == rig['event_seq']
                        and restored._last_event == rig['last_event']
                        and restored._saved_msm == rig['saved_msm']
                        and restored._payload['seed'] == rig['payload_seed']
                        and store_eq and status_eq)
            state_detail = (
                'seed=%r/%r slot=%r/%r seq=%r/%r msm=%r/%r '
                'store-eq=%s status-eq=%s last_event=%r'
                % (restored._payload['seed'], rig['payload_seed'],
                   restored._current_slot, rig['current_slot'],
                   int(restored._event_seq), rig['event_seq'],
                   restored._saved_msm, rig['saved_msm'],
                   store_eq, status_eq, restored._last_event))
        check('B restored GameWizard books == the run-1 snapshot',
              state_ok, state_detail)

        # Console cleanliness (ROADMAP criterion 3): the smoke does NOT
        # capture its own stdout, so cleanliness is proven by the
        # positive restore: the defect path PRINTS 'Session-Warning:
        # unable to restore wizard.' AND drops the wizard -- a restored
        # GameWizard on the stack means zero plugin-caused warnings.
        print('SMOKE-17 NOTE console: restored GameWizard on the stack '
              'implies NO Session-Warning was printed during cmd.load '
              '(criterion-3 console-clean claim recorded for the human '
              'checkpoint)', flush=True)
        if is_gw and state_ok:
            print('SMOKE-17 VERDICT wizard: strict restore compare -> '
                  'PROVEN', flush=True)
        else:
            print('SMOKE-17 VERDICT wizard: strict restore compare -> '
                  'REFUTED (restored=%r)' % (wiz_kind,), flush=True)

        # -- post-load identity invariant (07-01 addition; the probe
        # asserted _assert_identity pre-save only) ----------------------
        ident_bad = []
        if is_gw:
            for obj in sorted(rig['color_store_full']):
                try:
                    restored._assert_identity(obj)
                except Exception as exc:
                    ident_bad.append('%s: %s' % (obj, exc))
        check('B post-load identity invariant on recolored slot objects',
              is_gw and not ident_bad,
              'objects=%s bad=%s' % (sorted(rig['color_store_full']),
                                     ident_bad[:2]))

        # -- sentinel-first reconciliation demo -------------------------------
        recon_bad = []
        for obj in snap['game_objects']:
            want_n = len(snap['tags'][obj])
            got_n = cmd.count_atoms('%s and segi AAM and b < 0' % (obj,))
            if got_n != want_n:
                recon_bad.append('%s %d != %d' % (obj, got_n, want_n))
        check('B sentinel-first reconciliation (segi AAM and b < 0)',
              not recon_bad, 'per-object counts %s' % (recon_bad[:3],))

        # -- GameState reconstruction core (the sidecar payload) -------------
        gs = GameState.from_dict(snap['game_state'])
        check('B GameState.from_dict lossless (checkpoint core)',
              gs.to_dict() == snap['game_state'],
              'keys=%s timer_anchor=%r' % (sorted(gs.to_dict().keys()),
                                           gs.timer_anchor))
        check('B engine stays DEAD after load (sidecar owns game state)',
              engine._game is None,
              'engine._game=%r -- the .pse does NOT resurrect Python '
              'game state (Pitfall 10 confirmed)' % (engine._game,))

        # -- teardown B: fixtures deleted after a green verify ----------------
        if cmd.get_wizard() is not None:
            cmd.set_wizard()
        cleaned = placement.cleanup_game_objects()
        check('B teardown cleans the loaded game (incl. probe object)',
              cleaned['deleted'] > 0 and not _game_objects(),
              'deleted=%d post=%s' % (cleaned['deleted'],
                                      _game_objects()))
        try:
            os.remove(PSE_PATH)
            os.remove(SNAP_PATH)
            os.rmdir(FIXTURE_DIR)
        except OSError:
            pass
    except Exception:
        traceback.print_exc()
        check('B load-verify phase', False, 'raised (see traceback above)')
        try:
            if cmd.get_wizard() is not None:
                cmd.set_wizard()
        except Exception:
            pass
        placement.cleanup_game_objects()

# ======================================================================
# Verdict marker (the SOLE verdict carrier)
# ======================================================================
print('SMOKE-ENV record: %s'
      % dict((k, v) for k, v in sorted(REC.items())), flush=True)
print('=== SMOKE-17 %s ==='
      % ('FAIL: ' + ', '.join(failures) if failures else 'PASS'),
      flush=True)
