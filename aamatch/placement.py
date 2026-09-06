"""aamatch.placement -- the cmd-tier materializer (plan 02-13).

Layer: CMD TIER. ``from pymol import cmd`` at module level is LEGAL
here; this module must NEVER be added to ``PURE_MODULES`` in
``tests/test_purity.py`` (Gates A/B scan only the pure registry; Gate D
still compiles this file under the 3.6 syntax floor). It composes the
PURE vocabulary (``aamatch.capability.AA_TOKENS`` -- the ONE
generatortoken -> fragment/resn mapping), the PURE payload (generator
level-spec), ``aamatch.paths`` (every file path routes through
``to_windows_path``), and ``aamatch.geometry`` (coordinate reads) into
real PyMOL objects.

THE PHASE-2 RULE: bake coordinates, never matrices. ALL movement goes
through ``cmd.translate/rotate(..., camera=0)`` or
``cmd.transform_object(..., homogenous=1)`` -- the mechanisms that write
world-frame coordinates (probe-verified, materialization research
§1.5/§6.1), which is exactly what ``geometry.coords_of`` /
``iterate_state`` read back for pose assertions and what the detector
consumes. The object-matrix paths (``cmd.rotate(expression, object=
NAME)`` family -- display matrix only, coords unchanged) are NEVER used
in Phase 2.

BANNED CALLS (probe-proven hazards -- a source audit for these is part
of the 02-15 review):

- ``cmd.matrix_reset``        -- REVERTS BAKED coordinates to the
  pre-transform values (probe P3.2 ``reverted=True``). Reset = spec
  REPLAY (re-bake the spec grid poses, ``reset_to_grid`` below), never
  matrix_reset.
- ``cmd.get_object_ttt``      -- SEGFAULTS the process on a TTT-bearing
  object (crash probes §12.3-12.4). If a matrix read is ever genuinely
  needed (Phase 3+), use ``cmd.get_object_matrix(incl_ttt=1)``.
- ``cmd.create`` onto an EXISTING object -- the replace/merge trap
  (PITFALL 7). Materialization avoids it BY CONSTRUCTION: every object
  is born fresh via ``cmd.fragment`` / ``cmd.load`` into a
  ``get_unused_name``-issued name.
- ``cmd.load`` into an EXISTING name -- appends a state instead of
  replacing content (probe §1.1). Ligands always load into
  ``cmd.get_unused_name('_aam_lig')``-issued names.

CONVENTIONS ESTABLISHED HERE (Phase 4 Cleanup and Phase 7 sentinel-first
reconstruction consume them; materialization research §4/§5):

- Every game object is born ``cmd.get_unused_name('_aam_<role>')`` with
  role in {'lig', 'aa', 'tmp'} -- the reserved prefix is the ONLY
  cleanup selection rule (never hetatm/polymer/chemical filters).
- Sentinel: every atom of every game object (ligand included) carries
  ``segi='AAM'`` and ``b=-999.0`` (set via ``cmd.alter`` +
  ``cmd.sort``); selectors use ``segi AAM`` / ``b < 0`` -- never
  ``b -999`` (malformed selector, silently matches nothing).
- Identity = (object_name, atom_id): the materialize-time registry maps
  slot_id -> (object, sorted atom ids) -- the Phase 7 sidecar reconciles
  against it.
- Pose asserts compare COORDINATES within POSE_TOLERANCE (1e-6 --
  PyMOL stores float32; translate round-trips accumulate ~1e-7), never
  ``cmd.get_object_matrix`` (it is the non-identity coordinate-HISTORY
  record after bakes).

Scope note: full Cleanup-button semantics (pre-game atom counts of user
objects, adopted-vs-materialized ligand bookkeeping) are Phase 4; this
module establishes and proves the PREFIX conventions. Level-scoped
materialization: a level-spec payload carries D levels;
``materialize(payload, level_index)`` materializes ONE level at a time
(the game's current level) -- cross-level staging is Phase 4 flow.

Python floor: PyMOL's Windows Python 3.9 at runtime, written 3.6-safe
(Gate D compiles every aamatch/*.py under python3.6).
"""

from pymol import cmd

from . import capability, geometry
from .paths import package_data_path, to_windows_path

# Pose assertion tolerance: PyMOL stores coordinates as float32, so
# translate/untranslate round-trips accumulate ~1e-7 (research §6.2;
# 02-09 probe rule). Pose asserts compare baked coordinates against the
# spec pose within this tolerance -- never looser, never the matrix.
POSE_TOLERANCE = 1e-6

# Sentinel values (research §4). Selectors: 'segi AAM' / 'b < 0'.
SENTINEL_SEGI = 'AAM'
SENTINEL_B = -999.0


class PlacementError(ValueError):
    """A failed MATERIALIZATION/placement step (bad spec value or a
    count/pose assert that failed closed). Subclass of ValueError --
    peers with the house fail-closed style; the message NAMES the cause
    (object, slot, expected vs actual).
    """


# Reverse of capability.AA_TOKENS: the generator emits slot['aa'] as the
# canonical RESN (uppercase, from ALL_AA = sorted(AA_RESIDUES));
# AA_TOKENS is keyed by the lowercase token. ONE vocabulary -- the
# token table stays the single home; the reverse index is derived, not
# re-transcribed.
_TOKEN_BY_RESN = dict((entry['resn'], token)
                      for token, entry in capability.AA_TOKENS.items())


def effective_position(grid_pose_position, offset):
    """The world-frame target pose of one slot/ligand:
    ``grid_pose.position + placement.offset`` (additive; generation
    research §5.1 -- the per-molecule group shift applies to ligand and
    grid TOGETHER).

    Pure float math over the spec's serialized values; returns a
    3-tuple of floats.
    """
    return (float(grid_pose_position[0]) + float(offset[0]),
            float(grid_pose_position[1]) + float(offset[1]),
            float(grid_pose_position[2]) + float(offset[2]))


def _sorted_ids(object_name):
    """Sorted atom IDs of one object (identity half; uppercase ID in the
    expression namespace -- lowercase id is the Python builtin)."""
    ids = []
    cmd.iterate(object_name, 'stored.append(ID)', space={'stored': ids})
    return sorted(int(i) for i in ids)


def _assert_count(object_name, expected_min, where):
    n_atoms = cmd.count_atoms(object_name)
    if n_atoms < expected_min:
        raise PlacementError(
            '%s: object %r has %d atom(s), expected >= %d -- refusing '
            'to place an empty/degenerate object'
            % (where, object_name, n_atoms, expected_min))
    return n_atoms


def _sentinel_tag(object_name):
    """Tag EVERY atom of the object with the game sentinel
    (segi='AAM', b=-999.0) and re-sort (prior-art convention; selector
    discipline lives in the module docstring)."""
    cmd.alter(object_name,
              "segi='%s'; b=%f" % (SENTINEL_SEGI, SENTINEL_B), space={})
    cmd.sort(object_name)


def _assert_pose(object_name, target, where):
    """Fail-closed pose assert: centroid of the baked object must equal
    the spec target within POSE_TOLERANCE (per component -- the 3-vector
    is the pose contract, research §6.2)."""
    actual = geometry.centroid_of(object_name)
    for axis in range(3):
        if abs(actual[axis] - target[axis]) > POSE_TOLERANCE:
            raise PlacementError(
                '%s: baked centroid of %r is %r, target %r differs on '
                'axis %d by %g (tolerance %g) -- the bake did not land'
                % (where, object_name, actual, target, axis,
                   abs(actual[axis] - target[axis]), POSE_TOLERANCE))


def translate_to(object_name, position):
    """THE scripted-placement primitive: translate the object so its
    centroid lands on ``position`` (3 floats), baking world-frame
    coordinates (``cmd.translate(..., state=1, camera=0)``).

    Delta is computed from the CURRENT centroid -- the call is a
    pure-function-style "move to here" regardless of where the object
    currently sits. SMOKE-04's scripted placement and Phase 3's
    game-driven moves build on this. Pose discipline: assert via
    ``geometry.coords_of`` / ``centroid_of`` snapshots -- NEVER
    ``get_object_matrix``.
    """
    current = geometry.centroid_of(object_name)
    delta = [float(position[0]) - current[0],
             float(position[1]) - current[1],
             float(position[2]) - current[2]]
    cmd.translate(delta, object_name, state=1, camera=0)
    _assert_pose(object_name,
                 (float(position[0]), float(position[1]),
                  float(position[2])),
                 'translate_to')


def transform_baked(object_name, m16):
    """Bake a row-major homogeneous 4x4 into the object's coordinates
    (``cmd.transform_object(name, M, homogenous=1)`` -- probe-verified
    bake; matrix layout per editing.py:1962-1987).

    Pose assertion usage pattern (the ONLY correct discipline):
    ``before = geometry.coords_of(object_name)`` ->
    ``transform_baked(object_name, M)`` -> ``after =
    geometry.coords_of(object_name)`` -> assert ``after[i] ==
    R.dot(before[i]) + t`` per atom within POSE_TOLERANCE. NEVER assert
    via ``get_object_matrix`` -- it is the (non-identity) transformation
    history record, not the pose.
    """
    if not isinstance(m16, (list, tuple)) or len(m16) != 16:
        raise PlacementError(
            'transform_baked: m16 must be a 16-element row-major '
            'homogeneous 4x4 (found %r)' % (m16,))
    matrix = [float(v) for v in m16]
    cmd.transform_object(object_name, matrix, homogenous=1)


def materialize(payload, level_index=0):
    """Payload -> real PyMOL objects for ONE level of the game.

    Per molecule of ``payload['levels'][level_index]``:

    1. LIGAND: fresh name ``cmd.get_unused_name('_aam_lig')``;
       ``cmd.load(to_windows_path(package_data_path('data',
       ligand['file'])), name)`` -- ALWAYS a unique name (cmd.load into
       an existing name appends a state, probe-proven). Count-asserted
       (>= 1 atom); sentinel-tagged; translated by
       ``placement['offset']`` (camera=0).
    2. PER SLOT: ``cmd.get_unused_name('_aam_aa')`` ->
       ``cmd.fragment(AA_TOKENS[token]['fragment'], name, zoom=0)`` ->
       sentinel-tag -> ``cmd.sort`` -> centroid-delta
       ``cmd.translate`` to the EFFECTIVE pose
       (``grid_pose.position + placement.offset``, world frame). Pose
       asserted per slot within POSE_TOLERANCE. NO ``cmd.create``-onto-
       existing anywhere -- fragments create fresh objects by
       construction (PITFALL 7 avoided, count asserts still guard).

    Returns the registry:

        {'level_index': int,
         'pre_game_names': snapshot of cmd.get_names('objects') taken
                           BEFORE any object was born,
         'molecules': [{'molecule_id': str,
                        'offset': (x, y, z),
                        'ligand': (object_name, sorted atom ids),
                        'slots': {slot_id: (object_name, sorted ids)}}]}

    Raises PlacementError naming the cause on any malformed payload
    field, unknown AA token, empty object, or failed pose bake.
    """
    levels = payload.get('levels') if isinstance(payload, dict) else None
    if not isinstance(levels, list) or not 0 <= level_index < len(levels):
        raise PlacementError(
            'materialize: payload %s no level_index %d (levels: %s)'
            % ('lacks' if not isinstance(levels, list) else 'has',
               level_index,
               'not-a-list' if not isinstance(levels, list)
               else '%d' % len(levels)))
    level = levels[level_index]
    molecules = level.get('molecules')
    if not isinstance(molecules, list):
        raise PlacementError(
            'materialize: level %d lacks a molecules list' % level_index)

    # Reversibility payload (research §4): the pre-game object-name
    # snapshot -- cleanup asserts the post-cleanup scene equals this.
    pre_game_names = list(cmd.get_names('objects'))
    registry = {'level_index': int(level_index),
                'pre_game_names': pre_game_names,
                'molecules': []}

    for molecule in molecules:
        molecule_id = molecule.get('molecule_id')
        placement = molecule.get('placement') or {}
        offset = placement.get('offset', (0.0, 0.0, 0.0))
        if len(offset) != 3:
            raise PlacementError(
                'materialize: molecule %r placement.offset must be 3 '
                'numbers (found %r)' % (molecule_id, offset))
        offset = (float(offset[0]), float(offset[1]), float(offset[2]))

        ligand = molecule.get('ligand')
        if not isinstance(ligand, dict) or not ligand.get('file'):
            raise PlacementError(
                'materialize: molecule %r has no ligand.file (found %r)'
                % (molecule_id, ligand))
        # Unique name ALWAYS (cmd.load appends states into existing
        # names -- probe §1.1 hazard).
        lig_name = cmd.get_unused_name('_aam_lig')
        winpath = to_windows_path(
            package_data_path('data', ligand['file']))
        cmd.load(winpath, lig_name)
        n_lig = _assert_count(lig_name, 1,
                              'materialize ligand %s' % molecule_id)
        _sentinel_tag(lig_name)
        if offset != (0.0, 0.0, 0.0):
            cmd.translate(list(offset), lig_name, state=1, camera=0)
        lig_entry = (lig_name, _sorted_ids(lig_name))

        grid = molecule.get('grid') or {}
        slots = grid.get('slots')
        n = grid.get('n')
        if not isinstance(slots, list) \
                or len(slots) != (int(n) * int(n) if n is not None
                                  else -1):
            raise PlacementError(
                'materialize: molecule %r grid %r must carry exactly '
                'n*n slots (found %s slot(s))'
                % (molecule_id, n,
                   len(slots) if isinstance(slots, list) else slots))

        slot_entries = {}
        expected_created = 1 + n * n
        created = 1
        for slot in slots:
            slot_id = slot['slot_id']
            token = _TOKEN_BY_RESN.get(slot.get('aa'))
            if token is None:
                raise PlacementError(
                    'materialize: slot %r of molecule %r names unknown '
                    'AA %r -- no AA_TOKENS entry (vocabulary drift; '
                    'generator/capability are the one vocabulary home)'
                    % (slot_id, molecule_id, slot.get('aa')))
            frag = capability.AA_TOKENS[token]['fragment']
            aa_name = cmd.get_unused_name('_aam_aa')
            cmd.fragment(frag, aa_name, zoom=0)
            _assert_count(aa_name, 1, 'materialize slot %s' % slot_id)
            _sentinel_tag(aa_name)
            grid_pose = slot.get('grid_pose') or {}
            position = grid_pose.get('position')
            if not isinstance(position, (list, tuple)) \
                    or len(position) != 3:
                raise PlacementError(
                    'materialize: slot %r of molecule %r lacks '
                    'grid_pose.position (found %r)'
                    % (slot_id, molecule_id, position))
            target = effective_position(position, offset)
            centroid = geometry.centroid_of(aa_name)
            delta = [target[0] - centroid[0],
                     target[1] - centroid[1],
                     target[2] - centroid[2]]
            cmd.translate(delta, aa_name, state=1, camera=0)
            _assert_pose(aa_name, target,
                         'materialize slot %s' % slot_id)
            slot_entries[slot_id] = (aa_name, _sorted_ids(aa_name))
            created += 1

        if created != expected_created:
            raise PlacementError(           # defensive; unreachable
                'materialize: molecule %r created %d objects, expected '
                '%d (1 ligand + n*n slots)'
                % (molecule_id, created, expected_created))
        registry['molecules'].append({
            'molecule_id': molecule_id,
            'offset': offset,
            'ligand': lig_entry,
            'slots': slot_entries,
        })
    return registry


def reset_to_grid(payload, registry, level_index=0):
    """Re-bake every AA from its CURRENT pose back to the spec grid pose.

    SPEC REPLAY -- never ``cmd.matrix_reset`` (probe-proven it REVERTS
    baked coordinates). For each registered slot: current =
    ``geometry.centroid_of`` (baked world-frame coords), target =
    effective grid pose, ``cmd.translate(target - current, camera=0)``.
    Final centroid asserted == effective pose within POSE_TOLERANCE;
    any miss raises PlacementError naming the slot.
    """
    for reg_mol, mol in zip(registry['molecules'],
                            payload['levels'][level_index]['molecules']):
        offset = reg_mol['offset']
        for slot in mol['grid']['slots']:
            slot_id = slot['slot_id']
            aa_name = reg_mol['slots'][slot_id][0]
            target = effective_position(slot['grid_pose']['position'],
                                        offset)
            centroid = geometry.centroid_of(aa_name)
            delta = [target[0] - centroid[0],
                     target[1] - centroid[1],
                     target[2] - centroid[2]]
            cmd.translate(delta, aa_name, state=1, camera=0)
            _assert_pose(aa_name, target,
                         'reset_to_grid slot %s' % slot_id)


def cleanup_game_objects():
    """Delete every existing object carrying the reserved ``_aam_``
    prefix; return ``{'deleted': n}``.

    PREFIX-ONLY rule (research §4): no hetatm/polymer/organic selectors,
    no chemical filters -- user molecules must never match. Full
    Cleanup-button semantics (pre-game atom counts, adopted ligands,
    undo of interactions) are Phase 4; this is the convention proof.
    """
    doomed = [name for name in cmd.get_names('objects')
              if name.startswith(geometry.GAME_PREFIX)]
    for name in doomed:
        cmd.delete(name)
    return {'deleted': len(doomed)}
