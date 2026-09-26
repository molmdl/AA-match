"""Curated-manifest size-class supply measurement + default-config
generation proof (plan 08-10).

This test is the PERMANENT instrument that answers the question
generator.py's SIZE_S1/S2 comment explicitly deferred to Phase 8
("engineering buckets, tuned when the Phase-8 manifest exists"): does
the FINAL curated manifest carry enough size-class supply for the
generator's bucket machine (small < SIZE_S1(25) <= medium
< SIZE_S2(60) <= large; D >= 3 targets all three classes; NEAREST-BUCKET
fallback when the target pool is EMPTY; a non-empty-but-thin pool
raises GenerationError naming the shortage; binding constraint
len(pool) >= molecules_per_level)?

Measured on the real bundled manifest (data-relative, via the pure
parse chain -- read_json_file -> parse_manifest_dict -> enumerate
_entries; ZERO sys.modules stubs, repo-root anchored from __file__):

    CURATED BUCKET TALLY: small 12 / medium 4 / large 0  (EXPECTED_SUPPLY)
    ALL-SETS tally incl. demo-dev-1's 2 small entries: small 14. That
    difference is EXPECTED, not a failure -- the dev set sits outside
    the 08-04 decision-9 16-curated-ligands contract.

Generation proof: default config (molecules_per_level=2,
difficulty_levels=3, interaction_mode 'unset', allowed []) generates
without GenerationError over ALL sets ('' filter) and over each curated
set EXCEPT three genuinely thin pools whose fail-closed refusals are
PINNED below (refusals-are-correct is itself the assertion).

Pinned thin sets (VERIFIED against generator.py's refusal at the
distinctness raise site -- every seed identical, pool-structure refused
not seed-luck):
- demo-easy-3 (1 entry caffeine) and demo-veryhard-2 (1 entry heme):
  1 distinct candidate cannot fill m=2 distinct picks per level.
- demo-veryhard-1 (folic_acid medium + thyroxine small): the LEVEL-0
  small pool has only thyroxine -- the research-Q8 non-empty-but-thin
  refusal (fallback fires only on an EMPTY target pool). The 08-10
  plan text predicted only the first two (reasoning per-set ENTRY
  count); the measured per-BUCKET pool adds this third. Recorded as a
  plan-text correction in 08-10-SUMMARY.md; the refusal is the
  generator working as designed, NOT a SIZE_S1/S2 re-tune trigger.

Profiles are HAND-BUILT support-capable per the 08-10 plan mandate
(tests/test_generator.py profile() pattern: has_acceptor=True base +
has_halogen_donor/has_metal from the manifest flags): capability can
only SHRINK the unset-mode draw pool, never refuse on capability, so
any refusal in this file is BUCKET-SUPPLY by construction. Do NOT call
capability.ligand_profile here (counts/flags cannot supply atoms/bonds;
a fail-closed reconstructed profile would falsely trigger re-tune
reasoning).

Runs under bare python3.6 in WSL; NO PyMOL involvement (pure generator
over the real manifest).

RE-TUNE TRIGGER (08-10 plan task 2): re-tune SIZE_S1/S2 ONLY if this
file's all-sets default-config generation REFUSES or the medium bucket
falls below 3 (the Q8 minimum-viable floor: default m=2 + headroom at
D>=3). Any such change is permanent-recorded here via EXPECTED_SUPPLY.
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from aamatch.persistence import read_json_file  # noqa: E402
from aamatch.manifest import (  # noqa: E402
    parse_manifest_dict,
    enumerate_entries,
)
from aamatch.generator import (  # noqa: E402
    GenerationError,
    generate,
)
from aamatch.setup_state import validate_state  # noqa: E402

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MANIFEST_PATH = os.path.join(REPO_ROOT, 'aamatch', 'data',
                             'MANIFEST.json')

DEV_SET_ID = 'demo-dev-1'

# The 9 curated set ids of the 08-04 approval (16 curated ligands).
CURATED_SET_IDS = (
    'demo-easy-1', 'demo-easy-2', 'demo-easy-3',
    'demo-hard-1', 'demo-hard-2', 'demo-hard-3',
    'demo-veryhard-1', 'demo-veryhard-2',
    'demo-challenge-1',
)

# The measured curated size-class contract (12 small / 4 medium / 0
# large, 2026-09-26; the medium four are atp 31, nad 44, folic_acid 32,
# heme 43 heavy atoms). Update ONLY in the same commit that changes the
# bundled data.
EXPECTED_SUPPLY = {'small': 12, 'medium': 4, 'large': 0}

# Q8 minimum-viable floor: one bucket needs 3 distinct entries to
# support the default m=2 draw with headroom at D>=3.
MINIMUM_BUCKET_FLOOR = 3

# Default-config constants (frozen setup defaults, 01-09).
DEFAULT_MOLECULES = 2
DEFAULT_DIFFICULTY = 3

# The exact fail-closed refusal for a thin per-level pool (generator.py
# distinctness raise site; identical across seeds -- the pool structure
# is refused, not any draw).
THIN_REFUSAL_SMALL = (
    "size class 'small' (fallback target 'small') has 1 distinct "
    "candidate(s); level 0 needs 2 distinct molecules -- add candidates "
    "or lower molecules_per_level")

# Data-relative per-set expectations at the default config: the three
# thin sets refuse with the pinned message (see module docstring);
# every other curated set generates.
EXPECTED_THIN_REFUSALS = {
    'demo-easy-3': THIN_REFUSAL_SMALL,      # 1 entry (caffeine)
    'demo-veryhard-1': THIN_REFUSAL_SMALL,  # level-0 small pool: only
                                            # thyroxine (folic_acid is
                                            # medium) -- the non-empty-
                                            # but-thin case
    'demo-veryhard-2': THIN_REFUSAL_SMALL,  # 1 entry (heme)
}

# Three architecturally different seeds (generation must be
# pool-structural, never seed-luck).
PROOF_SEEDS = (1, 42, 999)


def _load_rows():
    """The real manifest's enumerate_entries rows (pure parse chain)."""
    payload = parse_manifest_dict(read_json_file(MANIFEST_PATH))
    return enumerate_entries(payload)


def _profile_for(row):
    """Hand-built SUPPORT-CAPABLE profile (test_generator.py profile()
    pattern): has_acceptor base + halogen/metal from manifest flags."""
    return {
        'has_donor': False,
        'has_acceptor': True,
        'charge_signs': set(),
        'ring_count': 0,
        'has_hydrophobe': False,
        'has_halogen_donor': bool(row['halogen_present']),
        'has_metal': bool(row['metal_present']),
    }


def _ligand_data(rows):
    """The 02-08 ligand_data contract keyed by (set_id, entry_id)."""
    return dict(((row['set_id'], row['entry_id']),
                 {'centroid': (0.0, 0.0, 0.0),
                  'radius': 4.0,
                  'profile': _profile_for(row)})
                for row in rows)


def _default_setup():
    """The frozen default config: demo / unset / allowed [] / m=2/D=3."""
    return validate_state({
        'interaction_mode': 'unset',
        'allowed_interactions': [],
        'molecules_per_level': DEFAULT_MOLECULES,
        'difficulty_levels': DEFAULT_DIFFICULTY,
    })


def _bucket_tally(rows):
    """Tally enumerate_entries rows by generator._candidate_class,
    computed DATA-RELATIVE from heavy_atom_count through the same
    derivation the manifest battery pins (size_class reproduced)."""
    from aamatch.generator import _candidate_class
    tally = dict((name, 0) for name in ('small', 'medium', 'large'))
    for row in rows:
        tally[_candidate_class(row)] += 1
    return tally


class TestCuratedBucketSupply(unittest.TestCase):
    """Measure the curated size-class supply of the REAL manifest."""

    @classmethod
    def setUpClass(cls):
        cls.rows = _load_rows()
        cls.set_ids = set(row['set_id'] for row in cls.rows)

    def setUp(self):
        if not set(CURATED_SET_IDS).issubset(self.set_ids):
            self.skipTest('curated sets not bundled yet')

    def _curated_rows(self):
        # Every bundled set EXCEPT demo-dev-1 (the 2 dev entries sit
        # outside the 08-04 16-curated-ligands contract).
        return [row for row in self.rows
                if row['set_id'] != DEV_SET_ID]

    def test_curated_bucket_tally_matches_expected_supply(self):
        curated = self._curated_rows()
        self.assertEqual(len(curated), 16,
                         'the 08-04 approval bundles 16 curated ligands')
        self.assertEqual(sorted(set(row['set_id'] for row in curated)),
                         sorted(CURATED_SET_IDS))
        tally = _bucket_tally(curated)
        # Verbatim measurement line for the SUMMARY record (unbuffered).
        sys.stderr.write(
            'CURATED BUCKET TALLY (measured, 08-10): '
            'small %d / medium %d / large %d\n'
            % (tally['small'], tally['medium'], tally['large']))
        self.assertEqual(tally, EXPECTED_SUPPLY)

    def test_all_sets_tally_includes_dev_set_textually(self):
        # The unfiltered tally = curated tally + demo-dev-1's 2 small
        # entries (14/4/0 unless the bundled data changes) -- that
        # difference is EXPECTED, never a failure.
        all_tally = _bucket_tally(self.rows)
        dev_tally = _bucket_tally(
            [row for row in self.rows if row['set_id'] == DEV_SET_ID])
        for bucket in EXPECTED_SUPPLY:
            self.assertEqual(all_tally[bucket] - dev_tally[bucket],
                             EXPECTED_SUPPLY[bucket],
                             'bucket %r drift outside dev-set growth'
                             % bucket)

    def test_medium_bucket_meets_minimum_viable_floor(self):
        # The Q8 floor: 3 distinct medium entries = default m=2 plus
        # headroom. Dropping below it is the 08-10 re-tune trigger, so
        # it is pinned LOUDLY here rather than absorbed by the tally.
        tally = _bucket_tally(self._curated_rows())
        self.assertGreaterEqual(
            tally['medium'], MINIMUM_BUCKET_FLOOR,
            'medium bucket %d below the Q8 minimum-viable floor %d -- '
            'SIZE_S1/S2 re-tune review required (never silent)'
            % (tally['medium'], MINIMUM_BUCKET_FLOOR))
        for bucket in ('small', 'medium'):
            self.assertGreaterEqual(tally[bucket], MINIMUM_BUCKET_FLOOR,
                                    'bucket %r below the Q8 floor'
                                    % bucket)


class TestDefaultConfigGeneration(unittest.TestCase):
    """Default-config generation over the REAL manifest's supply."""

    @classmethod
    def setUpClass(cls):
        cls.rows = _load_rows()
        cls.set_ids = set(row['set_id'] for row in cls.rows)

    def setUp(self):
        if not set(CURATED_SET_IDS).issubset(self.set_ids):
            self.skipTest('curated sets not bundled yet')

    def _assert_default_payload(self, payload, seed):
        levels = payload['levels']
        self.assertEqual(len(levels), DEFAULT_DIFFICULTY)
        self.assertEqual([level['difficulty']['molecule_size_class']
                          for level in levels],
                         ['small', 'medium', 'large'],
                         'seed %d: the difficulty dict records the '
                         'TARGET class even under bucket fallback'
                         % seed)
        for level_index, level in enumerate(levels):
            self.assertEqual(len(level['molecules']), DEFAULT_MOLECULES,
                             'seed %d level %d molecule count'
                             % (seed, level_index))

    def test_all_sets_default_config_generates(self):
        # ''-filter semantics: every bundled set incl. demo-dev-1. A
        # refusal HERE is a bucket-supply shortage by construction
        # (support-capable profiles) = the plan's re-tune trigger.
        setup = _default_setup()
        ligand_data = _ligand_data(self.rows)
        for seed in PROOF_SEEDS:
            payload = generate(seed, setup, self.rows, ligand_data,
                               DEFAULT_DIFFICULTY)
            self._assert_default_payload(payload, seed)

    def test_curated_only_default_config_generates(self):
        # The curated supply alone (no dev entries) carries default
        # games across all three target buckets via the NEAREST-BUCKET
        # fallback (large -> medium, the designed carrier).
        curated = [row for row in self.rows
                   if row['set_id'] != DEV_SET_ID]
        setup = _default_setup()
        ligand_data = _ligand_data(curated)
        for seed in PROOF_SEEDS:
            payload = generate(seed, setup, curated, ligand_data,
                               DEFAULT_DIFFICULTY)
            self._assert_default_payload(payload, seed)

    def test_per_curated_set_generation_or_pinned_refusal(self):
        # Per-set loop: DATA-RELATIVE, driven by the manifest itself;
        # fail-closed refusals for the thin sets are pinned VERBATIM
        # (refusals-are-correct IS the assertion).
        setup = _default_setup()
        for set_id in CURATED_SET_IDS:
            rows = [row for row in self.rows
                    if row['set_id'] == set_id]
            self.assertTrue(rows, 'curated set %r missing' % set_id)
            ligand_data = _ligand_data(rows)
            for seed in PROOF_SEEDS:
                if set_id in EXPECTED_THIN_REFUSALS:
                    with self.assertRaises(GenerationError) as ctx:
                        generate(seed, setup, rows, ligand_data,
                                 DEFAULT_DIFFICULTY)
                    self.assertEqual(str(ctx.exception),
                                     EXPECTED_THIN_REFUSALS[set_id],
                                     'set %r seed %d refusal wording'
                                     % (set_id, seed))
                else:
                    try:
                        payload = generate(seed, setup, rows,
                                           ligand_data,
                                           DEFAULT_DIFFICULTY)
                    except GenerationError as e:
                        self.fail('curated set %r seed %d refused '
                                  'default-config generation: %s'
                                  % (set_id, seed, e))
                    self._assert_default_payload(payload, seed)


if __name__ == '__main__':
    unittest.main()
