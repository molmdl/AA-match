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
3. ``place_aa(slot_id, position, molecule_index=None)`` -- translate_to
   over the registry's object for that slot (baked, count-asserted).
   Slot ids are PER-MOLECULE scoped (generator.py:524 -- 'r0c0'
   repeats across the molecules of one level), so the resolution is
   molecule-aware: ``molecule_index`` pins the molecule's slots
   EXACTLY (the wizard's scripted move_to passes its LIVE molecule
   index -- first-match across molecules would silently move the WRONG
   AA); None keeps the Phase-2 cross-molecule first-match search for
   the legacy single-molecule call sites.
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
5c. ``ligand_profile_molecule(level_index, molecule_index) ->
    profile`` -- the molecule's ligand chemistry profile recomputed
    LIVE from its materialized ligand object (extract restricted to
    that object -> _remap_ligand_bonds -> capability.ligand_profile);
    byte-equal to generation-time (the ligand never changes during
    play). The PLAY-05 hint's "could form" input (05-08).
6. ``score_current(level_index, molecule_index, required,
   records=None) -> (score, formed_types)`` -- game_state.score via
   record_molecule_result (score + formed types stored together);
   records None -> a fresh detect_molecule pass; returns plain data
   for a future UI.
7. ``confirm(level_index, molecule_index, required) -> (records,
   score, formed_types)`` -- detect_molecule + score_current
   composition (records returned are the MOLECULE-SCOPED set); the
   Phase-3 Confirm handler wraps exactly this.
 8. ``game_status() -> dict`` -- the 05-07 READ path: the live
    GameState's to_dict() snapshot, no mutation; EngineError before
    new_game (inherited from _current_game).
 9. ``record_scored(level_index, molecule_index, required,
    records=None) -> (score, formed_types)`` -- the ONE lifecycle
    record site (06-03): refuses a second record via
    GameState.has_record (the D4/Q10 guard covers Confirm AND Skip
    with one check), then delegates to score_current. The guard lives
    HERE, not inside score_current/confirm -- those stay byte-identical
    for the smoke detection probes that legitimately re-score.
10. ``skip_molecule(level_index, molecule_index, required) ->
    (score, formed_types)`` -- SCORE-05 mechanics: the
    detection-at-skip-time partial score via record_scored (the 02-10
    sanctioned semantics), then skip_count += 1.
11. ``advance_molecule()`` -- the data-only within-level transition
    (GameState.advance_molecule; deliberately no range check -- the
    wizard owns range logic).
12. ``total_score()`` -- the running total (SCORE-01 sum).
13. ``is_over()`` -- the game_over bool gate (EngineError before
    new_game via _current_game, like every read).
14. ``advance_level() -> registry`` -- SCORE-03 mechanics: cleanup ->
    materialize(L+1) -> GameState.advance_level LAST (fail-closed
    ordering; pure data cannot fail), the timer anchor untouched by
    design.
15. ``give_up(now=None) -> summary`` -- SCORE-06: giveup_count + 1,
    end_state 'gave_up', stop_timer freeze, then the endgame summary.
16. ``complete_game(now=None) -> summary`` -- the natural-completion
    twin (end_state 'completed'; same freeze + summary).
17. ``endgame_summary() -> dict`` -- the SCORE-07 READ op: the 06-01
    contract dict from the live game, no mutation.

Python floor: PyMOL's Windows Python 3.9 at runtime, written 3.6-safe
(Gate D compiles every aamatch/*.py under python3.6).
"""

import time

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
_ligand_content = None      # 06-03: advance_level's re-materialization input


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


def _ligand_data_for(row, names_before, ligand_content=None):
    """Build the {'centroid', 'radius', 'profile'} geometry dict for ONE
    manifest candidate row (the 02-08 deviation-3 contract, proven by
    SMOKE-03): temp load -> extract (this object only) -> bounding
    sphere + capability.ligand_profile -> temp deleted in a finally.
    Temp objects never leak; the caller asserts the object list is
    unchanged at the end.

    ``ligand_content`` (04-04, additive; default None): dict mapping
    synthetic file keys such as 'uploads/mol-001.sdf' to molecule
    record text; None = the package-resolved manifest flow. When the
    row's 'file' IS a key of the dict, the record loads FROM THE STRING
    via cmd.read_sdfstr/read_mol2str (same C parser as file loads,
    importing.py:931-959/1038-1069) -- the string path NEVER touches
    package_data_path or any filesystem path, so absolute-path keys are
    structurally impossible (the os.path.join hazard from the 04
    research). The reader is chosen from the row's 'format' key
    (manifest.py's format rule) and count_states must be exactly 1
    (records are split one molecule per content entry, fail-closed).
    The atom_count cross-check below stays ACTIVE for the string path
    too. Default None keeps every existing call site and test
    byte-identical (the package cmd.load path, unchanged).
    """
    identity = (row['set_id'], row['entry_id'])
    tmp_name = cmd.get_unused_name('_aam_tmp')
    try:
        if ligand_content is not None and row['file'] in ligand_content:
            text = ligand_content[row['file']]
            fmt = row.get('format')
            if fmt == 'mol2':
                if hasattr(cmd, 'read_mol2str'):
                    cmd.read_mol2str(text, tmp_name)
                else:
                    raise EngineError(
                        'new_game: uploaded ligand %r needs '
                        'cmd.read_mol2str, which THIS PyMOL build does '
                        'not export (2.5.0 api.py omits it) -- mol2 '
                        'uploads are unavailable here' % (identity,))
            elif fmt == 'sdf':
                cmd.read_sdfstr(text, tmp_name)
            else:
                raise EngineError(
                    'new_game: uploaded ligand %r has unsupported format %r '
                    '(expected sdf or mol2)' % (identity, fmt))
            if cmd.count_states(tmp_name) != 1:
                raise EngineError(
                    'new_game: uploaded ligand %r decoded to %d state(s) -- '
                    'records must be split one molecule per content entry'
                    % (identity, cmd.count_states(tmp_name)))
        else:
            winpath = to_windows_path(
                package_data_path('data', row['file']))
            try:
                cmd.load(winpath, tmp_name)
            except Exception as exc:
                raise EngineError(
                    'new_game: ligand %r failed to load from the '
                    'package data dir (%s: %s) -- the bundled fixture '
                    'may be missing/corrupt, or the row names a '
                    'synthetic key WITHOUT ligand_content'
                    % (identity, type(exc).__name__, exc))
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


def new_game(setup, seed, candidates=None, ligand_content=None):
    """Op 1: setup + seed -> (level-spec payload, manifest_entries).

    ``candidates`` is an optional override list of manifest entry rows
    (with 'set_id'); None parses the bundled MANIFEST.json: whole set,
    or filtered to rows matching the validated setup's non-empty
    ``demo_set_id`` (v1: single-set dev manifest). Whatever the source,
    ligand_data is built per the enrolled candidates and the scene is
    asserted unchanged across the op (temps never leak).

    ``ligand_content`` (04-04, additive; default None): dict mapping
    synthetic file keys such as 'uploads/mol-001.sdf' to molecule
    record text for uploaded games; None = the package-resolved
    manifest flow (byte-identical for demo sets -- every existing call
    site and test unchanged). Passed straight through to
    ``_ligand_data_for`` per candidate row; the string path never
    touches ``package_data_path``. The value is ALSO retained
    module-side (``_ligand_content``, 06-03): advance_level's
    re-materialization input for uploaded games (demo games store
    None -- byte-identical).
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
            _ligand_data_for(row, names_before, ligand_content)

    payload = generator.generate(seed, validated, rows, ligand_data,
                                 validated['difficulty_levels'])

    global _payload, _game, _registry, _ligand_content
    _payload = payload
    _registry = None               # a new game invalidates old objects
    _game = game_state.GameState()
    _ligand_content = ligand_content   # advance_level's re-materialize input
    if cmd.get_names('objects') != names_before:
        raise EngineError(
            'new_game: scene changed across generation (before: %s, '
            'after: %s)' % (names_before, cmd.get_names('objects')))
    return payload, rows


def materialize(payload, level_index=0, ligand_content=None):
    """Op 2: payload -> registry (placement.materialize delegate).

    The payload + registry are kept module-side, so place_aa /
    reset_to_grid / detect need no plumbing from callers.

    ``ligand_content`` (04-04, additive; default None): dict of
    synthetic file key to molecule record text for uploaded payloads;
    None = the package-resolved flow (byte-identical -- every existing
    call site unchanged). Passed straight through to
    ``placement.materialize``.
    """
    registry = placement.materialize(payload, level_index=level_index,
                                     ligand_content=ligand_content)
    global _payload, _registry
    _payload = payload
    _registry = registry
    return registry


def adopt_game(payload, registry, game_state_dict, ligand_content,
               elapsed_at_save=None):
    """Rebind ALL FOUR engine module globals from explicit inputs
    (Phase 7: the payload-direct import seam AND the checkpoint
    resume). NEVER regenerates -- the payload is the truth
    (embed-don't-regenerate, game_file.py:17-20).

    ``game_state_dict`` goes through GameState.from_dict (lossless,
    SMOKE-17-proven). ``elapsed_at_save`` (checkpoint resume only)
    rebases the timer via the P-4 single-anchor primitive when the
    game is NOT over and elapsed is not None -- the clock continues
    from the save moment. A fresh import passes game_state from a
    fresh GameState() and elapsed None (timer from zero at GO via
    activate_game). Fail-closed: a malformed game_state_dict raises
    the from_dict error wrapped as EngineError naming the cause.
    """
    global _payload, _registry, _game, _ligand_content
    try:
        game = game_state.GameState.from_dict(game_state_dict)
    except (KeyError, TypeError, ValueError) as exc:
        raise EngineError(
            'adopt_game: invalid game-state data (%s)' % exc)
    _payload = payload
    _registry = registry
    _game = game
    _ligand_content = ligand_content or None
    if elapsed_at_save is not None and not game.game_over:
        game.rebase_timer(time.time(), elapsed_at_save)
    return game


def _slot_object(registry, slot_id, molecule_index=None):
    """The object name registered for ``slot_id`` (fail-closed).

    Slot ids are PER-MOLECULE scoped by design (generator.py:524 --
    'r0c0' repeats across the molecules of one level), so the lookup
    is molecule-aware: ``molecule_index`` resolves within THAT
    molecule's slots exactly; None keeps the Phase-2 cross-molecule
    first-match search for the legacy single-molecule call sites
    (07-10 Rule-1 record -- a first-match hit on a shadowed slot id
    silently moved the wrong molecule's AA)."""
    if molecule_index is not None:
        molecules = [registry['molecules'][molecule_index]]
    else:
        molecules = registry['molecules']
    for mol in molecules:
        entry = mol['slots'].get(slot_id)
        if entry is not None:
            return entry[0]
    raise EngineError(
        'engine.place_aa: slot %r is not in the materialized registry '
        '[%s]' % (slot_id, sorted(
            sid for m in molecules for sid in m['slots'])))


def place_aa(slot_id, position, molecule_index=None):
    """Op 3: baked placement -- the object's centroid lands on
    ``position`` (3 floats) via placement.translate_to (count- and
    pose-asserted; camera=0, world frame). Pass ``molecule_index``
    whenever the caller knows the slot's molecule (the per-molecule
    slot_id scoping law) -- the wizard's scripted move_to always
    does."""
    registry = _current_registry()
    placement.translate_to(
        _slot_object(registry, slot_id, molecule_index), position)


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


def ligand_profile_molecule(level_index, molecule_index):
    """Op 5c: the molecule's ligand chemistry profile, recomputed LIVE
    from its materialized ligand object (the 05-08 PLAY-05 hint op;
    the 02-08 deviation-3 contract shape, _ligand_data_for above).

    The engine does NOT retain the generation-time profile: ligand_data
    is a LOCAL in new_game (op 1 above), and the payload carries no
    profile (level_spec shape, fields only) -- so the PLAY-05 "could
    form" input is read back from the LIVE object. Scoping mirrors
    detect_molecule: the record list is restricted to this molecule's
    ligand object, bonds are remapped via _remap_ligand_bonds, and
    capability.ligand_profile consumes them.

    Byte-equality argument: the ligand object is loaded once at
    materialize (placement) and NEVER modified afterwards -- movement
    in play is AA-only (wizard movement model), and detect writes
    nothing. ligand_profile reads only elements/names/formal charges +
    bond orders, so the replayed profile equals the generation-time one
    -- DETECT-04 by construction: the SAME capability.ligand_profile
    the generator consumed at generation time (its _profile_of seam),
    over the SAME chemistry. Fail-closed: out-of-range molecule_index
    raises EngineError naming the index + registry count, nothing
    materialized raises via _current_registry.
    """
    registry = _current_registry()
    molecules = registry['molecules']
    index = int(molecule_index)
    if not 0 <= index < len(molecules):
        raise EngineError(
            'engine.ligand_profile_molecule: molecule_index %d out of '
            'range (registry has %d molecule(s))'
            % (index, len(molecules)))
    lig_object = molecules[index]['ligand'][0]
    records = [r for r in geometry.extract_game_atoms()
               if r['object'] == lig_object]
    lig_records, lig_bonds = _remap_ligand_bonds(records, [lig_object])
    return capability.ligand_profile(lig_records, lig_bonds)


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


def record_scored(level_index, molecule_index, required, records=None):
    """Op 9: the ONE lifecycle record site (06-03) -- Confirm AND Skip
    route through here.

    Guard FIRST (D4/Q10): a molecule that already produced a record is
    REFUSED with the pinned message -- one ``GameState.has_record``
    check covers the re-Confirm AND the skip-after-record paths, so
    the flat ``molecule_scores`` list maps onto (level, molecule)
    positions under a strict one-record-per-molecule invariant. The
    Phase-3 re-Confirm caveat (wizard.py:550-553: repeated Confirm
    appends molecule_scores; Phase 6 owns score-history lifecycle)
    closes HERE: ``score_current``/``confirm`` stay BYTE-IDENTICAL
    (smoke_04/06/07 legitimately re-score as detection probes -- the
    guard must NOT live inside them); the lifecycle's guarded front
    door is this op.

    ``records`` None -> a fresh MOLECULE-SCOPED detect pass
    (detect_molecule -- the 03-06 cross-molecule scoring guard); an
    already-computed scoped record set can be threaded through to keep
    one detect pass per press. Returns (score, formed_types) via
    score_current (the two views still record together -- they can
    never drift).
    """
    game = _current_game()
    if game.has_record(level_index, molecule_index):
        raise EngineError(
            'This molecule already has a recorded result (scored or '
            'skipped) -- use Restart to replay the game.')
    if records is None:
        records = detect_molecule(level_index, molecule_index)
    return score_current(level_index, molecule_index, required,
                         records=records)


def skip_molecule(level_index, molecule_index, required):
    """Op 10: Skip (SCORE-05 mechanics) -- record the
    detection-AT-SKIP-TIME partial score via the SAME record path as
    Confirm (the 02-10 sanctioned semantics; spec.md:44: "store only
    up to current score of the molecule"), then increment
    ``skip_count``.

    The one-record guard applies identically (record_scored refuses a
    skip-after-record with the pinned message), so Confirm and Skip
    can never disagree about whether a molecule still accepts a
    result. Returns (score, formed_types) so the wizard's skip op can
    debrief exactly like a Confirm.
    """
    value, formed = record_scored(level_index, molecule_index,
                                  required)
    _current_game().skip_count += 1
    return value, formed


def advance_molecule():
    """Op 11: the data-only within-level advance. The registry already
    holds EVERY molecule of the level (placement.materialize builds
    all of them), so NO scene work happens here; the wizard rebinds
    its own books (the research-Q1 ownership split). Deliberately NO
    range check: GameState.advance_molecule is a plain transition and
    the wizard owns the last-molecule-of-level logic."""
    _current_game().advance_molecule()


def total_score():
    """Op 12: the running total (sum of the per-molecule recorded
    scores; SCORE-01's accumulated total). EngineError before
    new_game (via _current_game)."""
    return _current_game().total_score


def _molecule_counts():
    """Per-level molecule counts in payload order (the endgame_summary
    argument; the level structure lives engine-side, not in the pure
    container). Fail-closed when no payload is live."""
    if _payload is None:
        raise EngineError(
            'engine: no payload on the engine -- call '
            'new_game/materialize first')
    return [len(level['molecules']) for level in _payload['levels']]


def advance_level():
    """Op 14: SCORE-03 level advance -- scene collapse + L+1 build +
    GameState advance, ATOMIC in fail-closed order.

    Guards FIRST: a finished game and a no-payload engine refuse
    naming the cause; advancing past the last level refuses -- the
    game should complete instead (the wizard owns that routing).
    THEN the scene work: ``placement.cleanup_game_objects`` (prefix-
    only deletion) BEFORE ``materialize(_payload, L+1)`` -- the
    retained module ``_ligand_content`` is the re-materialization
    input for uploaded games (op 1's note; demo games pass None)],
    and ``game.advance_level()`` runs LAST (pure data cannot fail, so
    a materialize failure leaves the GameState consistent -- the
    scene, not the book, is the residue). Returns the NEW registry
    (fresh ``_aam_*`` names).

    CLEANUP-ORDER HAZARD (documented residue, research pitfall
    register): cleanup deletes the objects the LIVE wizard's maps
    reference; a mid-op failure leaves a cleaned scene with a live
    wizard -- clicks no-op via the empty-pk1 path; Restart is the
    recovery.

    The TIMER ANCHOR is untouched by design: the game clock runs
    ACROSS levels (only give_up/complete_game freeze it via
    stop_timer).
    """
    game = _current_game()
    if game.game_over:
        raise EngineError('engine.advance_level: the game is over')
    if _payload is None:
        raise EngineError(
            'engine.advance_level: no payload on the engine -- call '
            'new_game/materialize first')
    nxt = game.current_level_index + 1
    if nxt >= len(_payload['levels']):
        raise EngineError(
            'engine.advance_level: no next level (%d of %d) -- the '
            'game should complete instead'
            % (nxt, len(_payload['levels'])))
    placement.cleanup_game_objects()
    registry = materialize(_payload, nxt, ligand_content=_ligand_content)
    game.advance_level()
    return registry


def give_up(now=None):
    """Op 15: Give Up (SCORE-06) -- end the game at the current stage.

    ``giveup_count`` + 1, ``end_state`` 'gave_up', ``stop_timer``
    captures + freezes the final elapsed (the anchor itself is NEVER
    touched -- it is the pause mechanism's home). The CURRENT molecule
    is NOT scored (spec.md:44-45 -- the partial-score store is Skip's
    only). Returns the 06-01 SCORE-07 summary dict (end_state,
    level_scores, total, final_time, levels, molecules,
    molecules_completed, skip_count, giveup_count, ended_level,
    ended_molecule). A second give_up (any game-over replay) refuses
    naming the cause.
    """
    game = _current_game()
    if game.game_over:
        raise EngineError('engine.give_up: the game is already over')
    game.giveup_count += 1
    game.end_state = 'gave_up'
    game.stop_timer(now)
    return endgame_summary()


def complete_game(now=None):
    """Op 16: natural completion -- the twin of give_up without the
    counter: ``end_state`` 'completed', ``stop_timer`` freeze, then
    the same SCORE-07 summary dict. The 06-01 fail-closed record law
    applies (a 'completed' game must have EVERY molecule recorded, so
    this op is the last-molecule-Confirm path's ending, never an early
    exit). Refuses when the game is already over, same message class
    as give_up.
    """
    game = _current_game()
    if game.game_over:
        raise EngineError(
            'engine.complete_game: the game is already over')
    game.end_state = 'completed'
    game.stop_timer(now)
    return endgame_summary()


def endgame_summary():
    """Op 17: the SCORE-07 endgame READ op (06-03) -- the 06-01
    contract dict from the live game, returned as plain data through
    the op. READ-ONLY: give_up/complete_game mutate (counter, end
    state, freeze) and then delegate HERE, so a read can never change
    the game. Exact keys per the 06-01 contract: end_state,
    level_scores, total, final_time, levels, molecules,
    molecules_completed, skip_count, giveup_count, ended_level,
    ended_molecule.
    """
    return _current_game().endgame_summary(_molecule_counts())


def is_over():
    """Op 13: whether the game has ended (give_up/complete_game set
    the flag via stop_timer). A cheap bool gate for wizard/tab
    handlers; EngineError before new_game (via _current_game)."""
    return _current_game().game_over


def game_status():
    """Read-only plain-data snapshot of the live GameState (no
    mutation). Returns GameState.to_dict(): current_level_index,
    current_molecule_index, molecule_scores, skip_count, giveup_count,
    timer_anchor, formed_types_per_molecule, score_per_molecule,
    game_over, end_state, final_time. Raises EngineError when no
    game is live."""
    return _current_game().to_dict()
