"""Unit tests for aamatch.vec3 — pure 3-vector math on tuples (plan 02-02).

Every expected value below is hand-computed (no property testing here;
the statistical equivalence work lives in tests/test_spatial.py).
Runs under bare python3.6, stdlib only, zero stubs — vec3 itself must
import only `math` (purity Gate A, tests/test_purity.py).
"""

import math
import unittest

from aamatch import vec3


class TestAddSubScale(unittest.TestCase):
    """Tuple arithmetic: exact hand-computed sums/differences/scalings."""

    def test_add_hand_computed(self):
        self.assertEqual(vec3.add((1.0, 2.0, 3.0), (4.0, 5.0, 6.0)),
                         (5.0, 7.0, 9.0))

    def test_sub_hand_computed(self):
        self.assertEqual(vec3.sub((5.0, 7.0, 9.0), (4.0, 5.0, 6.0)),
                         (1.0, 2.0, 3.0))

    def test_sub_negative_components(self):
        self.assertEqual(vec3.sub((0.0, 0.0, 0.0), (1.5, -2.5, 3.5)),
                         (-1.5, 2.5, -3.5))

    def test_scale_hand_computed(self):
        self.assertEqual(vec3.scale((1.0, -2.0, 3.0), 2.0),
                         (2.0, -4.0, 6.0))

    def test_scale_by_fraction(self):
        # 0.5 is exactly representable -> exact equality is safe here
        self.assertEqual(vec3.scale((2.0, 4.0, 6.0), 0.5),
                         (1.0, 2.0, 3.0))


class TestDotCross(unittest.TestCase):
    """Dot/cross products: hand-computed values and handedness."""

    def test_dot_hand_computed(self):
        # 1*4 + 2*5 + 3*6 = 32
        self.assertEqual(vec3.dot((1.0, 2.0, 3.0), (4.0, 5.0, 6.0)), 32.0)

    def test_dot_orthogonal_is_zero(self):
        self.assertEqual(vec3.dot((1.0, 0.0, 0.0), (0.0, 1.0, 0.0)), 0.0)

    def test_cross_unit_axes_right_handed(self):
        # x ^ y = z
        self.assertEqual(vec3.cross((1.0, 0.0, 0.0), (0.0, 1.0, 0.0)),
                         (0.0, 0.0, 1.0))

    def test_cross_anticommutes(self):
        # y ^ x = -z
        self.assertEqual(vec3.cross((0.0, 1.0, 0.0), (1.0, 0.0, 0.0)),
                         (0.0, 0.0, -1.0))

    def test_cross_hand_computed_general(self):
        # (3*7-4*6, 4*5-2*7, 2*6-3*5) = (-3, 6, -3)
        self.assertEqual(vec3.cross((2.0, 3.0, 4.0), (5.0, 6.0, 7.0)),
                         (-3.0, 6.0, -3.0))


class TestNormDist(unittest.TestCase):
    """Lengths and distances: 3-4-5 triangle exact values."""

    def test_norm_3_4_5_triangle(self):
        self.assertEqual(vec3.norm((3.0, 4.0, 0.0)), 5.0)

    def test_norm_body_diagonal(self):
        self.assertAlmostEqual(vec3.norm((1.0, 1.0, 1.0)), math.sqrt(3.0),
                               places=15)

    def test_dist_3_4_5_triangle(self):
        self.assertEqual(vec3.dist((0.0, 0.0, 0.0), (3.0, 4.0, 0.0)), 5.0)

    def test_dist_symmetric(self):
        self.assertEqual(vec3.dist((1.0, 2.0, 3.0), (4.0, 6.0, 3.0)),
                         vec3.dist((4.0, 6.0, 3.0), (1.0, 2.0, 3.0)))

    def test_dist_zero_for_identical_points(self):
        self.assertEqual(vec3.dist((2.5, -1.0, 7.25), (2.5, -1.0, 7.25)), 0.0)

    def test_norm_squared_sqrt_free_exact(self):
        self.assertEqual(vec3.norm_squared((3.0, 4.0, 0.0)), 25.0)
        self.assertEqual(vec3.norm_squared((1.0, 1.0, 1.0)), 3.0)

    def test_norm_squared_matches_norm_squared(self):
        a = (1.5, -2.0, 3.5)
        self.assertAlmostEqual(vec3.norm_squared(a), vec3.norm(a) ** 2,
                               places=12)


class TestUnit(unittest.TestCase):
    """unit(): direction preserved, length 1, zero vector fails closed."""

    def test_unit_3_4_5_components(self):
        u = vec3.unit((3.0, 4.0, 0.0))
        self.assertAlmostEqual(u[0], 0.6, places=12)
        self.assertAlmostEqual(u[1], 0.8, places=12)
        self.assertAlmostEqual(u[2], 0.0, places=12)

    def test_unit_has_norm_one(self):
        self.assertAlmostEqual(vec3.norm(vec3.unit((1.0, 1.0, 1.0))), 1.0,
                               places=12)

    def test_unit_preserves_direction(self):
        v = (2.0, -1.0, 0.5)
        scaled_back = vec3.scale(vec3.unit(v), vec3.norm(v))
        for got, want in zip(scaled_back, v):
            self.assertAlmostEqual(got, want, places=12)

    def test_unit_zero_vector_raises(self):
        with self.assertRaises(ValueError):
            vec3.unit((0.0, 0.0, 0.0))


class TestAngleAt(unittest.TestCase):
    """angle_at(): radians at vertex p1 between (p0-p1) and (p2-p1)."""

    def test_right_angle_90deg(self):
        self.assertAlmostEqual(
            vec3.angle_at((1.0, 0.0, 0.0), (0.0, 0.0, 0.0), (0.0, 1.0, 0.0)),
            math.pi / 2.0, places=12)

    def test_straight_angle_180deg(self):
        self.assertAlmostEqual(
            vec3.angle_at((1.0, 0.0, 0.0), (0.0, 0.0, 0.0), (-2.0, 0.0, 0.0)),
            math.pi, places=12)

    def test_45deg(self):
        self.assertAlmostEqual(
            vec3.angle_at((1.0, 0.0, 0.0), (0.0, 0.0, 0.0), (1.0, 1.0, 0.0)),
            math.pi / 4.0, places=12)

    def test_vertex_not_at_origin(self):
        # same 90-degree geometry, vertex translated to (1, 1, 0)
        self.assertAlmostEqual(
            vec3.angle_at((2.0, 1.0, 0.0), (1.0, 1.0, 0.0), (1.0, 2.0, 0.0)),
            math.pi / 2.0, places=12)

    def test_degenerate_p0_equals_p1_raises(self):
        with self.assertRaises(ValueError):
            vec3.angle_at((1.0, 1.0, 0.0), (1.0, 1.0, 0.0), (0.0, 0.0, 0.0))

    def test_degenerate_p2_equals_p1_raises(self):
        with self.assertRaises(ValueError):
            vec3.angle_at((1.0, 0.0, 0.0), (0.0, 0.0, 0.0), (0.0, 0.0, 0.0))


class TestPlaneProject(unittest.TestCase):
    """plane_project(): point dropped onto a plane along its unit normal."""

    def test_project_onto_z0_plane(self):
        proj = vec3.plane_project((0.0, 0.0, 5.0), (0.0, 0.0, 0.0),
                                  (0.0, 0.0, 1.0))
        self.assertEqual(proj, (0.0, 0.0, 0.0))

    def test_project_keeps_inplane_components(self):
        proj = vec3.plane_project((1.0, 2.0, 3.0), (0.0, 0.0, 0.0),
                                  (0.0, 0.0, 1.0))
        self.assertEqual(proj, (1.0, 2.0, 0.0))

    def test_project_onto_offset_plane(self):
        proj = vec3.plane_project((0.5, -0.5, 4.0), (0.0, 0.0, 1.0),
                                  (0.0, 0.0, 1.0))
        self.assertEqual(proj, (0.5, -0.5, 1.0))

    def test_offset_distance_to_plane(self):
        # distance from the original point to the plane (offset-test use)
        point = (0.5, -0.5, 4.0)
        proj = vec3.plane_project(point, (0.0, 0.0, 1.0), (0.0, 0.0, 1.0))
        self.assertEqual(vec3.dist(point, proj), 3.0)

    def test_projected_point_lies_on_plane(self):
        point = (2.0, 3.0, 7.0)
        plane_point = (1.0, 1.0, 1.0)
        normal = (0.0, 0.0, 1.0)
        proj = vec3.plane_project(point, plane_point, normal)
        self.assertEqual(vec3.dot(vec3.sub(proj, plane_point), normal), 0.0)

    def test_project_diagonal_normal(self):
        normal = vec3.unit((1.0, 1.0, 1.0))
        proj = vec3.plane_project((1.0, 0.0, 0.0), (0.0, 0.0, 0.0), normal)
        # (1,0,0) minus its (1/sqrt(3)) component along the diagonal:
        # (1 - 1/3, -1/3, -1/3)
        self.assertAlmostEqual(proj[0], 2.0 / 3.0, places=12)
        self.assertAlmostEqual(proj[1], -1.0 / 3.0, places=12)
        self.assertAlmostEqual(proj[2], -1.0 / 3.0, places=12)
        # the offset equals the signed distance to the plane
        self.assertAlmostEqual(vec3.dist((1.0, 0.0, 0.0), proj),
                               1.0 / math.sqrt(3.0), places=12)


class TestFloatsInOut(unittest.TestCase):
    """Contract: int tuples in -> float tuples/results out (float coercion)."""

    def test_tuple_ops_return_float_components_from_int_inputs(self):
        results = (vec3.add((1, 2, 3), (4, 5, 6)),
                   vec3.sub((5, 4, 3), (1, 2, 3)),
                   vec3.scale((1, -2, 3), 2),
                   vec3.cross((1, 0, 0), (0, 1, 0)),
                   vec3.plane_project((1, 2, 3), (0, 0, 0), (0, 0, 1)))
        for result in results:
            for component in result:
                self.assertIsInstance(component, float)

    def test_scalar_results_are_float_from_int_inputs(self):
        self.assertIsInstance(vec3.dot((1, 2, 3), (4, 5, 6)), float)
        self.assertIsInstance(vec3.norm_squared((1, 2, 3)), float)
        self.assertIsInstance(vec3.norm((3, 4, 0)), float)
        self.assertIsInstance(vec3.dist((0, 0, 0), (3, 4, 0)), float)
        self.assertIsInstance(vec3.unit((3, 4, 0))[0], float)
        self.assertIsInstance(
            vec3.angle_at((1, 0, 0), (0, 0, 0), (0, 1, 0)), float)


if __name__ == '__main__':
    unittest.main()
