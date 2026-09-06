"""Unit tests for aamatch.thresholds — the approved threshold table (02-06).

Every constant assertion here is transcribed from the APPROVED DETECT-03
gate document (docs/DETECTION_THRESHOLDS.md, APPROVED 2026-09-06, human
gate at the phase-2 plan 02-01 checkpoint). The project truthfulness rule
forbids inventing chemistry: these tests pin the transcription so a drift
between the frozen document and the code fails the suite instead of
silently changing detection semantics.

Pinned beyond raw values:
- the public constant set is COMPLETE (exactly the approved table + the
  prefilter margin + the computed MAX_CUTOFF — nothing else leaks);
- MAX_CUTOFF is the computed max of all distance constants;
- AA_PREFILTER_MARGIN covers MAX_CUTOFF with headroom (detection research
  §5.2 item 2: the ligand sphere is inflated by 7.5 A — the research's
  headroom value, above the approved table's 6.0 A max cutoff);
- row 8 (15 deg) and the metal element list keep their SINGLE homes in
  aamatch/capability.py (recorded 02-05 decision: reference, never
  duplicate) and are re-exported here under their row names;
- every public constant carries a `source:` comment with the approving
  date (the done criterion: "every constant cites source + approval date");
- the module docstring carries the bump policy (any constant change here
  => DETECTOR_VERSION bump in aamatch/level_spec.py, gate §4.7) and the
  cell-cutoff note (spatial.cross_pairs derives its cell size from the
  cutoff argument — cell == cutoff keeps the 3x3x3 scan exhaustive).

Runs under bare python3.6, stdlib only, zero stubs.
"""

import unittest

from aamatch import capability
from aamatch import thresholds


# The approved table as (name -> approved value), transcribed row by row
# from docs/DETECTION_THRESHOLDS.md §2.2 (rows 1-10) plus the prefilter
# margin (detection research §5.2.2) and the computed MAX_CUTOFF.
EXPECTED = {
    # Row 1 — Hydrogen bond: BINANA pair 4.0 A / >= 140 deg [V]
    'HBOND_D_MAX': 4.0,
    'HBOND_ANGLE_MIN_DEG': 140.0,
    # Row 2 — Salt bridge: PLIP = BINANA = 5.5 A, group centers [V]
    'SALT_CENTER_D_MAX': 5.5,
    # Row 3 — pi-stacking: PLIP set 5.5 / 30 / 2.0 [V]
    'PISTACK_CENTER_D_MAX': 5.5,
    'PISTACK_ANGLE_TOL_DEG': 30.0,
    'PISTACK_OFFSET_MAX': 2.0,
    # Row 4 — Cation-pi: distance PLIP+BINANA 6.0 (P3); offset PLIP 2.0 [V]
    'CATIONPI_D_MAX': 6.0,
    'CATIONPI_OFFSET_MAX': 2.0,
    # Row 5 — Hydrophobic: PLIP+BINANA 4.0 (P3); PLIP graph rule [V]
    'HYDRO_D_MAX': 4.0,
    # Row 6 — Halogen: PLIP full set 4.0 / 165+-30 / 120+-30 [V]
    'HALOGEN_D_MAX': 4.0,
    'HALOGEN_DONOR_ANGLE_DEG': (135.0, 195.0),
    'HALOGEN_ACC_ANGLE_DEG': (90.0, 150.0),
    # Row 7 — Metal: PLIP 3.0 [V]; element list OQ-7 (single home: capability)
    'METAL_D_MAX': 3.0,
    'METAL_ELEMENTS': frozenset(('MG', 'ZN', 'FE', 'CA', 'MN', 'CU', 'NI',
                                 'CO', 'CD')),
    # Row 8 — ring-ID planarity fallback: BINANA 15 deg [V] (single home)
    'AROMATIC_PLANARITY_FALLBACK_DEG': 15.0,
    # Row 10 — global minimum distance: PLIP MIN_DIST 0.5 [V]
    'MIN_DIST': 0.5,
    # Prefilter margin (not a gate row): detection research §5.2.2 headroom
    'AA_PREFILTER_MARGIN': 7.5,
    # Computed: max of all distance constants (row values above)
    'MAX_CUTOFF': 6.0,
}

# The distance constants MAX_CUTOFF is computed over (MIN_DIST is a floor,
# not a cutoff — excluded; angles/tuples are not distances — excluded).
DISTANCE_CONSTANTS = ('HBOND_D_MAX', 'SALT_CENTER_D_MAX',
                      'PISTACK_CENTER_D_MAX', 'CATIONPI_D_MAX',
                      'HYDRO_D_MAX', 'HALOGEN_D_MAX', 'METAL_D_MAX')


class TestApprovedTableExact(unittest.TestCase):
    """Every constant equals the approved value, row for row (gate §2.2)."""

    def test_every_constant_equals_approved_value(self):
        for name in sorted(EXPECTED):
            expected = EXPECTED[name]
            actual = getattr(thresholds, name)
            with self.subTest(constant=name):
                self.assertEqual(actual, expected,
                                 '%s drifted from the approved table: '
                                 'expected %r, got %r (docs/'
                                 'DETECTION_THRESHOLDS.md §2.2; any change '
                                 'is a DETECTOR_VERSION bump event, gate '
                                 '§4.7)' % (name, expected, actual))

    def test_constant_set_is_complete(self):
        # The approved table as constants — nothing more, nothing less.
        # Extra public names would be unapproved chemistry; missing names
        # would push the detector toward inlined numbers.
        public = set(name for name in dir(thresholds)
                     if not name.startswith('_'))
        self.assertEqual(public, set(EXPECTED))

    def test_distance_values_are_floats(self):
        for name in DISTANCE_CONSTANTS + ('HBOND_ANGLE_MIN_DEG', 'MIN_DIST',
                                          'AA_PREFILTER_MARGIN'):
            self.assertIsInstance(getattr(thresholds, name), float,
                                  '%s must be a float literal' % name)

    def test_angle_windows_are_float_tuples(self):
        for name in ('HALOGEN_DONOR_ANGLE_DEG', 'HALOGEN_ACC_ANGLE_DEG'):
            value = getattr(thresholds, name)
            self.assertIsInstance(value, tuple)
            self.assertEqual(len(value), 2)
            for bound in value:
                self.assertIsInstance(bound, float)


class TestMaxCutoffComputed(unittest.TestCase):
    """MAX_CUTOFF is COMPUTED from the table — never a hand-maintained number."""

    def test_max_cutoff_is_max_of_distance_constants(self):
        computed = max(getattr(thresholds, name)
                       for name in DISTANCE_CONSTANTS)
        self.assertEqual(thresholds.MAX_CUTOFF, computed)
        # The approved table's largest distance criterion is cation-pi 6.0.
        self.assertEqual(computed, 6.0)

    def test_prefilter_margin_covers_max_cutoff(self):
        # Detection research §5.2 item 2: the AA prefilter inflates the
        # ligand bounding sphere so that EVERY approved cutoff is covered.
        # Feature centers (charge groups, ring centers) lie inside their
        # side's bounding sphere, so an interacting feature pair at
        # d <= MAX_CUTOFF implies center distance <= r_aa + r_lig + margin.
        self.assertGreaterEqual(thresholds.AA_PREFILTER_MARGIN,
                                thresholds.MAX_CUTOFF)


class TestSingleHomes(unittest.TestCase):
    """Values already homed in capability.py (02-05) are re-exported, not
    duplicated — the recorded "reference, do NOT duplicate" decision."""

    def test_metal_elements_is_the_capability_object(self):
        # source: gate §2.2 row 7 + §3.5 metal list (OQ-7); single home
        # capability.METAL_ELEMENTS (DETECT-04 single typing home §4.2).
        self.assertIs(thresholds.METAL_ELEMENTS, capability.METAL_ELEMENTS)

    def test_planarity_fallback_is_the_capability_object(self):
        # source: gate §2.2 row 8 (BINANA 15 deg [V]); single home
        # capability.RING_PLANARITY_FALLBACK_DEG (plan 02-05).
        self.assertIs(thresholds.AROMATIC_PLANARITY_FALLBACK_DEG,
                      capability.RING_PLANARITY_FALLBACK_DEG)


class TestProvenanceComments(unittest.TestCase):
    """Done criterion: "every constant cites source + approval date".

    Scans thresholds.py as TEXT: each public constant's definition must
    have a `source:` comment nearby that carries the approval date
    2026-09-06 (the DETECT-03 human gate date). This is the mechanical
    half of the truthfulness rule for the transcription.
    """

    def test_every_constant_has_source_comment_with_approval_date(self):
        path = 'aamatch/thresholds.py'
        with open(path) as handle:
            lines = handle.read().splitlines()
        missing = []
        for name in sorted(EXPECTED):
            defn = None
            for idx, line in enumerate(lines):
                stripped = line.strip()
                if stripped.startswith(name) and (
                        ' import ' in line or ' = ' in stripped):
                    defn = idx
                    break
            if defn is None:
                missing.append('%s: no definition line found' % name)
                continue
            window = lines[max(0, defn - 8):defn + 3]
            block = '\n'.join(window)
            if 'source:' not in block:
                missing.append('%s: no source: comment near line %d'
                               % (name, defn + 1))
            elif '2026-09-06' not in block:
                missing.append('%s: source comment lacks the 2026-09-06 '
                               'approval date' % name)
        self.assertEqual(
            missing, [],
            'thresholds.py provenance incomplete (gate doc requires a '
            'source citation + approval date per constant):\n  '
            + '\n  '.join(missing))


class TestModuleDocstringPolicy(unittest.TestCase):
    """The docstring is the policy carrier (plan Task 1 GREEN spec)."""

    def test_docstring_carries_bump_policy(self):
        doc = thresholds.__doc__ or ''
        self.assertIn('DETECTOR_VERSION', doc,
                      'thresholds docstring must state the bump policy: any '
                      'change here => DETECTOR_VERSION bump in '
                      'aamatch/level_spec.py (gate §4.7)')
        self.assertIn('bump', doc.lower())

    def test_docstring_carries_cell_cutoff_note(self):
        doc = thresholds.__doc__ or ''
        self.assertIn('cell', doc.lower(),
                      'thresholds docstring must carry the CELL-CUTOFF '
                      'note: spatial.cross_pairs derives its cell size '
                      'from the cutoff argument (cell == cutoff keeps the '
                      '3x3x3 neighbourhood scan exhaustive)')
        self.assertIn('cross_pairs', doc)


if __name__ == '__main__':
    unittest.main()
