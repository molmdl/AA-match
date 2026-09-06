"""aamatch.generator -- the pure seeded level generator (plan 02-08).

Layer: PURE. The game brain's producer side: consumes a validated setup
state + manifest candidate rows + per-molecule ligand bounds (fed IN by
the cmd tier -- the proven prior-art data-in/decisions-out pattern) and
emits a complete level-spec payload that FULLY DETERMINES the level:
slot assignments AND grid positions are serialized, nothing is recomputed
from the seed at replay time (generation research §7.2).

Scope (generation research §0/§3): difficulty expression (GEN-05),
deterministic grid geometry (GEN-03), required-set derivation with the
approved OQ-1 mode semantics (GEN-04 / gate §4.3), solvability-by-
construction slot allocation (GEN-04), payload assembly with version
stamps + deterministic RNG (GEN-01). The >= 100-seed invariant sweep is
plan 02-12; the cmd-tier wiring (manifest/lights-out extraction feeding
``ligand_data``) is plans 02-10/02-14.

RECORDED POLICIES carried by this module (each binds consumers
simultaneously -- the docstring is the policy carrier, house style):

- OQ-1 MODE SEMANTICS (docs/DETECTION_THRESHOLDS.md §4.3, approved
  2026-09-06): ``exclusive`` = "any interaction formed", scoped by
  ``allowed_interactions``; exclusive + empty allowed list ->
  GenerationError; ``unset`` + empty allowed list -> draw from the
  non-hydrophobic types (unset means "the game picks"); block_exclusive
  + a checked type the ligand cannot support -> refuse, NAMING the
  type(s) (never silently degrade). Binds derive_required (02-08) and
  score 'any' semantics (02-10).
- OQ-5 HYDROPHOBIC SAMPLING EXCLUSION (gate §4.5): hydrophobic is
  EXCLUDED from unset-mode required-type sampling (the 4.0 A C-C
  criterion is permissive; in random-required-set levels hydrophobic
  makes success near-trivial). Detection semantics unchanged -- a
  sampling policy, not a threshold change. Hydrophobic can appear in the
  required set ONLY via block_exclusive explicit check.
- D1 SIDE-CHAIN-ONLY capability (gate §4.1): consumed via
  capability.aa_capable -- the generator never re-derives typing
  (DETECT-04 single typing home, gate §4.2).
- D2/D3/D4: capped AAs, polarity-aware salt bridges, either-direction
  cation-pi -- all inside capability.aa_capable; the generator only
  feeds the ligand profile.
- TWO VERSION GATES (gate §4.7, never conflated): the payload stamps
  ``detector_version`` == level_spec.DETECTOR_VERSION (exact-match gate:
  stale AND newer specs are refused -- changed detection semantics make
  specs unsolvable) and ``format_version`` == level_spec.LEVEL_SPEC_VERSION
  (refuse-newer / accept-older, additive-only evolution).
- RNG DISCIPLINE (generation research §7.1): one master
  ``random.Random(seed)``; per-game-unit sub-seeds drawn from the master
  stream in FIXED ORDER (never ``hash()`` -- PYTHONHASHSEED); all
  randomness consumes the stream ONLY via randint/choice/sample/shuffle
  over SORTED or fixed-order lists -- never sets/dicts (set iteration
  order is not stable across processes for strings). Same interpreter +
  same seed -> byte-identical payload; cross-Python-version drift is
  moot because the payload never re-derives from the seed (§7.2).
- NO I/O, NO pymol/Qt/numpy/itertools (itertools is deliberately NOT
  whitelisted for pure modules, gate §4.6): explicit loops and
  comprehensions only. File I/O stays cmd-tier; the generator receives
  already-resolved Python data.

Grid geometry (generation research §5): a flat N x N plane facing +Z,
centered on the ligand centroid's (x, y), offset ``R + GAP_MARGIN`` from
the centroid along +Z. Constants are ENGINEERING choices, not chemistry
claims -- tune freely, assert via invariants (tests pin spacing/gap
honesty). All positions are in the ligand-file frame; the per-molecule
world offset (``placement.offset``, additive payload key -- passthrough
parse accepts it) shifts molecule group m by
``m * (grid_width + INTER_GRID_MARGIN)`` along +X so multi-molecule
levels are globally disjoint whether the materializer shows one molecule
at a time or all at once.

Difficulty (generation research §6): D = difficulty_levels in [1, 10]
(cap 10 human-amended at 01-09, frozen). Levels L = 0..D-1
(level_index == tier). All three axes escalate monotonically via INTEGER
HALF-UP interpolation -- never banker's rounding, which would make the
middle tier asymmetric:

    frac = (L * GRID_SPAN + (D - 1) // 2) // (D - 1)   if D > 1 else 0
    grid_n           = 3 + frac          in 3..9   (9x9 = 81 AAs = the
                                                    researched perf
                                                    ceiling, PITFALLS 15)
    n_required_types = 1 + frac          in 1..7   (pre-clamp intent; the
                                                    per-molecule draw
                                                    clamps down to the
                                                    ligand-supported set)
    molecule_size_class = small/medium/large by level thirds
                         ((L*3)//D -- matches the §6 reference rows for
                         D=3 and D=10; D=1 -> single easiest level).

Purity: module-level imports are stdlib (math, random) + pure aamatch
modules (capability, level_spec, setup_state) ONLY. NO file I/O here.
"""

import math
import random

from .capability import AA_RESIDUES, AA_TOKENS, aa_capable, ligand_support
from .level_spec import DETECTOR_VERSION, LEVEL_SPEC_VERSION
from .setup_state import (
    DIFFICULTY_CAP,
    INTERACTION_TYPES,
    MOLECULES_CAP,
)

# ---------------------------------------------------------------------------
# Engineering constants (generation research §5/§6 -- tune freely, the
# invariant tests pin their honesty, not chemistry).
# ---------------------------------------------------------------------------

# Adjacent grid AAs cannot interpenetrate: exceeds the largest capped-AA
# extent (Trp + caps ~ 10-12 A total length) with margin.
GRID_SPACING = 8.0
# "Beyond a gap": the nearest grid plane sits R + GAP_MARGIN from the
# ligand centroid -> no grid AA can intersect the ligand at spawn.
GAP_MARGIN = 5.0
# Multi-molecule group separation margin along +X (§5.1).
INTER_GRID_MARGIN = 6.0
# Difficulty interpolation span: grid_n 3..9, n_required_types 1..7.
GRID_SPAN = 6
# Molecule size buckets by heavy-atom count (small < S1 <= medium
# < S2 <= large) -- engineering buckets, tuned when the Phase-8 manifest
# exists; recorded as constants, not chemistry.
SIZE_S1 = 25
SIZE_S2 = 60

SIZE_CLASSES = ('small', 'medium', 'large')

# Minimum grid side (3x3 = 9 AAs = the smallest meaningful choice).
GRID_N_MIN = 3


class GenerationError(ValueError):
    """A failed GENERATION (infeasible configuration / bad input).

    Subclass of ValueError; deliberately NOT persistence.FormatError --
    a failed generation is not a malformed FILE (generation research
    §3.2). The caller (Phase 4 GUI / headless smoke) renders the message
    as a user-visible error; every refusal NAMES the cause.
    """


# ---------------------------------------------------------------------------
# Difficulty expression (GEN-05, generation research §6).
# ---------------------------------------------------------------------------

def difficulty_params(difficulty_levels, level_index):
    """Difficulty axes for level `level_index` of a `difficulty_levels`-
    level game.

    Returns the reserved per-level difficulty dict verbatim:
    ``{'tier': L, 'grid_n': 3..9, 'n_required_types': 1..7,
    'molecule_size_class': 'small'|'medium'|'large'}``.

    Integer HALF-UP interpolation (module docstring): for D > 1,
    ``frac = (L * GRID_SPAN + (D - 1) // 2) // (D - 1)``; for D == 1 the
    single level is the easiest (frac 0 -> grid 3, 1 type, small).
    D == 1 must not divide by zero -- guarded, never assumed.

    Monotonicity (tested over ALL legal D in 1..10): grid_n,
    n_required_types and the size-class rank are non-decreasing in L.
    """
    D = difficulty_levels
    L = level_index
    if D > 1:
        denom = D - 1
        frac = (L * GRID_SPAN + denom // 2) // denom
    else:
        frac = 0
    bucket_index = (L * 3) // D if D > 0 else 0
    if bucket_index > 2:                       # defensive; unreachable
        bucket_index = 2
    return {
        'tier': L,
        'grid_n': GRID_N_MIN + frac,
        'n_required_types': 1 + frac,
        'molecule_size_class': SIZE_CLASSES[bucket_index],
    }


# ---------------------------------------------------------------------------
# Grid geometry (GEN-03, generation research §5.1/§5.2).
# ---------------------------------------------------------------------------

def slot_position(row, col, n, centroid, radius):
    """Deterministic 3D position of grid slot (row, col) for an n x n
    grid around a ligand bounding sphere.

    Formula (generation research §5.2, ligand-file frame):

        half = (n - 1) / 2.0
        slot(r, c) = (cx + (c - half) * GRID_SPACING,
                      cy + (r - half) * GRID_SPACING,
                      cz + radius + GAP_MARGIN)

    Centered on the ligand centroid's (x, y); plane offset along +Z by
    ``R + GAP_MARGIN``. Invariants (tested): pairwise slot distances
    >= GRID_SPACING; every slot-to-centroid distance >= R + GAP_MARGIN.
    """
    half = (n - 1) / 2.0
    cx, cy, cz = centroid[0], centroid[1], centroid[2]
    return (
        cx + (col - half) * GRID_SPACING,
        cy + (row - half) * GRID_SPACING,
        cz + radius + GAP_MARGIN,
    )


def placement_offset(molecule_index, grid_n):
    """Per-molecule group offset along +X (generation research §5.1).

    Molecule group m (ligand + grid TOGETHER) is shifted by
    ``m * (grid_width + INTER_GRID_MARGIN)`` where grid_width is the
    conservative full extent ``grid_n * GRID_SPACING``. Slots of
    different molecules in one level are then at least one spacing apart
    (tested) -- globally disjoint whether the materializer shows one
    molecule at a time or all at once.
    """
    width = grid_n * GRID_SPACING
    return (molecule_index * (width + INTER_GRID_MARGIN), 0.0, 0.0)


# ---------------------------------------------------------------------------
# Input guards (fail EARLY -- persistence writes JSON with
# allow_nan=False, so a NaN/inf reaching save time is refused far from
# the bug; generation research §5.2/§10).
# ---------------------------------------------------------------------------

def _validate_ligand_data(ligand_data):
    """Validate one molecule's ligand geometry summary (fed IN by the
    cmd tier: ``{'centroid': (x, y, z), 'radius': R}`` -- the bounding
    sphere, ligand-file frame).

    Raises GenerationError naming the cause when the centroid is not
    exactly 3 finite numbers or the radius is not a finite number > 0.
    Grid float math must never produce NaN (they would be refused only
    at save time, allow_nan=False -- too far from the bug).
    """
    if not isinstance(ligand_data, dict):
        raise GenerationError(
            "ligand_data must be a dict {'centroid': (x, y, z), "
            "'radius': R} (found %s)" % type(ligand_data).__name__)
    centroid = ligand_data.get('centroid')
    if not isinstance(centroid, (list, tuple)) or len(centroid) != 3:
        raise GenerationError(
            "ligand_data 'centroid' must be 3 numbers (x, y, z), "
            "found %r" % (centroid,))
    finite = []
    for component in centroid:
        try:
            value = float(component)
        except (TypeError, ValueError):
            raise GenerationError(
                "ligand_data 'centroid' must be 3 numbers, found %r"
                % (centroid,))
        if not math.isfinite(value):
            raise GenerationError(
                "ligand_data 'centroid' must be finite (NaN/inf would be "
                "refused at save time); found %r" % (centroid,))
        finite.append(value)
    radius = ligand_data.get('radius')
    try:
        radius_f = float(radius)
    except (TypeError, ValueError):
        raise GenerationError(
            "ligand_data 'radius' must be a number > 0, found %r"
            % (radius,))
    if not math.isfinite(radius_f):
        raise GenerationError(
            "ligand_data 'radius' must be finite (NaN/inf would be "
            "refused at save time); found %r" % (radius,))
    if radius_f <= 0.0:
        raise GenerationError(
            "ligand_data 'radius' must be > 0 (a degenerate bounding "
            "sphere cannot size a grid); found %r" % (radius,))
    # Preserve the REST of the geometry dict (notably 'profile' -- the
    # chemistry half of the ligand_data contract) with the validated
    # centroid/radius normalized in place.
    validated = dict(ligand_data)
    validated['centroid'] = tuple(finite)
    validated['radius'] = radius_f
    return validated


# ---------------------------------------------------------------------------
# RNG skeleton (generation research §7.1).
# ---------------------------------------------------------------------------

_SUB_SEED_MAX = 2 ** 31 - 1


def _sub_seeds(master_rng, n_units):
    """Draw `n_units` per-game-unit sub-seeds from the master stream in
    FIXED order (generation research §7.1).

    Each unit (level x molecule) later runs its own
    ``random.Random(sub_seed)`` consumed in a fixed call order
    (derive_required -> slot sample -> distractor fill). Sub-seeding
    isolates units so adding a molecule cannot shift another molecule's
    stream (protects golden tests from unrelated churn -- PITFALL 11.2).
    Never hash()-derived: PYTHONHASHSEED would break reproducibility.
    """
    return [master_rng.randint(0, _SUB_SEED_MAX)
            for _ in range(n_units)]


# ---------------------------------------------------------------------------
# Required-set derivation (GEN-04, OQ-1 semantics) + slot allocation.
# ---------------------------------------------------------------------------

# The 20 standard AAs in canonical sorted order -- the ONE list every
# RNG touch uses (distractor draws, capable pools). Derived from the
# capability table (never re-derived typing), cross-checked against the
# materialization vocabulary AA_TOKENS so every emitted 'aa' can be
# loaded by the materializer.
ALL_AA = sorted(AA_RESIDUES)

_MATERIALIZABLE_RESNS = frozenset(
    entry['resn'] for entry in AA_TOKENS.values())


def _checked_allowed(setup):
    """setup['allowed_interactions'] as a canonical list, defensively
    validated: members outside INTERACTION_TYPES are refused loudly
    (validate_state already filters silently -- a RAW dict past the
    validated setup must not degrade silently here)."""
    allowed = setup.get('allowed_interactions')
    if not isinstance(allowed, (list, tuple)):
        raise GenerationError(
            "setup 'allowed_interactions' must be a list of interaction "
            "types (found %s)" % type(allowed).__name__)
    unknown = [t for t in allowed if t not in INTERACTION_TYPES]
    if unknown:
        raise GenerationError(
            "setup 'allowed_interactions' carries unknown interaction "
            "type(s): %s" % ', '.join(str(t) for t in unknown))
    return list(allowed)


def derive_required(setup, ligand_profile, rng, n_required_types):
    """Resolve the required interaction set for one molecule.

    Approved OQ-1 mode semantics (docs/DETECTION_THRESHOLDS.md §4.3,
    2026-09-06 -- binding) + OQ-5 hydrophobic sampling exclusion (§4.5):

    - ``exclusive`` = "any interaction formed", SCOPED BY
      ``allowed_interactions``: returns ``{'mode': 'any', 'items': []}``.
      Empty allowed list -> GenerationError naming the setup field.
      Ligand supports zero of the allowed types -> GenerationError.
    - ``block_exclusive`` = required set is EXACTLY the checked
      interactions (human-checked set): items are the allowed list in
      canonical INTERACTION_TYPES order, count 1 each. A checked type the
      ligand cannot support -> GenerationError NAMING the type(s) (never
      silently degrade). Empty allowed -> GenerationError ("no
      interactions checked"). Hydrophobic IS reachable here (explicit
      check -- the only route per OQ-5).
    - ``unset`` = random required set: the draw pool is the
      ligand-SUPPORTED subset of the vocabulary (allowed list, or ALL
      types when allowed is empty -- unset means "the game picks"),
      MINUS hydrophobic (OQ-5: hydrophobic can appear ONLY via
      block_exclusive explicit check). k = min(n_required_types,
      len(pool)); ``rng.sample`` over the canonical-ordered pool; items
      re-emitted in canonical order. Pool empty -> GenerationError
      naming the cause (only-hydrophobic names the OQ-5 policy).

    Edge-case rulings (generation research §4.3, verbatim):

    | Edge case | Ruling |
    |-----------|--------|
    | block_exclusive checked set includes an unsupported type | Refuse, naming the type(s); silent degradation would corrupt the game's contract |
    | unset random draw includes an unsupported type | Cannot happen -- the draw is from the supported subset |
    | exclusive ("any") + ligand supports zero of the allowed types | Refuse ("molecule supports none of the allowed interactions") |
    | Ligand with a metal: metal supportable only then; without metal never sampled | ligand_support() predicate -- DETECT-02 "conditional on metal present" |
    | Ligand without halogens: halogen never supportable (donors are ligand-side only) | Same predicate |
    | Required AA pool smaller than count | Guarded in allocate_slots; impossible in practice (>= 4 capable AAs per type) |
    | n^2 < needed + 1 | Refuse ("grid too small") in allocate_slots |
    | Empty allowed_interactions in block/unset modes | block: refuse ("no interactions checked"); unset: draw from all types (OQ-1), hydrophobic still excluded (OQ-5) |

    ``count`` semantics: v1 ALWAYS count = 1 (generation research §4.1);
    the field exists for future multi-instance requirements. ``rng`` is
    consumed ONLY via ``rng.sample`` over the canonical-ordered pool (a
    fixed-order list -- never a set/dict).
    """
    allowed = _checked_allowed(setup)
    mode = setup.get('interaction_mode')

    if mode == 'exclusive':
        if not allowed:
            raise GenerationError(
                "exclusive mode requires the setup field "
                "'allowed_interactions' to be non-empty -- check the "
                "interactions the game should teach in Setup")
        supported = [t for t in allowed
                     if ligand_support(t, ligand_profile)]
        if not supported:
            raise GenerationError(
                "molecule supports none of the allowed interactions (%s)"
                % ', '.join(allowed))
        return {'mode': 'any', 'items': []}

    if mode == 'block_exclusive':
        if not allowed:
            raise GenerationError(
                "block_exclusive mode requires 'allowed_interactions': "
                "no interactions checked")
        missing = [t for t in allowed
                   if not ligand_support(t, ligand_profile)]
        if missing:
            raise GenerationError(
                "molecule cannot support required interaction(s): %s"
                % ', '.join(missing))
        return {'mode': 'list',
                'items': [{'type': t, 'count': 1} for t in allowed]}

    if mode == 'unset':
        vocabulary = allowed if allowed \
            else [t for t in INTERACTION_TYPES if t != 'hydrophobic']
        # OQ-5: hydrophobic is EXCLUDED from unset sampling, always.
        pool = [t for t in vocabulary
                if t != 'hydrophobic' and ligand_support(t, ligand_profile)]
        if not pool:
            supported = [t for t in vocabulary
                         if ligand_support(t, ligand_profile)]
            if supported:
                raise GenerationError(
                    "molecule supports only %s; hydrophobic is excluded "
                    "from unset-mode sampling (DETECTION_THRESHOLDS OQ-5) "
                    "-- check explicit interactions in Setup"
                    % ', '.join(supported))
            raise GenerationError(
                "molecule supports none of the sampleable interactions "
                "(vocabulary: %s)"
                % (', '.join(vocabulary) if vocabulary else 'empty'))
        k = min(n_required_types, len(pool))
        picked = rng.sample(pool, k)          # pool: canonical-order list
        return {'mode': 'list',
                'items': [{'type': t, 'count': 1} for t in pool
                          if t in picked]}

    raise GenerationError(
        "unknown interaction_mode %r (expected one of exclusive, "
        "block_exclusive, unset)" % (mode,))


def allocate_slots(required_items, n, ligand_profile, rng):
    """One global allocation pass for one molecule (generation research
    §4.2): every required item gets a DEDICATED slot with
    ``role='required'`` and truthful ``can_form=[type]``; every remaining
    slot is a ``role='distractor'`` drawn from ALL 20 AAs.

    Solvability by construction: a single AA instance is never assigned
    two required types (simpler accounting; the required-slot guarantee
    is atomic). Distractors may coincide with capable AAs -- fine: the
    dedicated required slots guarantee solvability IN ADDITION to
    whatever distractors happen to support, and incapable distractors
    are the challenge. ``can_form`` semantics: "the interaction types
    this slot was CHOSEN to guarantee" -- a generation-time provenance
    record, NOT the Hint's data source (Hint recomputes capability live
    via the shared capability module, PLAY-05).

    RNG contract: consumed ONLY via sample (required-slot positions over
    the fixed-order (row, col) list), shuffle (required-item pairing),
    and choice (capable pools / the sorted 20-AA list) -- never over
    sets or dicts.

    Refusals (each names the cause): grid too small (n*n < needed + 1 --
    keeps at least one distractor slot; cannot trigger in v1 with n >= 3
    and <= 7 single-count types but guards future count>1 modes); no
    capable AA for a required type; required counts other than 1 (v1);
    capability/materialization vocabulary drift.
    """
    total = n * n
    needed = len(required_items)
    if needed + 1 > total:
        raise GenerationError(
            "grid %dx%d too small for %d required interactions "
            "(at least one distractor slot must remain)" % (n, n, needed))

    vocab_drift = [aa for aa in ALL_AA if aa not in _MATERIALIZABLE_RESNS]
    if vocab_drift:
        raise GenerationError(
            "capability/materialization vocabulary drift: %s have no "
            "AA_TOKENS entry (the materializer could not load them)"
            % ', '.join(vocab_drift))

    pools = {}
    for item in required_items:
        itype = item['type']
        count = item.get('count', 1)
        if count != 1:
            raise GenerationError(
                "required item counts other than 1 are not supported in "
                "v1 (found count=%r for %r)" % (count, itype))
        if itype not in pools:
            pools[itype] = [aa for aa in ALL_AA
                            if aa_capable(aa, itype, ligand_profile)]
        if len(pools[itype]) < 1:
            raise GenerationError(
                "no amino acid can form %r with this molecule" % (itype,))

    # WHERE the required AAs sit: one sample over the fixed-order slot
    # list (deterministic -- never iterated from a set/dict).
    slot_coords = [(row, col) for row in range(n) for col in range(n)]
    required_coords = rng.sample(slot_coords, needed)

    items = list(required_items)
    rng.shuffle(items)          # pairing shuffle over a list copy
    assignments = {}
    for coord, item in zip(sorted(required_coords), items):
        aa = rng.choice(pools[item['type']])
        assignments[coord] = {
            'aa': aa, 'role': 'required', 'can_form': [item['type']]}

    slots = []
    for coord in slot_coords:             # fixed row-major order
        row, col = coord
        assignment = assignments.get(coord)
        if assignment is None:            # distractor fill, fixed order
            assignment = {
                'aa': rng.choice(ALL_AA), 'role': 'distractor',
                'can_form': []}
        slots.append({
            'slot_id': 'r%dc%d' % (row, col),
            'row': row,
            'col': col,
            'aa': assignment['aa'],
            'role': assignment['role'],
            'can_form': list(assignment['can_form']),
        })
    return slots


# ---------------------------------------------------------------------------
# Payload assembly (GEN-01, generation research §7.2/§9).
# ---------------------------------------------------------------------------

def _is_int(value):
    """True for real ints only -- bool is an int subclass, never a
    seed/count (mirrors level_spec._is_int)."""
    return isinstance(value, int) and not isinstance(value, bool)


def _validated_candidates(candidates):
    """Validate candidate rows and return them re-sorted defensively by
    (set_id, entry_id).

    Candidates come pre-sorted per manifest enumerate_entries order;
    generate() re-sorts anyway and documents it (the generator must not
    depend on caller-side ordering discipline). Rows are manifest-shaped
    (schema frozen at 02-03): the entry's fields plus 'set_id'. Only the
    fields the payload consumes are checked here -- the manifest parse
    gate owns the full schema.
    """
    if not isinstance(candidates, (list, tuple)):
        raise GenerationError(
            "candidates must be a list of manifest entry rows (found %s)"
            % type(candidates).__name__)
    rows = []
    for row in candidates:
        if not isinstance(row, dict):
            raise GenerationError(
                "candidate rows must be dicts (found %s)"
                % type(row).__name__)
        set_id = row.get('set_id')
        entry_id = row.get('entry_id')
        if not isinstance(set_id, str) or not set_id \
                or not isinstance(entry_id, str) or not entry_id:
            raise GenerationError(
                "candidate rows must carry non-empty 'set_id' and "
                "'entry_id' strings (found %r)" % (row,))
        for key in ('file', 'sha256'):
            value = row.get(key)
            if not isinstance(value, str) or not value:
                raise GenerationError(
                    "candidate %r: %r must be a non-empty string"
                    % (entry_id, key))
        rows.append(row)
    return sorted(rows, key=lambda row: (row['set_id'], row['entry_id']))


def _candidate_class(row):
    """The molecule size bucket of one candidate: the manifest's recorded
    'size_class' when present, else derived from 'heavy_atom_count'
    (small < SIZE_S1 <= medium < SIZE_S2 <= large). Unknown shapes fail
    closed naming the candidate."""
    size_class = row.get('size_class')
    if size_class in SIZE_CLASSES:
        return size_class
    heavy = row.get('heavy_atom_count')
    if _is_int(heavy) and heavy > 0:
        if heavy < SIZE_S1:
            return 'small'
        if heavy < SIZE_S2:
            return 'medium'
        return 'large'
    raise GenerationError(
        "candidate %r needs a valid 'size_class' (%s) or a positive int "
        "'heavy_atom_count' (found size_class=%r, heavy_atom_count=%r)"
        % (row.get('entry_id'), '/'.join(SIZE_CLASSES), size_class, heavy))


def _select_pool(candidates, target_class):
    """Candidates in the target size-class bucket (sorted order
    preserved).

    SUPPLY-SIDE FALLBACK (recorded deviation, plan 02-08): when no
    candidate carries the target bucket, the NEAREST non-empty bucket by
    rank distance wins (ties -> the easier/smaller rank). The emitted
    difficulty dict keeps RECORDING the target size class -- the
    fallback degrades the supply, never the recorded difficulty axis.
    Rationale: v1's development manifest is small-only; a hard refusal
    would block every D >= 2 game (and with it the phase's own E2E)
    before curated Phase-8 data exists. Without ANY candidates,
    GenerationError.
    """
    pools = {}
    for row in candidates:                # sorted order preserved
        pools.setdefault(_candidate_class(row), []).append(row)
    pool = pools.get(target_class)
    if pool:
        return pool
    target_rank = SIZE_CLASSES.index(target_class)
    ranked = sorted(pools, key=lambda name: SIZE_CLASSES.index(name))
    nearest = min(ranked,
                  key=lambda name: (abs(SIZE_CLASSES.index(name)
                                        - target_rank),
                                    SIZE_CLASSES.index(name)))
    return pools[nearest]


def _geometry_for(identity, ligand_data):
    """Look up one molecule's geometry summary in ligand_data.

    Contract (generation research §3.2, made explicit): EITHER a dict
    keyed by ``(set_id, entry_id)`` tuples mapping to per-molecule
    ``{'centroid': (x, y, z), 'radius': R[, 'profile': {...}]}`` -- the
    02-14 new_game shape -- OR ONE shared ``{'centroid', 'radius'...}``
    dict applied to every molecule (single-ligand smokes/tests, 02-13
    pattern). Missing identity -> GenerationError naming it.
    """
    if not isinstance(ligand_data, dict):
        raise GenerationError(
            "ligand_data must be a dict keyed by (set_id, entry_id) "
            "with {'centroid', 'radius'} geometry, or ONE shared "
            "{'centroid', 'radius'} dict (found %s)"
            % type(ligand_data).__name__)
    if 'centroid' in ligand_data and 'radius' in ligand_data:
        return ligand_data
    geometry = ligand_data.get(identity)
    if geometry is None:
        raise GenerationError(
            "ligand_data has no entry for molecule %r -- key it by "
            "(set_id, entry_id) or pass one shared {'centroid', "
            "'radius'} dict" % (identity,))
    return geometry


def _profile_of(geometry, identity):
    """The molecule's chemistry profile (capability.ligand_profile
    shape), consumed by derive_required/allocate_slots.

    DEVIATION NOTE (contract gap closed here, binding on 02-13/02-14):
    the ligand_data entries must carry 'profile' -- the cmd tier computes
    it from the loaded ligand (extract_game_atoms side=='lig' records +
    ligand_bonds -> capability.ligand_profile). A MISSING profile
    degrades FAIL-CLOSED to an empty profile: every support predicate is
    False, so unset/block_exclusive modes refuse with the standard
    "supports none / cannot support" messages rather than silently
    promising unsolvable interactions.
    """
    profile_data = geometry.get('profile')
    if profile_data is None:
        return {}
    if not isinstance(profile_data, dict):
        raise GenerationError(
            "ligand_data profile for %r must be a "
            "capability.ligand_profile-shaped dict (found %s)"
            % (identity, type(profile_data).__name__))
    return profile_data


def _protonation_of(candidate, rng, identity):
    """Select and record the ligand protonation state (GEN-02 data side,
    generation research §7.3): a manifest-recorded string is used
    verbatim; multiple recorded states are picked via
    ``rng.choice(sorted(states))`` on the molecule's own RNG stream. The
    picked value lands in the spec, so replay never re-picks."""
    raw = candidate.get('protonation')
    if isinstance(raw, (list, tuple)):
        if not raw:
            raise GenerationError(
                "candidate %r offers an empty protonation list"
                % (identity,))
        return rng.choice(sorted(str(state) for state in raw))
    if isinstance(raw, str) and raw:
        return raw
    raise GenerationError(
        "candidate %r has no recorded 'protonation' (expected a string "
        "or a non-empty list of states; found %r)" % (identity, raw))


def generate(seed, setup, candidates, ligand_data, difficulty_levels):
    """Pure seeded level generation: returns the level-spec payload dict
    (the container's 'data').

    Inputs (all data-in, no I/O -- the cmd tier resolves files first):
    ``seed``: real int master seed (bool refused explicitly -- a clearer
    message than the parse gate). ``setup``: validated setup_state dict
    (mode, allowed_interactions, molecules_per_level, source_mode).
    ``candidates``: manifest entry rows (+ 'set_id'), PRE-SORTED per
    manifest enumerate_entries order -- re-sorted defensively by
    (set_id, entry_id) regardless. ``ligand_data``: per-molecule
    geometry + chemistry profile, keyed by (set_id, entry_id) tuples, or
    ONE shared geometry dict (see _geometry_for). ``difficulty_levels``:
    the clamped D (setup's difficulty_levels).

    Payload shape (reserved schema + ONE additive extension, generation
    research §7.2/§9):

        {'detector_version': DETECTOR_VERSION,    # exact-match gate
         'format_version': LEVEL_SPEC_VERSION,    # refuse-newer gate
         'seed': <int>,
         'levels': [{'level_index': L, 'tier' == L via 'difficulty',
                     'difficulty': {tier, grid_n, n_required_types,
                                    molecule_size_class},
                     'molecules': [{'molecule_id': 'mol-NNN',  # per level
                                    'ligand': {source, set_id, entry_id,
                                               file, sha256, protonation,
                                               provenance},
                                    'required': {mode, items},
                                    'placement': {'offset': [x, y, z]},
                                                              # additive
                                    'grid': {'n', 'slots': [...]}}]}]}

    ``placement.offset`` is the recorded additive extension of the
    reserved shape (passthrough parse accepts it, 01-06): molecule
    group m's shift along +X (materializer applies it to ligand + grid
    TOGETHER). ``molecule_id`` numbers molecules WITHIN each level
    (mol-001..); level_index + molecule_id identify globally, matching
    the per-molecule scoping of slot_id. 'file' stays package-relative
    (PITFALL 2; to_windows_path at load time only). ``provenance`` is
    the candidate's recorded provenance or '' until Phase 8 curates it.

    RNG layout (generation research §7.1): one master
    random.Random(seed) draws D * MOLECULES_CAP unit sub-seeds in fixed
    order -- one per (level, molecule SLOT) up to the setup cap, so the
    master stream consumption is setup-independent and adding a molecule
    consumes previously-drawn-but-unused seeds WITHOUT shifting an
    existing molecule's stream (PITFALL 11.2; byte-isolation tested).
    Each unit's Random(sub_seed) is consumed in a FIXED call order:
    molecule pick (rng.sample over the bucket's sorted candidate list,
    minus this level's already-picked molecules) -> protonation choice
    -> derive_required sampling -> allocate_slots. Molecules within a
    level are DISTINCT picks (dedup by (set_id, entry_id)).

    Selection: candidates are filtered to the level's size-class bucket
    (fallback: nearest non-empty bucket, recorded deviation -- the
    difficulty dict keeps the TARGET class); inside the pool the unit
    RNG samples from the deterministically sorted candidate list.

    The payload fully determines the level (nothing re-derives from the
    seed at replay): same seed + same inputs -> byte-identical payload
    (json sort_keys); all RNG touches go through sorted/fixed-order
    lists. Raises GenerationError naming the cause for every infeasible
    configuration (OQ-1 semantics) and every degenerate input.
    """
    if isinstance(seed, bool) or not isinstance(seed, int):
        raise GenerationError(
            "seed must be a real int -- bool is not a seed (a clearer "
            "message than the parse gate); found %r" % (seed,))
    if not _is_int(difficulty_levels) \
            or not 1 <= difficulty_levels <= DIFFICULTY_CAP:
        raise GenerationError(
            "difficulty_levels must be an int in 1..%d (the frozen setup "
            "clamp); found %r" % (DIFFICULTY_CAP, difficulty_levels))
    if not isinstance(setup, dict):
        raise GenerationError(
            "setup must be a validated setup_state dict (found %s)"
            % type(setup).__name__)
    molecules_per_level = setup.get('molecules_per_level')
    if not _is_int(molecules_per_level) or molecules_per_level < 1:
        raise GenerationError(
            "setup 'molecules_per_level' must be an int >= 1 (found %r)"
            % (molecules_per_level,))

    rows = _validated_candidates(candidates)
    if not rows:
        raise GenerationError(
            "no candidates supplied -- generate needs at least one "
            "manifest entry row")

    D = difficulty_levels
    master = random.Random(seed)
    unit_seeds = _sub_seeds(master, D * MOLECULES_CAP)

    levels = []
    for level_index in range(D):
        params = difficulty_params(D, level_index)
        n = params['grid_n']
        pool = _select_pool(rows, params['molecule_size_class'])
        taken = set()
        molecules = []
        for molecule_index in range(molecules_per_level):
            unit_rng = random.Random(
                unit_seeds[level_index * MOLECULES_CAP + molecule_index])
            available = [row for row in pool
                         if (row['set_id'], row['entry_id']) not in taken]
            if not available:
                distinct = len(set((row['set_id'], row['entry_id'])
                                   for row in pool))
                raise GenerationError(
                    "size class %r (fallback target %r) has %d distinct "
                    "candidate(s); level %d needs %d distinct molecules "
                    "-- add candidates or lower molecules_per_level"
                    % (params['molecule_size_class'],
                       params['molecule_size_class'], distinct,
                       level_index, molecules_per_level))
            picked = unit_rng.sample(available, 1)[0]
            identity = (picked['set_id'], picked['entry_id'])
            taken.add(identity)

            geometry = _validate_ligand_data(
                _geometry_for(identity, ligand_data))
            profile_data = _profile_of(geometry, identity)
            protonation = _protonation_of(picked, unit_rng, identity)
            required = derive_required(setup, profile_data, unit_rng,
                                       params['n_required_types'])
            slots = allocate_slots(required['items'], n, profile_data,
                                   unit_rng)

            offset = placement_offset(molecule_index, n)
            slot_payloads = []
            for slot in slots:
                position = slot_position(slot['row'], slot['col'], n,
                                         geometry['centroid'],
                                         geometry['radius'])
                for value in position:
                    if not math.isfinite(value):
                        raise GenerationError(
                            "grid position for slot %s of %r is "
                            "non-finite (degenerate ligand geometry?)"
                            % (slot['slot_id'], identity))
                slot_payloads.append({
                    'slot_id': slot['slot_id'],
                    'row': slot['row'],
                    'col': slot['col'],
                    'aa': slot['aa'],
                    'role': slot['role'],
                    'can_form': list(slot['can_form']),
                    'grid_pose': {'position': [float(position[0]),
                                               float(position[1]),
                                               float(position[2])]},
                })
            molecules.append({
                'molecule_id': 'mol-%03d' % (molecule_index + 1),
                'ligand': {
                    'source': setup.get('source_mode', 'demo'),
                    'set_id': picked['set_id'],
                    'entry_id': picked['entry_id'],
                    'file': picked['file'],
                    'sha256': picked['sha256'],
                    'protonation': protonation,
                    'provenance': picked.get('provenance', ''),
                },
                'required': required,
                'placement': {'offset': [float(offset[0]),
                                         float(offset[1]),
                                         float(offset[2])]},
                'grid': {'n': n, 'slots': slot_payloads},
            })
        levels.append({
            'level_index': level_index,
            'difficulty': params,
            'molecules': molecules,
        })

    return {
        'detector_version': DETECTOR_VERSION,
        'format_version': LEVEL_SPEC_VERSION,
        'seed': seed,
        'levels': levels,
    }
