"""Tests for aamatch.manifest -- bundled-data manifest container.

RED-first suite for plan 02-03. Covers:

- 'manifest' as a first-class container kind (additive KINDS change in
  aamatch/persistence.py; refusal messages stay built from KINDS)
- parse_manifest_dict: passthrough of a valid payload (P9) with zero
  mutation (P6); container gate reuses persistence.check_container's
  canonical refusals (foreign magic / newer version / misfiled kind)
- manifest_version gate: missing or > MANIFEST_VERSION refused with
  "unsupported manifest version ... (expected <= 1)"
- per-entry validation: every malformed variant refused with a message
  naming the set, the entry, and the offending field (entry schema is
  the verbatim 02-RESEARCH-materialization.md §3.2 field list)
- set-structure validation (sets list, set_id, entries list)
- enumerate_entries: deterministic flat rows (entry fields + set_id)
  sorted by (set_id, entry_id); input never mutated
- largest_entry: max heavy_atom_count, ties -> first in sorted order

Runs under bare python3.6 in WSL with stdlib only (no pymol/Qt/numpy
stubs needed -- the module under test is pure).
"""

import copy
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from aamatch.persistence import (
    KINDS,
    FormatError,
    check_container,
    make_container,
)
from aamatch.manifest import (
    MANIFEST_VERSION,
    enumerate_entries,
    largest_entry,
    parse_manifest_dict,
)


# --------------------------------------------------------------------------
# Fixtures -- the exact entry schema from 02-RESEARCH-materialization.md §3.2
# --------------------------------------------------------------------------

def _make_entry(**overrides):
    """One valid entry: the verbatim §3.2 schema fields."""
    entry = {
        'entry_id': 'mol-001',
        'file': 'demos/mol-001.sdf',
        'format': 'sdf',
        'sha256': 'a' * 64,
        'protonation': 'as-recorded',
        'atom_count': 8,
        'heavy_atom_count': 4,
        'bond_count': 7,
        'bond_order_counts': {'1': 6, '2': 1},
        'formal_charge_sum': 0,
        'states_expected': 1,
        'metal_present': False,
        'halogen_present': False,
        'size_class': 'small',
    }
    entry.update(overrides)
    return entry


def _make_entry_mol2():
    """Second valid entry (mol2 format, a metal-bearing medium molecule)."""
    return _make_entry(
        entry_id='mol-002',
        file='demos/mol-002.mol2',
        format='mol2',
        sha256='b' * 64,
        atom_count=12,
        heavy_atom_count=6,
        bond_count=11,
        bond_order_counts={'1': 9, '2': 2},
        formal_charge_sum=1,
        metal_present=True,
        size_class='medium',
    )


def _make_set(set_id='demo-easy-1', entries=None, **overrides):
    """One valid set dict (tier/title/license/provenance are Phase-8
    placeholder fields -- preserved, not validated)."""
    set_dict = {
        'set_id': set_id,
        'tier': 'easy',
        'title': 'Phase-2 development set',
        'license': '',
        'provenance': {},
        'entries': [_make_entry(), _make_entry_mol2()]
        if entries is None else entries,
    }
    set_dict.update(overrides)
    return set_dict


def _make_payload():
    """Valid payload: manifest_version=1, one set with 2 entries."""
    return {
        'manifest_version': 1,
        'sets': [_make_set()],
    }


def _wrap(payload, **container_overrides):
    """Wrap a payload in a kind='manifest' container (overrides for the
    header fields lets gate tests forge wrong magic/version/kind)."""
    container = {
        'magic': 'AAMATCH',
        'version': 1,
        'kind': 'manifest',
        'data': payload,
    }
    container.update(container_overrides)
    return container


def _set(**overrides):
    """Entry mutator for assert_entry_refused: override field values."""
    return lambda entry: entry.update(overrides)


def _make_remover(key):
    """Entry mutator for assert_entry_refused: remove one key."""
    def _remove(entry):
        entry.pop(key)
    return _remove


class _EntryRefusalMixin(object):
    """Shared helper: mutate entry 0 of the default set, expect FormatError
    whose message names the offending fragments (set/entry/field)."""

    def assert_entry_refused(self, mutate, *fragments):
        payload = _make_payload()
        mutate(payload['sets'][0]['entries'][0])
        with self.assertRaises(FormatError) as ctx:
            parse_manifest_dict(_wrap(payload))
        message = str(ctx.exception)
        for fragment in fragments:
            self.assertIn(fragment, message,
                          'expected %r in refusal message: %s'
                          % (fragment, message))


# --------------------------------------------------------------------------
# Task 1: 'manifest' is a legal container kind
# --------------------------------------------------------------------------

class TestManifestContainerKind(unittest.TestCase):
    """'manifest' is a first-class container kind (additive KINDS change)."""

    def test_make_container_manifest_succeeds(self):
        container = make_container('manifest', {'manifest_version': 1,
                                                'sets': []})
        self.assertEqual(container['kind'], 'manifest')
        self.assertEqual(container['magic'], 'AAMATCH')

    def test_check_container_accepts_manifest_kind(self):
        container = make_container('manifest', {'manifest_version': 1,
                                                'sets': []})
        result = check_container(container, 'manifest')
        self.assertIs(result, container)

    def test_manifest_in_kinds_tuple(self):
        self.assertIn('manifest', KINDS)

    def test_unknown_kind_still_refused_with_canonical_message(self):
        with self.assertRaises(FormatError) as ctx:
            make_container('bogus', {})
        message = str(ctx.exception)
        self.assertIn('unknown AA-match file kind', message)
        self.assertIn('bogus', message)

    def test_misfiled_kind_still_refused_with_canonical_message(self):
        manifest = make_container('manifest', {})
        with self.assertRaises(FormatError) as ctx:
            check_container(manifest, 'setup')
        self.assertIn('expected an AA-match setup file', str(ctx.exception))


# --------------------------------------------------------------------------
# Task 2: parse_manifest_dict -- container gate + version gate
# --------------------------------------------------------------------------

class TestParseManifestDict(unittest.TestCase):
    """Valid manifests parse passthrough (P9) without mutating (P6)."""

    def test_valid_container_returns_payload_unchanged(self):
        payload = _make_payload()
        result = parse_manifest_dict(_wrap(payload))
        self.assertIs(result, payload)
        self.assertEqual(result, payload)

    def test_parse_never_mutates_input(self):
        payload = _make_payload()
        snapshot = copy.deepcopy(payload)
        parse_manifest_dict(_wrap(payload))
        self.assertEqual(payload, snapshot)

    def test_negative_formal_charge_sum_is_valid(self):
        payload = _make_payload()
        payload['sets'][0]['entries'][0]['formal_charge_sum'] = -1
        result = parse_manifest_dict(_wrap(payload))
        self.assertEqual(
            result['sets'][0]['entries'][0]['formal_charge_sum'], -1)

    def test_unknown_extra_fields_preserved(self):
        payload = _make_payload()
        payload['sets'][0]['entries'][0]['future_field'] = {'x': 1}
        result = parse_manifest_dict(_wrap(payload))
        self.assertEqual(result['sets'][0]['entries'][0]['future_field'],
                         {'x': 1})

    def test_payload_must_be_dict(self):
        with self.assertRaises(FormatError) as ctx:
            parse_manifest_dict(_wrap(['nope']))
        self.assertIn('payload must be a dict', str(ctx.exception))

    def test_manifest_version_constant(self):
        self.assertEqual(MANIFEST_VERSION, 1)


class TestContainerGate(unittest.TestCase):
    """Header refusals reuse persistence.check_container's canonical
    messages -- manifest.py must not duplicate them."""

    def test_wrong_magic_refused(self):
        with self.assertRaises(FormatError) as ctx:
            parse_manifest_dict(_wrap(_make_payload(), magic='NOPE'))
        self.assertIn('not an AA-match file', str(ctx.exception))

    def test_misfiled_kind_refused(self):
        with self.assertRaises(FormatError) as ctx:
            parse_manifest_dict(_wrap(_make_payload(), kind='level_spec'))
        self.assertIn('expected an AA-match manifest file',
                      str(ctx.exception))

    def test_newer_container_version_refused(self):
        with self.assertRaises(FormatError) as ctx:
            parse_manifest_dict(_wrap(_make_payload(), version=2))
        message = str(ctx.exception)
        self.assertIn('unsupported AA-match format version', message)
        self.assertIn('Please update AA-match', message)

    def test_older_container_version_accepted(self):
        result = parse_manifest_dict(_wrap(_make_payload(), version=0))
        self.assertEqual(result['manifest_version'], 1)


class TestManifestVersionGate(unittest.TestCase):
    """manifest_version: refuse-newer / accept-older like FORMAT_VERSION;
    missing or > MANIFEST_VERSION -> the canonical version message."""

    def test_manifest_version_missing_refused(self):
        payload = _make_payload()
        del payload['manifest_version']
        with self.assertRaises(FormatError) as ctx:
            parse_manifest_dict(_wrap(payload))
        message = str(ctx.exception)
        self.assertIn('unsupported manifest version', message)
        self.assertIn('expected <= 1', message)

    def test_manifest_version_newer_refused(self):
        payload = _make_payload()
        payload['manifest_version'] = 2
        with self.assertRaises(FormatError) as ctx:
            parse_manifest_dict(_wrap(payload))
        self.assertIn('unsupported manifest version 2 (expected <= 1)',
                      str(ctx.exception))

    def test_manifest_version_bool_refused(self):
        payload = _make_payload()
        payload['manifest_version'] = True
        with self.assertRaises(FormatError) as ctx:
            parse_manifest_dict(_wrap(payload))
        self.assertIn('unsupported manifest version', str(ctx.exception))


# --------------------------------------------------------------------------
# Task 2: set + entry validation (every refusal names set/entry/field)
# --------------------------------------------------------------------------

class TestSetStructure(unittest.TestCase):

    def test_sets_must_be_a_list(self):
        with self.assertRaises(FormatError) as ctx:
            parse_manifest_dict(_wrap({'manifest_version': 1, 'sets': {}}))
        self.assertIn('sets', str(ctx.exception))

    def test_set_must_be_a_dict(self):
        payload = _make_payload()
        payload['sets'][0] = 'nope'
        with self.assertRaises(FormatError) as ctx:
            parse_manifest_dict(_wrap(payload))
        self.assertIn('sets[0]', str(ctx.exception))

    def test_set_id_must_be_nonempty_string(self):
        for bad in ('', 7, None):
            payload = _make_payload()
            payload['sets'][0]['set_id'] = bad
            with self.assertRaises(FormatError) as ctx:
                parse_manifest_dict(_wrap(payload))
            self.assertIn('set_id', str(ctx.exception))

    def test_entries_must_be_a_list(self):
        payload = _make_payload()
        payload['sets'][0]['entries'] = 'nope'
        with self.assertRaises(FormatError) as ctx:
            parse_manifest_dict(_wrap(payload))
        self.assertIn('entries', str(ctx.exception))


class TestEntryValidation(_EntryRefusalMixin, unittest.TestCase):
    """Every malformed entry variant is refused; the message names the
    entry (entry_id) and the offending field."""

    def test_missing_required_key_refused_and_named(self):
        self.assert_entry_refused(
            lambda entry: entry.pop('sha256'),
            'mol-001', 'sha256', 'missing')

    def test_every_required_key_is_required(self):
        required = ['entry_id', 'file', 'format', 'sha256', 'protonation',
                    'atom_count', 'heavy_atom_count', 'bond_count',
                    'bond_order_counts', 'formal_charge_sum',
                    'states_expected', 'metal_present', 'halogen_present',
                    'size_class']
        for key in required:
            with self.subTest(key=key):
                self.assert_entry_refused(
                    _make_remover(key), key, 'missing')

    def test_entry_not_a_dict_refused(self):
        payload = _make_payload()
        payload['sets'][0]['entries'][0] = 'nope'
        with self.assertRaises(FormatError) as ctx:
            parse_manifest_dict(_wrap(payload))
        message = str(ctx.exception)
        self.assertIn('demo-easy-1', message)
        self.assertIn('entries[0]', message)

    def test_entry_id_must_be_nonempty_string(self):
        for bad in (5, '', None):
            with self.subTest(entry_id=bad):
                self.assert_entry_refused(_set(entry_id=bad),
                                          'entry_id', 'demo-easy-1')

    def test_format_must_be_sdf_or_mol2(self):
        self.assert_entry_refused(_set(format='smi'),
                                  'format', 'smi', 'mol-001')

    def test_format_is_case_sensitive(self):
        self.assert_entry_refused(_set(format='SDF'), 'format', 'SDF')

    def test_sha256_must_be_64_lowercase_hex(self):
        for bad in ('A' * 64, 'a' * 63, 'g' * 64, 123, 'a' * 64 + 'extra'):
            with self.subTest(sha256=str(bad)[:16]):
                self.assert_entry_refused(_set(sha256=bad), 'sha256')

    def test_count_fields_must_be_real_ints(self):
        cases = [
            ('atom_count', True), ('atom_count', 8.0), ('atom_count', '8'),
            ('bond_count', True), ('bond_count', '7'),
            ('heavy_atom_count', None), ('heavy_atom_count', 4.5),
            ('states_expected', False), ('states_expected', 1.5),
        ]
        for key, value in cases:
            with self.subTest(key=key, value=value):
                self.assert_entry_refused(_set(**{key: value}), key)

    def test_bond_order_counts_must_be_dict(self):
        self.assert_entry_refused(_set(bond_order_counts=[('1', 6)]),
                                  'bond_order_counts')

    def test_bond_order_counts_keys_must_be_digit_strings(self):
        for bad in ({'one': 6}, {1: 6}, {'': 6}, {'1.0': 6}, {'-1': 6}):
            with self.subTest(key=repr(list(bad)[0])):
                self.assert_entry_refused(
                    _set(bond_order_counts=bad), 'bond_order_counts')

    def test_bond_order_counts_values_must_be_positive_ints(self):
        for bad in (0, -1, True, '6', 2.0):
            with self.subTest(value=bad):
                self.assert_entry_refused(
                    _set(bond_order_counts={'1': bad}),
                    'bond_order_counts')

    def test_formal_charge_sum_must_be_int(self):
        for bad in (-1.0, True, '0', None):
            with self.subTest(formal_charge_sum=bad):
                self.assert_entry_refused(
                    _set(formal_charge_sum=bad), 'formal_charge_sum')

    def test_size_class_must_be_small_medium_or_large(self):
        for bad in ('tiny', 'SMALL', '', None):
            with self.subTest(size_class=bad):
                self.assert_entry_refused(_set(size_class=bad), 'size_class')

    def test_flag_fields_must_be_real_bools(self):
        for key in ('metal_present', 'halogen_present'):
            for bad in (1, 0, 'yes', None):
                with self.subTest(key=key, value=bad):
                    self.assert_entry_refused(_set(**{key: bad}), key)

    def test_file_backslash_refused(self):
        self.assert_entry_refused(_set(file='demos\\mol-001.sdf'),
                                  'file', 'forward slash')

    def test_file_absolute_posix_refused(self):
        self.assert_entry_refused(_set(file='/abs/mol-001.sdf'),
                                  'file', 'absolute')

    def test_file_windows_drive_refused(self):
        self.assert_entry_refused(_set(file='C:/demos/mol-001.sdf'),
                                  'file', 'Windows drive')

    def test_file_must_be_nonempty_string(self):
        for bad in ('', 42, None):
            with self.subTest(file=bad):
                self.assert_entry_refused(_set(file=bad), 'file')


# --------------------------------------------------------------------------
# Task 2: enumerate_entries + largest_entry
# --------------------------------------------------------------------------

class TestEnumerateEntries(unittest.TestCase):

    @staticmethod
    def _two_set_payload():
        """Sets and entries deliberately OUT of sorted order."""
        set_b = _make_set(set_id='set-b', tier='hard', title='B', entries=[
            _make_entry(entry_id='mol-002', file='demos/b2.sdf'),
            _make_entry(entry_id='mol-001', file='demos/b1.sdf'),
        ])
        set_a = _make_set(set_id='set-a', tier='easy', title='A', entries=[
            _make_entry(entry_id='mol-002', file='demos/a2.sdf'),
            _make_entry(entry_id='mol-001', file='demos/a1.sdf'),
        ])
        return {'manifest_version': 1, 'sets': [set_b, set_a]}

    def test_flattens_entries_with_set_id_added(self):
        rows = enumerate_entries(_make_payload())
        self.assertEqual(len(rows), 2)
        first = rows[0]
        self.assertEqual(first['set_id'], 'demo-easy-1')
        self.assertEqual(first['entry_id'], 'mol-001')
        self.assertEqual(first['format'], 'sdf')
        self.assertEqual(first['atom_count'], 8)
        expected_keys = set(_make_entry().keys()) | {'set_id'}
        for row in rows:
            self.assertEqual(set(row.keys()), expected_keys)

    def test_rows_sorted_by_set_then_entry(self):
        rows = enumerate_entries(self._two_set_payload())
        order = [(row['set_id'], row['entry_id']) for row in rows]
        self.assertEqual(
            order,
            [('set-a', 'mol-001'), ('set-a', 'mol-002'),
             ('set-b', 'mol-001'), ('set-b', 'mol-002')])

    def test_deterministic_across_calls(self):
        payload = self._two_set_payload()
        self.assertEqual(enumerate_entries(payload),
                         enumerate_entries(payload))

    def test_input_payload_never_mutated(self):
        payload = self._two_set_payload()
        snapshot = copy.deepcopy(payload)
        rows = enumerate_entries(payload)
        self.assertEqual(payload, snapshot)
        for set_dict in payload['sets']:
            for entry in set_dict['entries']:
                self.assertNotIn('set_id', entry)
        input_entries = [entry for set_dict in payload['sets']
                         for entry in set_dict['entries']]
        for row in rows:
            for entry in input_entries:
                self.assertIsNot(row, entry)


class TestLargestEntry(unittest.TestCase):
    """The perf-smoke (DETECT-05) target selector: derived from entries,
    never a special-cased manifest field."""

    def test_selects_max_heavy_atom_count(self):
        entries = [
            _make_entry(entry_id='mol-001', heavy_atom_count=4),
            _make_entry(entry_id='mol-002', heavy_atom_count=12),
            _make_entry(entry_id='mol-003', heavy_atom_count=9),
        ]
        best = largest_entry(entries)
        self.assertEqual(best['entry_id'], 'mol-002')
        self.assertIs(best, entries[1])

    def test_tie_returns_first_in_given_order(self):
        entries = [
            _make_entry(entry_id='mol-001', heavy_atom_count=10),
            _make_entry(entry_id='mol-002', heavy_atom_count=10),
            _make_entry(entry_id='mol-003', heavy_atom_count=5),
        ]
        best = largest_entry(entries)
        self.assertEqual(best['entry_id'], 'mol-001')

    def test_empty_list_returns_none(self):
        self.assertIsNone(largest_entry([]))

    def test_works_on_enumerate_output(self):
        rows = enumerate_entries(_make_payload())
        best = largest_entry(rows)
        self.assertEqual(best['entry_id'], 'mol-002')  # heavy 6 vs 4


if __name__ == '__main__':
    unittest.main()
