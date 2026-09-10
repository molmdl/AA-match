"""aamatch.engine -- the headless operation set (plan 02-14).

Layer: CMD TIER. ``from pymol import cmd`` at module level is LEGAL
here; this module must NEVER be added to ``PURE_MODULES`` in
``tests/test_purity.py`` (Gates A/B scan only the pure registry; Gate D
still compiles this file under the 3.6 syntax floor). NO Qt anywhere --
the Phase-3+ controller wraps these same ops with callbacks; Phase 2
proves them headless (SMOKE-04), exactly per materialization research
SS7.2.

STATE SPLIT (the one data-flow rule, research SS7.2 / ARCHITECTURE):

- The LEVEL-SPEC PAYLOAD is the single source of truth: seed, grids,
  required, ligand refs, detector_version stamp. Nothing re-derives
  from the seed at replay; save/load is a Phase-7 persistence concern.
- Module-level runtime state here: the current payload, the placement
  registry, and ONE ``game_state.GameState`` (plain data -- scores,
  formed types, counters). Reset/recover replay the spec, never this
  state.
- PyMOL holds ATOMS + SENTINELS only.

MOLECULE SCOPING (03-06 cross-molecule scoring guard): the detector
runs on a COMBINED ligand feature layer, so an unscoped Confirm would
credit a required-type record formed over the WRONG molecule's ligand
(benign in the 1-scored-molecule field games, a landmine for real
multi-molecule play). ``detect_molecule`` restricts the detector's
INPUT to one molecule (its ligand object + its slot objects) -- the
wrong partner is absent by construction -- and post-filters with the
WSL-testable pure half ``game_state.records_for_molecule``;
``score_current``/``confirm`` consume the scoped pass. ``detect()``
remains the canonical WHOLE-SCENE surface (smoke/grid hygiene asserts).

OPS (each count-asserted; plain-data in/out):

1. ``new_game(setup, seed) -> (payload, manifest_entries)`` -- manifest
   parsed via read_json_file + parse_manifest_dict; candidates =
   enumerate_entries (whole set, or filtered to setup['demo_set_id']
   when non-empty); per-candidate ``ligand_data`` built the SMOKE-03
   way: temp ``_aam_tmp`` load -> extract_game_atoms (this object only)
   -> bounding_sphere + ligand_profile over the remapped bond block ->
   {'centroid', 'radius', 'profile'} keyed by (set_id, entry_id) (the
   02-08 deviation-3 contract) -> temp deleted in a finally. The object
   list is asserted UNCHANGED across the whole op.
2. ``materialize(payload, level_index=0) -> registry`` -- delegates to
   placement.materialize; payload + registry kept module-side so the
   later ops need no bookkeeping from callers.
3. ``place_aa(slot_id, position)`` -- translate_to over the registry's
   object for that slot (baked, count-asserted).
4. ``reset_to_grid()`` -- spec REPLAY via placement.reset_to_grid
   (never matrix_reset).
5. ``detect() -> records`` -- geometry.extract_game_atoms() +
   geometry.ligand_bonds per registered ligand object with the
   probe-pinned remap (bond position i -> index_to_id[i+1] -> atom id
   -> position in the (object, id)-sorted ligand records) ->
   detector.detect (the 7-type surface, NOT detect_part1). Whole-scene.
5b. ``detect_molecule(level_index, molecule_index) -> records`` -- the
   MOLECULE-SCOPED variant (see MOLECULE SCOPING above): input atoms
   restricted to the molecule's ligand + slot objects, bonds remapped
   for that ligand only, detector.detect over the subset, then the
   pure records_for_molecule post-filter.
6. ``score_current(level_index, molecule_index, required,
   records=None) -> (score, formed_types)`` -- game_state.score via
   record_molecule_result (score + formed types stored together);
   records None -> a fresh detect_molecule pass; returns plain data
   for a future UI.
7. ``confirm(level_index, molecule_index, required) -> (records,
   score, formed_types)`` -- detect_molecule + score_current
   composition (records returned are the MOLECULE-SCOPED set); the
   Phase-3 Confirm handler wraps exactly this.

Python floor: PyMOL's Windows Python 3.9 at runtime, written 3.6-safe
(Gate D compiles every aamatch/*.py under python3.6).
"""

from pymol import cmd

from . import capability, detector, game_state, generator, geometry
from . import placement
from .manifest import enumerate_entries, parse_manifest_dict
from .paths import package_data_path, to_windows_path
from .persistence import read_json_file
from .setup_state import validate_state


class EngineError(ValueError):
    """A failed ENGINE op (bad argument, missing runtime state, or a
    count/hygiene assert that failed closed). Subclass of ValueError --
    peers with PlacementError / GenerationError; the message NAMES the
    cause."""


# --- Module-level runtime state (see the STATE SPLIT docstring) -----------
_payload = None
_registry = None
_game = None


def _current_game():
    """The live GameState (created by new_game; EngineError before)."""
    if _game is None:
        raise EngineError(
            'engine: no live game -- call new_game(setup, seed) first')
    return _game


def _current_registry():
    if _registry is None:
        raise EngineError(
            'engine: nothing materialized -- call materialize(payload) '
            'after new_game')
    return _registry


def _remap_ligand_bonds(records, lig_objects):
    """Productionized SMOKE-03 remap helper (02-13 pattern, generalized
    to multiple ligand objects).

    ``records`` = extract_game_atoms output; ``lig_objects`` = the
    ligand object name(s) whose bond blocks to read. Bonds from
    ``cmd.get_bonds`` are 0-based WALK positions; for a whole
    single-object selection position i addresses the atom whose
    ``index`` property is i+1 (02-09 pinned mapping), and that atom's
    detector-side position in the (object, id)-sorted ligand record
    list is what the pure detector validates fail-closed.

    Returns (lig_records, lig_bonds) -- ligand-side records sorted by
    (object, id), bonds as 3-tuples (pos_i, pos_j, order) sorted
    ascending.
    """
    lig = sorted((r for r in records if r['side'] == 'lig'),
                 key=lambda r: (r['object'], r['id']))
    id_pos = dict(((r['object'], r['id']), i)
                  for i, r in enumerate(lig))
    out = []
    for obj in lig_objects:
        bonds, index_to_id = geometry.ligand_bonds(obj)
        for (i, j, order) in bonds:
            out.append((id_pos[(obj, index_to_id[i + 1])],
                        id_pos[(obj, index_to_id[j + 1])], int(order)))
    out.sort()
    return lig, out


def _ligand_data_for(row, names_before):
    """Build the {'centroid', 'radius', 'profile'} geometry dict for ONE
    manifest candidate row (the 02-08 deviation-3 contract, proven by
    SMOKE-03): temp load -> extract (this object only) -> bounding
    sphere + capability.ligand_profile -> temp deleted in a finally.
    Temp objects never leak; the caller asserts the object list is
    unchanged at the end.
    """
    identity = (row['set_id'], row['entry_id'])
    tmp_name = cmd.get_unused_name('_aam_tmp')
    try:
        winpath = to_windows_path(
            package_data_path('data', row['file']))
        cmd.load(winpath, tmp_name)
        n_atoms = cmd.count_atoms(tmp_name)
        want = row.get('atom_count')
        if want is not None and n_atoms != int(want):
            raise EngineError(
                'new_game: ligand %r loaded %d atom(s), manifest says '
                '%d -- the fixture/manifest pair is inconsistent'
                % (identity, n_atoms, int(want)))
        records = [r for r in geometry.extract_game_atoms()
                   if r['object'] == tmp_name]
        center, radius = geometry.bounding_sphere(records)
        lig_records, lig_bonds = _remap_ligand_bonds(records,
                                                     [tmp_name])
        profile = capability.ligand_profile(lig_records, lig_bonds)
        return {'centroid': center, 'radius': radius,
                'profile': profile}
    finally:
        if tmp_name in cmd.get_names('objects'):
            cmd.delete(tmp_name)
        if cmd.get_names('objects') != names_before:
            raise EngineError(
                'new_game: temp ligand %r leaked (objects before: %s, '
                'after: %s) -- new_game must leave the scene untouched'
                % (tmp_name, names_before, cmd.get_names('objects')))


def new_game(setup, seed, candidates=None):
    """Op 1: setup + seed -> (level-spec payload, manifest_entries).

    ``candidates`` is an optional override list of manifest entry rows
    (with 'set_id'); None parses the bundled MANIFEST.json: whole set,
    or filtered to rows matching the validated setup's non-empty
    ``demo_set_id`` (v1: single-set dev manifest). Whatever the source,
    ligand_data is built per the enrolled candidates and the scene is
    asserted unchanged across the op (temps never leak).
    """
    validated = validate_state(setup)
    names_before = list(cmd.get_names('objects'))
    if candidates is None:
        container = read_json_file(
            package_data_path('data', 'MANIFEST.json'))
        manifest_payload = parse_manifest_dict(container)
        rows = enumerate_entries(manifest_payload)
        demo_set = validated.get('demo_set_id') or ''
        if demo_set:
            rows = [row for row in rows
                    if row['set_id'] == demo_set]
            if not rows:
                raise EngineError(
                    'new_game: demo_set_id %r matches no manifest set '
                    '-- check setup/MANIFEST.json' % (demo_set,))
    else:
        rows = [dict(row) for row in candidates]
        for row in rows:
            if not row.get('set_id') or not row.get('entry_id'):
                raise EngineError(
                    'new_game: every candidate row must carry set_id '
                    'and entry_id (found %r)' % (row,))
    if not rows:
        raise EngineError(
            'new_game: zero ligand candidates enrolled -- generation '
            'cannot be solvable with an empty supply')

    ligand_data = {}
    for row in rows:
        ligand_data[(row['set_id'], row['entry_id'])] = \
            _ligand_data_for(row, names_before)

    payload = generator.generate(seed, validated, rows, ligand_data,
                                 validated['difficulty_levels'])

    global _payload, _game, _registry
    _payload = payload
    _registry = None               # a new game invalidates old objects
    _game = game_state.GameState()
    if cmd.get_names('objects') != names_before:
        raise EngineError(
            'new_game: scene changed across generation (before: %s, '
            'after: %s)' % (names_before, cmd.get_names('objects')))
    return payload, rows


def materialize(payload, level_index=0):
    """Op 2: payload -> registry (placement.materialize delegate).

    The payload + registry are kept module-side, so place_aa /
    reset_to_grid / detect need no plumbing from callers.
    """
    registry = placement.materialize(payload, level_index=level_index)
    global _payload, _registry
    _payload = payload
    _registry = registry
    return registry


def _slot_object(registry, slot_id):
    """The object name registered for ``slot_id`` (fail-closed)."""
    for mol in registry['molecules']:
        entry = mol['slots'].get(slot_id)
        if entry is not None:
            return entry[0]
    raise EngineError(
        'engine.place_aa: slot %r is not in the materialized registry '
        '[%s]' % (slot_id, sorted(
            sid for m in registry['molecules'] for sid in m['slots'])))


def place_aa(slot_id, position):
    """Op 3: baked placement -- the object's centroid lands on
    ``position`` (3 floats) via placement.translate_to (count- and
    pose-asserted; camera=0, world frame)."""
    registry = _current_registry()
    placement.translate_to(_slot_object(registry, slot_id), position)


def reset_to_grid():
    """Op 4: spec REPLAY -- every AA re-bakes to its spec grid pose
    (placement.reset_to_grid; never matrix_reset)."""
    registry = _current_registry()
    if _payload is None:
        raise EngineError(
            'engine.reset_to_grid: no payload on the engine -- call '
            'new_game/materialize first')
    placement.reset_to_grid(_payload, registry,
                            level_index=registry['level_index'])


def detect():
    """Op 5: the canonical 7-type detection over the live game scene.

    geometry.extract_game_atoms() + geometry.ligand_bonds per
    registered ligand object (probe-pinned remap via
    _remap_ligand_bonds) -> detector.detect -- the 7-type surface, NOT
    detect_part1. Returns the canonically sorted record list.
    """
    registry = _current_registry()
    records = geometry.extract_game_atoms()
    lig_objects = [mol['ligand'][0] for mol in registry['molecules']]
    _, lig_bonds = _remap_ligand_bonds(records, lig_objects)
    return detector.detect(records, lig_bonds)


def detect_molecule(level_index, molecule_index):
    """Op 5b: detection SCOPED to one molecule (03-06 cross-molecule
    scoring guard; see the module docstring's MOLECULE SCOPING note).

    The input atoms are restricted to the molecule's ligand object plus
    its slot objects (the wrong-ligand partner is absent by
    construction), the bond block is remapped for that ligand only,
    and the output runs through the pure
    game_state.records_for_molecule post-filter (belt-and-braces; the
    detector's group-based records name their ligand object via a
    single shared feature layer, so the post-filter also pins the
    attribution the combined layer cannot). Returns the canonically
    sorted scoped record list.
    """
    registry = _current_registry()
    molecules = registry['molecules']
    index = int(molecule_index)
    if not 0 <= index < len(molecules):
        raise EngineError(
            'engine.detect_molecule: molecule_index %d out of range '
            '(registry has %d molecule(s))' % (index, len(molecules)))
    molecule = molecules[index]
    lig_object = molecule['ligand'][0]
    slot_objects = set(entry[0]
                       for entry in molecule['slots'].values())
    keep = slot_objects | set((lig_object,))
    records = [r for r in geometry.extract_game_atoms()
               if r['object'] in keep]
    _, lig_bonds = _remap_ligand_bonds(records, [lig_object])
    found = detector.detect(records, lig_bonds)
    return game_state.records_for_molecule(found, slot_objects,
                                           lig_object)


def score_current(level_index, molecule_index, required, records=None):
    """Op 6: score the current scene against ``required``.

    ``records`` None -> a fresh MOLECULE-SCOPED detect pass
    (detect_molecule -- the 03-06 cross-molecule scoring guard). Score
    + formed types are recorded into the module-level GameState in ONE
    call (record_molecule_result -- the two views can never drift).
    Returns (score, formed_types): plain data for a future UI.
    """
    if records is None:
        records = detect_molecule(level_index, molecule_index)
    game = _current_game()
    value = game.record_molecule_result(level_index, molecule_index,
                                        required, records)
    key = game_state.GameState.molecule_key(level_index, molecule_index)
    formed = list(game.formed_types_per_molecule[key])
    return value, formed


def confirm(level_index, molecule_index, required):
    """Op 7: detect_molecule + score composition -> (records, score,
    formed_types); records are the MOLECULE-SCOPED set (03-06 guard).
    The Phase-3 Confirm handler wraps exactly this."""
    records = detect_molecule(level_index, molecule_index)
    value, formed = score_current(level_index, molecule_index,
                                  required, records=records)
    return records, value, formed
