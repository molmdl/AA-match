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

from aamatch import capability, detector, generator
from aamatch.generator import (
    GenerationError,
    GRID_SPACING,
    GAP_MARGIN,
    INTER_GRID_MARGIN,
    allocate_slots,
    derive_required,
    difficulty_params,
    placement_offset,
    slot_position,
)
from aamatch.setup_state import INTERACTION_TYPES

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


# ---------------------------------------------------------------------------
# Task 2: required-set derivation (OQ-1 semantics) + slot allocation
# (GEN-04) + the generator<->detector agreement cross-check (DETECT-04).
# Ligand profiles mirror the shape capability.ligand_profile() returns
# (hand-built; the generator never sees atoms).
# ---------------------------------------------------------------------------

def profile(has_donor=False, has_acceptor=False, charge_signs=(),
            ring_count=0, has_hydrophobe=False, has_halogen_donor=False,
            has_metal=False):
    """Hand-built ligand chemistry profile (capability.ligand_profile
    shape) for polarity/support tests."""
    return {
        'has_donor': has_donor,
        'has_acceptor': has_acceptor,
        'charge_signs': set(charge_signs),
        'ring_count': ring_count,
        'has_hydrophobe': has_hydrophobe,
        'has_halogen_donor': has_halogen_donor,
        'has_metal': has_metal,
    }


# A ligand carrying every feature: all 7 types supportable.
RICH = profile(has_donor=True, has_acceptor=True, charge_signs=('+', '-'),
               ring_count=2, has_hydrophobe=True, has_halogen_donor=True,
               has_metal=True)

ALL_TYPES = list(INTERACTION_TYPES)


def setup_of(mode, allowed, molecules=1, difficulty=3):
    """A validated setup_state dict (the generator's real input shape)."""
    from aamatch.setup_state import validate_state
    return validate_state({
        'interaction_mode': mode,
        'allowed_interactions': list(allowed),
        'molecules_per_level': molecules,
        'difficulty_levels': difficulty,
    })


class TestDeriveRequiredModeSemantics(unittest.TestCase):
    """OQ-1 mode semantics (gate §4.3) + OQ-5 hydrophobic exclusion
    (gate §4.5), transcribed row for row from the APPROVED gate doc."""

    def test_exclusive_is_any_scoped_by_allowed(self):
        setup = setup_of('exclusive', ['h_bond', 'pi_stacking'])
        required = derive_required(setup, RICH, random.Random(1), 3)
        self.assertEqual(required, {'mode': 'any', 'items': []})

    def test_exclusive_empty_allowed_refused_naming_the_field(self):
        setup = setup_of('exclusive', [])
        with self.assertRaises(GenerationError) as ctx:
            derive_required(setup, RICH, random.Random(1), 3)
        self.assertIn('allowed_interactions', str(ctx.exception))

    def test_exclusive_unsupported_allowed_refused(self):
        setup = setup_of('exclusive', ['halogen'])
        apolar = profile()                       # supports nothing
        with self.assertRaises(GenerationError) as ctx:
            derive_required(setup, apolar, random.Random(1), 3)
        self.assertIn('supports none', str(ctx.exception))

    def test_block_exclusive_items_are_exactly_the_checked_set(self):
        setup = setup_of('block_exclusive',
                         ['h_bond', 'salt_bridge', 'pi_stacking'])
        required = derive_required(setup, RICH, random.Random(1), 3)
        self.assertEqual(required['mode'], 'list')
        self.assertEqual(required['items'], [
            {'type': 'h_bond', 'count': 1},
            {'type': 'salt_bridge', 'count': 1},
            {'type': 'pi_stacking', 'count': 1},
        ])                                   # canonical INTERACTION_TYPES order

    def test_block_exclusive_unsupported_type_refused_naming_it(self):
        setup = setup_of('block_exclusive', ['h_bond', 'halogen'])
        no_halogen = profile(has_donor=True, has_acceptor=True)
        with self.assertRaises(GenerationError) as ctx:
            derive_required(setup, no_halogen, random.Random(1), 3)
        self.assertIn('halogen', str(ctx.exception))

    def test_block_exclusive_hydrophobic_reachable_via_explicit_check(self):
        # OQ-5: hydrophobic can appear ONLY via block_exclusive explicit
        # check -- and here it must NOT be silently degraded.
        setup = setup_of('block_exclusive', ['hydrophobic'])
        apolar = profile(has_hydrophobe=True)
        required = derive_required(setup, apolar, random.Random(1), 3)
        self.assertEqual(required['items'],
                         [{'type': 'hydrophobic', 'count': 1}])

    def test_block_exclusive_empty_allowed_refused(self):
        setup = setup_of('block_exclusive', [])
        with self.assertRaises(GenerationError) as ctx:
            derive_required(setup, RICH, random.Random(1), 3)
        self.assertIn('no interactions checked', str(ctx.exception))

    def test_unset_samples_from_supported_intersection(self):
        setup = setup_of('unset', ALL_TYPES)
        two_feature = profile(has_donor=True, has_acceptor=True,
                              charge_signs=('-',))
        required = derive_required(setup, two_feature, random.Random(4), 7)
        self.assertEqual(required['mode'], 'list')
        # supported (minus hydrophobic per OQ-5): h_bond + salt_bridge;
        # k clamps down to 2 -- a 2-feature ligand at tier 9 still gets 2.
        self.assertEqual([item['type'] for item in required['items']],
                         ['h_bond', 'salt_bridge'])
        self.assertTrue(all(item['count'] == 1
                            for item in required['items']))

    def test_unset_excludes_hydrophobic_from_sampling(self):
        # OQ-5 example from the plan: a ligand supporting only
        # hydrophobic + h_bond samples from the REMAINDER.
        setup = setup_of('unset', ALL_TYPES)
        hb_hydro = profile(has_donor=True, has_acceptor=True,
                           has_hydrophobe=True)
        for seed in range(20):
            required = derive_required(setup, hb_hydro,
                                       random.Random(seed), 2)
            types = [item['type'] for item in required['items']]
            self.assertNotIn('hydrophobic', types)
            self.assertEqual(types, ['h_bond'])   # the only remainder

    def test_unset_only_hydrophobic_refused_naming_the_policy(self):
        setup = setup_of('unset', ALL_TYPES)
        apolar = profile(has_hydrophobe=True)
        with self.assertRaises(GenerationError) as ctx:
            derive_required(setup, apolar, random.Random(1), 3)
        self.assertIn('hydrophobic', str(ctx.exception))

    def test_unset_empty_allowed_draws_from_all_types(self):
        # OQ-1: unset + empty allowed -> the game picks (from the
        # non-hydrophobic types; OQ-5 still binds the sampling pool).
        setup = setup_of('unset', [])
        outcomes = set()
        for seed in range(20):
            required = derive_required(setup, RICH, random.Random(seed), 3)
            types = [item['type'] for item in required['items']]
            self.assertNotIn('hydrophobic', types)
            self.assertEqual(types, [t for t in ALL_TYPES if t in types])
            outcomes.add(tuple(types))
        self.assertTrue(outcomes,
                        'unset + empty allowed must still draw items')
        self.assertGreater(len(outcomes), 1,
                           'multiple seeds must be able to differ')

    def test_unset_empty_allowed_featureless_ligand_refused(self):
        setup = setup_of('unset', [])
        with self.assertRaises(GenerationError):
            derive_required(setup, profile(), random.Random(1), 3)

    def test_unset_items_stay_within_allowed_and_canonical(self):
        setup = setup_of('unset', ['pi_stacking', 'h_bond', 'cation_pi'])
        for seed in range(20):
            required = derive_required(setup, RICH, random.Random(seed), 2)
            types = [item['type'] for item in required['items']]
            for t in types:
                self.assertIn(t, ('h_bond', 'pi_stacking', 'cation_pi'))
            self.assertEqual(types, sorted(types, key=ALL_TYPES.index))

    def test_unset_deterministic_per_seed(self):
        setup = setup_of('unset', ALL_TYPES)
        first = derive_required(setup, RICH, random.Random(11), 3)
        second = derive_required(setup, RICH, random.Random(11), 3)
        self.assertEqual(first, second)

    def test_unknown_mode_refused(self):
        setup = setup_of('unset', ALL_TYPES)
        setup['interaction_mode'] = 'bogus'
        with self.assertRaises(GenerationError):
            derive_required(setup, RICH, random.Random(1), 3)


class TestAllocateSlots(unittest.TestCase):
    """GEN-04 solvability by construction: one dedicated capable slot per
    required item, distractors from all 20 AAs, truthful can_form."""

    def _items(self, types):
        return [{'type': t, 'count': 1} for t in types]

    def test_one_dedicated_required_slot_per_item(self):
        items = self._items(['h_bond', 'pi_stacking', 'salt_bridge'])
        slots = allocate_slots(items, 3, RICH, random.Random(2))
        self.assertEqual(len(slots), 9)
        required = [s for s in slots if s['role'] == 'required']
        self.assertEqual(len(required), 3)
        self.assertEqual(sorted(s['can_form'][0] for s in required),
                         ['h_bond', 'pi_stacking', 'salt_bridge'])
        # required slots are unique and carry can_form=[their type]
        self.assertEqual(len(set(s['slot_id'] for s in required)), 3)
        for slot in required:
            self.assertEqual(len(slot['can_form']), 1)

    def test_grid_shape_and_ids_cover_full_range(self):
        slots = allocate_slots(self._items(['h_bond']), 4, RICH,
                               random.Random(3))
        self.assertEqual(len(slots), 16)
        ids = set()
        coords = set()
        for slot in slots:
            ids.add(slot['slot_id'])
            coords.add((slot['row'], slot['col']))
            self.assertEqual(slot['slot_id'],
                             'r%dc%d' % (slot['row'], slot['col']))
        self.assertEqual(len(ids), 16)
        self.assertEqual(coords,
                         set((r, c) for r in range(4) for c in range(4)))

    def test_can_form_is_truthful_against_capability(self):
        for seed in range(5):
            slots = allocate_slots(
                self._items(['h_bond', 'metal', 'cation_pi']), 4, RICH,
                random.Random(seed))
            for slot in slots:
                for t in slot['can_form']:
                    self.assertTrue(
                        capability.aa_capable(slot['aa'], t, RICH),
                        'can_form lie: %s cannot form %s'
                        % (slot['aa'], t))
                self.assertIn(slot['aa'], capability.AA_RESIDUES)

    def test_distractors_drawn_from_all_20_aas(self):
        slots = allocate_slots(self._items(['h_bond']), 3, RICH,
                               random.Random(4))
        distractors = [s for s in slots if s['role'] == 'distractor']
        self.assertEqual(len(distractors), 8)
        for slot in distractors:
            self.assertEqual(slot['can_form'], [])
            self.assertIn(slot['aa'], sorted(capability.AA_RESIDUES))

    def test_grid_too_small_refused(self):
        items = self._items(ALL_TYPES + ['h_bond', 'pi_stacking'])  # 9
        with self.assertRaises(GenerationError) as ctx:
            allocate_slots(items, 3, RICH, random.Random(5))
        self.assertIn('too small', str(ctx.exception))

    def test_no_capable_aa_refused_naming_the_type(self):
        items = self._items(['salt_bridge'])
        no_charges = profile(has_donor=True, has_acceptor=True)
        with self.assertRaises(GenerationError) as ctx:
            allocate_slots(items, 3, no_charges, random.Random(6))
        self.assertIn('salt_bridge', str(ctx.exception))

    def test_deterministic_per_seed(self):
        items = self._items(['h_bond', 'pi_stacking'])
        first = allocate_slots(items, 3, RICH, random.Random(7))
        second = allocate_slots(items, 3, RICH, random.Random(7))
        self.assertEqual(first, second)

    def test_seeds_vary_the_grid(self):
        items = self._items(['h_bond'])
        seen = set()
        for seed in range(6):
            slots = allocate_slots(items, 3, RICH, random.Random(seed))
            seen.add(tuple((s['slot_id'], s['aa']) for s in slots))
        self.assertGreater(len(seen), 1, 'seeds must vary the allocation')


class TestDetectorAgreement(unittest.TestCase):
    """DETECT-04 cross-check on synthetic geometry (real dependency on
    02-06): a required slot's AA placed within h_bond geometry of a
    synthetic ligand donor must BOTH be capability-capable AND yield a
    detector h_bond record -- "capable" and "detectable" agree through
    the SAME capability tables."""

    @staticmethod
    def _scene(resn):
        """SER (acceptor OG) or VAL (no typed role) at the origin; a
        ligand O-H donor collinear at 3.0 A (D...A <= 4.0, angle at H
        = 180 >= 140)."""
        aa = {'side': 'aa', 'object': '_aam_aa_r0c0', 'id': 1,
              'name': 'OG', 'elem': 'O', 'resn': resn, 'resi': 1,
              'alt': '', 'x': 0.0, 'y': 0.0, 'z': 0.0}
        lig_o = {'side': 'lig', 'object': '_aam_lig', 'id': 1,
                 'name': 'O1', 'elem': 'O', 'resn': 'LIG', 'resi': 1,
                 'alt': '', 'x': 3.0, 'y': 0.0, 'z': 0.0}
        lig_h = {'side': 'lig', 'object': '_aam_lig', 'id': 2,
                 'name': 'H1', 'elem': 'H', 'resn': 'LIG', 'resi': 1,
                 'alt': '', 'x': 2.04, 'y': 0.0, 'z': 0.0}
        return [aa, lig_o, lig_h], [(0, 1, 1)]

    def test_capable_aa_is_detectable(self):
        atoms, bonds = self._scene('SER')
        prof = capability.ligand_profile(
            [a for a in atoms if a['side'] == 'lig'], bonds)
        self.assertTrue(capability.aa_capable('SER', 'h_bond', prof),
                        'capability says SER cannot h_bond a donor '
                        'ligand -- table/detector drift')
        records = detector.detect_part1(atoms, bonds)
        hits = [r for r in records
                if r['type'] == 'h_bond' and r['aa']['resn'] == 'SER']
        self.assertEqual(len(hits), 1,
                         'detector missed the SER h_bond: %r' % (records,))
        self.assertEqual(hits[0]['aa']['role'], 'acceptor')

    def test_incapable_aa_is_not_detected(self):
        atoms, bonds = self._scene('VAL')
        prof = capability.ligand_profile(
            [a for a in atoms if a['side'] == 'lig'], bonds)
        self.assertFalse(capability.aa_capable('VAL', 'h_bond', prof))
        records = detector.detect_part1(atoms, bonds)
        hits = [r for r in records if r['type'] == 'h_bond']
        self.assertEqual(hits, [],
                         'detector fired where capability says incapable')

    def test_detector_result_feeds_allocate_pool(self):
        # The full agreement chain: the profile typed from the SAME
        # synthetic ligand puts SER in allocate_slots' capable pool.
        atoms, bonds = self._scene('SER')
        prof = capability.ligand_profile(
            [a for a in atoms if a['side'] == 'lig'], bonds)
        slots = allocate_slots([{'type': 'h_bond', 'count': 1}], 3, prof,
                               random.Random(8))
        required = [s for s in slots if s['role'] == 'required']
        self.assertEqual(len(required), 1)
        self.assertIn(required[0]['aa'],
                      ('SER', 'THR', 'TYR', 'ASN', 'GLN', 'ASP', 'GLU',
                       'HIS', 'CYS', 'LYS', 'ARG'))


if __name__ == '__main__':
    unittest.main()
