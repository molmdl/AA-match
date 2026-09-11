"""Headless smoke 08 - the STARTER path (plan 03-05).

Run (from WSL, repo root):
    bash smoke/run_smoke.sh smoke/smoke_08_starter.py 240
Verdict is carried by the printed marker (exit codes cannot carry
verdicts through the cmd.exe wrapper): grep '=== SMOKE-08 PASS ==='.

Proves the one-call game entry seam (aamatch/gamestart.py:start_game,
reached through aamatch.run_plugin_gui -- the Plugins-menu function
called DIRECTLY, which is legal headless: it is a plain function now,
the addmenuitemqt registration is irrelevant here) end-to-end in REAL
headless PyMOL, on the frozen Phase-1 DEFAULTS (molecules 2, D 3, mode
'unset', seed 42):

PART 1  start: run_plugin_gui() returns the live GameWizard and it is
        top-of-stack; msm is 0 during play (post-push snapshot kept);
        panel is non-empty with all 3-element entries; the prompt
        carries the click instruction; the scene grew by exactly
        len(registry['molecules']) x (1 + n*n) objects (the count is
        DERIVED from the returned wizard's registry/payload, never
        hard-coded); the 03-06 fix-pass asserts live here -- uniform
        AA representations (every slot object reads the sticks bit
        ONLY), the zoom-to-frame (view changed and the camera sits
        outside the scene bounding sphere), the 03-07 depth
        composition (ligand in front of the grid layer, per-atom
        non-occlusion on its own grid), and the multi-molecule
        scope notice in the panel (2-molecule defaults).
PART 2  restore-table spot check: a scripted pick (the 03-04 recipe:
        cmd.select('sele', '<slot object> and name CA') ->
        do_select('sele')) routes to a slot identity and recolors the
        object; Done (canonical cmd.set_wizard()) restores msm to the
        pre-smoke snapshot, restores the recolored slot's colors, and
        NEVER deletes the game objects.
PART 3  restart from an EMPTY wizard stack (the replace=0 path -- PART
        2's Done emptied the stack): run_plugin_gui() again cleans the
        old generation's objects FIRST, leaves exactly one fresh game
        in the scene (count matches the new registry), and the new
        wizard instance is top-of-stack. OLD-GENERATION GONE is proven
        by INSTANCE, not name: the fresh generation reuses the SAME
        deterministic _aam_* names once cleanup freed them, so the old
        generation is stamped (b-factor marker band) before the restart
        and the marker must read ZERO afterwards.
PART 4  mid-game restart WITHOUT Done (the replace=1 path, previously
        uncovered -- the restart-hygiene branch): with PART 3's wizard
        STILL top-of-stack, run_plugin_gui() again pops it (conditional
        replace=1 inside start_game), so cmd.get_wizard() is the NEWEST
        instance, exactly one generation exists in the scene (same
        instance-marker proof), and msm
        is 0 during play with the NEW wizard's post-push snapshot equal
        to the TRUE pre-smoke user value; Done then restores that true
        value (1 on stock), NOT a stale defensive 0 -- the assert that
        gives the 03-03 post-push snapshot ORDER LAW its regression
        teeth on the replace path.
PART 5  determinism: all three starts used the same default seed ->
        payload['seed'] equal and the level-0 molecule ligand files
        identical (read back through the returned wizards' _payload).
PART 6  teardown: Done + placement.cleanup_game_objects() returns the
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
from aamatch import geometry, placement, wizard_core  # noqa: E402
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
# PART 1: menu-path start (run_plugin_gui called directly)
# ============================================================
try:
    wiz1 = aamatch.run_plugin_gui()
    check('run_plugin_gui returns a GameWizard',
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

    # -- 03-06 fix: zoom-to-frame the whole game ----------------------
    view_post = list(cmd.get_view())
    atoms = geometry.extract_game_atoms()
    cx = sum(a['x'] for a in atoms) / len(atoms)
    cy = sum(a['y'] for a in atoms) / len(atoms)
    cz = sum(a['z'] for a in atoms) / len(atoms)
    r_scene = max(math.sqrt((a['x'] - cx) ** 2 + (a['y'] - cy) ** 2
                            + (a['z'] - cz) ** 2) for a in atoms)
    cam_d = -float(view_post[11])    # viewer distance behind the origin
    REC['scene_radius'] = r_scene
    REC['zoom_camera_dist'] = cam_d
    check('zoom pulled the camera back and frames the scene',
           view_post != pre_view and cam_d >= r_scene,
           'camera dist %.2f >= scene radius %.2f (view changed: %s)'
           % (cam_d, r_scene, view_post != pre_view))

    # -- 03-06/03-07: ligand composes ABOVE and IN FRONT OF the grid at
    # start (deterministic view-matrix asserts -- no rendering).
    # Camera-space coords of a world point: R rows of get_view .
    # (p - origin); cam-z is distance from the camera, so "in front"
    # reads as the SMALLER cam-z. --------------------------------------
    _lig_name = wiz1._registry['molecules'][0]['ligand'][0]
    _lig = [a for a in atoms
            if a['side'] == 'lig' and a['object'] == _lig_name]
    _grid = [a for a in atoms if a['side'] == 'aa']

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
    # 03-07: depth composition -- the ligand is NEARER the viewer than
    # the grid layer (eyes -> ligand -> grid, never occluded).
    check('active ligand sits in front of the grid centroid (depth)',
           _lz < _gz,
           'ligand cam-z %.3f < grid cam-z %.3f (smaller = nearer)'
           % (_lz, _gz))
    _slot_objects = set(e[0] for e in
                        wiz1._registry['molecules'][0]['slots'].values())
    _own_grid = [a for a in atoms
                 if a['side'] == 'aa' and a['object'] in _slot_objects]
    _own_z = min(
        view_post[6] * (a['x'] - view_post[9])
        + view_post[7] * (a['y'] - view_post[10])
        + view_post[8] * (a['z'] - view_post[11]) for a in _own_grid)
    check('active ligand clears its OWN grid layer (non-occlusion)',
           _lz < _own_z,
           'ligand cam-z %.3f in front of nearest own-grid atom %.3f '
           '(lead %.3f A)' % (_lz, _own_z, _own_z - _lz))

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
    wiz2 = aamatch.run_plugin_gui()
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
    wiz3 = aamatch.run_plugin_gui()
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
# PART 5: determinism (same default seed across all three starts)
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
# PART 6: teardown -- scene back to the pre-start snapshot EXACTLY
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
    check('part 6 teardown', False, 'raised (see traceback above)')
    placement.cleanup_game_objects()

# --- evidence summary -------------------------------------------------
print('SMOKE-ENV record: %s'
      % dict((k, v) for k, v in sorted(REC.items())), flush=True)

# --- Verdict marker (the SOLE verdict carrier) --------------------------
print('=== SMOKE-08 %s ==='
      % ('FAIL: ' + ', '.join(failures) if failures else 'PASS'),
      flush=True)
