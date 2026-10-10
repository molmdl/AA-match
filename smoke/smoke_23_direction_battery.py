"""Headless smoke 23 - the 8.2 DIRECTION BATTERY (plan 08.2-04).

Run (from WSL, repo root):
    bash smoke/run_smoke.sh smoke/smoke_23_direction_battery.py 240
Verdict is carried by the printed marker (exit codes cannot carry
verdicts through the cmd.exe wrapper): grep '=== SMOKE-23 PASS ==='.
Timeout: 240 s (real game start + composition, as SMOKE-07/08).

CLOSES the do_special/do_key ZERO-COVERAGE gap flagged in
08.2-RESEARCH-code.md section 1.1 ("Automated coverage of the keyboard
layer: ZERO ... a deliberate gap the planner should know"): until this
battery, every movement smoke drove the movement METHODS (nudge_cam /
rotate_view / step_to_ligand) directly and nothing anywhere drove the
keyboard handlers as live code -- a key-map regression would have been
invisible to the whole battery. Formalizes the P1 research probe
(tmp/probe_082_p1_nudge_so3.py, verbatim log tmp/probe_082_p1_output.log
-- R^T camera->world convention live-correct for FULL SO(3), 30/30
presses, max convention deviation 2.51e-07 A) as a PERMANENT battery
member (the battery is now smokes 01-23; 08.2-09 sweeps them all).

DECISION-INDEPENDENT BY CONSTRUCTION: every scripted view below is a
FIXED synthetic rotation block (a literal 3x3 written into this file,
NEVER re-captured from the live start view), with only the 9-number
tail copied verbatim from the captured live view (the smoke_07 PART B
pattern -- the tail is build-dependent state: origin, dolly, clips).
Whichever direction-control disposition the human lands on, these
scripted views remain valid orientations and the pinned behavior
remains TRUE. The Toward-ligand pin (PART C(b)) lands at the CURRENT
wizard_core.NUDGE_STEP constant (1.0 A) -- the pre-evolution baseline
that 08.2-06 will deliberately evolve IF the disposition changes the
Toward step (the 06-05/08.1 documented-evolution precedent).

PART 0  REAL GAME + SCRIPTED PICK: gamestart.start_game() (DEFAULTS,
        seed 42, bundled manifest -- the P1 recipe; the REAL start path
        incl. the compose); the wizard is obtained via cmd.get_wizard();
        molecule-0 slot r0c0 picked through the REAL do_select
        (cmd.select('sele', ...) -> do_select('sele'), the C-layer
        equivalent, smoke_07 recipe; P1-PICK lines in the probe log).
PART A  IDENTITY-VIEW KEYBOARD DRIVES (the rotation block scripted to
        identity, so expected world deltas are LITERAL): do_special(100)
        (GLUT LEFT) returns 1 and the picked AA's centroid moves exactly
        (-NUDGE_STEP, 0, 0); do_special(102) (RIGHT) -> (+NUDGE_STEP, 0,
        0); do_key('w')/'s' -> (0, +/-NUDGE_STEP, 0); 'q'/'e' -> (0, 0,
        -/+NUDGE_STEP). Per press: 02-15 per-axis float32 tolerance, the
        object matrix identity, wiz._error None. do_key(44) (',') ->
        rotate_view(-ROTATE_STEP_DEG): returns 1, centroid preserved
        (CENTROID_TOL), atoms moved (> 0.5 A), identity clean; do_key(46)
        ('.') same with +ROTATE_STEP_DEG.
PART B  DEAD-KEY + UNOWNED-KEY PINS: do_special(101) (UP) and
        do_special(103) (DOWN) return None AND the object does not move
        (centroid dev < 1e-9); do_key('z') returns None, no movement;
        do_key(200) returns None (out of ASCII range -> ch='' -> None).
        The UP/DOWN inertness is the C-source law: they co-fire
        command-line history unconditionally (OrthoSpecial), so the
        wizard layer can never own them (wizard.py do_special docstring;
        the 03-06 recorded law) -- a wizard that one day STARTS owning
        them would silently eat the user's history scrollback.
PART C  SCRIPTED S2 ROLLED VIEW (the FIXED historical block from the P1
        log / P1-POSTSTART-VIEW: (-0.447214, 0.894427, 0.0, -0.894427,
        -0.447214, 0.0, 0.0, 0.0, 1.0) -- a synthetic orientation used
        REGARDLESS of the live start composition; tail copied verbatim):
        (a) do_special(102) moves the AA by exactly
        view_camera_to_world(live_view, (1,0,0)) * NUDGE_STEP within
        1.12e-06 per axis (the 02-15 float32 contract), identity clean;
        the screen-direction angle between R.observed and the intended
        step (P1's viewer-relative metric) prints ~0.0000 deg.
        (b) step_to_ligand() WITH THE ROLLED VIEW STILL APPLIED lands
        the AA centroid EXACTLY NUDGE_STEP toward the LIVE ligand
        centroid (computed from geometry.centroid_of of both objects,
        the smoke_07 :519-537 shape) -- the view-INVARIANCE pin of the
        Toward direction.
PART D  FULL-SO(3) LIVE PIN (yaw+pitch+roll, closing the 03-04
        yaw-only-control gap at smoke level): script S3 = the FIXED
        Rx(30deg)*Ry(50deg)*Rz(20deg) rotation block (hand-derived
        literals, the SAME block as the 08.2-02 unit fixture); four
        presses covering +/-x (specials) and +/-y (keys): each observed
        displacement == R^T.step expectation via view_camera_to_world
        over the LIVE view within 1.12e-06/axis, the object matrix
        identity after EVERY press. P1-PRESS-style per-press verdict
        lines print throughout.

Conventions (frozen Phase 1, kept): anchor repo root via sys.argv first
/ cwd fallback (never __file__); import aamatch directly (module
identity 'aamatch'); every print on ONE line and flushed; explicit
space dicts in every iterate; no round() in compare expressions; no
calls to the placement.py banned cmd APIs -- cmd.get_object_matrix IS
legal and required (the identity-invariant re-assert); per-axis float32
tolerance (POSE_TOL + ULP_REL, the 02-15 contract); created game
objects deleted in a finally (scene restored to the pre-game names --
the probe's P1-CLEANUP pattern).

Python floor: runs inside PyMOL's Windows Python (3.9); written 3.6-safe.
"""
import math
import os
import sys
import traceback


def _find_repo_root():
    """Anchor the repo root WITHOUT trusting __file__ (01-07 discovery:
    inside a -cq script __file__ points at pymol/__init__.py)."""
    mine = 'smoke_23_direction_battery.py'
    for arg in sys.argv:
        if arg.endswith(mine) and os.path.exists(arg):
            return os.path.dirname(os.path.dirname(os.path.abspath(arg)))
    return os.getcwd()


_ROOT = _find_repo_root()
print('SMOKE-ENV root:', _ROOT, flush=True)

failures = []
REC = {}


def check(name, cond, detail=''):
    print('SMOKE-23 %-44s %s %s' % (name, 'PASS' if cond else 'FAIL',
                                    detail), flush=True)
    if not cond:
        failures.append(name)


if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from pymol import cmd  # noqa: E402

from aamatch import gamestart, geometry, placement, wizard_core  # noqa: E402

print('SMOKE-ENV pymol: %s' % (cmd.get_version()[0],), flush=True)
print('SMOKE-ENV python: %s' % (sys.version.split()[0],), flush=True)

POSE_TOL = 1e-6          # float32 pose tolerance floor (02-15)
ULP_REL = 1.1920929e-7   # float32 ulp relative slack (placement)
IDENT_F32 = 1e-6         # identity after float32-touching matrix ops
CENTROID_TOL = 1e-4      # rotation-about-centroid float32 budget


def _axis_tol(a, t):
    """Per-axis float32-realizable tolerance (the 02-15 pose contract)."""
    return POSE_TOL + ULP_REL * max(abs(a), abs(t))


def _max_axis_dev(actual, expected):
    return max(abs(actual[i] - expected[i]) for i in range(3))


def _max_axis_tol(actual, expected):
    return max(_axis_tol(actual[i], expected[i]) for i in range(3))


# --- tiny vec helpers (smoke-local, SMOKE-07 set) -------------------
def _sub(a, b):
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def _add(a, b):
    return (a[0] + b[0], a[1] + b[1], a[2] + b[2])


def _scale(s, a):
    return (s * a[0], s * a[1], s * a[2])


def _dot(a, b):
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def _norm(a):
    return math.sqrt(_dot(a, a))


def _angle_deg(a, b):
    """Angle between two vectors in degrees; 0/0-guarded."""
    la, lb = _norm(a), _norm(b)
    if la < 1e-12 or lb < 1e-12:
        return float('nan')
    c = _dot(a, b) / (la * lb)
    c = max(-1.0, min(1.0, c))
    return math.degrees(math.acos(c))


def _apply_r(r9, v):
    """Row-major 3x3 times 3-vector (P1's camera-frame projection)."""
    return (r9[0] * v[0] + r9[1] * v[1] + r9[2] * v[2],
            r9[3] * v[0] + r9[4] * v[1] + r9[5] * v[2],
            r9[6] * v[0] + r9[7] * v[1] + r9[8] * v[2])


def _tofloat(pt):
    return (float(pt[0]), float(pt[1]), float(pt[2]))


def _obj_matrix(name):
    """cmd.get_object_matrix as a 16-list (or None)."""
    m = cmd.get_object_matrix(name)
    if m is None:
        return None
    return [float(v) for v in m]


def _is_identity(m16, tol=IDENT_F32):
    if m16 is None or len(m16) != 16:
        return False
    want = (1.0, 0.0, 0.0, 0.0,
            0.0, 1.0, 0.0, 0.0,
            0.0, 0.0, 1.0, 0.0,
            0.0, 0.0, 0.0, 1.0)
    return all(abs(m16[i] - want[i]) <= tol for i in range(16))


def _coords_maxdisp(obj, before):
    """Max per-axis |after - before| for ``obj`` against a coords_of()
    snapshot list (atom id -> (x, y, z)), the smoke_07 shape."""
    bmap = dict((row[0], row[1:]) for row in before)
    worst = 0.0
    for row in geometry.coords_of(obj):
        b = bmap.get(row[0])
        if b is None:
            return float('inf')
        worst = max(worst, abs(row[1] - b[0]), abs(row[2] - b[1]),
                    abs(row[3] - b[2]))
    return worst


def _fmt3(v):
    return '(%.6f, %.6f, %.6f)' % (v[0], v[1], v[2])


pre_names = list(cmd.get_names('objects'))
ident_view = None

try:
    # ============================================================
    # PART 0: the REAL game + scripted pick (the P1 recipe)
    # ============================================================
    started = gamestart.start_game()          # DEFAULTS, seed 42
    wiz = cmd.get_wizard()
    check('real game started, wizard on stack',
          wiz is not None and wiz is started,
          'cmd.get_wizard()=%r (the start_game instance)' % (wiz,))
    registry = started._registry
    mol0 = registry['molecules'][0]
    lig_obj = mol0['ligand'][0]
    slot_id = sorted(mol0['slots'])[0]
    target = mol0['slots'][slot_id][0]
    print('SMOKE-ENV game seed=42 defaults ligand=%s slots=%d '
          'picked=%s (slot %s)'
          % (lig_obj, len(mol0['slots']), target, slot_id), flush=True)

    # Scripted pick, the C-layer equivalent (smoke_07 recipe; P1-PICK).
    cmd.select('sele', '%s and name CA' % target)
    wiz.do_select('sele')
    check('scripted pick routes to molecule-0 slot r0c0',
          wiz._current_slot == slot_id and wiz._error is None,
          '_current_slot=%r want %r error=%r'
          % (wiz._current_slot, slot_id, wiz._error))

    # Identity view: script ONLY the rotation block; copy the 9-number
    # tail verbatim from the captured live view (smoke_07 PART B -- the
    # tail is build-dependent origin/dolly/clip state).
    live0 = list(cmd.get_view())
    tail = list(live0[9:])
    ident_view = [1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0] + tail
    cmd.set_view(ident_view)

    step = wizard_core.NUDGE_STEP
    rot_step = wizard_core.ROTATE_STEP_DEG
    print('SMOKE-ENV NUDGE_STEP=%.6f ROTATE_STEP_DEG=%.6f'
          % (step, rot_step), flush=True)

    def _drive(key_kind, code):
        """Drive ONE keyboard press through the REAL handler."""
        if key_kind == 'special':
            return wiz.do_special(code, 0, 0, 0)
        return wiz.do_key(code, 0, 0, 0)

    def _translation_press(name, key_kind, code, camera_step, live_view):
        """Owned nudge press: returns (ret, observed_dev, tol, ok-extras,
        detail). Expected world delta = view_camera_to_world(live_view,
        camera_step) * NUDGE_STEP."""
        before = _tofloat(geometry.centroid_of(target))
        ret = _drive(key_kind, code)
        after = _tofloat(geometry.centroid_of(target))
        want = _add(before, _scale(step, wizard_core
                                   .view_camera_to_world(live_view,
                                                         camera_step)))
        dev = _max_axis_dev(after, want)
        tol = _max_axis_tol(after, want)
        ident_ok = _is_identity(_obj_matrix(target))
        ok = (ret == 1 and dev <= tol and ident_ok
              and wiz._error is None)
        detail = ('dev=%.3g tol=%.3g ret=%r want_delta=%s identity=%s '
                  'error=%r'
                  % (dev, tol, ret, _fmt3(_sub(want, before)),
                     ident_ok, wiz._error))
        return ok, dev, detail

    # ============================================================
    # PART A: identity-view keyboard drives (expected deltas LITERAL)
    # ============================================================
    for name, tag, key_kind, code, camera_step, want_delta in (
            ('do_special(100) LEFT  -> -x', 'left', 'special', 100,
             (-1.0, 0.0, 0.0), (-step, 0.0, 0.0)),
            ('do_special(102) RIGHT -> +x', 'right', 'special', 102,
             (1.0, 0.0, 0.0), (step, 0.0, 0.0)),
            ("do_key('w')           -> +y", 'w', 'key', ord('w'),
             (0.0, 1.0, 0.0), (0.0, step, 0.0)),
            ("do_key('s')           -> -y", 's', 'key', ord('s'),
             (0.0, -1.0, 0.0), (0.0, -step, 0.0)),
            ("do_key('q')           -> -z", 'q', 'key', ord('q'),
             (0.0, 0.0, -1.0), (0.0, 0.0, -step)),
            ("do_key('e')           -> +z", 'e', 'key', ord('e'),
             (0.0, 0.0, 1.0), (0.0, 0.0, step))):
        live_id = list(cmd.get_view())
        ok, dev, detail = _translation_press(name, key_kind, code,
                                             camera_step, live_id)
        check(name, ok, detail)
        REC['partA_%s' % tag] = dev

    # ',' / '.' rotation keys: centroid about-view-axis rotation --
    # centroid preserved (CENTROID_TOL), atoms moved, matrix identity.
    for name, code, want_deg in (("do_key(',')  rotate_view(-%g)"
                                  % rot_step, ord(','), -rot_step),
                                 ("do_key('.')  rotate_view(+%g)"
                                  % rot_step, ord('.'), rot_step)):
        coords0 = geometry.coords_of(target)
        cen0 = _tofloat(geometry.centroid_of(target))
        ret = wiz.do_key(code, 0, 0, 0)
        cen1 = _tofloat(geometry.centroid_of(target))
        moved = _coords_maxdisp(target, coords0)
        cen_dev = _max_axis_dev(cen1, cen0)
        ident_ok = _is_identity(_obj_matrix(target))
        check(name,
              ret == 1 and cen_dev <= CENTROID_TOL and moved > 0.5
              and ident_ok and wiz._error is None,
              'ret=%r centroid dev=%.3g atoms moved=%.3g A '
              'identity=%s error=%r'
              % (ret, cen_dev, moved, ident_ok, wiz._error))
        REC['partA_rotate_centroid_dev'] = max(
            REC.get('partA_rotate_centroid_dev', 0.0), cen_dev)

    # ============================================================
    # PART B: dead-key + unowned-key pins (NO movement allowed)
    # ============================================================
    # UP/DOWN: the C-source law -- they co-fire command-line history
    # unconditionally (OrthoSpecial), so the wizard layer can NEVER own
    # them (the 03-06 recorded law; do_special's docstring).
    for name, key_kind, code, why in (
            ('do_special(101) UP    inert', 'special', 101,
             'UP co-fires command history (OrthoSpecial C law)'),
            ('do_special(103) DOWN  inert', 'special', 103,
             'DOWN co-fires command history (OrthoSpecial C law)'),
            ("do_key('z')           unowned", 'key', ord('z'),
             'not in _KEY_NUDGES and not a rotate key'),
            ('do_key(200) out-of-ASCII inert', 'key', 200,
             'k >= 127 -> ch=\'\' -> falls through')):
        cen0 = _tofloat(geometry.centroid_of(target))
        ret = _drive(key_kind, code)
        cen1 = _tofloat(geometry.centroid_of(target))
        dev = _max_axis_dev(cen1, cen0)
        check(name,
              ret is None and dev < 1e-9,
              'ret=%r centroid dev=%.3g -- %s' % (ret, dev, why))

    # ============================================================
    # PART C: scripted S2 rolled view -- keyboard drive + Toward pin
    # ============================================================
    # S2 = the FIXED historical rotation block captured in the P1 log
    # (P1-POSTSTART-VIEW). It is a synthetic orientation scripted
    # REGARDLESS of the live start composition -- the smoke never
    # re-derives this block from the running session, so any later
    # direction-control disposition keeps this smoke true.
    s2_block = (-0.447214, 0.894427, 0.0,
                -0.894427, -0.447214, 0.0,
                0.0, 0.0, 1.0)
    cmd.set_view(list(s2_block) + tail)
    live_s2 = list(cmd.get_view())
    r_s2 = list(live_s2[0:9])

    before = _tofloat(geometry.centroid_of(target))
    ret = wiz.do_special(102, 0, 0, 0)
    after = _tofloat(geometry.centroid_of(target))
    want_delta = _scale(step, wizard_core.view_camera_to_world(
        live_s2, (1.0, 0.0, 0.0)))
    want = _add(before, want_delta)
    dev = _max_axis_dev(after, want)
    tol = _max_axis_tol(after, want)
    observed = _sub(after, before)
    # P1's viewer-relative metric: the CAMERA-frame displacement
    # R.observed vs the intended screen step -- ~0.0000 deg expected.
    s_angle = _angle_deg(_apply_r(r_s2, observed), (1.0, 0.0, 0.0))
    ident_ok = _is_identity(_obj_matrix(target))
    check('S2 rolled view: do_special(102) lands on R^T.(+x)',
          ret == 1 and dev <= tol and ident_ok and wiz._error is None,
          'dev=%.3g tol=%.3g obs=%s screen_dir_angle=%.4f deg '
          'identity=%s error=%r'
          % (dev, tol, _fmt3(observed), s_angle, ident_ok, wiz._error))
    REC['partC_s2_dev'] = dev
    REC['partC_s2_screen_angle'] = s_angle

    # step_to_ligand WITH the rolled view still applied: the Toward
    # direction is view-INVARIANT (world-frame ligand centroid aim).
    # This pin lands at the CURRENT NUDGE_STEP -- the pre-evolution
    # baseline 08.2-06 deliberately evolves if the disposition changes
    # the Toward step (documented-evolution precedent 06-05/08.1).
    cen_s0 = _tofloat(geometry.centroid_of(target))
    lig_cen = _tofloat(geometry.centroid_of(lig_obj))
    d = _sub(lig_cen, cen_s0)
    dlen = _norm(d)
    want_s = _add(cen_s0, _scale(step / dlen, d))
    wiz.step_to_ligand()
    cen_s1 = _tofloat(geometry.centroid_of(target))
    dev_s = _max_axis_dev(cen_s1, want_s)
    tol_s = _max_axis_tol(cen_s1, want_s)
    ident_ok = _is_identity(_obj_matrix(target))
    check('S2 rolled view: step_to_ligand view-INVARIANT 1.0 A',
          dev_s <= tol_s and ident_ok and wiz._error is None,
          'dev=%.3g tol=%.3g (ligand distance %.3f -> %.3f A) '
          'identity=%s error=%r'
          % (dev_s, tol_s, dlen, _norm(_sub(lig_cen, cen_s1)),
             ident_ok, wiz._error))
    REC['partC_toward_dev'] = dev_s

    # ============================================================
    # PART D: full-SO(3) live pin (yaw+pitch+roll; the 03-04 yaw-only
    # control gap closed at smoke level)
    # ============================================================
    # S3 = Rx(30deg)*Ry(50deg)*Rz(20deg), row-major, hand-derived (the
    # SAME block as the 08.2-02 unit fixture). Derivation (deg):
    #   Rx(30) = [1 0 0; 0 c30 -s30; 0 s30 c30], c30=0.866025 s30=0.5
    #   Ry(50) = [c50 0 s50; 0 1 0; -s50 0 c50], c50=0.642788 s50=0.766044
    #   Rz(20) = [c20 -s20 0; s20 c20 0; 0 0 1], c20=0.939693 s20=0.342020
    #   row0 = 1*Rz20 row0 composed through Ry50 then Rx30 (Rx leaves
    #          row0 untouched): (0.604023, -0.219846,  0.766044)
    #   row1 = c30*(row1 of Ry50.Rz20) - s30*(row2): (0.656121, 0.682796,
    #          -0.321394)
    #   row2 = s30*(row1 of Ry50.Rz20) + c30*(row2): (-0.452395, 0.696747,
    #          0.556670)
    s3_block = (0.604023, -0.219846, 0.766044,
                0.656121, 0.682796, -0.321394,
                -0.452395, 0.696747, 0.556670)
    cmd.set_view(list(s3_block) + tail)
    live_s3 = list(cmd.get_view())
    r_s3 = list(live_s3[0:9])

    for name, tag, key_kind, code, camera_step in (
            ('S3 press RIGHT (+x)', 'px', 'special', 102, (1.0, 0.0, 0.0)),
            ('S3 press LEFT  (-x)', 'nx', 'special', 100, (-1.0, 0.0, 0.0)),
            ('S3 press UP    (+y)', 'py', 'key', ord('w'), (0.0, 1.0, 0.0)),
            ('S3 press DOWN  (-y)', 'ny', 'key', ord('s'), (0.0, -1.0, 0.0))):
        before = _tofloat(geometry.centroid_of(target))
        ret = _drive(key_kind, code)
        after = _tofloat(geometry.centroid_of(target))
        observed = _sub(after, before)
        want_delta = _scale(step, wizard_core.view_camera_to_world(
            live_s3, camera_step))
        dev = max(abs(observed[i] - want_delta[i]) for i in range(3))
        tol = max(_axis_tol(observed[i], want_delta[i])
                  for i in range(3))
        s_angle = _angle_deg(_apply_r(r_s3, observed), camera_step)
        ident_ok = _is_identity(_obj_matrix(target))
        ok = (ret == 1 and dev <= tol and ident_ok
              and wiz._error is None)
        # P1-PRESS-style per-press verdict line.
        print('SMOKE-23 PRESS %-18s obs=%s conv_dev=%.3g (tol %.3g) '
              'screen_dir_angle=%.4f deg identity=%s err=%r'
              % (name, _fmt3(observed), dev, tol, s_angle,
                 'OK' if ident_ok else 'FAIL', wiz._error), flush=True)
        check(name, ok, 'ret=%r dev=%.3g tol=%.3g' % (ret, dev, tol))
        REC['partD_%s' % tag] = dev

except Exception:
    traceback.print_exc()
    check('direction battery driver', False, 'raised (see traceback)')
finally:
    try:
        if ident_view is not None:
            cmd.set_view(ident_view)          # restore the identity view
    except Exception:
        pass
    try:
        cmd.set_wizard()
    except Exception:
        pass
    try:
        placement.cleanup_game_objects()
    except Exception:
        pass
    left = sorted(set(cmd.get_names('objects')) - set(pre_names))
    if left:
        print('SMOKE-23 CLEANUP WARNING leftover objects: %s' % (left,),
              flush=True)
    else:
        print('SMOKE-23 CLEANUP scene restored to pre-game names',
              flush=True)

# --- Worst-drift summary (the research evidence lines) ---------------
print('SMOKE-ENV worst drifts: %s'
      % dict((k, ('%.3g' % v if isinstance(v, float) else v))
             for k, v in sorted(REC.items())), flush=True)

# --- Verdict marker (the SOLE verdict carrier) --------------------------
print('=== SMOKE-23 %s ==='
      % ('FAIL: ' + ', '.join(failures) if failures else 'PASS'),
      flush=True)
