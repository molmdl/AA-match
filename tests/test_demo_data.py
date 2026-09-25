"""Data-integrity battery over the REAL bundled manifest (plan 08-01).

The WSL-side half of SMOKE-02: reads aamatch/data/MANIFEST.json through
the pure parse chain (persistence.read_json_file + manifest
parse_manifest_dict) with ZERO sys.modules stubs and cross-checks every
entry against the committed ligand bytes. The battery is DATA-RELATIVE by
construction -- loop-driven over whatever sets/entries the manifest
carries, never per-set literals -- so it automatically covers the curated
sets landing in 08-05..08-07 (and it is why this file may NOT be relaxed
when those land: every curated set must satisfy the semantics test).

Deliberate scope decisions (08-RESEARCH Q5 binding verdict):
- The runtime validator (aamatch/manifest.py) is NOT grown here: adding
  REQUIRED runtime validation would violate refuse-newer/accept-older.
  Truthfulness of license/provenance is the GATE + DATA_SOURCES.md's
  job; this battery pins the mechanical floor (non-empty, vocabulary).
- Builder syntax is checked via compile() in-memory (no pyc writes, no
  subprocess) -- the py3.6 floor applies to scripts/ too.

Runs under bare python3.6 in WSL. Repo root anchored from __file__
(unit tests may use __file__; only smokes may not).
"""

import hashlib
import json
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from aamatch.persistence import read_json_file  # noqa: E402
from aamatch.manifest import (  # noqa: E402
    parse_manifest_dict,
    REQUIRED_ENTRY_KEYS,
)
from aamatch.generator import _candidate_class  # noqa: E402

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(REPO_ROOT, 'aamatch', 'data')
MANIFEST_PATH = os.path.join(DATA_DIR, 'MANIFEST.json')
SPECS_DIR = os.path.join(REPO_ROOT, 'scripts', 'demo_specs')
BUILDER_PATH = os.path.join(REPO_ROOT, 'scripts', 'build_demos.py')

DEV_SET_ID = 'demo-dev-1'
# Canonical curated tier vocabulary (pinned per 08-01-PLAN must_haves;
# the builder's TIERS tuple is the same list at its single home -- this
# literal is the battery's independent pin).
CURATED_TIERS = ('easy', 'hard', 'challenge', 'very_challenging')


def _load_payload():
    """The committed manifest payload via the pure parse chain."""
    return parse_manifest_dict(read_json_file(MANIFEST_PATH))


def _spec_path(set_id):
    return os.path.join(SPECS_DIR, '%s.json' % set_id)


def _load_spec(set_id):
    with open(_spec_path(set_id), 'rb') as fh:
        return json.loads(fh.read().decode('utf-8'))


class TestDemoData(unittest.TestCase):
    """The 10-check data-integrity battery (08-01-PLAN task 2)."""

    @classmethod
    def setUpClass(cls):
        cls.payload = _load_payload()
        cls.sets = cls.payload.get('sets', [])
        cls.set_by_id = {s['set_id']: s for s in cls.sets}

    # -- 1: manifest container parses -----------------------------------
    def test_01_manifest_container_parses(self):
        self.assertEqual(self.payload.get('manifest_version'), 1)
        self.assertIsInstance(self.sets, list)
        self.assertTrue(self.sets,
                        'manifest must carry at least one bundled set')

    # -- 2: every entry file exists + sha256 matches --------------------
    def test_02_entry_files_exist_and_sha256_match(self):
        for set_dict in self.sets:
            for entry in set_dict['entries']:
                path = os.path.join(
                    DATA_DIR, entry['file'].replace('/', os.sep))
                self.assertTrue(
                    os.path.isfile(path),
                    'missing bundled ligand file %r for set %r entry %r'
                    % (entry['file'], set_dict['set_id'], entry['entry_id']))
                with open(path, 'rb') as fh:
                    digest = hashlib.sha256(fh.read()).hexdigest()
                self.assertEqual(
                    digest, entry['sha256'],
                    'sha256 mismatch for %r (set %r entry %r): disk %s '
                    'vs manifest %s -- NEVER hand-edit; regenerate via '
                    'scripts/build_demos.py'
                    % (entry['file'], set_dict['set_id'], entry['entry_id'],
                       digest, entry['sha256']))

    # -- 3: exactly the 14 REQUIRED_ENTRY_KEYS, both directions ---------
    def test_03_exactly_required_entry_keys(self):
        required = set(REQUIRED_ENTRY_KEYS)
        for set_dict in self.sets:
            for entry in set_dict['entries']:
                self.assertEqual(
                    set(entry.keys()), required,
                    'entry %r of set %r has keys %s, expected exactly %s'
                    % (entry['entry_id'], set_dict['set_id'],
                       sorted(entry.keys()), sorted(required)))

    # -- 4: single-record law -------------------------------------------
    def test_04_states_expected_is_one(self):
        for set_dict in self.sets:
            for entry in set_dict['entries']:
                self.assertEqual(
                    entry['states_expected'], 1,
                    'entry %r of set %r has states_expected %r -- '
                    'multi-record sources must be split at curation time'
                    % (entry['entry_id'], set_dict['set_id'],
                       entry['states_expected']))

    # -- 5: bond_order_counts totals the bond count ---------------------
    def test_05_bond_order_counts_sum_to_bond_count(self):
        for set_dict in self.sets:
            for entry in set_dict['entries']:
                total = sum(entry['bond_order_counts'].values())
                self.assertEqual(
                    total, entry['bond_count'],
                    'entry %r of set %r: bond_order_counts %r total %d '
                    '!= bond_count %d'
                    % (entry['entry_id'], set_dict['set_id'],
                       entry['bond_order_counts'], total,
                       entry['bond_count']))

    # -- 6: size_class matches the generator's single bucket home -------
    def test_06_size_class_reproduces_candidate_class(self):
        for set_dict in self.sets:
            for entry in set_dict['entries']:
                derived = _candidate_class(
                    {'heavy_atom_count': entry['heavy_atom_count']})
                self.assertEqual(
                    derived, entry['size_class'],
                    'entry %r of set %r: heavy_atom_count %d buckets as '
                    '%r but manifest says %r -- regenerate'
                    % (entry['entry_id'], set_dict['set_id'],
                       entry['heavy_atom_count'], derived,
                       entry['size_class']))

    # -- 7: forward-slash package-relative file --------------------------
    def test_07_file_is_forward_slash_package_relative(self):
        for set_dict in self.sets:
            for entry in set_dict['entries']:
                file_rel = entry['file']
                self.assertIn(
                    '/', file_rel,
                    'entry %r of set %r: file %r is not a package-relative '
                    'path' % (entry['entry_id'], set_dict['set_id'],
                              file_rel))
                self.assertNotIn(
                    '\\', file_rel,
                    'entry %r of set %r: file %r uses backslashes'
                    % (entry['entry_id'], set_dict['set_id'], file_rel))
                self.assertFalse(
                    os.path.isabs(file_rel),
                    'entry %r of set %r: file %r is absolute'
                    % (entry['entry_id'], set_dict['set_id'], file_rel))

    # -- 8: curated-set semantics (dev set exempt) ----------------------
    def test_08_curated_set_semantics(self):
        for set_dict in self.sets:
            if set_dict['set_id'] == DEV_SET_ID:
                continue
            set_id = set_dict['set_id']
            self.assertTrue(
                set_dict.get('license'),
                'curated set %r has empty license' % set_id)
            self.assertIsInstance(
                set_dict.get('provenance'), dict,
                'curated set %r provenance must be a dict' % set_id)
            self.assertTrue(
                set_dict.get('provenance'),
                'curated set %r has empty provenance' % set_id)
            self.assertTrue(
                set_dict.get('title'),
                'curated set %r has empty title' % set_id)
            self.assertIn(
                set_dict.get('tier'), CURATED_TIERS,
                'curated set %r tier %r outside canonical vocabulary %s'
                % (set_id, set_dict.get('tier'), list(CURATED_TIERS)))
            # Provenance DEPTH lives in the spec (the single home of
            # citations); manifest entries stay 14-key (test 03).
            spec = _load_spec(set_id)
            for spec_entry in spec['entries']:
                prov = spec_entry.get('provenance', {})
                for key in ('source_url', 'notes', 'pdb_id'):
                    self.assertTrue(
                        prov.get(key),
                        'curated set %r entry %r: provenance %r is empty '
                        '-- citations are a data requirement'
                        % (set_id, spec_entry['entry_id'], key))

    # -- 9: spec coverage (every curated set backed by a committed spec) --
    def test_09_spec_coverage(self):
        for set_dict in self.sets:
            if set_dict['set_id'] == DEV_SET_ID:
                continue
            set_id = set_dict['set_id']
            self.assertTrue(
                os.path.isfile(_spec_path(set_id)),
                'curated set %r has no committed spec at '
                'scripts/demo_specs/%s.json' % (set_id, set_id))
            spec = _load_spec(set_id)
            self.assertEqual(
                spec.get('set_id'), set_id,
                'spec %s.json set_id %r != manifest set_id %r'
                % (set_id, spec.get('set_id'), set_id))
            spec_files = {}
            for spec_entry in spec['entries']:
                spec_files[spec_entry['entry_id']] = (
                    spec_entry.get('file')
                    or 'ligands/%s-%s.sdf' % (set_id,
                                              spec_entry['entry_id']))
            manifest_files = {e['entry_id']: e['file']
                              for e in set_dict['entries']}
            self.assertEqual(
                set(spec_files), set(manifest_files),
                'spec vs manifest entry_id drift for set %r: %s vs %s'
                % (set_id, sorted(spec_files), sorted(manifest_files)))
            for entry_id, file_rel in spec_files.items():
                self.assertEqual(
                    manifest_files[entry_id], file_rel,
                    'spec vs manifest file drift for set %r entry %r: '
                    '%r vs %r'
                    % (set_id, entry_id, file_rel, manifest_files[entry_id]))

    # -- 10: builder syntax floor (py3.6; in-memory compile, no pyc) ----
    def test_10_builder_syntax_floor(self):
        with open(BUILDER_PATH, 'rb') as fh:
            source = fh.read().decode('utf-8')
        try:
            compile(source, BUILDER_PATH, 'exec')
        except SyntaxError as exc:
            self.fail('scripts/build_demos.py fails the python3.6 syntax '
                      'floor: %s' % exc)


if __name__ == '__main__':
    unittest.main()
