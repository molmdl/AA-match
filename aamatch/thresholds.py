"""aamatch.thresholds -- the APPROVED detection threshold table as constants.

Layer: PURE (constants only). This module is the SINGLE IMPORT POINT for
every numeric detection criterion: detector code imports cutoffs/angles
from here and NEVER inlines a number (plan 02-06 must_haves). The values
are transcribed row-by-row from the frozen DETECT-03 gate document
(docs/DETECTION_THRESHOLDS.md §2.2, rows 1-10); each constant (or constant
group) carries a ``source:`` comment with its published provenance and the
approval record date.

BUMP POLICY (gate §4.7): ANY change to a constant in this module is a
DETECTOR_VERSION bump event in aamatch/level_spec.py -- never a silent
edit. ``detector_version`` is an exact-match gate: a level spec generated
under a different detector_version is refused ("stale or newer --
regenerate"), because changed detection semantics make specs unsolvable.
This gate is separate from the container ``format`` version
(FORMAT_VERSION in aamatch/persistence.py), which refuses only NEWER
values -- the two version gates must never be conflated. The table is
APPROVED-PROVISIONAL: values may need adjustment after the Phase-8
curated dataset lands, and that revisit is the same bump event.

CELL-CUTOFF NOTE: candidate-pair pruning runs through
``aamatch.spatial.cross_pairs``, which derives its cell size FROM the
cutoff argument it is given. With cell size == cutoff, a pair at distance
<= cutoff differs by at most one cell per axis, so the 3x3x3 neighbourhood
scan is provably exhaustive (proven against the brute-force oracle in
tests/test_spatial.py, the correctness half of DETECT-05). The detector
therefore passes a single shared atom-level cutoff (MAX_CUTOFF governs
its magnitude) and never a per-type smaller cell.

SINGLE HOMES: two of the approved values already live in
``aamatch/capability.py`` (plan 02-05, the single typing home -- gate
§4.2): the metal element list (needed there for ligand metal typing) and
the row-8 ring-planarity fallback (needed there for the ligand aromaticity
fallback). Per the recorded 02-05 decision ("reference it, do NOT
duplicate") this module RE-EXPORTS both under their row names so the
detector still imports all thresholds from exactly one module. Unit tests
pin the re-exports as the same objects (``is``).

Dependency direction: nothing but the two capability re-exports. No
itertools (recorded 02-01 convention), no numpy, no pymol.
"""

from .capability import METAL_ELEMENTS as _CAP_METAL_ELEMENTS
from .capability import RING_PLANARITY_FALLBACK_DEG as _CAP_RING_FALLBACK

# ---------------------------------------------------------------------------
# Row 1 -- Hydrogen bond. Adopted criterion: D...A <= 4.0 A AND angle at H
# >= 140 deg, both measured heavy-donor to heavy-acceptor / at H (gate
# §1.3 angle convention). Needs explicit polar H on both sides (gate §5.3,
# fail-closed donors). Rejected: PLIP 4.1/100 (permissive), ProLIF 3.5/130
# (tight). Narrative: gate §2.2 row 1.
# source: docs/DETECTION_THRESHOLDS.md §2.2 row 1 -- approved 2026-09-06.
# ---------------------------------------------------------------------------
HBOND_D_MAX = 4.0             # D...A distance, Angstrom (<=)
HBOND_ANGLE_MIN_DEG = 140.0   # angle D-H...A at H, degrees (>=)

# ---------------------------------------------------------------------------
# Row 2 -- Salt bridge (ionic folded in). Opposite charge-GROUP centers
# <= 5.5 A (group definitions: gate §2.3, BINANA's verified table).
# Unanimous distance across PLIP/BINANA; group-center form beats ProLIF's
# atom-atom 4.5. Narrative: gate §2.2 row 2.
# source: docs/DETECTION_THRESHOLDS.md §2.2 row 2 -- approved 2026-09-06.
# ---------------------------------------------------------------------------
SALT_CENTER_D_MAX = 5.5       # charge-group-center distance, Angstrom (<=)

# ---------------------------------------------------------------------------
# Row 3 -- pi-stacking (parallel + T-shaped as ONE category). Ring-center
# dist < 5.5 A AND normals within 30 deg of parallel OR perpendicular AND
# projected-center offset < 2.0 A; reported type is always pi_stacking
# (sub-type P/T is a metric only). Center distance and offset are STRICT
# less-than in the adopted criterion. Source of the set: PLIP. Narrative:
# gate §2.2 row 3.
# source: docs/DETECTION_THRESHOLDS.md §2.2 row 3 -- approved 2026-09-06.
# ---------------------------------------------------------------------------
PISTACK_CENTER_D_MAX = 5.5    # ring-center distance, Angstrom (<)
PISTACK_ANGLE_TOL_DEG = 30.0  # normals: <= 30 deg of parallel or
                              # perpendicular
PISTACK_OFFSET_MAX = 2.0      # projected-center offset, Angstrom (<)

# ---------------------------------------------------------------------------
# Row 4 -- Cation-pi. Charge center <-> ring center <= 6.0 A AND projected
# charge offset < 2.0 A; direction recorded (AA-cation over ligand ring vs
# lig-cation over AA ring, gate D4). Distance: PLIP+BINANA majority (P3);
# offset: PLIP. PLIP's ligand-side anti-artifact rule binds (OQ-4).
# Narrative: gate §2.2 row 4.
# source: docs/DETECTION_THRESHOLDS.md §2.2 row 4 -- approved 2026-09-06.
# ---------------------------------------------------------------------------
CATIONPI_D_MAX = 6.0          # charge center <-> ring center, Angstrom (<=)
CATIONPI_OFFSET_MAX = 2.0     # projected charge offset, Angstrom (<)

# ---------------------------------------------------------------------------
# Row 5 -- Hydrophobic contact. >= 1 pair of qualifying carbons with
# d <= 4.0 A; qualifying carbon = element C with all bonded neighbors in
# {C, H} -- the atom rule applies to the LIGAND side only; the AA side is
# residue-NAME-based (gate §3.4 pedagogical set). Binary presence
# semantics. Distance: PLIP+BINANA majority (P3). Narrative: gate §2.2
# row 5.
# source: docs/DETECTION_THRESHOLDS.md §2.2 row 5 -- approved 2026-09-06.
# ---------------------------------------------------------------------------
HYDRO_D_MAX = 4.0             # qualifying C-C distance, Angstrom (<=)

# ---------------------------------------------------------------------------
# Row 6 -- Halogen bond (donors ligand-side ONLY, X in {Cl, Br, I}; C-F
# donors EXCLUDED per the recorded ProLIF-precedent resolution). Acceptor
# atom ... halogen <= 4.0 A, angle A...X-D within 135-195 deg (165 +- 30,
# vertex at the halogen X), angle Y-A...X within 90-150 deg (120 +- 30,
# vertex at the acceptor A); acceptors AA-side O/N/S. Windows are
# INCLUSIVE bounds transcribed as tuples. Implementer note (02-07):
# acos-derived angles live in [0, 180]; the 195 upper bound mirrors 135
# about 180 -- apply the window to the computed angle consistently.
# Narrative: gate §2.2 row 6.
# source: docs/DETECTION_THRESHOLDS.md §2.2 row 6 -- approved 2026-09-06.
# ---------------------------------------------------------------------------
HALOGEN_D_MAX = 4.0                       # acceptor...X distance, A (<=)
HALOGEN_DONOR_ANGLE_DEG = (135.0, 195.0)  # angle A...X-D at X (window)
HALOGEN_ACC_ANGLE_DEG = (90.0, 150.0)     # angle Y-A...X at A (window)

# ---------------------------------------------------------------------------
# Row 7 -- Metal coordination (only when the ligand carries a metal).
# metal ... coordinating atom <= 3.0 A, DISTANCE-ONLY (no geometry
# fitting -- BINANA's published rationale; PLIP's 3.0 sits between
# ProLIF 2.8 and BINANA 3.5). Metals gated to ligand-side presence
# (capability.ligand_has_metal); donors AA-side N/O/S. The approved v1
# element list (OQ-7) is homed in capability.METAL_ELEMENTS (single
# typing home, gate §4.2 -- 02-05 needs it for ligand typing) and
# re-exported here under the row-7 name. Narrative: gate §2.2 row 7.
# source: docs/DETECTION_THRESHOLDS.md §2.2 row 7 + §3.5 metal list
# (OQ-7) -- approved 2026-09-06.
# ---------------------------------------------------------------------------
METAL_D_MAX = 3.0             # metal...coordinating atom distance, A (<=)
METAL_ELEMENTS = _CAP_METAL_ELEMENTS      # re-export (single home: capability)

# ---------------------------------------------------------------------------
# Row 8 -- Aromatic ring identification (support rule for rows 3-4).
# Primary: bond-order-derived aromaticity from the SDF/MOL2 bond block.
# Fallback for cycles with no bond orders: 5/6-member ring with
# adjacent-dihedral deviation <= 15 deg (BINANA [V]; defensive only --
# PLIP's 5.0 deg fallback was rejected as too strict for a defensive
# path). The single home is capability.RING_PLANARITY_FALLBACK_DEG (plan
# 02-05 consumes it for ligand aromatic typing), re-exported here under
# the row-8 name. Narrative: gate §2.2 row 8.
# source: docs/DETECTION_THRESHOLDS.md §2.2 row 8 -- approved 2026-09-06.
# ---------------------------------------------------------------------------
AROMATIC_PLANARITY_FALLBACK_DEG = _CAP_RING_FALLBACK  # re-export: 15.0 deg (<=)

# ---------------------------------------------------------------------------
# Row 9 -- Ring geometry (support rule): NO numeric constant. Approved
# definitions, implemented once in aamatch/detector.py's ring builder and
# pinned by its unit tests: ring center = mean of ring-atom coordinates;
# ring normal = plane normal of the first/third/fifth-atom plane (BINANA);
# ring radius = max(center -> ring atom). Narrative: gate §2.2 row 9.
# source: docs/DETECTION_THRESHOLDS.md §2.2 row 9 -- approved 2026-09-06.
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Row 10 -- Minimum distance (global). All pair distances must be > 0.5 A
# -- cheap guard against coincident/duplicate atoms (defensive; game data
# should not produce these). Value: PLIP MIN_DIST = 0.5 [V].
# Narrative: gate §2.2 row 10.
# source: docs/DETECTION_THRESHOLDS.md §2.2 row 10 -- approved 2026-09-06.
# ---------------------------------------------------------------------------
MIN_DIST = 0.5                # global pair-distance floor, Angstrom (>)

# ---------------------------------------------------------------------------
# AA prefilter margin (NOT a gate row -- pipeline constant). Sufficiency
# proof: every feature center the detector tests (charge-group centers,
# ring centers) lies inside its own side's bounding sphere, so an
# interacting feature pair at d <= MAX_CUTOFF implies sphere-center
# distance <= r_aa + r_lig + MAX_CUTOFF <= r_aa + r_lig + this margin.
# Kept at the research's 7.5 A headroom (>= MAX_CUTOFF = 6.0, pinned by
# test) so future approved cutoffs up to 7.5 A stay covered; raising it
# only costs prefilter precision, never correctness.
# source: detection research §5.2 item 2 (ligand sphere "inflated by the
# max cutoff (7.5 A)"), under the DETECT-03 gate approved 2026-09-06.
# ---------------------------------------------------------------------------
AA_PREFILTER_MARGIN = 7.5     # ligand-sphere inflation, Angstrom

# MAX_CUTOFF: computed from the table above -- never hand-maintained, so
# a future versioned table edit that adds a larger cutoff automatically
# widens both the prefilter math and the detector's shared atom-level
# pair cutoff. Not itself a gate value.
# source: computed max of the row distance constants (rows 1-7); policy
# per detection research §5.2.2 -- gate approved 2026-09-06.
_DISTANCE_CONSTANTS = (HBOND_D_MAX, SALT_CENTER_D_MAX, PISTACK_CENTER_D_MAX,
                       CATIONPI_D_MAX, HYDRO_D_MAX, HALOGEN_D_MAX,
                       METAL_D_MAX)
MAX_CUTOFF = max(_DISTANCE_CONSTANTS)
