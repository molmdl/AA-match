"""Pure wizard gameplay logic (plan 03-01, Phase 3).

Layer: PURE -- registered in tests/test_purity.py PURE_MODULES. NEVER
import cmd/pymol/Qt/numpy here (Gate A scans every scope, module level
and function bodies); the cmd-tier consumer is aamatch/wizard.py
(translated: this file may contain ZERO imports, stdlib or otherwise,
because the helpers below need nothing beyond plain Python).

House style: % formatting only, floats in/floats out via float()
coercion (vec3 contract), fail-closed ValueError refusals whose
messages NAME the cause.

The wizard-side logic that is NOT a ``cmd`` call lives here:

- ``build_slot_map`` -- reverse map {object_name: slot_id} over ONE
  molecule of the placement registry (aamatch/placement.py's registry
  shape; 03-RESEARCH-wizard-interaction.md sections 5.3/5.4: ONE
  ``_aam_aa*`` object per slot, so a click's object name alone resolves
  the slot -- the PLAY-01 pick-identity precondition).
- ``transient_selection`` -- the delete-guard behind the canonical
  do_select->do_pick map: only transient selections ('sele',
  'pk1'..'pk4', '_'-prefixed) may be deleted by the wizard's pick
  routing; a user's NAMED active selection must survive (RESEARCH
  section 10.2 recorded decision: transient-only delete, accepting a
  leftover enabled named selection over user-data loss). Game-object
  names are never passed to this guard by do_select -- the object
  identity comes from pk1's model field; the guard only classifies the
  selection NAME.
- ``view_camera_to_world`` -- convert a CAMERA-frame step (nudge intent
  from keys/buttons) into the WORLD-frame step to hand the movement
  layer. ``view`` mimics cmd.get_view() (>= 9 numbers; view[0:9] =
  row-major 3x3 rotation R, world->camera per PyMOL's get_view
  convention), so the world step is R^T . step: element i =
  R[0]*step[0] + R[3]*step[1] + R[6]*step[2] etc. NOTE (pinned for
  03-04/SMOKE-07): the R^T convention is live-verified against a
  scripted cmd.set_view; if the live build proves the opposite
  convention, this function is the single fix site.
- ``ensure_snapshot`` / ``color_map`` / ``snapshot_objects`` -- PLAY-01
  color-feedback bookkeeping (RESEARCH section 4): snapshot a slot's
  atom colors BEFORE its first recolor (lazy, per-slot, exactly once),
  restore via plain {ID: color} maps, cleanup iterates
  snapshot_objects. The store dict is mutated in place and is
  caller-owned plain picklable data ((ID, color) rows as cmd.iterate
  hands them to a space dict).
"""

# Movement model constants (03-RESEARCH-movement-spike.md verdict):
NUDGE_STEP = 1.0               # Angstrom per nudge press
ROTATE_STEP_DEG = 10.0         # keyboard rotate step, degrees
ROTATE_BUTTON_STEP_DEG = 90.0  # panel rotate-button step, degrees

# PLAY-01 feedback color (v1 recolor precedent, game.py:208-213).
HIGHLIGHT_COLOR = 'green'


def build_slot_map(registry, molecule_index):
    """Reverse map {object_name: slot_id} for ONE molecule's slots.

    ``registry`` is the materialize() return shape
    (aamatch/placement.py)::

        {'level_index': int,
         'pre_game_names': [...],
         'molecules': [{'molecule_id': str,
                        'offset': (x, y, z),
                        'ligand': (object, sorted ids),
                        'slots': {slot_id: (object_name, ids)}}]}

    Only molecules[molecule_index]'s slots land in the map (Phase 3
    scopes the wizard to one molecule; RESEARCH section 5.4). Raises
    ValueError naming the cause on a registry without a 'molecules'
    list, an out-of-range molecule_index, a molecule without a 'slots'
    dict, or a slot entry that is not a 2-tuple with a non-empty string
    object name -- the reverse map is the wizard's pick identity, so a
    bad shape must refuse loudly instead of misrouting clicks.
    """
    molecules = registry.get('molecules') if isinstance(registry, dict) \
        else None
    if not isinstance(molecules, list):
        raise ValueError(
            'build_slot_map: registry lacks a molecules list '
            '(registry as returned by placement.materialize)')
    try:
        index = int(molecule_index)
    except (TypeError, ValueError):
        raise ValueError(
            'build_slot_map: molecule_index must be an int (found %r)'
            % (molecule_index,))
    if not 0 <= index < len(molecules):
        raise ValueError(
            'build_slot_map: molecule_index %d out of range (registry '
            'has %d molecule(s))' % (index, len(molecules)))
    molecule = molecules[index]
    slots = molecule.get('slots') if isinstance(molecule, dict) else None
    if not isinstance(slots, dict):
        raise ValueError(
            'build_slot_map: molecule %d lacks a slots dict '
            '(registry shape is {slot_id: (object, ids)})' % index)
    reverse = {}
    for slot_id, entry in slots.items():
        if not isinstance(entry, tuple) or len(entry) != 2:
            raise ValueError(
                'build_slot_map: slot %r entry must be a 2-tuple '
                '(object_name, ids) (found %r)' % (slot_id, entry))
        object_name = entry[0]
        if not isinstance(object_name, str) or not object_name:
            raise ValueError(
                'build_slot_map: slot %r entry must carry a non-empty '
                'string object name (found %r)' % (slot_id, object_name))
        reverse[object_name] = slot_id
    return reverse


def transient_selection(name):
    """True iff ``name`` is a transient selection the wizard may delete.

    Only 'sele', the pick buffers 'pk1'..'pk4', and '_'-prefixed names
    are transient -- a user's named selection must survive the wizard's
    per-pick cleanup (recorded RESEARCH section 10.2 decision).
    """
    return (name == 'sele'
            or name in ('pk1', 'pk2', 'pk3', 'pk4')
            or name.startswith('_'))


def view_camera_to_world(view, step):
    """Convert a camera-frame step vector into world frame.

    ``view`` mimics cmd.get_view(): >= 9 numbers with view[0:9] the
    row-major 3x3 rotation R (world->camera, PyMOL convention). The
    world step is R^T . step, i.e. with R laid out row-major as
    (r00 r01 r02 r10 r11 r12 r20 r21 r22)::

        world_x = r00*sx + r10*sy + r20*sz
        world_y = r01*sx + r11*sy + r21*sz
        world_z = r02*sx + r12*sy + r22*sz

    Identity rotation is the pass-through identity. Returns a plain
    float 3-tuple (int steps coerced -- house vec3 contract; net of
    floats out). Raises ValueError naming the cause when ``view``
    carries fewer than 9 numbers (no square block to invert).
    """
    if len(view) < 9:
        raise ValueError(
            'view_camera_to_world: view must carry >= 9 numbers (the '
            'row-major 3x3 rotation block view[0:9]); found %d'
            % len(view))
    sx = float(step[0])
    sy = float(step[1])
    sz = float(step[2])
    r = view[0:9]
    return (float(r[0] * sx + r[3] * sy + r[6] * sz),
            float(r[1] * sx + r[4] * sy + r[7] * sz),
            float(r[2] * sx + r[5] * sy + r[8] * sz))


def ensure_snapshot(store, obj, rows):
    """Snapshot ``obj``'s atom colors into ``store`` exactly once.

    ``rows`` is the [(ID, color), ...] list the cmd tier harvested via
    cmd.iterate (space-dict pattern). The FIRST call copies ``rows``
    into ``store[obj]`` and returns True (the snapshot precedes the
    first recolor, PLAY-01 feedback); ANY later call returns False and
    leaves the ORIGINAL snapshot untouched (idempotent -- the recolored
    scene never drifts into the restore data).

    The copy is defensive: later mutation of the caller's ``rows``
    list or its tuples must not leak into the stored snapshot. The
    store is plain picklable data, mutated in place, caller-owned.
    """
    if obj in store:
        return False
    store[obj] = [(atom_id, color) for atom_id, color in rows]
    return True


def color_map(store, obj):
    """Restore view of a snapshot: {ID: color}, or None when absent."""
    rows = store.get(obj)
    if rows is None:
        return None
    result = {}
    for atom_id, color in rows:
        result[atom_id] = color
    return result


def snapshot_objects(store):
    """Sorted list of snapshotted object names (deterministic
    cleanup order; python3.6 does not guarantee dict order)."""
    return sorted(store)
