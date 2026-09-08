"""Headless smoke 06 - MOVEMENT-MODEL SPIKE (Phase 3 gate probe).

Run (from WSL, repo root):  bash smoke/run_smoke.sh smoke/smoke_06_spike_movement.py 180
Verdict is carried by the printed marker (exit codes cannot carry
verdicts through the cmd.exe wrapper): grep '=== SMOKE-06 PASS ==='.

ROADMAP Phase-3 criterion 4 gate: the movement-model spike verdict --
which movement primitive composes with the Phase-2 detector (stored
coords via iterate_state) AND with engine.reset_to_grid() -- plus the
cmd.drag(wizard=0) headless behavior record and the default
editor_scheme check.

What each PART probes (all numbers printed for the research record):

PART 0  env + engine setup on the bundled dev fixtures (SMOKE-04
        pattern) + baseline: grid pose scores 0; object matrices are
        IDENTITY after materialize; the INSTALLED pymol.wizard.dragging
        source is printed (the runtime build may differ from the
        pymol-src snapshot the research cited).
PART A  Q1 COORDINATE PATH: cmd.rotate(axis_vec, angle, SELECTION,
        camera=0, origin=ring_center) -- does it bake stored
        coordinates (iterate_state-visible), keep the object matrix
        identity, and let engine.detect()/score_current() report the
        moved (qualifying) pose?
PART A2 Q4a RESET semantics: engine.reset_to_grid() after the
        rotational move (position restored, orientation residual
        recorded) and after a pure-TRANSLATION move (per-atom exact
        restore within the 02-15 float32 tolerance).
PART B  Q2/Q4b OBJECT-MATRIX PATH: cmd.rotate(..., object=obj) writes
        the TTT DISPLAY matrix (incl_ttt=0 state slot stays identity);
        stored coordinates untouched; detection blind.  Read-back
        convention pinned.  THE CONJUGATION LAW: bakes (cmd.translate /
        selection-rotate) under a matrix residue apply the requested
        world transform T in the LOCAL frame (stored_new =
        M^-1 o T o M o stored; for translations stored_shift =
        R^-1 . s) -- so engine.place_aa fails CLOSED and
        reset_to_grid either silently ignores a matrix-only move or
        fails closed when stored is off-grid.  Screen (M o stored) vs
        detector (stored) mismatch quantified.  Fold-clear escape
        hatch (matrix_copy from the identity-matrix ligand) verified
        END-TO-END.
        NOTE: the spike must NOT CALL cmd.matrix_reset / get_object_ttt
        / get_model anywhere -- the 02-15 AST audit
        (tests/test_code_audit.py) scans smoke/ call sites too (prose
        mentions outside aamatch/ are not gated).
PART D  Q5 cmd.drag headless behavior: custom wizard installed ->
        cmd.drag(sel, wizard=0): exception? wizard kept? drag armed
        (get_drag_object_name)?  button_mode side effect (edit=1
        default flips the global mouse ring via edit_mode; edit=0
        variant probed too).  cmd.drag(sel, wizard=1): wizard STACK
        semantics (get_wizard_stack at each step).  Scheme gate: the
        DEFAULT cmd.get_editor_scheme() value + a directly instantiated
        pymol.wizard.dragging.Dragging check_valid() verdict, plus the
        scheme <-> mouse-ring coupling (the scheme is DERIVED from the
        active ring, which is why cmd.drag's edit=1 flip satisfies the
        gate).
        NOTE: no real mouse exists headless -- this records API-level
        state transitions only; interactive drag feel stays a HUMAN
        checkpoint.
PART C  Q3 transform_selection / transform_object semantics on scratch
        objects: which call BAKES coordinates (and in which matrix
        layout), what each leaves in get_object_matrix (incl_ttt
        decomposition), and the matrix_mode>0 duality that makes
        transform_object write the object matrix instead.

Conventions (frozen Phase 1, kept): anchor repo root via sys.argv first
/ cwd fallback (never __file__); import aamatch directly (module
identity 'aamatch'); every print on ONE line and flushed; explicit
space dicts in every iterate (the spike reuses aamatch.geometry
helpers, which own that discipline); no round() in expressions.

Python floor: runs inside PyMOL's Windows Python (3.9); written 3.6-safe.
"""
import math
import os
import sys
import traceback


def _find_repo_root():
    """Anchor the repo root WITHOUT trusting __file__ (01-07 discovery:
    inside a -cq script __file__ points at pymol/__init__.py)."""
    mine = 'smoke_06_spike_movement.py'
    for arg in sys.argv:
        if arg.endswith(mine) and os.path.exists(arg):
            return os.path.dirname(os.path.dirname(os.path.abspath(arg)))
    return os.getcwd()


_ROOT = _find_repo_root()
print('SMOKE-ENV root:', _ROOT, flush=True)

failures = []
REC = {}                     # recorded numbers for the final summary


def check(name, cond, detail=''):
    print('SMOKE-06 %-42s %s %s' % (name, 'PASS' if cond else 'FAIL', detail),
          flush=True)
    if not cond:
        failures.append(name)


def spike(msg):
    """Per-probe verdict line (the research-doc evidence lines)."""
    print('[SPIKE] %s' % msg, flush=True)


if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from pymol import cmd  # noqa: E402

from aamatch.persistence import read_json_file  # noqa: E402
from aamatch.manifest import parse_manifest_dict, enumerate_entries  # noqa: E402
from aamatch.setup_state import validate_state  # noqa: E402
from aamatch import capability, engine, geometry, placement  # noqa: E402
from aamatch.detector import extract_features  # noqa: E402
from aamatch.thresholds import PISTACK_ANGLE_TOL_DEG  # noqa: E402

print('SMOKE-ENV pymol: %s' % (cmd.get_version()[0],), flush=True)
print('SMOKE-ENV python: %s' % (sys.version.split()[0],), flush=True)

POSE_TOL = 1e-6          # float32 pose tolerance floor (02-15)
ULP_REL = 1.1920929e-7   # float32 ulp relative slack (placement)
PLANE_TOL_DEG = 1e-3     # ring-alignment window (SMOKE-04 precedent)
CONV_TOL = 1e-3          # matrix read-back composition tolerance
IDENT_TIGHT = 1e-9       # fresh-object matrix identity
IDENT_F32 = 1e-6         # identity after float32-touching matrix ops


def _axis_tol(a, t):
    """Per-axis float32-realizable tolerance (the 02-15 pose contract)."""
    return POSE_TOL + ULP_REL * max(abs(a), abs(t))


# --- tiny vec helpers (smoke-local, SMOKE-04 set) -------------------
def _sub(a, b):
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def _add(a, b):
    return (a[0] + b[0], a[1] + b[1], a[2] + b[2])


def _scale(s, a):
    return (s * a[0], s * a[1], s * a[2])


def _dot(a, b):
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def _cross(a, b):
    return (a[1] * b[2] - a[2] * b[1],
            a[2] * b[0] - a[0] * b[2],
            a[0] * b[1] - a[1] * b[0])


def _norm(a):
    return math.sqrt(_dot(a, a))


def _unit(a):
    n = _norm(a)
    if n < 1e-12:
        raise ValueError('zero-length vector')
    return (a[0] / n, a[1] / n, a[2] / n)


def _tofloat(pt):
    return (float(pt[0]), float(pt[1]), float(pt[2]))


def _angle_between_deg(a, b):
    c = max(-1.0, min(1.0, _dot(_unit(a), _unit(b))))
    return math.degrees(math.acos(c))


def _axis_angle(n_from, n_to):
    """(unit axis, angle_deg) rotating n_from onto n_to; None axis when
    already parallel."""
    c = max(-1.0, min(1.0, _dot(n_from, n_to)))
    k_raw = _cross(n_from, n_to)
    if _norm(k_raw) < 1e-9:
        if c > 0.0:
            return None, 0.0
        ref = (1.0, 0.0, 0.0)
        if abs(_dot(n_from, ref)) > 0.9:
            ref = (0.0, 1.0, 0.0)
        return _unit(_cross(n_from, ref)), 180.0
    return _unit(k_raw), math.degrees(math.acos(c))


def _axis_perp_both(n_a, n_l):
    """Unit axis perpendicular to both ring normals (angle-change
    guarantee); falls back to any axis perpendicular to n_l when the
    normals are (near) parallel."""
    k_raw = _cross(n_a, n_l)
    if _norm(k_raw) > 1e-6:
        return _unit(k_raw)
    ref = (0.0, 0.0, 1.0)
    if abs(_dot(n_l, ref)) > 0.9:
        ref = (1.0, 0.0, 0.0)
    return _unit(_cross(n_l, ref))


def _rot_pos(p, k, ang_rad, origin):
    """Rodrigues: where atom p lands under a rotation by ang about unit
    axis k through origin (float64 expectation model)."""
    d = _sub(p, origin)
    kd = _dot(k, d)
    kxd = _cross(k, d)
    c = math.cos(ang_rad)
    s = math.sin(ang_rad)
    dp = (d[0] * c + kxd[0] * s + k[0] * kd * (1.0 - c),
          d[1] * c + kxd[1] * s + k[1] * kd * (1.0 - c),
          d[2] * c + kxd[2] * s + k[2] * kd * (1.0 - c))
    return _add(origin, dp)


def _obj_matrix(name, incl_ttt=1):
    """cmd.get_object_matrix as a 16-list (or None)."""
    m = cmd.get_object_matrix(name, incl_ttt=incl_ttt)
    if m is None:
        return None
    return [float(v) for v in m]


def _is_identity(m16, tol=IDENT_TIGHT):
    if m16 is None or len(m16) != 16:
        return False
    want = (1.0, 0.0, 0.0, 0.0,
            0.0, 1.0, 0.0, 0.0,
            0.0, 0.0, 1.0, 0.0,
            0.0, 0.0, 0.0, 1.0)
    return all(abs(m16[i] - want[i]) <= tol for i in range(16))


def _mfmt(m16):
    if not m16:
        return 'None'
    return '[' + ', '.join('%.3e' % v for v in m16) + ']'


def _coords_maxdisp(before, after):
    """Max per-axis |after - before| over two coords_of() snapshots."""
    bmap = dict((c[0], c[1:]) for c in before)
    worst = 0.0
    for (aid, x, y, z) in after:
        b = bmap.get(aid)
        if b is None:
            return float('inf')
        worst = max(worst, abs(x - b[0]), abs(y - b[1]), abs(z - b[2]))
    return worst


def _coords_close(before, after):
    """(ok, worst, worst_tol) -- per-atom per-axis 02-15 tolerance."""
    bmap = dict((c[0], c[1:]) for c in before)
    ok = True
    worst = 0.0
    worst_tol = 0.0
    for (aid, x, y, z) in after:
        b = bmap.get(aid)
        if b is None:
            return False, float('inf'), 0.0
        for (va, vt) in ((x, b[0]), (y, b[1]), (z, b[2])):
            tol = _axis_tol(va, vt)
            dev = abs(va - vt)
            if dev > worst:
                worst = dev
                worst_tol = tol
            if dev > tol:
                ok = False
    return ok, worst, worst_tol


def _apply_ttt(m16, p):
    """Compose a get_object_matrix result with a POINT, PyMOL TTT
    convention (editing.py:1985-1987): y = R.(p + pre) + post, with
    pre = m12..m14 (bottom row), post = m3,m7,m11 (last column)."""
    q = (p[0] + m16[12], p[1] + m16[13], p[2] + m16[14])
    return (m16[0] * q[0] + m16[1] * q[1] + m16[2] * q[2] + m16[3],
            m16[4] * q[0] + m16[5] * q[1] + m16[6] * q[2] + m16[7],
            m16[8] * q[0] + m16[9] * q[1] + m16[10] * q[2] + m16[11])


def _apply_hom(m16, p):
    """Standard homogeneous row-major composition (translation in the
    last column): y = R.p + (m3, m7, m11)."""
    return (m16[0] * p[0] + m16[1] * p[1] + m16[2] * p[2] + m16[3],
            m16[4] * p[0] + m16[5] * p[1] + m16[6] * p[2] + m16[7],
            m16[8] * p[0] + m16[9] * p[1] + m16[10] * p[2] + m16[11])


def _rotate3(m16, v):
    """Rotation-part-only application (for direction vectors)."""
    return (m16[0] * v[0] + m16[1] * v[1] + m16[2] * v[2],
            m16[4] * v[0] + m16[5] * v[1] + m16[6] * v[2],
            m16[8] * v[0] + m16[9] * v[1] + m16[10] * v[2])


def _remap_ligand_bonds(records, bonds, index_to_id):
    """SMOKE-04 single-ligand remap (02-09 pinned mapping)."""
    lig = sorted((r for r in records if r['side'] == 'lig'),
                 key=lambda r: r['id'])
    id_pos = dict((r['id'], i) for i, r in enumerate(lig))
    out = []
    for (i, j, order) in bonds:
        out.append((id_pos[index_to_id[i + 1]],
                    id_pos[index_to_id[j + 1]], int(order)))
    return lig, out


def _stack_names():
    """The wizard stack as class-name strings (push/pop evidence)."""
    try:
        stk = cmd.get_wizard_stack() or []
    except Exception:
        return '<unavailable>'
    return [type(w).__name__ for w in stk]


# ============================================================
# PART 0: env + engine setup + baseline
# ============================================================
pre_names = list(cmd.get_names('objects'))
scheme_default = None
try:
    check('clean pre-game scene',
          not [n0 for n0 in pre_names
               if n0.startswith(geometry.GAME_PREFIX)],
          'pre names: %s' % pre_names)

    scheme_default = int(cmd.get_editor_scheme())
    button_mode0 = int(cmd.get('button_mode'))
    try:
        matrix_mode0 = int(cmd.get('matrix_mode'))
    except Exception:
        matrix_mode0 = None
    REC['editor_scheme_default'] = scheme_default
    REC['button_mode_initial'] = button_mode0
    REC['matrix_mode_initial'] = matrix_mode0
    REC['wizard_stack_initial'] = _stack_names()
    spike('env: editor_scheme default=%d button_mode=%d matrix_mode=%s '
          'wizard_stack=%s'
          % (scheme_default, button_mode0, matrix_mode0,
             REC['wizard_stack_initial']))

    # The INSTALLED dragging wizard source may differ from the
    # pymol-src snapshot the research cited -- print the evidence.
    try:
        import pymol.wizard.dragging as _dg
        import inspect
        print('SMOKE-ENV installed dragging module: %s'
              % (getattr(_dg, '__file__', '?'),), flush=True)
        print('SMOKE-ENV installed check_valid source:')
        for ln in inspect.getsource(
                _dg.Dragging.check_valid).rstrip().splitlines():
            print('SMOKE-ENV   %s' % ln, flush=True)
    except Exception as exc:
        print('SMOKE-ENV installed-source print failed: %r' % (exc,),
              flush=True)

    benz = None
    container = read_json_file(os.path.join(
        _ROOT, 'aamatch', 'data', 'MANIFEST.json'))
    entries = enumerate_entries(parse_manifest_dict(container))
    benz_rows = [row for row in entries if row['entry_id'] == 'benzamide']
    benz = benz_rows[0] if benz_rows else None
    check('benzamide candidate', benz is not None,
          benz['file'] if benz else 'entry_id benzamide not in manifest')

    setup = validate_state({'interaction_mode': 'block_exclusive',
                            'allowed_interactions': ['pi_stacking'],
                            'molecules_per_level': 1,
                            'difficulty_levels': 3})
    payload, rows = engine.new_game(setup, 42, candidates=[benz])
    check('new_game scene untouched',
          list(cmd.get_names('objects')) == pre_names, '')
    level0 = payload['levels'][0]
    n = level0['difficulty']['grid_n']
    mol_payload = level0['molecules'][0]
    required = mol_payload['required']

    registry = engine.materialize(payload, level_index=0)
    molecule = registry['molecules'][0]
    lig_obj = molecule['ligand'][0]
    check('materialize growth',
          len(set(cmd.get_names('objects')) - set(pre_names)) == 1 + n * n,
          'want %d' % (1 + n * n))

    req_slots = [s for s in mol_payload['grid']['slots']
                 if s.get('role') == 'required'
                 and 'pi_stacking' in (s.get('can_form') or ())]
    check('one required pi_stacking slot', len(req_slots) == 1,
          '%d slot(s)' % len(req_slots))
    slot = req_slots[0]
    slot_id = slot['slot_id']
    resn = slot['aa']
    check('required slot aromatic',
          bool(capability.AA_RESIDUES[resn]['rings']),
          'aa=%s' % resn)
    aa_obj = molecule['slots'][slot_id][0]

    # Baseline: grid pose scores 0; matrices IDENTITY (Phase-2 bakes
    # never write matrices -- asserted, not assumed).
    records0 = engine.detect()
    pi0 = [r for r in records0 if r['type'] == 'pi_stacking']
    check('grid yields zero pi_stacking', not pi0,
          'records=%d pi=%d' % (len(records0), len(pi0)))
    m_aa0 = _obj_matrix(aa_obj)
    m_lig0 = _obj_matrix(lig_obj)
    check('AA matrix identity after materialize', _is_identity(m_aa0),
          'm_aa0=%s' % (_mfmt(m_aa0),))
    check('ligand matrix identity after materialize', _is_identity(m_lig0),
          'm_lig0=%s' % (_mfmt(m_lig0),))

    coords_grid = geometry.coords_of(aa_obj)
    check('grid coords snapshot', len(coords_grid) > 0,
          '%d atoms' % len(coords_grid))

    records_live = geometry.extract_game_atoms()
    bonds, index_to_id = geometry.ligand_bonds(lig_obj)
    _, lig_remap = _remap_ligand_bonds(records_live, bonds, index_to_id)
    features = extract_features(records_live, lig_remap)
    lig_ring = features['lig']['rings'][0]
    aa_ring = features['aa'][aa_obj]['rings'][0]
    n_l = _tofloat(lig_ring['normal'])
    n_a = _tofloat(aa_ring['normal'])
    line_angle0 = _angle_between_deg(n_a, n_l)
    REC['grid_line_angle_deg'] = line_angle0
    print('SMOKE-ENV placement aa=%s slot=%s line_angle=%.3f deg'
          % (resn, slot_id, line_angle0), flush=True)
except Exception:
    traceback.print_exc()
    check('part 0 setup', False, 'raised (see traceback above)')
    payload = None
    registry = None
    coords_grid = None

# ============================================================
# PART A: Q1 -- COORDINATE PATH (selection-form rotate)
# ============================================================
try:
    if coords_grid is None:
        raise RuntimeError('part 0 failed')

    # Orientation step: axis+angle form of the SMOKE-04 Rodrigues
    # alignment, executed via the SELECTION-form cmd.rotate about the
    # AA ring center (the primitive a Phase-3 rotate gesture would use).
    target_n = n_l if _dot(n_a, n_l) >= 0.0 else _scale(-1.0, n_l)
    k, ang_deg = _axis_angle(n_a, target_n)
    ring_c = _tofloat(aa_ring['center'])
    coords_before = geometry.coords_of(aa_obj)
    if k is not None and ang_deg > PISTACK_ANGLE_TOL_DEG:
        cmd.rotate(list(k), ang_deg, aa_obj, camera=0, origin=list(ring_c))
        print('SMOKE-ENV rotated selection-form axis=(%.4f, %.4f, %.4f) '
              'angle=%.3f origin=(%.3f, %.3f, %.3f)'
              % ((k[0], k[1], k[2], ang_deg) + ring_c), flush=True)
    else:
        print('SMOKE-ENV alignment already within window '
              '(line_angle=%.3f)' % line_angle0, flush=True)

    coords_after = geometry.coords_of(aa_obj)
    disp_a = _coords_maxdisp(coords_before, coords_after)
    check('Q1 selection-rotate bakes coords', disp_a > 0.5,
          'max atom displacement %.4g A' % disp_a)
    m_after = _obj_matrix(aa_obj)
    check('Q1 selection-rotate keeps matrix identity',
          _is_identity(m_after), 'matrix=%s' % (_mfmt(m_after),))

    records_live = geometry.extract_game_atoms()
    features = extract_features(records_live, lig_remap)
    aa_ring = features['aa'][aa_obj]['rings'][0]
    lig_ring = features['lig']['rings'][0]
    n_l = _tofloat(lig_ring['normal'])
    new_angle = _angle_between_deg(_tofloat(aa_ring['normal']), n_l)
    check('Q1 ring alignment baked', new_angle <= PLANE_TOL_DEG,
          'was %.3f -> %.6f deg' % (line_angle0, new_angle))

    # Translation step through the engine (engine.place_aa = bake).
    ring_target = _add(_tofloat(lig_ring['center']), _scale(4.5, n_l))
    delta = _sub(ring_target, _tofloat(aa_ring['center']))
    position = _add(_tofloat(geometry.centroid_of(aa_obj)), delta)
    engine.place_aa(slot_id, position)
    records_live = geometry.extract_game_atoms()
    features = extract_features(records_live, lig_remap)
    placed_center = _tofloat(features['aa'][aa_obj]['rings'][0]['center'])
    drift = max(abs(placed_center[i] - ring_target[i]) for i in range(3))
    check('Q1 placement ring at target', drift < 1e-4, 'drift=%.2g' % drift)

    # THE Q1 QUESTION: does detect() see the moved pose?
    records_a = engine.detect()
    pi_here = [r for r in records_a
               if r['type'] == 'pi_stacking' and r['aa']['object'] == aa_obj]
    check('Q1 detect sees the moved pose', len(pi_here) >= 1,
          'pi records on placed object=%d' % len(pi_here))
    score_a, formed_a = engine.score_current(0, 0, required,
                                             records=records_a)
    check('Q1 score after coordinate move == 1.0',
          score_a == 1.0 and formed_a == ['pi_stacking'],
          'score=%r formed=%r' % (score_a, formed_a))
    m_ident = _is_identity(_obj_matrix(aa_obj))
    check('Q1 matrix still identity after full move', m_ident, '')
    if pi_here:
        m = pi_here[0]['metrics']
        REC['coord_d_center'] = float(m['d_center'])
        REC['coord_angle_deg'] = float(m['angle_deg'])
        REC['coord_disp_a'] = disp_a
        spike('Q1 coordinate-path: coords moved=True (disp=%.3g A) '
              'detect_sees=True (d_center=%.4f angle=%.4f subtype=%s, '
              'score 1.0) matrix_clean=%s'
              % (disp_a, m['d_center'], m['angle_deg'], m['subtype'],
                 m_ident))
except Exception:
    traceback.print_exc()
    check('part A coordinate path', False, 'raised (see traceback above)')

# ============================================================
# PART A2: Q4a -- RESET semantics (rotational vs translation-only)
# ============================================================
try:
    if coords_grid is None:
        raise RuntimeError('part 0 failed')

    # (i) reset after the ROTATIONAL move (align + place): the engine
    # re-bakes the grid POSITION only -- orientation is NOT replayed.
    engine.reset_to_grid()
    cen_r = geometry.centroid_of(aa_obj)
    mol_offset = molecule['offset']
    grid_slot = [s for s in mol_payload['grid']['slots']
                 if s['slot_id'] == slot_id][0]
    grid_target = placement.effective_position(
        grid_slot['grid_pose']['position'], mol_offset)
    cen_tol = max(_axis_tol(cen_r[i], grid_target[i]) for i in range(3))
    cen_dev = max(abs(cen_r[i] - grid_target[i]) for i in range(3))
    check('Q4a reset restores grid centroid', cen_dev <= cen_tol,
          'centroid dev %.3g (tol %.3g)' % (cen_dev, cen_tol))
    coords_rot_reset = geometry.coords_of(aa_obj)
    ok_rot, worst_rot, tol_rot = _coords_close(coords_grid,
                                               coords_rot_reset)
    records_c = engine.detect()
    pi_c = [r for r in records_c if r['type'] == 'pi_stacking']
    check('Q4a detect back to zero', not pi_c,
          'records=%d pi=%d' % (len(records_c), len(pi_c)))
    score_c, formed_c = engine.score_current(0, 0, required,
                                             records=records_c)
    check('Q4a score back to zero',
          score_c == 0.0 and formed_c == [],
          'score=%r formed=%r' % (score_c, formed_c))
    check('Q4a matrix identity after reset',
          _is_identity(_obj_matrix(aa_obj)), '')
    REC['reset_rot_worst_atom_dev'] = worst_rot
    spike('Q4a reset-after-ROTATIONAL-move: centroid restored (%.2g A) '
          'but per-atom residual %.3g A remains -> reset replays grid '
          'POSITIONS only, orientation NOT replayed (translate-only '
          're-bake); detect=0 score=0.0' % (cen_dev, worst_rot))

    # (ii) reset after a PURE-TRANSLATION move: per-atom exact restore.
    pos2 = _add(_tofloat(cen_r), (3.0, 0.0, 0.0))
    engine.place_aa(slot_id, pos2)
    coords_trans = geometry.coords_of(aa_obj)
    bmap = dict((c[0], c[1:]) for c in coords_rot_reset)
    trans_dev = 0.0
    for (aid, x, y, z) in coords_trans:
        b = bmap[aid]
        want = (b[0] + 3.0, b[1], b[2])
        trans_dev = max(trans_dev, max(abs((x, y, z)[i] - want[i])
                                       for i in range(3)))
    check('Q4a translation move lands exactly', trans_dev <= 1e-5,
          'worst dev vs +3x = %.3g A' % trans_dev)
    engine.reset_to_grid()
    coords_back = geometry.coords_of(aa_obj)
    ok_t, worst_t, tol_t = _coords_close(coords_rot_reset, coords_back)
    check('Q4a reset restores translation-only move EXACTLY', ok_t,
          'worst per-axis dev %.3g (tol %.3g)' % (worst_t, tol_t))
    REC['reset_trans_worst_dev'] = worst_t
    spike('Q4a reset-after-TRANSLATION-move: per-atom exact restore vs '
          'pre-move snapshot (worst=%.2g A vs tol %.2g) -> reset is '
          'fully exact when no rotation happened' % (worst_t, tol_t))

    # Re-extract the grid-pose features PART B needs (stored pose is
    # the exact grid snapshot again; orientation = natural fragment).
    records_live = geometry.extract_game_atoms()
    features = extract_features(records_live, lig_remap)
    lig_ring = features['lig']['rings'][0]
    aa_ring = features['aa'][aa_obj]['rings'][0]
    n_l = _tofloat(lig_ring['normal'])
    n_a = _tofloat(aa_ring['normal'])
    ring_c_grid = _tofloat(aa_ring['center'])
except Exception:
    traceback.print_exc()
    check('part A2 reset semantics', False, 'raised (see traceback above)')
    ring_c_grid = None

# ============================================================
# PART B: Q2/Q4b -- OBJECT-MATRIX PATH (+ conjugation law + reset)
#
# EMPIRICAL MODEL (pinned by the probes below):
#   on-screen pose = M_object o stored_coords   (M via get_object_matrix,
#   TTT convention; the TTT display slot is what cmd.rotate(object=)
#   writes -- the incl_ttt=0 state slot stays identity there).
#   The bake primitives (cmd.translate / cmd.rotate selection-form /
#   transform_selection) apply a requested world transform T in the
#   LOCAL frame of the current matrix: stored_new = M^-1 o T o M o stored.
#   For pure translations that reduces to stored_shift = R^-1 . s.
#   With M = identity (the Phase-2 invariant) local == world = pure bake.
# ============================================================
M = None
try:
    if coords_grid is None or ring_c_grid is None:
        raise RuntimeError('part 0/A2 failed')

    # Matrix-rotation axis: perpendicular to both ring normals so the
    # on-screen ring-normal angle changes by EXACTLY the rotation
    # angle (guaranteed screen-mismatch carrier, not luck).
    k_m = _axis_perp_both(n_a, n_l)
    ang_m = 37.0
    REC['matrix_axis'] = tuple(round(v, 6) for v in k_m)

    def _rot_matrix(k, ang_rad):
        """Rodrigues 3x3 (row-major rows) for unit axis k."""
        c = math.cos(ang_rad)
        s = math.sin(ang_rad)
        C = 1.0 - c
        return (
            (c + k[0] * k[0] * C,
             k[0] * k[1] * C - k[2] * s,
             k[0] * k[2] * C + k[1] * s),
            (k[1] * k[0] * C + k[2] * s,
             c + k[1] * k[1] * C,
             k[1] * k[2] * C - k[0] * s),
            (k[2] * k[0] * C - k[1] * s,
             k[2] * k[1] * C + k[0] * s,
             c + k[2] * k[2] * C),
        )

    def _mv(R3, v):
        return tuple(sum(R3[i][j] * v[j] for j in range(3))
                     for i in range(3))

    coords_preB = geometry.coords_of(aa_obj)
    m_before = _obj_matrix(aa_obj)
    check('B matrix identity before object-rotate', _is_identity(m_before),
          '')
    cmd.rotate(list(k_m), ang_m, object=aa_obj, origin=list(ring_c_grid),
               camera=0)
    coords_moved = geometry.coords_of(aa_obj)
    disp_b = _coords_maxdisp(coords_preB, coords_moved)
    check('B2 object-rotate leaves coords untouched', disp_b <= 1e-9,
          'max coord disp %.3g A (expect 0)' % disp_b)
    M = _obj_matrix(aa_obj)
    m_state = _obj_matrix(aa_obj, incl_ttt=0)
    REC['state_matrix_after_object_rotate'] = _mfmt(m_state)
    m_nonid = (M is not None) and not _is_identity(M)
    state_ident = _is_identity(m_state)
    check('B2 object-rotate writes the TTT display matrix', m_nonid,
          'M=%s' % (_mfmt(M),))
    check('B2 state slot (incl_ttt=0) stays identity', state_ident,
          'state=%s' % (_mfmt(m_state),))
    records_m = engine.detect()
    pi_m = [r for r in records_m
            if r['type'] == 'pi_stacking' and r['aa']['object'] == aa_obj]
    REC['matrix_path_coord_disp'] = disp_b
    spike('Q2 matrix-path: coords moved=False (disp=%.3g) '
          'detect_sees_stored_only (pi=%d); TTT display matrix=%s, '
          'state slot identity=%s'
          % (disp_b, len(pi_m), 'non-identity' if m_nonid else 'identity',
             state_ident))

    # B3: read-back convention (TTT vs homogeneous layouts coincide
    # when the bottom row is zero -- record which the numbers favor).
    ang_rad = math.radians(ang_m)
    dev_ttt = 0.0
    dev_hom = 0.0
    for (aid, x, y, z) in coords_moved:
        p = (x, y, z)
        want = _rot_pos(p, k_m, ang_rad, ring_c_grid)
        dev_ttt = max(dev_ttt,
                      max(abs(_apply_ttt(M, p)[i] - want[i])
                          for i in range(3)))
        dev_hom = max(dev_hom,
                      max(abs(_apply_hom(M, p)[i] - want[i])
                          for i in range(3)))
    check('B3 matrix read-back composes with stored coords',
          min(dev_ttt, dev_hom) <= CONV_TOL,
          'TTT-layout dev %.3g vs homogeneous-layout dev %.3g (tol %.0g)'
          % (dev_ttt, dev_hom, CONV_TOL))
    REC['readback_dev_ttt'] = dev_ttt
    REC['readback_dev_hom'] = dev_hom
    spike('B3 matrix read-back: TTT-layout dev=%.3g | homogeneous-layout '
          'dev=%.3g (bottom row m12..m14=(%.3g, %.3g, %.3g) -> the two '
          'coincide; TTT is the documented convention)'
          % (dev_ttt, dev_hom, M[12], M[13], M[14]))

    # B4a: THE CONJUGATION LAW -- cmd.translate under matrix residue
    # applies the shift in the LOCAL frame: stored_shift = R^-1 . s.
    R_inv = _rot_matrix(k_m, -ang_rad)
    cen_t0 = _tofloat(geometry.centroid_of(aa_obj))
    cmd.translate([0.0, 0.0, -1.0], aa_obj, state=1, camera=0)
    cen_t1 = _tofloat(geometry.centroid_of(aa_obj))
    t_shift = _sub(cen_t1, cen_t0)
    want_shift = _mv(R_inv, (0.0, 0.0, -1.0))
    conj_dev = max(abs(t_shift[i] - want_shift[i]) for i in range(3))
    REC['translate_under_matrix_shift'] = t_shift
    REC['translate_conjugation_dev'] = conj_dev
    check('B4a translate under matrix follows R^-1.s (local frame)',
          conj_dev <= 1e-6,
          'shift %s vs R^-1.s %s (dev %.3g)'
          % (['%.4g' % v for v in t_shift],
             ['%.4g' % v for v in want_shift], conj_dev))
    spike('B4a cmd.translate(s=(0,0,-1)) on matrix-bearing object: '
          'stored shift=%s = R^-1.s exactly -> bakes run in the LOCAL '
          'matrix frame (screen moves by s; stored does NOT)'
          % (['%.4g' % v for v in t_shift],))
    cmd.translate([0.0, 0.0, 1.0], aa_obj, state=1, camera=0)  # undo
    coords_u = geometry.coords_of(aa_obj)
    undo_dev = _coords_maxdisp(coords_preB, coords_u)
    REC['translate_undo_dev'] = undo_dev
    check('B4a conjugated translate undoes exactly', undo_dev <= 1e-5,
          'disp vs pre-B %.3g A' % undo_dev)

    # B4b: selection-form rotate under matrix residue -- stored coords
    # CHANGE (conjugated application), unlike the object-form rotate.
    coords_r0 = geometry.coords_of(aa_obj)
    cmd.rotate([0.0, 1.0, 0.0], 20.0, aa_obj, camera=0,
               origin=list(ring_c_grid))
    coords_r1 = geometry.coords_of(aa_obj)
    disp_r = _coords_maxdisp(coords_r0, coords_r1)
    REC['rotate_sel_under_matrix_disp'] = disp_r
    check('B4b selection-rotate under matrix edits stored coords',
          disp_r > 0.1,
          'max coord disp %.3g A (conjugated, not the requested '
          'rotation about the requested origin)' % disp_r)
    spike('B4b cmd.rotate(selection, origin=C) on matrix-bearing '
          'object: stored disp=%.3g A -- the bake lands CONJUGATED '
          '(M^-1 o T o M); with M=identity it is the pure world bake'
          % disp_r)
    cmd.rotate([0.0, 1.0, 0.0], -20.0, aa_obj, camera=0,
               origin=list(ring_c_grid))                      # undo
    coords_r2 = geometry.coords_of(aa_obj)
    undo_r = _coords_maxdisp(coords_r0, coords_r2)
    REC['rotate_sel_undo_dev'] = undo_r
    check('B4b conjugated rotate undoes (within float32)', undo_r <= 1e-3,
          'disp vs pre-rotate %.3g A' % undo_r)

    # B5: SCREEN-VS-DETECTOR mismatch at grid stored coords + matrix.
    records_now = geometry.extract_game_atoms()
    features_now = extract_features(records_now, lig_remap)
    n_stored = _tofloat(features_now['aa'][aa_obj]['rings'][0]['normal'])
    a_stored = _angle_between_deg(n_stored, n_l)
    a_screen = _angle_between_deg(_rotate3(M, n_stored), n_l)
    cen_eff = _apply_ttt(M, ring_c_grid)
    cen_shift = _norm(_sub(cen_eff, ring_c_grid))
    check('B5 on-screen pose differs from detection',
          abs(a_screen - a_stored) > 5.0,
          'screen ring angle %.3f deg vs detector-visible %.3f deg'
          % (a_screen, a_stored))
    REC['screen_angle_deg'] = a_screen
    REC['stored_angle_deg'] = a_stored
    REC['screen_center_shift'] = cen_shift
    spike('B5 blindness at grid+matrix: detector sees ring angle %.3f '
          'deg (0 pi records); on-screen (matrix o stored) ring angle '
          '%.3f deg -- the screen shows a pose the detector never '
          'scored' % (a_stored, a_screen))

    # B6a: reset_to_grid with stored AT grid + matrix residue: the
    # translate deltas are ~zero, so the engine completes silently --
    # but the matrix survives and the screen stays wrong.
    engine.reset_to_grid()
    M2 = _obj_matrix(aa_obj)
    residue_survives = (M2 is not None) and not _is_identity(M2)
    check('B6a reset completes; matrix residue SURVIVES', residue_survives,
          'M2=%s' % (_mfmt(M2),))
    a_screen2 = _angle_between_deg(_rotate3(M2, n_stored), n_l)
    check('B6a on-screen pose STILL wrong after reset',
          abs(a_screen2 - a_stored) > 5.0,
          'screen ring angle %.3f deg (unchanged by reset)' % a_screen2)
    REC['reset_matrix_residue'] = residue_survives
    REC['reset_screen_angle_deg'] = a_screen2
    spike('B6a reset-after-matrix-move (stored at grid): engine '
          'completes silently (zero deltas) but matrix residue=%s and '
          'on-screen angle %.3f deg -- reset cannot see or fix the '
          'matrix' % (residue_survives, a_screen2))

    # B4c: engine.place_aa fails CLOSED under matrix residue (its
    # world-frame delta lands conjugated -> the pose assert fires).
    # NOTE: the failed bake leaves the stored pose OFF-grid (the
    # conjugated landing) -- exactly the state B6b probes next, which
    # is why B4c deliberately runs after B6a.
    place_exc = None
    try:
        engine.place_aa(slot_id, _add(_tofloat(ring_c_grid), (0.0, 0.0,
                                                              2.0)))
    except placement.PlacementError as exc:
        place_exc = exc
    except Exception as exc:
        place_exc = exc
    check('B4c engine.place_aa FAILS under matrix residue',
          isinstance(place_exc, placement.PlacementError),
          'exc=%s' % (str(place_exc)[:90] if place_exc else 'None',))
    REC['place_aa_under_matrix'] = (
        type(place_exc).__name__ if place_exc else None)
    spike('B4c engine.place_aa on matrix-bearing object -> %s (the '
          'world-frame delta lands conjugated; engine ops fail closed '
          'and leave the stored pose displaced)'
          % (type(place_exc).__name__ if place_exc else 'NO EXCEPTION',))

    # B6b: reset when the stored pose is OFF-grid under the matrix:
    # the world-frame delta lands conjugated -> reset FAILS CLOSED.
    cmd.translate([2.0, 0.0, 0.0], aa_obj, state=1, camera=0)
    cen_o = _tofloat(geometry.centroid_of(aa_obj))
    off_dist = _norm(_sub(cen_o, ring_c_grid))
    reset_exc = None
    try:
        engine.reset_to_grid()
    except placement.PlacementError as exc:
        reset_exc = exc
    except Exception as exc:
        reset_exc = exc
    check('B6b reset_to_grid FAILS CLOSED off-grid under matrix',
          isinstance(reset_exc, placement.PlacementError),
          'exc=%s' % (str(reset_exc)[:90] if reset_exc else 'None',))
    REC['reset_under_matrix_offgrid'] = (
        type(reset_exc).__name__ if reset_exc else None)
    REC['offgrid_distance'] = off_dist
    spike('B6b reset_to_grid with stored off-grid (%.2g A) + matrix '
          'residue -> %s (the re-bake delta lands conjugated; the '
          'engine can neither fix nor tolerate the matrix path)'
          % (off_dist,
             type(reset_exc).__name__ if reset_exc else 'NO EXCEPTION',))

    # B7: fold-clear escape hatch END-TO-END: matrix_copy the ligand's
    # identity matrix over -> bakes run in the world frame again ->
    # reset fully recovers this translation-only excursion.
    check('B7 ligand donor matrix identity',
          _is_identity(_obj_matrix(lig_obj)), '')
    try:
        cmd.matrix_copy(lig_obj, aa_obj)
        M3 = _obj_matrix(aa_obj)
        cleared = _is_identity(M3, tol=IDENT_F32)
        check('B7 fold-clear via matrix_copy(identity ligand)', cleared,
              'matrix after copy: %s' % (_mfmt(M3),))
        cen_f0 = _tofloat(geometry.centroid_of(aa_obj))
        cmd.translate([0.0, 0.0, -1.0], aa_obj, state=1, camera=0)
        cen_f1 = _tofloat(geometry.centroid_of(aa_obj))
        f_shift = _sub(cen_f1, cen_f0)
        translate_alive = abs(f_shift[2] + 1.0) <= 1e-6 and \
            abs(f_shift[0]) <= 1e-6 and abs(f_shift[1]) <= 1e-6
        check('B7 engine translate ALIVE after fold-clear',
              translate_alive, 'shift %s'
              % (['%.3g' % v for v in f_shift],))
        engine.reset_to_grid()
        coords_f = geometry.coords_of(aa_obj)
        ok_f, worst_f, tol_f = _coords_close(coords_preB, coords_f)
        check('B7 fold-clear + reset fully recovers the pose', ok_f,
              'worst dev vs pre-B %.3g (tol %.3g)' % (worst_f, tol_f))
        M4 = _obj_matrix(aa_obj)
        records_f = engine.detect()
        pi_f = [r for r in records_f if r['type'] == 'pi_stacking']
        check('B7 detect clean + matrix clean after recovery',
              (not pi_f) and _is_identity(M4, tol=IDENT_F32),
              'pi=%d matrix=%s' % (len(pi_f), _mfmt(M4)))
        REC['fold_clear_works'] = cleared and translate_alive and ok_f
        spike('B7 fold-clear matrix_copy(ligand->aa): matrix_identity=%s, '
              'translate alive (shift=%s), reset recovers the pose '
              '(worst=%.2g A), detect=0 -- NOTE: recovery is complete '
              'here only because the excursion was translation-only; '
              'conjugated ROTATIONS (B4b) leave orientation damage in '
              'stored coords that only re-materialization undoes'
              % (cleared, ['%.3g' % v for v in f_shift], worst_f))
    except Exception as exc:
        check('B7 fold-clear via matrix_copy(identity ligand)', False,
              'raised: %r' % (exc,))
except Exception:
    traceback.print_exc()
    check('part B matrix path', False, 'raised (see traceback above)')

# ============================================================
# PART D: Q5 -- cmd.drag headless behavior + editor scheme
# ============================================================
button_mode0 = REC.get('button_mode_initial', 0)
try:
    import pymol.wizard as _wizard_mod
    import pymol.wizard.dragging as _dragging_mod

    class ProbeWizard(_wizard_mod.Wizard):
        """Trivial stand-in for the future game wizard."""

        def __init__(self):
            _wizard_mod.Wizard.__init__(self)
            self.pick_count = 0

        def do_pick(self, bondFlag):
            self.pick_count += 1

        def get_prompt(self):
            return ['AA-match spike probe wizard']

    probe = ProbeWizard()
    cmd.set_wizard(probe)
    w0 = cmd.get_wizard()
    REC['stack_after_install'] = _stack_names()
    check('D custom wizard installed',
          w0 is not None and type(w0).__name__ == 'ProbeWizard',
          'stack=%s' % (REC['stack_after_install'],))

    # --- wizard=0: arm the drag WITHOUT installing the Dragging wizard
    pre_drag_name = cmd.get_drag_object_name()
    cen_before = geometry.centroid_of(aa_obj)
    bm_before = int(cmd.get('button_mode'))
    exc0 = None
    try:
        cmd.drag(aa_obj, wizard=0)
    except Exception as exc:
        exc0 = exc
    w1 = cmd.get_wizard()
    drag_name0 = cmd.get_drag_object_name()
    cen_after = geometry.centroid_of(aa_obj)
    cen_drift = max(abs(cen_after[i] - cen_before[i]) for i in range(3))
    bm_after = int(cmd.get('button_mode'))
    check('D drag(wizard=0) raises nothing', exc0 is None,
          'exception: %r' % (exc0,))
    check('D drag(wizard=0) keeps the custom wizard',
          w1 is not None and type(w1).__name__ == 'ProbeWizard',
          'wizard=%s' % (type(w1).__name__ if w1 else None,))
    check('D drag(wizard=0) moves nothing headless', cen_drift <= 1e-9,
          'centroid drift %.3g' % cen_drift)
    cmd.drag()                       # deactivate the armed drag
    drag_name1 = cmd.get_drag_object_name()
    bm_after_off = int(cmd.get('button_mode'))
    REC['drag0_exception'] = repr(exc0)
    REC['drag0_wizard_kept'] = (w1 is not None
                                and type(w1).__name__ == 'ProbeWizard')
    REC['drag0_object'] = drag_name0
    REC['drag0_button_mode'] = (bm_before, bm_after, bm_after_off)
    REC['drag_off_object'] = drag_name1
    spike('Q5 drag(wizard=0): exception=%r wizard_kept=%s '
          'drag_object_name %r->%r (deactivate %r) coords_unchanged=%s '
          'button_mode %d->%d (deactivate does NOT restore; edit=1 '
          'default flips the mouse ring via edit_mode)'
          % (exc0, REC['drag0_wizard_kept'], pre_drag_name, drag_name0,
             drag_name1, cen_drift <= 1e-9, bm_before, bm_after_off))

    # --- edit=0 variant: does skipping edit_mode keep button_mode?
    bm_e0 = int(cmd.get('button_mode'))
    try:
        cmd.drag(aa_obj, wizard=0, edit=0)
        bm_e1 = int(cmd.get('button_mode'))
    except Exception as exc:
        bm_e1 = None
        spike('Q5 drag(wizard=0, edit=0) raised: %r' % (exc,))
    cmd.drag()
    REC['drag0_edit0_button_mode'] = (bm_e0, bm_e1)
    if bm_e1 is not None:
        spike('Q5 drag(wizard=0, edit=0): button_mode %d->%s '
              '(edit=0 avoids the mouse-ring flip)' % (bm_e0, bm_e1))

    # --- wizard=1: the built-in Dragging wizard goes ON TOP (stack)
    exc1 = None
    w2 = None
    try:
        cmd.drag(aa_obj, wizard=1)
        w2 = cmd.get_wizard()
    except Exception as exc:
        exc1 = exc
    w2_name = type(w2).__name__ if w2 is not None else None
    w2_valid = getattr(w2, 'valid', None) if w2 is not None else None
    REC['stack_after_drag1'] = _stack_names()
    REC['drag1_exception'] = repr(exc1)
    REC['drag1_wizard'] = w2_name
    REC['drag1_valid'] = w2_valid
    check('D drag(wizard=1) puts Dragging on top of the stack',
          w2 is not None and w2_name == 'Dragging',
          'stack=%s' % (REC['stack_after_drag1'],))
    spike('Q5 drag(wizard=1): exception=%r top=%s valid=%s stack=%s '
          '(the game wizard is PUSHED UNDER, not destroyed)'
          % (exc1, w2_name, w2_valid, REC['stack_after_drag1']))

    # Scheme gate, DIRECTLY (queue-timing independent): a fresh
    # Dragging instance runs check_valid() inside __init__.
    d = _dragging_mod.Dragging()
    REC['dragging_direct_valid'] = d.valid
    spike('Q5 dragging.Dragging() direct gate at default scheme: '
          'editor_scheme=%d -> check_valid verdict valid=%s '
          '(installed top valid=%s -- consistency recorded, not '
          'asserted: corpse-linger is queue-timing dependent)'
          % (scheme_default, d.valid, w2_valid))

    # Pop semantics: cmd.set_wizard() pops ONE level.
    cmd.set_wizard()
    w_pop1 = cmd.get_wizard()
    REC['stack_after_pop1'] = _stack_names()
    spike('Q5 after one cmd.set_wizard(): top=%s stack=%s '
          '(set_wizard() POPs one level -- game wizard resurfaces)'
          % (type(w_pop1).__name__ if w_pop1 is not None else None,
             REC['stack_after_pop1']))
    pops = 1
    while cmd.get_wizard() is not None and pops < 6:
        cmd.set_wizard()
        pops += 1
    w4 = cmd.get_wizard()
    REC['pops_to_empty'] = pops
    check('D wizard stack fully cleared', w4 is None,
          'pops=%d' % pops)
    sels = list(cmd.get_names('selections'))
    REC['leftover_selections'] = sels
    spike('Q5 cleanup: stack empty after %d pop(s); leftover '
          'selections=%s (the _drag selection lingers after '
          'deactivation)' % (pops, sels))
    if int(cmd.get('button_mode')) != button_mode0:
        cmd.set('button_mode', button_mode0, quiet=1)
        spike('Q5 button_mode restored to %d' % button_mode0)

    # --- Scheme law probe: get_editor_scheme() vs drag state vs ring.
    # (Observed across runs: the scheme stays 1 in idle sessions EVEN
    # after edit_mode(1) ring flips, yet the Dragging wizard installed
    # DURING cmd.drag(wizard=1) saw scheme==3 -- hypothesis: the ARMED
    # DRAG (the C-side _cmd.drag state) is what sets the scheme.)
    if int(cmd.get('button_mode')) != button_mode0:
        cmd.set('button_mode', button_mode0, quiet=1)
        cmd.edit_mode(0)
    scheme_idle = int(cmd.get_editor_scheme())
    d_idle = _dragging_mod.Dragging()
    cmd.drag(aa_obj, wizard=0)                 # arm the drag (C-side)
    scheme_armed = int(cmd.get_editor_scheme())
    d_armed = _dragging_mod.Dragging()
    cmd.drag()                                 # deactivate
    scheme_off = int(cmd.get_editor_scheme())
    cmd.edit_mode(1)                           # ring flip only (no drag)
    scheme_ring = int(cmd.get_editor_scheme())
    d_ring = _dragging_mod.Dragging()
    cmd.edit_mode(0)                           # restore viewing
    scheme_restored = int(cmd.get_editor_scheme())
    REC['scheme_idle'] = scheme_idle
    REC['dragging_valid_idle'] = d_idle.valid
    REC['scheme_drag_armed'] = scheme_armed
    REC['dragging_valid_armed'] = d_armed.valid
    REC['scheme_after_deactivate'] = scheme_off
    REC['scheme_ring_edited'] = scheme_ring
    REC['dragging_valid_ring_edited'] = d_ring.valid
    REC['scheme_restored'] = scheme_restored
    spike('Q5 scheme law: idle scheme=%d (Dragging.valid=%s) | drag '
          'ARMED scheme=%d (valid=%s) | deactivated scheme=%d | '
          'edit_mode(1) ring-only scheme=%d (valid=%s) | restored=%d '
          '-> the scheme tracks the ARMED DRAG state, not the mouse '
          'ring; cmd.drag arms BEFORE installing Dragging, so its own '
          'gate is satisfied by its own arming'
          % (scheme_idle, d_idle.valid, scheme_armed, d_armed.valid,
             scheme_off, scheme_ring, d_ring.valid, scheme_restored))
    check('D scheme gate: fires idle, satisfied while drag armed',
          scheme_idle != 3 and d_idle.valid == 0
          and scheme_armed == 3 and d_armed.valid == 1,
          'idle: scheme=%d valid=%s | armed: scheme=%d valid=%s'
          % (scheme_idle, d_idle.valid, scheme_armed, d_armed.valid))
except Exception:
    traceback.print_exc()
    check('part D drag probes', False, 'raised (see traceback above)')

# ============================================================
# Teardown: cleanup_game_objects back to the pre-game snapshot
# ============================================================
try:
    result = placement.cleanup_game_objects()
    post_names = list(cmd.get_names('objects'))
    check('cleanup count',
          result['deleted'] == 1 + n * n,
          'deleted=%d want %d' % (result['deleted'], 1 + n * n))
    check('teardown leaves scene pre-game',
          post_names == pre_names and not any(
              n0.startswith(geometry.GAME_PREFIX) for n0 in post_names),
          'post=%s' % post_names)
    payload = None
    registry = None
except Exception:
    traceback.print_exc()
    check('teardown', False, 'raised (see traceback above)')
    placement.cleanup_game_objects()   # never leave game objects

# ============================================================
# PART C: Q3 -- transform_selection / transform_object (scratch)
# ============================================================
try:
    scratch1 = 'zz_scr1'
    scratch2 = 'zz_scr2'
    try:
        cmd.fragment('gly', scratch1, zoom=0)
        cmd.fragment('gly', scratch2, zoom=0)
        check('C scratch objects born', cmd.count_atoms(scratch1) > 0
              and cmd.count_atoms(scratch2) > 0, '')
        check('C scratch matrices identity',
              _is_identity(_obj_matrix(scratch1))
              and _is_identity(_obj_matrix(scratch2)), '')

        # C1: transform_selection -- the exact form cmd.rotate(selection)
        # builds internally (editing.py:1815-1819): TTT layout
        # [R | origin; -origin | 1], homogenous=0 -> COORDINATE bake.
        # WHICH semantics? Compare the baked result against four
        # candidate models (the documented one is m1):
        #   m1_documented : y = R.(p - c0) + c0
        #   m2_pre_ignore : y = R.p + c0        (bottom row ignored)
        #   m3_post_ignore: y = R.(p - c0)      (last column ignored)
        #   m4_transposed : y = Rt.(p - c0) + c0
        c_before = geometry.coords_of(scratch1)
        c0 = geometry.centroid_of(scratch1)
        ang = math.radians(25.0)
        cz, sz = math.cos(ang), math.sin(ang)
        ttt = [cz, -sz, 0.0, c0[0],
               sz, cz, 0.0, c0[1],
               0.0, 0.0, 1.0, c0[2],
               -c0[0], -c0[1], -c0[2], 1.0]
        cmd.transform_selection(scratch1, ttt)
        c_after = geometry.coords_of(scratch1)
        Rt = ((cz, sz, 0.0), (-sz, cz, 0.0), (0.0, 0.0, 1.0))

        def _mv3(R3, v):
            return (R3[0][0] * v[0] + R3[0][1] * v[1] + R3[0][2] * v[2],
                    R3[1][0] * v[0] + R3[1][1] * v[1] + R3[1][2] * v[2],
                    R3[2][0] * v[0] + R3[2][1] * v[1] + R3[2][2] * v[2])

        def _pv(p):
            return (p[0], p[1], p[2])

        models = {
            'm1_documented': lambda p: _add(
                _mv3(((cz, -sz, 0.0), (sz, cz, 0.0), (0.0, 0.0, 1.0)),
                     _sub(_pv(p), c0)), c0),
            'm2_pre_ignore': lambda p: _add(
                _mv3(((cz, -sz, 0.0), (sz, cz, 0.0), (0.0, 0.0, 1.0)),
                     _pv(p)), c0),
            'm3_post_ignore': lambda p: _mv3(
                ((cz, -sz, 0.0), (sz, cz, 0.0), (0.0, 0.0, 1.0)),
                _sub(_pv(p), c0)),
            'm4_transposed': lambda p: _add(_mv3(Rt, _sub(_pv(p), c0)),
                                            c0),
        }
        devs = dict((name, 0.0) for name in models)
        bmap_c1 = dict((c[0], c[1:]) for c in c_before)
        for (aid, x, y, z) in c_after:
            b = bmap_c1[aid]
            for name, fn in models.items():
                want = fn(b)
                devs[name] = max(devs[name],
                                 max(abs((x, y, z)[i] - want[i])
                                     for i in range(3)))
        winner = min(devs, key=lambda k: devs[k])
        moved_sel = _coords_maxdisp(c_before, c_after)
        check('C1 transform_selection semantics identified',
              moved_sel > 0.1 and devs[winner] <= 1e-5,
              'moved=%.3g A; devs %s -> winner=%s'
              % (moved_sel,
                 dict((k, round(v, 6)) for k, v in devs.items()),
                 winner))
        check('C1 transform_selection leaves matrix identity',
              _is_identity(_obj_matrix(scratch1)), '')
        REC['transform_selection'] = (moved_sel, devs[winner], winner)
        spike('Q3 transform_selection (TTT layout, homogenous=0): bakes '
              'coords (moved=%.3g A); applied semantics = %s '
              '(dev %.3g; m1_documented dev %.3g); matrix untouched'
              % (moved_sel, winner, devs[winner],
                 devs['m1_documented']))

        # C2: transform_object homogenous=1 (placement.transform_baked's
        # proven form): standard homogeneous [R|t] -> COORDINATE bake.
        # What does it leave in get_object_matrix? (incl_ttt both ways.)
        t = (2.0, -1.5, 0.75)
        hom = [1.0, 0.0, 0.0, t[0],
               0.0, 1.0, 0.0, t[1],
               0.0, 0.0, 1.0, t[2],
               0.0, 0.0, 0.0, 1.0]
        c_before = geometry.coords_of(scratch1)
        cmd.transform_object(scratch1, hom, homogenous=1)
        c_after = geometry.coords_of(scratch1)
        bmap = dict((cc[0], cc[1:]) for cc in c_before)
        dev_obj = 0.0
        for (aid, x, y, z) in c_after:
            b = bmap[aid]
            want = (b[0] + t[0], b[1] + t[1], b[2] + t[2])
            dev_obj = max(dev_obj, max(abs((x, y, z)[i] - want[i])
                                       for i in range(3)))
        moved_obj = _coords_maxdisp(c_before, c_after)
        check('C2 transform_object(homogenous=1) bakes coords',
              moved_obj > 1.0 and dev_obj <= 1e-6,
              'moved=%.3g A, worst dev vs +t = %.3g' % (moved_obj, dev_obj))
        m_after_c2 = _obj_matrix(scratch1)
        m_after_c2_state = _obj_matrix(scratch1, incl_ttt=0)
        REC['transform_object_bake'] = (moved_obj, dev_obj)
        REC['transform_object_matrix_after'] = _mfmt(m_after_c2)
        REC['transform_object_state_matrix_after'] = _mfmt(
            m_after_c2_state)
        print('SMOKE-ENV C2 matrix after transform_object bake '
              '(incl_ttt=1): %s' % (_mfmt(m_after_c2),), flush=True)
        print('SMOKE-ENV C2 state matrix (incl_ttt=0): %s'
              % (_mfmt(m_after_c2_state),), flush=True)
        spike('Q3 transform_object(homogenous=1, matrix_mode=%s): bakes '
              'coords (moved=%.3g A, dev=%.3g); leaves matrix %s'
              % (matrix_mode0, moved_obj, dev_obj,
                 'RESIDUE (see REC)' if not _is_identity(
                     m_after_c2, tol=IDENT_F32) else 'identity'))
        # Whether the bake leaves residue is RECORDED either way; the
        # identity-matrix discipline is only asserted for the
        # translate/rotate(selection) path (Parts A/B).

        # C3: the duality -- matrix_mode>0 makes transform_object write
        # the object MATRIX instead (coords untouched).
        cmd.set('matrix_mode', 1)
        try:
            c_before = geometry.coords_of(scratch1)
            cmd.transform_object(scratch1, ttt)
            c_after = geometry.coords_of(scratch1)
            disp3 = _coords_maxdisp(c_before, c_after)
            m_scr = _obj_matrix(scratch1)
            scr_nonid = (m_scr is not None) and not _is_identity(m_scr)
            check('C3 transform_object(matrix_mode=1) writes matrix only',
                  disp3 <= 1e-9 and scr_nonid,
                  'coord disp %.3g; matrix %s'
                  % (disp3, 'non-identity' if scr_nonid else 'identity'))
            REC['transform_object_matrixmode1'] = (disp3, scr_nonid)
            spike('Q3 transform_object(matrix_mode=1): writes the object '
                  'matrix (coord disp=%.3g), coords untouched -- the '
                  'duality hazard' % (disp3,))
        finally:
            cmd.set('matrix_mode',
                    matrix_mode0 if matrix_mode0 is not None else 0)

        # C4 (observation): matrix_copy fold-clear on scratch.
        cmd.matrix_copy(scratch2, scratch1)
        m_scr2 = _obj_matrix(scratch1)
        cleared2 = _is_identity(m_scr2, tol=IDENT_F32)
        check('C4 fold-clear via matrix_copy(pristine scratch)',
              cleared2, 'matrix after copy: %s' % (_mfmt(m_scr2),))
        REC['fold_clear_scratch_donor'] = cleared2
        spike('Q3 fold-clear matrix_copy(pristine->dirty): '
              'matrix_now_identity=%s (float32-tight)' % (cleared2,))
    finally:
        for s in (scratch1, scratch2):
            if s in cmd.get_names('objects'):
                cmd.delete(s)
except Exception:
    traceback.print_exc()
    check('part C transform probes', False, 'raised (see traceback above)')

# --- Final leak check + recorded-numbers summary + verdict marker ------
try:
    post_names = list(cmd.get_names('objects'))
    check('final scene equals pre-game', post_names == pre_names,
          'post=%s' % post_names)
except Exception:
    traceback.print_exc()
    check('final leak check', False, 'raised')

for key in sorted(REC):
    print('SMOKE-06 REC %s = %r' % (key, REC[key]), flush=True)
print('=== SMOKE-06 %s ==='
      % ('FAIL: ' + ', '.join(failures) if failures else 'PASS'), flush=True)
