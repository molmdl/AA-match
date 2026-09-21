"""aamatch.checkpoint -- the checkpoint sidecar schema + .aamz zip I/O (07-02).

Layer: PURE (builds on persistence / game_file / game_state; imports
stdlib json/os/tempfile/zipfile + those pure siblings ONLY -- zipfile is
whitelisted in tests/test_purity.py ALLOWED_STDLIB for exactly this
module). No pymol/Qt/numpy anywhere, module level or function body, so
the module unit-tests in WSL with bare python3.6 and zero stubs.

The checkpoint is the THIRD versioned artifact -- the two-gates-law
extension story: container ``version`` (refuse-newer / accept-older,
persistence.FORMAT_VERSION) and the embedded spec's ``detector_version``
(exact match, level_spec.DETECTOR_VERSION) stay exactly two; the
checkpoint adds ONE new refuse-newer schema gate of its OWN,
``checkpoint_format_version`` (CHECKPOINT_VERSION below), never
conflated with either. The container kind 'checkpoint' was reserved in
persistence.py:37 from Phase 1.

The shipped artifact is ONE zip (``.aamz``) with two fixed members:
``game.pse`` (the session bytes, the pose/display/camera store) and
``state.json`` (the sidecar: the FULL versioned container JSON, so
check_container gate 1 applies on read). Design: 07-RESEARCH-state.md
S2 (sidecar schema) / S4 (sentinel-first reconstruction) / S5
(version-gate chain) / S7 (zip layout).

The sidecar data dict:

    {
      'checkpoint_format_version': CHECKPOINT_VERSION,  # schema gate
      'created_at': <str>,                              # provenance
      'generator': 'AA-match',                          # provenance
      'game': <game_file.make_game_data output>,        # VERBATIM: the
          # FULL game file (setup/seed/level_spec=THE PAYLOAD/ligand_files)
          # -- embed-don't-regenerate law: the payload is THE TRUTH,
          # never regenerated, never reduced.
      'candidates': None | [rows],                      # _last_start replay
          # input (uploaded games; demo = None), additive.
      'game_state': <GameState.to_dict()>,              # VERBATIM --
          # the 02-10 wrap-don't-reshape law: never reshape to_dict.
      'elapsed_at_save': float | None,                  # re-anchor
          # authority: restore rebase_timer(now, elapsed). Caller clamps
          # >= 0 at capture; parse refuse-negatives (rewind-the-clock).
      'registry': {                                     # CURRENT LEVEL ONLY
         'level_index': int,                            #  (placement.py:
         'molecules': [{...ligand: [name, [ids]],       #  64-66 -- only
                      slots: {slot_id: [name, [ids]]}}] #   one level ever
      },                                                #   materialized;
      'wizard': {...} | None,                           #   pre_game_names
    }                                                   #   dropped (zero
                                                        #   consumers);
                                                        #   wizard repair
                                                        #   block, additive.

Parse gate chain (parse_checkpoint_data; four gates IN ORDER, every
refusal a FormatError BEFORE any caller scene mutation):

1. persistence.check_container(container, 'checkpoint') -- foreign
   magic / newer container header / misfiled kind refused for free.
2. checkpoint_format_version gate: refuse-newer / accept-older (missing,
   non-int, or bool refused; older accepted with .get defaults --
   additive-only evolution).
3. The embedded 'game' block replays game_file.parse_game_data VERBATIM
   (wrap: make_container('game', data['game'])): the FULL five-gate
   chain with ZERO new version logic -- the detector_version EXACT-match
   gate applies to checkpoints (a stale detector makes the embedded spec
   unsolvable, not merely incomplete).
4. GameState light validator (_validate_game_state): required base keys
   (from_dict's seven direct indexes would bare-KeyError otherwise),
   the one-record-per-molecule invariant
   (len(molecule_scores) == len(score_per_molecule)),
   L<i>M<j> keys within the embedded payload's level/molecule bounds,
   int (non-bool) skip/give-up counters, elapsed_at_save >= 0 or None
   (a negative would push the timer anchor into the future and rewind
   the clock -- rebase_timer's own fail-closed rule, applied here so the
   refusal fires at parse, not at restore).

Registry/wizard/candidates blocks are additive .get reads; registry
'level_index' must equal game_state 'current_level_index' (consistency),
and a present wizard block must be a dict.
"""

import json
import os
import tempfile
import zipfile

from . import game_file
from .persistence import FormatError, check_container, make_container

CHECKPOINT_VERSION = 1        # schema gate: refuse-newer / accept-older
PSE_MEMBER = 'game.pse'
SIDECAR_MEMBER = 'state.json'


def build_checkpoint_data(game_data, game_state, elapsed_at_save, registry,
                          wizard_books=None, candidates=None, created_at=''):
    """Build the ``data`` dict of a checkpoint container (S2 schema).

    ``game_data`` is the FULL game_file.make_game_data output, embedded
    VERBATIM (setup/seed/level_spec=THE PAYLOAD/ligand_files -- the
    embed-don't-regenerate law). ``game_state`` is GameState.to_dict()
    output, embedded VERBATIM (the 02-10 wrap-don't-reshape law).
    ``elapsed_at_save`` is float or None -- the re-anchor authority; the
    CALLER clamps ``max(0.0, now - timer_anchor)`` at capture, and parse
    refuses negatives. ``registry`` is the CURRENT-LEVEL materialize
    registry; tuples are converted to JSON lists and ``pre_game_names``
    is dropped (zero functional consumers -- grep-verified; rebuilt as
    [] on restore). ``wizard_books`` embeds verbatim (repair block for
    the rebuild path); ``candidates`` passes through (None for demo
    games, uploads carry their rows -- the Restart-after-load replay
    input).
    """
    return {
        'checkpoint_format_version': CHECKPOINT_VERSION,
        'created_at': created_at,
        'generator': 'AA-match',
        'game': game_data,
        'candidates': candidates,
        'game_state': game_state,
        'elapsed_at_save': elapsed_at_save,
        'registry': _registry_to_json(registry),
        'wizard': wizard_books,
    }


def parse_checkpoint_data(container):
    """Validate a checkpoint container; return its parsed components.

    Runs the four-gate chain in the module docstring IN ORDER; every
    refusal is a FormatError naming the cause, raised BEFORE any caller
    scene mutation. Returns::

        {'setup': <validate_state output>,
         'payload': <the embedded level-spec payload, passthrough>,
         'ligand_texts': {file_key: decoded record text},
         'game_state': <to_dict output, verbatim (never reshaped)>,
         'elapsed_at_save': float | None,
         'registry': <sidecar registry block> | None,
         'wizard': <sidecar wizard block> | None,
         'candidates': <replay rows> | None}
    """
    container = check_container(container, 'checkpoint')       # gate 1
    data = container.get('data')
    if not isinstance(data, dict):
        data = {}

    # Gate 2: checkpoint_format_version -- refuse-newer / accept-older.
    version = data.get('checkpoint_format_version')
    if not isinstance(version, int) or isinstance(version, bool):
        raise FormatError(
            "checkpoint data is missing or has an invalid "
            "'checkpoint_format_version'")
    if version > CHECKPOINT_VERSION:
        raise FormatError(
            'unsupported checkpoint format version %d (expected <= %d). '
            'Please update AA-match.' % (version, CHECKPOINT_VERSION))

    # Gate 3: the embedded 'game' block replays parse_game_data
    # VERBATIM -- container check + game_format_version + validate_state
    # + the full parse_level_spec_dict chain incl. the exact-match
    # detector_version gate (zero new version logic).
    if 'game' not in data:
        raise FormatError("checkpoint data is missing 'game'")
    parsed = game_file.parse_game_data(make_container('game', data['game']))

    # Gate 4: the GameState light validator.
    if 'game_state' not in data:
        raise FormatError("checkpoint data is missing 'game_state'")
    game_state = data['game_state']
    _validate_game_state(game_state, parsed['payload'])
    elapsed = _validate_elapsed(data.get('elapsed_at_save'))

    # Gate 5: additive blocks + consistency refusals.
    registry = data.get('registry')
    if registry is not None:
        level_index = registry.get('level_index') \
            if isinstance(registry, dict) else None
        current = game_state['current_level_index']
        if level_index != current:
            raise FormatError(
                "checkpoint registry 'level_index' %r does not match "
                "game_state 'current_level_index' %r"
                % (level_index, current))
    wizard = data.get('wizard')
    if wizard is not None and not isinstance(wizard, dict):
        raise FormatError(
            "checkpoint 'wizard' block must be a dict, found %s"
            % type(wizard).__name__)

    return {'setup': parsed['setup'],
            'payload': parsed['payload'],
            'ligand_texts': parsed['ligand_texts'],
            'game_state': game_state,
            'elapsed_at_save': elapsed,
            'registry': registry,
            'wizard': wizard,
            'candidates': data.get('candidates')}


def reconcile_registry(sidecar_registry, observed, payload, level_index):
    """Sentinel-first registry reconciliation (S4).

    ``sidecar_registry`` is the sidecar's ``registry`` block (JSON form:
    tuples ride as lists). ``observed`` is the caller's sweep of the
    loaded scene, {object_name: sorted atom ids}. ``payload`` is the
    embedded level-spec payload; ``level_index`` the level the game is
    on (== game_state['current_level_index']).

    Returns (rebuilt_registry, report) where rebuilt_registry matches
    the placement.materialize shape EXACTLY (lists back to TUPLES --
    (name, ids_tuple) for ligand/slots, pre_game_names rebuilt as [])::

        {'level_index': int, 'pre_game_names': [],
         'molecules': [{'molecule_id', 'offset', 'ligand': (name, ids),
                        'slots': {slot_id: (name, ids)}}]}

    Match rule (the (object, sorted ids) identity contract,
    placement.py:51-53 -- SMOKE-17 proved ids stable 360/360): a
    sidecar entry is KEPT iff ``object`` is in ``observed`` AND
    ``sorted(observed[object]) == ids``.

    THE NEVER-GHOST-ENTRY LAW: a non-verifying entry is DROPPED, never
    registered (a registry entry must never reference a non-existent
    atom; v1 registry.py missing_from_pse semantics). Dropped entries
    land in ``report['dropped']`` (one dict per drop: molecule/slot/
    object/reason); observed objects with NO sidecar entry land in
    ``report['missing_from_sidecar']`` (sorted) -- real, clickable atoms
    with no slot identity, reported never fatal.

    COMPLETENESS GATE: the CURRENT level must reconcile completely --
    expected shape derived pure from
    ``payload['levels'][level_index]['molecules']`` (molecule ids +
    every slot id); every molecule's ligand and ALL slots must be kept,
    else FormatError naming the first missing piece. Future levels need
    NOTHING: only one level is ever materialized (placement.py:64-66)
    and level advance re-materializes from the payload.
    """
    if not isinstance(sidecar_registry, dict):
        sidecar_registry = {}
    observed = observed or {}
    rebuilt = {'level_index': int(level_index),
               'pre_game_names': [],
               'molecules': []}
    report = {'dropped': [], 'missing_from_sidecar': []}
    claimed = set()

    kept = {}                    # molecule_id -> rebuilt molecule row
    for row in sidecar_registry.get('molecules') or []:
        molecule_id = row.get('molecule_id')
        out = {'molecule_id': molecule_id,
               'offset': tuple(row.get('offset') or (0.0, 0.0, 0.0)),
               'ligand': None,
               'slots': {}}
        ligand = row.get('ligand')
        if _entry_ok(ligand, observed):
            out['ligand'] = (ligand[0], tuple(sorted(
                int(i) for i in ligand[1])))
            claimed.add(ligand[0])
        elif ligand is not None:
            report['dropped'].append(
                _drop(molecule_id, 'ligand', ligand, observed))
        for slot_id in sorted(row.get('slots') or {}):
            entry = row['slots'][slot_id]
            if _entry_ok(entry, observed):
                out['slots'][slot_id] = (entry[0], tuple(sorted(
                    int(i) for i in entry[1])))
                claimed.add(entry[0])
            else:
                report['dropped'].append(
                    _drop(molecule_id, slot_id, entry, observed))
        rebuilt['molecules'].append(out)
        kept[molecule_id] = out

    for name in sorted(observed):
        if name not in claimed:
            report['missing_from_sidecar'].append(name)

    # COMPLETENESS GATE: the expected shape comes from the PAYLOAD (the
    # one level ever materialized), never from the sidecar.
    level = (payload.get('levels') or [])[level_index]
    expected = {}                # molecule_id -> {'ligand': entry-or-None, slots: set}
    for row in sidecar_registry.get('molecules') or []:
        expected[row.get('molecule_id')] = row
    for molecule in level.get('molecules') or []:
        molecule_id = molecule.get('molecule_id')
        sidecar_row = expected.get(molecule_id) or {}
        out = kept.get(molecule_id)
        if out is None or out['ligand'] is None:
            ligand = sidecar_row.get('ligand')
            raise FormatError(_missing_piece(
                ligand[0] if ligand is not None else None,
                molecule_id, 'ligand'))
        slot_ids = [slot['slot_id'] for slot in
                    ((molecule.get('grid') or {}).get('slots') or [])]
        sidecar_slots = sidecar_row.get('slots') or {}
        for slot_id in slot_ids:
            if out is None or slot_id not in out['slots']:
                entry = sidecar_slots.get(slot_id)
                raise FormatError(_missing_piece(
                    entry[0] if entry is not None else None,
                    molecule_id, slot_id))
    return rebuilt, report


def write_checkpoint_zip(zip_path, data, tmp_pse_path):
    """Write the .aamz checkpoint archive atomically (S7).

    The sidecar member is the FULL container JSON (magic/kind=
    'checkpoint'/version/data) serialized with the write_json_atomic
    discipline (sort_keys, indent=2, allow_nan=False -- byte-stable,
    loud NaN refusal ), so check_container gate 1 applies on read. The
    zip itself is minted inside the TARGET directory via
    tempfile.mkstemp and committed with os.replace (the persistence
    temp+replace atomic-write pattern); on ANY failure the temp zip is
    removed (best-effort) and the target is left untouched.
    """
    sidecar = json.dumps(make_container('checkpoint', data),
                         indent=2, sort_keys=True,
                         allow_nan=False).encode('utf-8')
    dir_name = os.path.dirname(os.path.abspath(zip_path)) or '.'
    fd, tmp = tempfile.mkstemp(dir=dir_name, prefix='.aam_',
                               suffix='.tmp')
    os.close(fd)
    try:
        with zipfile.ZipFile(tmp, 'w', zipfile.ZIP_DEFLATED) as zf:
            zf.write(tmp_pse_path, arcname=PSE_MEMBER)
            zf.writestr(SIDECAR_MEMBER, sidecar)
        os.replace(tmp, zip_path)
    except BaseException:
        try:
            os.remove(tmp)
        except OSError:
            pass
        raise


def read_checkpoint_zip(zip_path):
    """Read an .aamz checkpoint archive -> (tmp_pse_path, parsed_data).

    Refusal-first order (the v1 read_bcmz pattern: parse gates precede
    extraction): open as zip (corrupt -> FormatError, NEVER a bare
    BadZipFile), namelist gate (missing state.json / game.pse), then
    parse the sidecar through parse_checkpoint_data -- every gate
    refused BEFORE extraction hands off. The sidecar member is the FULL
    container JSON, so check_container gate 1 applies here. On success
    game.pse is extracted into a tempfile.mkdtemp dir and
    (extracted_path, parsed_data) returned; the CALLER owns the rmtree.
    """
    try:
        zf = zipfile.ZipFile(zip_path, 'r')
    except zipfile.BadZipFile as exc:
        raise FormatError(
            'not an AA-match archive (unreadable zip: %s)' % exc)
    with zf:
        names = set(zf.namelist())
        if SIDECAR_MEMBER not in names:
            raise FormatError('not an AA-match archive (missing %s)'
                              % SIDECAR_MEMBER)
        if PSE_MEMBER not in names:
            raise FormatError('archive missing %s (cannot reconstruct)'
                              % PSE_MEMBER)
        try:
            sidecar = zf.read(SIDECAR_MEMBER)
        except (zipfile.BadZipFile, RuntimeError) as exc:
            raise FormatError(
                'not an AA-match archive (unreadable zip: %s)' % exc)
        try:
            container = json.loads(sidecar)
        except ValueError as exc:
            raise FormatError('could not parse AA-match JSON: %s' % exc)
        data = parse_checkpoint_data(container)      # ALL gates first
        try:
            pse_bytes = zf.read(PSE_MEMBER)
        except (zipfile.BadZipFile, RuntimeError) as exc:
            raise FormatError(
                'not an AA-match archive (unreadable zip: %s)' % exc)
    tmp_dir = tempfile.mkdtemp(prefix='aamatch_checkpoint_')
    pse_path = os.path.join(tmp_dir, PSE_MEMBER)
    with open(pse_path, 'wb') as handle:
        handle.write(pse_bytes)
    return pse_path, data


# ---------------------------------------------------------------------------
# Internals
# ---------------------------------------------------------------------------

_GAME_STATE_BASE_KEYS = (
    'current_level_index', 'current_molecule_index', 'molecule_scores',
    'skip_count', 'giveup_count', 'timer_anchor',
    'formed_types_per_molecule')


def _registry_to_json(registry):
    """materialize registry -> JSON sidecar block for the CURRENT level.

    Tuples become lists (JSON has no tuples); ``pre_game_names`` is
    dropped (zero functional consumers -- grep-verified; rebuilt as []
    on restore). ``level_index`` is coerced to a plain int.
    """
    molecules = []
    for row in registry['molecules']:
        ligand = row['ligand']
        slots = {}
        for slot_id, entry in row['slots'].items():
            slots[slot_id] = [entry[0], [int(i) for i in entry[1]]]
        molecules.append({
            'molecule_id': row['molecule_id'],
            'offset': [float(x) for x in row['offset']],
            'ligand': [ligand[0], [int(i) for i in ligand[1]]],
            'slots': slots,
        })
    return {'level_index': int(registry['level_index']),
            'molecules': molecules}


def _validate_game_state(game_state, payload):
    """The gate-4 GameState light validator (fail-closed, key-naming).

    from_dict's seven direct data['...'] indexes must exist (bare
    KeyError otherwise); the one-record-per-molecule invariant
    (game_state.py:284-302) must hold; every L<i>M<j> container key must
    sit inside the embedded payload's level/molecule bounds; skip/give-
    up counters must be real ints (bools are not counts).
    """
    if not isinstance(game_state, dict):
        raise FormatError('checkpoint \'game_state\' must be a dict, '
                          'found %s' % type(game_state).__name__)
    for key in _GAME_STATE_BASE_KEYS:
        if key not in game_state:
            raise FormatError(
                "checkpoint data is missing 'game_state.%s'" % key)
    scores = game_state['molecule_scores']
    score_map = game_state.get('score_per_molecule') or {}
    if len(scores) != len(score_map):
        raise FormatError(
            'checkpoint game_state breaks the one-record-per-molecule '
            'invariant (len(molecule_scores)=%d != '
            'len(score_per_molecule)=%d)'
            % (len(scores), len(score_map)))
    levels = payload.get('levels') or []
    keys = list(score_map) + \
        list(game_state.get('formed_types_per_molecule') or {})
    for key in keys:
        _check_molecule_key_bounds(key, levels)
    for counter in ('skip_count', 'giveup_count'):
        value = game_state[counter]
        if not isinstance(value, int) or isinstance(value, bool):
            raise FormatError(
                "checkpoint game_state '%s' must be an int, found %r"
                % (counter, value))


def _check_molecule_key_bounds(key, levels):
    """One L<i>M<j> key against the embedded payload's bounds."""
    level = molecule = None
    try:
        if isinstance(key, str) and key.startswith('L') and 'M' in key:
            left, right = key[1:].split('M', 1)
            level, molecule = int(left), int(right)
    except (TypeError, ValueError):
        level = molecule = None
    in_bounds = (level is not None and 0 <= level < len(levels)
                 and molecule is not None
                 and 0 <= molecule < len(
                     (levels[level].get('molecules') or [])))
    if not in_bounds:
        raise FormatError(
            "checkpoint game_state key %r is outside the embedded "
            "payload's level/molecule bounds" % (key,))


def _validate_elapsed(value):
    """elapsed_at_save: None allowed; else a non-negative number (the
    re-anchor authority -- a negative would rewind the clock)."""
    if value is None:
        return None
    if isinstance(value, bool) \
            or not isinstance(value, (int, float)) or value < 0:
        raise FormatError(
            "checkpoint 'elapsed_at_save' must be a non-negative float "
            "or null, found %r (a negative would push the timer anchor "
            "into the future and rewind the clock)" % (value,))
    return float(value)


def _entry_ok(entry, observed):
    """The (object, sorted ids) identity contract: kept iff the object
    is in the observed scene sweep AND the sorted ids match exactly."""
    if not isinstance(entry, (list, tuple)) or len(entry) < 2:
        return False
    name, ids = entry[0], list(entry[1])
    return name in observed and sorted(observed[name]) == sorted(
        [int(i) for i in ids])


def _drop(molecule_id, slot, entry, observed):
    """The never-ghost-entry report row for one non-verifying entry."""
    name, ids = entry[0], [int(i) for i in entry[1]]
    if name in observed:
        scene_ids = sorted(int(i) for i in observed[name])
        reason = 'scene atom ids %s do not match the sidecar ids %s' \
            % (scene_ids, sorted(_as_int_list(ids)))
    else:
        reason = 'object absent from scene'
    return {'molecule': molecule_id, 'slot': slot,
            'object': name, 'reason': reason}


def _as_int_list(ids):
    return [int(i) for i in ids]


def _missing_piece(obj_name, molecule_id, slot):
    """The completeness-gate message: names the first missing piece
    (object %r -- None when even the sidecar row is gone -- molecule +
    slot) and the cause (the saved session no longer matches)."""
    return ("checkpoint scene is missing game object %r (molecule %r, "
            "slot %r) -- the saved session no longer matches this "
            "checkpoint" % (obj_name, molecule_id, slot))
