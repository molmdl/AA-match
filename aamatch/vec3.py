"""Pure 3-vector math on plain float 3-tuples (plan 02-02).

The detector's per-candidate geometry (DETECT-05, plans 02-06/02-07)
runs on plain (x, y, z) tuples with stdlib ``math`` ONLY -- the purity
gate forbids numpy in the pure layer (tests/test_purity.py), and
per-candidate math must be constant-time on tuples.

Contract: every function takes and returns plain float 3-tuples;
components are coerced with float() so int inputs never leak through.
Degenerate geometry fails closed: zero-length vectors raise ValueError
in unit()/angle_at() rather than producing NaNs downstream.

No classes, no numpy, no itertools (recorded 02-01 convention:
itertools stays out of the pure-layer whitelist -- comprehensions and
explicit tuple arithmetic only).
"""

import math


def add(a, b):
    """Component-wise sum ``a + b``."""
    return (float(a[0] + b[0]), float(a[1] + b[1]), float(a[2] + b[2]))


def sub(a, b):
    """Component-wise difference ``a - b``."""
    return (float(a[0] - b[0]), float(a[1] - b[1]), float(a[2] - b[2]))


def scale(a, s):
    """Scalar multiple ``s * a``."""
    s = float(s)
    return (a[0] * s, a[1] * s, a[2] * s)


def dot(a, b):
    """Dot product ``a . b``."""
    return float(a[0] * b[0] + a[1] * b[1] + a[2] * b[2])


def cross(a, b):
    """Cross product ``a x b`` (right-handed)."""
    return (float(a[1] * b[2] - a[2] * b[1]),
            float(a[2] * b[0] - a[0] * b[2]),
            float(a[0] * b[1] - a[1] * b[0]))


def norm_squared(a):
    """Squared length ``|a|^2`` -- the sqrt-free variant for hot loops."""
    return float(a[0] * a[0] + a[1] * a[1] + a[2] * a[2])


def norm(a):
    """Length ``|a|``."""
    return math.sqrt(norm_squared(a))


def dist(a, b):
    """Euclidean distance between points ``a`` and ``b``."""
    return norm(sub(a, b))


def unit(a):
    """Unit vector along ``a``; raises ValueError for the zero vector."""
    n = norm(a)
    if n == 0.0:
        raise ValueError('unit(): zero-length vector has no direction')
    return scale(a, 1.0 / n)


def angle_at(p0, p1, p2):
    """Angle in RADIANS at vertex ``p1`` between arms (p0 - p1), (p2 - p1).

    Raises ValueError when either arm is zero-length (degenerate angle).
    """
    v0 = sub(p0, p1)
    v2 = sub(p2, p1)
    n0 = norm(v0)
    n2 = norm(v2)
    if n0 == 0.0 or n2 == 0.0:
        raise ValueError(
            'angle_at(): degenerate angle -- an arm has zero length')
    c = dot(v0, v2) / (n0 * n2)
    if c > 1.0:  # float rounding can push |cos| a hair past 1 near 0/pi
        c = 1.0
    elif c < -1.0:
        c = -1.0
    return math.acos(c)


def plane_project(point, plane_point, unit_normal):
    """Project ``point`` onto the plane through ``plane_point``.

    ``unit_normal`` must be a UNIT plane normal (as produced by unit()
    on a face/cross normal); the result is undefined for non-unit input.
    Useful for offset tests: dist(point, plane_project(...)) is the
    distance from the point to the plane.
    """
    d = dot(sub(point, plane_point), unit_normal)
    return sub(point, scale(unit_normal, d))
