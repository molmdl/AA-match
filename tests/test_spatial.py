"""Unit tests for aamatch.spatial — cell-list pruning + oracle (plan 02-02).

The correctness half of DETECT-05 (detection research §6.5): the
cell-list candidate generator must find EXACTLY the pair set the
brute-force oracle finds, proven over 100 seeded random clouds.
Hand-checked small cases pin the boundary semantics (<= cutoff) and
the floor-division cell keys.

Runs under bare python3.6, stdlib only, zero stubs — spatial itself
must import only `from .vec3 import dist` (purity Gate A).
"""

import math
import random
import unittest

from aamatch import spatial


def random_cloud(rng, n, lo=0.0, hi=20.0):
    """n random (x, y, z) tuples in the box [lo, hi]^3, in fixed order.

    Never samples from a set (PYTHONHASHSEED would break determinism) —
    a list comprehension over range() keeps the draw order fixed.
    """
    return [(rng.uniform(lo, hi), rng.uniform(lo, hi), rng.uniform(lo, hi))
            for _ in range(n)]


class TestCrossPairsHandChecked(unittest.TestCase):
    """Small hand-checkable scenes with exact expected pair sets."""

    def test_plan_example_single_pair(self):
        # only a[0]-b[0] (dist 1.0) is within cutoff 2.0
        a = [(0.0, 0.0, 0.0), (10.0, 0.0, 0.0)]
        b = [(1.0, 0.0, 0.0), (20.0, 0.0, 0.0)]
        self.assertEqual(spatial.cross_pairs(a, b, 2.0), [(0, 0)])

    def test_two_pairs_selected_correctly(self):
        # a[1]-b[0] dist 0.5 <= 1.0; the other three pairs are too far
        a = [(0.0, 0.0, 0.0), (1.0, 0.0, 0.0)]
        b = [(1.5, 0.0, 0.0), (5.0, 0.0, 0.0)]
        self.assertEqual(spatial.cross_pairs(a, b, 1.0), [(1, 0)])

    def test_result_is_sorted(self):
        a = [(5.0, 0.0, 0.0), (0.0, 0.0, 0.0)]
        b = [(0.5, 0.0, 0.0), (4.5, 0.0, 0.0)]
        result = spatial.cross_pairs(a, b, 1.0)
        self.assertEqual(result, sorted(result))
        self.assertIn((0, 1), result)
        self.assertIn((1, 0), result)


class TestBoundarySemantics(unittest.TestCase):
    """Distance exactly == cutoff is INCLUDED (<=)."""

    def test_exactly_at_cutoff_included(self):
        a = [(0.0, 0.0, 0.0)]
        b = [(2.0, 0.0, 0.0)]
        self.assertEqual(spatial.cross_pairs(a, b, 2.0), [(0, 0)])

    def test_exactly_at_cutoff_diagonal(self):
        # sqrt(2) is computed identically on both sides -> must be <=
        cutoff = math.sqrt(2.0)
        a = [(0.0, 0.0, 0.0)]
        b = [(1.0, 1.0, 0.0)]
        self.assertEqual(spatial.cross_pairs(a, b, cutoff), [(0, 0)])

    def test_just_beyond_cutoff_excluded(self):
        a = [(0.0, 0.0, 0.0)]
        b = [(2.0 + 1e-9, 0.0, 0.0)]
        self.assertEqual(spatial.cross_pairs(a, b, 2.0), [])


class TestEmptyInputs(unittest.TestCase):
    """Empty inputs yield empty pair lists."""

    def test_empty_a(self):
        self.assertEqual(spatial.cross_pairs([], [(1.0, 0.0, 0.0)], 2.0), [])

    def test_empty_b(self):
        self.assertEqual(spatial.cross_pairs([(1.0, 0.0, 0.0)], [], 2.0), [])

    def test_both_empty(self):
        self.assertEqual(spatial.cross_pairs([], [], 2.0), [])


class TestDeterminism(unittest.TestCase):
    """Same inputs twice -> identical output list."""

    def test_same_inputs_same_output_twice(self):
        rng = random.Random(7)
        a = random_cloud(rng, 15)
        b = random_cloud(rng, 15)
        first = spatial.cross_pairs(a, b, 4.0)
        second = spatial.cross_pairs(a, b, 4.0)
        self.assertEqual(first, second)


class TestBuildIndex(unittest.TestCase):
    """build_index(): cell keys use FLOOR division (negatives correct)."""

    def test_buckets_points_by_cell(self):
        index = spatial.build_index([(0.0, 0.0, 0.0), (0.5, 0.0, 0.0),
                                     (12.0, 0.0, 0.0)], 1.0)
        self.assertEqual(index.get((0, 0, 0)), [0, 1])
        self.assertEqual(index.get((12, 0, 0)), [2])

    def test_negative_coords_floor_not_truncate(self):
        # -0.5 // 1.0 == -1.0 (floor); int(-0.5 / 1.0) would truncate to 0
        index = spatial.build_index([(-0.5, -0.5, -0.5), (0.5, 0.5, 0.5)],
                                    1.0)
        self.assertEqual(index.get((-1, -1, -1)), [0])
        self.assertEqual(index.get((0, 0, 0)), [1])


class TestCellListEquivalence(unittest.TestCase):
    """DETECT-05 correctness half (detection research §6.5).

    For >= 100 seeds: cell-list cross_pairs output set == brute-force
    filtered pair set on randomized clouds. Pruning never misses a
    candidate. (The perf half of DETECT-05 lives in the headless smoke.)
    """

    SEEDS = 100
    CUTOFF = 4.0
    CLOUD_SIZE = 40
    BOX = 20.0

    def test_cross_pairs_equals_brute_force_over_100_seeds(self):
        for seed in range(self.SEEDS):
            rng = random.Random(seed)
            a = random_cloud(rng, self.CLOUD_SIZE, 0.0, self.BOX)
            b = random_cloud(rng, self.CLOUD_SIZE, 0.0, self.BOX)
            expected = sorted(spatial.brute_force_pairs(a, b, self.CUTOFF))
            actual = sorted(spatial.cross_pairs(a, b, self.CUTOFF))
            # vacuous-guard: 80 points in a 20 A box at 4 A must pair up
            self.assertTrue(
                actual,
                'seed %d: no pairs at all — equivalence would be vacuous'
                % seed)
            self.assertEqual(
                actual, expected,
                'seed %d: cell-list pruning missed/added candidates'
                % seed)


class TestOracleContract(unittest.TestCase):
    """The oracle must self-identify as test-only (plan 02-15 audit greps)."""

    def test_brute_force_docstring_declares_test_only(self):
        doc = spatial.brute_force_pairs.__doc__ or ''
        self.assertIn('test oracle only', doc.lower())
        self.assertIn('never call this outside tests', doc.lower())


if __name__ == '__main__':
    unittest.main()
