"""Tests for aamatch.persistence -- versioned container core + atomic JSON I/O.

RED-first suite for plan 01-02 (PERSIST-01 format discipline). Covers:

- container construction (magic/version/kind/data, exact shape)
- all three refusal classes with message assertions
  (foreign magic / unsupported newer version / misfiled kind)
- older-version acceptance (refuse-newer / accept-older policy)
- atomic JSON writes: round-trip exactness, no .tmp litter, failure
  simulation leaves the original intact, NaN refusal, byte stability

Runs under bare python3.6 in WSL with stdlib only (no pymol/Qt/numpy
stubs needed -- the module under test is pure).
"""

import glob
import os
import shutil
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from aamatch.persistence import (
    AAM_MAGIC,
    FORMAT_VERSION,
    KINDS,
    FormatError,
    check_container,
    load_container,
    make_container,
    read_json_file,
    save_container,
    write_json_atomic,
)


class TestModuleContract(unittest.TestCase):
    """Module constants and exception contract."""

    def test_constants(self):
        self.assertEqual(AAM_MAGIC, 'AAMATCH')
        self.assertEqual(FORMAT_VERSION, 1)
        self.assertEqual(KINDS, ('setup', 'level_spec', 'game',
                                 'checkpoint', 'manifest'))

    def test_format_error_is_value_error(self):
        self.assertTrue(issubclass(FormatError, ValueError))


class TestMakeContainer(unittest.TestCase):
    """Container construction (behaviors 1-2)."""

    def test_exact_shape(self):
        self.assertEqual(
            make_container('setup', {'a': 1}),
            {'magic': 'AAMATCH', 'version': 1, 'kind': 'setup', 'data': {'a': 1}},
        )

    def test_bogus_kind_refused_with_message_mentioning_kind(self):
        with self.assertRaises(FormatError) as ctx:
            make_container('bogus', {'a': 1})
        self.assertIn('kind', str(ctx.exception))

    def test_every_known_kind_accepted(self):
        for kind in KINDS:
            container = make_container(kind, {})
            self.assertEqual(container['kind'], kind)


class TestCheckContainer(unittest.TestCase):
    """Container validation and refusal classes (behaviors 3-8)."""

    def test_valid_container_returned_unchanged(self):
        data = {'a': 1}
        container = make_container('setup', data)
        result = check_container(container, 'setup')
        self.assertEqual(result, container)
        self.assertEqual(set(result.keys()), {'magic', 'version', 'kind', 'data'})

    def test_foreign_dict_refused_with_magic_message(self):
        with self.assertRaises(FormatError) as ctx:
            check_container({'nope': 1}, 'setup')
        self.assertIn('not an AA-match file', str(ctx.exception))

    def test_newer_version_refused_with_update_message(self):
        newer = {'magic': AAM_MAGIC, 'version': 999, 'kind': 'setup', 'data': {}}
        with self.assertRaises(FormatError) as ctx:
            check_container(newer, 'setup')
        message = str(ctx.exception)
        self.assertIn('unsupported', message)
        self.assertIn('Please update AA-match', message)

    def test_misfiled_kind_refused_with_expected_kind_message(self):
        level_spec = make_container('level_spec', {'levels': []})
        with self.assertRaises(FormatError) as ctx:
            check_container(level_spec, 'setup')
        self.assertIn('expected an AA-match setup file', str(ctx.exception))

    def test_older_version_accepted(self):
        # refuse-newer / accept-older policy: version < FORMAT_VERSION loads.
        older = {'magic': AAM_MAGIC, 'version': FORMAT_VERSION - 1,
                 'kind': 'setup', 'data': {'legacy': True}}
        result = check_container(older, 'setup')
        self.assertEqual(result, older)

    def test_corrupt_version_field_refused_not_crash(self):
        # A non-numeric version must yield a clear FormatError, not a bare
        # TypeError/ValueError from int().
        for bad in ('abc', None):
            payload = {'magic': AAM_MAGIC, 'version': bad, 'kind': 'setup',
                       'data': {}}
            with self.assertRaises(FormatError) as ctx:
                check_container(payload, 'setup')
            self.assertIn('version', str(ctx.exception))


class TestAtomicJsonIO(unittest.TestCase):
    """write_json_atomic / read_json_file behavior (behaviors 9-14)."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix='aamatch-test-')
        self.addCleanup(shutil.rmtree, self.tmp)

    def test_round_trip_exact(self):
        # Exact equality after load (NEVER assertAlmostEqual): nested dict,
        # unicode strings, boundary ints.
        payload = {
            'label': 'αβγ ↔ Ω',
            'text': '日本語 ✓',
            'nested': {
                'list': [1, 0, -2147483648, 2147483647],
                'float': 0.1234567890123456789,
                'deep': {'empty': {}, 'none': None, 'flag': True},
            },
        }
        path = os.path.join(self.tmp, 'roundtrip.json')
        write_json_atomic(path, payload)
        self.assertEqual(read_json_file(path), payload)

    def test_garbage_file_refused_with_parse_message(self):
        path = os.path.join(self.tmp, 'garbage.json')
        with open(path, 'wb') as fh:
            fh.write(b'{ this is not json ~~')
        with self.assertRaises(FormatError) as ctx:
            read_json_file(path)
        self.assertIn('could not parse AA-match JSON', str(ctx.exception))

    def test_no_tmp_litter_after_success(self):
        path = os.path.join(self.tmp, 'clean.json')
        write_json_atomic(path, {'ok': True})
        litter = glob.glob(os.path.join(self.tmp, '.aam_*.tmp'))
        self.assertEqual(litter, [])
        self.assertEqual(os.listdir(self.tmp), ['clean.json'])

    def test_failure_sim_keeps_original_and_no_litter(self):
        path = os.path.join(self.tmp, 'game.json')
        original = {'marker': 'original'}
        write_json_atomic(path, original)
        with open(path, 'rb') as fh:
            before = fh.read()
        with mock.patch('os.replace', side_effect=OSError('boom')):
            with self.assertRaises(OSError):
                write_json_atomic(path, {'marker': 'new'})
        with open(path, 'rb') as fh:
            self.assertEqual(fh.read(), before)
        self.assertEqual(glob.glob(os.path.join(self.tmp, '.aam_*.tmp')), [])

    def test_nan_refused(self):
        path = os.path.join(self.tmp, 'nan.json')
        with self.assertRaises(ValueError):
            write_json_atomic(path, {'bad': float('nan')})
        self.assertFalse(os.path.exists(path))

    def test_byte_stable_output(self):
        # sort_keys makes output byte-identical regardless of insertion order.
        first = os.path.join(self.tmp, 'a.json')
        second = os.path.join(self.tmp, 'b.json')
        write_json_atomic(first, {'b': 2, 'a': 1, 'c': {'z': 26, 'y': 25}})
        write_json_atomic(second, {'c': {'y': 25, 'z': 26}, 'a': 1, 'b': 2})
        with open(first, 'rb') as fh:
            bytes_first = fh.read()
        with open(second, 'rb') as fh:
            bytes_second = fh.read()
        self.assertEqual(bytes_first, bytes_second)


class TestContainerFileRoundTrip(unittest.TestCase):
    """save_container / load_container transparency (behavior 15)."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix='aamatch-test-')
        self.addCleanup(shutil.rmtree, self.tmp)

    def test_save_load_round_trip_returns_data(self):
        path = os.path.join(self.tmp, 'setup.json')
        data = {'molecules_per_level': 2, 'label': 'ève'}
        save_container(path, 'setup', data)
        self.assertEqual(load_container(path, 'setup'), data)

    def test_saved_file_carries_versioned_header(self):
        path = os.path.join(self.tmp, 'setup.json')
        save_container(path, 'setup', {'a': 1})
        on_disk = read_json_file(path)
        self.assertEqual(on_disk['magic'], AAM_MAGIC)
        self.assertEqual(on_disk['version'], FORMAT_VERSION)
        self.assertEqual(on_disk['kind'], 'setup')


if __name__ == '__main__':
    unittest.main()
