"""Headless smoke 08 - the STARTER path (plan 03-05).

Run (from WSL, repo root):
    bash smoke/run_smoke.sh smoke/smoke_08_starter.py 240
Verdict is carried by the printed marker (exit codes cannot carry
verdicts through the cmd.exe wrapper): grep '=== SMOKE-08 PASS ==='.

Proves the one-call game entry seam (aamatch/gamestart.py:start_game,
called DIRECTLY) end-to-end in REAL headless PyMOL, on the frozen
Phase-1 DEFAULTS (molecules 2, D 3, mode 'unset', seed 42). 04-05
re-point: run_plugin_gui now opens the Phase-4 Qt setup window (the
menu path is SMOKE-11's), so this smoke drives the SEAM directly --
the window's Start button delegates to the very same function:

PART 1  start: start_game() returns the live GameWizard and it is
        top-of-stack; msm is 0 during play (post-push snapshot kept);
        panel is non-empty with all 3-element entries; the prompt
        carries the click instruction; the scene grew by exactly
        len(registry['molecules']) x (1 + n*n) objects (the count is
        DERIVED from the returned wizard's registry/payload, never
        hard-coded); the 03-06 fix-pass asserts live here -- uniform
        AA representations (every slot object reads the sticks bit
        ONLY), the zoom-to-frame (view changed and the camera sits
        outside the ACTIVE molecule's bounding sphere -- 03-07 human
        decision 2026-09-10: frame ONLY the active molecule's grid +
        ligand so the view matches the panel's "molecule 1 of 2"
        notice), the 03-07 depth composition -- GEOMETRY-side
        (gamestart translates the ligand in WORLD space in front of
        its own grid layer; the retired camera-only pitch is gone):
        ligand in front of the grid centroid, per-atom non-occlusion
        on its own grid with a >= 5 A viewer-relative lead, sentinel
        integrity after the translate, the 03-07 blank-frame
        regression fit assert -- every ACTIVE-molecule atom inside the
        framed frustum + clip slab after the full composition -- the
        INACTIVE-molecule centroid OUTSIDE that frame (documents the
        active-only framing intent mechanically), and the
        multi-molecule scope notice in the panel (2-molecule
        defaults).
PART 2  restore-table spot check: a scripted pick (the 03-04 recipe:
        cmd.select('sele', '<slot object> and name CA') ->
        do_select('sele')) routes to a slot identity and recolors the
        object; Done (canonical cmd.set_wizard()) restores msm to the
        pre-smoke snapshot, restores the recolored slot's colors, and
        NEVER deletes the game objects.
PART 3  restart from an EMPTY wizard stack (the replace=0 path -- PART
        2's Done emptied the stack): start_game() again cleans the
        old generation's objects FIRST, leaves exactly one fresh game
        in the scene (count matches the new registry), and the new
        wizard instance is top-of-stack. OLD-GENERATION GONE is proven
        by INSTANCE, not name: the fresh generation reuses the SAME
        deterministic _aam_* names once cleanup freed them, so the old
        generation is stamped (b-factor marker band) before the restart
        and the marker must read ZERO afterwards.
PART 4  mid-game restart WITHOUT Done (the replace=1 path, previously
        uncovered -- the restart-hygiene branch): with PART 3's wizard
        STILL top-of-stack, start_game() again pops it (conditional
        replace=1 inside start_game), so cmd.get_wizard() is the NEWEST
        instance, exactly one generation exists in the scene (same
        instance-marker proof), and msm
        is 0 during play with the NEW wizard's post-push snapshot equal
        to the TRUE pre-smoke user value; Done then restores that true
        value (1 on stock), NOT a stale defensive 0 -- the assert that
        gives the 03-03 post-push snapshot ORDER LAW its regression
        teeth on the replace path.
PART 5  compose seam generalization (06-04): on a deferred
        (activate=False -- the SMOKE-11 PART H shape) 2-molecule
        sentinel game, compose_molecule_view(registry, 1) frames
        molecule 1 ONLY (view changed vs pre-compose, the zoom-target
        selection string names ONLY molecule-1 objects, molecule 0's
        ligand position untouched by the index-1 compose), is
        idempotent (a second index-1 compose is a geometry no-op via
        the need<=0 early return), and the default-index call equals
        the explicit compose_molecule_view(registry, 0) across FRESH
        materializes (ligand centroid + view equality); restore =
        prefix cleanup -> baseline EXACTLY + _last_start reset.
PART 6  determinism: all three starts used the same default seed ->
        payload['seed'] equal and the level-0 molecule ligand files
        identical (read back through the returned wizards' _payload).
PART 7  payload-direct seam (07-05): an equivalent payload is read off
        engine._payload (NEVER regenerated), an interloper seed-9999
        generation is stamped and must read ZERO after
        start_game_from_payload(payload, activate=False) replaces it --
        the produced registry is byte-equal modulo instance to the
        generated reference (same names, same sorted ids, same atom
        counts), the engine adopt bound the payload BY IDENTITY with a
        fresh GameState (all zeros, anchor None), _last_start carries
        EXACTLY the 5-key tuple with 'payload' is the embedded truth,
        and activate_game gives the same GO path (fresh float anchor,
        wizard pushed). Restore: Done + cleanup -> baseline.
PART 8  teardown: Done + placement.cleanup_game_objects() returns the
        scene to the pre-start snapshot EXACTLY.

Conventions (frozen Phase 1, kept): anchor repo root via sys.argv
first / cwd fallback (never __file__); import aamatch directly (module
identity 'aamatch' -- NEVER the pmg_tk.startup path in the same
session); every print on ONE line and flushed; explicit space dicts in
every iterate; no round() in expressions; no calls to the placement.py
banned cmd APIs anywhere; check details built from already-known data
only (the 03-04 eager-detail lesson).

Python floor: runs inside PyMOL's Windows Python (3.9); written 3.6-safe.
"""
import math
import os
import sys
import traceback


def _find_repo_root():
    """Anchor the repo root WITHOUT trusting __file__ (01-07 discovery:
    inside a -cq script __file__ points at pymol/__init__.py)."""
    mine = 'smoke_08_starter.py'
    for arg in sys.argv:
        if arg.endswith(mine) and os.path.exists(arg):
            return os.path.dirname(os.path.dirname(os.path.abspath(arg)))
    return os.getcwd()


_ROOT = _find_repo_root()
print('SMOKE-ENV root:', _ROOT, flush=True)

failures = []
REC = {}


def check(name, cond, detail=''):
    print('SMOKE-08 %-44s %s %s' % (name, 'PASS' if cond else 'FAIL',
                                     detail), flush=True)
    if not cond:
        failures.append(name)


if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from pymol import cmd  # noqa: E402

import aamatch  # noqa: E402
from aamatch import (engine, gamestart, geometry,  # noqa: E402
                     placement, setup_state, wizard_core)
from aamatch.wizard import GameWizard  # noqa: E402

print('SMOKE-ENV pymol: %s' % (cmd.get_version()[0],), flush=True)
print('SMOKE-ENV python: %s' % (sys.version.split()[0],), flush=True)


def _game_objects():
    """Sorted live scene objects carrying the reserved game prefix."""
    return sorted(n for n in cmd.get_names('objects')
                  if n.startswith(geometry.GAME_PREFIX))


def _color_map(obj):
    """{int(ID): int(color)} read-back (explicit space dict, uppercase
    ID, no round() -- Pitfall-8 conformant)."""
    rows = []
    cmd.iterate(obj, 'stored.append((ID, color))', space={'stored': rows})
    return dict((int(atom_id), int(color)) for (atom_id, color) in rows)


def _expected_count(wiz):
    """The whole-scene game-object count DERIVED from a wizard's
    registry/payload: len(registry['molecules']) x (1 + n*n), n from
    the level-0 difficulty spec -- never hard-coded."""
    n = int(wiz._payload['levels'][0]['difficulty']['grid_n'])
    return len(wiz._registry['molecules']) * (1 + n * n)


# Instance marker: same-seed restarts REBUILD the same deterministic
# object names once cleanup frees them, so NAME-set equality can never
# prove the old generation is gone. Stamp the live generation's
# b-factor into a marker band (game sentinels sit at b=-999.0, far
# outside it); a restart's cleanup deletes the marked instances, and
# the fresh ones are born with the sentinel value.
MARK_LOW, MARK_HIGH = -2.0, -0.5


def _stamp(objects):
    """Write the marker band onto every atom of ``objects``."""
    for name in objects:
        cmd.alter(name, 'b=-1.0', space={})


def _marked_atoms():
    """Atoms currently carrying the instance marker (0 after cleanup)."""
    return cmd.count_atoms('b > %f and b < %f' % (MARK_LOW, MARK_HIGH))


def _ligand_files(wiz):
    """Level-0 molecule ligand files in molecule order (determinism
    read-back through the returned wizard's payload)."""
    return [mol['ligand']['file']
            for mol in wiz._payload['levels'][0]['molecules']]


# ============================================================
# PART 0: pre-start snapshot
# ============================================================
pre_names = list(cmd.get_names('objects'))
pre_msm = int(cmd.get('mouse_selection_mode'))
pre_view = list(cmd.get_view())
REC['pre_msm'] = pre_msm
check('clean pre-start scene and stock msm',
      not _game_objects() and pre_msm == 1,
      'pre game objects=%s msm=%d (expect none/1 on stock)'
      % (_game_objects(), pre_msm))

wiz1 = wiz2 = wiz3 = None
gen1_expected = gen2_expected = gen3_expected = None

# ============================================================
# PART 1: direct-seam start (gamestart.start_game called directly)
# ============================================================
try:
    wiz1 = aamatch.gamestart.start_game()
    check('start_game returns a GameWizard',
          isinstance(wiz1, GameWizard), 'type=%r' % (type(wiz1),))
    check('wizard is top-of-stack', cmd.get_wizard() is wiz1,
          'get_wizard()=%r' % (cmd.get_wizard(),))
    msm_now = int(cmd.get('mouse_selection_mode'))
    check('msm zeroed during play, post-push snapshot kept',
          msm_now == 0 and wiz1._saved_msm == pre_msm,
          'msm=%d saved=%r pre=%d' % (msm_now, wiz1._saved_msm, pre_msm))
    panel = wiz1.get_panel()
    kinds_ok = all(len(e) == 3 and e[0] in (0, 1, 2) for e in panel)
    check('panel non-empty, all 3-element entries',
          bool(panel) and kinds_ok,
          '%d entries, kinds=%s'
          % (len(panel), sorted(set(e[0] for e in panel))))
    prompt = wiz1.get_prompt()
    check('prompt carries the click instruction',
          bool(prompt) and 'Click an amino acid' in prompt[0],
          'prompt[0]=%r' % (prompt[0] if prompt else None,))
    gen1_expected = _expected_count(wiz1)
    REC['gen1_objects'] = gen1_expected
    grew = sorted(set(cmd.get_names('objects')) - set(pre_names))
    check('scene grew by exactly molecules x (1 + n*n)',
          len(grew) == gen1_expected and _game_objects() == grew,
          'grew=%d want %d (derived from the returned registry)'
          % (len(grew), gen1_expected))

    # -- 03-06 fix: uniform AA representations (sticks ONLY) ----------
    reps_bad = []
    for mol in wiz1._registry['molecules']:
        for slot_id, entry in mol['slots'].items():
            rows = []
            cmd.iterate(entry[0], 'stored.append(reps)',
                        space={'stored': rows})
            vals = sorted(set(int(r) for r in rows))
            if vals != [1]:        # bit 0 = sticks, nothing else
                reps_bad.append('%s(%s)=%s' % (slot_id, entry[0], vals))
    check('every AA reads the sticks bit ONLY (uniform reps)',
          not reps_bad,
          'non-uniform: %s (the old split was neutral 49 vs charged '
          '2176)' % reps_bad)

    # -- 03-07 fix: zoom-to-frame the ACTIVE molecule only ------------
    # 03-07 human decision 2026-09-10 ("zooming to only the AA grid of
    # current active mol"): gamestart's final zoom names the ACTIVE
    # molecule's objects (slot objects + ligand, from the registry) --
    # the inactive molecule stays in the scene as context, out of the
    # initial frame. All composition asserts below are computed on the
    # ACTIVE molecule's atoms.
    view_post = list(cmd.get_view())
    atoms = geometry.extract_game_atoms()
    _lig_name = wiz1._registry['molecules'][0]['ligand'][0]
    _slot_objects = set(e[0] for e in
                        wiz1._registry['molecules'][0]['slots'].values())
    _active_objects = _slot_objects | {_lig_name}
    _active = [a for a in atoms if a['object'] in _active_objects]
    _inactive = [a for a in atoms if a['object'] not in _active_objects]
    cx = sum(a['x'] for a in _active) / len(_active)
    cy = sum(a['y'] for a in _active) / len(_active)
    cz = sum(a['z'] for a in _active) / len(_active)
    r_scene = max(math.sqrt((a['x'] - cx) ** 2 + (a['y'] - cy) ** 2
                            + (a['z'] - cz) ** 2) for a in _active)
    cam_d = -float(view_post[11])    # viewer distance behind the origin
    REC['scene_radius'] = r_scene
    REC['zoom_camera_dist'] = cam_d
    check('zoom pulled the camera back and frames the ACTIVE molecule',
           view_post != pre_view and cam_d >= r_scene,
           'camera dist %.2f >= active-molecule radius %.2f (view '
           'changed: %s)' % (cam_d, r_scene, view_post != pre_view))

    # -- 03-06/03-07: ligand composes ABOVE and IN FRONT OF its own
    # grid at start (deterministic view-matrix asserts -- no rendering;
    # ACTIVE molecule only). Camera-space coords of a world point: R
    # rows of get_view . (p - origin); cam-z grows toward the camera
    # (sign law proven by the fit theorem below). --------------------
    _lig = [a for a in atoms
            if a['side'] == 'lig' and a['object'] == _lig_name]
    _grid = [a for a in atoms
             if a['side'] == 'aa' and a['object'] in _slot_objects]

    def _cam_xyz(rows):
        px = sum(a['x'] for a in rows) / len(rows) - view_post[9]
        py = sum(a['y'] for a in rows) / len(rows) - view_post[10]
        pz = sum(a['z'] for a in rows) / len(rows) - view_post[11]
        return (view_post[0] * px + view_post[1] * py + view_post[2] * pz,
                view_post[3] * px + view_post[4] * py + view_post[5] * pz,
                view_post[6] * px + view_post[7] * py + view_post[8] * pz)
    _lx, _ly, _lz = _cam_xyz(_lig)
    _gx, _gy, _gz = _cam_xyz(_grid)
    check('active ligand composes above the grid (camera-space y)',
           _ly > _gy,
           'ligand cam-y %.3f > grid cam-y %.3f' % (_ly, _gy))
    check('ligand and grid screen-aligned (camera roll composed)',
           abs(_lx - _gx) <= max(1.0e-6, r_scene * 0.01),
           'cam-x delta %.4f within 1%% of scene radius %.2f'
           % (abs(_lx - _gx), r_scene))
    # 03-07: depth composition -- now GEOMETRY-side (gamestart moved
    # the ligand in world space toward the camera; the camera-only
    # pitch is retired). DEPTH SIGN, proven by the fit theorem below:
    # the camera looks down cam-space -z and every visible atom lands
    # in [-view[16], -view[15]], so NEARER THE VIEWER == LARGER row-2
    # projection (the constant origin shift between this cam() frame
    # and the T() render frame cancels out of every comparison here).
    # The PRE-FIX asserts codified the INVERSE comparison (and used
    # min = the FARTHEST own-grid atom) -- they passed while the
    # ligand genuinely sat BEHIND the whole grid layer, exactly the
    # human's "placement still behind" field report. The geometry
    # offset moves the ligand to the larger-side of the full grid
    # axis spread: eyes -> ligand -> grid, never occluded.
    check('active ligand sits in front of the grid centroid (depth)',
           _lz > _gz,
           'ligand cam-z %.3f > grid cam-z %.3f (larger = nearer)'
           % (_lz, _gz))
    _own_z = max(
        view_post[6] * (a['x'] - view_post[9])
        + view_post[7] * (a['y'] - view_post[10])
        + view_post[8] * (a['z'] - view_post[11]) for a in _grid)
    _LEAD_MIN = 5.0
    _lead = _lz - _own_z
    check('active ligand leads its OWN grid layer by >= 5 A (geometry offset)',
           _lead >= _LEAD_MIN - 1.0e-4,
           'ligand cam-z %.3f vs nearest own-grid atom %.3f -> lead '
           '%.3f A (floor %.4f, pose-tolerance 1e-4)'
           % (_lz, _own_z, _lead, _LEAD_MIN - 1.0e-4))
    # the world-space translate must not disturb the ligand sentinels
    _lig_tags = []
    cmd.iterate(_lig_name, 'stored.append((segi, b))',
                space={'stored': _lig_tags})
    check('ligand sentinels intact after geometry offset (segi AAM, b -999)',
           bool(_lig_tags) and all(
               s == placement.SENTINEL_SEGI
               and abs(b - placement.SENTINEL_B) < 1.0e-3
               for (s, b) in _lig_tags),
           '%d ligand atoms, tags %s' % (len(_lig_tags), _lig_tags[:2]))

    # -- 03-07 REGRESSION (blank start view): the whole ACTIVE molecule
    # must sit inside the framed view after the full start composition
    # (zoom now targets the active molecule's objects only -- 03-07
    # human decision 2026-09-10; the inactive molecule is asserted
    # OUTSIDE this frame below). TRUE
    # render map (pymolwiki Get_View, verified on this build: view
    # [12:15] reads exactly the selection centroid after a zoom):
    #   T(p) = R . (p - view[12:15]) + view[9:12]   (camera at cam-space
    #   origin looking down -z; view[9:12] = rotation origin in CAMERA
    #   coords; view[12:15] = rotation origin in WORLD coords;
    #   view[15]/[16] = front/rear clip distances from the camera).
    # Visibility criterion (both must hold for EVERY game atom):
    #   depth/slab : -view[16] + 2.0 <= T_z <= -view[15] - 2.0
    #                (2 Angstrom margin inside the clip slab; a stock
    #                zoom(buffer=5) leaves ~30 Angstrom of slab slack)
    #   lateral    : max(|T_x|, |T_y|) <= 0.90 * tan(fov/2) * (-T_z)
    #                (perspective frustum at the atom's OWN depth; the
    #                VERTICAL fov is applied to BOTH axes -- strictly
    #                conservative on any landscape viewport, 640x480
    #                here; 0.90 = atoms must sit 10% INSIDE the frame,
    #                not at its edge).
    # Regression teeth: the pre-fix ordering (zoom BEFORE roll/pitch --
    # the pitch wrote its pivot re-anchor into the camera-space origin
    # field view[9:12] across a ~180 A camera lever arm) put ALL 359 of
    # 359 seed-42 game atoms OUTSIDE this frame (headless probe tmp/
    # probe_0308_reframe.py: worst lateral 88.5 A vs 24.6 A allowed --
    # the human's "1st frame is blank" report). The fix runs ONE final
    # cmd.zoom AFTER all orientation changes: zoom is a pure dolly/
    # re-aim (R untouched -- probe: rotation element delta exactly 0.0)
    # so every composition assert above survives, while the origin
    # fields and clip slab are re-derived from the pitched R. Relative
    # camera-space depths are translation-invariant, so the depth
    # asserts above need no re-ordering.
    _fov_tan = math.tan(math.radians(
        float(cmd.get('field_of_view'))) / 2.0)
    _front, _rear = float(view_post[15]), float(view_post[16])

    def _T_in_frame(p):
        """One world point through the render map -> (framed?, T_x,
        T_y, T_z, lateral bound). Same visibility criterion as the fit
        loop: inside the perspective frustum at the point's own depth
        AND inside the clip slab with a 2 A margin."""
        _dx = p[0] - view_post[12]
        _dy = p[1] - view_post[13]
        _dz = p[2] - view_post[14]
        _tx = (view_post[0] * _dx + view_post[1] * _dy
               + view_post[2] * _dz + view_post[9])
        _ty = (view_post[3] * _dx + view_post[4] * _dy
               + view_post[5] * _dz + view_post[10])
        _tz = (view_post[6] * _dx + view_post[7] * _dy
               + view_post[8] * _dz + view_post[11])
        _depth = -_tz
        _bound = 0.90 * _fov_tan * _depth
        _ok = (_depth > 1.0e-9 and max(abs(_tx), abs(_ty)) <= _bound
               and -_rear + 2.0 <= _tz <= -_front - 2.0)
        return (_ok, _tx, _ty, _tz, _bound)

    _unframed = []
    _worst = (0.0, '?', 0.0, 0.0)   # (lat/bound, object, lat, bound)
    for _a in _active:
        _ok, _tx, _ty, _tz, _bound = _T_in_frame(
            (_a['x'], _a['y'], _a['z']))
        if not _ok:
            _unframed.append('%s/%s' % (_a['object'], _a['name']))
        if -_tz > 1.0e-9:
            _lat = max(abs(_tx), abs(_ty))
            if _lat / _bound > _worst[0]:
                _worst = (_lat / _bound, _a['object'], _lat, _bound)
    check('every ACTIVE-molecule atom framed after full composition',
          not _unframed,
          'worst %s lateral %.2f vs bound %.2f (%.0f%% of frame); '
          'unframed %d/%d %s'
          % (_worst[1], _worst[2], _worst[3], _worst[0] * 100.0,
             len(_unframed), len(_active), _unframed[:4]))

    # -- 03-07 NEW: the INACTIVE molecule must fall OUTSIDE the active
    # frame -- documents the human decision mechanically ("zooming to
    # only the AA grid of current active mol"): the start view names
    # the active molecule's objects only, so the other molecule is
    # scene context, not initial content. Same visibility criterion as
    # the fit assert, applied to the inactive molecule's centroid:
    # framed (inside frustum AND clip slab) must read False.
    _i_ok = False
    _i_lat = _i_bound = 0.0
    _i_tz = 0.0
    if _inactive:
        _ic = (sum(a['x'] for a in _inactive) / len(_inactive),
               sum(a['y'] for a in _inactive) / len(_inactive),
               sum(a['z'] for a in _inactive) / len(_inactive))
        _i_ok, _i_tx, _i_ty, _i_tz, _i_bound = _T_in_frame(_ic)
        _i_lat = max(abs(_i_tx), abs(_i_ty))
    check('INACTIVE molecule centroid OUTSIDE the active frame',
          bool(_inactive) and not _i_ok,
          'inactive centroid lateral %.2f vs bound %.2f, T_z %.2f vs '
          'slab [%.1f, %.1f] (framed reads %s -- must be False)'
          % (_i_lat, _i_bound, _i_tz, -_rear, -_front, _i_ok))

    # -- 03-06 fix: multi-molecule scope notice in the panel ----------
    panel_texts = [e[1] for e in panel]
    notices = [t for t in panel_texts if 'counts and is clickable' in t]
    check('2-molecule panel carries the scope notice',
          len(notices) == 1 and '1 of 2' in notices[0],
          'notice=%r' % (notices,))
except Exception:
    traceback.print_exc()
    check('part 1 starter path', False, 'raised (see traceback above)')
    wiz1 = None

# ============================================================
# PART 2: restore-table spot check (pick -> recolor -> Done restores)
# ============================================================
try:
    if wiz1 is None:
        raise RuntimeError('part 1 failed')
    slots = sorted(wiz1._registry['molecules'][0]['slots'])
    slot_id = slots[0]
    aa_obj = wiz1._registry['molecules'][0]['slots'][slot_id][0]
    pre_colors = _color_map(aa_obj)
    cmd.select('sele', '%s and name CA' % aa_obj)
    wiz1.do_select('sele')
    check('scripted pick routes to the slot identity',
          wiz1._current_slot == slot_id,
          '_current_slot=%r want %r' % (wiz1._current_slot, slot_id))
    green = int(cmd.get_color_index(wizard_core.HIGHLIGHT_COLOR))
    now_colors = _color_map(aa_obj)
    check('picked object recolored (spot atom colors all highlight)',
          bool(now_colors) and all(c == green for c in now_colors.values()),
          '%d atoms color==%d' % (len(now_colors), green))
    game_before_done = _game_objects()
    cmd.set_wizard()
    check('Done restores msm to the pre-start snapshot',
          int(cmd.get('mouse_selection_mode')) == pre_msm,
          'msm=%d snapshot=%d (never hard-coded 0)'
          % (int(cmd.get('mouse_selection_mode')), pre_msm))
    check('Done restores the recolored slot colors',
          _color_map(aa_obj) == pre_colors,
          'rows match the pre-recolor snapshot exactly')
    check('Done NEVER deletes game objects and pops the stack',
          _game_objects() == game_before_done
          and cmd.get_wizard() is None,
          'game objects=%d get_wizard()=%r'
          % (len(_game_objects()), cmd.get_wizard()))
except Exception:
    traceback.print_exc()
    check('part 2 restore-table spot check', False,
          'raised (see traceback above)')
    try:
        cmd.set_wizard()
    except Exception:
        pass

# ============================================================
# PART 3: restart from an EMPTY wizard stack (replace=0 path)
# ============================================================
try:
    gen1_names = _game_objects()
    _stamp(gen1_names)
    stamped3 = _marked_atoms()
    wiz2 = aamatch.gamestart.start_game()
    check('restart (empty stack) activates the NEW wizard',
          cmd.get_wizard() is wiz2 and wiz2 is not wiz1,
          'get_wizard()=%r' % (cmd.get_wizard(),))
    check('old generation cleaned first (instances, not names)',
          stamped3 > 0 and _marked_atoms() == 0,
          'stamped %d atom(s), survivors by marker: %d -- the fresh '
          'generation reuses the SAME deterministic names once cleanup '
          'freed them (the count asserts below catch any double '
          'generation)' % (stamped3, _marked_atoms()))
    gen2_expected = _expected_count(wiz2)
    REC['gen2_objects'] = gen2_expected
    check('exactly one fresh game generation in the scene',
          len(_game_objects()) == gen2_expected,
          'objects=%d want %d (the new registry, same seed/grid)'
          % (len(_game_objects()), gen2_expected))
    check('empy-stack restart grew ONLY game objects',
          sorted(set(cmd.get_names('objects')) - set(pre_names))
          == _game_objects(),
          'no non-game growth vs the pre-start snapshot')
except Exception:
    traceback.print_exc()
    check('part 3 empty-stack restart', False,
          'raised (see traceback above)')
    try:
        cmd.set_wizard()
    except Exception:
        pass
    wiz2 = None

# ============================================================
# PART 4: mid-game restart WITHOUT Done (replace=1 path)
# ============================================================
try:
    if wiz2 is None:
        raise RuntimeError('part 3 failed')
    if cmd.get_wizard() is not wiz2:
        raise RuntimeError('wiz2 not top-of-stack for the mid-game '
                           'restart')
    gen2_names = _game_objects()
    # NO Done / cmd.set_wizard() here -- the restart happens over a
    # LIVE GameWizard, so start_game must take replace=1 (restart
    # hygiene: the old game wizard is popped + cleaned).
    _stamp(gen2_names)
    stamped4 = _marked_atoms()
    wiz3 = aamatch.gamestart.start_game()
    check('replace=1 pops the old GameWizard, newest on top',
          cmd.get_wizard() is wiz3
          and wiz3 is not wiz2 and wiz3 is not wiz1,
          'get_wizard()=%r' % (cmd.get_wizard(),))
    gen3_expected = _expected_count(wiz3)
    REC['gen3_objects'] = gen3_expected
    check('replace=1 leaves exactly one game generation',
          stamped4 > 0 and _marked_atoms() == 0
          and len(_game_objects()) == gen3_expected,
          'stamped %d atom(s), survivors by marker %d, objects=%d '
          'want %d (names are reused -- instances are proven new)'
          % (stamped4, _marked_atoms(), len(_game_objects()),
             gen3_expected))
    msm_mid = int(cmd.get('mouse_selection_mode'))
    check('replace=1: msm 0 in play, snapshot == TRUE pre-game value',
          msm_mid == 0 and wiz3._saved_msm == pre_msm,
          'msm=%d saved=%r pre=%d (post-push snapshot captured the '
          'popped cleanup\'s restore -- the 03-03 ORDER LAW)'
          % (msm_mid, wiz3._saved_msm, pre_msm))
    cmd.set_wizard()   # Done on the restarted game
    check('Done after replace=1 restores the TRUE pre-game msm',
          int(cmd.get('mouse_selection_mode')) == pre_msm
          and cmd.get_wizard() is None,
          'msm=%d want %d (a stale defensive 0 here would prove the '
          'snapshot-before-push ordering regression)'
          % (int(cmd.get('mouse_selection_mode')), pre_msm))
except Exception:
    traceback.print_exc()
    check('part 4 mid-game restart', False, 'raised (see traceback)')
    try:
        cmd.set_wizard()
    except Exception:
        pass
    wiz3 = None

# ============================================================
# PART 5: compose_molecule_view molecule_index proof (06-04) --
# the generalized compose seam frames ANY molecule index, not only
# molecule 0, while the start path stays byte-identical
# ============================================================
try:
    sentinel5 = dict(setup_state.DEFAULTS)

    # (a) deferred prepare (the SMOKE-11 PART H shape: activate=False
    # prepares the full scene WITHOUT pushing the wizard) ------------
    wiz5 = aamatch.gamestart.start_game(setup=sentinel5, seed=4242,
                                        activate=False)
    # NOTE: PART 4 left its game objects in the scene (Done does not
    # delete them), so a fresh-start growth count against base5 reads
    # 0 -- the new generation REUSES the same deterministic names once
    # start_game's cleanup freed the old one. Prove freshness by the
    # DERIVED count instead (one generation, nothing extra).
    gen5_expected = _expected_count(wiz5)
    check('part 5 prepare: 2-molecule scene, wizard-free',
          isinstance(wiz5, GameWizard)
          and cmd.get_wizard() is None
          and len(_game_objects()) == gen5_expected,
          'game objects=%d want %d top=%r'
          % (len(_game_objects()), gen5_expected,
             cmd.get_wizard()))
    reg5 = wiz5._registry
    mol0 = reg5['molecules'][0]
    mol1 = reg5['molecules'][1]
    names0 = [mol0['ligand'][0]]
    names0.extend(entry[0] for entry in mol0['slots'].values())
    names1 = [mol1['ligand'][0]]
    names1.extend(entry[0] for entry in mol1['slots'].values())

    # (b) compose molecule 1 EXPLICITLY ------------------------------
    lig0_before = geometry.centroid_of(names0[0])
    view_pre5 = list(cmd.get_view())
    gamestart.compose_molecule_view(reg5, 1)
    view_post5 = list(cmd.get_view())
    check('part 5 index-1 compose ran a framing zoom (view changed)',
          view_post5 != view_pre5,
          '%d view elements compared' % (len(view_post5),))
    sel1 = gamestart._active_molecule_selection(reg5, 1)
    target1 = set(sel1.split(' or '))
    check('part 5 index-1 zoom target names ONLY molecule-1 objects',
          sel1 == ' or '.join(names1)
          and not any(n in target1 for n in names0),
          'target has %d objects, %d of them molecule-0'
          % (len(target1),
             len([n for n in names0 if n in target1])))
    check('part 5 index-1 compose left molecule-0 ligand UNMOVED',
          geometry.centroid_of(names0[0]) == lig0_before,
          'the front offset is a molecule-index-scoped translate')

    # (c) idempotence: a second index-1 compose moves nothing --------
    lig1_before = geometry.centroid_of(names1[0])
    gamestart.compose_molecule_view(reg5, 1)
    check('part 5 second index-1 compose is a geometry no-op',
          geometry.centroid_of(names1[0]) == lig1_before,
          'the need<=0 early return (idempotent front offset)')

    # (d) default-index equivalence across FRESH materializes --------
    wiz5a = aamatch.gamestart.start_game(setup=sentinel5, seed=4242,
                                         activate=False)
    gamestart.compose_molecule_view(wiz5a._registry)
    cen_a = geometry.centroid_of(
        wiz5a._registry['molecules'][0]['ligand'][0])
    view_a = list(cmd.get_view())
    wiz5b = aamatch.gamestart.start_game(setup=sentinel5, seed=4242,
                                         activate=False)
    gamestart.compose_molecule_view(wiz5b._registry, 0)
    cen_b = geometry.centroid_of(
        wiz5b._registry['molecules'][0]['ligand'][0])
    view_b = list(cmd.get_view())
    cdrift = max(abs(cen_a[i] - cen_b[i]) for i in range(3))
    vdrift = max(abs(view_a[i] - view_b[i]) for i in range(18))
    check('part 5 default index == explicit 0 (fresh materializes)',
          cdrift <= 1.0e-6 and vdrift <= 1.0e-6,
          'centroid drift %.2e A, view drift %.2e (tolerance 1e-6)'
          % (cdrift, vdrift))

    # (e) restore: prefix cleanup -> the pre-start snapshot EXACTLY
    # (the PART-4 generation still occupied the scene at part entry,
    # so this part's baseline IS the PART-0 pre_names), store reset --
    cleaned5 = placement.cleanup_game_objects()
    check('part 5 restore: pre-start scene EXACTLY, stack untouched',
          cleaned5['deleted'] > 0
          and cmd.get_names('objects') == pre_names
          and cmd.get_wizard() is None,
          'deleted=%d after=%r'
          % (cleaned5['deleted'], cmd.get_names('objects')))
    gamestart._last_start = None     # later parts start clean
    REC['part5_index1'] = ('zoom target molecule-1 only, molecule-0 '
                           'isolated, idempotent, default==0')
except Exception:
    traceback.print_exc()
    check('part 5 compose_molecule_view proof', False,
          'raised (see traceback above)')
    gamestart._last_start = None
    placement.cleanup_game_objects()

# ============================================================
# PART 6: determinism (same default seed across all three starts)
# ============================================================
try:
    trio = [w for w in (wiz1, wiz2, wiz3) if w is not None]
    if len(trio) != 3:
        raise RuntimeError('need all three wizards for determinism')
    seeds = [w._payload['seed'] for w in trio]
    files = [_ligand_files(w) for w in trio]
    check('all starts share the same seed',
          len(set(seeds)) == 1, 'seeds=%r' % (seeds,))
    check('level-0 ligand files identical across starts',
          files[0] == files[1] == files[2],
          'gen1=%r gen2=%r gen3=%r' % tuple(files))
except Exception:
    traceback.print_exc()
    check('part 5 determinism', False, 'raised (see traceback above)')

# ============================================================
# PART 7: payload-direct seam (07-05) -- start_game_from_payload
# materializes the EMBEDDED payload with ZERO generator involvement;
# the engine adopt sets all four module globals; _last_start carries
# the 5-key tuple; the GO path is identical to start_game's
# ============================================================
try:
    # P1: a normal GENERATED start (seed 42) -- capture the reference
    # registry shape + per-object atom counts -----------------------
    sentinel7 = dict(setup_state.DEFAULTS)
    wiz_a = aamatch.gamestart.start_game(setup=sentinel7, seed=42)
    reg_a = wiz_a._registry
    status_a = engine.game_status()
    names_a = _game_objects()

    def _reg_shape(reg):
        """Instance-free registry snapshot: molecule order preserved,
        every (object, sorted ids) entry captured by name."""
        shape = []
        for mol in reg['molecules']:
            slots = dict((slot_id, (entry[0], list(entry[1])))
                         for slot_id, entry in mol['slots'].items())
            shape.append({'ligand': (mol['ligand'][0],
                                     list(mol['ligand'][1])),
                          'slots': slots})
        return shape

    shape_a = _reg_shape(reg_a)
    counts_a = dict((obj, cmd.count_atoms(obj)) for obj in names_a)

    # P2: obtain the payload WITHOUT regeneration (the live module
    # state), swizzle the scene with a DIFFERENT seed (9999), stamp the
    # interloper generation's instances (03-05 restart-identity law:
    # same-level same-count scenes reuse the same deterministic names,
    # so NAME sets prove nothing -- the marker band does) --------------
    payload = engine._payload
    aamatch.gamestart.start_game(setup=sentinel7, seed=9999)
    _stamp(_game_objects())
    wiz_b = aamatch.gamestart.start_game_from_payload(payload,
                                                      activate=False)
    check('part 7 payload seam: a GameWizard returned, NOT pushed',
          isinstance(wiz_b, GameWizard)
          and cmd.get_wizard() is not wiz_b,
          'type=%r top=%r' % (type(wiz_b), cmd.get_wizard()))
    reg_b = wiz_b._registry
    shape_b = _reg_shape(reg_b)
    check('part 7 registries equal modulo instance (names + ids)',
          shape_a == shape_b,
          'seed-42 registry shape replayed pixel-for-pixel')
    counts_b = dict((obj, cmd.count_atoms(obj)) for obj in _game_objects())
    check('part 7 per-object atom counts equal (deterministic shape)',
          counts_a == counts_b,
          '%d objects compared' % (len(counts_a),))
    check('part 7 the seed-9999 generation is GONE (seam replaced)',
          _marked_atoms() == 0,
          'stamped interlopers surviving=%d' % (_marked_atoms(),))
    check('part 7 adopt bound the EMBEDDED payload BY IDENTITY',
          engine._payload is payload
          and engine._payload['seed'] == 42,
          'engine._payload=%r' % (engine._payload['seed'],))
    gs_b = engine.game_status()
    check('part 7 fresh GameState zeros (no regeneration residue)',
          gs_b['molecule_scores'] == []
          and gs_b['skip_count'] == 0
          and gs_b['giveup_count'] == 0
          and gs_b['game_over'] is False
          and gs_b['timer_anchor'] is None,
          'scores=%r skip=%d giveup=%d over=%r (generated game had '
          'status captured in P1 as the reference baseline)'
          % (gs_b['molecule_scores'], gs_b['skip_count'],
             gs_b['giveup_count'], gs_b['game_over']))
    check('part 7 wizard carries the payload + fresh books',
          wiz_b._payload is payload and wiz_b._current_slot is None,
          '_current_slot=%r' % (wiz_b._current_slot,))

    # P3: _last_start 5-key pin (07-05 Recorded Decision 1) -----------
    ls7 = gamestart._last_start or {}
    check('part 7 _last_start holds EXACTLY the 5-key tuple',
          sorted(ls7) == ['candidates', 'ligand_content', 'payload',
                          'seed', 'setup'],
          'keys=%r' % (sorted(ls7),))
    check('part 7 _last_start payload is the EMBEDDED truth',
          ls7.get('payload') is payload
          and ls7.get('seed') == payload['seed'],
          'seed=%r payload_seed=%r'
          % (ls7.get('seed'), payload['seed']))

    # P4: GO-path parity -- activate_game anchors from zero, pushes --
    gamestart.activate_game(wiz_b)
    anchor7 = engine._current_game().timer_anchor
    check('part 7 GO anchors a FRESH timer from zero, wizard pushed',
          cmd.get_wizard() is wiz_b and isinstance(anchor7, float),
          'top=%r anchor=%r' % (cmd.get_wizard(), anchor7))

    # Restore block: Done + prefix cleanup -> pre-start snapshot,
    # store reset (later teardown expects the PART-0 baseline) --------
    cmd.set_wizard()
    cleaned7 = placement.cleanup_game_objects()
    check('part 7 restore: pre-start scene EXACTLY, stack emptied',
          cleaned7['deleted'] > 0
          and cmd.get_names('objects') == pre_names
          and cmd.get_wizard() is None,
          'deleted=%d post wizard=%r'
          % (cleaned7['deleted'], cmd.get_wizard()))
    gamestart._last_start = None
    REC['part7_payload_seam'] = (
        'registry parity, adopt identity, fresh GameState, 5-key '
        '_last_start, GO parity')
except Exception:
    traceback.print_exc()
    check('part 7 payload-direct seam', False,
          'raised (see traceback above)')
    try:
        if cmd.get_wizard() is not None:
            cmd.set_wizard()
    except Exception:
        pass
    placement.cleanup_game_objects()
    gamestart._last_start = None

# ============================================================
# PART 8: teardown -- scene back to the pre-start snapshot EXACTLY
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
    check('part 8 teardown', False, 'raised (see traceback above)')
    placement.cleanup_game_objects()

# --- evidence summary -------------------------------------------------
print('SMOKE-ENV record: %s'
      % dict((k, v) for k, v in sorted(REC.items())), flush=True)

# --- Verdict marker (the SOLE verdict carrier) --------------------------
print('=== SMOKE-08 %s ==='
      % ('FAIL: ' + ', '.join(failures) if failures else 'PASS'),
      flush=True)
