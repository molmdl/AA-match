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
    movement model from 03-RESEARCH-movement-spike.md)."""

    def test_constants_exact(self):
        self.assertEqual(wizard_core.NUDGE_STEP, 1.0)
        self.assertEqual(wizard_core.ROTATE_STEP_DEG, 10.0)
        self.assertEqual(wizard_core.ROTATE_BUTTON_STEP_DEG, 90.0)
        self.assertEqual(wizard_core.HIGHLIGHT_COLOR, 'green')

    def test_constants_are_float_steps(self):
        self.assertIsInstance(wizard_core.NUDGE_STEP, float)
        self.assertIsInstance(wizard_core.ROTATE_STEP_DEG, float)
        self.assertIsInstance(wizard_core.ROTATE_BUTTON_STEP_DEG, float)


if __name__ == '__main__':
    unittest.main()
