"""aamatch.level_spec -- reserved level-spec schema + two version gates.

The level spec is the SHAREABLE SOURCE OF TRUTH for a generated game
(seed + per-level grids): Phase 2's generator/detector stamps it, Phase 3
replays it (reset-to-grid, crash recovery), Phase 7 embeds it in game
files/checkpoints. This module reserves the schema ONCE so those phases
extend it ADDITIVELY without breaking older readers.

RESERVED payload shape (the container's 'data'; research R5, H8-H12):

    {
      "detector_version": "det-1",   # EXACT match required (see below)
      "format_version": 1,           # additive evolution (refuse-newer)
      "seed": <int>,                 # deterministic regeneration (H12)
      "levels": [
        {
          "level_index": 0,          # 0-based
          "difficulty": {"tier": 0, "grid_n": 3, "n_required_types": 2,
                         "molecule_size_class": "small"},
          "molecules": [             # a level = a SET of molecules
            {
              "molecule_id": "mol-001",
              "ligand": {"source", "set_id", "entry_id", "file",
                         "sha256", "protonation", "provenance"},
              "required": {"mode": "any" | "list",     # RESOLVED set
                           "items": [{"type", "count"}]},
              "grid": {"n": 3,
                       "slots": [{"slot_id", "row", "col", "aa",
                                  "role", "can_form",
                                  "grid_pose": {"position"}}]}
            }
          ]
        }
      ]
    }

Versioning policy -- TWO gates with TWO distinct messages (P4):

- format_version: refuse-newer / accept-older. Additive-field evolution
  only; readers use .get() defaults for fields older payloads lack.
- detector_version: EXACT match against DETECTOR_VERSION -- stale AND
  newer stamps are BOTH refused, because changed detection semantics
  (thresholds/typing) make old specs unsolvable, not merely incomplete
  (DETECT-05 precursor; PITFALLS.md:274-280).

Unknown keys are PRESERVED, never stripped (P9): parse is passthrough,
so Phase 3/7 additive extensions survive a Phase-1-era reader. The
input dict is never mutated (P6).

Purity: module-level imports are stdlib + .persistence ONLY (pure<-pure,
direction per research R1). NO file I/O here -- persistence owns files;
level_spec owns dict-level parse only. NO pymol/Qt/numpy. level_spec
does NOT import setup_state (independent schemas): can_form members are
NOT validated against setup_state's interaction enum -- Phase 2's
generator guarantees that consistency.
"""

from .persistence import FormatError, check_container, make_container

DETECTOR_VERSION = "det-1"
LEVEL_SPEC_VERSION = 1


def _is_int(value):
    """True for real ints only -- bool is an int subclass, never a count."""
    return isinstance(value, int) and not isinstance(value, bool)


def make_level_spec_container(data):
    """Build a versioned container (kind='level_spec') around `data`.

    Convenience re-export of persistence.make_container for the Phase-2
    generator and tests.
    """
    return make_container('level_spec', data)


def parse_level_spec_dict(container):
    """Validate a level-spec container; return its payload UNCHANGED.

    `container` is a full AA-match container dict (magic/version/kind/
    data) as produced by make_level_spec_container or read from a file.
    Gate chain, in order:

    1. container gate -- persistence.check_container(kind='level_spec'):
       foreign magic / newer container version / misfiled kind refused.
    2. payload format_version (default 1): refuse-newer / accept-older;
       a newer payload is refused ("unsupported level spec version").
    3. payload detector_version: EXACT match against DETECTOR_VERSION;
       ANY other stamp -- stale or newer -- is refused (P4).
    4. structural minimums: int seed present; levels a non-empty list;
       every level's difficulty.grid_n >= 1; every molecule's grid.n >= 1;
       grid.slots a list with UNIQUE slot_id values per molecule.

    Returns the payload dict itself (passthrough, P9); the input is
    never mutated (P6). Raises FormatError naming the failing gate.
    """
    container = check_container(container, 'level_spec')
    data = container.get('data')
    if not isinstance(data, dict):
        raise FormatError(
            "level spec payload must be a dict (found %s)"
            % type(data).__name__)

    try:
        format_version = int(data.get('format_version', 1))
    except (TypeError, ValueError):
        raise FormatError(
            "missing or invalid format_version field in level spec "
            "(found %r)" % (data.get('format_version'),))
    if format_version > LEVEL_SPEC_VERSION:
        raise FormatError(
            "unsupported level spec version %d (expected <= %d). "
            "Please update AA-match." % (format_version, LEVEL_SPEC_VERSION))

    detector_version = data.get('detector_version')
    if detector_version != DETECTOR_VERSION:
        raise FormatError(
            "unsupported detector_version %r in level spec (expected %r): "
            "stale or newer game spec - regenerate it with a current "
            "AA-match generator" % (detector_version, DETECTOR_VERSION))

    _check_seed(data)
    _check_levels(data.get('levels'))
    return data


def _check_seed(data):
    """Seed must be present AND an int: a spec without one cannot be
    deterministically replayed (H12)."""
    seed = data.get('seed')
    if not _is_int(seed):
        raise FormatError(
            "level spec 'seed' must be present and an int for "
            "deterministic replay (found %r)" % (seed,))


def _check_levels(levels):
    """Non-empty levels list, then per-level structural minimums."""
    if not isinstance(levels, list) or not levels:
        raise FormatError(
            "level spec 'levels' must be a non-empty list (found %r)"
            % (levels,))
    for level_index, level in enumerate(levels):
        _check_level(level, level_index)


def _check_level(level, level_index):
    """One level: difficulty.grid_n >= 1 and a molecules list to walk."""
    if not isinstance(level, dict):
        raise FormatError(
            "levels[%d] must be a dict (found %s)"
            % (level_index, type(level).__name__))
    difficulty = level.get('difficulty')
    if not isinstance(difficulty, dict):
        raise FormatError(
            "levels[%d] 'difficulty' must be a dict (found %s)"
            % (level_index, type(difficulty).__name__))
    grid_n = difficulty.get('grid_n')
    if not _is_int(grid_n) or grid_n < 1:
        raise FormatError(
            "levels[%d] difficulty 'grid_n' must be an int >= 1 (found %r)"
            % (level_index, grid_n))
    molecules = level.get('molecules')
    if not isinstance(molecules, list):
        raise FormatError(
            "levels[%d] 'molecules' must be a list (found %s)"
            % (level_index, type(molecules).__name__))
    for molecule in molecules:
        _check_molecule_grid(molecule)


def _check_molecule_grid(molecule):
    """One molecule: grid.n >= 1 and slots with unique slot_id values
    (scope is PER MOLECULE -- the generator's global allocation
    invariant, PITFALLS.md:270-271)."""
    if not isinstance(molecule, dict):
        raise FormatError(
            "level molecules entries must be dicts (found %s)"
            % type(molecule).__name__)
    molecule_id = molecule.get('molecule_id')
    grid = molecule.get('grid')
    if not isinstance(grid, dict):
        raise FormatError(
            "molecule %r 'grid' must be a dict (found %s)"
            % (molecule_id, type(grid).__name__))
    n = grid.get('n')
    if not _is_int(n) or n < 1:
        raise FormatError(
            "molecule %r grid 'n' must be an int >= 1 (found %r)"
            % (molecule_id, n))
    slots = grid.get('slots')
    if not isinstance(slots, list):
        raise FormatError(
            "molecule %r grid 'slots' must be a list (found %s)"
            % (molecule_id, type(slots).__name__))
    seen_slot_ids = set()
    for slot in slots:
        if not isinstance(slot, dict):
            raise FormatError(
                "grid slots entries must be dicts (found %s)"
                % type(slot).__name__)
        slot_id = slot.get('slot_id')
        try:
            duplicate = slot_id in seen_slot_ids
        except TypeError:
            raise FormatError(
                "molecule %r slot_id must be a hashable scalar (found %r)"
                % (molecule_id, slot_id))
        if duplicate:
            raise FormatError(
                "duplicate slot_id %r in one molecule's grid slots "
                "(slot ids must be unique per molecule)" % (slot_id,))
        seen_slot_ids.add(slot_id)
