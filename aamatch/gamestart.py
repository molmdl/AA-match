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
    slots = sum(len(mol['slots']) for mol in registry['molecules'])
    print('AA-match %s: game started -- %d molecule(s), %d amino-acid '
          'slot(s), seed %d (cleaned %d prior game object(s)).'
          % (__version__, len(registry['molecules']), slots,
             int(seed), cleaned['deleted']))
    return wiz
