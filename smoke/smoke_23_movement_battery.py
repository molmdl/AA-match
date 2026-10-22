"""Headless smoke 23 - the 8.3 MOVEMENT BATTERY (plan 08.3-09 rework).

Run (from WSL, repo root):
    bash smoke/run_smoke.sh smoke/smoke_23_movement_battery.py 240
Verdict is carried by the printed marker (exit codes cannot carry
verdicts through the cmd.exe wrapper): grep '=== SMOKE-23 PASS ==='.
Timeout: 240 s (real game start + composition, as SMOKE-07/08).

PHASE 8.3 PIVOT REWORK (dated 2026-10-18 human design decision;
recorded disposition 2026-10-19 `smoke23_rename: yes`):
  RENAMED from smoke_23_direction_battery.py with `git mv` so git
  history follows the file. The ROSTER NUMBER 23 is preserved because
  run_smoke.sh derives SMOKE-NN from the basename digits (the 02-04
  sed rule) -- no runner edit; the printed marker stays SMOKE-23.
  THE KEYBOARD DIRECTION INPUT CLASS IS GONE from the production wizard
  (08.3-03 production deletion). This smoke's former keyboard-drive
  parts and dead-key/unowned-key inertness pins died WITH that class --
  by design, not by silent edit: their proof homes are now the
  tests/test_wizard_source.py AST pins (08.3-05) and the dated records.
  The retired full-SO(3) live keyboard proof has its DRAG successor in
  SMOKE-24 row 7 (owner plan 08.3-14, wave 5) -- it is NOT re-created
  here.
  WHAT KEEPS (rework-never-delete, 08.1-04/05/06 precedent): the
  real-game harness + REC machinery (PART 0) and the Toward
  view-invariance chain -- the PERMANENT home of the surviving movement
  op. Under a FIXED rolled view, step_to_ligand() must land the AA
  centroid EXACTLY TOWARD_STEP toward the LIVE ligand centroid (world/
  goal-directed, hence view-invariant), and a second press while the
  remaining distance exceeds TOWARD_STEP must shrink that distance by
  exactly TOWARD_STEP. The drag battery (gesture transforms, bake
  proofs) lives in SMOKE-24.

DATED EXPECTED-RED BRIDGE (captured 2026-10-23 on the post-08.3-03
tree, BEFORE this rework; quoted from the 08.3-03-SUMMARY roster):
  `bash smoke/run_smoke.sh smoke/smoke_23_direction_battery.py 240`
  -> PART 0 rows PASS (real game on stack; scripted pick -> r0c0), then
     FAIL at the harness read of the deleted wizard_core nudge-step
     constant:
         AttributeError: module 'aamatch.wizard_core' has no attribute
         <deleted nudge-step constant>
         -> '=== SMOKE-23 FAIL: direction battery driver ==='
  That RED is the expected bridge for a file-scoped battery; the rework
  below (import list trimmed to surviving names; keyboard/dead-key/
  R^T-keyboard/full-SO(3) parts removed behind the tombstones below)
  lands directly behind it. The verbatim receipt (with the constant's
  exact name) is transcribed in 08.3-09-SUMMARY.md.

PART 0  REAL GAME + SCRIPTED PICK (kept verbatim from the 08.2-04
        battery): gamestart.start_game() (DEFAULTS, seed 42, bundled
        manifest -- the P1 recipe; the REAL start path incl. the
        compose); the wizard is obtained via cmd.get_wizard();
        molecule-0 slot r0c0 picked through the REAL do_select
        (cmd.select('sele', ...) -> do_select('sele'), the C-layer
        equivalent, smoke_07 recipe).
PART M  TOWARD VIEW-INVARIANCE (the surviving movement op; formerly
        PART C(b)): the FIXED historical S2 rolled-view rotation block
        is applied (a synthetic orientation scripted REGARDLESS of the
        live start composition; only the 9-number tail is copied from
        the live view -- the smoke_07 PART B pattern), then
        step_to_ligand() must land the AA centroid EXACTLY TOWARD_STEP
        toward the LIVE ligand centroid (geometry.centroid_of of both
        objects), the object matrix identity clean; plus a convergence
        sanity press while the remaining distance > TOWARD_STEP that
        shrinks the AA->ligand distance by exactly TOWARD_STEP. The
        step is read from its single home wizard_core.TOWARD_STEP
        (2.5 A, Phase-8.2 2026-10-11 disposition; single-home law).

Conventions (frozen Phase 1, kept): anchor repo root via sys.argv first
/ cwd fallback (never __file__); import aamatch directly (module
identity 'aamatch'); every print on ONE line and flushed; explicit
space dicts in every iterate; no round() in compare expressions; no
calls to the placement.py banned cmd APIs -- cmd.get_object_matrix IS
legal and required (the identity-invariant re-assert); per-axis float32
tolerance (POSE_TOL + ULP_REL, the 02-15 contract); created game
objects deleted in a finally (scene restored to the pre-game names --
the probe's P1-CLEANUP pattern); a planned-check count assert at the
end so no planned row can be skipped silently.

Python floor: runs inside PyMOL's Windows Python (3.9); written 3.6-safe.
"""
import math
import os
import sys
import traceback


def _find_repo_root():
    """Anchor the repo root WITHOUT trusting __file__ (01-07 discovery:
    inside a -cq script __file__ points at pymol/__init__.py)."""
    mine = 'smoke_23_movement_battery.py'
    for arg in sys.argv:
        if arg.endswith(mine) and os.path.exists(arg):
            return os.path.dirname(os.path.dirname(os.path.abspath(arg)))
    return os.getcwd()


_ROOT = _find_repo_root()
print('SMOKE-ENV root:', _ROOT, flush=True)

failures = []
CHECKS = []               # ordered registry of every check run
REC = {}


def check(name, cond, detail=''):
    print('SMOKE-23 %-44s %s %s' % (name, 'PASS' if cond else 'FAIL',
                                    detail), flush=True)
    CHECKS.append(name)
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


pre_names = list(cmd.get_names('objects'))
ident_view = None
conv_ran = False

try:
    # ============================================================
    # PART 0: the REAL game + scripted pick (the P1 recipe; kept)
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
    # tail is build-dependent origin/dolly/clip state). Kept from the
    # pre-pivot harness as the smoke's teardown restore view.
    live0 = list(cmd.get_view())
    tail = list(live0[9:])
    ident_view = [1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0] + tail
    cmd.set_view(ident_view)

    # DELETED 2026-10-18 (pivot disposition; executed 08.3-03): the
    # identity-view keyboard nudge drives (LEFT/RIGHT, w/s, q/e) and the
    # ','/'.' fine-rotation key drives that used to live here. They died
    # WITH the keyboard input class, not silently: see the dated bridge
    # in this file's header + 08.3-03-SUMMARY.md. Their surviving proof
    # homes are the 08.3-05 AST pins.

    # ============================================================
    # PART M (formerly PART C(b)): Toward view-invariance -- the
    # permanent home of the surviving movement op
    # ============================================================
    # DELETED 2026-10-18 (pivot disposition; executed 08.3-03): the
    # former dead-key / unowned-key inertness pins (moot -- the wizard
    # owns no keys) and the rolled-view camera-step keyboard drive whose
    # full-SO(3) live pin died with the keyboard class (drag successor =
    # SMOKE-24 row 7, owner 08.3-14). Everything below is the KEPT
    # Toward chain, byte-preserved from the 08.2-04/08.2-06 battery.
    #
    # S2 = the FIXED historical rotation block captured in the P1 log
    # (P1-POSTSTART-VIEW). It is a synthetic orientation scripted
    # REGARDLESS of the live start composition -- the smoke never
    # re-derives this block from the running session, so any later
    # input-model change keeps this smoke true.
    s2_block = (-0.447214, 0.894427, 0.0,
                -0.894427, -0.447214, 0.0,
                0.0, 0.0, 1.0)
    cmd.set_view(list(s2_block) + tail)

    # step_to_ligand WITH the rolled view still applied: the Toward
    # direction is view-INVARIANT (world-frame ligand centroid aim).
    # The step is read from its single home wizard_core.TOWARD_STEP --
    # EVOLVED by 08.2-06 per the Phase-8.2 2026-10-11 disposition
    # (1.0 -> 2.5 A); dated EXPECTED-RED bridge 2026-10-11
    # (documented-evolution precedent 06-05/08.1, rework-never-delete).
    toward_step = wizard_core.TOWARD_STEP
    cen_s0 = _tofloat(geometry.centroid_of(target))
    lig_cen = _tofloat(geometry.centroid_of(lig_obj))
    d = _sub(lig_cen, cen_s0)
    dlen = _norm(d)
    want_s = _add(cen_s0, _scale(toward_step / dlen, d))
    wiz.step_to_ligand()
    cen_s1 = _tofloat(geometry.centroid_of(target))
    dev_s = _max_axis_dev(cen_s1, want_s)
    tol_s = _max_axis_tol(cen_s1, want_s)
    ident_ok = _is_identity(_obj_matrix(target))
    check('S2 rolled view: step_to_ligand view-INVARIANT TOWARD_STEP',
          dev_s <= tol_s and ident_ok and wiz._error is None,
          'dev=%.3g tol=%.3g (ligand distance %.3f -> %.3f A) '
          'identity=%s error=%r'
          % (dev_s, tol_s, dlen, _norm(_sub(lig_cen, cen_s1)),
             ident_ok, wiz._error))
    REC['partM_toward_dev'] = dev_s

    # 08.2-06 convergence sanity (the smoke_07 shape): while the
    # AA->ligand distance remains > TOWARD_STEP, a second press shrinks
    # that distance by exactly TOWARD_STEP -- unchanged geometry, same
    # unit direction, identity clean after both presses (rolled view
    # STILL applied -- view-invariance holds per press).
    #
    # The row ALWAYS runs (the planned-check count below stays fixed):
    # with the seed-42 default geometry the start distance is ~13.8 A,
    # so the precondition holds; should the composition ever change, the
    # unmet precondition is reported as a LOUD FAIL, never skipped.
    dist_s1 = _norm(_sub(lig_cen, cen_s1))
    conv_ok = False
    if dist_s1 > toward_step:
        conv_ran = True
        wiz.step_to_ligand()
        cen_s2 = _tofloat(geometry.centroid_of(target))
        dist_s2 = _norm(_sub(lig_cen, cen_s2))
        shrink = dist_s1 - dist_s2
        tol_shrink = POSE_TOL + ULP_REL * max(dist_s1, dist_s2)
        ident_ok = _is_identity(_obj_matrix(target))
        conv_ok = (abs(shrink - toward_step) <= tol_shrink
                   and ident_ok and wiz._error is None)
        conv_detail = ('shrink=%.3g tol=%.3g want=%.6f (ligand distance '
                       '%.3f -> %.3f A) identity=%s error=%r'
                       % (shrink, tol_shrink, toward_step, dist_s1,
                          dist_s2, ident_ok, wiz._error))
    else:
        conv_detail = ('precondition unmet: AA->ligand distance %.3f A '
                       '<= TOWARD_STEP %.3f A -- convergence press not '
                       'exercised' % (dist_s1, toward_step))
    check('S2 rolled view: second Toward press shrinks AA->ligand '
          'distance by exactly TOWARD_STEP',
          conv_ok, conv_detail)

except Exception:
    traceback.print_exc()
    check('movement battery driver', False, 'raised (see traceback)')
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
print('SMOKE-ENV convergence press ran: %s' % (conv_ran,), flush=True)

# --- Check-count assert: every planned row must have run ----------------
# (4 planned checks precede this one: PART 0 x2, PART M x2. An exception
# path inserts the unplanned 'movement battery driver' row and the count
# fails loudly -- no planned row may be skipped silently.)
PLANNED_CHECKS = 4
check('planned check count (all battery rows ran)',
      len(CHECKS) == PLANNED_CHECKS,
      'ran=%d want=%d (+ this count row)' % (len(CHECKS), PLANNED_CHECKS))

# --- Verdict marker (the SOLE verdict carrier) --------------------------
print('=== SMOKE-23 %s ==='
      % ('FAIL: ' + ', '.join(failures) if failures else 'PASS'),
      flush=True)
