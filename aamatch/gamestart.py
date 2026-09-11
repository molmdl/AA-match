"""aamatch.gamestart -- THE single game entry point (plan 03-05).

Layer: CMD TIER. ``from pymol import cmd`` at module level is LEGAL
here; this module must NEVER be added to ``PURE_MODULES`` in
``tests/test_purity.py`` (Gates A/B scan only the pure registry; Gate D
still compiles this file under the 3.6 syntax floor). NO Qt anywhere.

THE SEAM: everything that wants to start a game calls
``start_game(setup=None, seed=42, candidates=None)`` -- the Plugins-menu
item today (``aamatch/__init__.py:run_plugin_gui`` via a lazy import,
Gate A2 preserved), the Phase-4 Qt setup window tomorrow (it passes the
user's validated setup through the same seam). One call takes the scene
from any state to a playable game:

1. ``placement.cleanup_game_objects()`` FIRST -- a restart must never
   leave two generations of ``_aam_*`` objects (prefix-only deletion;
   user objects untouched).
2. ``engine.new_game(setup or DEFAULTS, seed, candidates)`` -- the
   setup is validated fail-closed INSIDE new_game.
3. ``engine.materialize(payload, 0)`` -- ONE level (the game's current
   level; cross-level staging is Phase 4/6 flow).
4. ``GameWizard(payload, registry, 0, 0).activate(replace)`` where
   replace is CONDITIONAL (RECORDED DECISION, revised per checker):
   replace=1 ONLY when the prior top-of-stack wizard is itself a
   GameWizard (restart hygiene: pop + clean the old game wizard so its
   stale msm/colors/selection cannot leak; 03-03's activate snapshots
   msm AFTER the push, so the popped wizard's cleanup-restored user
   value is what the new game captures -- no explicit pre-pop needed
   here). Otherwise replace=0 (plain push): a user's wizard (e.g.
   ``wizard measurement``) is NEVER popped at start -- it goes dormant
      beneath the game and auto-resumes after Done (stack-native
      lifecycle, 03-RESEARCH-wizard-interaction sec. 1.2/2.3). On a fresh
      PyMOL (empty stack, prior is None) this degenerates to a plain push.
5. Zoom the camera to frame the WHOLE game (grids + all ligands) with a
   small spatial margin (03-06 field report: PyMOL's fresh camera sat
   zoomed-in on the ligand and the player could not see the grid). The
   zoom selection is the game sentinel ('segi AAM') -- every game atom
   carries it, so no long name list and no user object can ever match.
6. Roll the camera about its forward axis so the ACTIVE ligand (the
   one Confirm scores) composes ABOVE the AA grid on screen (03-06
   human preference). CAMERA COMPOSITION ONLY -- the game geometry is
   generator-owned and never moved; roll does not change distance,
   scale, or what falls inside the zoomed frame, and the wizard's
   nudge math re-reads cmd.get_view() per press so a rolled start
   view needs no movement-side change.
7. Pitch the camera about its screen-x axis through the ACTIVE ligand's
   centroid so the ligand composes clearly IN FRONT of its own AA-grid
   layer (03-07 human requirement: from the eye outward it must read
   eyes -> ligand -> grid, never occluded). The generator places the
   ligand floating ~5 Angstrom in front of its grid's CENTER, so a
   face-on start view buries it inside the grid layer; the pitch tips
   the grid layer back (its far side recedes; the ligand stays put as
   the pivot) which creates the depth cue. The angle is chosen
   deterministically per scene: the largest pitch (capped) that still
   keeps every atom of the active grid at least _PITCH_MIN_GAP
   Angstrom BEHIND the ligand centroid, or no pitch when that is
   infeasible (fail-soft: the rolled view remains, which was already
   centroid-in-front on all generated layouts). Camera-only as above.

Engine state (payload / registry / GameState) lives module-side in
``aamatch.engine`` -- the wizard requires it live, which start_game
guarantees by construction (new_game + materialize are called here,
in order, every time).

The editor_scheme start-guard contingency (03-RESEARCH-movement-spike
sec. 5.6) is explicitly NOT implemented: no start-time scheme check on
PyMOL 2.5.0 (recorded as contingency only -- §3.3's scheme law makes
the game's baked world-frame transforms scheme-independent).

Python floor: PyMOL's Windows Python 3.9 at runtime, written 3.6-safe
(Gate D compiles every aamatch/*.py under python3.6).
"""

import math

from pymol import cmd

from . import __version__, engine, geometry, placement, setup_state
from .wizard import GameWizard

# 03-07 depth-composition design constants (see step 7 above):
# the pitch is the largest angle up to _PITCH_MAX_DEG that keeps every
# atom of the active molecule's grid at least _PITCH_MIN_GAP Angstrom
# behind the ligand centroid; both were sized on the seed-42 probe
# (ligand floats ~5.3 Angstrom in front of its grid center; theta limit
# for a 2 Angstrom gap was 31.7 deg, so 25 deg is comfortably inside).
_PITCH_MAX_DEG = 25.0
_PITCH_MIN_GAP = 2.0


def _frame_ligand_above_grid(registry):
    """Roll the camera so molecule 0's ligand sits ABOVE the AA grid.

    Camera composition only (03-06 human preference) -- no game object
    moves. ``view`` per cmd.get_view(): view[0:9] = row-major world->cam
    rotation R, view[9:12] = origin, view[12:14] clip front/rear,
    view[15:] flag block; this rewrites ONLY rows 0/1 of R. Fail-soft:
    an empty/distributed scene keeps the plain zoom view.
    """
    view = list(cmd.get_view())
    atoms = geometry.extract_game_atoms()
    lig_name = registry['molecules'][0]['ligand'][0]
    lig = [a for a in atoms
           if a['side'] == 'lig' and a['object'] == lig_name]
    grid = [a for a in atoms if a['side'] == 'aa']
    if not lig or not grid:
        return

    def centroid(rows):
        return (sum(a['x'] for a in rows) / len(rows),
                sum(a['y'] for a in rows) / len(rows),
                sum(a['z'] for a in rows) / len(rows))

    def cam_x(p):   # screen-x of a world point, R row 0 . (p - origin)
        return (view[0] * (p[0] - view[9])
                + view[1] * (p[1] - view[10])
                + view[2] * (p[2] - view[11]))

    def cam_y(p):   # screen-y (up) of a world point, R row 1
        return (view[3] * (p[0] - view[9])
                + view[4] * (p[1] - view[10])
                + view[5] * (p[2] - view[11]))

    lpt, gpt = centroid(lig), centroid(grid)
    sx = cam_x(lpt) - cam_x(gpt)
    sy = cam_y(lpt) - cam_y(gpt)
    h = math.hypot(sx, sy)
    if h < 1.0e-8:      # grid<->ligand axis along the sight line: no roll
        return
    phi = math.atan2(-sx, sy)           # roll: ligand->up, centered-x
    c, s = math.cos(phi), math.sin(phi)
    r0 = list(view[0:3])
    r1 = list(view[3:6])
    for i in range(3):
        view[0 + i] = c * r0[i] + s * r1[i]
        view[3 + i] = -s * r0[i] + c * r1[i]
    cmd.set_view(view)


def _pitch_ligand_in_front(registry):
    """Tip the camera so the active ligand reads clearly IN FRONT of
    its own AA-grid layer (03-07 human requirement).

    Rotation about the camera's screen-x axis (get_view row 0) through
    the active ligand's centroid -- CAMERA ONLY, no game object moves;
    the pivot keeps the ligand's own cam-space coordinates (hence the
    03-06 above-grid roll composition and its x-alignment) untouched.
    Screen-x is never affected by an x-axis pitch, so the roll's
    asserts survive verbatim. The sign is picked so the grid side of
    the ligand RECEDES (deepens); atoms on the ligand's far side then
    approach, so the angle is the largest one (capped at
    _PITCH_MAX_DEG) that still leaves every atom of the ACTIVE
    molecule's grid at least _PITCH_MIN_GAP behind the ligand
    centroid. Molecule-1's grid sits below the ligand on screen (the
    03-06 roll stacks the two molecules vertically) and only ever
    recedes further under this sign. Fail-soft: an empty/degenerate
    scene or an infeasible gap keeps the rolled view (all generated
    layouts already start centroid-in-front).
    """
    view = list(cmd.get_view())
    atoms = geometry.extract_game_atoms()
    molecule = registry['molecules'][0]
    lig_name = molecule['ligand'][0]
    lig = [a for a in atoms
           if a['side'] == 'lig' and a['object'] == lig_name]
    slot_objects = set(entry[0] for entry in molecule['slots'].values())
    grid = [a for a in atoms
            if a['side'] == 'aa' and a['object'] in slot_objects]
    if not lig or not grid:
        return

    def cam(p):     # cam-space coords under the CURRENT view
        dx, dy, dz = p[0] - view[9], p[1] - view[10], p[2] - view[11]
        return (view[0] * dx + view[1] * dy + view[2] * dz,
                view[3] * dx + view[4] * dy + view[5] * dz,
                view[6] * dx + view[7] * dy + view[8] * dz)

    cpt = (sum(a['x'] for a in lig) / len(lig),
           sum(a['y'] for a in lig) / len(lig),
           sum(a['z'] for a in lig) / len(lig))
    cx, cy, cz = cam(cpt)

    g_rows = [cam((a['x'], a['y'], a['z'])) for a in grid]
    gy_cen = sum(p[1] for p in g_rows) / len(g_rows)
    side = -1.0 if gy_cen <= cy else 1.0     # which side the grid is on

    # theta limit: atoms OPPOSING the grid side approach the ligand
    # plane under the pitch; keep them _PITCH_MIN_GAP behind.
    limit = math.radians(_PITCH_MAX_DEG)
    for px, py, pz in g_rows:
        y_rel = py - cy
        if y_rel * side >= 0.0:
            continue            # grid side: recedes under the pitch
        depth = pz - cz
        if depth <= _PITCH_MIN_GAP:
            return              # cannot guarantee the gap: keep roll
        limit = min(limit, math.atan2(depth - _PITCH_MIN_GAP,
                                      abs(y_rel)))
    if limit < math.radians(0.5):
        return                  # effect below visual noise

    alpha = side * limit        # sin(alpha) matches the grid side
    c, s = math.cos(alpha), math.sin(alpha)
    r1 = list(view[3:6])
    r2 = list(view[6:9])
    for i in range(3):
        view[3 + i] = c * r1[i] - s * r2[i]
        view[6 + i] = s * r1[i] + c * r2[i]
    # re-anchor the view origin so the ligand pivot is invariant:
    # o' = o + R_old^T . (c_cam - Rx^T . c_cam), Rx the cam-space
    # rotation (r1/r2 still hold the OLD rows -- row 0 is pitch-invariant)
    rx_c = (cx, c * cy + s * cz, -s * cy + c * cz)
    delta = (cx - rx_c[0], cy - rx_c[1], cz - rx_c[2])
    for i in range(3):
        view[9 + i] += (view[0 + i] * delta[0]
                        + r1[i] * delta[1]
                        + r2[i] * delta[2])
    cmd.set_view(view)


def start_game(setup=None, seed=42, candidates=None):
    """One call: fresh/cleaned scene -> materialized game -> active
    GameWizard. Returns the LIVE wizard instance (smokes assert on its
    registry/payload via the return value).

    ``setup``  None -> a copy of setup_state.DEFAULTS (frozen Phase-1
               defaults); a user dict (Phase 4's Qt window output) is
               validated fail-closed inside engine.new_game.
    ``seed``   the generator seed (42 default; identical seeds give
               identical games).
    ``candidates``  optional manifest-row override (deterministic smoke
               candidate restriction, engine.new_game's documented
               path); None parses the bundled MANIFEST.json.

    Fail-closed: engine.GenerationError / EngineError / WizardError
    (the ValueError family) propagate -- the menu handler surfaces the
    traceback; a failed start NEVER leaves a half-built game silently.
    """
    cleaned = placement.cleanup_game_objects()
    spec = dict(setup_state.DEFAULTS if setup is None else setup)
    payload, rows = engine.new_game(spec, seed, candidates=candidates)
    registry = engine.materialize(payload, 0)
    prior = cmd.get_wizard()
    wiz = GameWizard(payload, registry, 0, 0)
    wiz.activate(replace=(1 if isinstance(prior, GameWizard) else 0))
    cmd.zoom('segi %s' % placement.SENTINEL_SEGI, buffer=5.0)
    _frame_ligand_above_grid(registry)
    _pitch_ligand_in_front(registry)
    slots = sum(len(mol['slots']) for mol in registry['molecules'])
    print('AA-match %s: game started -- %d molecule(s), %d amino-acid '
          'slot(s), seed %d (cleaned %d prior game object(s)).'
          % (__version__, len(registry['molecules']), slots,
             int(seed), cleaned['deleted']))
    return wiz
