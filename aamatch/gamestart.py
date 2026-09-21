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

Phase-5 deferred activation (SETUP-11, plan 05-05): ``start_game``'s
``activate=False`` branch takes the scene to a FULLY-PREPARED game
WITHOUT pushing the wizard (spec.md: "countdown ... then start the
game" -- during the countdown the player must NOT pick/move/confirm via
a live game wizard). The Phase-5 Qt window orchestrates the whole
layout: pop the prior wizard -> prepare with ``activate=False`` ->
switch tab -> countdown 3-2-1 -> GO -> ``activate_game(wiz)``.
``activate_game`` is THE single activation home: it re-evaluates the
conditional replace AT ACTIVATION (the wizard stack can change during
the countdown -- the 03-05 decision is re-checked, never cached) and
anchors the per-molecule timer from zero via
``engine._current_game().start_timer(time.time())``. The DEFAULT path
(``activate=True``) is byte-identical to the pre-Phase-5 behaviour: one
call still goes from any state to a playable game, and SMOKE-08's
checks (incl. the msm ORDER-LAW teeth) stay green unchanged.

1. ``placement.cleanup_game_objects()`` FIRST -- a restart must never
   leave two generations of ``_aam_*`` objects (prefix-only deletion;
   user objects untouched).
2. ``engine.new_game(setup or DEFAULTS, seed, candidates)`` -- the
   setup is validated fail-closed INSIDE new_game.
3. ``engine.materialize(payload, 0)`` -- ONE level (the game's current
   level; cross-level staging is Phase 4/6 flow).
4. ``activate_game(wiz)`` -- THE single activation home: on the default
   path ``start_game`` calls it right after the compose; on the
   deferred path the Phase-5 window calls it at GO. It pushes the
   prepared ``GameWizard(payload, registry, 0, 0)`` with a CONDITIONAL
   replace (RECORDED DECISION, revised per checker) RE-EVALUATED at
   activation time, and starts the timer from zero. replace=1 ONLY when
   the then-current top-of-stack wizard is itself a GameWizard (restart
   hygiene: pop + clean the old game wizard so its stale msm/colors/
   selection cannot leak; 03-03's activate snapshots msm AFTER the
   push, so the popped wizard's cleanup-restored user value is what the
   new game captures -- no explicit pre-pop needed here). Otherwise
   replace=0 (plain push): a user's wizard (e.g.
   ``wizard measurement``) is NEVER popped at activation -- it goes
   dormant beneath the game and auto-resumes after Done (stack-native
   lifecycle, 03-RESEARCH-wizard-interaction sec. 1.2/2.3). On a fresh
   PyMOL (empty stack, top is None) this degenerates to a plain push.
5. Move the ACTIVE molecule's ligand to the FRONT of its own AA-grid
   layer -- IN WORLD SPACE (03-07 human decision 2026-09-10: the human
   explicitly rejected further camera surgery -- "move the molecule"
   -- after the camera-only pitch regressed the start frame to blank
   once and still read ligand-BEHIND-grid). cmd.translate along the
   current view's scene-to-camera direction until the ligand centroid
   leads EVERY atom of its own grid by at least _FRONT_LEAD Angstrom
   (visible parallax, no occlusion ambiguity). CAMERA-DEPTH SIGN LAW,
   verified against this build's own render map (smoke 08's fit
   theorem: T(p) = R . (p - view[12:15]) + view[9:12]; the camera
   looks down -z and every visible atom lands in
   [-view[16], -view[15]]): NEARER THE VIEWER READS AS THE LARGER
   cam-z. The retired camera-only pitch codified the INVERSE reading
   (it pushed the GRID nearer on screen -- the human's "placement
   still behind") and its pivot write-back of view[9:12] across a
   ~180 Angstrom camera lever arm had already thrown the whole scene
   out of frame once (both mechanisms in the regression law below).
   A world translate is immune to all of it: no view field is ever
   written, sentinels (segi/b) are untouched, and every later camera
   op preserves what this step bought -- the roll rewrites R rows 0/1
   only (cam-z invariant), the final zoom preserves R exactly. The
   offset is GAMESTART-ONLY composition: Phase-2 materialize semantics
   are untouched, so SMOKE-03/04 (which run materialize directly,
   never start_game) are unaffected; engine ops (place / detect /
   score / confirm / reset_to_grid) all read LIVE geometry, so nothing
   assumes the ligand sits at its grid's center.
6. Roll the camera about its forward axis so the ACTIVE ligand (the
   one Confirm scores) composes ABOVE its own AA grid on screen (03-06
   human preference). CAMERA COMPOSITION ONLY -- only R rows 0/1 are
   rewritten, so the step-5 front-offset (a pure cam-z matter) is
   invariant under it; the wizard's nudge math re-reads cmd.get_view()
   per press so a rolled start view needs no movement-side change. The
   roll reads ONLY the active molecule's grid (its registry slot
   objects) for the composition centroid, so an out-of-frame inactive
   molecule can never tilt the start composition.
7. Zoom the camera to frame ONLY the ACTIVE molecule -- molecule 0 in
   the Phase-3 loop: its grid slot objects PLUS its ligand object,
   identified by name from the materialize registry output -- with a
   small spatial margin -- LAST, after ALL composition (03-06 field
   report: PyMOL's fresh camera sat zoomed-in on the ligand and the
   player could not see the grid; 03-07 REGRESSION LAW below). 03-07
   HUMAN DECISION (2026-09-10): "why not zooming to only the AA grid
   of current active mol to avoid confusion" -- the start view must
   frame the active molecule's grid + ligand ONLY, so the on-screen
   frame matches the panel's "Only molecule 1 of 2 counts and is
   clickable" notice. The INACTIVE molecule stays in the scene,
   untouched, out of the initial frame as context -- its clicks are
   no-ops by design (build_slot_map scopes the loop to molecule 0;
   pick behavior unchanged). The retired whole-scene sentinel
   selection ('segi AAM' -- every game atom carries it, so it always
   pulled BOTH molecules into frame) is replaced by the registry's own
    name list, which no user object can ever match either. PHASE 5/6
    NOTE (updated 06-04): re-framing when the active molecule advances
    is a scoring-lifecycle concern (Phase 6), NOT start_game's -- but
    the composition itself is NOW AVAILABLE for any molecule index via
    ``compose_molecule_view(registry, molecule_index)`` (06-04; the
    same three helper calls, parameterized). Phase 6's wizard
    lifecycle consumes it on every molecule/level advance; the history
    above stands (gamestart composes level-0 molecule-0 starts only;
    start_game calls compose_molecule_view with the default index 0,
    byte-identical to the retired inline sequence).
   cmd.zoom is a pure dolly/re-aim: it preserves the rotation matrix
   exactly (headless probe: element delta 0.0) and therefore the roll
   composition and every relative camera-space depth established by
   step 5, while it re-derives the origin fields and clip slab from
   the current R.

   03-07 REGRESSION LAW (blank start view): an earlier build zoomed
   FIRST (step 7 before 5/6) and the then-current camera pitch rewrote
   view[9:12] -- the rotation origin RELATIVE TO THE CAMERA in camera
   coords (pymolwiki Get_View layout: 0:9 R, 9:12 origin-in-cam, 12:15
   origin in world, 15/16 front/rear clip distances, 17 ortho) --
   through a ~180 Angstrom lever arm (the camera-to-origin offset),
   shifting the whole scene ~76 Angstrom out of the framed frustum
   (probe: all 359 seed-42 game atoms outside; human report "1st frame
   is blank"). Zooming after composition is mandatory whenever the
   composition writes view fields itself: zoom re-derives
   9:12/12:15/15:16 from the selection and the CURRENT rotation. The
   geometry-side front-offset writes NO view field, but the law is
   kept binding for all future camera composition. DECISION LAW
   (03-07 human, 2026-09-10): scene composition prefers geometry-side
   moves over camera-field surgery -- the camera-only pitch regressed
   to a blank frame once and its inverted depth reading never read
   in-front to a human eye.

Engine state (payload / registry / GameState) lives module-side in
``aamatch.engine`` -- the wizard requires it live, which start_game
guarantees by construction (new_game + materialize are called here,
in order, every time). The initial-state INPUT tuple lives module-side
HERE in ``_last_start`` (SETUP-11; see below): Phase 6 Restart replays
it verbatim through ``start_game`` (ROADMAP:159). NOT a v1-style
backup object -- the materialization inputs fully regenerate the
scene, so no backup machinery is ported.

The editor_scheme start-guard contingency (03-RESEARCH-movement-spike
sec. 5.6) is explicitly NOT implemented: no start-time scheme check on
PyMOL 2.5.0 (recorded as contingency only -- §3.3's scheme law makes
the game's baked world-frame transforms scheme-independent).

Python floor: PyMOL's Windows Python 3.9 at runtime, written 3.6-safe
(Gate D compiles every aamatch/*.py under python3.6).
"""

import math
import time

from pymol import cmd

from . import __version__, engine, geometry, placement, setup_state
from .wizard import GameWizard

# 03-07 front-composition constant (see the module docstring step 5):
# the ligand centroid must lead EVERY atom of its own grid by at least
# this many Angstrom along the current view's depth axis -- generous
# (the generator floats the ligand ~5.3 Angstrom off its grid center as
# raw material; a full 5 Angstrom of viewer-relative lead on top gives
# unambiguous parallax with zero occlusion).
_FRONT_LEAD = 5.0

# SETUP-11 initial-state store (plan 05-05): after every successful
# start, start_game captures the materialization INPUT tuple here --
# {'setup' (DEEP-COPIED so later widget/export mutation can never
# corrupt the restart source), 'seed', 'candidates', 'ligand_content'}.
# Phase 6 Restart replays the tuple verbatim through start_game
# (ROADMAP:159 -- the inputs fully regenerate the scene; this is NOT
# a v1-style backup object). Set AFTER new_game + materialize (and the
# compose) SUCCEED and BEFORE any wizard mutation: a failed start
# leaves the store holding the last successfully BUILT game's tuple.
# Lives in gamestart (never in the window's _last_export): a later
# export must never corrupt the restart source.
_last_start = None


def _active_molecule_selection(registry, molecule_index=0):
    """Selection expression naming EVERY object of the ACTIVE molecule
    (molecule 0 in the Phase-3 loop): its ligand object plus all of its
    grid slot objects, taken from the materialize registry output.

    Used as the final zoom target (03-07 human decision 2026-09-10:
    frame only the active molecule's grid + ligand -- module docstring
    step 7). Name-based (``_aam_*`` reserved prefix): a user object can
    never match, and -- unlike the retired whole-scene ``segi AAM``
    selection -- the INACTIVE molecule's objects are not named, so they
    stay out of the initial frame.

    ``molecule_index`` defaults to 0 (the start path); the Phase-6
    lifecycle passes the advanced index.
    """
    molecule = registry['molecules'][molecule_index]
    names = [molecule['ligand'][0]]
    names.extend(entry[0] for entry in molecule['slots'].values())
    return ' or '.join(names)


def _frame_ligand_above_grid(registry, molecule_index=0):
    """Roll the camera so the ACTIVE molecule's ligand sits ABOVE its
    own AA grid.

    Camera composition only (03-06 human preference) -- no game object
    moves. ``view`` per cmd.get_view(): view[0:9] = row-major world->cam
    rotation R, view[9:12] = origin, view[12:14] clip front/rear,
    view[15:] flag block; this rewrites ONLY rows 0/1 of R. Fail-soft:
    an empty/distributed scene keeps the plain zoom view.

    The composition centroid is the ACTIVE molecule's grid ONLY (its
    registry slot objects): with the start view framing just that
    molecule (03-07 human decision), an out-of-frame inactive grid
    must never pull the roll alignment off the framed grid.

    ``molecule_index`` defaults to 0 (the start path); the Phase-6
    lifecycle passes the advanced index.
    """
    view = list(cmd.get_view())
    atoms = geometry.extract_game_atoms()
    molecule = registry['molecules'][molecule_index]
    lig_name = molecule['ligand'][0]
    lig = [a for a in atoms
           if a['side'] == 'lig' and a['object'] == lig_name]
    slot_objects = set(entry[0] for entry in molecule['slots'].values())
    grid = [a for a in atoms
            if a['side'] == 'aa' and a['object'] in slot_objects]
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


def _move_ligand_in_front(registry, molecule_index=0):
    """Translate the ACTIVE molecule's ligand toward the CAMERA in WORLD
    space so its centroid leads every atom of its own AA grid by at
    least _FRONT_LEAD (03-07 human decision 2026-09-10).

    ``molecule_index`` defaults to 0 (the start path); the Phase-6
    lifecycle passes the advanced index.

    GEOMETRY-SIDE composition (decision law, module docstring step 5):
    replaces the retired camera-only pitch, which regressed the start
    frame to blank once (pivot write-back of view[9:12] across the
    ~180 Angstrom camera lever arm) and read ligand-BEHIND-grid to the
    human eye. DEPTH SIGN LAW on this build (verified against smoke
    08's fit theorem -- T(p) = R . (p - view[12:15]) + view[9:12],
    camera looking down -z, visible slab T_z in [-view[16], -view[15]]):
    NEARER THE VIEWER == LARGER cam-z; the scene-to-camera world
    direction is R^T . (0,0,1), which for a row-major world->camera R
    is exactly R's ROW 2 (view[6:9]) -- the same convention
    wizard_core.view_camera_to_world proves per nudge keypress
    (view_camera_to_world(view, (0,0,1)) == (view[6], view[7],
    view[8])). A translate along that unit row adds its length to the
    cam-z of every translated point and nothing else.

    cmd.translate preserves atom identity and every per-atom tag --
    the AAM/Z sentinels (segi, b=-999) are untouched -- and it is
    viewer-relative: the needed distance is recomputed per call from
    the LIVE view and geometry. Idempotent by construction: a ligand
    already in front by _FRONT_LEAD is a no-op (need <= 0), and every
    start runs it on FRESH materialize output, so restarts reproduce
    the same composed scene. Fail-soft: an empty/second-generation
    degenerate scene (no ligand rows or no grid rows) just keeps the
    materialized geometry (the roll + final zoom still run).

    Invariance under the later steps: the offset adds nothing to cam-x
    or cam-y (translate along a depth row is orthogonal to both screen
    rows), so the step-6 roll reads the same screen separation either
    way; the roll rewrites R rows 0/1 only, so the bought cam-z lead
    survives; the final zoom preserves R exactly. Phase-2 materialize
    NEVER sees this offset -- it is gamestart-only composition.
    """
    view = list(cmd.get_view())
    atoms = geometry.extract_game_atoms()
    molecule = registry['molecules'][molecule_index]
    lig_name = molecule['ligand'][0]
    lig = [a for a in atoms
           if a['side'] == 'lig' and a['object'] == lig_name]
    slot_objects = set(entry[0] for entry in molecule['slots'].values())
    grid = [a for a in atoms
            if a['side'] == 'aa' and a['object'] in slot_objects]
    if not lig or not grid:
        return

    def cam_z(p):   # depth-axis projection; LARGER == nearer camera
        return (view[6] * (p[0] - view[9])
                + view[7] * (p[1] - view[10])
                + view[8] * (p[2] - view[11]))

    cpt = (sum(a['x'] for a in lig) / len(lig),
           sum(a['y'] for a in lig) / len(lig),
           sum(a['z'] for a in lig) / len(lig))
    nearest_grid = max(cam_z((a['x'], a['y'], a['z'])) for a in grid)
    need = nearest_grid + _FRONT_LEAD - cam_z(cpt)
    if need <= 0.0:
        return                  # already in front: idempotent no-op
    # scene-to-camera world direction = R row 2 (unit, R orthonormal)
    cmd.translate([need * view[6], need * view[7], need * view[8]],
                  lig_name, state=1, camera=0)


def compose_molecule_view(registry, molecule_index=0):
    """Compose the camera + world geometry onto ONE molecule: the 03-07
    framing laws, parameterized. GEOMETRY first -- move the molecule's
    ligand IN FRONT of its own grid in world space (03-07 human
    decision: the geometry-side offset replaced the camera-only pitch,
    whose pivot regressed the frame blank; see _move_ligand_in_front)
    -- then the 03-06 above-grid camera roll, then ONE final framing
    zoom LAST over the molecule's own objects only (03-07 human
    decision: frame the active molecule's grid + ligand so the view
    matches the "molecule 1 of 2" panel notice; regression law: zoom
    is a pure dolly/re-aim that preserves R, so every composition
    depth survives while the origin + clip slab re-derive).

    THE ONE compose home for starts AND Phase-6 molecule/level
    advances (06-04; module docstring step 7's PHASE 5/6 NOTE):
    ``start_game`` calls it with the default index 0 (byte-identical
    to the pre-06-04 inline sequence); the Phase-6 wizard lifecycle
    calls it with the advanced molecule index so a newly advanced
    molecule is framed with exactly the same composition, no
    duplicated logic.
    """
    _move_ligand_in_front(registry, molecule_index)
    _frame_ligand_above_grid(registry, molecule_index)
    cmd.zoom(_active_molecule_selection(registry, molecule_index),
             buffer=5.0)


def activate_game(wiz):
    """Push the prepared GameWizard + anchor the timer (Phase 5 GO
    step). The conditional replace is re-evaluated HERE (the stack can
    change during the countdown -- 03-05's decision re-checked, not
    cached).

    THE single activation home (05-RESEARCH-window-start-timer
    Pattern 2): the default ``start_game`` path calls it immediately
    after the compose; the deferred SETUP-11 countdown path calls it
    at GO. Either way the push happens per the 03-03 msm ORDER LAW
    (snapshot after the push) and the per-molecule timer anchors from
    zero on the live GameState.
    """
    from . import engine
    replace = 1 if isinstance(cmd.get_wizard(), GameWizard) else 0
    wiz.activate(replace=replace)
    engine._current_game().start_timer(time.time())


def start_game(setup=None, seed=42, candidates=None, ligand_content=None,
               activate=True):
    """One call: fresh/cleaned scene -> materialized game -> active
    GameWizard (unless ``activate=False``). Returns the wizard instance
    (smokes assert on its registry/payload via the return value).

    ``setup``  None -> a copy of setup_state.DEFAULTS (frozen Phase-1
               defaults); a user dict (Phase 4's Qt window output) is
               validated fail-closed inside engine.new_game.
    ``seed``   the generator seed (42 default; identical seeds give
               identical games).
    ``candidates``  optional manifest-row override (deterministic smoke
               candidate restriction, engine.new_game's documented
               path); None parses the bundled MANIFEST.json.
    ``ligand_content``  dict of synthetic file key to molecule text for
               uploaded games (04-04, additive); None = the bundled-
               manifest flow (byte-identical -- every existing call
               site unchanged). Passed through to BOTH engine.new_game
               and engine.materialize so the one-call seam stays
               complete for uploaded payloads.
    ``activate``  True (default) preserves every existing caller
               byte-for-byte: the wizard is pushed immediately and the
               timer anchors at once (the pre-Phase-5 behaviour). False
               PREPARES the game fully (cleanup -> new_game ->
               materialize -> compose) but defers activation to
               ``activate_game(wiz)`` for the countdown window
               (SETUP-11; the Phase-5 Qt path) -- the returned wizard
               is NOT on the stack until GO.

    Initial-state store: after new_game + materialize (and the compose)
    SUCCEED and BEFORE any wizard mutation, the materialization INPUT
    tuple is captured in module-level ``_last_start`` (setup is
    DEEP-COPIED; a failed start leaves the store holding the last
    successfully BUILT game's tuple -- Phase 6 Restart's replay
    source).

    Fail-closed: engine.GenerationError / EngineError / WizardError
    (the ValueError family) propagate -- the menu handler surfaces the
    traceback; a failed start NEVER leaves a half-built game silently.
    """
    cleaned = placement.cleanup_game_objects()
    spec = dict(setup_state.DEFAULTS if setup is None else setup)
    payload, rows = engine.new_game(spec, seed, candidates=candidates,
                                    ligand_content=ligand_content)
    registry = engine.materialize(payload, 0,
                                  ligand_content=ligand_content)
    wiz = GameWizard(payload, registry, 0, 0)
    # (No stack-top caching here: the conditional-replace top-of-stack
    # read moved INTO activate_game, re-evaluated at activation time --
    # the stack can change during the deferred path's countdown.)
    # Compose BEFORE activate (failure must never leave a live wizard
    # over a half-composed scene): GEOMETRY first -- move the active
    # ligand in FRONT of its own grid in world space (03-07 human
    # decision: geometry-side offset replaces the camera-only pitch,
    # whose pivot regressed the frame blank and which still read
    # behind; see _move_ligand_in_front) -- then the 03-06 above-grid
    # camera roll, then ONE final framing zoom LAST over the ACTIVE
    # molecule's objects only (03-07 human decision 2026-09-10: frame
    # the current molecule's grid + ligand so the view matches the
    # "molecule 1 of 2" panel notice; regression law: zoom-then-compose
    # threw the whole scene out of frame; zoom-last is a pure dolly/
    # re-aim that preserves R -- both compositions and every relative
    # camera-space depth -- while re-deriving origin + clip slab).
    compose_molecule_view(registry)
    # Capture the initial-state INPUT tuple AFTER new_game+materialize
    # (and the compose) SUCCEEDED and BEFORE any wizard mutation
    # (SETUP-11): the setup is DEEP-COPIED (allowed_interactions list
    # aliasing -- the 04-09 _reset_impl note) so later widget/export
    # mutation can never corrupt Phase 6 Restart's replay source.
    global _last_start
    import copy
    _last_start = {'setup': copy.deepcopy(spec), 'seed': seed,
                   'candidates': candidates, 'ligand_content': ligand_content}
    if activate:
        activate_game(wiz)
    slots = sum(len(mol['slots']) for mol in registry['molecules'])
    print('AA-match %s: game started -- %d molecule(s), %d amino-acid '
          'slot(s), seed %d (        cleaned %d prior game object(s)).'
          % (__version__, len(registry['molecules']), slots,
             int(seed), cleaned['deleted']))
    return wiz


def capture_checkpoint_snapshot(elapsed=None):
    """Build the COMPLETE checkpoint sidecar data dict (plan 07-04).

    Read-only: no scene mutation, no viewer calls besides
    ``cmd.get_wizard()``. The CALLER (``save_checkpoint`` below, or a
    smoke) owns all I/O. Returns the ``checkpoint.build_checkpoint_data``
    output (07-RESEARCH-state.md s2 schema): the embedded 'game' block
    is the FULL game_file.make_game_data output VERBATIM
    (embed-don't-regenerate; ``_last_start`` carries the materialization
    setup + candidates, ``engine._payload``/``_ligand_content`` the live
    module state), 'game_state' is engine.game_status() VERBATIM,
    'registry' is the identity-only JSON conversion, 'wizard' is
    wiz.snapshot_books().

    Elapsed resolution (timer doctrine, plan 07-04 decision 2): the
    caller-passed value (captured BEFORE the file dialog by the 07-06
    wrapper) is stored VERBATIM; None resolves to
    ``max(0.0, now - timer_anchor)`` while a game is running, and to
    None on a game_over state (final_time is frozen by stop_timer and
    authoritative). Saving on game_over is ALLOWED (decision 3 --
    to_dict carries game_over/end_state/final_time losslessly).

    Reading engine._payload/_registry/_ligand_content directly here is
    SANCTIONED: gamestart is the cmd-tier lifecycle home (the
    05-07/05-10 law binds the Qt tier only -- the tab reaches this
    state exclusively through this seam).

    Fail-closed: raises ValueError when no live GameWizard is on the
    stack (defensive for direct drives; the Qt wrapper's gate-first
    silent no-op is the primary path) or when the _last_start store is
    missing under a live wizard.
    """
    from . import checkpoint, game_file
    wiz = cmd.get_wizard()
    if not isinstance(wiz, GameWizard):
        raise ValueError(
            'no live AA-match game to save (start or resume a game '
            'first).')
    gs = engine.game_status()
    if gs['game_over']:
        elapsed = None            # final_time is frozen + authoritative
    elif elapsed is None:
        elapsed = max(0.0, time.time() - gs['timer_anchor'])
    if _last_start is None:
        raise ValueError(
            'cannot checkpoint: the initial-state store _last_start is '
            'missing under a live game wizard.')
    ligand_files = (game_file.encode_ligand_files(engine._ligand_content)
                    if engine._ligand_content else None)
    created_at = time.strftime('%Y-%m-%dT%H:%M:%S')
    game_data = game_file.make_game_data(
        setup=_last_start['setup'], payload=engine._payload,
        ligand_files=ligand_files, created_at=created_at)
    return checkpoint.build_checkpoint_data(
        game_data=game_data, game_state=gs, elapsed_at_save=elapsed,
        registry=engine._registry, wizard_books=wiz.snapshot_books(),
        candidates=_last_start['candidates'], created_at=created_at)


def save_checkpoint(path, data):
    """Write ONE atomic .aamz checkpoint archive; return the final path.

    (plan 07-04, Recorded Decision 1) ``cmd.save`` scope = FULL session
    (no selection argument), paired with the full-replace resume load --
    a game-scoped session save would DESTROY the user's own objects on
    resume, and SMOKE-17 proved the full-session round-trip exactly.

    Sequence: mint a temp .pse INSIDE this (Windows) process (no path
    conversion needed -- 07-RESEARCH-import.md S3-3), save the full
    session into it, hand it to ``checkpoint.write_checkpoint_zip``
    (its own temp + os.replace atomic write, members game.pse +
    state.json), then remove the temp .pse best-effort in a finally
    block (the PA-__init__:775 shape). ``path`` is routed through
    paths.to_windows_path (the AGENTS path law; Windows QFileDialog
    paths pass through unchanged).

    NO viewer refresh, NO modal, NO scheduling tail -- Save never ends
    the game. Failures (session-save OSError family; zip OSError /
    ValueError) propagate to the caller's guard (the 04-09 contract): a
    failed save leaves the scene and the game untouched, and the temp
    .pse is cleaned regardless.
    """
    import os
    import tempfile
    from . import checkpoint, paths
    final = paths.to_windows_path(path)
    fd, tmp_pse = tempfile.mkstemp(suffix='.pse')
    os.close(fd)
    try:
        cmd.save(tmp_pse)                 # FULL session (decision 1)
        checkpoint.write_checkpoint_zip(final, data, tmp_pse)
    finally:
        try:
            os.unlink(tmp_pse)
        except OSError:
            pass
    return final
