"""TDD RED battery for aamatch/wizard_core.py (plan 03-01).

Phase 3 introduces the gameplay wizard. Every gameplay DECISION that is
not a ``cmd`` call must live in a PURE, WSL-testable module (the repo
pattern: pure helpers gated by tests/test_purity.py PURE_MODULES, cmd
glue in the cmd-tier ``aamatch/wizard.py``). This file is written FIRST
(RED): ``aamatch.wizard_core`` does not exist yet, so simply collecting
this module raises ImportError -- that failure IS the RED proof. The
task-2 GREEN then implements the helpers until every hand-computed
expectation below passes, and registers the module in PURE_MODULES.

Covered pure logic (03-RESEARCH-wizard-interaction.md):
- build_slot_map: wizard-side reverse map {object_name: slot_id} over
  ONE molecule of the placement registry (sections 5.3/5.4 -- one
  object per slot, registry shape from aamatch/placement.py), with
  fail-closed refusals on bad registry shapes (PLAY-01 pick-identity
  precondition).
- transient_selection: the delete-guard behind the canonical
  do_select->do_pick map (section 10.2 -- only transient selections
  'sele'/pk1..pk4/'_'-prefixed may be deleted; the user's NAMED active
  selection must survive).
- view_camera_to_world: camera-frame nudge to world-frame conversion
  view step = R^T . step over cmd.get_view()'s row-major world->camera
  rotation block (movement constants feed plan 03-02/03-03).
- ensure_snapshot / color_map / snapshot_objects: PLAY-01 color
  feedback bookkeeping -- per-slot color snapshot taken exactly once,
  before the first recolor, restore via {ID: color} maps (section 4).
"""

import math
import unittest

from aamatch import wizard_core


def _registry_two_molecules():
    """Minimal placement-registry shape (aamatch/placement.py):
    {'level_index', 'pre_game_names', 'molecules': [
        {'molecule_id', 'offset', 'ligand', 'slots': {slot_id: (obj, ids)}},
        ...]}."""
    return {
        'level_index': 0,
        'pre_game_names': [],
        'molecules': [
            {'molecule_id': 'mol-001',
             'offset': (0.0, 0.0, 0.0),
             'ligand': ('_aam_lig', [1, 2]),
             'slots': {'r0c0': ('_aam_aa', [1, 2, 3]),
                       'r0c1': ('_aam_aa001', [1, 2, 3, 4])}},
            {'molecule_id': 'mol-002',
             'offset': (0.0, 0.0, 30.0),
             'ligand': ('_aam_lig001', [1, 2]),
             'slots': {'r0c0': ('_aam_aa002', [1, 2, 3]),
                       'r0c1': ('_aam_aa003', [1, 2, 3, 4])}},
        ],
    }


class TestBuildSlotMap(unittest.TestCase):
    """Reverse map {object_name: slot_id} for ONE molecule (PLAY-01 pick
    identity): a click's object name alone resolves the slot."""

    def test_exact_reverse_map_for_single_molecule(self):
        registry = _registry_two_molecules()
        self.assertEqual(
            wizard_core.build_slot_map(registry, 0),
            {'_aam_aa': 'r0c0', '_aam_aa001': 'r0c1'})

    def test_scoped_to_molecule_index(self):
        registry = _registry_two_molecules()
        # Only molecule 1's slots land in the map when index 1 is asked;
        # molecule 0's objects are absent (and vice versa above).
        self.assertEqual(
            wizard_core.build_slot_map(registry, 1),
            {'_aam_aa002': 'r0c0', '_aam_aa003': 'r0c1'})

    def test_refuses_registry_without_molecules_list(self):
        with self.assertRaises(ValueError) as cm:
            wizard_core.build_slot_map({'level_index': 0}, 0)
        self.assertIn('molecules', str(cm.exception))

    def test_refuses_non_dict_registry(self):
        with self.assertRaises(ValueError) as cm:
            wizard_core.build_slot_map([1, 2], 0)
        self.assertIn('molecules', str(cm.exception))

    def test_refuses_out_of_range_molecule_index(self):
        registry = _registry_two_molecules()
        for bad in (2, -1):
            with self.assertRaises(ValueError) as cm:
                wizard_core.build_slot_map(registry, bad)
            self.assertIn('molecule_index', str(cm.exception))

    def test_refuses_bad_slot_entry_shapes(self):
        def bad(slots):
            registry = _registry_two_molecules()
            registry['molecules'][0]['slots'] = slots
            return registry
        # Not a 2-tuple at all:
        for slots in ({'r0c0': '_aam_aa'},
                      {'r0c0': ('_aam_aa', [1, 2], 'extra')},
                      {'r0c0': ('', [1, 2])},
                      {'r0c0': (None, [1, 2])},
                      {'r0c0': (123, [1, 2])}):
            with self.assertRaises(ValueError):
                wizard_core.build_slot_map(bad(slots), 0)
        # Molecule without a slots dict:
        registry = _registry_two_molecules()
        registry['molecules'][0] = {'molecule_id': 'mol-001'}
        with self.assertRaises(ValueError) as cm:
            wizard_core.build_slot_map(registry, 0)
        self.assertIn('slots', str(cm.exception))


class TestTransientSelection(unittest.TestCase):
    """Delete-guard behind the canonical do_select->do_pick map
    (RESEARCH section 10.2 decision: transient-only delete)."""

    def test_transient_names(self):
        for name in ('sele', 'pk1', 'pk2', 'pk3', 'pk4',
                     '_drag', '_anything', '_aam_aa'):
            with self.subTest(name=name):
                self.assertTrue(wizard_core.transient_selection(name))

    def test_user_named_selections_survive(self):
        for name in ('mysel', 'ligand'):
            with self.subTest(name=name):
                self.assertFalse(wizard_core.transient_selection(name))


class TestViewCameraToWorld(unittest.TestCase):
    """camera step -> world step: world = R^T . camera over the
    row-major world->camera rotation block view[0:9] of cmd.get_view().
    Identity view must be the pass-through identity."""

    IDENTITY_VIEW = (1.0, 0.0, 0.0,
                     0.0, 1.0, 0.0,
                     0.0, 0.0, 1.0,
                     0.0, 0.0, 0.0,    # origin
                     40.0,             # z slabs + front/min_scale
                     0.0, 100.0,
                     0.0, 0.0, 0.0)

    def test_identity_view_passes_step_through(self):
        # Identity rotation: step unchanged, coerced to a float 3-tuple
        # (int inputs never leak -- house vec3 contract).
        out = wizard_core.view_camera_to_world(self.IDENTITY_VIEW, (1, 2, 3))
        self.assertEqual(out, (1.0, 2.0, 3.0))
        self.assertTrue(all(isinstance(v, float) for v in out))
        self.assertIsInstance(out, tuple)
        self.assertEqual(len(out), 3)

    def test_rz90_hand_computed(self):
        # R = Rz(+90 deg), row-major [0,-1,0, 1,0,0, 0,0,1]: maps the
        # world x-hat to the camera y-hat. world = R^T . step.
        view = (0.0, -1.0, 0.0,
                1.0, 0.0, 0.0,
                0.0, 0.0, 1.0,
                9.0, 8.0, 7.0, 40.0, 0.0, 100.0, 1.0, 2.0, 3.0)
        self.assertEqual(wizard_core.view_camera_to_world(view, (1, 0, 0)),
                         (0.0, -1.0, 0.0))
        self.assertEqual(wizard_core.view_camera_to_world(view, (0, 1, 0)),
                         (1.0, 0.0, 0.0))
        self.assertEqual(wizard_core.view_camera_to_world(view, (0, 0, 1)),
                         (0.0, 0.0, 1.0))

    def test_short_view_refused_naming_the_cause(self):
        for view in ((), (1.0, 0.0, 0.0), (1.0,) * 8):
            with self.assertRaises(ValueError) as cm:
                wizard_core.view_camera_to_world(view, (1, 0, 0))
            self.assertIn('9', str(cm.exception))


class TestViewCameraToWorldFullSO3(unittest.TestCase):
    """Frozen R^T camera->world nudge convention for FULL SO(3), not
    just yaw (08.2-02; closes the 03-01/03-04 yaw-only pin gap
    "pitch/roll never live-tested").

    Provenance:
    - P1 probe verdict (08.2-RESEARCH-probes.md section 2): the R^T
      convention was pressed live for FULL SO(3) -- 30/30 presses moved
      the AA exactly along the intended screen direction (max screen
      direction angle 0.0000 deg, max convention deviation 2.51e-07 A),
      over identity, Rz90, the ACTUAL rolled post-start view, and two
      synthetic SO(3) views -- so P1-VERDICT: "R^T holds for FULL SO(3)
      incl. the actual rolled start view: YES". This class formalizes
      P1 at unit level: any future regression against the frozen
      convention now fails loudly in WSL, decision-independent (every
      8.2 disposition A/B/C/D keeps the math untouched).
    - Frozen movement-model laws M5/M6 (RESEARCH-history.md section 2):
      M5 = "step_world = R^T . step over get_view's row-major
      world->camera block; identity view = pass-through"
      (wizard_core.py:135-159 pins the exact formula); M6 =
      wizard_core.view_camera_to_world is the SINGLE fix site.
    - Probe-log cross-check (test_s2_probe_log_cross_check): the three
      exact literals come from tmp/probe_082_p1_output.log
      (P1-POSTSTART-VIEW row; P1-VIEW S2-ACTUAL-poststart table rows).

    Derivation rule (anti-tautology, mirroring
    test_rz90_hand_computed): for a unit camera step e_i the expected
    world vector is R^T . e_i == ROW i of the rotation block
    (view[3i:3i+3]) -- that IS the transposed-matrix convention itself,
    so every expected tuple below is a hand-derived literal, never a
    runtime recomputation of the formula under test.

    Tolerance note: per-element delta 1e-9 -- this function is pure
    double-precision math. The 1.12e-06 tolerance class seen in P1
    belongs to PyMOL float32 view storage / live displacement
    measurement, NOT to this pure helper.

    Fixtures (each a 9-number row-major world->camera block + an
    arbitrary tail padded to 18 numbers -- view_camera_to_world reads
    ONLY view[0:9]):

    S2  The P1-captured ACTUAL post-start rolled view (the historical
        trigger of the 2026-09-21 re-open / standing request) --
        P1-POSTSTART-VIEW row of tmp/probe_082_p1_output.log, rotation
        block only.
    S3  Synthetic Rx(30) * Ry(50) * Rz(20), row-major composed by hand:
            Ry(50).Rz(20) =
              ( c50*c20,  -c50*s20,  s50)     = ( 0.604022774, -0.219846310,  0.766044443)
              ( s20,       c20,      0.0)     = ( 0.342020143,  0.939692621,  0.0)
              (-s50*c20,   s50*s20,  c50)     = (-0.719846310,  0.262002630,  0.642787610)
            Rx(30).(above) =
              (  r00,               r01,               r02)
              ( c30*r10 - s30*r20,  c30*r11 - s30*r21, c30*r12 - s30*r22)
              ( s30*r10 + c30*r20,  s30*r11 + c30*r21, s30*r12 + c30*r22)
        evaluated ONCE with plain math.cos/math.sin arithmetic while
        writing this fixture, then hard-coded below at full double
        (repr) precision -- full precision, not 6-decimal rounding, so
        the block is orthogonal at double precision and the 1e-12
        norm-preservation pin (test_norm_preservation_*) is honest.
    S4  Synthetic Rz(200) * Rx(25), row-major composed by hand:
            ( c200, -s200*c25,  s200*s25)
            ( s200,  c200*c25, -c200*s25)
            ( 0.0,   s25,       c25)
        same full-double-precision hard-coding discipline as S3.
    S5  Pure pitch Rx(-90): cos=0, sin=-1 exactly.
    """

    # S2 -- P1-captured ACTUAL post-start rolled view block
    # (tmp/probe_082_p1_output.log, P1-POSTSTART-VIEW row:
    # "-0.447214 0.894427 0 -0.894427 -0.447214 -0 0 0 1 ..."; -0 == 0.0
    # in floats, normalized here). Tail is arbitrary (view_camera_to_world
    # reads ONLY view[0:9]).
    S2_VIEW = (-0.447214, 0.894427, 0.0,
               -0.894427, -0.447214, 0.0,
               0.0, 0.0, 1.0,
               0.0, 0.0, -97.2456,      # origin from the probe row
               0.158331, 0.149332, 9.2822,
               76.6692, 117.822, -20.0)

    # S3 -- Rx(30) * Ry(50) * Rz(20), full-double literals (derivation
    # rows in the class docstring).
    S3_VIEW = (0.6040227735550537, -0.2198463103929542, 0.766044443118978,
               0.6561212879225009, 0.6827963662346814, -0.3213938048432696,
               -0.4523951199579622, 0.6967472440299423, 0.5566703992264195,
               9.0, 8.0, 7.0, 40.0, 0.0, 100.0, 1.0, 2.0, 3.0)

    # S4 -- Rz(200) * Rx(25), full-double literals (derivation rows in
    # the class docstring).
    S4_VIEW = (-0.9396926207859084, 0.3099755192194446, -0.144543958452599,
               -0.34202014332566866, -0.8516507396391465, 0.39713126196710286,
               0.0, 0.42261826174069944, 0.9063077870366499,
               1.0, 2.0, 3.0, 40.0, 0.0, 100.0, 9.0, 8.0, 7.0)

    # S5 -- pure pitch Rx(-90): cos(-90)=0, sin(-90)=-1 exactly.
    S5_VIEW = (1.0, 0.0, 0.0,
               0.0, 0.0, 1.0,
               0.0, -1.0, 0.0,
               0.0, 0.0, 0.0, 40.0, 0.0, 100.0, 0.0, 0.0, 0.0)

    def _assert_vec3_almost(self, actual, expected):
        # Per-element delta 1e-9: pure double-precision math, NOT the
        # 1.12e-06 PyMOL float32 storage tolerance class (see class
        # docstring "Tolerance note").
        self.assertEqual(len(actual), 3)
        for a, e in zip(actual, expected):
            self.assertAlmostEqual(a, e, delta=1e-9)

    def _expected_rows(self):
        """{name: (view, {step: hand-derived ROW/negated-ROW literal})}.
        The expected vector for +e_i is ROW i of the block (the R^T
        convention itself); for -e_i it is the negated row. ALL tuples
        are literals transcribed from the fixture blocks above, not
        computed expressions (anti-tautology discipline)."""
        neg = lambda r: (-r[0], -r[1], -r[2])
        tables = {}
        for name, view in (('S2', self.S2_VIEW), ('S3', self.S3_VIEW),
                           ('S4', self.S4_VIEW), ('S5', self.S5_VIEW)):
            rows = (view[0:3], view[3:6], view[6:9])
            tables[name] = (view, {
                (1, 0, 0): rows[0],
                (-1, 0, 0): neg(rows[0]),
                (0, 1, 0): rows[1],
                (0, -1, 0): neg(rows[1]),
                (0, 0, 1): rows[2],
                (0, 0, -1): neg(rows[2]),
            })
        return tables

    def _run_fixture(self, name):
        view, expectations = self._expected_rows()[name]
        for step, expected in expectations.items():
            with self.subTest(step=step):
                self._assert_vec3_almost(
                    wizard_core.view_camera_to_world(view, step), expected)

    def test_s2_actual_poststart_rolled_view_all_unit_steps(self):
        # S2: the historical trigger view -- rolled, not yaw-only.
        self._run_fixture('S2')

    def test_s3_rx30_ry50_rz20_all_unit_steps(self):
        # S3: arbitrary SO(3) -- roll+pitch+yaw composed.
        self._run_fixture('S3')

    def test_s4_rz200_rx25_all_unit_steps(self):
        # S4: rolled-then-pitched SO(3).
        self._run_fixture('S4')

    def test_s5_pure_pitch_rx_neg90_all_unit_steps(self):
        # S5: pure pitch -- Up(+y) nudges toward +z (toward viewer) and
        # +z nudges toward -y; pitch finally unit-tested.
        self._run_fixture('S5')

    def test_s2_probe_log_cross_check(self):
        # EXACT literals from tmp/probe_082_p1_output.log, P1-VIEW
        # "S2-ACTUAL-poststart" table:
        #   RIGHT(+x)         -> world (-0.447214, 0.894427, 0.000000)
        #   UP(+y)            -> world (-0.894427, -0.447214, 0.000000)
        #   TOWARD-VIEWER(+z) -> world (0.000000, 0.000000, 1.000000)
        # (block itself from the P1-POSTSTART-VIEW row; observed press
        # displacements in the P1-PRESS S2 rows match these to ~1e-7,
        # i.e. the live float32 tolerance class -- here the value IS the
        # stored block row, so plain equality is the cross-check).
        self.assertEqual(
            wizard_core.view_camera_to_world(self.S2_VIEW, (1, 0, 0)),
            (-0.447214, 0.894427, 0.0))
        self.assertEqual(
            wizard_core.view_camera_to_world(self.S2_VIEW, (0, 1, 0)),
            (-0.894427, -0.447214, 0.0))
        self.assertEqual(
            wizard_core.view_camera_to_world(self.S2_VIEW, (0, 0, 1)),
            (0.0, 0.0, 1.0))

    def test_linearity_composite_step_s3_s4(self):
        # Composite step (1,-2,3): result must equal the weighted sum
        # r0 - 2*r1 + 3*r2 of the three unit-row results -- a property
        # of the frozen convention independent of rote transcription.
        for view in (self.S3_VIEW, self.S4_VIEW):
            actual = wizard_core.view_camera_to_world(view, (1, -2, 3))
            expected = (
                view[0] - 2.0 * view[3] + 3.0 * view[6],
                view[1] - 2.0 * view[4] + 3.0 * view[7],
                view[2] - 2.0 * view[5] + 3.0 * view[8])
            self._assert_vec3_almost(actual, expected)

    def test_norm_preservation_composite_step_s3_s4(self):
        # R^T over an SO(3) block preserves vector norm exactly at
        # double precision (fixture literals are full-repr so the block
        # IS orthogonal -- see the S3 fixture comment): |(1,-2,3)| is
        # sqrt(14); the world step must match within 1e-12.
        for view in (self.S3_VIEW, self.S4_VIEW):
            actual = wizard_core.view_camera_to_world(view, (1, -2, 3))
            norm = math.sqrt(sum(v * v for v in actual))
            self.assertAlmostEqual(norm, math.sqrt(14.0), delta=1e-12)


class TestColorSnapshotBookkeeping(unittest.TestCase):
    """PLAY-01 feedback / PLAY-04 restore bookkeeping: the per-slot
    snapshot is taken exactly once (BEFORE the first recolor) and is
    idempotent afterwards; the restore view is a plain {ID: color} map.
    The store dict is caller-owned plain picklable data."""

    def test_ensure_snapshot_once_then_idempotent(self):
        store = {}
        original = [(1, 3), (2, 8), (3, 3)]
        self.assertTrue(wizard_core.ensure_snapshot(store, '_aam_aa', original))
        # Second call with DIFFERENT rows: False, original snapshot kept.
        drifted = [(1, 10), (2, 10), (3, 10)]
        self.assertFalse(wizard_core.ensure_snapshot(store, '_aam_aa', drifted))
        self.assertEqual(store['_aam_aa'], list(original))

    def test_ensure_snapshot_stores_a_copy(self):
        store = {}
        rows = [(1, 3), (2, 8)]
        wizard_core.ensure_snapshot(store, '_aam_aa', rows)
        rows.append((3, 99))              # mutating caller rows afterwards...
        rows[0] = (1, -1)
        self.assertEqual(store['_aam_aa'], [(1, 3), (2, 8)])  # ...no effect

    def test_per_object_snapshots_are_independent(self):
        store = {}
        self.assertTrue(wizard_core.ensure_snapshot(store, 'a', [(1, 3)]))
        self.assertTrue(wizard_core.ensure_snapshot(store, 'b', [(1, 5)]))
        self.assertFalse(wizard_core.ensure_snapshot(store, 'a', [(1, 9)]))
        self.assertEqual(store['a'], [(1, 3)])
        self.assertEqual(store['b'], [(1, 5)])

    def test_color_map_view(self):
        store = {}
        wizard_core.ensure_snapshot(store, '_aam_aa', [(1, 3), (2, 8)])
        self.assertEqual(wizard_core.color_map(store, '_aam_aa'),
                         {1: 3, 2: 8})
        self.assertIsNone(wizard_core.color_map(store, '_aam_aa999'))

    def test_snapshot_objects_sorted(self):
        store = {}
        # Insert deliberately out of sorted order; python3.6 does not
        # guarantee dict insertion order, so the helper must sort.
        for name in ('_aam_aa003', '_aam_aa', '_aam_aa001'):
            wizard_core.ensure_snapshot(store, name, [(1, 3)])
        self.assertEqual(wizard_core.snapshot_objects(store),
                         ['_aam_aa', '_aam_aa001', '_aam_aa003'])
        self.assertEqual(wizard_core.snapshot_objects({}), [])


class TestMovementAndFeedbackConstants(unittest.TestCase):
    """Exact pinned constants (v1 recolor precedent game.py:208-213;
    movement model from 03-RESEARCH-movement-spike.md; hint color from
    05-RESEARCH-hint.md standard_stack/Q3).

    Dated EXPECTED-RED bridge -- 2026-10-21 (06-05 convention; the
    2026-10-18 pivot, recorded human disposition 2026-10-19: STATE.md
    "Phase 8.3 Decisions & Laws", ledger rows C1 / C3 / C4, consequence
    map in 08.3-DECISION-MENU.md section 8). 08.3-03 SWEPT three
    movement constants out of aamatch/wizard_core.py: the nudge-channel
    step (C1, unconditional -- the nudge channel is gone), the keyboard
    fine-rotation step (C3, per rotate_keys=delete) and the panel
    Rotate-90 step (C4, per rotate_button=delete). Dead symbols are not
    re-named here on purpose (the pin file must not cite removed homes);
    the verbatim pre-edit failure receipt lives in 08.3-11-SUMMARY.md.

    Pre-edit receipt (BEFORE any edit, 2026-10-21,
    ``python3.6 -m unittest tests.test_wizard_core -v``): 26 tests ran,
    exactly 2 ERRORs, both the expected pins -- ``test_constants_exact``
    and ``test_constants_are_float_steps`` raised AttributeError on the
    first (nudge-step) assert line of each. Both TestViewCameraToWorld*
    classes were GREEN in the same run (the C6-survivor row:
    view_camera_to_world keeps its drag_move consumer). The deleted
    constants' assert LINES are REMOVED, not weakened -- TOWARD_STEP 2.5
    and both color pins stay byte-identical below, and the 08.3-04
    drag-scale helpers get their own battery (TestDragScaleMath) in this
    file.
    """

    def test_constants_exact(self):
        # Toward-ligand step: 2.5 A per the Phase-8.2 human disposition
        # (STATE.md Phase 8.2 Decisions, 2026-10-11: toward_step 2.5,
        # toward_accel none -- NO acceleration constants exist to pin).
        # 2026-10-18 pivot: the nudge-step / keyboard-rotation-step /
        # panel-Rotate-step pins left with their constants (deletion
        # research T5 row); TOWARD + colors keep.
        self.assertEqual(wizard_core.TOWARD_STEP, 2.5)
        self.assertEqual(wizard_core.HIGHLIGHT_COLOR, 'green')
        self.assertEqual(wizard_core.HINT_COLOR, 'orange')

    def test_hint_color_is_a_string(self):
        # 'orange' is a registered named color on this PyMOL 2.5.0 build
        # (Color.cpp:1039; live probe index 13) and must stay a plain
        # str so cmd.color(HINT_COLOR, ...) consumes it directly.
        self.assertIsInstance(wizard_core.HINT_COLOR, str)
        self.assertNotEqual(wizard_core.HINT_COLOR,
                            wizard_core.HIGHLIGHT_COLOR)

    def test_constants_are_float_steps(self):
        # 2026-10-18 pivot: the three deleted constants' isinstance rows
        # removed with the constants (same dated bridge as the class
        # docstring); TOWARD_STEP keeps.
        self.assertIsInstance(wizard_core.TOWARD_STEP, float)


class TestDragScaleMath(unittest.TestCase):
    """Unit battery for the 08.3-04 pure drag-scale math (Phase 8.3).

    ``aamatch/wizard_core.py`` carries the pure half of the C-side drag
    path (SceneMouse.cpp:1479-1507) -- ``a_per_px`` (vScale) and
    ``drag_world_step`` (the pixel delta -> world delta). Both are
    probe-receipted against PyMOL 2.5.0 (probe_083c C1/C2, transcribed
    in 08.3-RESEARCH-drag.md RQ3); this class makes those receipts
    permanent, machine-checked unit pins so SMOKE-24 row 7 (08.3-14)
    drives an already-unit-proven seam end-to-end.

    Import floor: stdlib ``math`` (module-level, for the norm check)
    plus ``aamatch.wizard_core`` ONLY -- this file stays pure (no
    pymol/Qt/numpy); tests/test_purity.py gates the production module.

    Formula receipt (probe C1)::

        vScale [A/px] = depth * 2 * tan(fov * pi / 360) / viewport_h
        depth         = -view[11]

    Probe G (the real seed-42 start view): viewport 640x480, fov 20,
    depth = 97.2456 -> A/px = 0.07145 (exact double 0.071445929...).
    Probe 083c C2: the ``drag_world_step`` -> ``view_camera_to_world``
    R^T equivalence at full SO(3) holds element-for-element, dev
    0.00e+00.
    """

    # Probe G / probe_083c C1 case: the real seed-42 start view's depth
    # component (view[11] = -97.2456; origin row from the P1-POSTSTART
    # view receipt). Identity rotation so the expected world step is a
    # hand-readable (dx*s, 0, 0); the SO(3) cases below swap only the
    # rotation block.
    PROBE_G_VIEW = (1.0, 0.0, 0.0,
                    0.0, 1.0, 0.0,
                    0.0, 0.0, 1.0,
                    0.0, 0.0, -97.2456,     # origin: view[11] = -97.2456
                    0.158331, 0.149332, 9.2822,
                    76.6692, 117.822, -20.0)

    # The probe-G depth tail (origin + slabs), appended to each rotation
    # block reused from TestViewCameraToWorldFullSO3's 08.2-02 fixtures.
    PROBE_G_TAIL = (0.0, 0.0, -97.2456,
                    0.158331, 0.149332, 9.2822,
                    76.6692, 117.822, -20.0)

    def _so3_views(self):
        """[(name, view)]: >= 3 orthogonal blocks + identity, each with
        the probe-G depth tail so ``a_per_px`` is a realistic positive
        scale. Rotation blocks are the 08.2-02 fixture literals already
        in this file (anti-tautology: literals, not runtime products)."""
        fixture = TestViewCameraToWorldFullSO3
        return (
            ('identity', self.PROBE_G_VIEW),
            ('S2-actual-poststart', fixture.S2_VIEW[0:9] + self.PROBE_G_TAIL),
            ('S3-Rx30-Ry50-Rz20', fixture.S3_VIEW[0:9] + self.PROBE_G_TAIL),
            ('S4-Rz200-Rx25', fixture.S4_VIEW[0:9] + self.PROBE_G_TAIL),
        )

    def test_a_per_px_probe_g_exact(self):
        # Probe G measured 0.07145 A/px at the real seed-42 start view
        # (drag research RQ3 / probe_083c C1 "calc=0.07145"). The probe
        # printed 5 decimals, hence places=5 against the measurement;
        # the deterministic pure-double value is pinned at 1e-12.
        s = wizard_core.a_per_px(self.PROBE_G_VIEW, 480.0, 20.0)
        self.assertAlmostEqual(s, 0.07145, places=5)
        self.assertAlmostEqual(s, 0.07144592931326292, delta=1e-12)
        # Gameplay sanity (RQ3): one TOWARD-like 2.5 A is ~35 px at this
        # view, and the identity rotation maps the drag straight to
        # world +x.
        step = wizard_core.drag_world_step(self.PROBE_G_VIEW, 35, 0, 480.0)
        self.assertAlmostEqual(step[0], 35.0 * s, delta=1e-12)
        self.assertEqual(step[1], 0.0)
        self.assertEqual(step[2], 0.0)

    def test_drag_world_step_rt_equivalence_full_so3(self):
        # Probe 083c C2: per motion event the C path conjugates the
        # camera A/px vector by R^T (SceneMouse.cpp:1492-1502) -- the
        # EXACT convention view_camera_to_world implements. Both call
        # paths share the same code, so the equality is exact up to
        # float() coercion (delta 1e-12); the hand-derived row sum below
        # keeps the pin non-tautological.
        for name, view in self._so3_views():
            s = wizard_core.a_per_px(view, 480.0)
            for dx, dy in ((5.0, 0.0), (0.0, -7.0), (13.0, 21.0)):
                with self.subTest(view=name, dx=dx, dy=dy):
                    actual = wizard_core.drag_world_step(view, dx, dy, 480.0)
                    composite = wizard_core.view_camera_to_world(
                        view, (dx * s, dy * s, 0.0))
                    for got, want in zip(actual, composite):
                        self.assertAlmostEqual(got, want, delta=1e-12)
                    # R^T . (dx*s, dy*s, 0) = dx*s * ROW0 + dy*s * ROW1
                    # (rows of the row-major view[0:9] block).
                    expected = (dx * s * view[0] + dy * s * view[3],
                                dx * s * view[1] + dy * s * view[4],
                                dx * s * view[2] + dy * s * view[5])
                    for got, want in zip(actual, expected):
                        self.assertAlmostEqual(got, want, delta=1e-12)
                    # House vec3 contract: plain float 3-tuple out.
                    self.assertIsInstance(actual, tuple)
                    self.assertEqual(len(actual), 3)
                    self.assertTrue(all(isinstance(v, float)
                                        for v in actual))

    def test_a_per_px_refusals(self):
        # Fail-closed house convention (ValueError naming the cause).
        view = self.PROBE_G_VIEW
        for bad_h in (0, -1, -480.0):
            with self.subTest(viewport_h=bad_h):
                with self.assertRaises(ValueError) as cm:
                    wizard_core.a_per_px(view, bad_h)
                self.assertIn('viewport_h', str(cm.exception))
        for bad_fov in (0.0, -20.0):
            with self.subTest(fov=bad_fov):
                with self.assertRaises(ValueError) as cm:
                    wizard_core.a_per_px(view, 480, bad_fov)
                self.assertIn('fov', str(cm.exception))
        # A view too short to carry view[11] (the depth component).
        with self.assertRaises(ValueError) as cm:
            wizard_core.a_per_px(view[:11], 480)
        self.assertIn('12', str(cm.exception))
        # drag_world_step inherits both refusals (fail-closed by
        # construction -- it delegates to a_per_px).
        with self.assertRaises(ValueError):
            wizard_core.drag_world_step(view, 1.0, 1.0, 0)
        with self.assertRaises(ValueError):
            wizard_core.drag_world_step(view, 1.0, 1.0, 480, fov=-1.0)
        # NOT refused: depth <= 0. A camera origin at/behind the scene
        # maps to a non-positive scale; the formula stays honest (returns
        # <= 0) rather than crashing -- recorded semantics for this pin.
        zero_depth = view[:11] + (0.0,) + view[12:]
        self.assertEqual(wizard_core.a_per_px(zero_depth, 480), 0.0)
        behind = view[:11] + (5.0,) + view[12:]   # view[11] = +5 -> depth -5
        self.assertLess(wizard_core.a_per_px(behind, 480), 0.0)


if __name__ == '__main__':
    unittest.main()
