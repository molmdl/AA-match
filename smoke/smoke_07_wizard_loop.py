"""Headless smoke 07 - the E2E WIZARD GAMEPLAY LOOP (plan 03-04).

Run (from WSL, repo root):
    bash smoke/run_smoke.sh smoke/smoke_07_wizard_loop.py 240
Verdict is carried by the printed marker (exit codes cannot carry
verdicts through the cmd.exe wrapper): grep '=== SMOKE-07 PASS ==='.

PLAY-01..04's headless half (only real-mouse delivery remains for the
human checkpoints, plans 03-06/03-07). Proves the 03-03 GameWizard
end-to-end in REAL headless PyMOL:

PART 0  env + the deterministic SMOKE-04 game (block_exclusive
        [pi_stacking], molecules 1, D 3, seed 42, benzamide candidate)
        + mouse-mode baseline (button_mode 0, mouse_selection_mode 1 on
        stock).
PART A  ACTIVATION + ROUTING + RECOLOR: activate() pushes the wizard,
        snapshots then zeroes msm; scripted do_select routes a pick to
        slot identity, recolors it HIGHLIGHT_COLOR, deletes the
        transient 'sele' and CONSUMES pk1 via do_pick's hygiene unpick
        (probe-pinned: unpick deletes the pk1 selection buffer in this
        build, so cleanup's pk1 deletion is a defensive no-op -- the
        plan's "pk1 present but unpicked" expectation was superseded by
        the live build, Rule-1 deviation recorded in 03-04-SUMMARY.md);
        a switch restores the previous object's snapshotted colors
        first; ligand / scratch / empty-space picks are NO-OPs.
PART B  MOVEMENT + THE IDENTITY INVARIANT: wizard_core.
        view_camera_to_world is LIVE-VERIFIED against a scripted
        cmd.set_view (only the 3x3 rotation block is scripted; the tail
        is copied verbatim from the captured view -- build-dependent);
        nudge_cam presses displace the centroid by exactly NUDGE_STEP
        steps along the scripted world vector with the object matrix
        identity after every press; rotate_view / rotate_axis keep the
        centroid (rotation about the centroid) and move atoms;
        step_to_ligand lands exactly 1.0 A towards the ligand centroid.
PART C  CONFIRM COMPOSITION (the PLAY-02 payoff): after the explicit
        baked ring-alignment step (02-14 decision -- a pure translate
        cannot fix ring orientation; implemented via the wizard's own
        rotate_axis) and move_to so the AA ring sits 4.5 A above the
        ligand ring center, confirm_molecule scores 1.0 with
        pi_stacking formed, the result text renders in the live wizard
        panel + prompt, and the engine GameState recorded the result
        (re-Confirm-accumulates caveat documented -- Phase 6 owns
        score-once).
PART D  RESET + RESTORE (PLAY-03/04): reset_grid replays grid positions
        (rotations persist -- recorded 03-03 option a), re-detect is
        zero, _result clears, selection + recolor persist; the panel
        Done path (canonical cmd.set_wizard()) runs cleanup: msm back
        to the pre-game snapshot, pk1 deleted, selected slot's colors
        restored, game objects STILL PRESENT, get_wizard() None, stack
        empty; cleanup() is idempotent.
PART E  MULTI-MOLECULE SCOPING: a second DEFAULTS-shaped 2-molecule
        game documents the molecule-0 scoping decision (a molecule-1 AA
        pick leaves _current_slot None); teardown returns the scene to
        the pre-game snapshot EXACTLY.
PART F  THE 03-06 FIELD BUG BATTERIES (checkpoint fix pass):
        (1) the FULL multi-switch click sequence from the field report
        (mol-0 re-click chain incl. a same-slot re-click, then ligand /
        other-molecule no-op interleave) asserting AT DATA LEVEL the
        invariants the GUI must show: exactly ONE green AA at any time
        (the current selection), a switch restores the previous object
        EXACTLY, a same-slot re-click changes nothing, ligand /
        non-game / other-molecule picks change nothing, and Reset
        restores every recolored object except the current selection
        (the selection's green is intended); (2) a rebuild spy proves
        the switch path re-issues the restored object's DISPLAY lists
        (the field bug's root cause: cmd.alter restores the data but
        leaves the stale drawn lists on screen until some later op
        rebuilds them -- headless could never see that; the spy makes
        the display path mechanical); (3) the cross-molecule scoring
        guard: with mol-0 scored, a mol-0 charged AA parked on mol-1's
        ligand provably forms an interaction in the WHOLE-SCENE
        detect() yet confirm_molecule()/engine.confirm returns the
        scope -- score 0.00, empty result -- the wrong-ligand record
        can no longer count.

Pick scripting (real-mouse delivery is the human checkpoint,
03-RESEARCH-wizard-interaction.md SS8): the C layer would route a
click as cmd.select('sele', '<slot object> and name CA') ->
do_select('sele'); the smoke scripts exactly that.

Conventions (frozen Phase 1, kept): anchor repo root via sys.argv first
/ cwd fallback (never __file__); import aamatch directly (module
identity 'aamatch' -- NEVER the pmg_tk.startup path in the same
session); every print on ONE line and flushed; explicit space dicts in
every iterate; no round() in expressions; no calls to the placement.py
banned cmd APIs anywhere -- cmd.get_object_matrix IS legal and required
(the identity-invariant re-assert); per-axis float32 tolerance
(POSE_TOL + ULP_REL, the 02-15 contract).

Python floor: runs inside PyMOL's Windows Python (3.9); written 3.6-safe.
"""
import math
import os
import sys
import traceback


def _find_repo_root():
    """Anchor the repo root WITHOUT trusting __file__ (01-07 discovery:
    inside a -cq script __file__ points at pymol/__init__.py)."""
    mine = 'smoke_07_wizard_loop.py'
    for arg in sys.argv:
        if arg.endswith(mine) and os.path.exists(arg):
            return os.path.dirname(os.path.dirname(os.path.abspath(arg)))
    return os.getcwd()


_ROOT = _find_repo_root()
print('SMOKE-ENV root:', _ROOT, flush=True)

failures = []
REC = {}


def check(name, cond, detail=''):
    print('SMOKE-07 %-40s %s %s' % (name, 'PASS' if cond else 'FAIL',
                                    detail), flush=True)
    if not cond:
        failures.append(name)


if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from pymol import cmd  # noqa: E402

from aamatch.persistence import read_json_file  # noqa: E402
from aamatch.manifest import parse_manifest_dict, enumerate_entries  # noqa: E402
from aamatch.setup_state import validate_state  # noqa: E402
from aamatch import engine, geometry, placement, wizard_core  # noqa: E402
from aamatch.wizard import GameWizard  # noqa: E402
from aamatch.detector import extract_features  # noqa: E402
from aamatch.thresholds import PISTACK_ANGLE_TOL_DEG  # noqa: E402

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


def _color_map(obj):
    """{int(ID): int(color)} -- the PLAY-01 read-back (explicit space
    dict, uppercase ID, no round() -- Pitfall-8 conformant)."""
    rows = []
    cmd.iterate(obj, 'stored.append((ID, color))', space={'stored': rows})
    return dict((int(atom_id), int(color)) for (atom_id, color) in rows)


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


def _selections():
    return list(cmd.get_names('selections'))


def _script_pick(wiz, selection):
    """Drive a pick the way the C layer does (RESEARCH SS8):
    cmd.select('sele', selection) -> do_select('sele')."""
    cmd.select('sele', selection)
    wiz.do_select('sele')


# ============================================================
# PART 0: env + the deterministic SMOKE-04 game
# ============================================================
pre_names = list(cmd.get_names('objects'))
pre_msm = None
payload = registry = mol_payload = required = None
aa1_obj = aa2_obj = req_obj = lig_obj = slot1 = slot2 = req_slot = None
pre_colors1 = pre_colors2 = pre_colors_req = None
try:
    check('clean pre-game scene',
          not [n0 for n0 in pre_names
               if n0.startswith(geometry.GAME_PREFIX)],
          'pre names: %s' % pre_names)
    pre_msm = int(cmd.get('mouse_selection_mode'))
    pre_button_mode = int(cmd.get('button_mode'))
    REC['pre_msm'] = pre_msm
    REC['pre_button_mode'] = pre_button_mode
    check('stock mouse modes', pre_button_mode == 0 and pre_msm == 1,
          'button_mode=%d (expect 0) mouse_selection_mode=%d (expect 1 '
          'on stock)' % (pre_button_mode, pre_msm))

    container = read_json_file(os.path.join(
        _ROOT, 'aamatch', 'data', 'MANIFEST.json'))
    entries = enumerate_entries(parse_manifest_dict(container))
    benz_rows = [row for row in entries
                 if row['entry_id'] == 'benzamide']
    benz = benz_rows[0] if benz_rows else None
    check('benzamide candidate', benz is not None,
          benz['file'] if benz else 'entry_id benzamide not in manifest')

    setup = validate_state({'interaction_mode': 'block_exclusive',
                            'allowed_interactions': ['pi_stacking'],
                            'molecules_per_level': 1,
                            'difficulty_levels': 3})
    payload, rows = engine.new_game(setup, 42, candidates=[benz])
    check('new_game scene untouched',
          list(cmd.get_names('objects')) == pre_names,
          'new_game loads temps only and deletes them')
    level0 = payload['levels'][0]
    n = level0['difficulty']['grid_n']
    mol_payload = level0['molecules'][0]
    required = mol_payload['required']

    registry = engine.materialize(payload, level_index=0)
    post_names = list(cmd.get_names('objects'))
    grew = sorted(set(post_names) - set(pre_names))
    check('materialize object growth', len(grew) == 1 + n * n,
          'grew=%d want %d' % (len(grew), 1 + n * n))

    molecule0 = registry['molecules'][0]
    lig_obj = molecule0['ligand'][0]
    slot_ids = sorted(molecule0['slots'])
    slot1, slot2 = slot_ids[0], slot_ids[1]
    aa1_obj = molecule0['slots'][slot1][0]
    aa2_obj = molecule0['slots'][slot2][0]

    req_slots = [s for s in mol_payload['grid']['slots']
                 if s.get('role') == 'required'
                 and 'pi_stacking' in (s.get('can_form') or ())]
    check('one required pi_stacking slot', len(req_slots) == 1,
          '%d slot(s)' % len(req_slots))
    req_slot = req_slots[0]['slot_id']
    req_obj = molecule0['slots'][req_slot][0]
    print('SMOKE-ENV game n=%d slots=%d required=%s (%s)'
          % (n, len(slot_ids), req_slot, req_obj), flush=True)

    records0 = engine.detect()
    pi0 = [r for r in records0 if r['type'] == 'pi_stacking']
    check('grid yields zero pi_stacking', not pi0,
          'records=%d pi=%d' % (len(records0), len(pi0)))
except Exception:
    traceback.print_exc()
    check('part 0 setup', False, 'raised (see traceback above)')
    payload = registry = None

# ============================================================
# PART A: activation + routing + recolor + switch + no-ops
# ============================================================
wiz = None
try:
    if registry is None:
        raise RuntimeError('part 0 failed')
    wiz = GameWizard(payload, registry, 0, 0)
    wiz.activate()
    check('activate pushes the wizard', cmd.get_wizard() is wiz,
          'stack top=%r' % (cmd.get_wizard(),))
    msm_now = int(cmd.get('mouse_selection_mode'))
    check('activate zeroes msm after snapshot',
          msm_now == 0 and wiz._saved_msm == pre_msm,
          'msm=%d saved=%r (pre=%d)' % (msm_now, wiz._saved_msm, pre_msm))
    panel = cmd.get_wizard().get_panel()
    kinds_ok = all(len(e) == 3 and e[0] in (0, 1, 2) for e in panel)
    check('panel entries all 3-element valid kinds', kinds_ok,
          '%d entries, kinds=%s'
          % (len(panel), sorted(set(e[0] for e in panel))))
    prompt = cmd.get_wizard().get_prompt()
    check('prompt carries the click instruction',
          bool(prompt) and 'Click an amino acid' in prompt[0],
          'prompt[0]=%r' % (prompt[0] if prompt else None,))

    # -- scripted pick #1: route to slot identity + recolor ----------
    pre_colors1 = _color_map(aa1_obj)
    _script_pick(wiz, '%s and name CA' % aa1_obj)
    check('pick routes to slot identity', wiz._current_slot == slot1,
          '_current_slot=%r want %r' % (wiz._current_slot, slot1))
    green = int(cmd.get_color_index(wizard_core.HIGHLIGHT_COLOR))
    now1 = _color_map(aa1_obj)
    green_ok = bool(now1) and all(c == green for c in now1.values())
    check('picked object recolored highlight', green_ok,
          'all %d atoms color==%d (%s)' % (len(now1), green,
                                           wizard_core.HIGHLIGHT_COLOR))
    check('transient sele deleted, pk1 consumed by do_pick unpick',
          'sele' not in _selections() and 'pk1' not in _selections(),
          'selections=%s (probe-pinned: unpick deletes the pk1 buffer '
          'in this build; cleanup\'s pk1 deletion is defensive)'
          % (_selections(),))

    # -- switch: old object's colors restored, new slot recolored -----
    pre_colors2 = _color_map(aa2_obj)
    _script_pick(wiz, '%s and name CA' % aa2_obj)
    back1 = _color_map(aa1_obj)
    check('switch restores previous colors first',
          back1 == pre_colors1,
          'restored rows match the pre-recolor snapshot exactly')
    now2 = _color_map(aa2_obj)
    check('switch recolors the new slot',
          wiz._current_slot == slot2 and bool(now2)
          and all(c == green for c in now2.values()),
          '_current_slot=%r, %d atoms recolored'
          % (wiz._current_slot, len(now2)))

    # -- no-ops: ligand pick, scratch-object pick, empty-space pick ---
    _script_pick(wiz, '%s and name C' % lig_obj)
    check('ligand pick is a no-op', wiz._current_slot == slot2,
          '_current_slot=%r (unchanged)' % (wiz._current_slot,))
    scratch = 'zz_smoke07_scratch'
    try:
        cmd.fragment('ala', scratch, zoom=0)
        check('scratch object born', cmd.count_atoms(scratch) > 0,
              'name=%s' % scratch)
        _script_pick(wiz, '%s and name CA' % scratch)
        check('scratch pick is a no-op', wiz._current_slot == slot2,
              '_current_slot=%r (user objects are not slots)'
              % (wiz._current_slot,))
    finally:
        if scratch in cmd.get_names('objects'):
            cmd.delete(scratch)
    cmd.select('sele', 'none')
    wiz.do_select('sele')
    check('empty-space pick is a no-op',
          wiz._current_slot == slot2
          and wiz._error is None,
          '_current_slot=%r error=%r' % (wiz._current_slot, wiz._error))
except Exception:
    traceback.print_exc()
    check('part A activation/routing', False, 'raised (see traceback)')

# ============================================================
# PART B: movement + identity invariant (live R^T verification)
# ============================================================
try:
    if wiz is None or wiz._current_slot != slot2:
        raise RuntimeError('part A failed')
    sel_obj = aa2_obj

    # Identity view: script the rotation block, copy the tail verbatim.
    view0 = list(cmd.get_view())
    ident_tail = list(view0[9:])
    ident_view = [1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0] \
        + ident_tail
    cmd.set_view(ident_view)
    w_ident = wizard_core.view_camera_to_world(cmd.get_view(), (1, 0, 0))
    check('camera->world identity pass-through',
          _max_axis_dev(w_ident, (1.0, 0.0, 0.0)) <= 1e-9,
          'view_camera_to_world(identity, (1,0,0))=%r' % (w_ident,))

    # LIVE R^T convention check: rotation block Rz(90deg) (world->camera
    # row-major), every remaining entry copied verbatim from the captured
    # view's tail -- only the rotation block is scripted.
    rz90_view = [0.0, -1.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0] \
        + ident_tail
    cmd.set_view(rz90_view)
    cen_rt0 = _tofloat(geometry.centroid_of(sel_obj))
    wiz.nudge_cam(1, 0, 0)
    cen_rt1 = _tofloat(geometry.centroid_of(sel_obj))
    # R^T . (1,0,0) over the scripted Rz(90deg) block = (r00, r01, r02)
    # = (0, -1, 0); expected displacement (0, -NUDGE_STEP, 0).
    want_rt = (cen_rt0[0], cen_rt0[1] - wizard_core.NUDGE_STEP,
               cen_rt0[2])
    dev_rt = _max_axis_dev(cen_rt1, want_rt)
    tol_rt = _max_axis_tol(cen_rt1, want_rt)
    check('LIVE R^T: nudge lands on the scripted world vector',
          dev_rt <= tol_rt and wiz._error is None,
          'dev=%.3g tol=%.3g (R^T.(1,0,0)=(0,-1,0) x %g A) error=%r'
          % (dev_rt, tol_rt, wizard_core.NUDGE_STEP, wiz._error))
    REC['rt_live_dev'] = dev_rt
    cmd.set_view(ident_view)                     # restore the identity view

    # Three nudge presses: exactly 3 x NUDGE_STEP along world X, the
    # identity object matrix re-asserted after EVERY press.
    cen_n0 = _tofloat(geometry.centroid_of(sel_obj))
    ident_every_press = True
    for _press in range(3):
        wiz.nudge_cam(1, 0, 0)
        ident_every_press = ident_every_press and \
            _is_identity(_obj_matrix(sel_obj))
    cen_n1 = _tofloat(geometry.centroid_of(sel_obj))
    want_n = _add(cen_n0, (3.0 * wizard_core.NUDGE_STEP, 0.0, 0.0))
    dev_n = _max_axis_dev(cen_n1, want_n)
    tol_n = _max_axis_tol(cen_n1, want_n)
    check('3 nudges displace exactly 3x NUDGE_STEP world-X',
          dev_n <= tol_n and ident_every_press and wiz._error is None,
          'dev=%.3g tol=%.3g identity-after-every-press=%s'
          % (dev_n, tol_n, ident_every_press))
    REC['nudge3_dev'] = dev_n

    # rotate_view(90): centroid unchanged (rotation about the centroid),
    # atoms moved, matrix identity.
    coords_r0 = geometry.coords_of(sel_obj)
    cen_rv0 = _tofloat(geometry.centroid_of(sel_obj))
    wiz.rotate_view(90.0)
    cen_rv1 = _tofloat(geometry.centroid_of(sel_obj))
    coords_r1 = geometry.coords_of(sel_obj)
    moved_rv = _coords_maxdisp(coords_r0, coords_r1)
    cen_dev_rv = _max_axis_dev(cen_rv1, cen_rv0)
    check('rotate_view keeps centroid, moves atoms, identity',
          cen_dev_rv <= CENTROID_TOL and moved_rv > 0.5
          and _is_identity(_obj_matrix(sel_obj)) and wiz._error is None,
          'centroid dev=%.3g atoms moved=%.3g A'
          % (cen_dev_rv, moved_rv))
    REC['rotate_view_centroid_dev'] = cen_dev_rv

    # rotate_axis((0,1,0), 90, origin=centroid): same contract.
    cen_ra0 = _tofloat(geometry.centroid_of(sel_obj))
    wiz.rotate_axis((0.0, 1.0, 0.0), 90.0, origin=cen_ra0)
    cen_ra1 = _tofloat(geometry.centroid_of(sel_obj))
    coords_r2 = geometry.coords_of(sel_obj)
    moved_ra = _coords_maxdisp(coords_r1, coords_r2)
    cen_dev_ra = _max_axis_dev(cen_ra1, cen_ra0)
    check('rotate_axis keeps centroid, moves atoms, identity',
          cen_dev_ra <= CENTROID_TOL and moved_ra > 0.5
          and _is_identity(_obj_matrix(sel_obj)) and wiz._error is None,
          'centroid dev=%.3g atoms moved=%.3g A'
          % (cen_dev_ra, moved_ra))
    REC['rotate_axis_centroid_dev'] = cen_dev_ra

    # step_to_ligand: centroid lands exactly 1.0 A towards the ligand
    # centroid (the scripted 02-09 direction).
    cen_s0 = _tofloat(geometry.centroid_of(sel_obj))
    lig_cen = _tofloat(geometry.centroid_of(lig_obj))
    d = _sub(lig_cen, cen_s0)
    dlen = _norm(d)
    want_s = _add(cen_s0,
                  _scale(wizard_core.NUDGE_STEP / dlen, d))
    wiz.step_to_ligand()
    cen_s1 = _tofloat(geometry.centroid_of(sel_obj))
    dev_s = _max_axis_dev(cen_s1, want_s)
    tol_s = _max_axis_tol(cen_s1, want_s)
    check('step_to_ligand lands 1.0 A toward the ligand',
          dev_s <= tol_s and _is_identity(_obj_matrix(sel_obj))
          and wiz._error is None,
          'dev=%.3g tol=%.3g (ligand distance %.3f -> %.3f A)'
          % (dev_s, tol_s, dlen,
             _norm(_sub(lig_cen, cen_s1))))
    REC['step_to_ligand_dev'] = dev_s
except Exception:
    traceback.print_exc()
    check('part B movement', False, 'raised (see traceback above)')

# ============================================================
# PART C: confirm composition -- the PLAY-02 payoff
# ============================================================
try:
    if registry is None:
        raise RuntimeError('part 0 failed')

    # Select the REQUIRED slot via a scripted pick.
    pre_colors_req = _color_map(req_obj)
    _script_pick(wiz, '%s and name CA' % req_obj)
    check('required slot selected via pick', wiz._current_slot == req_slot,
          '_current_slot=%r want %r' % (wiz._current_slot, req_slot))

    # Ring centers/normals from the SAME feature layer detect() uses
    # (SMOKE-04 lines 292-320 shape).
    records_live = geometry.extract_game_atoms()
    bonds, index_to_id = geometry.ligand_bonds(lig_obj)
    _, lig_remap = _remap_ligand_bonds(records_live, bonds, index_to_id)
    features = extract_features(records_live, lig_remap)
    lig_ring = features['lig']['rings'][0]
    aa_ring = features['aa'][req_obj]['rings'][0]
    n_l = _tofloat(lig_ring['normal'])
    n_a = _tofloat(aa_ring['normal'])
    d_n = _dot(n_a, n_l)
    target_n = n_l if d_n >= 0.0 else _scale(-1.0, n_l)
    line_angle = math.degrees(math.acos(abs(max(-1.0, min(1.0, d_n)))))
    print('SMOKE-ENV placement slot=%s line_angle=%.3f deg'
          % (req_slot, line_angle), flush=True)

    # The explicit baked ring-alignment step (02-14 decision): a pure
    # translate CANNOT fix orientation; route the Rodrigues alignment
    # through the wizard's own rotate_axis about the ring center.
    if line_angle > PISTACK_ANGLE_TOL_DEG:
        k = _cross(n_a, target_n)
        ang = math.degrees(math.acos(max(-1.0, min(1.0,
                                                   _dot(n_a, target_n)))))
        origin_c = _tofloat(aa_ring['center'])
        wiz.rotate_axis(_scale(1.0 / max(_norm(k), 1e-12), k), ang,
                        origin=origin_c)
        records_live = geometry.extract_game_atoms()
        features = extract_features(records_live, lig_remap)
        aa_ring = features['aa'][req_obj]['rings'][0]
        lig_ring = features['lig']['rings'][0]
        n_l = _tofloat(lig_ring['normal'])
        n_a = _tofloat(aa_ring['normal'])
        new_angle = math.degrees(math.acos(abs(
            max(-1.0, min(1.0, _dot(n_a, n_l))))))
        check('ring alignment baked via wizard rotate_axis',
              new_angle <= 1e-3 and wiz._error is None,
              'was %.3f -> %.6f deg' % (line_angle, new_angle))
    else:
        check('ring alignment already fine', True,
              'natural line_angle %.3f <= %.1f deg'
              % (line_angle, float(PISTACK_ANGLE_TOL_DEG)))

    # move_to: the AA ring center lands 4.5 A directly above the ligand
    # ring center (offset ~ 0 -> the P-subtype construction).
    aa_center = _tofloat(aa_ring['center'])
    lig_center = _tofloat(lig_ring['center'])
    ring_target = _add(lig_center, _scale(4.5, n_l))
    position = _add(_tofloat(geometry.centroid_of(req_obj)),
                    _sub(ring_target, aa_center))
    wiz.move_to(position)
    records_live = geometry.extract_game_atoms()
    features = extract_features(records_live, lig_remap)
    placed_center = _tofloat(
        features['aa'][req_obj]['rings'][0]['center'])
    drift_c = _max_axis_dev(placed_center, ring_target)
    check('move_to places the ring at the target',
          drift_c < 1e-4 and _is_identity(_obj_matrix(req_obj))
          and wiz._error is None,
          'drift=%.2g' % drift_c)

    # CONFIRM: the engine.confirm composition scores the moved pose.
    wiz.confirm_molecule()
    res = wiz._result
    check('confirm scores the placed pose 1.0',
          res is not None and res['score'] == 1.0
          and 'pi_stacking' in res['formed'] and wiz._error is None,
          'result=%r error=%r' % (res, wiz._error))

    # The result text renders in the LIVE wizard (wizard_text output).
    panel_c = cmd.get_wizard().get_panel()
    prompt_c = cmd.get_wizard().get_prompt()
    panel_lines = [e[1] for e in panel_c if e[0] == 1]
    want_lines = ['1/1 required interactions formed (score 1.00)',
                  'Formed: pi_stacking']
    check('result lines in panel and prompt',
          all(any(w in line for line in panel_lines) for w in want_lines)
          and all(any(w in line for line in prompt_c)
                  for w in want_lines),
          'panel=%r prompt=%r' % (panel_lines, prompt_c))

    # Engine GameState recorded the result (re-Confirm-accumulates
    # caveat: Phase 6 owns score-once semantics -- recorded behavior).
    gs = engine._game
    scores = list(gs.molecule_scores) if gs is not None else []
    check('engine recorded the molecule score',
          len(scores) >= 1 and scores[-1] == 1.0,
          'molecule_scores=%r' % (scores,))
except Exception:
    traceback.print_exc()
    check('part C confirm composition', False, 'raised (see traceback)')

# ============================================================
# PART D: reset + the full cleanup restore table (Done path)
# ============================================================
try:
    if registry is None:
        raise RuntimeError('part 0 failed')

    wiz.reset_grid()
    molecule0 = registry['molecules'][0]
    offset = molecule0['offset']
    worst_reset = 0.0
    reset_fail = []
    for slot in mol_payload['grid']['slots']:
        target = placement.effective_position(
            slot['grid_pose']['position'], offset)
        centroid = geometry.centroid_of(
            molecule0['slots'][slot['slot_id']][0])
        dev = _max_axis_dev(_tofloat(centroid), _tofloat(target))
        tol = _max_axis_tol(_tofloat(centroid), _tofloat(target))
        worst_reset = max(worst_reset, dev)
        if dev > tol:
            reset_fail.append('%s(%.2g)' % (slot['slot_id'], dev))
    REC['reset_worst_dev'] = worst_reset
    check('reset_grid replays grid positions', not reset_fail,
          'worst=%.2g (02-15 pose tolerance)%s'
          % (worst_reset,
             ' FAIL: ' + ', '.join(reset_fail) if reset_fail else ''))
    records_d = engine.detect()
    pi_d = [r for r in records_d if r['type'] == 'pi_stacking']
    check('reset clears the interaction', not pi_d,
          'records=%d pi=%d' % (len(records_d), len(pi_d)))
    mats_ok = all(_is_identity(_obj_matrix(ob))
                  for ob in [e[0] for e in molecule0['slots'].values()])
    check('all AA matrices identity after reset', mats_ok,
          'checked %d objects' % len(molecule0['slots']))
    check('reset clears the stale result, keeps selection + recolor',
          wiz._result is None and wiz._current_slot == req_slot
          and all(c == int(cmd.get_color_index(
              wizard_core.HIGHLIGHT_COLOR))
              for c in _color_map(req_obj).values()),
          '_result=%r _current_slot=%r'
          % (wiz._result, wiz._current_slot))

    # ---- The Done path: canonical cmd.set_wizard() runs cleanup. ----
    game_names = sorted(set(cmd.get_names('objects')) - set(pre_names))
    cmd.set_wizard()
    msm_after = int(cmd.get('mouse_selection_mode'))
    check('Done restores the msm snapshot (never hard-coded 0)',
          msm_after == pre_msm,
          'msm=%d snapshot=%d' % (msm_after, pre_msm))
    check('Done leaves no pk1 pick buffer', 'pk1' not in _selections(),
          'selections=%s (pk1 already consumed by do_pick\'s unpick; '
          'cleanup\'s delete is the defensive post-Done guarantee)'
          % (_selections(),))
    back_req = _color_map(req_obj)
    check('Done restores the selected slot colors',
          back_req == pre_colors_req,
          'restored rows match the PART-C pre-recolor snapshot')
    back2 = _color_map(aa2_obj)
    check('Done restores every recolored slot',
          back2 == pre_colors2,
          'slot2 rows match the PART-A pre-recolor snapshot')
    post_done = list(cmd.get_names('objects'))
    still = sorted(set(post_done) - set(pre_names))
    check('Done NEVER deletes game objects', still == game_names,
          'game objects still present: %d' % len(still))
    check('Done pops the wizard stack',
          cmd.get_wizard() is None
          and not (cmd.get_wizard_stack() or []),
          'get_wizard()=%r stack=%r'
          % (cmd.get_wizard(), cmd.get_wizard_stack()))

    # Idempotence: a second cleanup() raises nothing and changes nothing.
    names_before = list(cmd.get_names('objects'))
    msm_before = int(cmd.get('mouse_selection_mode'))
    wiz.cleanup()
    check('cleanup is idempotent',
          list(cmd.get_names('objects')) == names_before
          and int(cmd.get('mouse_selection_mode')) == msm_before,
          'second cleanup(): no exception, scene/msn unchanged')

    placement.cleanup_game_objects()
    check('game-1 teardown leaves scene pre-game',
          list(cmd.get_names('objects')) == pre_names,
          'post=%s' % list(cmd.get_names('objects')))
except Exception:
    traceback.print_exc()
    check('part D reset/restore', False, 'raised (see traceback above)')
    placement.cleanup_game_objects()

# ============================================================
# PART E: multi-molecule scoping (molecule-0 pick map documented)
# ============================================================
try:
    all_entries = entries
    setup2 = validate_state({'interaction_mode': 'unset',
                             'molecules_per_level': 2,
                             'difficulty_levels': 3})
    payload2, rows2 = engine.new_game(setup2, 42,
                                      candidates=list(all_entries))
    registry2 = engine.materialize(payload2, level_index=0)
    check('game 2 materialized (2 molecules)',
          len(registry2['molecules']) == 2,
          'molecules=%d' % len(registry2['molecules']))
    wiz2 = GameWizard(payload2, registry2, 0, 0)
    wiz2.activate()
    mol1_slots = sorted(registry2['molecules'][1]['slots'])
    mol1_obj = registry2['molecules'][1]['slots'][mol1_slots[0]][0]
    _script_pick(wiz2, '%s and name CA' % mol1_obj)
    check('molecule-1 AA pick is out of scope (no-op)',
          wiz2._current_slot is None,
          '_current_slot=%r -- molecule-0 scoping decision documented'
          % (wiz2._current_slot,))
    cmd.set_wizard()
    placement.cleanup_game_objects()
    check('game-2 teardown leaves scene pre-game EXACTLY',
          list(cmd.get_names('objects')) == pre_names,
          'post=%s' % list(cmd.get_names('objects')))
except Exception:
    traceback.print_exc()
    check('part E multi-molecule scoping', False, 'raised (see traceback)')
    try:
        cmd.set_wizard()
    except Exception:
        pass
    placement.cleanup_game_objects()

# ============================================================
# PART F: the 03-06 field bug batteries (multi-switch greening +
# display rebuild + cross-molecule scoring guard)
# ============================================================
try:
    setup_f = validate_state({'interaction_mode': 'unset',
                              'molecules_per_level': 2,
                              'difficulty_levels': 3})
    payload_f, rows_f = engine.new_game(setup_f, 42,
                                        candidates=list(entries))
    registry_f = engine.materialize(payload_f, level_index=0)
    mol0_f = registry_f['molecules'][0]
    mol1_f = registry_f['molecules'][1]
    lig0_f = mol0_f['ligand'][0]
    lig1_f = mol1_f['ligand'][0]
    req_f = payload_f['levels'][0]['molecules'][0]['required']
    slots0_f = sorted(mol0_f['slots'])
    objs0_f = [mol0_f['slots'][s][0] for s in slots0_f]
    objs1_f = [mol1_f['slots'][s][0] for s in sorted(mol1_f['slots'])]
    print('SMOKE-ENV part F game: mol0=%s lig=%s mol1=%s lig=%s '
          'required=%s'
          % (slots0_f, lig0_f, sorted(mol1_f['slots']), lig1_f, req_f),
          flush=True)

    originals_f = {}
    for ob in objs0_f + objs1_f:
        originals_f[ob] = _color_map(ob)
    green_f = int(cmd.get_color_index(wizard_core.HIGHLIGHT_COLOR))

    def _green_objects_f():
        out = []
        for ob in objs0_f + objs1_f:
            cm = _color_map(ob)
            if cm and all(c == green_f for c in cm.values()):
                out.append(ob)
        return out

    def _others_restored_f(current):
        return all(_color_map(ob) == originals_f[ob]
                   for ob in objs0_f + objs1_f if ob != current)

    def _pick_atom_f(obj, first=True):
        ids = []
        cmd.iterate(obj, 'stored.append(ID)', space={'stored': ids})
        ids = sorted(int(i) for i in ids)
        atom_id = ids[0] if first else ids[-1]
        cmd.select('sele', '%s and id %d' % (obj, atom_id))
        wiz_f.do_select('sele')

    wiz_f = GameWizard(payload_f, registry_f, 0, 0)
    wiz_f.activate()

    # (1) THE FIELD SEQUENCE: mol-0 chain incl. a same-slot re-click.
    sequence_f = [(objs0_f[3], True), (objs0_f[3], False),
                  (objs0_f[2], False), (objs0_f[1], False),
                  (objs0_f[0], False), (objs0_f[3], False),
                  (objs0_f[6], False), (objs0_f[7], False),
                  (objs0_f[8], False)]
    for step, (ob, first) in enumerate(sequence_f):
        _pick_atom_f(ob, first)
        want_slot = wiz_f._slot_by_object[ob]
        check('switch %d %s: exactly one green + it is current'
              % (step + 1, ob),
              _green_objects_f() == [ob]
              and wiz_f._current_slot == want_slot,
              'greens=%s current=%r'
              % (_green_objects_f(), wiz_f._current_slot))
        check('switch %d %s: every other object restored EXACTLY'
              % (step + 1, ob), _others_restored_f(ob), '')

    # (1b) Ligand / other-molecule / double-click no-op interleave.
    _pick_atom_f(lig0_f, True)
    for ob in (objs1_f[6], objs1_f[6], objs1_f[3], objs1_f[3],
               objs1_f[0]):
        _pick_atom_f(ob, True)
    check('ligand + other-molecule + double picks are no-ops',
          _green_objects_f() == [objs0_f[8]]
          and wiz_f._current_slot == wiz_f._slot_by_object[objs0_f[8]],
          'greens=%s current=%r'
          % (_green_objects_f(), wiz_f._current_slot))

    # (2) THE REBUILD SPY: the field bug was DISPLAY staleness; the
    # switch path must re-issue the restored object's display lists.
    rebuild_calls = []
    orig_rebuild = cmd.rebuild

    def _spy_rebuild(*args, **kwargs):
        rebuild_calls.append(args[0] if args else None)
        return orig_rebuild(*args, **kwargs)

    try:
        cmd.rebuild = _spy_rebuild
        _pick_atom_f(objs0_f[0], True)
    finally:
        cmd.rebuild = orig_rebuild
    check('switch re-issues the restored object display lists',
          objs0_f[8] in rebuild_calls
          and _green_objects_f() == [objs0_f[0]],
          'rebuild_calls=%s greens=%s'
          % (rebuild_calls, _green_objects_f()))

    # (1c) Reset restores every recolored object EXCEPT the current
    # selection (the selection's green persists -- intended).
    wiz_f.reset_grid()
    check('reset: current stays green, every other color restored',
          _green_objects_f() == [objs0_f[0]]
          and _others_restored_f(objs0_f[0])
          and wiz_f._current_slot == wiz_f._slot_by_object[objs0_f[0]],
          'greens=%s current=%r'
          % (_green_objects_f(), wiz_f._current_slot))
    cmd.set_wizard()

    # (3) THE CROSS-MOLECULE SCORING GUARD: park a mol-0 charged AA on
    # the mol-1 ligand; the whole-scene detect() must provably catch an
    # interaction, yet the confirm path must return the EMPTY scope.
    charged = [s for s in payload_f['levels'][0]['molecules'][0]
               ['grid']['slots'] if s.get('aa') in ('LYS', 'ARG', 'HIS')]
    check('a cationic mol-0 slot exists for the guard',
          bool(charged),
          'cationic slots=%s' % [s['slot_id'] for s in charged])
    c_slot = charged[0]['slot_id']
    c_obj = mol0_f['slots'][c_slot][0]
    c_name = 'NZ' if charged[0]['aa'] == 'LYS' else 'CZ'
    nz_rows = []
    cmd.iterate_state(1, '%s and name %s' % (c_obj, c_name),
                      'stored.append((x, y, z))', space={'stored': nz_rows})
    check('charged atom located', len(nz_rows) == 1,
          '%s in %s: %d' % (c_name, c_obj, len(nz_rows)))
    lig1_c = _tofloat(geometry.centroid_of(lig1_f))
    target_c = _add(lig1_c, (0.0, 0.0, 3.0))
    cur = (float(nz_rows[0][0]), float(nz_rows[0][1]),
           float(nz_rows[0][2]))
    cmd.translate([target_c[0] - cur[0], target_c[1] - cur[1],
                   target_c[2] - cur[2]], c_obj, state=1, camera=0)
    whole = engine.detect()
    guard_teeth = [r for r in whole if r['aa']['object'] == c_obj]
    check('whole-scene detect DOES form with the wrong ligand nearby',
          bool(guard_teeth),
          'records over %s: %s'
          % (c_obj, [(r['type'], r['lig']['object'])
                     for r in guard_teeth]))
    scoped_recs, guard_score, guard_formed = engine.confirm(
        0, 0, req_f)
    leaked = [r for r in scoped_recs
              if r['lig']['object'] == lig1_f
              or r['aa']['object'] == c_obj]
    check('confirm returns the molecule scope -- no cross-molecule '
          'records, score 0.00',
          not leaked and guard_score == 0.0 and guard_formed == [],
          'scoped=%s score=%s formed=%s leaked=%s'
          % ([(r['type'], r['aa']['object'], r['lig']['object'])
              for r in scoped_recs], guard_score, guard_formed,
             leaked))

    placement.cleanup_game_objects()
    check('part F teardown leaves scene pre-game EXACTLY',
          list(cmd.get_names('objects')) == pre_names,
          'post=%s' % list(cmd.get_names('objects')))
except Exception:
    traceback.print_exc()
    check('part F field-bug batteries', False, 'raised (see traceback)')
    try:
        cmd.set_wizard()
    except Exception:
        pass
    placement.cleanup_game_objects()

# --- Worst-drift summary (the research evidence lines) ---------------
print('SMOKE-ENV worst drifts: %s'
      % dict((k, ('%.3g' % v if isinstance(v, float) else v))
             for k, v in sorted(REC.items())), flush=True)

# --- Verdict marker (the SOLE verdict carrier) --------------------------
print('=== SMOKE-07 %s ==='
      % ('FAIL: ' + ', '.join(failures) if failures else 'PASS'),
      flush=True)
