"""Tests for aamatch.level_spec -- reserved level-spec schema + version gates.

RED-first suite for plan 01-06 (DETECT-05 precursor; H8-H12). Covers:

- module constants: DETECTOR_VERSION 'det-1' (exact-match gate) and
  LEVEL_SPEC_VERSION 1 (refuse-newer gate), plus the container re-export
- minimal valid spec parses and passes through unchanged (P9: unknown
  keys preserved, never stripped; P6: input never mutated)
- container round-trip through persistence (kind='level_spec')
- the TWO distinct version policies proven distinct:
  * payload format_version: refuse-newer / accept-older (additive only)
  * payload detector_version: EXACT match -- stale AND newer both
    refused (P4: refuse-newer-only would wrongly accept newer detectors)
- structural minimums: non-empty levels list, grid n >= 1, unique
  slot_id values per molecule (same id across molecules is fine)
- required seed: present AND an int (H12 deterministic replay)

Runs under bare python3.6 in WSL with stdlib only (no pymol/Qt/numpy
stubs needed -- the module under test is pure).
"""

import copy
import os
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from aamatch.level_spec import (
    DETECTOR_VERSION,
    LEVEL_SPEC_VERSION,
    make_level_spec_container,
    parse_level_spec_dict,
)
from aamatch.persistence import (
    AAM_MAGIC,
    FORMAT_VERSION,
    FormatError,
    read_json_file,
    save_container,
)


def _spec():
    """Minimal valid level-spec payload (research R5 shape, one of everything).

    Top-level keys: detector_version, format_version, seed, levels.
    One level > one molecule > one slot carrying every reserved slot key.
    """
    return {
        "detector_version": "det-1",
        "format_version": 1,
        "seed": 20260905,
        "levels": [
            {
                "level_index": 0,
                "difficulty": {
                    "tier": 0,
                    "grid_n": 3,
                    "n_required_types": 2,
                    "molecule_size_class": "small",
                },
                "molecules": [
                    {
                        "molecule_id": "mol-001",
                        "ligand": {
                            "source": "demo",
                            "set_id": "demo-xxx",
                            "entry_id": "",
                            "file": "",
                            "sha256": "",
                            "protonation": "",
                            "provenance": "",
                        },
                        "required": {
                            "mode": "any",
                            "items": [{"type": "h_bond", "count": 1}],
                        },
                        "grid": {
                            "n": 3,
                            "slots": [
                                {
                                    "slot_id": 0,
                                    "row": 0,
                                    "col": 0,
                                    "aa": "ALA",
                                    "role": "required",
                                    "can_form": ["h_bond"],
                                    "grid_pose": {
                                        "position": [0.0, 0.0, 0.0],
                                    },
                                }
                            ],
                        },
                    }
                ],
            }
        ],
    }


def _two_molecule_spec():
    """Valid spec with TWO molecules (for cross-molecule slot-id scoping)."""
    spec = _spec()
    second = copy.deepcopy(spec['levels'][0]['molecules'][0])
    second['molecule_id'] = 'mol-002'
    spec['levels'][0]['molecules'].append(second)
    return spec


class TestModuleContract(unittest.TestCase):
    """Module constants and the container re-export."""

    def test_constants(self):
        self.assertEqual(DETECTOR_VERSION, 'det-1')
        self.assertEqual(LEVEL_SPEC_VERSION, 1)

    def test_make_level_spec_container_uses_persistence_container(self):
        container = make_level_spec_container({'a': 1})
        self.assertEqual(container['magic'], AAM_MAGIC)
        self.assertEqual(container['version'], FORMAT_VERSION)
        self.assertEqual(container['kind'], 'level_spec')
        self.assertEqual(container['data'], {'a': 1})


class TestValidSpecPassthrough(unittest.TestCase):
    """Behavior 1 (valid spec passthrough), 2 (file round-trip), 11 (unknown keys)."""

    def test_minimal_valid_spec_passes_and_returns_same_content(self):
        spec = _spec()
        result = parse_level_spec_dict(make_level_spec_container(spec))
        self.assertEqual(result, spec)
        # P6: parsing must never mutate the caller's dict.
        self.assertEqual(spec, _spec())

    def test_container_file_round_trip(self):
        spec = _spec()
        tmp = tempfile.mkdtemp(prefix='aamatch-test-')
        self.addCleanup(shutil.rmtree, tmp)
        path = os.path.join(tmp, 'spec.json')
        save_container(path, 'level_spec', spec)
        result = parse_level_spec_dict(read_json_file(path))
        self.assertEqual(result, spec)

    def test_unknown_keys_preserved_at_every_level(self):
        # P9: additive fields are preserved, not validated away -- Phase 3/7
        # extensions must survive a Phase-1-era reader.
        spec = _spec()
        spec['future_field'] = {'anything': True}
        level = spec['levels'][0]
        level['future'] = 'reserved'
        slot = level['molecules'][0]['grid']['slots'][0]
        slot['future'] = 42
        slot['grid_pose']['rotation'] = [1.0, 0.0, 0.0, 0.0]
        result = parse_level_spec_dict(make_level_spec_container(spec))
        self.assertIs(result['future_field'], spec['future_field'])
        self.assertEqual(result['levels'][0]['future'], 'reserved')
        self.assertEqual(
            result['levels'][0]['molecules'][0]['grid']['slots'][0]['future'], 42)
        self.assertEqual(
            result['levels'][0]['molecules'][0]['grid']['slots'][0]
            ['grid_pose']['rotation'], [1.0, 0.0, 0.0, 0.0])


class TestDetectorVersionExactMatch(unittest.TestCase):
    """Behaviors 3-5 + 12: detector_version refuses ANY mismatch (P4)."""

    def test_stale_detector_refused(self):
        spec = _spec()
        spec['detector_version'] = 'det-0'
        with self.assertRaises(FormatError) as ctx:
            parse_level_spec_dict(make_level_spec_container(spec))
        message = str(ctx.exception)
        self.assertIn('detector', message)
        self.assertIn('stale or newer', message)

    def test_newer_detector_refused(self):
        # P4 regression trap: refuse-newer-only would WRONGLY accept det-2.
        spec = _spec()
        spec['detector_version'] = 'det-2'
        with self.assertRaises(FormatError) as ctx:
            parse_level_spec_dict(make_level_spec_container(spec))
        message = str(ctx.exception)
        self.assertIn('detector', message)
        self.assertIn('stale or newer', message)

    def test_two_version_gates_have_distinct_messages(self):
        newer_detector = _spec()
        newer_detector['detector_version'] = 'det-2'
        with self.assertRaises(FormatError) as ctx:
            parse_level_spec_dict(make_level_spec_container(newer_detector))
        detector_message = str(ctx.exception)

        newer_format = _spec()
        newer_format['format_version'] = LEVEL_SPEC_VERSION + 1
        with self.assertRaises(FormatError) as ctx:
            parse_level_spec_dict(make_level_spec_container(newer_format))
        format_message = str(ctx.exception)

        self.assertNotEqual(detector_message, format_message)
        self.assertIn('stale or newer', detector_message)
        self.assertNotIn('stale or newer', format_message)
        self.assertIn('unsupported level spec version', format_message)

    def test_missing_detector_version_refused(self):
        # Exact-match gate: absence is not 'det-1'.
        spec = _spec()
        del spec['detector_version']
        with self.assertRaises(FormatError) as ctx:
            parse_level_spec_dict(make_level_spec_container(spec))
        self.assertIn('detector', str(ctx.exception))


class TestFormatVersionRefuseNewer(unittest.TestCase):
    """Behaviors 6-7: payload format_version uses the additive policy."""

    def test_newer_format_version_refused(self):
        spec = _spec()
        spec['format_version'] = LEVEL_SPEC_VERSION + 1
        with self.assertRaises(FormatError) as ctx:
            parse_level_spec_dict(make_level_spec_container(spec))
        self.assertIn('unsupported level spec version', str(ctx.exception))

    def test_older_format_version_accepted(self):
        spec = _spec()
        spec['format_version'] = 0
        result = parse_level_spec_dict(make_level_spec_container(spec))
        self.assertEqual(result, spec)

    def test_bogus_format_version_refused_not_crash(self):
        spec = _spec()
        spec['format_version'] = 'not-a-number'
        with self.assertRaises(FormatError) as ctx:
            parse_level_spec_dict(make_level_spec_container(spec))
        self.assertIn('format_version', str(ctx.exception))


class TestStructuralMinimums(unittest.TestCase):
    """Behaviors 8-10: non-empty levels, grid n >= 1, unique slot ids."""

    def test_empty_levels_refused(self):
        spec = _spec()
        spec['levels'] = []
        with self.assertRaises(FormatError) as ctx:
            parse_level_spec_dict(make_level_spec_container(spec))
        self.assertIn('levels', str(ctx.exception))

    def test_levels_not_a_list_refused(self):
        spec = _spec()
        spec['levels'] = {'oops': True}
        with self.assertRaises(FormatError) as ctx:
            parse_level_spec_dict(make_level_spec_container(spec))
        self.assertIn('levels', str(ctx.exception))

    def test_difficulty_grid_n_zero_refused(self):
        spec = _spec()
        spec['levels'][0]['difficulty']['grid_n'] = 0
        with self.assertRaises(FormatError) as ctx:
            parse_level_spec_dict(make_level_spec_container(spec))
        self.assertIn('grid', str(ctx.exception))

    def test_molecule_grid_n_negative_refused(self):
        spec = _spec()
        spec['levels'][0]['molecules'][0]['grid']['n'] = -1
        with self.assertRaises(FormatError) as ctx:
            parse_level_spec_dict(make_level_spec_container(spec))
        self.assertIn('grid', str(ctx.exception))

    def test_duplicate_slot_id_within_one_molecule_refused(self):
        spec = _spec()
        grid = spec['levels'][0]['molecules'][0]['grid']
        duplicate = copy.deepcopy(grid['slots'][0])
        grid['slots'].append(duplicate)  # same slot_id, same molecule
        with self.assertRaises(FormatError) as ctx:
            parse_level_spec_dict(make_level_spec_container(spec))
        self.assertIn('slot', str(ctx.exception))

    def test_same_slot_id_in_different_molecules_accepted(self):
        # Uniqueness scope is PER MOLECULE.
        spec = _two_molecule_spec()
        result = parse_level_spec_dict(make_level_spec_container(spec))
        self.assertEqual(result, spec)


class TestSeedRequired(unittest.TestCase):
    """Behaviors 13-14: seed must be present AND an int (H12 replay)."""

    def test_missing_seed_refused(self):
        spec = _spec()
        del spec['seed']
        with self.assertRaises(FormatError) as ctx:
            parse_level_spec_dict(make_level_spec_container(spec))
        self.assertIn('seed', str(ctx.exception))

    def test_non_int_seed_refused(self):
        # "42" (string), 42.5 (float), None (absent value), True (bool --
        # technically an int subclass but never a valid RNG seed).
        for bad_seed in ('42', 42.5, None, True):
            spec = _spec()
            spec['seed'] = bad_seed
            with self.assertRaises(FormatError) as ctx:
                parse_level_spec_dict(make_level_spec_container(spec))
            self.assertIn('seed', str(ctx.exception),
                          'seed=%r must be refused' % (bad_seed,))


if __name__ == '__main__':
    unittest.main()
