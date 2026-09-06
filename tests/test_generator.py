"""Unit tests for aamatch.generator -- the pure seeded level generator.

The generator is the game brain's producer side (plan 02-08): difficulty
expression (GEN-05), grid geometry (GEN-03), required-set derivation with
the approved OQ-1 mode semantics (docs/DETECTION_THRESHOLDS.md §4.3),
solvability-by-construction slot allocation (GEN-04), and payload
assembly with version stamps + deterministic RNG (GEN-01). Its payload is
what materialization (02-13), E2E (02-14) and Reset replay forever after.

Mode semantics and the hydrophobic sampling exclusion are transcribed
from the APPROVED gate document (docs/DETECTION_THRESHOLDS.md, approved
2026-09-06): OQ-1 (§4.3) binds derive_required, OQ-5 (§4.5) excludes
hydrophobic from unset-mode sampling. Grid geometry follows generation
research §5; difficulty follows §6 (integer half-up interpolation, NO
banker's rounding); RNG discipline follows §7 (randint/choice/sample/
shuffle over sorted/fixed-order lists only).

Runs under bare python3.6, stdlib only, zero stubs. generator must import
only `math`, `random` and pure aamatch modules (purity Gate A; registered
in tests/test_purity.py PURE_MODULES by Task 3).
"""

import math
import random
import unittest

from aamatch import generator
from aamatch.generator import (
    GenerationError,
    GRID_SPACING,
    GAP_MARGIN,
    INTER_GRID_MARGIN,
    difficulty_params,
    placement_offset,
    slot_position,
)

EPS = 1e-9


def close(a, b, eps=EPS):
    """Absolute-distance comparison for float assertions."""
    return abs(a - b) <= eps


class TestDifficultyMapping(unittest.TestCase):
    """GEN-05: integer half-up interpolation over all 10 legal D values.

    The mapping must never use banker's rounding (round(2.5) == 2 would
    make the middle tier asymmetric); the plan pins INTEGER HALF-UP:
    frac = (L*GRID_SPAN + (D-1)//2) // (D-1) for D > 1, else 0.
    """

    def test_every_legal_D_yields_exactly_D_levels_with_tiers_0_to_D_minus_1(self):
        for D in range(1, 11):
            tiers = [difficulty_params(D, L)['tier'] for L in range(D)]
            self.assertEqual(tiers, list(range(D)),
                             'D=%d must yield tiers 0..%d' % (D, D - 1))

    def test_grid_n_monotonic_non_decreasing_within_3_to_9(self):
        for D in range(1, 11):
            ns = [difficulty_params(D, L)['grid_n'] for L in range(D)]
            for n in ns:
                self.assertTrue(3 <= n <= 9,
                                'D=%d grid_n %r outside 3..9' % (D, n))
            for a, b in zip(ns, ns[1:]):
                self.assertLessEqual(a, b,
                                     'D=%d grid_n not monotonic: %r' % (D, ns))

    def test_n_required_types_monotonic_non_decreasing_within_1_to_7(self):
        for D in range(1, 11):
            ks = [difficulty_params(D, L)['n_required_types']
                  for L in range(D)]
            for k in ks:
                self.assertTrue(1 <= k <= 7,
                                'D=%d n_required_types %r outside 1..7'
                                % (D, k))
            for a, b in zip(ks, ks[1:]):
                self.assertLessEqual(a, b,
                                     'D=%d types not monotonic: %r' % (D, ks))

    def test_size_class_rank_monotonic_and_in_enum(self):
        rank = {'small': 0, 'medium': 1, 'large': 2}
        for D in range(1, 11):
            classes = [difficulty_params(D, L)['molecule_size_class']
                       for L in range(D)]
            for c in classes:
                self.assertIn(c, rank, 'D=%d unknown size class %r' % (D, c))
            ranks = [rank[c] for c in classes]
            for a, b in zip(ranks, ranks[1:]):
                self.assertLessEqual(a, b,
                                     'D=%d size class not monotonic: %r'
                                     % (D, classes))

    def test_D1_single_easiest_level(self):
        params = difficulty_params(1, 0)
        self.assertEqual(params['tier'], 0)
        self.assertEqual(params['grid_n'], 3)
        self.assertEqual(params['n_required_types'], 1)
        self.assertEqual(params['molecule_size_class'], 'small')

    def test_D3_reference_rows(self):
        # Generation research §6 reference table, D=3 column. Asserted via
        # computed values; if the formula disagreed with these rows the
        # FORMULA WINS (plan instruction) -- it does not: they agree.
        expected = [
            (0, 3, 1, 'small'),
            (1, 6, 4, 'medium'),
            (2, 9, 7, 'large'),
        ]
        for L, grid_n, types, size in expected:
            params = difficulty_params(3, L)
            self.assertEqual(params['tier'], L)
            self.assertEqual(params['grid_n'], grid_n,
                             'D=3 L=%d grid_n' % L)
            self.assertEqual(params['n_required_types'], types,
                             'D=3 L=%d types' % L)
            self.assertEqual(params['molecule_size_class'], size,
                             'D=3 L=%d size class' % L)

    def test_D10_top_tier_is_max_grid_and_types(self):
        params = difficulty_params(10, 9)
        self.assertEqual(params['grid_n'], 9)
        self.assertEqual(params['n_required_types'], 7)
        self.assertEqual(params['molecule_size_class'], 'large')

    def test_payload_has_reserved_difficulty_keys_only(self):
        params = difficulty_params(3, 1)
        self.assertEqual(sorted(params),
                         ['grid_n', 'molecule_size_class',
                          'n_required_types', 'tier'])

    def test_no_round_call_in_generator_source(self):
        # Mechanical pin of the "never banker's rounding" rule: the token
        # 'round(' must not appear anywhere in generator.py (prose uses
        # "half-up"/"rounding" wording instead, so this cannot false-fire
        # on the docstring by accident).
        with open('aamatch/generator.py', 'rb') as f:
            source = f.read().decode('utf-8')
        self.assertNotIn(
            'round(', source,
            'generator.py must not use round(): banker\'s rounding makes '
            'the middle difficulty tier asymmetric -- integer half-up '
            'arithmetic only')


class TestGridGeometry(unittest.TestCase):
    """GEN-03: the deterministic flat-plane grid (generation research §5)."""

    def test_n3_first_slot_exact_reference(self):
        # n=3, centroid (0,0,0), R=4: slot(0,0) = (-8.0, -8.0, 9.0)
        # (spacing 8.0, plane at cz + R + GAP_MARGIN = 0 + 4 + 5).
        pos = slot_position(0, 0, 3, (0.0, 0.0, 0.0), 4.0)
        self.assertEqual(len(pos), 3)
        for got, want in zip(pos, (-8.0, -8.0, 9.0)):
            self.assertTrue(close(got, want),
                            'slot(0,0) %r != (-8.0, -8.0, 9.0)' % (pos,))

    def test_grid_centered_on_centroid_xy(self):
        n = 4
        centroid = (10.0, -5.0, 2.0)
        R = 3.0
        xs = [slot_position(0, c, n, centroid, R)[0] for c in range(n)]
        ys = [slot_position(r, 0, n, centroid, R)[1] for r in range(n)]
        self.assertTrue(close(min(xs) + max(xs), 2 * centroid[0]))
        self.assertTrue(close(min(ys) + max(ys), 2 * centroid[1]))

    def test_pairwise_slot_distances_at_least_spacing(self):
        for n in range(1, 10):
            slots = [slot_position(r, c, n, (0.0, 0.0, 0.0), 4.0)
                     for r in range(n) for c in range(n)]
            for i in range(len(slots)):
                for j in range(i + 1, len(slots)):
                    d = math.sqrt(sum((slots[i][k] - slots[j][k]) ** 2
                                      for k in range(3)))
                    self.assertGreaterEqual(
                        d, GRID_SPACING - EPS,
                        'n=%d slots %d/%d distance %r < spacing' % (n, i, j, d))

    def test_every_slot_beyond_ligand_gap(self):
        n = 5
        centroid = (1.0, 2.0, 3.0)
        R = 6.5
        for r in range(n):
            for c in range(n):
                pos = slot_position(r, c, n, centroid, R)
                d = math.sqrt(sum((pos[k] - centroid[k]) ** 2
                                  for k in range(3)))
                self.assertGreaterEqual(
                    d, R + GAP_MARGIN - EPS,
                    'slot (%d,%d) inside the R+GAP_MARGIN gap' % (r, c))
                # sanity ceiling: the gap must not be absurdly large
                self.assertLessEqual(
                    d, R + GAP_MARGIN + n * GRID_SPACING + EPS,
                    'slot (%d,%d) unreasonably far' % (r, c))

    def test_plane_offset_along_plus_z(self):
        pos = slot_position(1, 1, 3, (0.0, 0.0, 7.0), 2.0)
        self.assertTrue(close(pos[2], 7.0 + 2.0 + GAP_MARGIN))

    def test_placement_offsets_keep_molecule_slots_disjoint(self):
        # Molecule index m shifts its whole group along +x by
        # m * (grid_width + INTER_GRID_MARGIN): two molecules' slots never
        # coincide (and stay at least one spacing apart).
        n = 3
        centroid = (0.0, 0.0, 0.0)
        R = 4.0
        slots_m0 = [slot_position(r, c, n, centroid, R)
                    for r in range(n) for c in range(n)]
        off = placement_offset(1, n)
        slots_m1 = [tuple(pos[k] + off[k] for k in range(3))
                    for pos in slots_m0]
        for a in slots_m0:
            for b in slots_m1:
                d = math.sqrt(sum((a[k] - b[k]) ** 2 for k in range(3)))
                self.assertGreaterEqual(
                    d, GRID_SPACING - EPS,
                    'cross-molecule slots closer than one spacing: %r %r'
                    % (a, b))
        # offset is purely additive along +x
        self.assertEqual(off[1], 0.0)
        self.assertEqual(off[2], 0.0)
        self.assertGreater(off[0], 0.0)
        # molecule 0 sits at the origin offset
        self.assertEqual(placement_offset(0, n), (0.0, 0.0, 0.0))


class TestLigandDataGuards(unittest.TestCase):
    """Degenerate ligand bounds must fail EARLY with a clear message.

    persistence writes JSON with allow_nan=False, so a NaN/inf that
    reaches save time is refused far from the bug (generation research
    §5.2/§10): the generator refuses at the source.
    """

    def test_nan_centroid_refused(self):
        for axis in range(3):
            centroid = [0.0, 0.0, 0.0]
            centroid[axis] = float('nan')
            with self.assertRaises(GenerationError) as ctx:
                generator._validate_ligand_data(
                    {'centroid': tuple(centroid), 'radius': 4.0})
            self.assertIn('centroid', str(ctx.exception))

    def test_inf_centroid_refused(self):
        with self.assertRaises(GenerationError):
            generator._validate_ligand_data(
                {'centroid': (0.0, float('inf'), 0.0), 'radius': 4.0})

    def test_nonfinite_radius_refused(self):
        for bad in (float('nan'), float('inf'), float('-inf')):
            with self.assertRaises(GenerationError) as ctx:
                generator._validate_ligand_data(
                    {'centroid': (0.0, 0.0, 0.0), 'radius': bad})
            self.assertIn('radius', str(ctx.exception))

    def test_nonpositive_radius_refused(self):
        for bad in (0.0, -1.0, -1e-9):
            with self.assertRaises(GenerationError) as ctx:
                generator._validate_ligand_data(
                    {'centroid': (0.0, 0.0, 0.0), 'radius': bad})
            self.assertIn('radius', str(ctx.exception))

    def test_bad_centroid_arity_refused(self):
        for bad in ((0.0, 0.0), (0.0, 0.0, 0.0, 0.0), ()):
            with self.assertRaises(GenerationError):
                generator._validate_ligand_data(
                    {'centroid': bad, 'radius': 4.0})

    def test_valid_bounds_pass(self):
        generator._validate_ligand_data(
            {'centroid': (1.0, -2.0, 3.0), 'radius': 4.5})

    def test_error_is_ValueError_subclass(self):
        # GenerationError is a pure exception (generation research §3.2):
        # a failed generation is not a malformed FILE (not FormatError).
        self.assertTrue(issubclass(GenerationError, ValueError))


class TestSubSeedDerivation(unittest.TestCase):
    """Per-unit sub-seeds drawn from the master stream in fixed order
    (generation research §7.1) -- never from hash()."""

    def test_deterministic_fixed_order(self):
        expected = []
        master = random.Random(42)
        for _ in range(5):
            expected.append(master.randint(0, 2 ** 31 - 1))
        self.assertEqual(generator._sub_seeds(random.Random(42), 5), expected)

    def test_same_seed_same_sub_seeds(self):
        self.assertEqual(generator._sub_seeds(random.Random(7), 4),
                         generator._sub_seeds(random.Random(7), 4))

    def test_zero_units(self):
        self.assertEqual(generator._sub_seeds(random.Random(1), 0), [])

    def test_seeds_are_real_ints_in_range(self):
        seeds = generator._sub_seeds(random.Random(99), 20)
        for seed in seeds:
            self.assertIsInstance(seed, int)
            self.assertNotIsInstance(seed, bool)
            self.assertTrue(0 <= seed <= 2 ** 31 - 1)

    def test_sub_rng_streams_are_independent_of_consumption_order(self):
        # The isolation property that protects golden tests (PITFALL 11.2):
        # each unit's RNG depends only on its sub-seed, so consuming unit
        # 1's stream cannot shift unit 2's.
        seeds = generator._sub_seeds(random.Random(5), 3)
        first = random.Random(seeds[1]).randint(0, 10 ** 6)
        random.Random(seeds[0]).randint(0, 10 ** 6)   # consume another unit
        second = random.Random(seeds[1]).randint(0, 10 ** 6)
        self.assertEqual(first, second)


if __name__ == '__main__':
    unittest.main()
