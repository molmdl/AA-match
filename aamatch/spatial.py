"""Cell-list spatial pruning + brute-force test oracle (plan 02-02).

``cross_pairs`` is the detector's ONLY candidate-pair source (DETECT-05,
consumed by plans 02-06/02-07): points_b are bucketed into a uniform
grid whose cell size equals the cutoff; each point_a scans its own cell
plus the 26 neighbours (3x3x3 via nested dx/dy/dz loops -- itertools is
deliberately NOT in the pure-layer whitelist, per the recorded 02-01
convention). A pair at distance <= cutoff differs by at most one cell
per axis when cell size == cutoff, so the 3x3x3 scan is provably
exhaustive -- proven against the brute-force oracle over 100 seeded
random clouds in tests/test_spatial.py (detection research §6.5, the
correctness half of DETECT-05).

``brute_force_pairs`` is a TEST ORACLE ONLY -- the detector must never
call it outside tests (the plan 02-15 code audit greps for this).
"""

from .vec3 import dist


def build_index(points, cell):
    """Bucket ``points`` into ``{cell key: [point indices]}``.

    The key is ``(int(x // cell), int(y // cell), int(z // cell))``:
    floor division FIRST, then int() -- this handles negative
    coordinates correctly (int(x / cell) would truncate toward zero and
    wrongly merge the two cells either side of the origin plane).
    """
    index = {}
    for idx, p in enumerate(points):
        key = (int(p[0] // cell), int(p[1] // cell), int(p[2] // cell))
        bucket = index.get(key)
        if bucket is None:
            index[key] = [idx]
        else:
            bucket.append(idx)
    return index


def cross_pairs(points_a, points_b, cutoff):
    """Sorted ``(i, j)`` pairs with ``dist(points_a[i], points_b[j]) <= cutoff``.

    ``points_a``/``points_b`` are lists of (x, y, z) float tuples. The
    b-side is indexed once (cell = cutoff); each a-point scans its own
    cell + 26 neighbours, so work scales with neighbourhood occupancy,
    not with len(points_b) (no full double loop).
    """
    index = build_index(points_b, cutoff)
    pairs = []
    for i, pa in enumerate(points_a):
        cx = int(pa[0] // cutoff)
        cy = int(pa[1] // cutoff)
        cz = int(pa[2] // cutoff)
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                for dz in (-1, 0, 1):
                    bucket = index.get((cx + dx, cy + dy, cz + dz))
                    if bucket is None:
                        continue
                    for j in bucket:
                        if dist(pa, points_b[j]) <= cutoff:
                            pairs.append((i, j))
    pairs.sort()
    return pairs


def brute_force_pairs(points_a, points_b, cutoff):
    """Test oracle only -- the detector must never call this outside tests.

    O(N*M) double loop over ALL cross pairs; exists solely so
    tests/test_spatial.py can prove ``cross_pairs`` prunes nothing it
    should keep (cell-list equivalence, detection research §6.5).
    """
    pairs = []
    for i, pa in enumerate(points_a):
        for j, pb in enumerate(points_b):
            if dist(pa, pb) <= cutoff:
                pairs.append((i, j))
    pairs.sort()
    return pairs
