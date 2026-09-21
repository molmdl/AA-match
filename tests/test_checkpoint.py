"""Unit tests for aamatch.checkpoint -- the checkpoint sidecar module (07-02).

The checkpoint is the THIRD versioned artifact (kind='checkpoint', already
reserved in persistence.KINDS): one .aamz zip carrying game.pse plus a
state.json sidecar whose data dict embeds the FULL game-file data VERBATIM
(embed-don't-regenerate), the GameState.to_dict VERBATIM (wrap-don't-
reshape), the elapsed_at_save re-anchor authority, a JSON-converted
current-level registry (never-ghost-entry reconciliation input), and the
additive wizard repair block. Design: 07-RESEARCH-state.md S2/S4/S5/S7.

Gate chain under test (all refusals FormatError with pinned messages):
1. persistence.check_container(container, 'checkpoint') -- foreign magic /
   newer container header / misfiled kind come for free.
2. checkpoint_format_version: refuse-newer / accept-older (missing or
   non-int refused; 0 accepted as the positive control for accept-older).
3. The embedded 'game' block replays game_file.parse_game_data VERBATIM
   (wrapped via persistence.make_container('game', data['game'])) -- the
   exact-match detector_version gate applies to checkpoints with ZERO new
   version logic.
4. GameState light validator: required base keys, the one-record-per-
   molecule invariant, L<i>M<j> keys inside the embedded payload bounds,
   int skip/give-up counters, non-negative elapsed_at_save (None allowed),
   registry level_index consistency, wizard-must-be-a-dict.

TDD: this file lands BEFORE aamatch/checkpoint.py (RED); the payload-
fixture recipe is copied from tests/test_game_file.py's builders (the
house fixture-copy pattern).

Runs under bare python3.6, stdlib only, zero stubs.
"""

import copy
import json
import os
import shutil
import tempfile
import unittest
import zipfile

from aamatch import checkpoint, game_file, generator
from aamatch.checkpoint import (
    CHECKPOINT_VERSION,
    PSE_MEMBER,
    SIDECAR_MEMBER,
    build_checkpoint_data,
    parse_checkpoint_data,
    read_checkpoint_zip,
    reconcile_registry,
    write_checkpoint_zip,
)
from aamatch.game_state import GameState
from aamatch.persistence import FormatError, make_container
from aamatch.setup_state import INTERACTION_TYPES, validate_state


# ---------------------------------------------------------------------------
# Fixtures -- copied from tests/test_game_file.py's payload builders.
# ---------------------------------------------------------------------------

SET_ID = 'demo-dev-1'


def _rich_profile():
    """Hand-built capability.ligand_profile shape: every feature on, so
    all 7 interaction types are supportable (test_generator.py RICH)."""
    return {
        'has_donor': True,
        'has_acceptor': True,
        'charge_signs': {'+', '-'},      # a SET (input-side only)
        'ring_count': 2,
        'has_hydrophobe': True,
        'has_halogen_donor': True,
        'has_metal': True,
    }


def _candidate(entry_id, size_class='small', **over):
    """One manifest-shaped candidate row (enumerate_entries shape)."""
    heavy = {'small': 9, 'medium': 40, 'large': 80}[size_class]
    row = {
        'set_id': SET_ID,
        'entry_id': entry_id,
        'file': 'ligands/%s.sdf' % entry_id,
        'format': 'sdf',
        'sha256': 'a' * 64,
        'protonation': 'as-recorded',
        'atom_count': heavy + 7,
        'heavy_atom_count': heavy,
        'bond_count': heavy + 7,
        'bond_order_counts': {'1': 12, '2': 4},
        'formal_charge_sum': 0,
        'states_expected': 1,
        'metal_present': False,
        'halogen_present': False,
        'size_class': size_class,
    }
    row.update(over)
    return row


RICH = _rich_profile()

CANDIDATES = sorted([
    _candidate('acetate'),
    _candidate('benzamide'),
    _candidate('toluene'),
], key=lambda c: (c['set_id'], c['entry_id']))

LIGAND_DATA = dict(
    ((c['set_id'], c['entry_id']),
     {'centroid': (0.0, 0.0, 0.0), 'radius': 4.0, 'profile': RICH})
    for c in CANDIDATES)

PSE_FIXTURE_BYTES = b'PSE-session-bytes-fixture: stands in for .pse data\n'


def make_setup(molecules=1, difficulty=2):
    """A validated setup_state dict (the generator's real input shape)."""
    return validate_state({
        'interaction_mode': 'unset',
        'allowed_interactions': list(INTERACTION_TYPES),
        'molecules_per_level': molecules,
        'difficulty_levels': difficulty,
    })


def make_payload(seed=42, molecules=1, difficulty=2):
    """(setup, payload): a REAL generator.generate payload for tests."""
    setup = make_setup(molecules, difficulty)
    payload = generator.generate(
        seed, setup, CANDIDATES, LIGAND_DATA, difficulty)
    return setup, payload


def make_registry(payload, level_index=0):
    """A materialize-shaped registry for `level_index`, slot ids derived
    FROM the payload (identity = (object, sorted ids); tuples, as
    placement.materialize returns them)."""
    level = payload['levels'][level_index]
    molecules = []
    for mi, molecule in enumerate(level['molecules']):
        molecule_id = molecule['molecule_id']
        slots = {}
        for si, slot in enumerate(molecule['grid']['slots']):
            slot_id = slot['slot_id']
            slots[slot_id] = (
                '_aam_aa_%s_%d' % (slot_id, mi),
                (10 + 10 * si, 11 + 10 * si, 12 + 10 * si))
        molecules.append({
            'molecule_id': molecule_id,
            'offset': (0.0, 0.0, 0.0),
            'ligand': ('_aam_lig_%s' % molecule_id, (1, 2, 3, 4)),
            'slots': slots,
        })
    return {'level_index': level_index,
            'pre_game_names': ['user_obj'],
            'molecules': molecules}


def observed_for(registry):
    """The sentinel-first sweep of a registry that verifies EXACTLY:
    {object_name: sorted ids} for every registry object."""
    observed = {}
    for molecule in registry['molecules']:
        name, ids = molecule['ligand']
        observed[name] = sorted(ids)
        for slot_id, (name, ids) in molecule['slots'].items():
            observed[name] = sorted(ids)
    return observed


WIZARD_BOOKS = {'current_slot': None, 'color_store': {},
                'event_seq': 0, 'last_event': None, 'error': None,
                'saved_msm': 1}


def make_valid_data(wizard_books=None, candidates=None,
                    created_at='2026-09-21T00:00:00',
                    elapsed=12.5):
    """(container, data, setup, payload, registry, game_state_dict) for a
    well-formed checkpoint container."""
    setup, payload = make_payload()
    game_data = game_file.make_game_data(setup, payload)
    registry = make_registry(payload, 0)
    gs = GameState()
    gs_dict = gs.to_dict()
    data = build_checkpoint_data(
        game_data, gs_dict, elapsed, registry,
        wizard_books=WIZARD_BOOKS if wizard_books is None else wizard_books,
        candidates=candidates, created_at=created_at)
    return make_container('checkpoint', data), data, setup, payload, \
        registry, gs_dict


def _editor(container):
    """(edit_fn) -> container with edit_fn applied to a deep-copied data
    dict (the test_game_file mutation pattern, deep-copied because the
    game block embeds the shared fixture payload)."""
    def edit(edit_fn):
        mutated = copy.deepcopy(container)
        edit_fn(mutated['data'])
        return mutated
    return edit


class TestBuildShape(unittest.TestCase):
    """build_checkpoint_data: exact key set, stamps, verbatim embeds,
    JSON-converted registry (tuples -> lists, pre_game_names dropped)."""

    def test_key_set_and_constants(self):
        _, data, setup, payload, registry, gs_dict = make_valid_data()
        self.assertEqual(
            sorted(data),
            ['candidates', 'checkpoint_format_version', 'created_at',
             'elapsed_at_save', 'game', 'game_state', 'generator',
             'registry', 'wizard'])
        self.assertEqual(data['checkpoint_format_version'],
                         CHECKPOINT_VERSION)
        self.assertEqual(CHECKPOINT_VERSION, 1)
        self.assertEqual(PSE_MEMBER, 'game.pse')
        self.assertEqual(SIDECAR_MEMBER, 'state.json')
        self.assertEqual(data['generator'], 'AA-match')
        self.assertEqual(data['created_at'], '2026-09-21T00:00:00')
        self.assertEqual(data['elapsed_at_save'], 12.5)
        # THE mirroring ban: detector_version lives ONLY inside the
        # embedded spec -- never at the checkpoint layer.
        self.assertNotIn('detector_version', data)

    def test_embeds_verbatim(self):
        _, data, setup, payload, registry, gs_dict = make_valid_data()
        # Embed-don't-regenerate: the game block IS the make_game_data
        # output (level_spec == the payload).
        self.assertEqual(data['game']['level_spec'], payload)
        # Wrap-don't-reshape: the game_state block carries the to_dict
        # output key-for-key, never reshaped.
        self.assertEqual(sorted(data['game_state']), sorted(gs_dict))
        self.assertIsNone(data['candidates'])

    def test_registry_tuples_become_json_lists_and_pre_game_dropped(self):
        _, data, setup, payload, registry, gs_dict = make_valid_data()
        sidecar = data['registry']
        self.assertEqual(sorted(sidecar), ['level_index', 'molecules'])
        self.assertNotIn('pre_game_names', sidecar)
        self.assertEqual(sidecar['level_index'], 0)
        molecule = sidecar['molecules'][0]
        ligand = molecule['ligand']
        self.assertEqual(ligand, ['_aam_lig_%s' % molecule_id(payload), [1, 2, 3, 4]])
        self.assertIsInstance(ligand[0], str)
        self.assertIsInstance(ligand[1], list)
        for slot_id, entry in molecule['slots'].items():
            self.assertIsInstance(entry[0], str)
            self.assertIsInstance(entry[1], list)
            for atom_id in entry[1]:
                self.assertIsInstance(atom_id, int)
        self.assertEqual(len(molecule['slots']),
                         len(payload['levels'][0]['molecules'][0]
                             ['grid']['slots']))

    def test_candidates_passthrough(self):
        rows = [CANDIDATES[0]]
        _, data, *_ = make_valid_data(candidates=rows)
        self.assertEqual(data['candidates'], rows)


def molecule_id(payload, level_index=0, molecule_index=0):
    return payload['levels'][level_index]['molecules'][molecule_index][
        'molecule_id']


class TestRoundTrip(unittest.TestCase):
    """build -> container -> (JSON bytes) -> parse: every block
    round-trips; the embedded payload comes back IDENTICAL."""

    def test_round_trip(self):
        container, data, setup, payload, registry, gs_dict = (
            make_valid_data())
        reloaded = json.loads(json.dumps(container, sort_keys=True))
        parsed = parse_checkpoint_data(reloaded)
        self.assertEqual(
            sorted(parsed),
            ['candidates', 'elapsed_at_save', 'game_state',
             'ligand_texts', 'payload', 'registry', 'setup', 'wizard'])
        self.assertEqual(parsed['setup'], validate_state(setup))
        self.assertEqual(parsed['payload'], payload)
        self.assertEqual(
            json.dumps(parsed['payload'], sort_keys=True),
            json.dumps(payload, sort_keys=True))
        jsonl = json.loads(json.dumps(gs_dict, sort_keys=True))
        self.assertEqual(parsed['game_state'], jsonl)
        self.assertEqual(parsed['elapsed_at_save'], 12.5)
        self.assertEqual(parsed['registry'], data['registry'])
        self.assertEqual(parsed['wizard'], WIZARD_BOOKS)
        self.assertIsNone(parsed['candidates'])
        self.assertEqual(parsed['ligand_texts'], {})

    def test_game_state_from_dict_lossless_after_parse(self):
        container, data, setup, payload, registry, gs_dict = (
            make_valid_data())
        parsed = parse_checkpoint_data(container)
        rebuilt = GameState.from_dict(parsed['game_state'])
        self.assertEqual(rebuilt.to_dict(), gs_dict)


class TestParseGate1ContainerHeader(unittest.TestCase):
    """Gate 1: check_container(container, 'checkpoint') for free."""

    def test_foreign_magic_refused(self):
        container = make_valid_data()[0]
        bad = dict(container)
        bad['magic'] = 'NOTAAM'
        with self.assertRaises(FormatError) as ctx:
            parse_checkpoint_data(bad)
        self.assertIn('not an AA-match file', str(ctx.exception))

    def test_misfiled_kind_refused(self):
        _, data, *_ = make_valid_data()
        bad = make_container('game', data)
        with self.assertRaises(FormatError) as ctx:
            parse_checkpoint_data(bad)
        self.assertEqual(
            "expected an AA-match checkpoint file, found kind='game'",
            str(ctx.exception))


class TestParseGate2CheckpointFormatVersion(unittest.TestCase):
    """Gate 2: checkpoint_format_version refuse-newer / accept-older."""

    def test_missing_refused(self):
        edit = _editor(make_valid_data()[0])
        container = edit(lambda d: d.pop('checkpoint_format_version'))
        with self.assertRaises(FormatError) as ctx:
            parse_checkpoint_data(container)
        self.assertEqual(
            "checkpoint data is missing or has an invalid "
            "'checkpoint_format_version'", str(ctx.exception))

    def test_non_int_refused(self):
        edit = _editor(make_valid_data()[0])
        container = edit(lambda d: d.update(checkpoint_format_version='x'))
        with self.assertRaises(FormatError) as ctx:
            parse_checkpoint_data(container)
        self.assertEqual(
            "checkpoint data is missing or has an invalid "
            "'checkpoint_format_version'", str(ctx.exception))

    def test_bool_refused(self):
        edit = _editor(make_valid_data()[0])
        container = edit(lambda d: d.update(checkpoint_format_version=True))
        with self.assertRaises(FormatError) as ctx:
            parse_checkpoint_data(container)
        self.assertEqual(
            "checkpoint data is missing or has an invalid "
            "'checkpoint_format_version'", str(ctx.exception))

    def test_newer_refused_with_exact_message(self):
        edit = _editor(make_valid_data()[0])
        container = edit(lambda d: d.update(checkpoint_format_version=2))
        with self.assertRaises(FormatError) as ctx:
            parse_checkpoint_data(container)
        self.assertEqual(
            'unsupported checkpoint format version 2 (expected <= 1). '
            'Please update AA-match.', str(ctx.exception))

    def test_older_accepted(self):
        # Positive control for accept-older (additive-only evolution).
        edit = _editor(make_valid_data()[0])
        container = edit(lambda d: d.update(checkpoint_format_version=0))
        parsed = parse_checkpoint_data(container)
        self.assertIn('payload', parsed)


class TestParseGate3EmbeddedGameReplay(unittest.TestCase):
    """Gate 3: the 'game' block replays parse_game_data VERBATIM -- the
    five-gate chain incl. the detector exact-match gate, zero new code."""

    def test_missing_game_refused(self):
        edit = _editor(make_valid_data()[0])
        container = edit(lambda d: d.pop('game'))
        with self.assertRaises(FormatError) as ctx:
            parse_checkpoint_data(container)
        self.assertEqual("checkpoint data is missing 'game'",
                         str(ctx.exception))

    def test_stale_detector_version_refused_exactly(self):
        container, data, setup, payload, registry, gs_dict = (
            make_valid_data())
        payload = copy.deepcopy(payload)
        payload['detector_version'] = 'det-0'     # re-stamp (02-15:82)
        container = copy.deepcopy(container)
        container['data']['game']['level_spec'] = payload
        with self.assertRaises(FormatError) as ctx:
            parse_checkpoint_data(container)
        self.assertEqual(
            "unsupported detector_version 'det-0' in level spec "
            "(expected 'det-1'): stale or newer game spec - regenerate "
            "it with a current AA-match generator", str(ctx.exception))

    def test_newer_game_format_version_refused_exactly(self):
        edit = _editor(make_valid_data()[0])
        container = edit(lambda d: d['game'].update(game_format_version=2))
        with self.assertRaises(FormatError) as ctx:
            parse_checkpoint_data(container)
        self.assertEqual(
            'unsupported game file version 2 (expected <= 1). '
            'Please update AA-match.', str(ctx.exception))


class TestParseGate4GameStateValidator(unittest.TestCase):
    """Gate 4: the GameState light validator (fail-closed, key-naming)."""

    def _parse_with_gs_edit(self, edit_fn):
        edit = _editor(make_valid_data()[0])
        container = edit(lambda d: edit_fn(d['game_state']))
        return parse_checkpoint_data(container)

    def test_missing_required_base_key_refused(self):
        for key in ('current_level_index', 'current_molecule_index',
                    'molecule_scores', 'skip_count', 'giveup_count',
                    'timer_anchor', 'formed_types_per_molecule'):
            with self.assertRaises(FormatError) as ctx:
                self._parse_with_gs_edit(lambda d, k=key: d.pop(k))
            self.assertEqual(
                "checkpoint data is missing 'game_state.%s'" % key,
                str(ctx.exception))

    def test_one_record_invariant_refused(self):
        def edit_fn(d):
            d['molecule_scores'] = [0.5]      # no score_per_molecule key
        with self.assertRaises(FormatError) as ctx:
            self._parse_with_gs_edit(edit_fn)
        self.assertEqual(
            'checkpoint game_state breaks the one-record-per-molecule '
            'invariant (len(molecule_scores)=1 != '
            'len(score_per_molecule)=0)', str(ctx.exception))

    def test_out_of_bounds_molecule_key_refused(self):
        def edit_fn(d):
            d['molecule_scores'] = [0.5]
            d['score_per_molecule'] = {'L7M0': 0.5}
            d['formed_types_per_molecule'] = {'L7M0': []}
        with self.assertRaises(FormatError) as ctx:
            self._parse_with_gs_edit(edit_fn)
        self.assertEqual(
            "checkpoint game_state key 'L7M0' is outside the embedded "
            "payload's level/molecule bounds", str(ctx.exception))

    def test_out_of_bounds_molecule_index_refused(self):
        def edit_fn(d):
            d['molecule_scores'] = [0.5]
            d['score_per_molecule'] = {'L0M9': 0.5}
            d['formed_types_per_molecule'] = {'L0M9': []}
        with self.assertRaises(FormatError) as ctx:
            self._parse_with_gs_edit(edit_fn)
        self.assertEqual(
            "checkpoint game_state key 'L0M9' is outside the embedded "
            "payload's level/molecule bounds", str(ctx.exception))

    def test_in_bounds_molecule_key_accepted(self):
        def edit_fn(d):
            d['molecule_scores'] = [0.5]
            d['score_per_molecule'] = {'L0M0': 0.5}
            d['formed_types_per_molecule'] = {'L0M0': []}
        parsed = self._parse_with_gs_edit(edit_fn)
        self.assertEqual(parsed['game_state']['molecule_scores'], [0.5])

    def test_skip_count_non_int_refused(self):
        def edit_fn(d):
            d['skip_count'] = True            # bools are not counts
        with self.assertRaises(FormatError) as ctx:
            self._parse_with_gs_edit(edit_fn)
        self.assertEqual(
            "checkpoint game_state 'skip_count' must be an int, "
            'found True', str(ctx.exception))

    def test_giveup_count_non_int_refused(self):
        def edit_fn(d):
            d['giveup_count'] = 'two'
        with self.assertRaises(FormatError) as ctx:
            self._parse_with_gs_edit(edit_fn)
        self.assertEqual(
            "checkpoint game_state 'giveup_count' must be an int, "
            "found 'two'", str(ctx.exception))

    def test_negative_elapsed_refused_naming_rewind(self):
        edit = _editor(make_valid_data()[0])
        container = edit(lambda d: d.update(elapsed_at_save=-1.0))
        with self.assertRaises(FormatError) as ctx:
            parse_checkpoint_data(container)
        self.assertEqual(
            "checkpoint 'elapsed_at_save' must be a non-negative float "
            "or null, found -1.0 (a negative would push the timer anchor "
            "into the future and rewind the clock)", str(ctx.exception))

    def test_non_float_elapsed_refused(self):
        edit = _editor(make_valid_data()[0])
        container = edit(lambda d: d.update(elapsed_at_save='12:30'))
        with self.assertRaises(FormatError) as ctx:
            parse_checkpoint_data(container)
        self.assertEqual(
            "checkpoint 'elapsed_at_save' must be a non-negative float "
            "or null, found '12:30' (a negative would push the timer "
            "anchor into the future and rewind the clock)",
            str(ctx.exception))

    def test_none_elapsed_accepted(self):
        edit = _editor(make_valid_data()[0])
        container = edit(lambda d: d.update(elapsed_at_save=None))
        parsed = parse_checkpoint_data(container)
        self.assertIsNone(parsed['elapsed_at_save'])

    def test_int_elapsed_coerced_to_float(self):
        edit = _editor(make_valid_data()[0])
        container = edit(lambda d: d.update(elapsed_at_save=7))
        parsed = parse_checkpoint_data(container)
        self.assertEqual(parsed['elapsed_at_save'], 7.0)
        self.assertIsInstance(parsed['elapsed_at_save'], float)


class TestParseGate5Blocks(unittest.TestCase):
    """Gate 5: registry/wizard additive blocks + consistency refusals."""

    def test_registry_level_index_mismatch_refused(self):
        edit = _editor(make_valid_data()[0])
        container = edit(lambda d: d['registry'].update(level_index=1))
        with self.assertRaises(FormatError) as ctx:
            parse_checkpoint_data(container)
        self.assertEqual(
            "checkpoint registry 'level_index' 1 does not match "
            "game_state 'current_level_index' 0", str(ctx.exception))

    def test_wizard_non_dict_refused(self):
        edit = _editor(make_valid_data()[0])
        container = edit(lambda d: d.update(wizard=['not', 'a', 'dict']))
        with self.assertRaises(FormatError) as ctx:
            parse_checkpoint_data(container)
        self.assertEqual(
            "checkpoint 'wizard' block must be a dict, found list",
            str(ctx.exception))

    def test_missing_blocks_accepted_as_none(self):
        # Additive evolution: a v1-minus-extras checkpoint parses with
        # .get defaults (registry/wizard/candidates absent -> None).
        edit = _editor(make_valid_data()[0])
        container = edit(
            lambda d: [d.pop(k) for k in ('registry', 'wizard',
                                          'candidates')])
        parsed = parse_checkpoint_data(container)
        self.assertIsNone(parsed['registry'])
        self.assertIsNone(parsed['wizard'])
        self.assertIsNone(parsed['candidates'])

    def test_elapsed_feeds_rebase_timer(self):
        # The re-anchor authority: parse output elapsed_at_save goes
        # straight into GameState.rebase_timer (anchor == now - elapsed).
        container = make_valid_data(elapsed=12.5)[0]
        parsed = parse_checkpoint_data(container)
        gs = GameState()
        gs.rebase_timer(1000.0, parsed['elapsed_at_save'])
        self.assertEqual(gs.timer_anchor, 987.5)


class TestReconcileRegistry(unittest.TestCase):
    """reconcile_registry: keep-iff-verified, never-ghost-entry, report,
    tuple-shaped rebuild, current-level completeness gate."""

    def _registry_payload(self):
        setup, payload = make_payload()
        registry = make_registry(payload, 0)
        return payload, registry

    def test_exact_sweep_keeps_everything_and_rebuilds_tuples(self):
        payload, registry = self._registry_payload()
        observed = observed_for(registry)
        sidecar = json.loads(json.dumps(
            {k: registry[k] for k in ('level_index', 'molecules')}))
        rebuilt, report = reconcile_registry(sidecar, observed, payload, 0)
        self.assertEqual(report, {'dropped': [],
                                  'missing_from_sidecar': []})
        self.assertEqual(rebuilt['level_index'], 0)
        self.assertEqual(rebuilt['pre_game_names'], [])
        self.assertEqual(len(rebuilt['molecules']),
                         len(registry['molecules']))
        for original, new in zip(registry['molecules'],
                                 rebuilt['molecules']):
            self.assertEqual(new['molecule_id'],
                             original['molecule_id'])
            self.assertEqual(new['offset'], original['offset'])
            self.assertIsInstance(new['offset'], tuple)
            # THE round-trip law: lists become TUPLES matching the
            # placement.materialize registry shape.
            self.assertEqual(new['ligand'], original['ligand'])
            self.assertIsInstance(new['ligand'], tuple)
            self.assertIsInstance(new['ligand'][1], tuple)
            for slot_id, entry in original['slots'].items():
                rebuilt_entry = new['slots'][slot_id]
                self.assertEqual(rebuilt_entry, entry)
                self.assertIsInstance(rebuilt_entry, tuple)
                self.assertIsInstance(rebuilt_entry[1], tuple)

    def test_ghost_entry_dropped_and_reported_never_registered(self):
        payload, registry = self._registry_payload()
        observed = observed_for(registry)
        sidecar = json.loads(json.dumps(
            {k: registry[k] for k in ('level_index', 'molecules')}))
        # An extra entry whose object is absent from the scene: the
        # never-ghost-entry law DROPS it (registered entries must always
        # reference real atoms).
        sidecar['molecules'][0]['slots']['bogus_slot'] = \
            ['_aam_aa_ghost', [999]]
        rebuilt, report = reconcile_registry(sidecar, observed, payload, 0)
        self.assertNotIn('bogus_slot', rebuilt['molecules'][0]['slots'])
        self.assertEqual(len(report['dropped']), 1)
        drop = report['dropped'][0]
        self.assertEqual(drop['object'], '_aam_aa_ghost')
        self.assertEqual(drop['slot'], 'bogus_slot')
        self.assertEqual(drop['reason'], 'object absent from scene')
        self.assertEqual(report['missing_from_sidecar'], [])

    def test_id_mismatch_entry_dropped_and_reported(self):
        payload, registry = self._registry_payload()
        observed = observed_for(registry)
        sidecar = json.loads(json.dumps(
            {k: registry[k] for k in ('level_index', 'molecules')}))
        observed['_aam_aa_drift'] = [1, 2]      # ids differ from sidecar
        sidecar['molecules'][0]['slots']['bogus_slot'] = \
            ['_aam_aa_drift', [1, 2, 3]]
        rebuilt, report = reconcile_registry(sidecar, observed, payload, 0)
        self.assertNotIn('bogus_slot', rebuilt['molecules'][0]['slots'])
        self.assertEqual(len(report['dropped']), 1)
        drop = report['dropped'][0]
        self.assertEqual(drop['object'], '_aam_aa_drift')
        self.assertEqual(drop['reason'],
                         'scene atom ids [1, 2] do not match the '
                         'sidecar ids [1, 2, 3]')

    def test_scene_object_without_sidecar_entry_reported(self):
        payload, registry = self._registry_payload()
        observed = observed_for(registry)
        observed['_aam_aa_stray'] = [5, 6]
        sidecar = json.loads(json.dumps(
            {k: registry[k] for k in ('level_index', 'molecules')}))
        rebuilt, report = reconcile_registry(sidecar, observed, payload, 0)
        self.assertEqual(report['dropped'], [])
        self.assertEqual(report['missing_from_sidecar'],
                         ['_aam_aa_stray'])

    def test_missing_ligand_refuses_naming_first_piece(self):
        payload, registry = self._registry_payload()
        observed = observed_for(registry)
        # The current-level ligand object is gone from the scene.
        lig_name = registry['molecules'][0]['ligand'][0]
        del observed[lig_name]
        sidecar = json.loads(json.dumps(
            {k: registry[k] for k in ('level_index', 'molecules')}))
        with self.assertRaises(FormatError) as ctx:
            reconcile_registry(sidecar, observed, payload, 0)
        self.assertEqual(
            "checkpoint scene is missing game object %r (molecule "
            "'mol-001', slot 'ligand') -- the saved session no longer "
            "matches this checkpoint" % lig_name, str(ctx.exception))

    def test_missing_slot_refuses_naming_first_piece(self):
        payload, registry = self._registry_payload()
        observed = observed_for(registry)
        # One expected slot object fails to verify (absent from scene).
        slots = registry['molecules'][0]['slots']
        slot_id = sorted(slots)[0]
        obj_name = slots[slot_id][0]
        del observed[obj_name]
        sidecar = json.loads(json.dumps(
            {k: registry[k] for k in ('level_index', 'molecules')}))
        with self.assertRaises(FormatError) as ctx:
            reconcile_registry(sidecar, observed, payload, 0)
        self.assertEqual(
            "checkpoint scene is missing game object %r (molecule "
            "'mol-001', slot '%s') -- the saved session no longer "
            "matches this checkpoint" % (obj_name, slot_id),
            str(ctx.exception))

    def test_missing_sidecar_row_refuses_naming_first_piece(self):
        payload, registry = self._registry_payload()
        observed = observed_for(registry)
        sidecar = json.loads(json.dumps(
            {k: registry[k] for k in ('level_index', 'molecules')}))
        # The sidecar lost the molecule row entirely (corrupt sidecar):
        # the piece's object name is UNKNOWN, the gate names None.
        sidecar['molecules'] = []
        with self.assertRaises(FormatError) as ctx:
            reconcile_registry(sidecar, observed, payload, 0)
        self.assertEqual(
            "checkpoint scene is missing game object None (molecule "
            "'mol-001', slot 'ligand') -- the saved session no longer "
            "matches this checkpoint", str(ctx.exception))

    def test_future_levels_need_nothing(self):
        # Only ONE level is ever materialized (placement.py:64-66): the
        # expected-shape gate walks the CURRENT level only, even when the
        # payload carries more (difficulty=2 -> 2 levels).
        payload, registry = self._registry_payload()
        self.assertEqual(len(payload['levels']), 2)
        observed = observed_for(registry)
        sidecar = json.loads(json.dumps(
            {k: registry[k] for k in ('level_index', 'molecules')}))
        rebuilt, report = reconcile_registry(sidecar, observed, payload, 0)
        self.assertEqual(report, {'dropped': [],
                                  'missing_from_sidecar': []})


class TestZipIO(unittest.TestCase):
    """write_checkpoint_zip / read_checkpoint_zip: atomic temp+replace
    write, refusal-before-extraction read, byte-identical .pse member."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp(prefix='aamatch_checkpoint_')

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def _write_zip(self, members):
        path = os.path.join(self.tmpdir, 'arch.aamz')
        with zipfile.ZipFile(path, 'w') as zf:
            for arcname, data in members:
                zf.writestr(arcname, data)
        return path

    def test_round_trip(self):
        container, data, setup, payload, registry, gs_dict = (
            make_valid_data())
        pse_src = os.path.join(self.tmpdir, 'session.pse')
        with open(pse_src, 'wb') as handle:
            handle.write(PSE_FIXTURE_BYTES)
        zip_path = os.path.join(self.tmpdir, 'save.aamz')
        write_checkpoint_zip(zip_path, data, pse_src)
        self.assertTrue(os.path.exists(zip_path))
        pse_path, parsed = read_checkpoint_zip(zip_path)
        with open(pse_path, 'rb') as handle:
            self.assertEqual(handle.read(), PSE_FIXTURE_BYTES)
        self.assertEqual(os.path.basename(pse_path), 'game.pse')
        self.assertEqual(parsed['payload'], payload)
        self.assertEqual(parsed['elapsed_at_save'], 12.5)

    def test_sidecar_member_is_full_container(self):
        # check_container gate 1 applies on read: the sidecar member IS
        # the full {magic, version, kind, data} JSON.
        container, data, *_ = make_valid_data()
        pse_src = os.path.join(self.tmpdir, 'session.pse')
        with open(pse_src, 'wb') as handle:
            handle.write(PSE_FIXTURE_BYTES)
        zip_path = os.path.join(self.tmpdir, 'save.aamz')
        write_checkpoint_zip(zip_path, data, pse_src)
        with zipfile.ZipFile(zip_path, 'r') as zf:
            self.assertEqual(sorted(zf.namelist()),
                             [PSE_MEMBER, SIDECAR_MEMBER])
            sidecar = json.loads(
                zf.read(SIDECAR_MEMBER).decode('utf-8'))
        self.assertEqual(sorted(sidecar),
                         ['data', 'kind', 'magic', 'version'])
        self.assertEqual(sidecar['magic'], 'AAMATCH')
        self.assertEqual(sidecar['kind'], 'checkpoint')

    def test_missing_state_json_refused(self):
        path = self._write_zip([(PSE_MEMBER, PSE_FIXTURE_BYTES)])
        with self.assertRaises(FormatError) as ctx:
            read_checkpoint_zip(path)
        self.assertEqual('not an AA-match archive (missing state.json)',
                         str(ctx.exception))

    def test_missing_game_pse_refused(self):
        container, data, *_ = make_valid_data()
        sidecar = json.dumps(make_container('checkpoint', data),
                             sort_keys=True).encode('utf-8')
        path = self._write_zip([(SIDECAR_MEMBER, sidecar)])
        with self.assertRaises(FormatError) as ctx:
            read_checkpoint_zip(path)
        self.assertEqual('archive missing game.pse (cannot reconstruct)',
                         str(ctx.exception))

    def test_corrupt_zip_refused_as_format_error_not_bad_zip(self):
        path = os.path.join(self.tmpdir, 'broken.aamz')
        with open(path, 'wb') as handle:
            handle.write(b'this is not a zip file at all')
        with self.assertRaises(FormatError):
            read_checkpoint_zip(path)

    def test_foreign_sidecar_refused_before_extraction(self):
        # Gate 1 fires on read: a checkpoint member with foreign magic
        # is refused with the canonical header message.
        _, data, *_ = make_valid_data()
        container = make_container('checkpoint', data)
        container['magic'] = 'NOTAAM'
        sidecar = json.dumps(container, sort_keys=True).encode('utf-8')
        path = self._write_zip([(SIDECAR_MEMBER, sidecar),
                                (PSE_MEMBER, PSE_FIXTURE_BYTES)])
        with self.assertRaises(FormatError) as ctx:
            read_checkpoint_zip(path)
        self.assertIn('not an AA-match file', str(ctx.exception))

    def test_temp_zip_removed_on_write_failure(self):
        # The write_json_atomic discipline: a failure removes the temp
        # zip and never leaves .aam_* debris in the target dir.
        container, data, *_ = make_valid_data()
        pse_src = os.path.join(self.tmpdir, 'session.pse')
        with open(pse_src, 'wb') as handle:
            handle.write(PSE_FIXTURE_BYTES)
        bad_target = os.path.join(self.tmpdir, 'no_such_dir',
                                  'save.aamz')
        # mkstemp mints the temp inside the target's parent dir, which
        # does not exist here -> the write raises before creating any
        # temp; the refusal surfaces and nothing is created.
        with self.assertRaises(OSError):
            write_checkpoint_zip(bad_target, data, pse_src)
        leftovers = [name for name in os.listdir(self.tmpdir)
                     if name.startswith('.aam_')]
        self.assertEqual(leftovers, [])


if __name__ == '__main__':
    unittest.main()
