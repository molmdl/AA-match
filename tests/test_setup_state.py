"""Tests for aamatch.setup_state + setup-file persistence wrappers.

RED-first suite for plan 01-05 (Phase-1 success criterion 1: the 7-field
setup model round-trips through a versioned setup file -- PERSIST-01).
Covers:

- DEFAULTS schema regression: exact 7-key set, no 'format' field (D2/P8)
- validate_state: missing-key fill, enum fallback, int coercion+clamping,
  allowed_interactions filter/dedup/canonical order, upload shape check,
  input non-mutation (D3/P6)
- randomize_state: seed determinism, complete valid output (D4)
- PERSIST-01 round-trip: an every-field-non-default state survives
  save_setup_file/load_setup_file with EXACT dict equality
- validate-on-load idempotence
- refusal classes, message-asserted (foreign JSON / newer version /
  misfiled kind / garbage bytes) -- the checks prior art lacked (C3/C6)
- older-container-version acceptance + old-data forward-fill from
  DEFAULTS (refuse-newer / accept-older, B4 .get discipline)

Runs under bare python3.6 in WSL with stdlib only (no pymol/Qt/numpy
stubs needed -- the modules under test are pure).
"""

import copy
import os
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from aamatch.persistence import (
    AAM_MAGIC,
    FORMAT_VERSION,
    FormatError,
    load_setup_file,
    make_container,
    read_json_file,
    save_setup_file,
    validate_state as persistence_validate_state,
    write_json_atomic,
)
from aamatch.setup_state import (
    DEFAULTS,
    DIFFICULTY_CAP,
    DIFFICULTY_DEFAULT,
    DIFFICULTY_MIN,
    INTERACTION_MODES,
    INTERACTION_TYPES,
    MOLECULES_CAP,
    MOLECULES_DEFAULT,
    MOLECULES_MIN,
    randomize_state,
    validate_state,
)

EXPECTED_KEYS = {
    'source_mode',
    'demo_set_id',
    'upload',
    'molecules_per_level',
    'difficulty_levels',
    'interaction_mode',
    'allowed_interactions',
}


def _non_default_raw_state(interaction_mode):
    """Raw state with EVERY field at a non-default value (case 9 basis).

    Unicode demo_set_id, boundary ints (MIN for molecules, CAP for
    difficulty), all 7 interaction types, an upload dict -- only the
    interaction mode varies (subTest per mode, all 3 covered).
    """
    return {
        'source_mode': 'upload',                        # non-default ('demo')
        'demo_set_id': 'démo-β',                        # unicode, non-empty
        'upload': {'path': 'C:\\sets\\ligand.sdf', 'sha256': 'ab' * 32},
        'molecules_per_level': MOLECULES_MIN,           # boundary MIN (1)
        'difficulty_levels': DIFFICULTY_CAP,            # boundary CAP (10)
        'interaction_mode': interaction_mode,
        'allowed_interactions': list(INTERACTION_TYPES),  # all 7 types
    }


class TestSetupStateContract(unittest.TestCase):
    """Module surface: constants (D2 pattern) + persistence import direction."""

    def test_01_defaults_key_set_is_exactly_the_7_fields(self):
        # Schema drift must fail loudly (D2); container header is the
        # ONLY format tag, so 'format' must never appear (P8/C1).
        self.assertEqual(set(DEFAULTS), EXPECTED_KEYS)
        self.assertNotIn('format', DEFAULTS)

    def test_01b_enum_and_clamp_constants(self):
        self.assertEqual(
            INTERACTION_TYPES,
            ['h_bond', 'salt_bridge', 'pi_stacking', 'cation_pi',
             'hydrophobic', 'halogen', 'metal'])
        self.assertEqual(
            INTERACTION_MODES, ['exclusive', 'block_exclusive', 'unset'])
        self.assertEqual(
            (MOLECULES_DEFAULT, MOLECULES_MIN, MOLECULES_CAP), (2, 1, 10))
        self.assertEqual(
            (DIFFICULTY_DEFAULT, DIFFICULTY_MIN, DIFFICULTY_CAP), (3, 1, 10))

    def test_persistence_wrappers_share_the_model_validate(self):
        # B8 dependency direction: persistence imports the pure model
        # (module-level), never the reverse.
        self.assertIs(persistence_validate_state, validate_state)


class TestValidateState(unittest.TestCase):
    """validate_state: fill / fallback / clamp / normalize / non-mutation."""

    def test_02_validate_empty_state_deep_equals_defaults(self):
        result = validate_state({})
        self.assertEqual(result, copy.deepcopy(DEFAULTS))
        # A NEW dict built from a DEFAULTS copy -- never the object itself.
        self.assertIsNot(result, DEFAULTS)

    def test_03_invalid_interaction_mode_falls_back_to_unset(self):
        for bogus in ('bogus', 3, None, ''):
            result = validate_state({'interaction_mode': bogus})
            self.assertEqual(result['interaction_mode'], 'unset')

    def test_03b_valid_enum_values_pass_through(self):
        for mode in INTERACTION_MODES:
            result = validate_state({'interaction_mode': mode})
            self.assertEqual(result['interaction_mode'], mode)
        for source in ('demo', 'upload'):
            result = validate_state({'source_mode': source})
            self.assertEqual(result['source_mode'], source)

    def test_03c_invalid_source_mode_falls_back_to_demo(self):
        result = validate_state({'source_mode': 'bogus'})
        self.assertEqual(result['source_mode'], 'demo')

    def test_04_int_fields_coerce_then_clamp(self):
        cases = [
            ({'molecules_per_level': 99}, MOLECULES_CAP),
            ({'molecules_per_level': 0}, MOLECULES_MIN),
            ({'molecules_per_level': -50}, MOLECULES_MIN),
            ({'molecules_per_level': 'x'}, MOLECULES_DEFAULT),
            ({'molecules_per_level': None}, MOLECULES_DEFAULT),
            ({'molecules_per_level': '5'}, 5),
            ({'molecules_per_level': MOLECULES_CAP}, MOLECULES_CAP),
            ({'difficulty_levels': -1}, DIFFICULTY_MIN),
            ({'difficulty_levels': 99}, DIFFICULTY_CAP),
            # Human-amended cap (01-09): literal pins prove the boundary
            # independent of the constant -- 10 accepted, 11 clamps to 10.
            ({'difficulty_levels': 10}, 10),
            ({'difficulty_levels': 11}, 10),
            ({'difficulty_levels': 'x'}, DIFFICULTY_DEFAULT),
            ({'difficulty_levels': DIFFICULTY_MIN}, DIFFICULTY_MIN),
            ({'difficulty_levels': DIFFICULTY_CAP}, DIFFICULTY_CAP),
        ]
        for dirty, expected in cases:
            with self.subTest(dirty=dirty, expected=expected):
                result = validate_state(dirty)
                key = list(dirty)[0]
                self.assertEqual(result[key], expected)

    def test_05_allowed_interactions_filtered_deduped_canonical(self):
        dirty = ['halogen', 'h_bond', 'halogen', 'bogus', 'metal']
        result = validate_state({'allowed_interactions': dirty})
        self.assertEqual(result['allowed_interactions'],
                         ['h_bond', 'halogen', 'metal'])

    def test_05b_equal_interaction_sets_serialize_identically(self):
        a = validate_state({'allowed_interactions': ['metal', 'h_bond']})
        b = validate_state({'allowed_interactions': ['h_bond', 'metal']})
        self.assertEqual(a, b)

    def test_05c_non_list_allowed_interactions_becomes_empty(self):
        for bad in ('h_bond', 7, None):
            result = validate_state({'allowed_interactions': bad})
            self.assertEqual(result['allowed_interactions'], [])

    def test_06_upload_shape_checked(self):
        # Wrong member types -> refused to None.
        result = validate_state({'upload': {'path': 3, 'sha256': 'abc'}})
        self.assertIsNone(result['upload'])
        # Missing sha256 -> refused.
        result = validate_state({'upload': {'path': 'C:\\x.sdf'}})
        self.assertIsNone(result['upload'])
        # Non-dict values -> None.
        for bad in ('path', 7, ['x'], True, None):
            result = validate_state({'upload': bad})
            self.assertIsNone(result['upload'])
        # Valid dict kept, extra keys dropped, exactly {path, sha256}.
        good = {'path': 'C:\\x.sdf', 'sha256': 'ab', 'extra': 'drop me'}
        result = validate_state({'upload': good})
        self.assertEqual(result['upload'], {'path': 'C:\\x.sdf', 'sha256': 'ab'})
        self.assertEqual(set(result['upload']), {'path', 'sha256'})

    def test_07_validate_state_never_mutates_its_input(self):
        dirty = {
            'source_mode': 'upload',
            'demo_set_id': 'démo-β',
            'upload': {'path': 3, 'sha256': 'abc', 'extra': 1},
            'molecules_per_level': 99,
            'difficulty_levels': 'x',
            'interaction_mode': 'bogus',
            'allowed_interactions': ['halogen', 'h_bond', 'halogen', 'bogus'],
            'unknown_future_field': {'keep': 'me?'},
        }
        snapshot = copy.deepcopy(dirty)
        result = validate_state(dirty)
        self.assertEqual(dirty, snapshot)   # input untouched (P6/D3)
        self.assertIsNot(result, dirty)     # output is a NEW dict
        self.assertEqual(result['allowed_interactions'], ['h_bond', 'halogen'])

    def test_07b_mutating_result_cannot_leak_into_input(self):
        dirty = {
            'upload': {'path': 'C:\\a.sdf', 'sha256': 'ff'},
            'allowed_interactions': ['metal'],
        }
        snapshot = copy.deepcopy(dirty)
        result = validate_state(dirty)
        result['upload']['path'] = 'MUTATED'
        result['allowed_interactions'].append('h_bond')
        self.assertEqual(dirty, snapshot)   # deep independence


class TestRandomizeState(unittest.TestCase):
    """randomize_state: complete valid state, deterministic under seed (D4)."""

    def test_08_seeded_randomize_is_deterministic_and_valid(self):
        first = randomize_state(seed=42)
        second = randomize_state(seed=42)
        self.assertEqual(first, second)
        # Complete: all 7 keys present.
        self.assertEqual(set(first), EXPECTED_KEYS)
        # A randomized state must be USABLE: demo source, no upload file.
        self.assertEqual(first['source_mode'], 'demo')
        self.assertIsNone(first['upload'])
        self.assertIsInstance(first['demo_set_id'], str)
        self.assertTrue(first['demo_set_id'])
        # Ints within clamps, enums valid.
        self.assertTrue(MOLECULES_MIN <= first['molecules_per_level']
                        <= MOLECULES_CAP)
        self.assertTrue(DIFFICULTY_MIN <= first['difficulty_levels']
                        <= DIFFICULTY_CAP)
        self.assertIn(first['interaction_mode'], INTERACTION_MODES)
        # allowed_interactions: non-empty subset in canonical order.
        interactions = first['allowed_interactions']
        self.assertTrue(interactions)
        self.assertTrue(all(t in INTERACTION_TYPES for t in interactions))
        canonical = [t for t in INTERACTION_TYPES if t in set(interactions)]
        self.assertEqual(interactions, canonical)
        # Already-valid output is a fixpoint of validate_state.
        self.assertEqual(validate_state(first), first)

    def test_08b_unseeded_randomize_is_complete_and_valid(self):
        state = randomize_state()
        self.assertEqual(set(state), EXPECTED_KEYS)
        self.assertEqual(validate_state(state), state)


class TestSetupFileRoundTrip(unittest.TestCase):
    """PERSIST-01 through the versioned setup-file wrappers."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix='aamatch-test-')
        self.addCleanup(shutil.rmtree, self.tmp)

    def test_09_round_trip_every_field_non_default(self):
        for mode in INTERACTION_MODES:
            with self.subTest(interaction_mode=mode):
                raw = _non_default_raw_state(mode)
                original = validate_state(raw)
                path = os.path.join(self.tmp, 'setup-%s.json' % mode)
                save_setup_file(path, raw)      # validates BEFORE write
                loaded = load_setup_file(path)  # validates AGAIN on load
                self.assertEqual(loaded, original)  # EXACT dict equality
                # The file carries the versioned container header.
                on_disk = read_json_file(path)
                self.assertEqual(on_disk['magic'], AAM_MAGIC)
                self.assertEqual(on_disk['version'], FORMAT_VERSION)
                self.assertEqual(on_disk['kind'], 'setup')

    def test_09b_save_normalizes_invalid_state_before_write(self):
        path = os.path.join(self.tmp, 'dirty.json')
        save_setup_file(path, {'molecules_per_level': 99,
                               'interaction_mode': 'bogus'})
        loaded = load_setup_file(path)
        self.assertEqual(loaded['molecules_per_level'], MOLECULES_CAP)
        self.assertEqual(loaded['interaction_mode'], 'unset')

    def test_10_validate_on_load_is_idempotent(self):
        for mode in INTERACTION_MODES:
            with self.subTest(interaction_mode=mode):
                raw = _non_default_raw_state(mode)
                once = validate_state(raw)
                self.assertEqual(validate_state(once), once)
                path = os.path.join(self.tmp, 'setup-%s.json' % mode)
                save_setup_file(path, once)
                loaded = load_setup_file(path)
                # Load re-validates -- it must not change anything.
                self.assertEqual(validate_state(loaded), loaded)
                self.assertEqual(load_setup_file(path), loaded)


class TestSetupFileRefusals(unittest.TestCase):
    """Refusal classes, message-asserted (prior art had NO checks, C3)."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix='aamatch-test-')
        self.addCleanup(shutil.rmtree, self.tmp)

    def test_11a_foreign_json_refused(self):
        path = os.path.join(self.tmp, 'foreign.json')
        write_json_atomic(path, {'hello': 'world', 'list': [1, 2, 3]})
        with self.assertRaises(FormatError) as ctx:
            load_setup_file(path)
        self.assertIn('not an AA-match file', str(ctx.exception))

    def test_11b_newer_version_refused_with_update_message(self):
        path = os.path.join(self.tmp, 'newer.json')
        container = {'magic': AAM_MAGIC, 'version': 999, 'kind': 'setup',
                     'data': {}}
        write_json_atomic(path, container)
        with self.assertRaises(FormatError) as ctx:
            load_setup_file(path)
        message = str(ctx.exception)
        self.assertIn('unsupported', message)
        self.assertIn('Please update AA-match', message)

    def test_11c_misfiled_kind_refused(self):
        path = os.path.join(self.tmp, 'level_spec.json')
        write_json_atomic(path, make_container('level_spec', {'levels': []}))
        with self.assertRaises(FormatError) as ctx:
            load_setup_file(path)
        self.assertIn('expected an AA-match setup file', str(ctx.exception))

    def test_11d_garbage_bytes_refused_with_parse_message(self):
        path = os.path.join(self.tmp, 'truncated.json')
        with open(path, 'wb') as fh:
            fh.write(b'{"magic": "AAMAT')   # truncated mid-JSON
        with self.assertRaises(FormatError) as ctx:
            load_setup_file(path)
        self.assertIn('could not parse AA-match JSON', str(ctx.exception))

    def test_12_older_container_version_accepted(self):
        # refuse-newer / accept-older: version FORMAT_VERSION - 1 loads.
        path = os.path.join(self.tmp, 'older.json')
        container = {'magic': AAM_MAGIC, 'version': FORMAT_VERSION - 1,
                     'kind': 'setup', 'data': {}}
        write_json_atomic(path, container)
        loaded = load_setup_file(path)      # must NOT raise
        self.assertEqual(loaded, validate_state({}))

    def test_13_old_data_dict_forward_filled_from_defaults(self):
        # A v0-era payload missing 'upload'/'allowed_interactions' loads
        # with those keys filled from DEFAULTS (B4 .get discipline).
        path = os.path.join(self.tmp, 'legacy.json')
        legacy_data = {
            'source_mode': 'demo',
            'demo_set_id': 'legacy-set',
            'molecules_per_level': 2,
            'difficulty_levels': 3,
            'interaction_mode': 'exclusive',
        }
        write_json_atomic(path, make_container('setup', legacy_data))
        loaded = load_setup_file(path)
        self.assertIsNone(loaded['upload'])
        self.assertEqual(loaded['allowed_interactions'], [])
        self.assertEqual(loaded['interaction_mode'], 'exclusive')
        self.assertEqual(loaded, validate_state(legacy_data))


if __name__ == '__main__':
    unittest.main()
