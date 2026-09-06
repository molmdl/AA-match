"""The >= 100-seed generator invariant suite (plan 02-12).

ROADMAP Phase-2 success criterion 3 / generation research §8 items 1-19
(items 20-22 are headless-only and belong to 02-13/02-14). This file is
the PERMANENT proof that GEN-01 (determinism/format), GEN-03 (grid
geometry), GEN-04 (solvability by construction) and GEN-05 (difficulty
escalation) hold across the seed corpus -- PITFALL 11 is closed by
invariant assertion, not by inspecting sample outputs.

Invariants test the IMPLEMENTED semantics recorded by 02-08-SUMMARY.md
(never the plan sketches):

- ligand_data contract (02-08 deviation 3): entries keyed by
  (set_id, entry_id) carrying {'centroid', 'radius', 'profile'} where
  'profile' is the capability.ligand_profile shape. The multi-feature
  RICH fixture below (donor + acceptor + anionic + cationic + rings +
  hydrophobe + halogen donor + metal) supports all 7 types.
- Mode semantics (OQ-1 / OQ-5): exclusive = {'mode': 'any', 'items': []}
  (no dedicated slots; coverage is vacuous by construction -- scoring
  is 02-10); block_exclusive = EXACTLY the checked set in canonical
  order (hydrophobic reachable ONLY here); unset = support-filtered
  sampling minus hydrophobic, k = min(n_required_types, len(pool)).
- Difficulty (02-08 deviation 1): INTEGER HALF-UP interpolation
  grid_n = 3 + frac / n_required_types = 1 + frac / size thirds.
- Distinctness is measured with the 'seed' echo stripped (the payload
  carries its own seed; comparing raw bytes would trivially pass and
  catch nothing).

Sweep: 100 seeds x D in {1, 3, 10} x all 3 modes x molecules in {1, 2}
= 18 configurations x 100 seeds = 1800 payloads (research §8 preamble:
never below 100 seeds per swept dimension pair). Determinism doubles
the generation work. Runs under bare python3.6, stdlib only, zero
sys.modules stubs; module-level lazy corpus built once and shared by
every invariant group. Recorded runtime: ~51 s wall for this file
alone on the WSL dev host (~56 s with the full suite including the
pre-existing 438 tests).
"""

import json
import math
import unittest

from aamatch import capability
from aamatch.capability import AA_RESIDUES, aa_capable, ligand_support
from aamatch.generator import (
    GAP_MARGIN,
    GRID_SPACING,
    GenerationError,
    generate,
)
from aamatch.level_spec import (
    DETECTOR_VERSION,
    LEVEL_SPEC_VERSION,
    make_level_spec_container,
    parse_level_spec_dict,
)
from aamatch.setup_state import INTERACTION_TYPES, validate_state

EPS = 1e-9
SPACING2 = GRID_SPACING * GRID_SPACING

SEEDS = list(range(100))
DISTINCT_FLOOR = 95                      # research §8 item 4

DIFFICULTY_SWEEP = (1, 3, 10)
MOLECULES_SWEEP = (1, 2)

# Legal per-mode allowed_interactions for the sweep. exclusive needs a
# non-empty realistic checked set; block_exclusive checks ALL types
# (the only OQ-5-legit route to a required hydrophobic; every type has
# a capable AA against RICH so D=1's 3x3 grid still fits 7 + 1 slots);
# unset uses the empty list ("the game picks", OQ-1 harmonized with the
# support-filter edge ruling) so the full 6-type sample pool is drawn.
EXCLUSIVE_ALLOWED = ('h_bond', 'salt_bridge', 'pi_stacking')
BLOCK_ALLOWED = tuple(INTERACTION_TYPES)
MODE_CONFIGS = (
    ('exclusive', EXCLUSIVE_ALLOWED),
    ('block_exclusive', BLOCK_ALLOWED),
    ('unset', ()),
)

SET_ID = 'demo-dev-1'
CENTROID = (0.0, 0.0, 0.0)
RADIUS = 4.0


def synthetic_profile(**overrides):
    """Hand-built ligand chemistry profile (capability.ligand_profile
    shape; WSL-pure, NO atoms/manifest/file reads -- the generator
    never sees atoms). Defaults support nothing."""
    profile = {
        'has_donor': False,
        'has_acceptor': False,
        'charge_signs': set(),
        'ring_count': 0,
        'has_hydrophobe': False,
        'has_halogen_donor': False,
        'has_metal': False,
    }
    profile.update(overrides)
    return profile


# The multi-feature fixture: exercises all 7 interaction types.
RICH = synthetic_profile(
    has_donor=True, has_acceptor=True, charge_signs=set(('+', '-')),
    ring_count=2, has_hydrophobe=True, has_halogen_donor=True,
    has_metal=True)

HALOGEN_FREE = synthetic_profile(has_donor=True, has_acceptor=True,
                                 charge_signs=set(('+', '-')), ring_count=2)


def candidate(entry_id, size_class='small', protonation='standard'):
    """One manifest-shaped candidate row (enumerate_entries shape: the
    entry's fields plus 'set_id' -- the schema frozen at 02-03)."""
    heavy = {'small': 9, 'medium': 40, 'large': 80}[size_class]
    return {
        'set_id': SET_ID,
        'entry_id': entry_id,
        'file': 'ligands/%s.sdf' % entry_id,
        'format': 'sdf',
        'sha256': 'a' * 64,
        'protonation': protonation,
        'atom_count': heavy + 7,
        'heavy_atom_count': heavy,
        'bond_count': heavy + 7,
        'bond_order_counts': {'1': 12, '2': 4},
        'formal_charge_sum': 0,
        'states_expected': 1,
        'metal_present': False,
        'halogen_present': False,
        'size_class': size_class,
    }


# Two candidates per size bucket (m=2 distinct picks are legal in every
# bucket; the nearest-bucket supply fallback therefore never fires
# here -- it is 02-08-covered).
ENTRY_IDS = {
    'small': ('acetate', 'benzamide'),
    'medium': ('naphthalene', 'anthracene'),
    'large': ('coronene', 'pentacene'),
}
CANDIDATES = [candidate(entry_id, size_class)
              for size_class in ('small', 'medium', 'large')
              for entry_id in ENTRY_IDS[size_class]]

# The 02-08 ligand_data CONTRACT: (set_id, entry_id) -> {'centroid',
# 'radius', 'profile'}.
LIGAND_DATA = dict(
    ((row['set_id'], row['entry_id']),
     {'centroid': CENTROID, 'radius': RADIUS, 'profile': RICH})
    for row in CANDIDATES)


def make_setup(mode, allowed, molecules, difficulty):
    """A validated setup_state dict (the generator's real input
    shape -- validate_state canonicalizes allowed_interactions into
    INTERACTION_TYPES order, matching the real Setup flow)."""
    return validate_state({
        'interaction_mode': mode,
        'allowed_interactions': list(allowed),
        'molecules_per_level': molecules,
        'difficulty_levels': difficulty,
    })


# ---------------------------------------------------------------------------
# Corpus: module-level lazy singleton -- 1800 payloads generated once,
# shared by every invariant group (generation is the dominant cost).
# Key: (config_index, difficulty, molecules_per_level) -> list of 100
# payloads, one per seed in SEEDS.
# ---------------------------------------------------------------------------

_CORPUS = None


def corpus():
    global _CORPUS
    if _CORPUS is None:
        _CORPUS = {}
        for config_index, (mode, allowed) in enumerate(MODE_CONFIGS):
            for difficulty in DIFFICULTY_SWEEP:
                for molecules in MOLECULES_SWEEP:
                    setup = make_setup(mode, allowed, molecules, difficulty)
                    _CORPUS[(config_index, difficulty, molecules)] = [
                        generate(seed, setup, CANDIDATES, LIGAND_DATA,
                                 difficulty)
                        for seed in SEEDS]
    return _CORPUS


def payload_bytes(payload):
    """Canonical byte form: json.dumps(sort_keys=True)."""
    return json.dumps(payload, sort_keys=True)


def seedless_bytes(payload):
    """Byte form with the seed echo stripped -- cross-seed
    distinctness must measure level CONTENT (research §8 item 4)."""
    stripped = dict(payload)
    stripped.pop('seed')
    return json.dumps(stripped, sort_keys=True)


def molecule_profile(molecule):
    """The ligand profile the generator derived this molecule's
    required set and slot capability against."""
    return LIGAND_DATA[(molecule['ligand']['set_id'],
                        molecule['ligand']['entry_id'])]['profile']


def iter_molecules(payload):
    for level in payload['levels']:
        for molecule in level['molecules']:
            yield level, molecule


def sweep_violations(points, limit2=SPACING2):
    """Count position pairs closer than sqrt(limit2) (minus EPS), via
    an exhaustive sorted-x sliding window: any pair violating the limit
    must have |dx| < limit, so the window misses nothing. O(k log k +
    k*w) with w the window occupancy (<= grid side on a correct
    lattice) -- full O(k^2) over 1800 payloads would dominate runtime
    for no added rigor."""
    ordered = sorted(points)
    violations = 0
    count = len(ordered)
    for i in range(count):
        xi, yi, zi = ordered[i]
        for j in range(i + 1, count):
            xj, yj, zj = ordered[j]
            dx = xj - xi
            d2 = dx * dx
            if d2 >= limit2:
                break                    # sorted: no later j can qualify
            dy = yj - yi
            dz = zj - zi
            if d2 + dy * dy + dz * dz < limit2 - EPS:
                violations += 1
    return violations


def slot_positions(molecule):
    return [tuple(slot['grid_pose']['position'])
            for slot in molecule['grid']['slots']]


def world_positions(molecule):
    """grid_pose.position + placement.offset -- the materializer's
    world frame (offset applied to ligand + grid TOGETHER)."""
    offset = molecule['placement']['offset']
    return [(pos[0] + offset[0], pos[1] + offset[1], pos[2] + offset[2])
            for pos in slot_positions(molecule)]


def profile_vocabulary(mode, allowed):
    """The type vocabulary required items may come from, per mode
    (OQ-1 / OQ-5 semantics over the IMPLEMENTED derivation)."""
    if mode == 'unset':
        base = allowed if allowed else INTERACTION_TYPES
        return [t for t in INTERACTION_TYPES
                if t in base and t != 'hydrophobic']
    return [t for t in INTERACTION_TYPES if t in allowed]


def sample_pool(mode, allowed, profile):
    """The exact supported pool derive_required draws items from
    (unset: OQ-5 hydrophobic exclusion; block/exclusive: the checked
    set)."""
    return [t for t in profile_vocabulary(mode, allowed)
            if ligand_support(t, profile)]


# ---------------------------------------------------------------------------
# Group A (research §8 items 1-4): determinism, round-trip, version
# stamps, cross-seed distinctness.
# ---------------------------------------------------------------------------

class TestDeterminismAndFormat(unittest.TestCase):

    def test_A1_byte_determinism_same_seed(self):
        data = corpus()
        for key, payloads in data.items():
            mode, allowed = MODE_CONFIGS[key[0]]
            setup = make_setup(mode, allowed, key[2], key[1])
            for index, seed in enumerate(SEEDS):
                with self.subTest(config=key, seed=seed):
                    again = generate(seed, setup, CANDIDATES, LIGAND_DATA,
                                     key[1])
                    self.assertEqual(payload_bytes(again),
                                     payload_bytes(payloads[index]),
                                     'same seed + inputs must be '
                                     'byte-identical (GEN-01)')

    def test_A2_roundtrip_through_level_spec_gates(self):
        for key, payloads in corpus().items():
            for payload in payloads:
                with self.subTest(config=key, seed=payload['seed']):
                    parsed = parse_level_spec_dict(
                        make_level_spec_container(payload))
                    self.assertEqual(parsed, payload,
                                     'payload must round-trip '
                                     'parse_level_spec_dict('
                                     'make_level_spec_container()) '
                                     'unchanged (GEN-01)')

    def test_A3_version_stamps_and_seed_type(self):
        for key, payloads in corpus().items():
            for index, payload in enumerate(payloads):
                with self.subTest(config=key, seed=index):
                    self.assertEqual(payload['detector_version'],
                                     DETECTOR_VERSION)
                    self.assertEqual(payload['format_version'],
                                     LEVEL_SPEC_VERSION)
                    self.assertIsInstance(payload['seed'], int)
                    self.assertNotIsInstance(payload['seed'], bool,
                                             'a bool seed can never '
                                             'appear')
                    self.assertEqual(payload['seed'], SEEDS[index])

    def test_A4_cross_seed_distinctness_at_least_95_of_100(self):
        for key, payloads in corpus().items():
            distinct = len(set(seedless_bytes(p) for p in payloads))
            with self.subTest(config=key):
                self.assertGreaterEqual(
                    distinct, DISTINCT_FLOOR,
                    'config %r: only %d/%d distinct level contents '
                    '(accidental constant-generation?)'
                    % (key, distinct, len(payloads)))


# ---------------------------------------------------------------------------
# Group B (research §8 items 5-8): solvability-by-construction, can_form
# truthfulness, OQ-1/OQ-5 mode semantics, feasibility refusals.
# ---------------------------------------------------------------------------

class TestSolvability(unittest.TestCase):

    def test_B5_required_coverage_dedicated_slots(self):
        for key, payloads in corpus().items():
            for payload in payloads:
                for level, molecule in iter_molecules(payload):
                    required = molecule['required']
                    if required['mode'] != 'list':
                        continue     # 'any' mode: vacuous by construction
                    slots = molecule['grid']['slots']
                    with self.subTest(config=key, seed=payload['seed'],
                                      level=level['level_index'],
                                      mol=molecule['molecule_id']):
                        for item in required['items']:
                            dedicated = len([
                                slot for slot in slots
                                if slot['role'] == 'required'
                                and item['type'] in slot['can_form']])
                            self.assertGreaterEqual(
                                dedicated, item['count'],
                                'required item %r lacks its dedicated '
                                'capable slot (GEN-04)' % (item,))

    def test_B6_can_form_truthfulness_and_role_accounting(self):
        for key, payloads in corpus().items():
            for payload in payloads:
                for level, molecule in iter_molecules(payload):
                    profile = molecule_profile(molecule)
                    required = molecule['required']
                    n_list_items = len(required['items']) \
                        if required['mode'] == 'list' else 0
                    n_required = 0
                    for slot in molecule['grid']['slots']:
                        with self.subTest(config=key,
                                          seed=payload['seed'],
                                          slot=slot['slot_id']):
                            self.assertTrue(all(
                                t in INTERACTION_TYPES
                                for t in slot['can_form']),
                                'can_form outside the enum: %r'
                                % (slot['can_form'],))
                            for itype in slot['can_form']:
                                self.assertTrue(
                                    aa_capable(slot['aa'], itype,
                                               profile),
                                    'can_form LIES: %s cannot form %s '
                                    'with this ligand (GEN-04/DETECT-04)'
                                    % (slot['aa'], itype))
                            if slot['role'] == 'required':
                                n_required += 1
                                self.assertEqual(len(slot['can_form']), 1)
                            else:
                                self.assertEqual(slot['can_form'], [])
                    with self.subTest(config=key, seed=payload['seed'],
                                      level=level['level_index']):
                        self.assertEqual(
                            n_required, n_list_items,
                            'required-slot count must equal the list-'
                            'mode item count (one dedicated slot per '
                            'item); any mode dedicates none')

    def test_B7_mode_semantics(self):
        for key, payloads in corpus().items():
            mode, allowed = MODE_CONFIGS[key[0]]
            for payload in payloads:
                for level, molecule in iter_molecules(payload):
                    required = molecule['required']
                    profile = molecule_profile(molecule)
                    n_types = level['difficulty']['n_required_types']
                    with self.subTest(config=key, seed=payload['seed'],
                                      level=level['level_index']):
                        if mode == 'exclusive':
                            self.assertEqual(
                                required, {'mode': 'any', 'items': []},
                                "exclusive = 'any' scoped by allowed "
                                '(OQ-1)')
                            continue
                        self.assertEqual(required['mode'], 'list')
                        items = required['items']
                        self.assertTrue(all(item['count'] == 1
                                            for item in items),
                                        'v1 required counts are always 1')
                        if mode == 'block_exclusive':
                            self.assertEqual(
                                items,
                                [{'type': t, 'count': 1} for t in allowed],
                                'block_exclusive items must be EXACTLY '
                                'the checked set in canonical order')
                        else:                        # unset
                            item_types = [item['type'] for item in items]
                            self.assertNotIn(
                                'hydrophobic', item_types,
                                'OQ-5: hydrophobic is excluded from '
                                'unset-mode sampling')
                            vocabulary = profile_vocabulary(mode, allowed)
                            self.assertTrue(all(
                                t in vocabulary for t in item_types),
                                'unset items outside the vocabulary '
                                '(allowed or all-non-hydrophobic)')
                            pool = sample_pool(mode, allowed, profile)
                            self.assertEqual(
                                len(items),
                                min(n_types, len(pool)),
                                'k must equal min(n_required_types, '
                                'len(supported pool))')
                            canonical = sorted(
                                item_types,
                                key=INTERACTION_TYPES.index)
                            self.assertEqual(item_types, canonical,
                                             'items must re-emit in '
                                             'canonical order')

    def test_B8_feasibility_refusals_name_the_cause(self):
        # block_exclusive with halogen on a halogen-free ligand: refuse
        # NAMING the type (never silently degrade).
        setup = make_setup('block_exclusive', ('h_bond', 'halogen'), 1, 3)
        ligand_data = dict(
            ((row['set_id'], row['entry_id']),
             {'centroid': CENTROID, 'radius': RADIUS,
              'profile': HALOGEN_FREE})
            for row in CANDIDATES)
        with self.assertRaises(GenerationError) as ctx:
            generate(0, setup, CANDIDATES, ligand_data, 3)
        self.assertIn('halogen', str(ctx.exception))

        # exclusive + empty allowed_interactions: refuse naming the
        # setup field.
        setup = make_setup('exclusive', (), 1, 3)
        with self.assertRaises(GenerationError) as ctx:
            generate(0, setup, CANDIDATES, LIGAND_DATA, 3)
        self.assertIn('allowed_interactions', str(ctx.exception))

        # unset + allowed=('hydrophobic',) on a hydrophobe-carrying
        # ligand: the OQ-5 exclusion empties the pool and the refusal
        # names the policy. (With an EMPTY allowed list the vocabulary
        # already excludes hydrophobic, so the same ligand gets the
        # generic 'supports none of the sampleable interactions'
        # refusal -- both are fail-closed.)
        hydro_only = synthetic_profile(has_hydrophobe=True)
        ligand_data = dict(
            ((row['set_id'], row['entry_id']),
             {'centroid': CENTROID, 'radius': RADIUS,
              'profile': hydro_only})
            for row in CANDIDATES)
        setup = make_setup('unset', ('hydrophobic',), 1, 3)
        with self.assertRaises(GenerationError) as ctx:
            generate(0, setup, CANDIDATES, ligand_data, 3)
        self.assertIn('hydrophobic', str(ctx.exception))


# ---------------------------------------------------------------------------
# Group C (research §8 items 9-13): grid shape, non-overlap, beyond-gap,
# global disjointness, float hygiene.
# ---------------------------------------------------------------------------

class TestGridStructure(unittest.TestCase):

    def test_C9_grid_shape_and_slot_identity(self):
        for key, payloads in corpus().items():
            for payload in payloads:
                for level, molecule in iter_molecules(payload):
                    n = level['difficulty']['grid_n']
                    grid = molecule['grid']
                    with self.subTest(config=key, seed=payload['seed'],
                                      level=level['level_index'],
                                      mol=molecule['molecule_id']):
                        self.assertEqual(grid['n'], n)
                        slots = grid['slots']
                        self.assertEqual(len(slots), n * n)
                        coords = sorted((slot['row'], slot['col'])
                                        for slot in slots)
                        self.assertEqual(
                            coords,
                            [(r, c) for r in range(n) for c in range(n)],
                            '(row, col) must cover 0..n-1 exactly once')
                        for slot in slots:
                            self.assertEqual(
                                slot['slot_id'],
                                'r%dc%d' % (slot['row'], slot['col']))
                        self.assertEqual(
                            len(set(slot['slot_id'] for slot in slots)),
                            n * n,
                            'slot_id unique per molecule')

    def test_C10_to_C13_spacing_gap_ceiling_and_finiteness(self):
        for key, payloads in corpus().items():
            for payload in payloads:
                for level, molecule in iter_molecules(payload):
                    n = molecule['grid']['n']
                    points = slot_positions(molecule)
                    with self.subTest(config=key, seed=payload['seed'],
                                      level=level['level_index'],
                                      mol=molecule['molecule_id']):
                        self.assertEqual(
                            sweep_violations(points), 0,
                            'all pairwise slot distances must be >= '
                            'GRID_SPACING')
                        self.assertTrue(all(
                            math.isfinite(v) for pos in points
                            for v in pos),
                            'every serialized position must be finite '
                            '(persistence writes allow_nan=False)')
                        ceiling = (RADIUS + GAP_MARGIN
                                   + n * GRID_SPACING + EPS)
                        centroid = CENTROID
                        gap2 = (RADIUS + GAP_MARGIN) ** 2
                        for pos in points:
                            d2 = sum((pos[k] - centroid[k]) ** 2
                                     for k in range(3))
                            self.assertGreaterEqual(
                                d2, gap2 - EPS,
                                'slot inside the ligand gap: %r' % (pos,))
                            self.assertLessEqual(
                                math.sqrt(d2), ceiling,
                                'beyond-gap but absurdly far (sanity '
                                'ceiling R + GAP_MARGIN + n*SPACING): '
                                '%r' % (pos,))

    def test_C12_cross_molecule_global_disjointness(self):
        for (config_index, difficulty, molecules), payloads in \
                corpus().items():
            if molecules != 2:
                continue
            for payload in payloads:
                for level in payload['levels']:
                    combined = []
                    for molecule in level['molecules']:
                        combined.extend(world_positions(molecule))
                    with self.subTest(
                            config=(config_index, difficulty, molecules),
                            seed=payload['seed'],
                            level=level['level_index']):
                        self.assertEqual(
                            len(set(combined)), len(combined),
                            'no two slots from different molecules may '
                            'share a world position')
                        self.assertEqual(
                            sweep_violations(combined), 0,
                            'cross-molecule world slots must stay >= '
                            'GRID_SPACING apart (offsets obey the '
                            'inter-grid margin)')


# ---------------------------------------------------------------------------
# Group D (research §8 items 14-16): monotonic escalation, clamping
# honesty, cap compliance over ALL legal D in 1..10.
# ---------------------------------------------------------------------------

class TestDifficultyEscalation(unittest.TestCase):

    def test_D14_D16_exactly_D_levels_for_every_legal_D(self):
        # Parametrized over all 10 legal difficulty values (cap 10,
        # human-amended at 01-09 and frozen).
        setup = make_setup('unset', (), 1, 3)
        for difficulty in range(1, 11):
            for seed in SEEDS[:5]:
                payload = generate(seed, setup, CANDIDATES, LIGAND_DATA,
                                   difficulty)
                with self.subTest(D=difficulty, seed=seed):
                    levels = payload['levels']
                    self.assertEqual(len(levels), difficulty)
                    self.assertEqual([level['level_index']
                                      for level in levels],
                                     list(range(difficulty)),
                                     'tiers must be 0..D-1 strictly '
                                     'ascending')
                    for level in levels:
                        self.assertEqual(
                            level['difficulty']['tier'],
                            level['level_index'],
                            'level_index == tier')

    def test_D14_monotonic_escalation_across_levels(self):
        rank = {'small': 0, 'medium': 1, 'large': 2}
        for key, payloads in corpus().items():
            for payload in payloads:
                ns, ks, ranks = [], [], []
                for level in payload['levels']:
                    diff = level['difficulty']
                    ns.append(diff['grid_n'])
                    ks.append(diff['n_required_types'])
                    ranks.append(rank[diff['molecule_size_class']])
                with self.subTest(config=key, seed=payload['seed']):
                    for values, axis in ((ns, 'grid_n'),
                                         (ks, 'n_required_types'),
                                         (ranks, 'size class')):
                        for earlier, later in zip(values, values[1:]):
                            self.assertLessEqual(
                                earlier, later,
                                'difficulty axis %s not monotonic: %r'
                                % (axis, values))

    def test_D15_clamping_honesty(self):
        for key, payloads in corpus().items():
            mode, allowed = MODE_CONFIGS[key[0]]
            for payload in payloads:
                for level, molecule in iter_molecules(payload):
                    diff = level['difficulty']
                    profile = molecule_profile(molecule)
                    pool = sample_pool(mode, allowed, profile)
                    items = molecule['required']['items']
                    with self.subTest(config=key, seed=payload['seed'],
                                      level=level['level_index'],
                                      mol=molecule['molecule_id']):
                        self.assertLessEqual(
                            diff['n_required_types'], 7,
                            'pre-clamp intent must stay within 1..7')
                        self.assertLessEqual(
                            len(items), len(pool),
                            'emitted required.items count must not '
                            'exceed len(supported intersection) -- '
                            'never promise what the ligand cannot do')


# ---------------------------------------------------------------------------
# Group E (research §8 items 17-19 + clamped type coverage): soft corpus
# statistics over a single 100-seed sweep (D=3, unset, 2 molecules) plus
# the full-corpus type-coverage proof. Hydrophobic-required can ONLY be
# sourced from block_exclusive (OQ-5), so type coverage aggregates the
# whole corpus -- that is the recorded 02-08 semantics, not a weakening.
# ---------------------------------------------------------------------------

class TestCorpusStatistics(unittest.TestCase):

    def _unset_sweep(self):
        unset_index = [i for i, c in enumerate(MODE_CONFIGS)
                       if c[0] == 'unset'][0]
        return corpus()[(unset_index, 3, 2)]

    def test_E17a_every_aa_appears_as_a_distractor(self):
        distractors = set()
        for payload in self._unset_sweep():
            for level, molecule in iter_molecules(payload):
                for slot in molecule['grid']['slots']:
                    if slot['role'] == 'distractor':
                        distractors.add(slot['aa'])
        self.assertEqual(distractors, set(AA_RESIDUES),
                         'all 20 AAs must appear as distractors across '
                         'the corpus (a broken distractor pool hides)')

    def test_E17b_no_all_identical_grid(self):
        for payload in self._unset_sweep():
            for level, molecule in iter_molecules(payload):
                slots = molecule['grid']['slots']
                with self.subTest(seed=payload['seed'],
                                  level=level['level_index'],
                                  mol=molecule['molecule_id']):
                    self.assertGreater(
                        len(set(slot['aa'] for slot in slots)), 1,
                        'degenerate all-identical grid')
                    self.assertGreaterEqual(
                        len([slot for slot in slots
                             if slot['role'] == 'distractor']), 1,
                        'every grid keeps at least one distractor slot')

    def test_E18_every_type_required_somewhere(self):
        required_counts = dict((t, 0) for t in INTERACTION_TYPES)
        unset_counts = dict((t, 0) for t in INTERACTION_TYPES)
        for config_index in range(len(MODE_CONFIGS)):
            mode = MODE_CONFIGS[config_index][0]
            for difficulty in DIFFICULTY_SWEEP:
                for molecules in MOLECULES_SWEEP:
                    for payload in corpus()[(config_index, difficulty,
                                             molecules)]:
                        for level, molecule in iter_molecules(payload):
                            for item in molecule['required']['items']:
                                required_counts[item['type']] += 1
                                if mode == 'unset':
                                    unset_counts[item['type']] += 1
        # Full corpus: every one of the 7 types is required at least
        # once (hydrophobic ONLY via the block_exclusive explicit check,
        # OQ-5).
        for itype in INTERACTION_TYPES:
            self.assertGreater(required_counts[itype], 0,
                               'type %r is required nowhere across the '
                               'corpus -- a sampling bug that starves a '
                               'type would be invisible' % (itype,))
        # Unset sampling alone must not starve ANY of its 6 legal pool
        # members (hydrophobic's pool membership is forbidden outright).
        for itype in INTERACTION_TYPES:
            if itype == 'hydrophobic':
                self.assertEqual(unset_counts[itype], 0,
                                 'OQ-5: hydrophobic can never be '
                                 'required via unset')
            else:
                self.assertGreater(unset_counts[itype], 0,
                                   'unset sampling starved type %r'
                                   % (itype,))

    def test_E19_required_slots_not_concentrated_on_fixed_positions(self):
        total_units = 0
        r0c0_required = 0
        for payload in self._unset_sweep():
            for level, molecule in iter_molecules(payload):
                total_units += 1
                for slot in molecule['grid']['slots']:
                    if slot['slot_id'] == 'r0c0':
                        if slot['role'] == 'required':
                            r0c0_required += 1
                        break
        fraction = r0c0_required / float(total_units)
        self.assertLess(fraction, 0.5,
                        'slot r0c0 is required in %.3f of %d units -- '
                        'required slots must not concentrate on fixed '
                        'positions' % (fraction, total_units))
        self.assertGreater(r0c0_required, 0,
                           'required slots never reach r0c0 at all -- '
                           'position sampling looks broken')


if __name__ == '__main__':
    unittest.main()
